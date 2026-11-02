# NER Logistics & Accessibility Monitor — Streamlit version (SIH 2026 PS 26002)

A pure-Python prototype (Streamlit + folium) of the same system as the React version: **field report → verification → road status → risk re-score → route comparison → delivery impact → alert**, plus offline reporting.

> **Everything is simulated sample data.** No live weather, GPS tracking, verified closures or AI model. Distances/speeds are invented, road lines are schematic, risk is a transparent rule-based score (not AI).

## Run

```bash
pip install -r requirements.txt
streamlit run app.py        # opens http://localhost:8501
pytest -q                   # 11 tests
```
Needs Python 3.10+ and an internet connection (the map loads Leaflet and OpenStreetMap tiles from the web). State is saved in `data/state.json`; the sidebar "Reset demo data" restores the sample data.

## Where is the "backend"?
Streamlit is both the UI and the server: the Python code runs on the server and Streamlit draws the page. There is no separate frontend project to build. `core/` has no Streamlit imports (pure Python, unit-tested) and `views/` only draws screens, so a FastAPI/database backend can replace `core/storage.py` later.

```
app.py              sidebar (navigation, role, offline toggle, simulation controls) + page router
core/seed.py        SAMPLE places, roads, incidents, deliveries
core/risk.py        rule-based risk scoring and explanations
core/routing.py     route search, risk-adjusted ranking, recommendation text
core/delivery.py    vehicle simulation, disruption detection, reroute suggestion, priority rules
core/actions.py     every state change (submit/sync/review report, set road status, reroute, tick) + alert generation
core/storage.py     JSON file persistence (swap for a database later)
views/              dashboard, road_map, routes, deliveries, reports, alerts + common helpers (folium map)
tests/              test_workflow.py (logic), test_app_ui.py (headless UI test via Streamlit AppTest)
```
Rules (same as the React version): risk = Σ(type weight × severity × verification factor) + status points (open 0 / risky 15 / blocked 40); levels Low <15, Medium <35, High <60, Critical ≥60. An **unverified report raises risk but never closes a road**; only an authority can set confirmed status. Routes are ranked by time × (1 + penalty for the worst risk: 5 / 25 / 60 %). Delivery priority = supply urgency + route risk + blocked-ahead + delay.

## Demo script (≈3 min)
1. **Dashboard**: DEL-101 (medicines, Guwahati → Silchar) is in transit. Use *Advance simulation ▶* or turn on *Auto-run* (vehicles move every 2 s on the Dashboard and Deliveries pages).
2. **Field reports** → *Fill demo landslide report* → *Submit report*. It shows **Pending Review**. The Route planner still recommends the Shillong route.
3. Click **Verify** (role must be Authority; switch the sidebar role to *Field user* to see verification disabled).
4. **Road map**: select *Shillong–Jowai* → Blocked, Critical, with reasons. **Route planner**: now recommends Guwahati → Nagaon → Lumding → Haflong → Silchar with an explanation. **Deliveries**: DEL-101 is *Disruption ahead*, High priority → **Apply reroute**. **Alerts**: critical alert with recommended action.
5. **Offline**: switch on *Simulate offline mode* (sidebar), submit a report → saved as *Pending sync* with no effect on risk. Switch it off → it syncs once automatically.

## Limitations of the Streamlit version (honest list)
* **Offline mode is simulated.** Streamlit runs on a server, so it cannot see the browser going offline or store data in the browser. The toggle makes the app queue reports as `pending_sync` and sync them when switched off; duplicates are ignored by a per-report `client_id`. A true offline-first app (service worker + local storage) needs the React version.
* Map: clicking a road/marker does not select it (the map is display-only to avoid constant page reloads). Use the dropdowns on the Road map page to see details. Panning and zooming work normally.
* Simulation advances only via the button or Auto-run, and only while the Dashboard or Deliveries page is open.
* GPS capture is optional (`pip install streamlit-geolocation`); it was **not tested**. Manual coordinates always work, and the nearest road is auto-suggested.
* One shared `data/state.json`: several people using the same running app share one dataset. Roles are a dropdown, not login.

## Test results (executed 2 Nov 2026)
`pytest -q`: **11 passed**. This covers the logic (risk rules, unverified vs verified, routing, vehicle hold and turn-back, offline queue and duplicate protection, storage round-trip) and a headless run of the actual app screens through the whole demo workflow, the offline sync and all six pages.
Real-browser checks (Chromium): dashboard and map render; submit → Pending Review → Verify → Deliveries shows the suggested reroute; Auto-run advanced the simulation (108 → 123 min in ~9 s). Not tested: GPS, tile images (no internet in the test sandbox), mobile layout.

## Roadmap
FastAPI + PostgreSQL/PostGIS backend; real road network and routing engine; real weather feeds; real offline-first client; real GPS; validated ML risk model; authentication, audit log, multilingual alerts.
