from __future__ import annotations

import time
from typing import Any

from eclipse.config import DATA_DIR, PROJECT_DEFAULT
from eclipse.jobs import append_log, create as create_job
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
    return _state.read()


def set_mode(mode: str) -> dict[str, Any]:
    data = _state.read()
    prev = data.get("mode")
    data["mode"] = mode
    data["mode_entered"] = time.time()
    # Mode-sticky: do not unload on re-entry of same mode.
    if prev != mode:
        data["loaded"] = data.get("loaded") if prev == mode else data.get("loaded")
        if prev and prev != mode:
            data["loaded"] = None  # swap: previous heavy pipeline gone (none installed yet)
    _state.write(data)
    return data


def set_ladder(ladder: str) -> dict[str, Any]:
    allowed = {"fast", "balanced", "quality", "max"}
    if ladder not in allowed:
        raise ValueError("Unknown ladder")
    data = _state.read()
    data["ladder"] = ladder
    _state.write(data)
    return data


def make_image(prompt: str) -> dict[str, Any]:
    """Phase 0: honest job. No fake picture."""
    data = session()
    if data.get("mode") != "image":
        set_mode("image")
    job = create_job(
        "image",
        (prompt or "untitled")[:80],
        {"prompt": prompt, "ladder": data.get("ladder"), "seed": data.get("seed")},
    )
    append_log(job["id"], "Image mode is warm. No image model is installed yet.", state="blocked", progress=0)
    append_log(
        job["id"],
        "Paste a Hugging Face or GitHub link in Library when Phase 1 acquire ships. Nothing was faked.",
        state="blocked",
    )
    return get_job_safe(job["id"])


def get_job_safe(job_id: str) -> dict[str, Any]:
    from eclipse.jobs import get

    return get(job_id) or {}
