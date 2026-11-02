import streamlit as st

from core.delivery import compute_view
from core.risk import assess_all
from views.common import build_map, fmt_min, fmt_time, get_state, risk_md, show_map


def render():
    s = get_state()
    risks = assess_all(s["segments"], s["incidents"])
    views = [compute_view(d, s["segments"], s["incidents"]) for d in s["deliveries"]]
    st.header("Operations overview")
    count = lambda x: sum(1 for g in s["segments"] if g["status"] == x)
    active = [v for v in views if not v["delivery"]["delivered"]]
    hi = sum(1 for i in s["incidents"] if i["verification"] != "rejected" and i["severity"] >= 4)
    pend = sum(1 for r in s["reports"] if r["status"] == "pending_review" and r["sync_state"] == "synced")
    unsynced = sum(1 for r in s["reports"] if r["sync_state"] == "pending_sync")
    cols = st.columns(6)
    cols[0].metric("Active deliveries", len(active))
    cols[1].metric("Open roads", count("open"))
    cols[2].metric("Risky roads", count("risky"))
    cols[3].metric("Blocked roads", count("blocked"))
    cols[4].metric("High-severity incidents (4–5)", hi)
    cols[5].metric("Reports pending review", pend, help=f"{unsynced} more saved offline, not yet synced" if unsynced else None)

    left, right = st.columns([3, 2])
    with left:
        st.subheader("Road map")
        show_map(build_map(s, risks, views), height=440, key="dash_map")
    with right:
        with st.container(border=True):
            st.subheader("Needs attention")
            flagged = sorted([v for v in active if v["priority"]["level"] != "Normal"], key=lambda v: -v["priority"]["score"])
            if not flagged:
                st.caption("No deliveries flagged.")
            for v in flagged:
                d = v["delivery"]
                st.markdown(f"**{d['id']}** · {d['cargo']} — {':red[High]' if v['priority']['level'] == 'High' else ':orange[Medium]'}")
                st.caption(" · ".join(v["priority"]["reasons"]))

        with st.container(border=True):
            st.subheader("Delivery status summary")
            labels = ["In transit", "Disruption ahead", "Held – road blocked", "Rerouted – in transit", "Delivered"]
            for l in labels:
                n = sum(1 for v in views if v["display_status"] == l or (l == "In transit" and v["display_status"] == "In transit – high risk ahead"))
                st.write(f"{l}: **{n}**")

        with st.container(border=True):
            st.subheader("Recent alerts")
            for a in s["alerts"][:4]:
                icon = {"critical": "🔴", "warning": "🟠", "info": "🔵"}[a["severity"]]
                st.markdown(f"{icon} **{a['title']}**  \n:gray[{a['location']} · {fmt_time(a['time'])}]")

    with st.container(border=True):
        st.subheader("Active deliveries")
        st.dataframe([{"ID": v["delivery"]["id"], "Cargo": v["delivery"]["cargo"], "Status": v["display_status"],
                       "Worst risk ahead": v["worst_risk"], "ETA (est.)": fmt_min(v["eta_min"])} for v in active],
                     use_container_width=True, hide_index=True)
