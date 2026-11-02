"""All state changes live here (mirrors the TypeScript reducer). Each function mutates and returns the state dict.
Replace the bodies with API calls when a backend exists."""
import uuid

from .delivery import advance_delivery, compute_view
from .risk import TYPE_LABEL, assess_segment
from .seed import initial_state, place_name


def push_alert(state, **a):
    a.setdefault("incident_type", None)
    state["alerts"].insert(0, {"id": "AL-" + uuid.uuid4().hex[:8], **a})
    del state["alerts"][60:]


def _seg(state, sid):
    return next(s for s in state["segments"] if s["id"] == sid)


def _report(state, rid):
    return next((r for r in state["reports"] if r["id"] == rid), None)


def affected_delivery_ids(state, seg_id):
    return [d["id"] for d in state["deliveries"] if not d["delivered"]
            and seg_id in compute_view(d, state["segments"], state["incidents"])["remaining_segment_ids"]]


def _register_report(state, r, now):
    """Add an UNVERIFIED incident + alert for a report that has reached the 'server'. Idempotent."""
    if any(i["report_id"] == r["id"] for i in state["incidents"]):
        return
    inc = {"id": f"INC-{r['id']}", "type": r["type"], "severity": r["severity"], "segment_id": r["segment_id"],
           "lat": r["lat"], "lng": r["lng"], "description": r["description"], "verification": "unverified",
           "source": "field_report", "report_id": r["id"], "created_at": now}
    state["incidents"].append(inc)
    r["incident_id"] = inc["id"]
    seg = _seg(state, r["segment_id"])
    label = TYPE_LABEL[r["type"]].lower()
    push_alert(state, time=now, severity="warning", kind="report", incident_type=r["type"],
               title=f"Unverified {label} report", location=seg["name"],
               explanation=(f"A field user reported a {label} (severity {r['severity']}/5). It is a POTENTIAL hazard: risk was "
                            f'raised, but the road stays "{seg["status"]}" until an authority verifies it.'),
               action="Authority: review the report and confirm or reject it.")


def submit_report(state, report, online, now):
    if any(r["client_id"] == report["client_id"] for r in state["reports"]):
        return state  # duplicate-submit guard
    report = {**report, "sync_state": "synced" if online else "pending_sync"}
    state["reports"].insert(0, report)
    if not online:
        push_alert(state, time=now, severity="info", kind="sync", title="Report saved on device (offline)",
                   location=place_name(_seg(state, report["segment_id"])["from"]),
                   explanation="No connection. The report is stored locally and does not affect road risk yet.",
                   action="It will sync automatically when the connection returns.")
        return state
    _register_report(state, report, now)
    return state


def sync_reports(state, now):
    pending = [r for r in state["reports"] if r["sync_state"] == "pending_sync"]
    if not pending:
        return state
    for r in pending:
        r["sync_state"] = "synced"
        _register_report(state, r, now)
    push_alert(state, time=now, severity="info", kind="sync", title=f"{len(pending)} offline report(s) synced",
               location="Field reports",
               explanation="Locally saved reports were submitted once each (duplicates are ignored by report ID).",
               action="Authority: review the new pending reports.")
    return state


def _status_alert(state, seg_id, prev, now, rtype=None):
    seg = _seg(state, seg_id)
    risk = assess_segment(seg, state["incidents"])
    ids = affected_delivery_ids(state, seg_id)
    sev = "critical" if seg["status"] == "blocked" else "warning" if seg["status"] == "risky" else "info"
    title = (f"Road blocked (confirmed): {seg['name']}" if seg["status"] == "blocked"
             else f"Road status changed to {seg['status']}: {seg['name']}")
    affected = f"Affected deliveries: {', '.join(ids)}." if ids else "No active deliveries use this road."
    if seg["status"] == "blocked":
        action = (f"Review suggested reroutes for {', '.join(ids)} on the Deliveries page; check the Route planner."
                  if ids else "Update route plans; no active deliveries affected.")
    elif seg["status"] == "risky":
        action = "Advise drivers to proceed with caution."
    else:
        action = "Road reopened: re-check route recommendations."
    push_alert(state, time=now, severity=sev, kind="status", incident_type=rtype, title=title, location=seg["name"],
               explanation=f"Confirmed status changed {prev} → {seg['status']}. Rule-based risk is now {risk['level']} "
                           f"(score {risk['score']}). {affected}", action=action)


def review_report(state, rid, decision, now, role, road_status=None, note=""):
    if role != "authority":
        return state
    r = _report(state, rid)
    if not r or r["status"] != "pending_review" or r["sync_state"] != "synced":
        return state
    seg = _seg(state, r["segment_id"])
    inc = next((i for i in state["incidents"] if i["report_id"] == rid), None)
    r["reviewed_at"], r["review_note"] = now, note
    if decision == "reject":
        r["status"] = "rejected"
        if inc:
            inc["verification"] = "rejected"
        push_alert(state, time=now, severity="info", kind="report", incident_type=r["type"], title="Field report rejected",
                   location=seg["name"], explanation="The report was rejected. Road status and risk were not increased by it.",
                   action="No action needed.")
        return state
    status = road_status or ("blocked" if r["severity"] >= 4 else "risky")
    prev = seg["status"]
    r["status"] = "verified"
    if inc:
        inc["verification"] = "verified"
    seg.update(status=status, status_updated_at=now, status_note=f"Verified from report {rid}")
    _status_alert(state, seg["id"], prev, now, r["type"])
    return state


def set_segment_status(state, seg_id, status, now, role):
    if role != "authority":
        return state
    seg = _seg(state, seg_id)
    if seg["status"] == status:
        return state
    prev = seg["status"]
    seg.update(status=status, status_updated_at=now, status_note="Set manually by authority (demo)")
    _status_alert(state, seg_id, prev, now)
    return state


def tick(state, dt_min):
    state["deliveries"] = [advance_delivery(d, state["segments"], dt_min) for d in state["deliveries"]]
    return state


def apply_reroute(state, delivery_id, now):
    d = next((x for x in state["deliveries"] if x["id"] == delivery_id), None)
    if not d:
        return state
    g = compute_view(d, state["segments"], state["incidents"])["suggestion"]
    if not g:
        return state
    d.update(nodes=g["nodes"], leg_index=g["leg_index"], leg_frac=g["leg_frac"], returning=g["returning"], rerouted=True)
    push_alert(state, time=now, severity="info", kind="delivery", title=f"Reroute applied: {d['id']}", location=d["vehicle_id"],
               explanation=f"{g['note']} New estimated remaining time {round(g['est_remaining_min'])} min (estimate).",
               action="Monitor the vehicle on the Deliveries page.")
    return state


def reset(now):
    return initial_state(now)
