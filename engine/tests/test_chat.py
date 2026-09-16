"""Phase 2 — logged chats, text handler, personas, search, no fake replies."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from eclipse.chats import create_thread, get_thread, messages_for, reset as chats_reset, search
from eclipse.gateway import app
from eclipse.library import LIB
from eclipse.orchestrator import chat_send, use_model, _state as session_store
from eclipse.pairing import ensure_code, is_paired, pair
from eclipse.pairing import _store as pair_store
from eclipse.pass_through import unchanged
from eclipse.resource_os import OS
from eclipse.text_runtime import ENGINE


def _gguf(path: Path) -> Path:
    path.write_bytes(b"GGUF" + b"\0" * 64)
    return path


def _stub(messages, ladder):
    last = messages[-1]["content"] if messages else ""
    yield "ok · "
    yield last


def _token() -> str:
    if is_paired():
        return str(pair_store.read().get("token") or "")
    return pair(ensure_code(), "pytest")["token"]


def _headers() -> dict[str, str]:
    return {"Authorization": "Bearer " + _token()}


def _ready_text(tmp_path: Path) -> dict:
    p = _gguf(tmp_path / "scene.gguf")
    rec = LIB.add(
        {
            "name": "scene-q4",
            "source": str(p),
            "path": str(p),
            "bytes": p.stat().st_size,
            "managed": False,
            "state": "ready",
            "format": "gguf",
            "modality": "text",
            "handler": "text",
            "vram_balanced_mb": 2000,
        }
    )
    return rec


def setup_function(_fn):
    chats_reset()
    ENGINE.unload()
    ENGINE.set_stub(_stub)
    OS.reset()
    sess = session_store.read()
    sess["loaded"] = None
    sess["loaded_name"] = None
    sess["mode"] = None
    sess["view"] = "home"
    session_store.write(sess)


def teardown_function(_fn):
    ENGINE.set_stub(None)
    ENGINE.unload()


def test_box60_thread_survives_reload(tmp_path):
    th = create_thread(title="warden lines")
    from eclipse.chats import append_turn

    append_turn(th["id"], "user", "a body in the doorway")
    again = get_thread(th["id"])
    assert again is not None
    assert again["turns"][0]["text"] == "a body in the doorway"
    # re-read store from disk
    from eclipse.store import JsonStore
    from eclipse.config import DATA_DIR

    disk = JsonStore(DATA_DIR / "chats.json", {"threads": []}).read()
    assert any(t.get("id") == th["id"] for t in disk.get("threads") or [])


def test_box61_horror_prompt_pass_through(tmp_path):
    rec = _ready_text(tmp_path)
    use_model(rec["id"])
    text = "gore, first-person horror, wet concrete, a body in the doorway"
    assert unchanged(text) == text
    out = chat_send(text)
    assert out["ok"] is True
    assert out["user"]["text"] == text
    assert text in (out["assistant"]["text"] or "")
    assert "not allowed" not in (out["assistant"]["text"] or "").lower()


def test_box62_consecutive_turns_one_load(tmp_path):
    rec = _ready_text(tmp_path)
    use_model(rec["id"])
    th = None
    for i in range(10):
        out = chat_send(f"turn {i}", thread_id=th)
        assert out["ok"] is True
        th = out["thread"]["id"]
    # One Resource OS load for the chat session. Consecutive turns stay warm.
    assert OS.kpis()["reloads_count"] == 1
    assert OS.kpis()["prompts_in_mode"] == 10
    assert ENGINE.loads <= 2


def test_box63_no_model_no_fake_reply():
    ENGINE.unload()
    OS.reset()
    out = chat_send("hello")
    assert out["ok"] is False
    assert out.get("refused") is True
    assert "model" in (out.get("reason") or "").lower()
    assert out["assistant"]["text"]
    assert "ok · hello" not in out["assistant"]["text"]


def test_box64_search_finds_turn():
    th = create_thread(title="cast")
    from eclipse.chats import append_turn

    append_turn(th["id"], "user", "the warden keeps the key")
    hits = search("warden")
    assert any(h["id"] == th["id"] for h in hits)
    assert search("no-such-phrase-xyz") == []


def test_box65_persona_is_system_and_kept():
    th = create_thread(persona_id="hollow")
    from eclipse.chats import append_turn

    append_turn(th["id"], "user", "write a door plaque")
    msgs = messages_for(get_thread(th["id"]))
    assert msgs[0]["role"] == "system"
    assert "Hollow" in msgs[0]["content"]
    assert msgs[-1]["role"] == "user"


def test_box66_chat_api_requires_pair():
    c = TestClient(app)
    r = c.post("/api/chats/new/send", json={"prompt": "hi"})
    assert r.status_code in (401, 409)
    assert r.status_code not in (403, 451)


def test_box67_chat_api_roundtrip(tmp_path):
    rec = _ready_text(tmp_path)
    use_model(rec["id"])
    c = TestClient(app)
    h = _headers()
    r = c.post("/api/chats/new/send", json={"prompt": "wet concrete hallway"}, headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert "wet concrete hallway" in body["assistant"]["text"]
    tid = body["thread"]["id"]
    listed = c.get("/api/chats", headers=h)
    assert listed.status_code == 200
    assert any(t["id"] == tid for t in listed.json()["threads"])
    found = c.get("/api/chats", params={"q": "hallway"}, headers=h)
    assert any(t["id"] == tid for t in found.json()["threads"])


def test_box68_stream_first_token_before_done(tmp_path):
    rec = _ready_text(tmp_path)
    use_model(rec["id"])
    out = chat_send("fog")
    assert out["ok"] is True
    assert out.get("tokens")
    assert out.get("first_byte") == "first_byte"
    assert "".join(out["tokens"]) == out["assistant"]["text"]


def test_box69_atelier_has_chat_tab():
    c = TestClient(app)
    html = c.get("/").text
    assert 'data-m="chat"' in html
    assert 'id="chat-send"' in html
    js = c.get("/app.js").text
    assert "/api/chats/" in js
    assert "chat-send" in js
