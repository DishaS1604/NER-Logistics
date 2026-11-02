"""SAMPLE DATA ONLY. Places are real towns (approximate coordinates). Distances, speeds, incidents,
vehicles and road statuses are invented for demonstration and are NOT live or verified."""
from .routing import segment_between

PLACES = [
    {"id": "GUW", "name": "Guwahati", "lat": 26.1445, "lng": 91.7362},
    {"id": "SHL", "name": "Shillong", "lat": 25.5788, "lng": 91.8933},
    {"id": "JWI", "name": "Jowai", "lat": 25.434, "lng": 92.205},
    {"id": "SIL", "name": "Silchar", "lat": 24.8333, "lng": 92.7795},
    {"id": "NAG", "name": "Nagaon", "lat": 26.35, "lng": 92.683},
    {"id": "LUM", "name": "Lumding", "lat": 25.75, "lng": 93.17},
    {"id": "HAF", "name": "Haflong", "lat": 25.1667, "lng": 93.0167},
    {"id": "AIZ", "name": "Aizawl", "lat": 23.7271, "lng": 92.7176},
    {"id": "DIM", "name": "Dimapur", "lat": 25.9044, "lng": 93.7267},
    {"id": "KOH", "name": "Kohima", "lat": 25.6751, "lng": 94.1086},
]
_P = {p["id"]: p for p in PLACES}


def place_name(pid):
    return _P[pid]["name"] if pid in _P else pid


def _pt(pid):
    return [_P[pid]["lat"], _P[pid]["lng"]]


def _seg(sid, frm, to, dist, speed, via, now):
    return {"id": sid, "name": f"{place_name(frm)}–{place_name(to)}", "from": frm, "to": to,
            "distance_km": dist, "speed_kmh": speed, "status": "open", "status_note": "",
            "status_updated_at": now, "path": [_pt(frm)] + via + [_pt(to)]}  # SCHEMATIC line


def make_segments(now):
    segs = [
        _seg("S1", "GUW", "SHL", 100, 40, [[26.0, 91.85], [25.75, 91.9]], now),
        _seg("S2", "SHL", "JWI", 65, 35, [[25.5, 92.05]], now),
        _seg("S3", "JWI", "SIL", 210, 40, [[25.15, 92.35], [24.95, 92.55]], now),
        _seg("S4", "GUW", "NAG", 125, 50, [[26.25, 92.2]], now),
        _seg("S5", "NAG", "LUM", 80, 45, [[26.05, 92.95]], now),
        _seg("S6", "LUM", "HAF", 100, 35, [[25.45, 93.1]], now),
        _seg("S7", "HAF", "SIL", 110, 35, [[25.0, 92.4]], now),
        _seg("S8", "SIL", "AIZ", 180, 30, [[24.3, 92.75]], now),
        _seg("S9", "GUW", "DIM", 290, 50, [[26.55, 92.4], [26.45, 93.5]], now),
        _seg("S10", "DIM", "KOH", 74, 30, [[25.8, 93.9]], now),
        _seg("S11", "LUM", "DIM", 105, 40, [[25.85, 93.45]], now),
    ]
    for s in segs:
        if s["id"] == "S8":
            s["status"], s["status_note"] = "risky", "Heavy rainfall advisory"
    return segs


def make_incidents(now):
    base = {"verification": "verified", "source": "sample", "created_at": now, "report_id": None}
    return [
        {**base, "id": "INC-S1", "type": "heavy_rain", "severity": 2, "segment_id": "S8", "lat": 24.3, "lng": 92.75,
         "description": "Heavy rainfall on the Silchar–Aizawl road."},
        {**base, "id": "INC-S2", "type": "road_damage", "severity": 3, "segment_id": "S6", "lat": 25.45, "lng": 93.1,
         "description": "Damaged road surface near Lumding–Haflong."},
        {**base, "id": "INC-S3", "type": "flood", "severity": 3, "segment_id": "S9", "lat": 26.45, "lng": 93.5,
         "description": "Waterlogging on the Guwahati–Dimapur road."},
    ]


def plan_minutes(nodes, segments):
    t = 0.0
    for i in range(len(nodes) - 1):
        s = segment_between(segments, nodes[i], nodes[i + 1])
        t += s["distance_km"] / s["speed_kmh"] * 60
    return t


def make_delivery(did, vehicle, supply, cargo, nodes, leg_index, leg_frac, segments):
    elapsed = sum(plan_minutes([nodes[i], nodes[i + 1]], segments) for i in range(leg_index))
    elapsed += leg_frac * plan_minutes([nodes[leg_index], nodes[leg_index + 1]], segments)
    return {"id": did, "vehicle_id": vehicle, "supply": supply, "cargo": cargo, "destination": nodes[-1],
            "nodes": nodes, "leg_index": leg_index, "leg_frac": leg_frac, "elapsed_min": elapsed,
            "planned_total_min": plan_minutes(nodes, segments), "rerouted": False, "returning": False,
            "delivered": False}


def initial_state(now):
    segs = make_segments(now)
    return {
        "segments": segs,
        "incidents": make_incidents(now),
        "reports": [],
        "alerts": [{"id": "AL-0", "time": now, "severity": "info", "kind": "system", "title": "System initialized",
                    "incident_type": None, "location": "All roads",
                    "explanation": "Active roads, incidents and delivery vehicles loaded.",
                    "action": "Submit a field report or monitor operations."}],
        "deliveries": [
            make_delivery("DEL-101", "AS-01-MED-4821", "medicine", "Essential medicines (cold chain)", ["GUW", "SHL", "JWI", "SIL"], 0, 0.1, segs),
            make_delivery("DEL-102", "AS-11-FD-2207", "food", "Rice and dal relief stock", ["SIL", "AIZ"], 0, 0.3, segs),
            make_delivery("DEL-103", "MZ-01-EM-9013", "emergency", "Emergency shelter kits", ["GUW", "DIM", "KOH"], 0, 0.15, segs),
            make_delivery("DEL-104", "NL-07-MED-1180", "medicine", "Vaccines and IV fluids", ["DIM", "KOH"], 0, 0.5, segs),
        ],
    }
