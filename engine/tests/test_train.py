"""Phase 6 — Train. Stub writes a real tiny LoRA in tests. Production never fakes one."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eclipse.detect import sniff
from eclipse.library import Library
from eclipse.orchestrator import start_train, _state as session_store
from eclipse.resource_os import OS
from eclipse.train_runtime import TRAIN, TrainError, probe_dataset, recipe, refuse_base, run_train, write_tiny_lora

TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de"
    "0000000c49444154789c63606060000000040001f61738550000000049454e44ae426082"
)


def _lib(tmp_path: Path) -> Library:
    return Library(tmp_path / "library")


def _sd_rec(lib: Library, tmp_path: Path, name: str = "dreamshaper_8") -> dict:
    ckpt = tmp_path / "models" / "checkpoints" / f"{name}.safetensors"
    ckpt.parent.mkdir(parents=True, exist_ok=True)
    ckpt.write_bytes(b"u")
    return lib.add(
        {
            "name": name,
            "path": str(ckpt),
            "bytes": 2_000_000_000,
            "managed": False,
            "state": "ready",
            "format": "safetensors",
            "modality": "image",
            "handler": "t2i",
            "vram_balanced_mb": 4200,
        }
    )


def _dataset(tmp_path: Path, captions: bool = True) -> Path:
    root = tmp_path / "stills"
    root.mkdir(parents=True, exist_ok=True)
    (root / "hallway.png").write_bytes(TINY_PNG)
    (root / "door.jpg").write_bytes(TINY_PNG)
    if captions:
        (root / "hallway.txt").write_text("wet concrete corridor", encoding="utf-8")
    return root


def setup_function(_fn):
    TRAIN.set_stub(None)
    OS.reset()
    sess = session_store.read()
    sess["loaded"] = None
    sess["loaded_name"] = None
    sess["mode"] = None
    sess["by_mode"] = {}
    sess["ladder"] = "balanced"
    session_store.write(sess)


def teardown_function(_fn):
    TRAIN.set_stub(None)


def test_box94_probe_counts_stills_and_captions(tmp_path):
    root = _dataset(tmp_path, captions=True)
    info = probe_dataset(str(root))
    assert info["ok"] is True
    assert info["images"] == 2
    assert info["captions"] == 1
    assert "2 stills" in info["notes"]
    assert "file name" in info["notes"]


def test_box94_probe_empty_and_missing():
    try:
        probe_dataset("")
        raise AssertionError("empty path should refuse")
    except TrainError as e:
        assert "folder" in str(e).lower()
    try:
        probe_dataset("/no/such/eclipse-dataset-folder")
        raise AssertionError("missing folder should refuse")
    except TrainError as e:
        assert "folder" in str(e).lower() or "not" in str(e).lower()


def test_box94_probe_no_pictures(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    (empty / "notes.txt").write_text("no stills", encoding="utf-8")
    try:
        probe_dataset(str(empty))
        raise AssertionError("no pictures should refuse")
    except TrainError as e:
        assert "faked" in str(e).lower()


def test_box95_refuse_qwen_flux_vae():
    assert refuse_base(None)
    assert "Ready" in (refuse_base({"state": "inbox", "handler": "t2i", "name": "dreamshaper_8"}) or "")
    assert "VAE" in (refuse_base({"state": "ready", "handler": "vae", "name": "vae"}) or "")
    q = refuse_base({"state": "ready", "handler": "t2i", "modality": "image", "name": "qwen_image_edit_2509", "path": "x"})
    assert q and "Qwen" in q and "faked" in q.lower()
    f = refuse_base({"state": "ready", "handler": "t2i", "modality": "image", "name": "flux1-dev", "path": "x"})
    assert f and "Flux" in f
    ok = refuse_base({"state": "ready", "handler": "t2i", "modality": "image", "name": "dreamshaper_8", "path": "C:/ckpts/dreamshaper_8.safetensors"})
    assert ok is None
    assert recipe("fast")["steps"] == 200
    assert recipe("balanced")["rank"] == 16
    assert recipe("quality")["res"] == 768
    assert recipe("max")["steps"] == 2500


def test_box96_tiny_lora_sniffs_ready(tmp_path):
    path = write_tiny_lora(tmp_path / "hollow.safetensors")
    info = sniff(path)
    assert info["known"] is True
    assert info["modality"] == "lora"
    assert info["handler"] == "lora"


def test_box97_stub_catalogs_lora(tmp_path, monkeypatch):
    from eclipse import library as library_mod

    lib = _lib(tmp_path)
    rec = _sd_rec(lib, tmp_path)
    data = _dataset(tmp_path)
    monkeypatch.setattr(library_mod, "LIB", lib)
    monkeypatch.setattr("eclipse.train_runtime.DATA_DIR", tmp_path)
    OS.reset()
    TRAIN.set_stub(lambda _rec, _info, _opts, dest: write_tiny_lora(Path(dest)))
    job = start_train(rec["id"], str(data), ladder="fast", name="hollow")
    assert job["payload"]["dataset"] == str(data)
    assert job.get("state") == "done"
    art = Path(job["artifact"])
    assert art.is_file()
    assert sniff(art)["modality"] == "lora"
    items = lib.items()
    loras = [i for i in items if i.get("modality") == "lora"]
    assert loras
    assert loras[0]["state"] == "ready"
    assert loras[0]["handler"] == "lora"
    log = " ".join(x["line"] for x in job.get("log") or [])
    assert "first_byte" in log
    assert "not allowed" not in log.lower()


def test_box98_qwen_base_blocked_no_file(tmp_path, monkeypatch):
    from eclipse import library as library_mod

    lib = _lib(tmp_path)
    rec = _sd_rec(lib, tmp_path, name="qwen_image_edit_2509")
    data = _dataset(tmp_path)
    monkeypatch.setattr(library_mod, "LIB", lib)
    monkeypatch.setattr("eclipse.train_runtime.DATA_DIR", tmp_path)
    TRAIN.set_stub(lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("stub must not run")))
    job = start_train(rec["id"], str(data), ladder="fast", name="nope")
    assert job.get("state") == "blocked"
    assert job.get("artifact") is None
    log = " ".join(x["line"] for x in job.get("log") or [])
    assert "Qwen" in log
    assert "faked" in log.lower()
    assert not list((tmp_path / "loras").glob("**/*.safetensors"))


def test_box99_no_pictures_blocked(tmp_path, monkeypatch):
    from eclipse import library as library_mod

    lib = _lib(tmp_path)
    rec = _sd_rec(lib, tmp_path)
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setattr(library_mod, "LIB", lib)
    job = start_train(rec["id"], str(empty), ladder="fast", name="nope")
    assert job.get("state") == "blocked"
    assert job.get("artifact") is None
    log = " ".join(x["line"] for x in job.get("log") or [])
    assert "faked" in log.lower()


def test_box100_production_never_writes_fake_lora(tmp_path, monkeypatch):
    TRAIN.set_stub(None)
    monkeypatch.setattr("eclipse.train_runtime.DATA_DIR", tmp_path)
    rec = {
        "state": "ready",
        "handler": "t2i",
        "modality": "image",
        "name": "dreamshaper_8",
        "path": str(tmp_path / "dreamshaper_8.safetensors"),
    }
    (tmp_path / "dreamshaper_8.safetensors").write_bytes(b"not-weights")
    data = _dataset(tmp_path)
    try:
        run_train(rec, str(data), ladder="fast", name="hollow", job_id="nope")
        raise AssertionError("should refuse without kohya/diffusers")
    except TrainError as e:
        msg = str(e).lower()
        assert "faked" in msg or "exited" in msg or "diffusers" in msg or "kohya" in msg
    dest = tmp_path / "loras" / "nope" / "hollow.safetensors"
    assert not dest.is_file()
    script = Path(__file__).resolve().parents[1] / "eclipse" / "scripts" / "train_lora.py"
    src = script.read_text(encoding="utf-8")
    assert "write_tiny_lora" not in src
    assert "Nothing was faked" in src
    runtime = Path(__file__).resolve().parents[1] / "eclipse" / "train_runtime.py"
    rt = runtime.read_text(encoding="utf-8")
    assert "Production never writes a fake adapter" in rt or "never writes a fake" in rt.lower()
