"""LoRA train handler. Stub is tests only. Production never writes a fake adapter."""

from __future__ import annotations

import json
import os
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from eclipse.config import DATA_DIR
from eclipse.image_runtime import _comfy_main, _comfy_python

IMG_SUFFIX = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

RECIPES = {
    "fast": {"steps": 200, "rank": 8, "lr": 1e-4, "res": 512},
    "balanced": {"steps": 800, "rank": 16, "lr": 1e-4, "res": 512},
    "quality": {"steps": 1500, "rank": 32, "lr": 8e-5, "res": 768},
    "max": {"steps": 2500, "rank": 32, "lr": 8e-5, "res": 768},
}


class TrainError(RuntimeError):
    pass


class TrainEngine:
    def __init__(self) -> None:
        self._stub: Callable[..., Path] | None = None
        self._stop = False
        self._proc: subprocess.Popen | None = None

    def set_stub(self, fn: Callable[..., Path] | None) -> None:
        self._stub = fn

    def stop(self) -> None:
        self._stop = True
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()


TRAIN = TrainEngine()


def recipe(ladder: str) -> dict[str, Any]:
    return dict(RECIPES.get(ladder) or RECIPES["balanced"])


def probe_dataset(path: str) -> dict[str, Any]:
    if not (path or "").strip():
        raise TrainError("Paste a folder of stills. Files stay where they are.")
    root = Path(path).expanduser()
    try:
        root = root.resolve()
    except OSError as e:
        raise TrainError(f"Couldn’t read that folder: {e}") from e
    if not root.is_dir():
        raise TrainError("That path is not a folder on this PC.")
    pics = [p for p in root.iterdir() if p.is_file() and p.suffix.lower() in IMG_SUFFIX]
    caps = 0
    for p in pics:
        if p.with_suffix(".txt").is_file():
            caps += 1
    if not pics:
        raise TrainError("No pictures in that folder (png / jpg / webp). Nothing was faked.")
    return {
        "ok": True,
        "path": str(root),
        "images": len(pics),
        "captions": caps,
        "notes": (
            f"{len(pics)} stills · {caps} captions"
            + (f" · {len(pics) - caps} will use the file name" if caps < len(pics) else "")
        ),
    }


def refuse_base(rec: dict[str, Any] | None) -> str | None:
    if not rec or rec.get("state") != "ready":
        return "Pick a Ready image checkpoint as the base."
    if rec.get("handler") in {"vae", "clip", "lora"} or rec.get("modality") in {"vae", "clip", "lora", "text"}:
        return "Pick the diffusion checkpoint, not a VAE / CLIP / LoRA / text model."
    blob = (str(rec.get("name") or "") + " " + str(rec.get("path") or "")).lower().replace("_", "-")
    if any(x in blob for x in ("qwen-edit", "qwen-image", "qwenimage", "flux", "hunyuan", "wan2", "ltxv")):
        return (
            "This trainer is the SD / SDXL recipe. Qwen and Flux LoRA are a later hop. "
            "Pick DreamShaper / SD1.5 / SDXL. Nothing was faked."
        )
    return None


def run_train(
    rec: dict[str, Any],
    dataset: str,
    *,
    ladder: str = "balanced",
    name: str = "",
    job_id: str = "lora",
    log: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    TRAIN._stop = False
    reason = refuse_base(rec)
    if reason:
        raise TrainError(reason)
    info = probe_dataset(dataset)
    opts = recipe(ladder)
    out_name = (name or (str(rec.get("name") or "base") + "-lora")).strip()
    out_name = "".join(ch if ch.isalnum() or ch in "-_." else "-" for ch in out_name) or "lora"
    out_dir = Path(DATA_DIR) / "loras" / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"{out_name}.safetensors"
    if TRAIN._stub is not None:
        path = TRAIN._stub(rec, info, opts, dest)
        if not Path(path).is_file():
            raise TrainError("Trainer stub did not write a file. Nothing was faked.")
        return {"path": str(path), "impl": "stub", **opts, "images": info["images"]}
    if log:
        log(f"recipe {ladder} · {opts['steps']} steps · rank {opts['rank']} · {opts['res']}px · {info['notes']}")
    impl, path = _run_real(rec, info, opts, dest, job_id, log)
    if not Path(path).is_file():
        raise TrainError("Trainer finished without a LoRA file. Nothing was faked.")
    return {"path": str(path), "impl": impl, **opts, "images": info["images"]}


def write_tiny_lora(path: Path) -> Path:
    """Test helper. Real train never calls this."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    header = {
        "lora_unet_down_blocks_0_attentions_0.lora_down.weight": {
            "dtype": "F16",
            "shape": [1, 1],
            "data_offsets": [0, 2],
        }
    }
    raw = json.dumps(header).encode("utf-8")
    path.write_bytes(struct.pack("<Q", len(raw)) + raw + b"\x00\x00")
    return path


def _run_real(
    rec: dict[str, Any],
    info: dict[str, Any],
    opts: dict[str, Any],
    dest: Path,
    job_id: str,
    log: Callable[[str], None] | None,
) -> tuple[str, str]:
    py = _train_python()
    script = Path(__file__).resolve().parent / "scripts" / "train_lora.py"
    if not script.is_file():
        raise TrainError("Train script missing from the repo.")
    cmd = [
        str(py),
        str(script),
        "--base",
        str(rec.get("path") or ""),
        "--data",
        str(info["path"]),
        "--out",
        str(dest),
        "--steps",
        str(opts["steps"]),
        "--rank",
        str(opts["rank"]),
        "--lr",
        str(opts["lr"]),
        "--res",
        str(opts["res"]),
    ]
    kohya = _kohya_script()
    if kohya:
        cmd += ["--kohya", str(kohya)]
    if log:
        log(" ".join(cmd[:4]) + " …")
    TRAIN._proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=str(script.parent),
    )
    assert TRAIN._proc.stdout is not None
    for line in TRAIN._proc.stdout:
        if TRAIN._stop:
            TRAIN._proc.terminate()
            raise TrainError("Cancelled.")
        bit = line.strip()
        if bit and log:
            log(bit[:400])
    code = TRAIN._proc.wait()
    TRAIN._proc = None
    if code != 0:
        raise TrainError(f"Trainer exited {code}. Nothing was faked.")
    if not dest.is_file():
        raise TrainError("Trainer exited 0 but wrote no LoRA. Nothing was faked.")
    return "train", str(dest)


def _train_python() -> Path:
    main = _comfy_main()
    if main:
        py = _comfy_python(main.parent)
        if py:
            return py
    return Path(sys.executable)


def _kohya_script() -> Path | None:
    home = Path.home()
    extra = os.environ.get("ECLIPSE_KOHYA", "")
    for p in (
        Path(extra) if extra else None,
        home / "kohya_ss" / "sd-scripts" / "train_network.py",
        home / "sd-scripts" / "train_network.py",
        home / "kohya_ss" / "train_network.py",
        Path("C:/kohya_ss/sd-scripts/train_network.py"),
        Path("C:/sd-scripts/train_network.py"),
    ):
        if p and p.is_file():
            return p
    return None
