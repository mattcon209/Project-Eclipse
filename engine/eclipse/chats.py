"""Logged chat threads. History lives on the PC and survives app kill."""

from __future__ import annotations

import time
import uuid
from typing import Any

from eclipse.config import DATA_DIR, PROJECT_DEFAULT
from eclipse.store import JsonStore

_store = JsonStore(
    DATA_DIR / "chats.json",
    {
        "threads": [],
        "personas": [
            {"id": "none", "name": "None", "prompt": ""},
            {
                "id": "hollow",
                "name": "Hollow writer",
                "prompt": "You write for the game Hollow, a first-person horror game. Scene text, item copy, NPC lines. Match the register of wet concrete and tungsten light.",
            },
        ],
    },
)

MAX_THREADS = 200
MAX_TURNS = 400


def _data() -> dict[str, Any]:
    return _store.read()


def personas() -> list[dict[str, Any]]:
    return list(_data().get("personas") or [])


def get_persona(pid: str | None) -> dict[str, Any] | None:
    if not pid:
        return None
    for p in personas():
        if p.get("id") == pid:
            return p
    return None


def add_persona(name: str, prompt: str) -> dict[str, Any]:
    rec = {"id": uuid.uuid4().hex[:8], "name": (name or "untitled").strip()[:40], "prompt": prompt or ""}
    data = _data()
    data.setdefault("personas", []).append(rec)
    _store.write(data)
    return rec


def list_threads() -> list[dict[str, Any]]:
    return list(_data().get("threads") or [])


def get_thread(thread_id: str) -> dict[str, Any] | None:
    for t in list_threads():
        if t.get("id") == thread_id:
            return t
    return None


def create_thread(
    *,
    title: str = "",
    model_id: str | None = None,
    model_name: str | None = None,
    persona_id: str | None = None,
) -> dict[str, Any]:
    persona = get_persona(persona_id)
    rec = {
        "id": uuid.uuid4().hex[:12],
        "title": (title or "New chat").strip()[:80],
        "created": time.time(),
        "updated": time.time(),
        "model_id": model_id,
        "model_name": model_name,
        "persona_id": (persona or {}).get("id") or "none",
        "persona_prompt": (persona or {}).get("prompt") or "",
        "project": PROJECT_DEFAULT,
        "turns": [],
    }
    data = _data()
    data["threads"].insert(0, rec)
    data["threads"] = data["threads"][:MAX_THREADS]
    _store.write(data)
    return rec


def save_thread(rec: dict[str, Any]) -> dict[str, Any]:
    rec = dict(rec)
    rec["updated"] = time.time()
    rec["turns"] = list(rec.get("turns") or [])[-MAX_TURNS:]
    data = _data()
    threads = data.get("threads") or []
    for i, t in enumerate(threads):
        if t.get("id") == rec.get("id"):
            threads[i] = rec
            data["threads"] = threads
            _store.write(data)
            return rec
    data["threads"].insert(0, rec)
    _store.write(data)
    return rec


def delete_thread(thread_id: str) -> dict[str, Any] | None:
    rec = get_thread(thread_id)
    if not rec:
        return None
    data = _data()
    data["threads"] = [t for t in data["threads"] if t.get("id") != thread_id]
    _store.write(data)
    return rec


def append_turn(thread_id: str, role: str, text: str, **extra: Any) -> dict[str, Any] | None:
    rec = get_thread(thread_id)
    if not rec:
        return None
    turn = {
        "id": uuid.uuid4().hex[:10],
        "role": role,
        "text": text,
        "created": time.time(),
        **extra,
    }
    rec.setdefault("turns", []).append(turn)
    if role == "user" and (not rec.get("title") or rec.get("title") == "New chat"):
        rec["title"] = (text or "New chat").strip().split("\n")[0][:80] or "New chat"
    save_thread(rec)
    return turn


def update_turn(thread_id: str, turn_id: str, **fields: Any) -> dict[str, Any] | None:
    rec = get_thread(thread_id)
    if not rec:
        return None
    for t in rec.get("turns") or []:
        if t.get("id") == turn_id:
            t.update(fields)
            save_thread(rec)
            return t
    return None


def search(q: str) -> list[dict[str, Any]]:
    needle = (q or "").strip().lower()
    if not needle:
        return list_threads()
    hits: list[dict[str, Any]] = []
    for th in list_threads():
        blob = (th.get("title") or "") + " " + (th.get("model_name") or "")
        for turn in th.get("turns") or []:
            blob += " " + str(turn.get("text") or "")
        if needle in blob.lower():
            hits.append(th)
    return hits


def messages_for(thread: dict[str, Any], extra_user: str | None = None) -> list[dict[str, str]]:
    """Build chat messages. System persona is never dropped."""
    msgs: list[dict[str, str]] = []
    persona = (thread.get("persona_prompt") or "").strip()
    if persona:
        msgs.append({"role": "system", "content": persona})
    for turn in thread.get("turns") or []:
        role = turn.get("role")
        if role not in {"user", "assistant", "system"}:
            continue
        text = turn.get("text") or ""
        if role == "system" and persona:
            continue
        msgs.append({"role": role, "content": text})
    if extra_user is not None:
        msgs.append({"role": "user", "content": extra_user})
    return msgs


def reset() -> None:
    _store.write(
        {
            "threads": [],
            "personas": [
                {"id": "none", "name": "None", "prompt": ""},
                {
                    "id": "hollow",
                    "name": "Hollow writer",
                    "prompt": "You write for the game Hollow, a first-person horror game. Scene text, item copy, NPC lines. Match the register of wet concrete and tungsten light.",
                },
            ],
        }
    )
