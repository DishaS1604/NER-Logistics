import base64
import io
import uuid
from datetime import datetime, time as dtime

import streamlit as st
from PIL import Image

from core import actions as A
from core.geo import distance_to_path_km
from core.risk import TYPE_LABEL
from views.common import IST, commit, fmt_time, get_state, now_iso


def _shrink(uploaded):
    """Shrink photo to a small JPEG data URL so state stays small."""
    img = Image.open(uploaded).convert("RGB")
    img.thumbnail((480, 480))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=60)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def _nearest(state, lat, lng):
    best, bd = None, 1e9
    for g in state["segments"]:
        d = distance_to_path_km([lat, lng], g["path"])
        if d < bd:
            best, bd = g["id"], d
    return best if bd < 40 else None


def _fill_demo():
    n = st.session_state["form_n"]
    st.session_state.update({f"type_{n}": "landslide", f"sev_{n}": 4, f"lat_{n}": "25.50", f"lng_{n}": "92.05",
                             f"desc_{n}": "Landslide debris covering both lanes near Shillong–Jowai. Vehicles cannot pass."})


def render(role, online):
    s = get_state()
    st.header("Field reports")
    n = st.session_state.setdefault("form_n", 0)  # bumping n resets all form widgets
    segs = {g["id"]: g for g in s["segments"]}
    left, right = st.columns(2)

    with left:
        st.subheader("Submit a field report")
        st.markdown(":green-badge[Online]" if online else ":red-badge[Offline – will save on this device]")
        st.button("Fill landslide report", on_click=_fill_demo)
        typ = st.selectbox("Hazard type", list(TYPE_LABEL), format_func=TYPE_LABEL.get, key=f"type_{n}")
        sev = st.selectbox("Severity (1 minor – 5 severe)", [1, 2, 3, 4, 5], index=2, key=f"sev_{n}")
        c1, c2 = st.columns(2)
        lat_s = c1.text_input("Latitude", placeholder="25.50", key=f"lat_{n}")
        lng_s = c2.text_input("Longitude", placeholder="92.05", key=f"lng_{n}")
        source = "manual"
        try:  # optional browser GPS (needs `pip install streamlit-geolocation`); manual entry is the fallback
            from streamlit_geolocation import streamlit_geolocation
            with st.expander("Use my GPS location (optional)"):
                loc = streamlit_geolocation()
            if loc and loc.get("latitude") and not lat_s:
                lat_s, lng_s, source = f"{loc['latitude']:.5f}", f"{loc['longitude']:.5f}", "gps"
                st.caption(f"GPS captured: {lat_s}, {lng_s} — copy these into the fields above to use them.")
        except ImportError:
            st.caption("GPS capture needs the optional `streamlit-geolocation` package; enter the location manually.")
        guess = None
        try:
            guess = _nearest(s, float(lat_s), float(lng_s))
        except ValueError:
            pass
        opts = ["auto"] + list(segs)
        seg_choice = st.selectbox("Affected road", opts, key=f"seg_{n}",
                                  format_func=lambda i: f"Auto: nearest to location ({segs[guess]['name'] if guess else 'enter location first'})" if i == "auto" else segs[i]["name"])
        d_in = st.date_input("Date observed", datetime.now(IST).date(), key=f"date_{n}")
        t_in = st.time_input("Time observed", datetime.now(IST).time().replace(second=0, microsecond=0), key=f"time_{n}")
        desc = st.text_area("Description", placeholder="What did you see?", key=f"desc_{n}")
        photo = st.file_uploader("Photo (optional)", type=["jpg", "jpeg", "png"], key=f"photo_{n}")

        if st.button("Submit report", type="primary"):
            errs = []
            try:
                lat, lng = float(lat_s), float(lng_s)
                if not (20 <= lat <= 30):
                    errs.append("Latitude must be between 20 and 30 (Northeast India).")
                if not (86 <= lng <= 98):
                    errs.append("Longitude must be between 86 and 98 (Northeast India).")
            except ValueError:
                lat = lng = 0.0
                errs.append("Latitude and longitude must be numbers.")
            seg_id = guess if seg_choice == "auto" else seg_choice
            if not seg_id:
                errs.append("Select the affected road (or enter a location near one).")
            if len(desc.strip()) < 10:
                errs.append("Description must be at least 10 characters.")
            img = None
            if photo is not None:
                try:
                    img = _shrink(photo)
                except Exception:
                    errs.append("That file is not a readable image.")
            if errs:
                for e in errs:
                    st.error(e)
            else:
                now = now_iso()
                rep = {"id": "R-" + uuid.uuid4().hex[:8], "client_id": "c-" + uuid.uuid4().hex, "type": typ, "severity": sev,
                       "segment_id": seg_id, "lat": lat, "lng": lng, "location_source": source,
                       "occurred_at": datetime.combine(d_in, t_in, tzinfo=IST).isoformat(), "description": desc.strip(),
                       "photo": img, "status": "pending_review", "sync_state": "synced" if online else "pending_sync",
                       "submitted_at": now, "reviewed_at": None, "review_note": "", "incident_id": None}
                A.submit_report(s, rep, online, now)
                commit()
                st.session_state["form_msg"] = ("Report submitted. Status: Pending Review." if online else
                                                "You are offline. Report saved on this device and will sync when you are back online.")
                st.session_state["form_n"] = n + 1
                st.rerun()
        if st.session_state.get("form_msg"):
            st.success(st.session_state.pop("form_msg"))
        st.caption("A report never closes a road by itself; an authority must verify it.")

    with right:
        st.subheader("Report list")
        if not s["reports"]:
            st.caption("No reports yet.")
        for r in s["reports"]:
            g = segs[r["segment_id"]]
            with st.container(border=True):
                badge = {"pending_review": ":orange-badge[Pending Review]", "verified": ":green-badge[Verified]", "rejected": ":red-badge[Rejected]"}[r["status"]]
                sync = " :blue-badge[Pending sync (on device)]" if r["sync_state"] == "pending_sync" else ""
                st.markdown(f"**{TYPE_LABEL[r['type']]} · {g['name']}**  {badge}{sync}")
                st.caption(f"Severity {r['severity']}/5 · {r['lat']:.3f}, {r['lng']:.3f} ({'GPS' if r['location_source'] == 'gps' else 'manual'}) · "
                           f"observed {fmt_time(r['occurred_at'])} · submitted {fmt_time(r['submitted_at'])}")
                st.write(r["description"])
                if r.get("photo"):
                    st.image(base64.b64decode(r["photo"].split(",", 1)[1]), width=160)
                if r["status"] == "pending_review" and r["sync_state"] == "synced":
                    if role == "authority":
                        dflt = ["open", "risky", "blocked"].index("blocked" if r["severity"] >= 4 else "risky")
                        new_status = st.selectbox("If verified, set road to", ["open", "risky", "blocked"], index=dflt, key=f"rs_{r['id']}")
                        note = st.text_input("Review note (optional)", key=f"note_{r['id']}")
                        b1, b2 = st.columns(2)
                        if b1.button("Verify", key=f"ver_{r['id']}", type="primary"):
                            A.review_report(s, r["id"], "verify", now_iso(), role, new_status, note)
                            commit()
                            st.rerun()
                        if b2.button("Reject", key=f"rej_{r['id']}"):
                            A.review_report(s, r["id"], "reject", now_iso(), role, None, note)
                            commit()
                            st.rerun()
                    else:
                        st.caption("Switch role to Authority (sidebar) to review this report.")
                if r.get("review_note"):
                    st.caption("Review note: " + r["review_note"])
