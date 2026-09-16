from __future__ import annotations

import time
from typing import Any

from eclipse.config import DATA_DIR, PROJECT_DEFAULT
from eclipse.jobs import append_log, create as create_job
from eclipse.pass_through import unchanged
from eclipse.resource_os import OS
from eclipse.store import JsonStore

_state = JsonStore(
    DATA_DIR / "session.json",
    {
        "project": PROJECT_DEFAULT,
        "mode": None,
        "mode_entered": None,
        "loaded": None,
        "ladder": "balanced",
        "seed_lock": True,
        "seed": 441029,
    },
)


def session() -> dict[str, Any]:
    data = _state.read()
    data["kpis"] = OS.kpis()
    return data


def set_mode(mode: str) -> dict[str, Any]:
    data = _state.read()
    prev = data.get("mode")
    data["mode"] = mode
    data["mode_entered"] = time.time()
    if prev and prev != mode:
        data["loaded"] = None
    OS.enter_mode(mode, data.get("loaded"))
    _state.write(data)
    return session()


def set_ladder(ladder: str) -> dict[str, Any]:
    allowed = {"fast", "balanced", "quality", "max"}
    if ladder not in allowed:
        raise ValueError("Unknown ladder")
    data = _state.read()
    data["ladder"] = ladder
    _state.write(data)
    return session()


def make_image(prompt: str) -> dict[str, Any]:
    prompt = unchanged(prompt)
    data = session()
    if data.get("mode") != "image":
        set_mode("image")
        data = session()
    job = create_job(
        "image",
        (prompt or "untitled")[:80],
        {"prompt": prompt, "ladder": data.get("ladder"), "seed": data.get("seed")},
    )
    result = OS.run(prompt, ladder=data.get("ladder") or "balanced", job_id=job["id"])
    if result.refused:
        append_log(job["id"], result.refuse_reason or "Refused.", state="blocked", progress=0)
        if "model" in (result.refuse_reason or "").lower():
            append_log(
                job["id"],
                "Paste a Hugging Face or GitHub link in Library when Phase 1 acquire ships. Nothing was faked.",
                state="blocked",
            )
        return get_job_safe(job["id"])
    if result.queued:
        append_log(job["id"], "Queued — one heavy GPU job at a time.", state="queued", progress=0)
        return get_job_safe(job["id"])
    append_log(job["id"], "first_byte", state="running", progress=1)
    append_log(job["id"], "No image handler in Phase 0 — blocked after first-byte contract.", state="blocked")
    return get_job_safe(job["id"])


def get_job_safe(job_id: str) -> dict[str, Any]:
    from eclipse.jobs import get

    return get(job_id) or {}
