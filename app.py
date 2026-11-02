"""NER Logistics & Accessibility Monitor (SIH 2026 PS 26002). Run:  streamlit run app.py"""
import streamlit as st

from core import actions as A
from core.storage import clear_state, load_state
from views import alerts, dashboard, deliveries, reports, road_map, routes
from views.common import commit, now_iso

st.set_page_config(page_title="NER Logistics Monitor", page_icon="🚚", layout="wide")

if "state" not in st.session_state:
    st.session_state["state"] = load_state(now_iso())
    st.session_state.update(sim_offline=False, auto=False, speed=3)
s = st.session_state["state"]

PAGES = ["Dashboard", "Road map", "Route planner", "Deliveries", "Field reports", "Alerts"]
with st.sidebar:
    st.title("NER Logistics")
    st.caption("Accessibility monitor")
    page = st.radio("Navigate", PAGES, label_visibility="collapsed", key="page")
    st.divider()
    role_label = st.selectbox("Role", ["Authority (can verify)", "Field user"])
    role = "authority" if role_label.startswith("Authority") else "field"
    st.toggle("Offline mode", key="sim_offline", help="Reports are saved on the device and synced when you turn it off.")
    online = not st.session_state["sim_offline"]
    pending = sum(1 for r in s["reports"] if r["sync_state"] == "pending_sync")
    st.markdown((":green[● Online]" if online else ":red[○ Offline]") + (f" · {pending} to sync" if pending else ""))
    if online and pending:  # auto-sync when connectivity returns (idempotent)
        A.sync_reports(s, now_iso())
        commit()
        st.rerun()
    st.divider()
    st.markdown(":violet-badge[TRACKING] vehicles")
    st.select_slider("Speed (minutes per step)", [3, 10, 30], key="speed")
    if st.button("Advance simulation ▶"):
        A.tick(s, st.session_state["speed"])
        commit()
    st.toggle("Auto-run (Dashboard & Deliveries pages)", key="auto")
    if st.button("Reset data"):
        clear_state()
        st.session_state["state"] = load_state(now_iso())
        st.session_state["form_n"] = st.session_state.get("form_n", 0) + 1
        st.rerun()


def with_autorun(render_fn):
    """Re-run just this page every 2 s while auto-run is on, ticking the simulation."""
    @st.fragment(run_every=2 if st.session_state["auto"] else None)
    def frag():
        if st.session_state["auto"]:
            A.tick(s, st.session_state["speed"])
            commit()
        render_fn()
    frag()


if page == "Dashboard":
    with_autorun(dashboard.render)
elif page == "Road map":
    road_map.render(role)
elif page == "Route planner":
    routes.render()
elif page == "Deliveries":
    with_autorun(deliveries.render)
elif page == "Field reports":
    reports.render(role, online)
else:
    alerts.render()
