from __future__ import annotations

import secrets
import time
from pathlib import Path

from eclipse.config import DATA_DIR
from eclipse.store import JsonStore

_store = JsonStore(
    DATA_DIR / "auth.json",
    {"code": None, "code_exp": 0, "token": None, "device": None, "paired_at": None},
)


def _fresh_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def ensure_code() -> str:
    data = _store.read()
    now = time.time()
    if data.get("token"):
        return "PAIRED"
    if not data.get("code") or now > float(data.get("code_exp") or 0):
        data["code"] = _fresh_code()
        data["code_exp"] = now + 15 * 60
        _store.write(data)
    return data["code"]


def rotate_code() -> str:
    data = _store.read()
    data["code"] = _fresh_code()
    data["code_exp"] = time.time() + 15 * 60
    _store.write(data)
    return data["code"]


def is_paired() -> bool:
    return bool(_store.read().get("token"))


def pair(code: str, device_name: str) -> dict:
    data = _store.read()
    if data.get("token"):
        return {"ok": True, "token": data["token"], "already": True}
    if not code or code.strip() != str(data.get("code")):
        return {"ok": False, "error": "That code doesn’t match. Check the engine screen."}
    if time.time() > float(data.get("code_exp") or 0):
        return {"ok": False, "error": "Code expired. Ask the engine for a new one."}
    token = secrets.token_urlsafe(32)
    data["token"] = token
    data["device"] = device_name or "Galaxy S24+"
    data["paired_at"] = time.time()
    data["code"] = None
    _store.write(data)
    return {"ok": True, "token": token, "already": False}


def check_token(token: str | None) -> bool:
    if not token:
        return False
    return secrets.compare_digest(token, str(_store.read().get("token") or ""))


def status() -> dict:
    data = _store.read()
    return {
        "paired": bool(data.get("token")),
        "device": data.get("device"),
        "code": None if data.get("token") else ensure_code(),
    }
