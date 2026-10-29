# Freight Crew Balancing and Staffing Simulator

Standalone two-terminal synthetic freight-crew scenario lab. Separate from process-modelling.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
pytest -q
```

## Features
UP A→B and DN B→A demand; single-side A HQ or two-end HQ; away-terminal running-room rest vs HQ rest; road and passenger-timetable deadheading, five policies; coverage, reposition cost, crew usage, staffing sweep and CSV exports.

## Modelling assumptions / limitations
Discrete-time event simulation with fixed freight run times and one crew-unit per train. Freight is covered at scheduled departure or recorded uncovered; no train holding. Deadheading is triggered only when no crew is ready at an origin. Road and passenger seats, directional timetable variation, accommodation capacity, duty-link regulatory compliance, leave/training reserve, route knowledge, traction qualification, crew base quotas and stochastic travel delays are not modelled. Passenger timetable entries apply both ways. A crew becomes available after journey + sign/release + location-dependent rest. Deadheading adds a separate rest period. Staffing sweep reports first *tested* feasible size, not a proof of global optimum. All defaults are synthetic and must be calibrated against railway rules and records prior to any operational use.

## Streamlit
On https://share.streamlit.io select this GitHub repository, default branch `main`, main file `app.py`. A private repo may need Streamlit GitHub authorization.
