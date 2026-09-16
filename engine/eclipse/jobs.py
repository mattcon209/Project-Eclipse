from __future__ import annotations

import time
import uuid
from typing import Any

from eclipse.config import DATA_DIR
from eclipse.store import JsonStore

_store = JsonStore(DATA_DIR / "jobs.json", {"jobs": []})


def list_jobs() -> list[dict[str, Any]]:
    return list(_store.read().get("jobs") or [])


def get(job_id: str) -> dict[str, Any] | None:
    for j in list_jobs():
        if j["id"] == job_id:
            return j
    return None


def create(kind: str, title: str, payload: dict | None = None) -> dict[str, Any]:
    job = {
        "id": uuid.uuid4().hex[:12],
        "kind": kind,
        "title": title,
        "state": "queued",
        "progress": 0,
        "log": [],
        "payload": payload or {},
        "created": time.time(),
        "updated": time.time(),
        "error": None,
        "artifact": None,
    }
    data = _store.read()
    data["jobs"].insert(0, job)
    data["jobs"] = data["jobs"][:200]
    _store.write(data)
    return job


def append_log(job_id: str, line: str, state: str | None = None, progress: int | None = None) -> dict | None:
    data = _store.read()
    for j in data["jobs"]:
        if j["id"] == job_id:
            j["log"].append({"t": time.time(), "line": line})
            j["updated"] = time.time()
            if state:
                j["state"] = state
            if progress is not None:
                j["progress"] = progress
            _store.write(data)
            return j
    return None


def cancel(job_id: str) -> dict | None:
    return append_log(job_id, "Cancelled.", state="cancelled")
