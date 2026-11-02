"""UI workflow test using Streamlit's headless AppTest (no browser needed). Run: pytest -q"""
import os
import tempfile

os.environ["NER_STATE_FILE"] = os.path.join(tempfile.mkdtemp(), "state.json")  # isolate from the real demo data

from streamlit.testing.v1 import AppTest  # noqa: E402

APP = os.path.join(os.path.dirname(__file__), "..", "app.py")


def fresh():
    from core.storage import clear_state
    clear_state()  # every test starts from the sample data
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    assert not at.exception, at.exception
    return at


def go(at, page):
    at.sidebar.radio(key="page").set_value(page).run()
    assert not at.exception, at.exception


def click(at, label):
    next(b for b in at.button if b.label == label).click().run()
    assert not at.exception, at.exception


def text(at):
    return " ".join([m.value for m in at.markdown] + [m.value for m in at.caption] + [m.value for m in at.error] + [m.value for m in at.success])


def test_full_demo_workflow_in_ui():
    at = fresh()
    assert any(m.label == "Open roads" and m.value == "10" for m in at.metric)
    assert any(m.label == "Active deliveries" and m.value == "4" for m in at.metric)

    # invalid form -> errors, nothing saved
    go(at, "Field reports")
    click(at, "Submit report")
    assert len(at.error) >= 3
    assert "No reports yet" in text(at)

    # report -> Pending Review, road still open, route unchanged
    click(at, "Fill landslide report")
    click(at, "Submit report")
    assert "Pending Review" in text(at)
    go(at, "Route planner")
    assert any(m.value.startswith("**Guwahati → Shillong → Jowai → Silchar**") for m in at.markdown)

    # field role cannot verify
    go(at, "Field reports")
    at.sidebar.selectbox[0].set_value("Field user").run()
    assert not any(b.label == "Verify" for b in at.button)
    at.sidebar.selectbox[0].set_value("Authority (can verify)").run()

    # verify -> blocked
    click(at, "Verify")
    assert "Verified" in text(at)
    go(at, "Dashboard")
    assert any(m.label == "Blocked roads" and m.value == "1" for m in at.metric)
    assert any(m.label == "Reports pending review" and m.value == "0" for m in at.metric)

    go(at, "Route planner")
    assert any(m.value.startswith("**Guwahati → Nagaon → Lumding → Haflong → Silchar**") for m in at.markdown)
    assert "Not passable" in text(at)

    go(at, "Deliveries")
    assert "Disruption ahead" in text(at) and "Suggested reroute" in text(at)
    click(at, "Apply reroute")
    assert "Rerouted" in text(at)

    go(at, "Alerts")
    assert "Road blocked (confirmed)" in text(at) and "Recommended action" in text(at)


def test_offline_report_and_sync_in_ui():
    at = fresh()
    go(at, "Field reports")
    at.sidebar.toggle(key="sim_offline").set_value(True).run()
    click(at, "Fill landslide report")
    click(at, "Submit report")
    assert "Pending sync" in text(at) and "saved on this device" in text(at)
    st_reports = at.session_state["state"]["reports"]
    assert st_reports[0]["sync_state"] == "pending_sync"
    assert not any(i["report_id"] == st_reports[0]["id"] for i in at.session_state["state"]["incidents"])
    at.sidebar.toggle(key="sim_offline").set_value(False).run()
    s = at.session_state["state"]
    assert s["reports"][0]["sync_state"] == "synced"
    assert sum(1 for i in s["incidents"] if i["report_id"] == s["reports"][0]["id"]) == 1
    assert sum(1 for a in s["alerts"] if "synced" in a["title"]) == 1


def test_all_pages_render_and_simulation_advances():
    at = fresh()
    for p in ["Dashboard", "Road map", "Route planner", "Deliveries", "Field reports", "Alerts"]:
        go(at, p)
    before = at.session_state["state"]["deliveries"][0]["elapsed_min"]
    click(at, "Advance simulation ▶")
    assert at.session_state["state"]["deliveries"][0]["elapsed_min"] > before
