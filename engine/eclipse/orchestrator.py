from __future__ import annotations

import time
from typing import Any

from eclipse.chats import append_turn, create_thread, get_thread, messages_for, save_thread, update_turn
from eclipse.config import DATA_DIR, PROJECT_DEFAULT
from eclipse.jobs import append_log, create as create_job
from eclipse.library import get_item, register_card
from eclipse.pass_through import unchanged
from eclipse.resource_os import OS
from eclipse.store import JsonStore
from eclipse.text_runtime import ENGINE, TextError

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
        ENGINE.unload()
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
    data["loaded_name"] = rec.get("ollama_name") or rec.get("name")
    OS.enter_mode(mode, rec["id"])
    _state.write(data)
    if modality == "text":
        try:
            ENGINE.load(rec)
        except TextError:
            pass
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


def iter_chat(
    prompt: str,
    *,
    thread_id: str | None = None,
    persona_id: str | None = None,
):
    """Yield user / token / done as the runtime produces them. Prompt is never rewritten."""
    prompt = unchanged(prompt)
    data = session()
    model_id = data.get("loaded")
    rec = get_item(model_id) if model_id else None
    if data.get("mode") != "chat":
        set_mode("chat")
        data = session()
    thread = get_thread(thread_id) if thread_id else None
    if not thread:
        thread = create_thread(
            model_id=model_id,
            model_name=data.get("loaded_name") or (rec or {}).get("name"),
            persona_id=persona_id or None,
        )
    elif persona_id and persona_id != thread.get("persona_id"):
        from eclipse.chats import get_persona

        p = get_persona(persona_id)
        thread["persona_id"] = persona_id
        thread["persona_prompt"] = (p or {}).get("prompt") or ""
        save_thread(thread)
    if rec:
        thread["model_id"] = rec["id"]
        thread["model_name"] = rec.get("ollama_name") or rec.get("name")
        save_thread(thread)

    user = append_turn(thread["id"], "user", prompt, model_id=model_id)
    thread = get_thread(thread["id"]) or thread
    yield {"type": "user", "turn": user, "thread": thread}

    def _fail(reason: str, **extra: Any):
        asst = append_turn(thread["id"], "assistant", reason, error=True)
        return {
            "type": "done",
            "ok": False,
            "refused": True,
            "reason": reason,
            "thread": get_thread(thread["id"]),
            "user": user,
            "assistant": asst,
            "tokens": extra.pop("tokens", []),
            "warm": extra.pop("warm", False),
            **extra,
        }

    if not rec or rec.get("modality") != "text":
        yield _fail("No text model loaded. Use a Ready text card in Library, then Send.")
        return

    register_card(rec)
    ladder = data.get("ladder") or "balanced"
    est = OS.estimate(rec["id"], ladder)
    if not est.fits:
        yield _fail(
            est.reason or "Won’t fit VRAM.",
            fit={"fits": False, "vram_mb": est.vram_mb, "reason": est.reason},
        )
        return

    result = OS.run(prompt, ladder=ladder, job_id="chat-" + thread["id"])
    if result.refused:
        yield _fail(result.refuse_reason or "Refused.")
        return
    if result.queued:
        yield _fail("Queued — one heavy GPU job at a time.", queued=True, warm=True)
        return

    try:
        load_info = ENGINE.load(rec)
    except TextError as e:
        yield _fail(str(e))
        return

    msgs = messages_for(thread)
    tokens: list[str] = []
    t0 = time.time()
    ttft_ms = None
    name = rec.get("ollama_name") or rec.get("name")
    asst = append_turn(
        thread["id"],
        "assistant",
        "",
        model_id=rec["id"],
        model_name=name,
        impl=ENGINE.impl,
    )
    try:
        for piece in ENGINE.generate(msgs, ladder=ladder):
            if ttft_ms is None:
                ttft_ms = int((time.time() - t0) * 1000)
            tokens.append(piece)
            yield {"type": "token", "text": piece, "ttft_ms": ttft_ms}
            if len(tokens) % 12 == 0:
                update_turn(thread["id"], asst["id"], text="".join(tokens), ttft_ms=ttft_ms)
    except TextError as e:
        yield _fail(str(e), tokens=tokens, warm=load_info.get("warm"))
        return

    asst = update_turn(
        thread["id"],
        asst["id"],
        text="".join(tokens),
        ttft_ms=ttft_ms,
        impl=ENGINE.impl,
        model_name=name,
    ) or asst
    yield {
        "type": "done",
        "ok": True,
        "refused": False,
        "thread": get_thread(thread["id"]),
        "user": user,
        "assistant": asst,
        "tokens": tokens,
        "warm": load_info.get("warm"),
        "ttft_ms": ttft_ms,
        "impl": ENGINE.impl,
        "first_byte": "first_byte" if tokens else "",
    }


def chat_send(
    prompt: str,
    *,
    thread_id: str | None = None,
    persona_id: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {"tokens": []}
    for ev in iter_chat(prompt, thread_id=thread_id, persona_id=persona_id):
        kind = ev.get("type")
        if kind == "token":
            result["tokens"].append(ev.get("text") or "")
        elif kind == "user":
            result["user"] = ev.get("turn")
            result["thread"] = ev.get("thread")
        elif kind == "done":
            result.update(ev)
    result.pop("type", None)
    return result


def chat_stop() -> dict[str, Any]:
    ENGINE.stop()
    return {"ok": True}
