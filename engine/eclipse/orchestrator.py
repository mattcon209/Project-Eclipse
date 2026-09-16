from __future__ import annotations

import time
from typing import Any

from eclipse.config import DATA_DIR, PROJECT_DEFAULT
from eclipse.jobs import append_log, create as create_job
from eclipse.library import get_item, register_card
from eclipse.pass_through import unchanged
from eclipse.resource_os import OS
from eclipse.store import JsonStore

GENERATION_MODES = {"image", "chat", "audio", "edit", "video", "talk", "train"}
VIEW_MODES = {"home", "jobs", "library", "gallery", "more"}

_state = JsonStore(
    DATA_DIR / "session.json",
    {
        "project": PROJECT_DEFAULT,
        "mode": None,
        "mode_entered": None,
        "loaded": None,
        "loaded_name": None,
        "loras": [],
        "ladder": "balanced",
        "seed_lock": True,
        "seed": 441029,
        "view": "home",
    },
)


def session() -> dict[str, Any]:
    data = _state.read()
    data["kpis"] = OS.kpis()
    return data


def set_mode(mode: str) -> dict[str, Any]:
    data = _state.read()
    if mode in VIEW_MODES or mode not in GENERATION_MODES:
        # Home / Jobs / Library are not leases. Pause is not exit.
        data["view"] = mode
        _state.write(data)
        return session()
    prev = data.get("mode")
    data["mode"] = mode
    data["view"] = mode
    data["mode_entered"] = time.time()
    if prev and prev != mode:
        data["loaded"] = None
        data["loaded_name"] = None
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


def use_model(item_id: str) -> dict[str, Any]:
    rec = get_item(item_id)
    if not rec:
        raise ValueError("No such library item.")
    if rec.get("state") == "inbox":
        raise ValueError("Not Ready — still in Inbox. Identify it or paste a different link.")
    if rec.get("state") != "ready":
        raise ValueError("Not Ready yet.")
    if rec.get("modality") == "lora":
        data = _state.read()
        loras = list(data.get("loras") or [])
        if rec["id"] not in loras:
            loras.append(rec["id"])
        data["loras"] = loras
        _state.write(data)
        return {"ok": True, "attached": "lora", "record": rec, "session": session()}
    register_card(rec)
    data = _state.read()
    modality = rec.get("modality") or "image"
    mode_map = {
        "text": "chat",
        "image": "image",
        "video": "video",
        "audio": "audio",
        "speech": "talk",
        "lora": "image",
    }
    mode = data.get("mode") if data.get("mode") in GENERATION_MODES else mode_map.get(modality, "image")
    if modality == "text":
        mode = "chat"
    elif modality in {"image", "video", "audio"}:
        mode = modality
    data["mode"] = mode
    data["view"] = mode
    data["mode_entered"] = time.time()
    data["loaded"] = rec["id"]
    data["loaded_name"] = rec.get("name")
    OS.enter_mode(mode, rec["id"])
    _state.write(data)
    est = OS.estimate(rec["id"], data.get("ladder") or "balanced")
    return {"ok": True, "record": rec, "fit": {"fits": est.fits, "vram_mb": est.vram_mb, "reason": est.reason}, "session": session()}


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
        reason = (result.refuse_reason or "").lower()
        if "model" in reason:
            append_log(
                job["id"],
                "Search this PC or paste a Hugging Face / GitHub link in Library. Nothing was faked.",
                state="blocked",
            )
        return get_job_safe(job["id"])
    if result.queued:
        append_log(job["id"], "Queued — one heavy GPU job at a time.", state="queued", progress=0)
        return get_job_safe(job["id"])
    append_log(job["id"], "first_byte", state="running", progress=1)
    append_log(
        job["id"],
        "Model is Ready. Image handler ships in Phase 3 — nothing was faked.",
        state="blocked",
    )
    return get_job_safe(job["id"])


def get_job_safe(job_id: str) -> dict[str, Any]:
    from eclipse.jobs import get

    return get(job_id) or {}
