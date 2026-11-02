import streamlit as st

from core import actions as A
from core.delivery import compute_view
from core.risk import assess_all
from core.routing import route_label
from core.seed import PLACES, place_name
from views.common import SUPPLY, build_map, commit, fmt_min, get_state, now_iso, risk_md, show_map, sim_tag


def render():
    s = get_state()
    risks = assess_all(s["segments"], s["incidents"])
    views = sorted((compute_view(d, s["segments"], s["incidents"]) for d in s["deliveries"]), key=lambda v: -v["priority"]["score"])
    st.header("Essential-supply deliveries " + sim_tag("SIMULATED VEHICLES, NOT GPS"))
    st.caption("Vehicle positions move along sample routes in a simulation. Use the sidebar to advance or auto-run it.")
    left, right = st.columns([1, 1])
    with left:
        for v in views:
            d = v["delivery"]
            with st.container(border=True):
                lvl = v["priority"]["level"]
                pri = {"High": ":red[**High**]", "Medium": ":orange[**Medium**]", "Normal": ":green[**Normal**]"}[lvl]
                st.markdown(f"**{d['id']} · {SUPPLY[d['supply']]}** — Priority: {pri}")
                st.write(f"{d['cargo']} · Vehicle **{d['vehicle_id']}** (simulated)")
                st.write(f"To **{place_name(d['destination'])}** · Status: **{v['display_status']}** · Risk ahead {risk_md(v['worst_risk'])}")
                delay = f" · :red[**Delay +{fmt_min(v['delay_min'])}**]" if v["delay_min"] and v["delay_min"] > 1 and not d["delivered"] else ""
                st.write(f"Position (simulated): {v['position'][0]:.3f}, {v['position'][1]:.3f} · Remaining {round(v['remaining_km'])} km · ETA est. {fmt_min(v['eta_min'])}{delay}")
                st.caption("Route: " + route_label(d["nodes"], PLACES))
                with st.expander(f"Why this priority? ({v['priority']['score']} pts)"):
                    for r in v["priority"]["reasons"]:
                        st.write("• " + r)
                if v["disruption"].startswith("blocked"):
                    seg = next(x for x in s["segments"] if x["id"] == v["blocked_segment_id"])
                    st.error(f"**Road blocked:** {seg['name']} is confirmed blocked on this route.")
                    g = v["suggestion"]
                    if g:
                        st.write(f"**Suggested reroute:** {route_label(g['route']['nodes'], PLACES)} — {g['note']} "
                                 f"Est. remaining {fmt_min(g['est_remaining_min'])}; total delay vs plan ≈ +{fmt_min(g['est_delay_min'])}.")
                        if st.button("Apply reroute", key=f"rr_{d['id']}", type="primary"):
                            A.apply_reroute(s, d["id"], now_iso())
                            commit()
                            st.rerun()
                    else:
                        st.write("No passable alternative found in the sample network. Hold the vehicle.")
    with right:
        pick = st.selectbox("Highlight remaining route of", ["—"] + [v["delivery"]["id"] for v in views])
        hl = next((v["remaining_segment_ids"] for v in views if v["delivery"]["id"] == pick), None)
        show_map(build_map(s, risks, views, highlight=hl), height=560, key="deliv_map")
