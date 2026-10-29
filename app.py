import streamlit as st
import pandas as pd
from dataclasses import asdict
from engine import Config, simulate, staff_sweep, POLICIES
st.set_page_config(page_title="Freight Crew Balancing Lab",page_icon="🚂",layout="wide")
st.title("Freight Crew Balancing & Staffing Lab")
st.caption("Synthetic corridor A ⇄ B | planning prototype, not a legal-duty roster or operational dispatch tool")
with st.sidebar:
    st.header("Demand")
    days=st.slider("Days",1,30,7)
    crews=st.slider("Crew units",1,300,60)
    up=st.number_input("UP A → B freight / day",0.,150.,18.,step=1.)
    dn=st.number_input("DN B → A freight / day",0.,150.,18.,step=1.)
    variation=st.slider("Daily demand variation",0.,1.,.2,.05)
    seed=st.number_input("Random seed",0,100000,7)
    st.header("Headquarters / rest")
    hq=st.selectbox("HQ model",["Both terminals","A only"])
    share=st.slider("Fraction of HQ crews at A",0.,1.,.5,.05,disabled=hq=="A only")
    home=st.number_input("HQ rest (hours)",1.,48.,16.)
    away=st.number_input("RR / away rest (hours)",1.,48.,8.)
    st.header("Duty")
    travel=st.number_input("Freight journey hours",1.,24.,6.)
    duty=st.number_input("Maximum freight duty hours",1.,24.,10.)
    st.header("Balancing")
    policy=st.selectbox("Deadheading policy",POLICIES)
    road=st.number_input("Road hours",.5,24.,3.)
    passenger=st.number_input("Passenger hours",.5,24.,4.)
    rc=st.number_input("Road transfer cost ₹",0.,100000.,1500.)
    pc=st.number_input("Passenger transfer cost ₹",0.,100000.,350.)
    schedule=st.text_input("Passenger departures (both directions)","02:00,08:00,14:00,20:00")
    maxwait=st.number_input("Maximum passenger wait (hours)",0.,24.,12.)
cfg=Config(days=days,crews=crews,up_per_day=up,down_per_day=dn,variation=variation,seed=int(seed),
 hq_mode=hq,share_a=share,home_rest_hours=home,away_rest_hours=away,freight_hours=travel,
 duty_limit_hours=duty,policy=policy,road_hours=road,passenger_hours=passenger,
 road_cost=rc,passenger_cost=pc,passenger_departures=schedule,max_wait_hours=maxwait)
try: summary,assignments,moves,roster=simulate(cfg)
except ValueError as exc: st.error(str(exc));st.stop()
cols=st.columns(5)
for col,key in zip(cols,["demand","covered","uncovered","coverage_pct","deadheading_cost"]):
    col.metric(key.replace("_"," ").title(),summary[key])
a,b,c=st.tabs(["Scenario","Policy comparison","Staffing & downloads"])
with a:
    st.subheader("Coverage by direction")
    st.dataframe(pd.DataFrame([{"direction":d,"trains":len(df),"covered":sum(df.status=="covered")}
        for d,df in assignments.groupby("direction")]),hide_index=True)
    st.dataframe(assignments,use_container_width=True,hide_index=True)
with b:
    if st.button("Compare all policies"):
        rows=[]
        for p in POLICIES:
            s,*_=simulate(Config(**{**asdict(cfg),"policy":p}))
            rows.append({"policy":p,**s})
        st.dataframe(pd.DataFrame(rows),hide_index=True)
        st.bar_chart(pd.DataFrame(rows).set_index("policy")[["up_coverage_pct","dn_coverage_pct"]])
with c:
    target=st.slider("Minimum freight coverage (%)",80,100,99)
    if st.button("Compute staffing requirement"):
        n,scan=staff_sweep(cfg,target)
        st.success(f"First tested fleet reaching target: {n}" if n else "No fleet within search range reaches target")
        st.dataframe(scan.tail(30),hide_index=True)
        st.download_button("Download staffing sweep CSV",scan.to_csv(index=False),"staffing.csv","text/csv")
    st.download_button("Download assignment CSV",assignments.to_csv(index=False),"assignments.csv","text/csv")
    st.download_button("Download deadheading CSV",moves.to_csv(index=False),"transfers.csv","text/csv")
    st.download_button("Download crew roster CSV",roster.to_csv(index=False),"crews.csv","text/csv")
