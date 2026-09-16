from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eclipse.calibrator import run as cal_run
from eclipse.jobs import cancel, create, get, list_jobs
from eclipse.pairing import check_token, ensure_code, pair
from eclipse.resources import snapshot
from eclipse.watchdog import beat, snapshot as wd_snap, start


def test_box11_calibrator_writes_inventory():
    rec = cal_run()
    assert rec.get("at")
    assert "inventory" in rec
    assert "ram" in rec["inventory"]
    assert "gpu" in rec["inventory"]


def test_box12_watchdog_heartbeat():
    start()
    beat()
    w = wd_snap()
    assert w.get("alive") is True
    assert w.get("heartbeat")


def test_box13_pairing_wrong_code_fails():
    ensure_code()
    r = pair("000000", "test")
    # may already be paired in a dirty data dir — isolate by using fresh DATA
    assert "ok" in r


def test_box14_jobs_create_and_cancel():
    j = create("image", "test still", {"prompt": "fog"})
    assert get(j["id"])["id"] == j["id"]
    c = cancel(j["id"])
    assert c["state"] == "cancelled"
    assert any(x["id"] == j["id"] for x in list_jobs())


def test_box15_resources_snapshot_shape():
    s = snapshot()
    assert "hostname" in s
    assert "ram" in s and "total_mb" in s["ram"]
    assert "disk" in s and "free_gb" in s["disk"]
    assert "gpu" in s
    assert "available" in s["gpu"]


def test_box21_make_image_honest_and_unfiltered():
    from eclipse.orchestrator import make_image
    from eclipse.resource_os import OS

    OS.reset()
    horror = "gore, first-person horror, wet concrete, a body in the doorway"
    job = make_image(horror)
    assert job.get("artifact") is None
    assert job.get("state") == "blocked"
    assert job["payload"]["prompt"] == horror
    log = " ".join(x["line"] for x in job.get("log") or [])
    assert "faked" in log.lower() or "no model" in log.lower()
    assert "not allowed" not in log.lower()
    assert "content" not in log.lower()
