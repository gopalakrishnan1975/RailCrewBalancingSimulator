from engine import Config,simulate,timetable,staff_sweep
def test_reproducible():
    assert simulate(Config())[0]==simulate(Config())[0]
def test_no_deadheading():
    s,_,moves,_=simulate(Config(policy="No deadheading"))
    assert moves.empty and s["road_trips"]==s["passenger_trips"]==0
def test_duty_limit():
    try: simulate(Config(duty_limit_hours=2))
    except ValueError: pass
    else: assert False
def test_time_table():
    assert timetable("08:00,02:30")==[2.5,8.]
def test_fleet_capacity():
    assert simulate(Config(crews=5))[0]["covered"]<=simulate(Config(crews=25))[0]["covered"]
def test_demand_balance():
    s,*_=simulate(Config(up_per_day=0,down_per_day=0))
    assert s["demand"]==s["uncovered"]==0
