"""Phase 3 — stills. Stub runtime only in tests. Never a fake production PNG."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eclipse.detect import sniff
from eclipse.image_runtime import IMAGE, ImageError, resolve_stack
from eclipse.library import Library
from eclipse.orchestrator import make_image, use_model, _state as session_store
from eclipse.pass_through import unchanged
from eclipse.resource_os import OS

TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de"
    "0000000c49444154789c63606060000000040001f61738550000000049454e44ae426082"
)


def _lib(tmp_path: Path) -> Library:
    return Library(tmp_path / "library")


def _png_stub(rec, prompt, ladder, seed):
    assert prompt == unchanged(prompt)
    return TINY_PNG


def setup_function(_fn):
    IMAGE.set_stub(None)
    OS.reset()
    sess = session_store.read()
    sess["loaded"] = None
    sess["loaded_name"] = None
    sess["mode"] = None
    sess["by_mode"] = {}
    sess["seed"] = 441029
    sess["seed_random"] = False
    session_store.write(sess)


def teardown_function(_fn):
    IMAGE.set_stub(None)


def test_box80_vae_is_companion_not_t2i(tmp_path):
    p = tmp_path / "models" / "vae" / "qwen_image_vae.safetensors"
    p.parent.mkdir(parents=True)
    p.write_bytes(b"not-real")
    s = sniff(p)
    assert s["handler"] == "vae"
    assert s["modality"] == "vae"


def test_box80_clip_is_companion(tmp_path):
    p = tmp_path / "models" / "text_encoders" / "qwen_2.5_vl_7b_fp8_scaled.safetensors"
    p.parent.mkdir(parents=True)
    p.write_bytes(b"not-real")
    s = sniff(p)
    assert s["handler"] == "clip"


def test_box80_unet_is_t2i(tmp_path):
    p = tmp_path / "models" / "diffusion_models" / "qwen_image_edit_2509_fp8_e4m3fn.safetensors"
    p.parent.mkdir(parents=True)
    p.write_bytes(b"not-real")
    s = sniff(p)
    assert s["handler"] == "t2i"
    assert s["modality"] == "image"


def test_box81_no_model_no_fake_still():
    OS.reset()
    horror = "gore, first-person horror, wet concrete, a body in the doorway"
    job = make_image(horror)
    assert job.get("artifact") is None
    assert job.get("state") == "blocked"
    assert job["payload"]["prompt"] == horror
    log = " ".join(x["line"] for x in job.get("log") or [])
    assert "faked" in log.lower() or "model" in log.lower()
    assert "not allowed" not in log.lower()


def test_box82_stub_writes_png_unfiltered(tmp_path, monkeypatch):
    from eclipse import library as library_mod

    lib = _lib(tmp_path)
    models = tmp_path / "GameAI" / "ComfyUI" / "models"
    unet = models / "diffusion_models" / "qwen_image_edit_2509_fp8_e4m3fn.safetensors"
    vae = models / "vae" / "qwen_image_vae.safetensors"
    clip = models / "text_encoders" / "qwen_2.5_vl_7b_fp8_scaled.safetensors"
    unet.parent.mkdir(parents=True)
    vae.parent.mkdir(parents=True)
    clip.parent.mkdir(parents=True)
    unet.write_bytes(b"u")
    vae.write_bytes(b"v")
    clip.write_bytes(b"c")
    rec = lib.add(
        {
            "name": "qwen_image_edit_2509_fp8_e4m3fn",
            "path": str(unet),
            "bytes": 20_000_000_000,
            "managed": False,
            "state": "ready",
            "format": "safetensors",
            "modality": "image",
            "handler": "t2i",
            "vram_balanced_mb": 7000,
        }
    )
    lib.add(
        {
            "name": "qwen_image_vae",
            "path": str(vae),
            "state": "ready",
            "format": "safetensors",
            "modality": "vae",
            "handler": "vae",
            "managed": False,
        }
    )
    lib.add(
        {
            "name": "qwen_2.5_vl_7b_fp8_scaled",
            "path": str(clip),
            "state": "ready",
            "format": "safetensors",
            "modality": "clip",
            "handler": "clip",
            "managed": False,
        }
    )
    monkeypatch.setattr(library_mod, "LIB", lib)
    monkeypatch.setattr("eclipse.image_runtime.list_items", lib.items)
    OS.reset()
    IMAGE.set_stub(_png_stub)
    use_model(rec["id"])
    text = "gore, first-person horror, wet concrete, a body in the doorway"
    job = make_image(text)
    assert job["payload"]["prompt"] == text
    assert job.get("state") == "done"
    art = Path(job["artifact"])
    assert art.is_file()
    assert art.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    log = " ".join(x["line"] for x in job.get("log") or [])
    assert "first_byte" in log
    assert "not allowed" not in log.lower()


def test_box83_stack_resolves_companions(tmp_path, monkeypatch):
    from eclipse import library as library_mod

    lib = _lib(tmp_path)
    models = tmp_path / "models"
    unet = models / "diffusion_models" / "qwen_image_edit_2509_fp8_e4m3fn.safetensors"
    vae = models / "vae" / "qwen_image_vae.safetensors"
    clip = models / "text_encoders" / "qwen_2.5_vl_7b_fp8_scaled.safetensors"
    unet.parent.mkdir(parents=True)
    vae.parent.mkdir(parents=True)
    clip.parent.mkdir(parents=True)
    unet.write_bytes(b"u")
    vae.write_bytes(b"v")
    clip.write_bytes(b"c")
    rec = {"name": unet.stem, "path": str(unet), "handler": "t2i", "modality": "image"}
    monkeypatch.setattr(library_mod, "LIB", lib)
    monkeypatch.setattr("eclipse.image_runtime.list_items", lib.items)
    stack = resolve_stack(rec)
    assert stack["unet_name"] == unet.name
    assert stack["vae_name"] == vae.name
    assert stack["clip_name"] == clip.name


def test_box85_checkpoint_does_not_need_vae(tmp_path, monkeypatch):
    from eclipse.image_runtime import _workflow

    rec = {
        "name": "Qwen-Edit-abliterated-checkpoint_v1.2",
        "path": str(tmp_path / "models" / "checkpoints" / "Qwen-Edit-abliterated-checkpoint_v1.2.safetensors"),
        "handler": "t2i",
        "modality": "image",
    }
    monkeypatch.setattr("eclipse.image_runtime.list_items", lambda: [])
    stack = resolve_stack(rec)
    assert stack["kind"] == "checkpoint"
    graph = _workflow(stack, "hallway", {"steps": 20, "cfg": 2.5, "width": 768, "height": 768}, 7, "j1")
    assert graph["4"]["class_type"] == "CheckpointLoaderSimple"
    assert "VAELoader" not in {n["class_type"] for n in graph.values()}


def test_box86_seed_random_rolls(monkeypatch):
    from eclipse.orchestrator import set_seed, session

    set_seed(441029, random=False)
    assert session()["seed"] == 441029
    assert session()["seed_random"] is False
    set_seed(random=True)
    assert session()["seed_random"] is True
    monkeypatch.setattr("eclipse.orchestrator.secrets.randbelow", lambda n: 99)
    OS.reset()
    job = make_image("x")
    assert job.get("payload", {}).get("seed") == 99 or session()["seed"] == 99


def test_box87_nested_checkpoint_uses_comfy_rel(tmp_path, monkeypatch):
    from eclipse.image_runtime import _comfy_rel, _match_comfy, _workflow

    rec = {
        "name": "model-1",
        "path": str(
            tmp_path
            / "models"
            / "checkpoints"
            / "v1.2"
            / "Qwen-Edit-abliterated-checkpint_v1.2.safetensors"
        ),
        "handler": "t2i",
        "modality": "image",
    }
    monkeypatch.setattr("eclipse.image_runtime.list_items", lambda: [])
    stack = resolve_stack(rec)
    assert stack["kind"] == "checkpoint"
    assert stack["unet_name"] == "v1.2/Qwen-Edit-abliterated-checkpint_v1.2.safetensors"
    graph = _workflow(stack, "hallway", {"steps": 8, "cfg": 2.5, "width": 512, "height": 512}, 1, "j")
    assert graph["4"]["inputs"]["ckpt_name"] == stack["unet_name"]
    choices = [
        "Qwen-Edit-abliterated-4step-v1.safetensors",
        "v1.2\\Qwen-Edit-abliterated-checkpint_v1.2.safetensors",
    ]
    assert _match_comfy("model-1", choices) is None
    assert _match_comfy(stack["unet_name"], choices) == choices[1]
    assert _comfy_rel(Path(rec["path"])).endswith("checkpint_v1.2.safetensors")


def test_box84_non_png_is_refused():
    IMAGE.set_stub(lambda *a: b"not a picture")
    rec = {"id": "x", "handler": "t2i", "modality": "image", "path": "/tmp/x.safetensors", "state": "ready"}
    try:
        IMAGE.generate(rec, "hallway", job_id="nope")
        raise AssertionError("should refuse")
    except ImageError as e:
        assert "faked" in str(e).lower() or "png" in str(e).lower()
