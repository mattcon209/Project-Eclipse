"""Phase 7 — Video. Stub writes a real tiny webp in tests. Production never fakes a clip."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eclipse.library import Library
from eclipse.orchestrator import make_image, make_video, use_model, _state as session_store
from eclipse.pass_through import unchanged
from eclipse.resource_os import OS
from eclipse.video_runtime import LADDER, VIDEO, VideoError, family_of, refuse_pair, write_tiny_webp, _workflow

TINY_WEBP = bytes.fromhex(
    "52494646240000005745425056503820180000003001009d012a010001000100"
    "430000fed2fffff000000000"
)


def _lib(tmp_path: Path) -> Library:
    return Library(tmp_path / "library")


def _vid_rec(lib: Library, tmp_path: Path, name: str = "ltx-video-2b-v0.9.5") -> dict:
    ckpt = tmp_path / "models" / "checkpoints" / f"{name}.safetensors"
    ckpt.parent.mkdir(parents=True, exist_ok=True)
    ckpt.write_bytes(b"u")
    return lib.add(
        {
            "name": name,
            "path": str(ckpt),
            "bytes": 6_000_000_000,
            "managed": False,
            "state": "ready",
            "format": "safetensors",
            "modality": "video",
            "handler": "t2v",
            "vram_balanced_mb": 11000,
        }
    )


def setup_function(_fn):
    VIDEO.set_stub(None)
    OS.reset()
    sess = session_store.read()
    sess["loaded"] = None
    sess["loaded_name"] = None
    sess["mode"] = None
    sess["by_mode"] = {}
    sess["seed"] = 441029
    sess["seed_random"] = False
    sess["ladder"] = "balanced"
    session_store.write(sess)


def teardown_function(_fn):
    VIDEO.set_stub(None)


def test_box101_family_and_refuse():
    assert family_of({"name": "ltx-video-2b-v0.9.5", "path": "x"}) == "ltxv"
    assert family_of({"name": "hunyuan_video_t2v_720p", "path": "x"}) == "hunyuan"
    assert family_of({"name": "wan2.1_t2v_1.3B", "path": "x"}) == "wan"
    assert family_of({"name": "mochi-1", "handler": "t2v", "path": "x"}) is None
    rec = {"name": "hunyuan_video_t2v_720p_bf16", "path": "x"}
    assert refuse_pair(rec, "still.png")
    assert refuse_pair(rec, None) is None
    rec_i = {"name": "hunyuan_video_image_to_video_720p", "path": "x"}
    assert refuse_pair(rec_i, None)
    assert refuse_pair(rec_i, "still.png") is None


def test_box102_ltxv_graphs():
    stack = {
        "family": "ltxv",
        "kind": "checkpoint",
        "unet_name": "ltx-video-2b-v0.9.5.safetensors",
        "clip_name": "t5xxl_fp16.safetensors",
        "clip_type": "ltxv",
        "vae_name": "",
    }
    g = _workflow(stack, "hallway", LADDER["fast"], 7, "j")
    assert g["5"]["class_type"] == "EmptyLTXVLatentVideo"
    assert g["5"]["inputs"]["length"] == 9
    assert g["11"]["class_type"] == "SaveAnimatedWEBP"
    stack["image"] = "eclipse-j.png"
    g = _workflow(stack, "the door eases open", LADDER["balanced"], 7, "j")
    assert g["5"]["class_type"] == "LTXVImgToVideo"
    assert g["41"]["class_type"] == "LoadImage"


def test_box103_hunyuan_wan_graphs():
    h = {
        "family": "hunyuan",
        "kind": "unet",
        "unet_name": "hunyuan_video_t2v_720p_bf16.safetensors",
        "clip_name": "clip_l.safetensors",
        "clip_name2": "llava_llama3_fp8_scaled.safetensors",
        "vae_name": "hunyuan_video_vae_bf16.safetensors",
        "dtype": "default",
    }
    g = _workflow(h, "fog", LADDER["fast"], 1, "j")
    assert g["5"]["class_type"] == "EmptyHunyuanLatentVideo"
    assert g["8"]["class_type"] == "DualCLIPLoader"
    w = {
        "family": "wan",
        "kind": "unet",
        "unet_name": "wan2.1_t2v_1.3B_fp8.safetensors",
        "clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
        "vae_name": "wan_2.1_vae.safetensors",
        "dtype": "fp8_e4m3fn",
    }
    g = _workflow(w, "fog", LADDER["fast"], 1, "j")
    assert g["5"]["class_type"] == "EmptyHunyuanLatentVideo"
    w["image"] = "eclipse-j.png"
    g = _workflow(w, "fog", LADDER["fast"], 1, "j")
    assert g["5"]["class_type"] == "WanImageToVideo"


def test_box104_no_model_no_fake_clip():
    horror = "gore, first-person horror, wet concrete, a body in the doorway"
    job = make_video(horror)
    assert job.get("artifact") is None
    assert job.get("state") == "blocked"
    assert job["payload"]["prompt"] == horror
    log = " ".join(x["line"] for x in job.get("log") or [])
    assert "faked" in log.lower() or "model" in log.lower()
    assert "not allowed" not in log.lower()


def test_box105_stub_writes_webp_unfiltered(tmp_path, monkeypatch):
    from eclipse import library as library_mod

    lib = _lib(tmp_path)
    rec = _vid_rec(lib, tmp_path)
    monkeypatch.setattr(library_mod, "LIB", lib)
    monkeypatch.setattr("eclipse.video_runtime.DATA_DIR", tmp_path)
    monkeypatch.setattr("eclipse.config.DATA_DIR", tmp_path)
    OS.reset()

    def _stub(rec, prompt, ladder, seed):
        assert prompt == unchanged(prompt)
        return TINY_WEBP

    VIDEO.set_stub(_stub)
    use_model(rec["id"])
    text = "gore, first-person horror, wet concrete, a body in the doorway"
    job = make_video(text)
    assert job["payload"]["prompt"] == text
    assert job.get("state") == "done"
    art = Path(job["artifact"])
    assert art.is_file()
    assert art.read_bytes()[:4] == b"RIFF"
    assert art.read_bytes()[8:12] == b"WEBP"
    log = " ".join(x["line"] for x in job.get("log") or [])
    assert "first_byte" in log
    assert "clip" in log.lower()


def test_box106_make_image_routes_video(tmp_path, monkeypatch):
    from eclipse import library as library_mod

    lib = _lib(tmp_path)
    rec = _vid_rec(lib, tmp_path)
    monkeypatch.setattr(library_mod, "LIB", lib)
    monkeypatch.setattr("eclipse.video_runtime.DATA_DIR", tmp_path)
    OS.reset()
    VIDEO.set_stub(lambda *a: TINY_WEBP)
    use_model(rec["id"])
    job = make_image("abandoned corridor, tungsten")
    assert job.get("kind") == "video"
    assert job.get("state") == "done"


def test_box107_i2v_hunyuan_t2v_file_refused(tmp_path, monkeypatch):
    from eclipse import library as library_mod
    from eclipse.jobs import create as create_job, update as job_update

    lib = _lib(tmp_path)
    rec = _vid_rec(lib, tmp_path, name="hunyuan_video_t2v_720p_bf16")
    still = tmp_path / "stills"
    still.mkdir()
    png = still / "x.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
    src = create_job("image", "still", {"prompt": "hallway"})
    job_update(src["id"], artifact=str(png), state="done")
    monkeypatch.setattr(library_mod, "LIB", lib)
    OS.reset()
    VIDEO.set_stub(None)
    use_model(rec["id"])
    try:
        VIDEO.generate(rec, "the door eases open", source_path=str(png), job_id="nope")
        raise AssertionError("should refuse I2V on a T2V Hunyuan")
    except VideoError as e:
        msg = str(e)
        assert "T2V" in msg or "t2v" in msg.lower() or "image-to-video" in msg.lower()
    job = make_video("the door eases open", source=src["id"])
    assert job.get("state") == "blocked"
    assert job.get("artifact") is None


def test_box108_production_never_writes_fake_clip(tmp_path):
    VIDEO.set_stub(None)
    rec = {
        "state": "ready",
        "handler": "t2v",
        "modality": "video",
        "name": "ltx-video-2b-v0.9.5",
        "path": str(tmp_path / "ltx-video-2b-v0.9.5.safetensors"),
    }
    (tmp_path / "ltx-video-2b-v0.9.5.safetensors").write_bytes(b"not-weights")
    try:
        VIDEO.generate(rec, "hallway", job_id="nope")
        raise AssertionError("should refuse")
    except VideoError as e:
        msg = str(e).lower()
        assert "faked" in msg or "comfy" in msg or "runtime" in msg
    dest = Path("/tmp") / "nope.webp"
    assert not (tmp_path / "clips" / "nope.webp").is_file()
    src = Path(__file__).resolve().parents[1] / "eclipse" / "video_runtime.py"
    rt = src.read_text(encoding="utf-8")
    assert "never writes a fake clip" in rt.lower()
    assert "write_tiny_webp" in rt
