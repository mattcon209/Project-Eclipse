"""Image handler — Qwen / Comfy-style split weights via local ComfyUI.

ComfyUI is a runtime, like Ollama for GGUF. GameAI UI and workflows are not copied.
Stub is for tests only. Production never writes a fake still.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

from eclipse.config import DATA_DIR
from eclipse.library import list_items

COMFY = os.environ.get("ECLIPSE_COMFY", "http://127.0.0.1:8188").rstrip("/")

LADDER = {
    "fast": {"steps": 8, "cfg": 2.5, "width": 512, "height": 512},
    "balanced": {"steps": 20, "cfg": 2.5, "width": 768, "height": 768},
    "quality": {"steps": 28, "cfg": 3.5, "width": 768, "height": 768},
    "max": {"steps": 40, "cfg": 4.0, "width": 1024, "height": 1024},
}


class ImageError(RuntimeError):
    pass


class ImageEngine:
    def __init__(self) -> None:
        self._stub: Callable[..., bytes] | None = None
        self._stop = False
        self._proc: subprocess.Popen | None = None
        self.impl: str | None = None
        self.loads = 0

    def set_stub(self, fn: Callable[..., bytes] | None) -> None:
        self._stub = fn
        self.impl = "stub" if fn is not None else None

    def stop(self) -> None:
        self._stop = True
        try:
            _http("POST", COMFY + "/interrupt", {}, timeout=2)
        except ImageError:
            pass

    def generate(
        self,
        rec: dict[str, Any],
        prompt: str,
        *,
        ladder: str = "balanced",
        seed: int = 441029,
        job_id: str = "still",
        source_path: str | None = None,
    ) -> dict[str, Any]:
        self._stop = False
        if rec.get("handler") in {"vae", "clip", "lora"}:
            raise ImageError("Pick the diffusion model in Image, not a VAE / CLIP / LoRA.")
        if rec.get("handler") not in {"t2i", None} and rec.get("modality") != "image":
            raise ImageError("No image model loaded.")
        opts = dict(LADDER.get(ladder) or LADDER["balanced"])
        name = str(rec.get("name") or rec.get("path") or "").lower().replace("_", "-")
        if "4step" in name or "4-step" in name:
            opts["steps"] = min(int(opts["steps"]), 4)
            opts["cfg"] = 1.0
        elif "8step" in name or "8-step" in name:
            opts["steps"] = min(int(opts["steps"]), 8)
            opts["cfg"] = 1.0
        if self._stub is not None:
            self.impl = "stub"
            self.loads += 1
            png = self._stub(rec, prompt, ladder, seed)
            path = _write_still(job_id, png)
            return {"path": str(path), "impl": "stub", "steps": opts["steps"], "seed": seed, "width": opts["width"]}
        stack = resolve_stack(rec)
        self.impl = "comfy"
        _ensure_comfy()
        stack = _bind_comfy_names(stack)
        self.loads += 1
        png = _comfy_run(stack, prompt, opts, seed, job_id, lambda: self._stop)
        path = _write_still(job_id, png)
        return {
            "path": str(path),
            "impl": "comfy",
            "steps": opts["steps"],
            "seed": seed,
            "width": opts["width"],
            "height": opts["height"],
            "unet": stack["unet_name"],
        }


IMAGE = ImageEngine()


def resolve_stack(rec: dict[str, Any]) -> dict[str, str]:
    unet_path = _weight_file(Path(rec.get("path") or rec.get("source") or ""))
    unet_name = _comfy_rel(unet_path) or unet_path.name or str(rec.get("name") or "")
    kind = _kind(rec, unet_path)
    if kind == "companion" or rec.get("handler") in {"vae", "clip", "lora"}:
        raise ImageError("Pick the diffusion model in Image, not a VAE / CLIP / LoRA.")
    dtype = "fp8_e4m3fn" if "fp8" in unet_name.lower() else "default"
    stack = {
        "unet_name": unet_name,
        "unet_path": str(unet_path),
        "vae_name": "",
        "clip_name": "",
        "dtype": dtype,
        "kind": kind,
        "clip_type": _clip_type(unet_name),
        "latent": "EmptySD3LatentImage" if _qwenish(unet_name) else "EmptyLatentImage",
    }
    items = list_items()
    prefer_vae = ("qwen_image_vae",) if _qwenish(unet_name) else ()
    prefer_clip = ("qwen_2.5_vl", "qwen2.5-vl") if _qwenish(unet_name) else ()
    vae_name = _pick_name(items, "vae", prefer=prefer_vae, skip=unet_path) or _beside(
        unet_path, "vae", ("qwen_image_vae.safetensors",)
    )
    clip_name = _pick_name(items, "clip", prefer=prefer_clip, skip=unet_path) or _beside(
        unet_path,
        "text_encoders",
        ("qwen_2.5_vl_7b_fp8_scaled.safetensors", "qwen_2.5_vl_7b.safetensors"),
    )
    if kind == "checkpoint":
        stack["vae_name"] = vae_name or ""
        stack["clip_name"] = clip_name or ""
        if _qwenish(unet_name) and (not vae_name or not clip_name):
            raise ImageError(
                "Qwen Edit checkpoints are UNET-only — they need models/vae/qwen_image_vae "
                "and models/text_encoders/qwen_2.5_vl on disk. Search this PC again. Nothing was faked."
            )
        return stack
    if not vae_name or not clip_name:
        missing = []
        if not vae_name:
            missing.append("VAE (models/vae)")
        if not clip_name:
            missing.append("CLIP / text encoder (models/text_encoders)")
        raise ImageError(
            "This UNET needs " + " and ".join(missing) + " on disk. "
            "Search this PC again. AIO checkpoints in models/checkpoints do not need companions. "
            "Nothing was faked."
        )
    stack["vae_name"] = vae_name
    stack["clip_name"] = clip_name
    return stack


def _qwenish(name: str) -> bool:
    n = (name or "").lower().replace("_", "-")
    return "qwen-image" in n or "qwen-edit" in n or "qwenimage" in n or "qwenedit" in n


def _clip_type(name: str) -> str:
    n = (name or "").lower().replace("_", "-")
    if "qwen" in n:
        return "qwen_image"
    if "flux" in n:
        return "flux"
    if "sd3" in n or "sd-3" in n:
        return "sd3"
    if "hidream" in n:
        return "hidream"
    return "stable_diffusion"


def _kind(rec: dict[str, Any], path: Path) -> str:
    parts = [p.lower() for p in path.parts]
    blob = (str(path) + " " + str(rec.get("name") or "")).lower().replace("_", "-")
    if any(p in parts for p in ("vae", "text_encoders", "text-encoders", "clip", "loras", "lora")):
        return "companion"
    if "diffusion_models" in parts or "unet" in parts:
        return "unet"
    if "checkpoints" in parts or "checkpoint" in blob:
        return "checkpoint"
    if _qwenish(blob) and "vae" not in blob:
        return "unet"
    return "checkpoint"


def _weight_file(path: Path) -> Path:
    if path.is_file() or not path.exists():
        return path
    if path.is_dir():
        hits = [p for p in path.rglob("*") if p.suffix.lower() in {".safetensors", ".ckpt"}]
        if hits:
            try:
                return max(hits, key=lambda p: p.stat().st_size)
            except OSError:
                return hits[0]
    return path


def _comfy_rel(path: Path) -> str:
    markers = {
        "checkpoints",
        "diffusion_models",
        "unet",
        "vae",
        "text_encoders",
        "text-encoders",
        "clip",
        "loras",
    }
    parts = path.parts
    low = [p.lower() for p in parts]
    for i, p in enumerate(low):
        if p in markers and i + 1 < len(parts):
            return "/".join(parts[i + 1 :])
    return path.name


def _comfy_choices(node: str, field: str) -> list[str]:
    try:
        info = _http("GET", f"{COMFY}/object_info/{node}", timeout=8)
    except ImageError:
        return []
    block = info.get(node) or info
    inp = ((block.get("input") or {}).get("required") or {}).get(field)
    if isinstance(inp, list) and inp and isinstance(inp[0], list):
        return [str(x) for x in inp[0]]
    return []


def _match_comfy(name: str, choices: list[str]) -> str | None:
    if not name or not choices:
        return None
    n = name.replace("\\", "/")
    for c in choices:
        if c.replace("\\", "/") == n:
            return c
    base = Path(n).name.lower()
    hits = [c for c in choices if Path(str(c).replace("\\", "/")).name.lower() == base]
    if hits:
        return hits[0]
    stem = Path(base).stem.lower()
    hits = [c for c in choices if Path(str(c).replace("\\", "/")).stem.lower() == stem]
    return hits[0] if hits else None


def _bind_comfy_names(stack: dict[str, str]) -> dict[str, str]:
    try:
        return _bind_comfy_names_once(stack)
    except ImageError as e:
        msg = str(e)
        if not any(s in msg for s in ("has no UNET", "has no checkpoint", "has no VAE", "has no CLIP")):
            raise
        _publish_comfy_paths(stack)
        return _bind_comfy_names_once(stack)


def _bind_comfy_names_once(stack: dict[str, str]) -> dict[str, str]:
    out = dict(stack)
    vaes = _comfy_choices("VAELoader", "vae_name")
    clips = _comfy_choices("CLIPLoader", "clip_name")
    want_vae = stack.get("vae_name") or ""
    want_clip = stack.get("clip_name") or ""
    v = _match_comfy(want_vae, vaes)
    c = _match_comfy(want_clip, clips)
    if want_vae and vaes and not v:
        shown = ", ".join(vaes[:8]) or "(none)"
        disk = stack.get("vae_path") or ""
        where = f" On disk at {disk}." if disk else ""
        raise ImageError(
            f"ComfyUI has no VAE named {want_vae}.{where} "
            f"It sees: {shown}. Pick one of those. Nothing was faked."
        )
    if want_clip and clips and not c:
        shown = ", ".join(clips[:8]) or "(none)"
        disk = stack.get("clip_path") or ""
        where = f" On disk at {disk}." if disk else ""
        raise ImageError(
            f"ComfyUI has no CLIP named {want_clip}.{where} "
            f"It sees: {shown}. Pick one of those. Nothing was faked."
        )
    if v:
        out["vae_name"] = v
    if c:
        out["clip_name"] = c
    if stack.get("kind") == "checkpoint":
        choices = _comfy_choices("CheckpointLoaderSimple", "ckpt_name")
        matched = _match_comfy(stack.get("unet_name") or "", choices)
        if not matched:
            unets = _comfy_choices("UNETLoader", "unet_name")
            u = _match_comfy(stack.get("unet_name") or "", unets)
            if u:
                out["kind"] = "unet"
                out["unet_name"] = u
                return out
        if choices and not matched:
            shown = ", ".join(choices[:8]) or "(none)"
            raise ImageError(
                f"ComfyUI has no checkpoint named {stack.get('unet_name')}. "
                f"It sees: {shown}. Pick one of those. Nothing was faked."
            )
        if matched:
            out["unet_name"] = matched
        return out
    unets = _comfy_choices("UNETLoader", "unet_name")
    matched = _match_comfy(stack.get("unet_name") or "", unets)
    if unets and not matched:
        shown = ", ".join(unets[:8]) or "(none)"
        disk = stack.get("unet_path") or ""
        where = f" On disk at {disk}." if disk else ""
        raise ImageError(
            f"ComfyUI has no UNET named {stack.get('unet_name')}.{where} "
            f"It sees: {shown}. Pick one of those. Nothing was faked."
        )
    if matched:
        out["unet_name"] = matched
    return out


def _short_comfy_err(err: Any) -> str:
    if isinstance(err, dict):
        nodes = err.get("node_errors") or {}
        if isinstance(nodes, dict):
            for node in nodes.values():
                if not isinstance(node, dict):
                    continue
                for e in node.get("errors") or []:
                    if isinstance(e, dict) and (e.get("details") or e.get("message")):
                        return str(e.get("details") or e.get("message"))[:400]
        inner = err.get("error")
        if isinstance(inner, dict) and inner.get("message"):
            return str(inner.get("message"))[:400]
    return str(err)[:400]


def _looks_handler(it: dict[str, Any], handler: str) -> bool:
    if it.get("handler") == handler or it.get("modality") == handler:
        return True
    blob = (str(it.get("path") or "") + " " + str(it.get("name") or "")).lower().replace("_", "-")
    if handler == "vae":
        return any(x in blob for x in ("/vae/", "\\vae\\", "/models/vae", "-vae.", "/vae\\"))
    if handler == "clip":
        return any(
            x in blob
            for x in (
                "text-encoder",
                "text_encoder",
                "/clip/",
                "\\clip\\",
                "qwen-2.5-vl",
                "qwen2.5-vl",
            )
        )
    return False


def _pick_file(
    items: list[dict[str, Any]],
    handler: str,
    *,
    prefer: tuple[str, ...] = (),
    skip: Path | None = None,
    must_prefer: bool = False,
) -> Path | None:
    ranked: list[tuple[int, Path]] = []
    skip_s = str(skip) if skip else ""
    for it in items:
        if it.get("state") != "ready":
            continue
        if not _looks_handler(it, handler):
            continue
        p = Path(it.get("path") or "")
        if not p.name:
            continue
        if skip_s and str(p) == skip_s:
            continue
        low = p.name.lower()
        score = 0
        for i, needle in enumerate(prefer):
            if needle.lower() in low:
                score = 100 - i
                break
        if must_prefer and prefer and score <= 0:
            continue
        ranked.append((score, p))
    ranked.sort(key=lambda x: (-x[0], x[1].name))
    return ranked[0][1] if ranked else None


def _pick_name(
    items: list[dict[str, Any]],
    handler: str,
    *,
    prefer: tuple[str, ...] = (),
    skip: Path | None = None,
    must_prefer: bool = False,
) -> str | None:
    hit = _pick_file(items, handler, prefer=prefer, skip=skip, must_prefer=must_prefer)
    if not hit:
        return None
    return _comfy_rel(hit) or hit.name


def _models_dir_for(unet: Path) -> Path:
    models = unet.parent
    for p in [unet, *unet.parents]:
        if p.name.lower() in {"diffusion_models", "unet", "checkpoints"}:
            return p.parent
        if p.name.lower() == "models":
            return p
    return models


def _beside_file(unet: Path, folder: str, needles: tuple[str, ...]) -> Path | None:
    """First safetensors in models/<folder> whose name contains a needle."""
    if not unet or not needles:
        return None
    d = _models_dir_for(unet) / folder
    if not d.is_dir():
        return None
    want = tuple(n.lower().replace("_", "-") for n in needles)
    for p in sorted(d.iterdir()):
        if p.suffix.lower() != ".safetensors":
            continue
        low = p.name.lower().replace("_", "-")
        if any(n in low for n in want):
            return p
    return None


def _beside_match(unet: Path, folder: str, needles: tuple[str, ...]) -> str | None:
    """Name must contain a needle. Never the first random file in the folder."""
    hit = _beside_file(unet, folder, needles)
    if not hit:
        return None
    return _comfy_rel(hit) or hit.name


def _beside(unet: Path, folder: str, names: tuple[str, ...]) -> str | None:
    if not unet:
        return None
    models = unet.parent
    for p in [unet, *unet.parents]:
        if p.name.lower() in {"diffusion_models", "unet", "checkpoints"}:
            models = p.parent
            break
        if p.name.lower() == "models":
            models = p
            break
    d = models / folder
    for n in names:
        if (d / n).is_file():
            return n
    if d.is_dir():
        for p in sorted(d.iterdir()):
            if p.suffix.lower() == ".safetensors":
                return p.name
    return None


def _write_still(job_id: str, png: bytes) -> Path:
    if not png or png[:8] != b"\x89PNG\r\n\x1a\n":
        raise ImageError("Runtime returned bytes that are not a PNG. Nothing was faked.")
    folder = Path(DATA_DIR) / "stills"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{job_id}.png"
    path.write_bytes(png)
    return path


def _comfy_input_dir() -> Path:
    main = _comfy_main()
    if main:
        d = main.parent / "input"
        d.mkdir(parents=True, exist_ok=True)
        return d
    d = Path(DATA_DIR) / "comfy-input"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _stage_image(path: Path, job_id: str) -> str:
    src = Path(path)
    if not src.is_file():
        raise ImageError("No still to edit. Make one first. Nothing was faked.")
    name = f"eclipse-{job_id}.png"
    dest = _comfy_input_dir() / name
    shutil.copy2(src, dest)
    return name


def _clip_ref(graph: dict[str, Any]) -> list[Any]:
    node = graph.get("8") or {}
    if node.get("class_type") == "CLIPLoader":
        return ["8", 0]
    return ["4", 1]


def _vae_ref(graph: dict[str, Any]) -> list[Any]:
    node = graph.get("9") or {}
    if node.get("class_type") == "VAELoader":
        return ["9", 0]
    return ["4", 2]


def _with_image(graph: dict[str, Any], stack: dict[str, str], prompt: str, opts: dict[str, Any]) -> dict[str, Any]:
    image = stack.get("image") or ""
    if not image:
        return graph
    graph = dict(graph)
    graph["41"] = {"class_type": "LoadImage", "inputs": {"image": image}}
    sampler = dict(graph["3"])
    sampler["inputs"] = dict(sampler.get("inputs") or {})
    if _qwenish(stack.get("unet_name") or ""):
        graph["67"] = {
            "class_type": "ModelSamplingAuraFlow",
            "inputs": {"shift": 3.1, "model": ["4", 0]},
        }
        graph["6"] = {
            "class_type": "TextEncodeQwenImageEditPlus",
            "inputs": {
                "prompt": prompt,
                "clip": _clip_ref(graph),
                "vae": _vae_ref(graph),
                "image1": ["41", 0],
            },
        }
        graph["7"] = {
            "class_type": "TextEncodeQwenImageEditPlus",
            "inputs": {
                "prompt": "",
                "clip": _clip_ref(graph),
                "vae": _vae_ref(graph),
                "image1": ["41", 0],
            },
        }
        sampler["inputs"]["model"] = ["67", 0]
        sampler["inputs"]["denoise"] = 1.0
        graph["3"] = sampler
        return graph
    graph["5"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["41", 0], "vae": _vae_ref(graph)}}
    sampler["inputs"]["denoise"] = float(opts.get("denoise") or 0.55)
    graph["3"] = sampler
    return graph


def _comfy_run(
    stack: dict[str, str],
    prompt: str,
    opts: dict[str, Any],
    seed: int,
    job_id: str,
    stopped: Callable[[], bool],
) -> bytes:
    graph = _workflow(stack, prompt, opts, seed, job_id)
    try:
        queued = _http("POST", COMFY + "/prompt", {"prompt": graph, "client_id": "eclipse-" + job_id}, timeout=30)
    except ImageError as e:
        raise ImageError(f"ComfyUI rejected the graph: {e}") from e
    err = queued.get("error") or queued.get("node_errors")
    if err:
        raise ImageError("ComfyUI rejected the graph: " + _short_comfy_err(err))
    pid = queued.get("prompt_id") or queued.get("promptId")
    if not pid:
        raise ImageError("ComfyUI did not return a prompt_id.")
    deadline = time.time() + 900
    while time.time() < deadline:
        if stopped():
            raise ImageError("Cancelled.")
        hist = _http("GET", COMFY + "/history/" + str(pid), timeout=8)
        rec = hist.get(str(pid)) or hist.get(pid) or {}
        status = (rec.get("status") or {})
        if status.get("status_str") == "error" or rec.get("status_str") == "error":
            raise ImageError(_status_error(rec) or "ComfyUI job failed.")
        images = _history_images(rec)
        if images:
            meta = images[0]
            return _view(meta)
        time.sleep(0.6)
    raise ImageError("ComfyUI timed out waiting for a still.")


def _workflow(stack: dict[str, str], prompt: str, opts: dict[str, Any], seed: int, job_id: str) -> dict[str, Any]:
    latent = stack.get("latent") or (
        "EmptySD3LatentImage" if "edit" in (stack.get("unet_name") or "").lower() else "EmptyLatentImage"
    )
    sampler = {
        "class_type": "KSampler",
        "inputs": {
            "seed": int(seed) % (2**32),
            "steps": int(opts["steps"]),
            "cfg": float(opts["cfg"]),
            "sampler_name": "euler",
            "scheduler": "simple",
            "denoise": 1.0,
            "model": ["4", 0],
            "positive": ["6", 0],
            "negative": ["7", 0],
            "latent_image": ["5", 0],
        },
    }
    save = {"class_type": "SaveImage", "inputs": {"filename_prefix": "eclipse-" + job_id, "images": ["10", 0]}}
    empty = {
        "class_type": latent,
        "inputs": {"width": int(opts["width"]), "height": int(opts["height"]), "batch_size": 1},
    }
    if stack.get("kind") == "checkpoint" and stack.get("vae_name") and stack.get("clip_name"):
        graph = {
            "3": sampler,
            "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": stack["unet_name"]}},
            "5": empty,
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["8", 0]}},
            "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["8", 0]}},
            "8": {
                "class_type": "CLIPLoader",
                "inputs": {"clip_name": stack["clip_name"], "type": stack.get("clip_type") or "qwen_image"},
            },
            "9": {"class_type": "VAELoader", "inputs": {"vae_name": stack["vae_name"]}},
            "10": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["9", 0]}},
            "11": save,
        }
        return _with_image(graph, stack, prompt, opts)
    if stack.get("kind") == "checkpoint":
        graph = {
            "3": sampler,
            "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": stack["unet_name"]}},
            "5": empty,
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["4", 1]}},
            "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["4", 1]}},
            "10": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
            "11": save,
        }
        return _with_image(graph, stack, prompt, opts)
    graph = {
        "3": sampler,
        "4": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": stack["unet_name"], "weight_dtype": stack.get("dtype") or "default"},
        },
        "5": empty,
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["8", 0]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["8", 0]}},
        "8": {
            "class_type": "CLIPLoader",
            "inputs": {"clip_name": stack["clip_name"], "type": stack.get("clip_type") or "qwen_image"},
        },
        "9": {"class_type": "VAELoader", "inputs": {"vae_name": stack["vae_name"]}},
        "10": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["9", 0]}},
        "11": save,
    }
    return _with_image(graph, stack, prompt, opts)


def _history_images(rec: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    outputs = rec.get("outputs") or {}
    if not isinstance(outputs, dict):
        return out
    for node in outputs.values():
        if not isinstance(node, dict):
            continue
        for im in node.get("images") or []:
            if isinstance(im, dict) and im.get("filename"):
                out.append(im)
    return out


def _status_error(rec: dict[str, Any]) -> str:
    msgs = ((rec.get("status") or {}).get("messages")) or rec.get("messages") or []
    bits = []
    for m in msgs:
        bits.append(json.dumps(m, default=str)[:400] if not isinstance(m, str) else m)
    return " ".join(bits)[:800]


def _view(meta: dict[str, Any]) -> bytes:
    q = urllib.parse.urlencode(
        {
            "filename": meta.get("filename") or "",
            "subfolder": meta.get("subfolder") or "",
            "type": meta.get("type") or "output",
        }
    )
    url = COMFY + "/view?" + q
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return r.read()
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise ImageError(f"Could not fetch the still from ComfyUI: {e}") from e


def _comfy_root() -> Path | None:
    main = _comfy_main()
    return main.parent if main else None


def _models_tree(path: Path) -> Path | None:
    for p in [path, *path.parents]:
        if p.name.lower() in {"diffusion_models", "unet", "checkpoints", "vae", "text_encoders", "clip", "loras"}:
            return p.parent
        if p.name.lower() == "models":
            return p
    return path.parent if path.parent.exists() else None


def _expose_weight(src: Path, kind: str) -> None:
    """Hardlink into the running Comfy models folder. File stays where Search found it."""
    root = _comfy_root()
    if not root or not src.is_file():
        return
    slot = {
        "unet": "diffusion_models",
        "checkpoint": "checkpoints",
        "vae": "vae",
        "clip": "text_encoders",
    }.get(kind, "diffusion_models")
    dest_dir = root / "models" / slot
    dest = dest_dir / src.name
    try:
        if dest.exists():
            return
        dest_dir.mkdir(parents=True, exist_ok=True)
        os.link(src, dest)
    except OSError:
        try:
            if not dest.exists():
                dest.symlink_to(src)
        except OSError:
            return


def _publish_comfy_paths(stack: dict[str, str] | None = None) -> None:
    """Tell Comfy about folders Search already catalogued. No copy."""
    trees: list[Path] = []
    seen: set[str] = set()

    def _add(raw: str | Path | None) -> None:
        if not raw:
            return
        p = Path(str(raw))
        tree = _models_tree(p if p.is_dir() else p.parent)
        if not tree:
            return
        key = str(tree)
        if key not in seen:
            seen.add(key)
            trees.append(tree)
        kind = "unet"
        parts = [x.lower() for x in p.parts]
        if "vae" in parts:
            kind = "vae"
        elif any(x in parts for x in ("text_encoders", "text-encoders", "clip")):
            kind = "clip"
        elif "checkpoints" in parts:
            kind = "checkpoint"
        if p.is_file():
            _expose_weight(p, kind)

    if stack:
        _add(stack.get("unet_path"))
        _add(stack.get("vae_path"))
        _add(stack.get("clip_path"))
        _add(stack.get("clip_path2"))
        raw = stack.get("unet_path")
        if raw:
            models = _models_dir_for(Path(raw))
            for folder, kind in (
                ("diffusion_models", "unet"),
                ("unet", "unet"),
                ("checkpoints", "checkpoint"),
                ("vae", "vae"),
                ("text_encoders", "clip"),
                ("clip", "clip"),
            ):
                d = models / folder
                if not d.is_dir():
                    continue
                for child in d.iterdir():
                    if child.suffix.lower() in {".safetensors", ".ckpt"}:
                        _add(child)
    for it in list_items():
        if it.get("state") == "ready":
            _add(it.get("path") or it.get("source"))
    lines = ["# Eclipse — weights stay where Search found them.", ""]
    for i, tree in enumerate(trees):
        key = "eclipse" if i == 0 else f"eclipse_{i}"
        base = tree.parent if tree.name.lower() == "models" else tree
        models = base / "models" if (base / "models").is_dir() else tree
        lines.append(f"{key}:")
        lines.append(f"  base_path: {_yaml_escape(base)}")
        if models.is_dir():
            for sub, field in (
                ("checkpoints", "checkpoints"),
                ("diffusion_models", "diffusion_models"),
                ("unet", "unet"),
                ("vae", "vae"),
                ("text_encoders", "text_encoders"),
                ("clip", "clip"),
                ("loras", "loras"),
            ):
                folder = models / sub
                if folder.is_dir():
                    lines.append(f"  {field}: models/{sub}")
        lines.append("")
    dest = Path(DATA_DIR) / "comfy_extra_model_paths.yaml"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    root = _comfy_root()
    if root:
        _merge_eclipse_yaml(root / "extra_model_paths.yaml", "\n".join(lines))


def _yaml_escape(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/")


def _merge_eclipse_yaml(path: Path, body: str) -> None:
    try:
        old = path.read_text(encoding="utf-8") if path.is_file() else ""
    except OSError:
        return
    kept: list[str] = []
    skip = False
    for line in old.splitlines():
        if line.startswith("eclipse:") or line.startswith("eclipse_"):
            skip = True
            continue
        if skip and line and not line[:1].isspace() and not line.startswith("#"):
            skip = False
        if skip:
            continue
        kept.append(line)
    text = "\n".join(kept).rstrip() + "\n\n" + body.strip() + "\n"
    try:
        path.write_text(text, encoding="utf-8")
    except OSError:
        return


def _ensure_comfy() -> None:
    if _comfy_up():
        return
    main = _comfy_main()
    py = _comfy_python(main.parent) if main else None
    if not main or not py:
        raise ImageError(
            "No image runtime. Start ComfyUI on 127.0.0.1:8188 (GameAI\\ComfyUI) or set ECLIPSE_COMFY. "
            "Weights stay on disk; nothing was faked."
        )
    creation = 0x00000008 if os.name == "nt" else 0  # DETACHED_PROCESS on Windows
    cmd = [str(py), str(main), "--listen", "127.0.0.1", "--port", "8188", "--lowvram"]
    extra = Path(DATA_DIR) / "comfy_extra_model_paths.yaml"
    if extra.is_file():
        cmd += ["--extra-model-paths-config", str(extra)]
    IMAGE._proc = subprocess.Popen(
        cmd,
        cwd=str(main.parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creation if os.name == "nt" else 0,
    )
    deadline = time.time() + 90
    while time.time() < deadline:
        if _comfy_up():
            return
        time.sleep(0.5)
    raise ImageError("ComfyUI was started but did not come up on 8188.")


def _comfy_up() -> bool:
    for path in ("/system_stats", "/object_info", "/"):
        try:
            urllib.request.urlopen(COMFY + path, timeout=1.2).read(64)
            return True
        except (urllib.error.URLError, TimeoutError, OSError):
            continue
    return False


def _comfy_main() -> Path | None:
    home = Path.home()
    for p in (
        home / "GameAI" / "ComfyUI" / "main.py",
        home / "ComfyUI" / "main.py",
        home / "ComfyUI_windows_portable" / "ComfyUI" / "main.py",
        home / "AI-Video-Server" / "ComfyUI_windows_portable" / "ComfyUI" / "main.py",
        Path(os.environ.get("ECLIPSE_COMFY_ROOT", "")) / "main.py",
    ):
        if p.is_file():
            return p
    return None


def _comfy_python(root: Path) -> Path | None:
    for p in (
        root / "venv" / "Scripts" / "python.exe",
        root / ".venv" / "Scripts" / "python.exe",
        root / "python_embeded" / "python.exe",
        root / "venv" / "bin" / "python",
        root / ".venv" / "bin" / "python",
        Path(sys.executable),
    ):
        if p.is_file():
            return p
    return None


def _http(method: str, url: str, body: dict[str, Any] | None = None, timeout: float = 30) -> dict[str, Any]:
    data = None if body is None or method == "GET" else json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:400]
        raise ImageError(detail or str(e)) from e
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise ImageError(str(e)) from e
    if not raw:
        return {}
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}
