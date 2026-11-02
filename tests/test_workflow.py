"""Logic + workflow tests (no UI). Run: pytest -q"""
from core import actions as A
from core.delivery import compute_view
from core.risk import assess_segment
from core.routing import find_routes, recommend
from core.seed import PLACES, initial_state

NOW = "2026-11-02T10:00:00+00:00"


def report(**o):
    r = dict(id="R1", client_id="c1", type="landslide", severity=4, segment_id="S2", lat=25.5, lng=92.05,
             location_source="manual", occurred_at=NOW, description="Landslide on NH-6", photo=None,
             status="pending_review", sync_state="synced", submitted_at=NOW, reviewed_at=None, review_note="", incident_id=None)
    r.update(o)
    return r


def best(s):
    return recommend(find_routes(s["segments"], s["incidents"], "GUW", "SIL"), PLACES, s["segments"])


def seg(s, i):
    return next(x for x in s["segments"] if x["id"] == i)


def test_sample_risk():
    s = initial_state(NOW)
    assert assess_segment(seg(s, "S2"), s["incidents"])["level"] == "Low"
    assert assess_segment(seg(s, "S8"), s["incidents"])["level"] == "Medium"


def test_unverified_does_not_close_road():
    s = A.submit_report(initial_state(NOW), report(), True, NOW)
    a = assess_segment(seg(s, "S2"), s["incidents"])
    assert seg(s, "S2")["status"] == "open" and a["has_unverified_hazard"] and a["level"] == "Medium"
    assert best(s)[0]["nodes"] == ["GUW", "SHL", "JWI", "SIL"]


def test_end_to_end_workflow():
    s = initial_state(NOW)
    assert best(s)[0]["nodes"] == ["GUW", "SHL", "JWI", "SIL"]
    v0 = compute_view(s["deliveries"][0], s["segments"], s["incidents"])
    assert v0["disruption"] == "none" and v0["priority"]["level"] == "Medium"
    A.submit_report(s, report(), True, NOW)
    assert s["reports"][0]["status"] == "pending_review" and "Unverified" in s["alerts"][0]["title"]
    A.review_report(s, "R1", "verify", NOW, "authority", road_status="blocked")
    assert seg(s, "S2")["status"] == "blocked" and s["reports"][0]["status"] == "verified"
    assert assess_segment(seg(s, "S2"), s["incidents"])["level"] == "Critical"
    assert s["alerts"][0]["severity"] == "critical" and "DEL-101" in s["alerts"][0]["explanation"]
    rec, why = best(s)
    assert rec["nodes"] == ["GUW", "NAG", "LUM", "HAF", "SIL"] and "confirmed-blocked" in why
    v1 = compute_view(s["deliveries"][0], s["segments"], s["incidents"])
    assert v1["disruption"] == "blocked_ahead" and v1["priority"]["level"] == "High" and v1["suggestion"]
    A.apply_reroute(s, "DEL-101", NOW)
    d = s["deliveries"][0]
    assert d["rerouted"] and "blocked" not in compute_view(d, s["segments"], s["incidents"])["disruption"]
    for _ in range(400):
        A.tick(s, 10)
    assert s["deliveries"][0]["delivered"]


def test_roles_and_reject():
    s = A.submit_report(initial_state(NOW), report(), True, NOW)
    A.review_report(s, "R1", "verify", NOW, "field")
    assert s["reports"][0]["status"] == "pending_review"
    A.review_report(s, "R1", "reject", NOW, "authority")
    assert seg(s, "S2")["status"] == "open" and assess_segment(seg(s, "S2"), s["incidents"])["level"] == "Low"


def test_reopen_restores_route():
    s = A.set_segment_status(initial_state(NOW), "S2", "blocked", NOW, "authority")
    assert "SHL" not in best(s)[0]["nodes"]
    A.set_segment_status(s, "S2", "open", NOW, "authority")
    assert "SHL" in best(s)[0]["nodes"]


def test_vehicle_holds_then_turns_back():
    s = initial_state(NOW)
    s["deliveries"] = [{**s["deliveries"][0], "leg_index": 1, "leg_frac": 0.4}]
    A.set_segment_status(s, "S2", "blocked", NOW, "authority")
    before = s["deliveries"][0]["leg_frac"]
    A.tick(s, 30)
    assert s["deliveries"][0]["leg_frac"] == before
    assert compute_view(s["deliveries"][0], s["segments"], s["incidents"])["disruption"] == "blocked_here"
    A.apply_reroute(s, "DEL-101", NOW)
    for _ in range(400):
        A.tick(s, 10)
    assert s["deliveries"][0]["delivered"]


def test_offline_queue_and_dedup():
    s = A.submit_report(initial_state(NOW), report(), False, NOW)
    assert s["reports"][0]["sync_state"] == "pending_sync" and not any(i["report_id"] == "R1" for i in s["incidents"])
    A.submit_report(s, report(), False, NOW)  # double tap
    assert len(s["reports"]) == 1
    A.sync_reports(s, NOW)
    A.sync_reports(s, NOW)
    assert s["reports"][0]["sync_state"] == "synced"
    assert sum(1 for i in s["incidents"] if i["report_id"] == "R1") == 1
    assert sum(1 for a in s["alerts"] if "synced" in a["title"]) == 1


def test_storage_roundtrip(tmp_path):
    from core.storage import load_state, save_state
    s = initial_state(NOW)
    A.submit_report(s, report(), True, NOW)
    p = tmp_path / "s.json"
    save_state(s, p)
    assert load_state(NOW, p) == s
