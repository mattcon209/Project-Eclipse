from __future__ import annotations

import time
import uuid
from pathlib import Path
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


def update(job_id: str, **fields: Any) -> dict | None:
    data = _store.read()
    for j in data["jobs"]:
        if j["id"] == job_id:
            j.update(fields)
            j["updated"] = time.time()
            _store.write(data)
            return j
    return None


def cancel(job_id: str) -> dict | None:
    return append_log(job_id, "Cancelled.", state="cancelled")


def remove(job_id: str) -> dict[str, Any] | None:
    data = _store.read()
    found: dict[str, Any] | None = None
    kept: list[dict[str, Any]] = []
    for j in data.get("jobs") or []:
        if j.get("id") == job_id:
            found = j
        else:
            kept.append(j)
    if not found:
        return None
    _unlink_still(found.get("artifact"))
    data["jobs"] = kept
    _store.write(data)
    return found


def _unlink_still(artifact: Any) -> None:
    if not artifact:
        return
    path = Path(str(artifact))
    try:
        resolved = path.resolve()
        stills = (Path(DATA_DIR) / "stills").resolve()
        if resolved.is_file() and resolved.parent == stills:
            resolved.unlink()
    except OSError:
        pass
