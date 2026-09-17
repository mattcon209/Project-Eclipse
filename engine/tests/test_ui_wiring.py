"""Every button in the lab UI must have a listener. Catch the Search-this-PC class of bug."""

from __future__ import annotations

import re
from pathlib import Path

from fastapi.testclient import TestClient

from eclipse.gateway import app

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "atelier" / "index.html").read_text(encoding="utf-8")
JS = (ROOT / "atelier" / "app.js").read_text(encoding="utf-8")

# Static buttons that must be wired in app.js (not dynamically rendered).
STATIC_BUTTON_IDS = [
    "pair-btn",
    "make",
    "lib-search",
    "lib-add",
    "recal",
    "q-ladder",
    "q-seed",
    "q-paste",
    "q-search",
    "help-ok",
    "help-hide",
    "chat-send",
    "chat-new",
    "chat-stop",
    "q-persona",
    "q-model",
    "edit",
    "enhance",
    "train-probe",
    "train-start",
    "q-train",
    "q-i2v",
]


def test_box57_every_static_button_is_in_html_and_js():
    for bid in STATIC_BUTTON_IDS:
        assert f'id="{bid}"' in HTML, f"HTML missing #{bid}"
        assert bid in JS, f"app.js never mentions #{bid} — unattached control"


def test_box57_search_and_add_have_click_listeners():
    assert "searchThisPc" in JS
    assert "/api/library/search" in JS
    assert "/api/library/acquire" in JS
    assert "addEventListener" in JS
    # Search must actually bind a click, not just define a function
    assert re.search(r"lib-search[\s\S]{0,200}addEventListener\(\s*[\"']click[\"']", JS)
    assert re.search(r"""\$\([\"']#lib-add[\"']\)\.addEventListener\(\s*[\"']click[\"']""", JS)
    assert re.search(r"""\$\([\"']#make[\"']\)\.addEventListener\(\s*[\"']click[\"']""", JS)
    assert re.search(r"""\$\([\"']#pair-btn[\"']\)\.addEventListener\(\s*[\"']click[\"']""", JS)
    assert re.search(r"""\$\([\"']#chat-send[\"']\)\.addEventListener\(\s*[\"']click[\"']""", JS)
    assert re.search(r"""\$\([\"']#chat-new[\"']\)\.addEventListener\(\s*[\"']click[\"']""", JS)


def test_box57_js_api_paths_exist_on_gateway():
    paths = set(re.findall(r"""["'](/api/[^"'?\s]+)""", JS))
    assert "/api/library/search" in paths
    assert "/api/make" in paths
    client = TestClient(app)
    # Unpaired: these must not 404 (missing route). 401/409/405 ok.
    for path, method in (
        ("/api/library/search", "post"),
        ("/api/library/acquire", "post"),
        ("/api/make", "post"),
        ("/api/jobs", "get"),
        ("/api/calibrate", "post"),
        ("/api/ladder", "post"),
        ("/api/seed", "post"),
        ("/api/mode", "post"),
        ("/api/library", "get"),
        ("/api/chats", "get"),
        ("/api/personas", "get"),
        ("/api/jobs/x", "delete"),
        ("/api/train", "post"),
        ("/api/train/probe", "post"),
        ("/api/video", "post"),
    ):
        fn = getattr(client, method)
        body = {} if method == "post" else None
        r = fn(path, json=body) if body is not None else fn(path)
        assert r.status_code != 404, f"{method.upper()} {path} is not mounted"


def test_box57_favicon_is_not_404():
    c = TestClient(app)
    r = c.get("/favicon.ico")
    assert r.status_code == 200


def test_box57_html_buttons_match_live_index():
    c = TestClient(app)
    live = c.get("/").text
    for bid in STATIC_BUTTON_IDS:
        assert f'id="{bid}"' in live


def test_box57_jobs_cancel_and_boot_refresh_library():
    assert "/api/jobs/" in JS
    assert "cancel" in JS
    assert re.search(r"async function boot\([\s\S]*?refreshLibrary", JS)


def test_box57_android_searchpc_is_defined():
    kt = (
        ROOT.parent
        / "atelier-android"
        / "app"
        / "src"
        / "main"
        / "java"
        / "com"
        / "eclipse"
        / "atelier"
        / "MainActivity.kt"
    ).read_text(encoding="utf-8")
    assert "fun searchPc" in kt
    assert "/api/library/search" in kt


def test_box70_per_tab_model_picks_and_chat_scroll():
    assert 'id="chat-model"' in HTML
    assert 'id="image-model"' in HTML
    assert 'id="task-mode"' in HTML
    assert 'id="later-empty"' in HTML
    assert "fillPicks" in JS
    assert "by_mode" in JS
    assert "showStill" in JS
    assert 'id="still"' in HTML
    assert 'handler === "t2i"' in JS or "handler === 't2i'" in JS
    assert 'id="seed"' in HTML
    assert 'id="seed-random"' in HTML
    assert "/api/seed" in JS
    css = (ROOT / "atelier" / "atelier.css").read_text(encoding="utf-8")
    assert "100dvh" in css
    assert ".chat-log" in css
    assert "overflow-y: auto" in css
    assert "rgba(0,0,0,:" not in css
    assert "atelier.css?v=" in HTML
    # No extra Audio/Video tabs in the nav — Mode dropdown on Chat instead.
    assert HTML.count('data-m="audio"') == 0
    assert HTML.count('data-m="video"') == 0
    assert HTML.count('data-m="train"') == 0
    assert 'id="screen-train"' in HTML
    assert 'value="train"' in HTML
    assert 'data-go="train"' in HTML
    assert "/api/train" in JS
    assert "/api/train/probe" in JS
    assert "Phase 4" in JS and "Phase 5" in JS
    assert "Video handler is Phase 7" not in JS
    assert 'id="clip"' in HTML
    assert 'kind === "video"' in JS
    assert "lastImageStill" in JS
    assert "videoStillSource" in JS
    assert "extra.source = src" in JS
    assert "i2v-wrap" in HTML
    assert 'id="i2v"' in HTML
    assert "Nothing was faked" in JS


def test_box89_image_strip_keeps_stills():
    assert 'id="strip"' in HTML
    css = (ROOT / "atelier" / "atelier.css").read_text(encoding="utf-8")
    assert ".strip" in css
    assert ".thumb" in css
    assert "refreshStrip" in JS
    assert "stillJobs" in JS
    assert "currentStill" in JS
    assert HTML.count('data-m="gallery"') == 0
