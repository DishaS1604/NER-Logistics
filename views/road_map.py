import streamlit as st

from core.delivery import compute_view
from core.risk import TYPE_LABEL, assess_all
from core.seed import place_name
from views.common import build_map, commit, fmt_time, get_state, now_iso, risk_md, show_map, status_md
from core import actions as A


def render(role):
    s = get_state()
    risks = assess_all(s["segments"], s["incidents"])
    views = [compute_view(d, s["segments"], s["incidents"]) for d in s["deliveries"]]
    st.header("Road accessibility map")
    c1, c2, c3 = st.columns(3)
    status = c1.selectbox("Road status", ["all", "open", "risky", "blocked"])
    typ = c2.selectbox("Incident type", ["all"] + list(TYPE_LABEL), format_func=lambda t: "All" if t == "all" else TYPE_LABEL[t])
    segs = {g["id"]: g for g in s["segments"]}
    sel = c3.selectbox("Select a road for details", ["—"] + list(segs), format_func=lambda i: "—" if i == "—" else segs[i]["name"])
    left, right = st.columns([2, 1])
    with left:
        show_map(build_map(s, risks, views, status, typ, selected_seg=None if sel == "—" else sel), height=520, key="main_map")
    with right:
        with st.container(border=True):
            st.subheader("Road details")
            if sel == "—":
                st.caption("Choose a road above, or an incident below.")
            else:
                g = segs[sel]
                r = risks[sel]
                st.markdown(f"**{g['name']}** — {status_md(g['status'])}")
                st.write(f"{place_name(g['from'])} ↔ {place_name(g['to'])} · {g['distance_km']} km")
                st.markdown(f"Rule-based risk: {risk_md(r['level'])} · score {r['score']}")
                for reason in r["reasons"]:
                    st.write("• " + reason)
                st.caption(f"Confirmed status updated {fmt_time(g['status_updated_at'])} {('· ' + g['status_note']) if g['status_note'] else ''}")
                st.write("**Set confirmed status (authority):**")
                bc = st.columns(3)
                for col, st_name in zip(bc, ["open", "risky", "blocked"]):
                    if col.button(st_name, key=f"set_{sel}_{st_name}", disabled=role != "authority" or g["status"] == st_name):
                        A.set_segment_status(s, sel, st_name, now_iso(), role)
                        commit()
                        st.rerun()
                if role != "authority":
                    st.caption("Switch role to Authority in the sidebar.")

        with st.container(border=True):
            st.subheader("Incident inspector")
            incs = [i for i in s["incidents"] if i["verification"] != "rejected"]
            pick = st.selectbox("Incident details", ["—"] + [i["id"] for i in incs],
                                format_func=lambda x: "—" if x == "—" else f"{TYPE_LABEL[next(i for i in incs if i['id'] == x)['type']]} ({x})")
            if pick != "—":
                i = next(i for i in incs if i["id"] == pick)
                st.markdown(f"**{TYPE_LABEL[i['type']]}** · severity {i['severity']}/5 · {i['verification']}")
                st.write(i["description"])
                st.caption(f"{'Incident' if i['source'] == 'sample' else 'Field report ' + str(i['report_id'])} · created {fmt_time(i['created_at'])}")
