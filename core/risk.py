"""Transparent RULE-BASED risk scoring. This is NOT a trained AI model.
To plug in a validated model later, replace `assess_segment` (keep the return shape)."""

TYPE_LABEL = {"landslide": "Landslide", "flood": "Flood", "heavy_rain": "Heavy rainfall", "road_damage": "Road damage"}
TYPE_WEIGHT = {"landslide": 8, "flood": 7, "road_damage": 5, "heavy_rain": 4}  # points per severity step
VERIFY_FACTOR = {"verified": 1.0, "unverified": 0.6, "rejected": 0.0}
STATUS_POINTS = {"open": 0, "risky": 15, "blocked": 40}
LEVEL_ORDER = ["Low", "Medium", "High", "Critical"]


def level_from_score(score):
    if score >= 60:
        return "Critical"
    if score >= 35:
        return "High"
    if score >= 15:
        return "Medium"
    return "Low"


def max_level(a, b):
    return a if LEVEL_ORDER.index(a) >= LEVEL_ORDER.index(b) else b


def assess_segment(seg, incidents):
    reasons, score, unverified = [], 0, False
    for inc in incidents:
        if inc["segment_id"] != seg["id"] or inc["verification"] == "rejected":
            continue
        pts = round(TYPE_WEIGHT[inc["type"]] * inc["severity"] * VERIFY_FACTOR[inc["verification"]])
        score += pts
        if inc["verification"] == "unverified":
            unverified = True
        reasons.append(f"{TYPE_LABEL[inc['type']]}, severity {inc['severity']}/5, {inc['verification']}: +{pts}")
    sp = STATUS_POINTS[seg["status"]]
    if sp:
        score += sp
        reasons.append(f'Confirmed road status "{seg["status"]}": +{sp}')
    if unverified and seg["status"] == "open":
        reasons.append("Hazard is unverified: it raises risk but the road is NOT treated as closed until an authority confirms.")
    if not reasons:
        reasons.append("No active incidents and road status is open.")
    return {"score": score, "level": level_from_score(score), "reasons": reasons,
            "has_unverified_hazard": unverified, "confirmed_status": seg["status"]}


def assess_all(segments, incidents):
    return {s["id"]: assess_segment(s, incidents) for s in segments}
