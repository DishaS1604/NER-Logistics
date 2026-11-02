"""Shared UI helpers: state access, formatting, folium map."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import folium
import streamlit as st

from core.risk import TYPE_LABEL
from core.storage import load_state, save_state

IST = ZoneInfo("Asia/Kolkata")
STATUS_COLOR = {"open": "#1f9d55", "risky": "#e0a100", "blocked": "#d64545"}
TYPE_ICON = {"landslide": "⛰️", "flood": "🌊", "heavy_rain": "🌧️", "road_damage": "🚧"}
SUPPLY = {"medicine": "Medicines", "food": "Food / essentials", "emergency": "Emergency materials"}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def get_state():
    return st.session_state["state"]


def commit():
    """Persist the current state to disk after a change."""
    save_state(st.session_state["state"])


def fmt_time(iso):
    return datetime.fromisoformat(iso).astimezone(IST).strftime("%d %b %H:%M")


def fmt_min(m):
    if m is None:
        return "Unavailable"
    m = max(0, round(m))
    return f"{m // 60} h {m % 60} m" if m >= 60 else f"{m} m"


def status_md(status):
    return {"open": ":green[**Open**]", "risky": ":orange[**Risky**]", "blocked": ":red[**Blocked**]"}[status]


def risk_md(level):
    return {"Low": ":green[**Low**]", "Medium": ":orange[**Medium**]", "High": ":orange[**High**]", "Critical": ":red[**Critical**]"}[level]


def sim_tag(text=""):
    return ""


def build_map(state, risks, views=None, status_filter="all", type_filter="all", highlight=None, selected_seg=None):
    m = folium.Map(location=[25.4, 92.6], zoom_start=7, tiles="OpenStreetMap", control_scale=True)
    highlight = set(highlight or [])
    pts = []
    for s in state["segments"]:
        if status_filter != "all" and s["status"] != status_filter:
            continue
        pts += s["path"]
        dim = bool(highlight) and s["id"] not in highlight
        big = s["id"] in highlight or s["id"] == selected_seg
        folium.PolyLine(
            s["path"], color=STATUS_COLOR[s["status"]], weight=9 if big else 5, opacity=0.25 if dim else 0.9,
            dash_array="8 8" if s["status"] == "blocked" else None,
            tooltip=f"{s['name']} · {s['status'].upper()} · risk {risks[s['id']]['level']}",
        ).add_to(m)
    from core.seed import PLACES
    for p in PLACES:
        folium.CircleMarker([p["lat"], p["lng"]], radius=5, color="#0b2545", fill=True, fill_color="#fff",
                            fill_opacity=1, tooltip=p["name"]).add_to(m)
    segs = {s["id"]: s for s in state["segments"]}
    for i in state["incidents"]:
        if i["verification"] == "rejected":
            continue
        if type_filter != "all" and i["type"] != type_filter:
            continue
        if status_filter != "all" and segs[i["segment_id"]]["status"] != status_filter:
            continue
        border = "#e0a100" if i["verification"] == "unverified" else "#0b2545"
        style = "dashed" if i["verification"] == "unverified" else "solid"
        html = (f'<div style="width:30px;height:30px;border-radius:50%;background:#fff;border:3px {style} {border};'
                f'display:flex;align-items:center;justify-content:center;font-size:15px;box-shadow:0 1px 4px #0005">{TYPE_ICON[i["type"]]}</div>')
        folium.Marker([i["lat"], i["lng"]], icon=folium.DivIcon(html=html, icon_size=(30, 30), icon_anchor=(15, 15)),
                      tooltip=f"{TYPE_LABEL[i['type']]} · severity {i['severity']} · {i['verification']}").add_to(m)
    for v in views or []:
        bad = v["disruption"].startswith("blocked")
        html = (f'<div style="background:{"#d64545" if bad else "#0b2545"};color:#fff;border-radius:6px;font-size:11px;'
                f'padding:1px 4px;white-space:nowrap;border:2px solid #fff;box-shadow:0 1px 4px #0006">🚚 {v["delivery"]["id"][-3:]}</div>')
        folium.Marker(v["position"], icon=folium.DivIcon(html=html, icon_size=(44, 22), icon_anchor=(22, 11)),
                      tooltip=f"{v['delivery']['vehicle_id']} · {v['display_status']}").add_to(m)
    if pts:
        m.fit_bounds([[min(p[0] for p in pts), min(p[1] for p in pts)], [max(p[0] for p in pts), max(p[1] for p in pts)]], padding=(20, 20))
    return m


def show_map(m, height=460, key=None):
    from streamlit_folium import st_folium
    st_folium(m, height=height, use_container_width=True, returned_objects=[], key=key)
    st.caption("🟩 open · 🟧 risky · 🟥 dashed = confirmed blocked · ⛰️🌊🌧️🚧 incidents (dashed ring = unverified) · 🚚 vehicle location. "
               "Road lines are schematic, not surveyed geometry.")
