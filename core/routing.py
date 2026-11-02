"""Route enumeration + recommendation over the small SAMPLE road network.
Replace `find_routes` with a real routing service later; keep the route dict shape."""
from .risk import assess_segment, max_level

RISK_PENALTY = {"Low": 0.0, "Medium": 0.05, "High": 0.25, "Critical": 0.6}
INF = float("inf")


def segment_between(segments, a, b):
    for s in segments:
        if (s["from"] == a and s["to"] == b) or (s["from"] == b and s["to"] == a):
            return s
    return None


def build_route(segments, incidents, nodes):
    seg_ids, dist, minutes, level, blocked, warnings = [], 0.0, 0.0, "Low", [], []
    for i in range(len(nodes) - 1):
        s = segment_between(segments, nodes[i], nodes[i + 1])
        if s is None:
            return None
        seg_ids.append(s["id"])
        dist += s["distance_km"]
        minutes += s["distance_km"] / s["speed_kmh"] * 60
        a = assess_segment(s, incidents)
        level = max_level(level, a["level"])
        if s["status"] == "blocked":
            blocked.append(s["id"])
        if a["level"] != "Low" or s["status"] != "open":
            warnings.append({"segment_id": s["id"], "segment_name": s["name"], "level": a["level"], "reasons": a["reasons"]})
    passable = not blocked
    return {"nodes": list(nodes), "segment_ids": seg_ids, "distance_km": dist, "time_min": minutes,
            "risk_level": level, "passable": passable, "blocked_segments": blocked, "warnings": warnings,
            "cost": minutes * (1 + RISK_PENALTY[level]) if passable else INF}


def find_routes(segments, incidents, frm, to, avoid=(), max_routes=5):
    if frm == to:
        return []
    found = []

    def dfs(cur, path):
        if len(path) > 8:
            return
        if cur == to:
            found.append(path)
            return
        for s in segments:
            nxt = s["to"] if s["from"] == cur else s["from"] if s["to"] == cur else None
            if nxt is None or nxt in path or nxt in avoid:
                continue
            dfs(nxt, path + [nxt])

    dfs(frm, [frm])
    routes = [r for r in (build_route(segments, incidents, n) for n in found) if r]
    routes.sort(key=lambda r: (not r["passable"], r["cost"] if r["passable"] else r["time_min"]))
    return routes[:max_routes]


def route_label(nodes, places):
    names = {p["id"]: p["name"] for p in places}
    return " → ".join(names.get(n, n) for n in nodes)


def recommend(routes, places, segments):
    """Returns (best passable route or None, explanation text)."""
    if not routes:
        return None, "No route exists between these places in the road network."
    passable = [r for r in routes if r["passable"]]
    if not passable:
        return None, "No passable route: every route in the road network includes a confirmed-blocked road."
    rec = passable[0]
    fastest = min(routes, key=lambda r: r["time_min"])
    name = {s["id"]: s["name"] for s in segments}
    if fastest is rec:
        why = f"Shortest estimated time among passable routes (risk-adjusted). Worst risk on this route: {rec['risk_level']}."
    elif not fastest["passable"]:
        blocked = ", ".join(name[b] for b in fastest["blocked_segments"])
        why = (f"The shortest route ({route_label(fastest['nodes'], places)}) is not recommended because it includes a "
               f"confirmed-blocked road: {blocked}. This route is the best passable option.")
    else:
        pct = round(RISK_PENALTY[fastest["risk_level"]] * 100)
        why = (f"The fastest route ({route_label(fastest['nodes'], places)}, risk {fastest['risk_level']}) loses once a "
               f"{pct}% risk penalty is added to its time; this route has lower risk-adjusted time.")
    return rec, why + " Times are estimates; no route is guaranteed safe."
