"""Delivery simulation, disruption detection, reroute suggestion and transparent prioritisation."""
from .geo import point_along
from .risk import LEVEL_ORDER, assess_segment, max_level
from .routing import find_routes, recommend, segment_between
from .seed import PLACES


def _leg_min(s):
    return s["distance_km"] / s["speed_kmh"] * 60


def advance_delivery(d, segments, dt_min):
    """SIMULATION ONLY: moves a vehicle along its route. Not GPS."""
    if d["delivered"]:
        return d
    d = dict(d)
    left = dt_min
    while left > 0 and d["leg_index"] < len(d["nodes"]) - 1:
        s = segment_between(segments, d["nodes"][d["leg_index"]], d["nodes"][d["leg_index"] + 1])
        can_turn_back = d["returning"] and d["leg_index"] == 0
        if s["status"] == "blocked" and not can_turn_back:
            break  # vehicle holds before/inside a blocked road
        lm = _leg_min(s)
        to_end = (1 - d["leg_frac"]) * lm
        if left >= to_end:
            left -= to_end
            d["leg_index"] += 1
            d["leg_frac"] = 0.0
            d["returning"] = False
        else:
            d["leg_frac"] += left / lm
            left = 0
    if d["leg_index"] >= len(d["nodes"]) - 1:
        d["delivered"], d["leg_frac"] = True, 0.0
    d["elapsed_min"] += dt_min
    return d


def position_of(d, segments):
    if d["delivered"]:
        p = next(p for p in PLACES if p["id"] == d["nodes"][-1])
        return [p["lat"], p["lng"]]
    a, b = d["nodes"][d["leg_index"]], d["nodes"][d["leg_index"] + 1]
    s = segment_between(segments, a, b)
    path = s["path"] if s["from"] == a else list(reversed(s["path"]))
    return point_along(path, d["leg_frac"])


def suggest_reroute(d, segments, incidents):
    a0, a1 = d["nodes"][d["leg_index"]], d["nodes"][d["leg_index"] + 1]
    s = segment_between(segments, a0, a1)
    lm = _leg_min(s)
    dest = d["destination"]
    cands = []

    def add(route, nodes, leg_frac, returning, rem, note):
        cands.append({"nodes": nodes, "leg_index": 0, "leg_frac": leg_frac, "returning": returning,
                      "est_remaining_min": rem, "est_delay_min": d["elapsed_min"] + rem - d["planned_total_min"],
                      "route": route, "note": note})

    if s["status"] != "blocked":  # (b) continue to next junction, then divert
        r, _ = recommend(find_routes(segments, incidents, a1, dest, [a0]), PLACES, segments)
        if r:
            add(r, [a0] + r["nodes"], d["leg_frac"], False, (1 - d["leg_frac"]) * lm + r["time_min"],
                "Continue to the next junction, then divert.")
    r2, _ = recommend(find_routes(segments, incidents, a0, dest), PLACES, segments)  # (a) turn back
    if r2 and r2["nodes"][1] != a1:
        add(r2, [a1, a0] + r2["nodes"][1:], 1 - d["leg_frac"], True, d["leg_frac"] * lm + r2["time_min"],
            "Turn back to the previous junction, then divert.")
    cands.sort(key=lambda c: c["est_remaining_min"])
    return cands[0] if cands else None


def compute_view(d, segments, incidents):
    position = position_of(d, segments)
    if d["delivered"]:
        return {"delivery": d, "position": position, "remaining_km": 0, "eta_min": 0,
                "delay_min": d["elapsed_min"] - d["planned_total_min"], "disruption": "delivered",
                "blocked_segment_id": None, "worst_risk": "Low", "display_status": "Delivered", "suggestion": None,
                "priority": {"score": 0, "level": "Normal", "reasons": ["Delivered"]}, "remaining_segment_ids": []}
    remaining_km = rem_min = 0.0
    worst, blocked_id, rem_ids = "Low", None, []
    for i in range(d["leg_index"], len(d["nodes"]) - 1):
        s = segment_between(segments, d["nodes"][i], d["nodes"][i + 1])
        frac = 1 - d["leg_frac"] if i == d["leg_index"] else 1
        remaining_km += s["distance_km"] * frac
        rem_min += _leg_min(s) * frac
        rem_ids.append(s["id"])
        worst = max_level(worst, assess_segment(s, incidents)["level"])
        turning_back_here = i == d["leg_index"] and d["returning"]
        if s["status"] == "blocked" and blocked_id is None and not turning_back_here:
            blocked_id = s["id"]
    cur = segment_between(segments, d["nodes"][d["leg_index"]], d["nodes"][d["leg_index"] + 1])
    disruption = "none"
    if blocked_id:
        disruption = "blocked_here" if blocked_id == cur["id"] else "blocked_ahead"
    elif LEVEL_ORDER.index(worst) >= LEVEL_ORDER.index("High"):
        disruption = "risk_ahead"
    eta = None if blocked_id else rem_min
    delay = None if eta is None else d["elapsed_min"] + eta - d["planned_total_min"]
    suggestion = suggest_reroute(d, segments, incidents) if blocked_id else None

    reasons, score = [], 0
    urg = {"medicine": 40, "emergency": 40, "food": 20}[d["supply"]]
    score += urg
    reasons.append(f"{ {'food': 'Food/essential supplies', 'medicine': 'Medical supplies', 'emergency': 'Emergency materials'}[d['supply']] }: +{urg}")
    rp = {"Low": 0, "Medium": 10, "High": 25, "Critical": 40}[worst]
    if rp:
        score += rp
        reasons.append(f"Worst remaining road risk {worst}: +{rp}")
    if blocked_id:
        score += 30
        reasons.append("A confirmed-blocked road is on the remaining route: +30")
    if delay is not None and delay > 60:
        score += 20
        reasons.append("Estimated delay over 60 min: +20")
    elif delay is not None and delay > 0:
        score += 10
        reasons.append("Estimated delay: +10")
    level = "High" if score >= 70 else "Medium" if score >= 40 else "Normal"
    status = ("Held – road blocked" if disruption == "blocked_here" else
              "Disruption ahead" if disruption == "blocked_ahead" else
              "Rerouted – in transit" if d["rerouted"] else
              "In transit – high risk ahead" if disruption == "risk_ahead" else "In transit")
    return {"delivery": d, "position": position, "remaining_km": remaining_km, "eta_min": eta, "delay_min": delay,
            "disruption": disruption, "blocked_segment_id": blocked_id, "worst_risk": worst, "display_status": status,
            "suggestion": suggestion, "priority": {"score": score, "level": level, "reasons": reasons},
            "remaining_segment_ids": rem_ids}
