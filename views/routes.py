import streamlit as st

from core.risk import assess_all
from core.routing import find_routes, recommend, route_label
from core.seed import PLACES
from views.common import build_map, fmt_min, get_state, risk_md, show_map, sim_tag


def render():
    s = get_state()
    risks = assess_all(s["segments"], s["incidents"])
    st.header("Route planner " + sim_tag("SAMPLE NETWORK"))
    ids = [p["id"] for p in PLACES]
    names = {p["id"]: p["name"] for p in PLACES}
    c1, c2 = st.columns(2)
    frm = c1.selectbox("Origin", ids, index=ids.index("GUW"), format_func=names.get)
    to = c2.selectbox("Destination", ids, index=ids.index("SIL"), format_func=names.get)
    if frm == to:
        st.info("Choose two different places.")
        return
    routes = find_routes(s["segments"], s["incidents"], frm, to)
    rec, why = recommend(routes, PLACES, s["segments"])
    left, right = st.columns([1, 1])
    with left:
        st.subheader("Recommendation")
        st.markdown(f"**{route_label(rec['nodes'], PLACES)}**" if rec else "**No recommendation**")
        st.write(why)
        labels = [f"{'⭐ ' if r is rec else '⛔ ' if not r['passable'] else ''}{route_label(r['nodes'], PLACES)}" for r in routes]
        pick = st.radio("Show route on map", range(len(routes)), format_func=lambda i: labels[i],
                        index=routes.index(rec) if rec else 0) if routes else None
        for r in routes:
            with st.container(border=True):
                tag = " :green[**Recommended**]" if r is rec else " :red[**Not passable**]" if not r["passable"] else ""
                st.markdown(f"**{route_label(r['nodes'], PLACES)}**{tag}")
                st.write(f"{round(r['distance_km'])} km (sample) · est. {fmt_min(r['time_min'])} · worst risk {risk_md(r['risk_level'])}")
                for w in r["warnings"]:
                    st.caption(f"{w['segment_name']} ({w['level']}): " + "; ".join(w["reasons"]))
                if not r["passable"]:
                    st.caption("Includes a CONFIRMED-blocked road, so it is excluded from recommendations.")
        st.caption("Estimates use sample distances and nominal speeds. Risk uses transparent rules (not AI). No route is guaranteed safe.")
    with right:
        hl = routes[pick]["segment_ids"] if routes else None
        show_map(build_map(s, risks, highlight=hl), height=520, key="route_map")
