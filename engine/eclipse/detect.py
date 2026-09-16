"""Sniff a file or folder. Unknown → Inbox, never silent Ready."""

from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any

IMAGE_CLASSES = (
    "StableDiffusionPipeline",
    "StableDiffusionXLPipeline",
    "StableDiffusionXLImg2ImgPipeline",
    "StableDiffusionInpaintPipeline",
    "StableDiffusionXLInpaintPipeline",
    "FluxPipeline",
    "AutoPipelineForText2Image",
    "QwenImagePipeline",
    "KolorsPipeline",
    "StableDiffusion3Pipeline",
    "HiDreamImagePipeline",
)
VIDEO_CLASSES = (
    "TextToVideoSDPipeline",
    "StableVideoDiffusionPipeline",
    "AnimateDiffPipeline",
    "CogVideoXPipeline",
)


def sniff(path: str | Path) -> dict[str, Any]:
    root = Path(path)
    if not root.exists():
        return _unknown(root, "Path is gone.")
    if root.is_file():
        return _sniff_file(root, display=root.stem)
    return _sniff_dir(root)


def _unknown(root: Path, notes: str) -> dict[str, Any]:
    return {
        "format": "unknown",
        "modality": "unknown",
        "handler": "inbox",
        "name": root.name or "untitled",
        "notes": notes,
        "known": False,
    }


def _sniff_dir(root: Path) -> dict[str, Any]:
    files = [p for p in root.rglob("*") if p.is_file() and not p.name.endswith(".part")]
    if not files:
        return _unknown(root, "Empty folder.")
    index = next((p for p in files if p.name == "model_index.json"), None)
    if index:
        return _sniff_model_index(index, display=root.name)
    gguf = next((p for p in files if p.suffix.lower() in {".gguf", ".ggml"}), None)
    if gguf:
        return _sniff_file(gguf, display=root.name)
    cfg = next((p for p in files if p.name == "config.json"), None)
    st = [p for p in files if p.suffix.lower() == ".safetensors"]
    if st and _any_lora(st):
        return {
            "format": "lora",
            "modality": "lora",
            "handler": "lora",
            "name": root.name,
            "notes": "LoRA adapter.",
            "known": True,
        }
    if cfg:
        return _sniff_config(cfg, display=root.name)
    if len(st) == 1:
        return _sniff_file(st[0], display=root.name)
    guessed = _guess_from_name(str(root))
    if guessed and (st or any(p.suffix.lower() in {".ckpt", ".pt", ".bin", ".gguf"} for p in files)):
        fmt = "safetensors" if st else "weights"
        return guessed | {"format": fmt, "name": root.name, "known": True}
    if st:
        return {
            "format": "safetensors",
            "modality": "unknown",
            "handler": "inbox",
            "name": root.name,
            "notes": "Weights found — identify before Ready.",
            "known": False,
        }
    return _unknown(root, "No known model files.")


def _sniff_file(path: Path, display: str) -> dict[str, Any]:
    suf = path.suffix.lower()
    if suf in {".gguf", ".ggml"} or _is_gguf(path):
        guessed = _guess_from_name(str(path) + " " + display)
        if guessed:
            return guessed | {"format": "gguf", "name": display, "known": True}
        return {
            "format": "gguf",
            "modality": "text",
            "handler": "text",
            "name": display,
            "notes": "GGUF / llama-class text.",
            "known": True,
        }
    if path.name == "model_index.json":
        return _sniff_model_index(path, display)
    if suf == ".safetensors":
        keys = _safetensors_keys(path)
        if keys and _keys_look_lora(keys):
            return {
                "format": "lora",
                "modality": "lora",
                "handler": "lora",
                "name": display,
                "notes": "LoRA adapter.",
                "known": True,
            }
        guessed = _guess_from_name(str(path) + " " + display)
        if guessed:
            return guessed | {"format": "safetensors", "name": display, "known": True}
        return {
            "format": "safetensors",
            "modality": "unknown",
            "handler": "inbox",
            "name": display,
            "notes": "Single weight file — Inbox until identified.",
            "known": False,
        }
    if path.name == "config.json":
        return _sniff_config(path, display)
    if suf in {".ckpt", ".pt", ".pth", ".bin"}:
        guessed = _guess_from_name(str(path) + " " + display)
        if guessed:
            return guessed | {"format": suf.lstrip("."), "name": display, "known": True}
        return {
            "format": suf.lstrip("."),
            "modality": "unknown",
            "handler": "inbox",
            "name": display,
            "notes": "Weight file — Inbox until identified.",
            "known": False,
        }
    if suf in {".onnx"}:
        return {
            "format": "onnx",
            "modality": "unknown",
            "handler": "inbox",
            "name": display,
            "notes": "ONNX runtime — identify family.",
            "known": False,
        }
    return _unknown(path, "Unknown file type.")


def _sniff_model_index(path: Path, display: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _unknown(path, "model_index.json is unreadable.")
    cls = str(data.get("_class_name") or "")
    if any(v in cls for v in VIDEO_CLASSES) or "Video" in cls or "Animate" in cls:
        return {
            "format": "diffusers",
            "modality": "video",
            "handler": "t2v",
            "name": display,
            "notes": cls or "Diffusers video.",
            "known": True,
        }
    if any(v in cls for v in IMAGE_CLASSES) or "Diffusion" in cls or "Flux" in cls or "QwenImage" in cls or "Kolors" in cls:
        return {
            "format": "diffusers",
            "modality": "image",
            "handler": "t2i",
            "name": display,
            "notes": cls or "Diffusers image.",
            "known": True,
        }
    return {
        "format": "diffusers",
        "modality": "unknown",
        "handler": "inbox",
        "name": display,
        "notes": f"Diffusers class {cls or 'unknown'} — Inbox.",
        "known": False,
    }


def _sniff_config(path: Path, display: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _unknown(path, "config.json is unreadable.")
    mt = str(data.get("model_type") or "").lower()
    arch = " ".join(str(x) for x in (data.get("architectures") or [])).lower()
    blob = mt + " " + arch
    if "whisper" in blob or "parakeet" in blob or "wav2vec" in blob or "sensevoice" in blob:
        return {
            "format": "transformers",
            "modality": "speech",
            "handler": "stt",
            "name": display,
            "notes": "Speech-to-text.",
            "known": True,
        }
    guessed = _guess_from_name(display + " " + str(path))
    if guessed and guessed.get("modality") != "text":
        return guessed | {"format": "transformers", "name": display, "known": True}
    if mt or arch:
        return {
            "format": "transformers",
            "modality": "text",
            "handler": "text",
            "name": display,
            "notes": mt or arch,
            "known": True,
        }
    if guessed:
        return guessed | {"format": "transformers", "name": display, "known": True}
    return _unknown(path, "config.json has no model_type.")


def _guess_from_name(blob: str) -> dict[str, Any] | None:
    """Filename / path hints. Never a silent Ready for unknown families."""
    n = blob.lower().replace(" ", "-").replace("_", "-")
    if "lora" in n:
        return None
    if any(x in n for x in ("/vae/", "\\vae\\", "/models/vae", "-vae.", "_vae.", "/vae\\")):
        return {"modality": "vae", "handler": "vae", "notes": "VAE companion."}
    if any(x in n for x in ("/text-encoders/", "/text_encoders/", "\\text_encoders\\", "/clip/", "\\clip\\", "/models/clip", "qwen-2.5-vl", "qwen2.5-vl")):
        return {"modality": "clip", "handler": "clip", "notes": "Text encoder / CLIP companion."}
    image_needles = (
        "qwen-image",
        "qwenimage",
        "flux",
        "sdxl",
        "stable-diffusion",
        "sd-1.5",
        "sd15",
        "sd1.5",
        "sd3",
        "hidream",
        "kolors",
        "auraflow",
        "pixart",
        "pony-diffusion",
        "/unet/",
        "/diffusion-models/",
        "/diffusion_models/",
        "/checkpoints/",
        "\\checkpoints\\",
        "/models/stable-diffusion",
    )
    if any(x in n for x in image_needles):
        return {"modality": "image", "handler": "t2i", "notes": "Image weights (name/path)."}
    if any(x in n for x in ("ltxv", "cogvideo", "hunyuan-video", "wan2.1", "wan-2", "text-to-video", "mochi-1")):
        return {"modality": "video", "handler": "t2v", "notes": "Video weights (name/path)."}
    if any(x in n for x in ("whisper", "parakeet", "fish-speech", "f5-tts", "kokoro", "xtts", "openvoice", "sensevoice")):
        return {"modality": "speech", "handler": "stt", "notes": "Speech weights (name/path)."}
    if any(x in n for x in ("musicgen", "stable-audio", "audiogen")):
        return {"modality": "audio", "handler": "t2a", "notes": "Audio weights (name/path)."}
    return None


def _is_gguf(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return f.read(4) == b"GGUF"
    except OSError:
        return False


def _safetensors_keys(path: Path) -> list[str] | None:
    try:
        with path.open("rb") as f:
            n_raw = f.read(8)
            if len(n_raw) < 8:
                return None
            n = struct.unpack("<Q", n_raw)[0]
            if n == 0 or n > 16_000_000:
                return None
            header = json.loads(f.read(n))
            if not isinstance(header, dict):
                return None
            return [k for k in header.keys() if k != "__metadata__"]
    except (OSError, json.JSONDecodeError, ValueError, UnicodeDecodeError):
        return None


def _keys_look_lora(keys: list[str]) -> bool:
    return any("lora" in k.lower() for k in keys)


def _any_lora(files: list[Path]) -> bool:
    return any(_keys_look_lora(_safetensors_keys(p) or []) for p in files)
