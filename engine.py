"""Two-terminal freight-crew staffing prototype; synthetic planning only."""
from dataclasses import dataclass, asdict
from random import Random
import math
import pandas as pd

POLICIES = ("No deadheading","Road first","Passenger first","Lowest cost","Hybrid")
@dataclass
class Config:
    days:int=7
    crews:int=60
    hq_mode:str="Both terminals"
    share_a:float=.5
    up_per_day:float=18
    down_per_day:float=18
    variation:float=.2
    freight_hours:float=6
    duty_limit_hours:float=10
    sign_on_hours:float=.5
    release_hours:float=.5
    home_rest_hours:float=16
    away_rest_hours:float=8
    road_hours:float=3
    road_cost:float=1500
    passenger_hours:float=4
    passenger_cost:float=350
    passenger_departures:str="02:00,08:00,14:00,20:00"
    max_wait_hours:float=12
    policy:str="Road first"
    seed:int=7

def timetable(value):
    times=[]
    for p in value.split(","):
        try:
            h,m=map(int,p.strip().split(":"))
            if not (0<=h<24 and 0<=m<60): raise ValueError()
        except ValueError: raise ValueError("Passenger departure must be HH:MM")
        times.append(h+m/60)
    if not times: raise ValueError("At least one passenger departure required")
    return sorted(set(times))

def generate_trains(cfg):
    rng=Random(cfg.seed); trains=[]
    for day in range(cfg.days):
        for origin,avg,direction in (("A",cfg.up_per_day,"UP"),("B",cfg.down_per_day,"DN")):
            count=max(0,round(avg*(1+rng.uniform(-cfg.variation,cfg.variation))))
            for j in range(count):
                t=24*day+24*(j+rng.random())/max(count,1)
                trains.append(dict(id="F%05d"%(len(trains)+1),departure=round(t,3),
                    origin=origin,destination="B" if origin=="A" else "A",direction=direction))
    return sorted(trains,key=lambda x:x["departure"])

def next_departure(t,clock):
    d=math.floor(t/24)
    return min(24*k+h for k in range(d,d+3) for h in clock if 24*k+h>=t-1e-8)

def simulate(cfg):
    if cfg.days<1 or cfg.crews<1 or cfg.freight_hours<=0 or cfg.up_per_day<0 or cfg.down_per_day<0 or not 0<=cfg.variation<=1: raise ValueError("Invalid horizon, crew or demand")
    if cfg.hq_mode not in ("Both terminals","A only") or not 0<=cfg.share_a<=1: raise ValueError("Invalid HQ configuration")
    if cfg.policy not in POLICIES: raise ValueError("Unknown balancing policy")
    if min(cfg.home_rest_hours,cfg.away_rest_hours,cfg.road_hours,cfg.passenger_hours)<0: raise ValueError("Negative rest or travel")
    if cfg.freight_hours+cfg.sign_on_hours+cfg.release_hours>cfg.duty_limit_hours: raise ValueError("Duty exceeds configured maximum")
    clock=timetable(cfg.passenger_departures) if cfg.policy in ("Passenger first","Lowest cost","Hybrid") else []
    na=cfg.crews if cfg.hq_mode=="A only" else round(cfg.crews*cfg.share_a)
    crews=[dict(id=i+1,hq="A" if i<na else "B",location="A" if i<na else "B",
               available=0.,freight=0,road=0,passenger=0) for i in range(cfg.crews)]
    assignments=[]; transfers=[]
    def reposition(c,target,deadline):
        if cfg.policy=="No deadheading" or c["location"]==target: return False
        now=c["available"]
        modes=[("road",now,now+cfg.road_hours,cfg.road_cost)]
        if clock:
            dep=next_departure(now,clock)
            modes.append(("passenger",dep,dep+cfg.passenger_hours,cfg.passenger_cost))
        if cfg.policy=="Road first": modes=modes[:1]
        elif cfg.policy=="Passenger first": modes.sort(key=lambda x:(x[0]!="passenger",x[2]))
        elif cfg.policy=="Lowest cost": modes.sort(key=lambda x:(x[3],x[2]))
        else: modes.sort(key=lambda x:(x[2],x[3]))
        for mode,dep,arr,cost in modes:
            rest=cfg.home_rest_hours if target==c["hq"] else cfg.away_rest_hours
            if dep-now>cfg.max_wait_hours or arr+rest>deadline: continue
            initial=c["location"]
            c["location"]=target;c["available"]=arr+rest;c[mode]+=1
            transfers.append(dict(crew=c["id"],from_terminal=initial,to_terminal=target,
                       mode=mode,depart=round(dep,2),arrive=round(arr,2),
                       available=round(arr+rest,2),cost=cost))
            return True
        return False
    trains=generate_trains(cfg)
    for train in trains:
        t=train["departure"];origin=train["origin"]
        ready=[c for c in crews if c["location"]==origin and c["available"]<=t]
        if not ready and cfg.policy!="No deadheading":
            for c in sorted((c for c in crews if c["location"]!=origin and c["available"]<t),key=lambda x:x["available"]):
                if reposition(c,origin,t):
                    ready=[r for r in crews if r["location"]==origin and r["available"]<=t]
                    if ready: break
        row={**train,"crew":None,"status":"uncovered","crew_hq":None,"next_available":None}
        if ready:
            c=min(ready,key=lambda x:(x["location"]!=x["hq"],x["available"],x["id"]))
            c["location"]=train["destination"]
            c["available"]=t+cfg.sign_on_hours+cfg.freight_hours+cfg.release_hours+(
                cfg.home_rest_hours if c["location"]==c["hq"] else cfg.away_rest_hours)
            c["freight"]+=1
            row.update(crew=c["id"],status="covered",crew_hq=c["hq"],next_available=round(c["available"],2))
        assignments.append(row)
    df=pd.DataFrame(assignments,columns=["id","departure","origin","destination","direction","crew","status","crew_hq","next_available"])
    moves=pd.DataFrame(transfers,columns=["crew","from_terminal","to_terminal","mode","depart","arrive","available","cost"])
    covered=sum(r["status"]=="covered" for r in assignments)
    up=[r for r in assignments if r["direction"]=="UP"];dn=[r for r in assignments if r["direction"]=="DN"]
    summary=dict(demand=len(trains),covered=covered,uncovered=len(trains)-covered,
      coverage_pct=round(100*covered/max(1,len(trains)),2),
      up_coverage_pct=round(100*sum(r["status"]=="covered" for r in up)/max(1,len(up)),2),
      dn_coverage_pct=round(100*sum(r["status"]=="covered" for r in dn)/max(1,len(dn)),2),
      road_trips=sum(r["mode"]=="road" for r in transfers),
      passenger_trips=sum(r["mode"]=="passenger" for r in transfers),
      deadheading_cost=round(sum(r["cost"] for r in transfers),2),
      crews_used=sum(c["freight"]>0 for c in crews),
      away_terminal_crew_end=sum(c["location"]!=c["hq"] for c in crews),
      crew_utilization_pct=round(100*covered*(cfg.sign_on_hours+cfg.freight_hours+cfg.release_hours)/(cfg.crews*cfg.days*24),2))
    return summary,df,moves,pd.DataFrame(crews)

def staff_sweep(cfg,target=99,high=300):
    rows=[]
    for n in range(1,high+1):
        s,*_=simulate(Config(**{**asdict(cfg),"crews":n}))
        rows.append(dict(crews=n,**s))
        if s["coverage_pct"]>=target: return n,pd.DataFrame(rows)
    return None,pd.DataFrame(rows)
