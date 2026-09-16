"""Phase 1 — library, acquire, detect, size-gate."""

from __future__ import annotations

import json
import struct
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eclipse.acquire import AcquireError, classify, host_allowed, pick_gguf, run as acquire_run, scan_folder
from eclipse.convert import MIN_FREE_AFTER, rent_test
from eclipse.detect import sniff
from eclipse.library import Library, guess_vram_mb
from eclipse.resource_os import OS, ResourceOS

ROOT = Path(__file__).resolve().parents[1]


def _gguf(path: Path) -> Path:
    path.write_bytes(b"GGUF" + b"\0" * 64)
    return path


def _lora(path: Path) -> Path:
    header = {"lora_unet.down.lora_A.weight": {"dtype": "F16", "shape": [4, 4], "data_offsets": [0, 32]}}
    raw = json.dumps(header).encode()
    path.write_bytes(struct.pack("<Q", len(raw)) + raw + b"\0" * 32)
    return path


def _sdxl(folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "model_index.json").write_text(
        json.dumps({"_class_name": "StableDiffusionXLPipeline", "_diffusers_version": "0.29.0"}),
        encoding="utf-8",
    )
    return folder


def _unknown(path: Path) -> Path:
    path.write_bytes(b"not a model at all")
    return path


def _lib(tmp_path: Path) -> Library:
    return Library(tmp_path / "library")


def _os() -> ResourceOS:
    r = ResourceOS()
    r.disk_free_bytes = 300 * 1024**3
    r.disk_used_pct = 40.0
    return r


# --- detect ---


def test_box30_gguf_is_text_ready(tmp_path):
    p = _gguf(tmp_path / "tiny.gguf")
    s = sniff(p)
    assert s["known"] is True
    assert s["modality"] == "text"
    assert s["format"] == "gguf"


def test_box31_diffusers_sdxl_is_image(tmp_path):
    s = sniff(_sdxl(tmp_path / "sdxl"))
    assert s["known"] is True
    assert s["modality"] == "image"
    assert s["handler"] == "t2i"


def test_box32_lora_keys(tmp_path):
    s = sniff(_lora(tmp_path / "hollow.safetensors"))
    assert s["known"] is True
    assert s["modality"] == "lora"


def test_box33_unknown_is_inbox_not_ready(tmp_path):
    s = sniff(_unknown(tmp_path / "mystery.bin"))
    assert s["known"] is False
    assert s["handler"] == "inbox"


# --- allowlist / classify ---


def test_box34_allowlist_rejects_random():
    assert host_allowed("evil.example") is False
    try:
        classify("https://evil.example/gore-pack.gguf")
        raise AssertionError("should refuse")
    except AcquireError as e:
        assert "install list" in str(e).lower() or "isn’t" in str(e)


def test_box35_hf_github_civitai_shapes_ok():
    assert classify("https://huggingface.co/org/model")["kind"] == "hf"
    assert classify("https://github.com/org/repo")["kind"] == "github"
    assert classify("https://civitai.com/models/123")["kind"] == "civitai"
    assert host_allowed("cdn-lfs.huggingface.co") is True


def test_box36_horror_name_is_not_content_policy():
    src = classify("https://huggingface.co/someone/gore-horror-wet-concrete")
    assert src["kind"] == "hf"


# --- convert rent ---


def test_box37_convert_skips_when_disk_tight():
    ok, reason = rent_test(size_bytes=10_000, free_bytes=MIN_FREE_AFTER - 1, cuts_fit=True)
    assert ok is False
    assert "headroom" in reason.lower() or "disk" in reason.lower()


def test_box38_eager_is_enough_when_no_rent():
    ok, reason = rent_test(size_bytes=1000, free_bytes=200 * 1024**3, cuts_fit=False, eta_cut=0.0)
    assert ok is False
    assert "eager" in reason.lower()


# --- size-gate / confirm / paste → ready ---


def test_box39_unknown_size_refuses(tmp_path):
    lib = _lib(tmp_path)
    ros = _os()

    def opener(req, timeout=None):
        raise AssertionError("must not download if size unknown")

    class Fake:
        pass

    # file-url with HEAD that returns no length
    class H(BaseHTTPRequestHandler):
        def do_HEAD(self):
            self.send_response(200)
            self.end_headers()

        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"GGUF")

        def log_message(self, *args):
            pass

    httpd = HTTPServer(("127.0.0.1", 0), H)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        url = f"http://127.0.0.1:{httpd.server_address[1]}/x.gguf"
        out = acquire_run(url, lib=lib, ros=ros)
        assert out["ok"] is False
        assert out["refused"] is True
        assert "size" in (out["reason"] or "").lower()
    finally:
        httpd.shutdown()


def test_box40_size_gate_refuses(tmp_path):
    lib = _lib(tmp_path)
    ros = _os()
    ros.disk_free_bytes = 100
    p = _gguf(tmp_path / "big.gguf")
    p.write_bytes(b"GGUF" + b"\0" * 500)
    out = acquire_run(str(p), lib=lib, ros=ros)
    assert out["ok"] is False
    assert out["refused"] is True


def test_box41_local_gguf_becomes_ready(tmp_path):
    lib = _lib(tmp_path)
    ros = _os()
    p = _gguf(tmp_path / "tiny-q4.gguf")
    out = acquire_run(str(p), lib=lib, ros=ros)
    assert out["ok"] is True
    rec = out["record"]
    assert rec["state"] == "ready"
    assert rec["modality"] == "text"


def test_box42_unknown_folder_is_inbox(tmp_path):
    lib = _lib(tmp_path)
    ros = _os()
    p = _unknown(tmp_path / "blob.bin")
    out = acquire_run(str(p), lib=lib, ros=ros)
    rec = out["record"]
    assert rec["state"] == "inbox"
    assert rec["state"] != "ready"


def test_box43_scan_folder_finds_sdxl(tmp_path):
    lib = _lib(tmp_path)
    _sdxl(tmp_path / "models" / "sdxl-hollow")
    found = scan_folder(tmp_path / "models", lib=lib)
    assert found
    assert any(r["state"] == "ready" and r["modality"] == "image" for r in found)


def test_box44_pick_q4_gguf():
    siblings = [
        {"rfilename": "model-Q8_0.gguf", "size": 8},
        {"rfilename": "model-Q4_K_M.gguf", "size": 4},
        {"rfilename": "model-Q5_K_M.gguf", "size": 5},
    ]
    pick = pick_gguf(siblings)
    assert pick["rfilename"] == "model-Q4_K_M.gguf"


class _FileHandler(BaseHTTPRequestHandler):
    payload = b"GGUF" + b"\0" * 200

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Length", str(len(self.payload)))
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Length", str(len(self.payload)))
        self.end_headers()
        self.wfile.write(self.payload)

    def log_message(self, *args):
        pass


def test_box45_paste_link_to_ready_card(tmp_path):
    lib = _lib(tmp_path)
    ros = _os()
    httpd = HTTPServer(("127.0.0.1", 0), _FileHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        url = f"http://127.0.0.1:{httpd.server_address[1]}/horror-corridor.gguf"
        out = acquire_run(url, lib=lib, ros=ros)
        assert out["ok"] is True, out
        rec = out["record"]
        assert rec["state"] == "ready"
        assert rec["modality"] == "text"
        assert rec["managed"] is True
        assert Path(rec["path"]).exists()
    finally:
        httpd.shutdown()


def test_box46_large_needs_confirm(tmp_path):
    lib = _lib(tmp_path)
    ros = _os()
    httpd = HTTPServer(("127.0.0.1", 0), _FileHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        url = f"http://127.0.0.1:{httpd.server_address[1]}/big.gguf"
        out = acquire_run(url, lib=lib, ros=ros, large_after=10)
        assert out["needs_confirm"] is True
        assert out["record"] is None
        out2 = acquire_run(url, lib=lib, ros=ros, large_after=10, confirm=True)
        assert out2["ok"] is True
        assert out2["record"]["state"] == "ready"
    finally:
        httpd.shutdown()


def test_box47_partial_part_file_not_ready(tmp_path):
    folder = tmp_path / "inc"
    folder.mkdir()
    (folder / "weights.gguf.part").write_bytes(b"GGUF" + b"\0" * 20)
    s = sniff(folder)
    assert s["known"] is False


def test_box48_use_loads_once(tmp_path, monkeypatch):
    from eclipse.orchestrator import use_model
    from eclipse import library as library_mod

    lib = _lib(tmp_path)
    ros = _os()
    p = _gguf(tmp_path / "chat.gguf")
    rec = acquire_run(str(p), lib=lib, ros=ros)["record"]
    monkeypatch.setattr(library_mod, "LIB", lib)
    OS.reset()
    out = use_model(rec["id"])
    assert out["ok"] is True
    assert OS.reloads == 1
    use_model(rec["id"])
    assert OS.reloads == 1
    assert OS.model_id == rec["id"]


def test_box49_home_view_does_not_unload():
    from eclipse.orchestrator import set_mode

    OS.reset()
    OS.enter_mode("image", "sdxl")
    assert OS.reloads == 1
    set_mode("home")
    set_mode("library")
    set_mode("jobs")
    assert OS.mode == "image"
    assert OS.model_id == "sdxl"
    assert OS.unloads == 0
    set_mode("chat")
    assert OS.unloads == 1


def test_box50_library_api_requires_pair():
    from fastapi.testclient import TestClient
    from eclipse.gateway import app

    c = TestClient(app)
    r = c.post("/api/library/acquire", json={"url": "https://huggingface.co/org/gore"})
    assert r.status_code in (401, 409)
    assert r.status_code not in (403, 451)


def test_box51_guess_vram_lora_is_zero():
    assert guess_vram_mb("lora", 50_000_000) == 0


def test_box52_search_finds_nested_gguf_and_does_not_copy(tmp_path):
    from eclipse.scan import scan_machine

    home = tmp_path / "home"
    nested = home / ".cache" / "huggingface" / "hub" / "models--org--gore-llm" / "snapshots" / "abc"
    nested.mkdir(parents=True)
    _gguf(nested / "gore-horror-Q4_K_M.gguf")
    lib = _lib(tmp_path)
    out = scan_machine(lib=lib, home=home)
    assert out["ok"] is True
    assert out["added"] >= 1
    rec = next(r for r in out["items"] if r.get("state") == "ready")
    assert rec["managed"] is False
    assert rec["modality"] == "text"
    assert "gore" in rec["name"].lower() or "gore" in rec["source"].lower()
    assert Path(rec["path"]).exists()
    # still on disk in the cache, not copied into library/items
    assert "library/items" not in rec["path"].replace("\\", "/")


def test_box53_search_dedupes_second_run(tmp_path):
    from eclipse.scan import scan_machine

    home = tmp_path / "home"
    d = home / "Downloads"
    d.mkdir(parents=True)
    _gguf(d / "local.gguf")
    lib = _lib(tmp_path)
    a = scan_machine(lib=lib, home=home)
    b = scan_machine(lib=lib, home=home)
    assert a["added"] >= 1
    assert b["added"] == 0
    assert b["already"] >= 1


def test_box54_search_api_requires_pair():
    from fastapi.testclient import TestClient
    from eclipse.gateway import app

    c = TestClient(app)
    r = c.post("/api/library/search", json={})
    assert r.status_code in (401, 409)
    assert r.status_code not in (403, 451)


def test_box55_atelier_has_search_button():
    from fastapi.testclient import TestClient
    from eclipse.gateway import app

    c = TestClient(app)
    r = c.get("/")
    assert r.status_code == 200
    assert "Search this PC" in r.text
    js = c.get("/app.js")
    assert js.status_code == 200
    assert "searchThisPc" in js.text
    assert "/api/library/search" in js.text


def test_box56_ollama_blob_without_gguf_suffix(tmp_path):
    from eclipse.scan import scan_machine

    home = tmp_path / "home"
    blobs = home / ".ollama" / "models" / "blobs"
    blobs.mkdir(parents=True)
    blob = blobs / "sha256-deadbeefcafebabe"
    blob.write_bytes(b"GGUF" + b"\0" * 64)
    manifests = home / ".ollama" / "models" / "manifests" / "registry.ollama.ai" / "library" / "llama3.2"
    manifests.mkdir(parents=True)
    (manifests / "latest").write_text(
        json.dumps({"layers": [{"digest": "sha256:deadbeefcafebabe", "mediaType": "application/vnd.ollama.image.model"}]}),
        encoding="utf-8",
    )
    lib = _lib(tmp_path)
    out = scan_machine(lib=lib, home=home)
    assert out["added"] >= 1
    rec = next(r for r in out["items"] if r["state"] == "ready")
    assert rec["managed"] is False
    assert rec["modality"] == "text"
    assert "llama3.2" in rec["name"]


def _fat_safetensors(path: Path, name_stem: str | None = None) -> Path:
    header = {"weight": {"dtype": "F16", "shape": [4, 4], "data_offsets": [0, 32]}}
    raw = json.dumps(header).encode()
    path.write_bytes(struct.pack("<Q", len(raw)) + raw + b"\0" * (256 * 1024))
    return path


def test_box70_qwen_image_safetensors_is_t2i(tmp_path):
    p = _fat_safetensors(tmp_path / "Qwen-Image-BF16.safetensors")
    s = sniff(p)
    assert s["known"] is True
    assert s["modality"] == "image"
    assert s["handler"] == "t2i"


def test_box70_search_finds_standalone_safetensors(tmp_path):
    from eclipse.scan import scan_machine

    home = tmp_path / "home"
    ckpt = home / "ComfyUI" / "models" / "checkpoints"
    ckpt.mkdir(parents=True)
    _fat_safetensors(ckpt / "qwen_image_fp8.safetensors")
    lib = _lib(tmp_path)
    out = scan_machine(lib=lib, home=home)
    assert out["added"] >= 1
    rec = next(r for r in out["items"] if "qwen" in (r.get("name") or "").lower() or "qwen" in (r.get("source") or "").lower())
    assert rec["state"] == "ready"
    assert rec["modality"] == "image"
    assert rec["managed"] is False


def test_box70_mode_remembers_last_model_per_tab(tmp_path, monkeypatch):
    from eclipse.orchestrator import session, set_mode, use_model, _state as session_store
    from eclipse import library as library_mod

    sess = session_store.read()
    sess["mode"] = None
    sess["loaded"] = None
    sess["loaded_name"] = None
    sess["by_mode"] = {}
    session_store.write(sess)
    lib = _lib(tmp_path)
    ros = _os()
    text = acquire_run(str(_gguf(tmp_path / "qwen3.gguf")), lib=lib, ros=ros)["record"]
    img = acquire_run(str(_sdxl(tmp_path / "qwen-image")), lib=lib, ros=ros)["record"]
    monkeypatch.setattr(library_mod, "LIB", lib)
    OS.reset()
    use_model(text["id"])
    assert session()["mode"] == "chat"
    assert session()["loaded"] == text["id"]
    use_model(img["id"])
    assert session()["mode"] == "image"
    assert session()["loaded"] == img["id"]
    assert (session().get("by_mode") or {}).get("chat", {}).get("id") == text["id"]
    set_mode("chat")
    assert session()["loaded"] == text["id"]
    set_mode("image")
    assert session()["loaded"] == img["id"]


def test_box71_comfy_extra_model_paths_yaml(tmp_path):
    from eclipse.scan import scan_machine

    home = tmp_path / "home"
    weights = tmp_path / "sd" / "models" / "checkpoints"
    weights.mkdir(parents=True)
    _fat_safetensors(weights / "qwen_image.safetensors")
    comfy = home / "ComfyUI"
    comfy.mkdir(parents=True)
    (comfy / "extra_model_paths.yaml").write_text(
        "comfyui:\n"
        f"  base_path: {tmp_path.joinpath('sd').as_posix()}\n"
        "  checkpoints: models/checkpoints\n",
        encoding="utf-8",
    )
    lib = _lib(tmp_path)
    out = scan_machine(lib=lib, home=home)
    rec = next(
        r
        for r in out["items"]
        if "qwen" in (r.get("name") or "").lower() or "qwen" in (r.get("source") or "").lower()
    )
    assert rec["state"] == "ready"
    assert rec["modality"] == "image"
    assert rec["managed"] is False


def test_box72_gameai_comfy_qwen_and_skips_hf_bin(tmp_path):
    from eclipse.scan import scan_machine

    home = tmp_path / "home"
    unet = home / "GameAI" / "ComfyUI" / "models" / "diffusion_models"
    unet.mkdir(parents=True)
    _fat_safetensors(unet / "qwen_image_edit_2509_fp8_e4m3fn.safetensors")
    junk = home / ".cache" / "huggingface" / "hub" / "models--org--foo" / "snapshots" / "abc"
    junk.mkdir(parents=True)
    (junk / "pytorch_model.bin").write_bytes(b"not a model" * 1000)
    lib = _lib(tmp_path)
    out = scan_machine(lib=lib, home=home)
    rec = next(
        r
        for r in out["items"]
        if "qwen" in (r.get("name") or "").lower() or "qwen" in (r.get("source") or "").lower()
    )
    assert rec["state"] == "ready"
    assert rec["modality"] == "image"
    assert rec["managed"] is False
    assert not any((r.get("path") or "").endswith("pytorch_model.bin") for r in out["items"])


def test_box73_scan_drops_missing_and_inbox_bin(tmp_path):
    from eclipse.scan import scan_machine

    home = tmp_path / "home"
    d = home / "Downloads"
    d.mkdir(parents=True)
    keep = _gguf(d / "keep.gguf")
    gone = d / "deleted.gguf"
    _gguf(gone)
    junk = d / "pytorch_model.bin"
    junk.write_bytes(b"not a model" * 1000)
    lib = _lib(tmp_path)
    rec_keep = lib.add(
        {
            "name": "keep",
            "path": str(keep.resolve()),
            "state": "ready",
            "format": "gguf",
            "modality": "text",
            "handler": "text",
            "managed": False,
            "source_kind": "scan",
        }
    )
    rec_gone = lib.add(
        {
            "name": "deleted",
            "path": str(gone.resolve()),
            "state": "ready",
            "format": "gguf",
            "modality": "text",
            "handler": "text",
            "managed": False,
            "source_kind": "scan",
        }
    )
    rec_bin = lib.add(
        {
            "name": "pytorch_model",
            "path": str(junk.resolve()),
            "state": "inbox",
            "format": "bin",
            "modality": "unknown",
            "handler": "inbox",
            "managed": False,
            "source_kind": "scan",
        }
    )
    gone.unlink()
    out = scan_machine(lib=lib, home=home)
    ids = {it["id"] for it in out["items"]}
    assert rec_keep["id"] in ids
    assert rec_gone["id"] not in ids
    assert rec_bin["id"] not in ids
    assert out["removed"] >= 2
    assert all(it.get("format") != "bin" for it in out["items"])
