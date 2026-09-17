"""Video handler — LTXV / Hunyuan / Wan via local ComfyUI.

Same ComfyUI runtime as Image. Stub is tests only. Production never writes a fake clip.
16 GB recipes stay short and small. Queued, not 1080p.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Callable

from eclipse.config import DATA_DIR
from eclipse.image_runtime import (
    COMFY,
    IMAGE,
    ImageError,
    _beside,
    _beside_file,
    _beside_match,
    _bind_comfy_names,
    _comfy_choices,
    _comfy_rel,
    _ensure_comfy,
    _history_images,
    _http,
    _kind,
    _match_comfy,
    _pick_file,
    _pick_name,
    _short_comfy_err,
    _stage_image,
    _status_error,
    _view,
    _weight_file,
    resolve_stack,
)
from eclipse.library import list_items

# LTXV length is 1+8k; Hunyuan/Wan length is 1+4k. 9/17/25/33 fit both.
# Width/height divisible by 32 (LTXV) and 16 (Wan/Hunyuan). Length 1+8k / 1+4k.
# Fast is no longer a 384×256 8-step smear — that looked like noise on Wan 2.2 5B.
LADDER = {
    "fast": {"steps": 12, "cfg": 4.0, "width": 512, "height": 320, "frames": 17, "fps": 16},
    "balanced": {"steps": 20, "cfg": 5.0, "width": 640, "height": 384, "frames": 17, "fps": 24},
    "quality": {"steps": 24, "cfg": 5.0, "width": 704, "height": 384, "frames": 25, "fps": 24},
    "max": {"steps": 30, "cfg": 5.0, "width": 768, "height": 480, "frames": 33, "fps": 24},
}

VideoError = ImageError


class VideoEngine:
    def __init__(self) -> None:
        self._stub: Callable[..., bytes] | None = None
        self._stop = False
        self.impl: str | None = None
        self.loads = 0

    def set_stub(self, fn: Callable[..., bytes] | None) -> None:
        self._stub = fn
        self.impl = "stub" if fn is not None else None

    def stop(self) -> None:
        self._stop = True
        IMAGE.stop()

    def generate(
        self,
        rec: dict[str, Any],
        prompt: str,
        *,
        ladder: str = "balanced",
        seed: int = 441029,
        job_id: str = "clip",
        source_path: str | None = None,
    ) -> dict[str, Any]:
        self._stop = False
        if rec.get("handler") in {"vae", "clip", "lora"}:
            raise VideoError("Pick the video diffusion model, not a VAE / CLIP / LoRA.")
        family = family_of(rec)
        if not family:
            raise VideoError(
                "This trainer is LTXV / Hunyuan / Wan. CogVideo / Mochi wait. "
                "Pick those weights. Nothing was faked."
            )
        if rec.get("modality") not in {"video", "image"} and rec.get("handler") not in {"t2v", "t2i"}:
            raise VideoError("No video model loaded. Nothing was faked.")
        reason = refuse_pair(rec, source_path)
        if reason:
            raise VideoError(reason)
        opts = dict(LADDER.get(ladder) or LADDER["balanced"])
        if family == "wan":
            opts["cfg"] = max(float(opts["cfg"]), 5.0)
        if self._stub is not None:
            self.impl = "stub"
            self.loads += 1
            blob = self._stub(rec, prompt, ladder, seed)
            path = _write_clip(job_id, blob)
            return {
                "path": str(path),
                "impl": "stub",
                "steps": opts["steps"],
                "seed": seed,
                "width": opts["width"],
                "frames": opts["frames"],
                "family": family,
            }
        stack = _video_stack(rec, family)
        self.impl = "comfy"
        _ensure_comfy()
        stack = _bind_video_names(stack)
        if source_path:
            stack["image"] = _stage_image(Path(source_path), job_id)
        self.loads += 1
        blob = _comfy_clip(stack, prompt, opts, seed, job_id, lambda: self._stop)
        path = _write_clip(job_id, blob)
        return {
            "path": str(path),
            "impl": "comfy",
            "steps": opts["steps"],
            "seed": seed,
            "width": opts["width"],
            "height": opts["height"],
            "frames": opts["frames"],
            "family": family,
            "unet": stack.get("unet_name"),
        }


VIDEO = VideoEngine()


def _name_blob(rec: dict[str, Any] | None) -> str:
    rec = rec or {}
    name = str(rec.get("name") or "")
    fname = Path(str(rec.get("path") or "")).name
    return (name + " " + fname).lower().replace("_", "-")


def family_of(rec: dict[str, Any] | None) -> str | None:
    blob = _name_blob(rec)
    if any(x in blob for x in ("ltxv", "ltx-video", "ltxvideo", "ltx-2")):
        return "ltxv"
    if "hunyuan" in blob:
        return "hunyuan"
    if any(x in blob for x in ("wan2", "wan-2", "wan21", "wan22", "wan-i2v", "wan-t2v")):
        return "wan"
    if rec and rec.get("handler") == "t2v":
        return None
    return None


def refuse_pair(rec: dict[str, Any], source_path: str | None) -> str | None:
    blob = _name_blob(rec)
    i2v = bool(source_path)
    if "hunyuan" in blob:
        t2v_only = "t2v" in blob and "image-to-video" not in blob and "i2v" not in blob
        i2v_only = "image-to-video" in blob or ("i2v" in blob and "t2v" not in blob)
        if i2v and t2v_only:
            return "This Hunyuan file is T2V. Pick the image-to-video Hunyuan for a still, or Make without a still."
        if not i2v and i2v_only:
            return "This Hunyuan file is I2V. Put a still on the strip, then Make. Nothing was faked."
    if any(x in blob for x in ("wan2", "wan-2", "wan21", "wan22")):
        t2v_only = "t2v" in blob and "i2v" not in blob and "ti2v" not in blob
        i2v_only = "i2v" in blob and "t2v" not in blob and "ti2v" not in blob
        if i2v and t2v_only:
            return "This Wan file is T2V. Pick an I2V / TI2V Wan for a still, or Make without a still."
        if not i2v and i2v_only:
            return "This Wan file is I2V. Put a still on the strip, then Make. Nothing was faked."
    return None


def write_tiny_webp(path: Path) -> Path:
    """Test helper. Real generate never calls this."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # 1×1 lossy VP8 webp
    path.write_bytes(
        bytes.fromhex(
            "52494646240000005745425056503820180000003001009d012a010001000100"
            "430000fed2fffff000000000"
        )
    )
    return path


def _video_stack(rec: dict[str, Any], family: str) -> dict[str, str]:
    if family == "ltxv":
        stack = resolve_stack(rec)
        items = list_items()
        clip = stack.get("clip_name") or _pick_name(items, "clip", prefer=("t5xxl", "t5-xxl", "t5xxl_fp16", "t5xxl_fp8"))
        if stack.get("kind") != "checkpoint" and not clip:
            raise VideoError(
                "LTXV needs t5xxl in models/text_encoders. Search this PC. Nothing was faked."
            )
        stack["family"] = "ltxv"
        stack["clip_name"] = clip or stack.get("clip_name") or ""
        stack["clip_type"] = "ltxv"
        return stack
    unet_path = _weight_file(Path(rec.get("path") or rec.get("source") or ""))
    unet_name = _comfy_rel(unet_path) or unet_path.name or str(rec.get("name") or "")
    kind = _kind(rec, unet_path)
    items = list_items()
    dtype = "fp8_e4m3fn" if "fp8" in unet_name.lower() else "default"
    stack = {
        "family": family,
        "unet_name": unet_name,
        "unet_path": str(unet_path),
        "kind": "unet" if kind == "unet" else "checkpoint",
        "dtype": dtype,
        "clip_name": "",
        "clip_name2": "",
        "vae_name": "",
        "clip_type": "hunyuan_video" if family == "hunyuan" else "wan",
    }
    if family == "hunyuan":
        clip1 = _pick_file(items, "clip", prefer=("clip_l", "clip-l"), must_prefer=True)
        clip2 = _pick_file(items, "clip", prefer=("llava_llama3", "llava-llama", "llava_llama"), must_prefer=True)
        vae_p = _pick_file(items, "vae", prefer=("hunyuan_video_vae", "hunyuan-video-vae"), must_prefer=True) or _beside_file(
            unet_path, "vae", ("hunyuan-video-vae", "hunyuan_video_vae")
        )
        stack["clip_name"] = (_comfy_rel(clip1) or clip1.name) if clip1 else ""
        stack["clip_path"] = str(clip1) if clip1 else ""
        stack["clip_name2"] = (_comfy_rel(clip2) or clip2.name) if clip2 else ""
        stack["clip_path2"] = str(clip2) if clip2 else ""
        stack["vae_name"] = (_comfy_rel(vae_p) or vae_p.name) if vae_p else ""
        stack["vae_path"] = str(vae_p) if vae_p else ""
        if not stack["clip_name"] or not stack["clip_name2"] or not stack["vae_name"]:
            raise VideoError(
                "Hunyuan needs clip_l + llava_llama3 in text_encoders and hunyuan_video_vae in vae. "
                "Search this PC. Nothing was faked."
            )
        return stack
    clip_p = _pick_file(items, "clip", prefer=("umt5_xxl", "umt5-xxl", "umt5"), must_prefer=True) or _beside_file(
        unet_path, "text_encoders", ("umt5",)
    )
    vae_p = _pick_file(
        items,
        "vae",
        prefer=("wan2.2_vae", "wan_2.2_vae", "wan2.1_vae", "wan_2.1_vae", "wan-2.1-vae", "wan2.2-vae", "wan2.1-vae"),
        must_prefer=True,
    ) or _beside_file(
        unet_path, "vae", ("wan2.2_vae", "wan_2.2_vae", "wan2.1_vae", "wan_2.1_vae", "wan2.2-vae", "wan2.1-vae")
    )
    stack["clip_name"] = (_comfy_rel(clip_p) or clip_p.name) if clip_p else ""
    stack["clip_path"] = str(clip_p) if clip_p else ""
    stack["vae_name"] = (_comfy_rel(vae_p) or vae_p.name) if vae_p else ""
    stack["vae_path"] = str(vae_p) if vae_p else ""
    if not stack["clip_name"] or not stack["vae_name"]:
        raise VideoError(
            "Wan needs umt5 in text_encoders and a Wan VAE in vae (not taesdxl). "
            "Search this PC. Nothing was faked."
        )
    return stack


def _bind_video_names(stack: dict[str, str]) -> dict[str, str]:
    out = _bind_comfy_names(stack)
    clips = _comfy_choices("CLIPLoader", "clip_name") or _comfy_choices("DualCLIPLoader", "clip_name1")
    if stack.get("family") == "hunyuan":
        dual = _comfy_choices("DualCLIPLoader", "clip_name1")
        c1 = _match_comfy(stack.get("clip_name") or "", dual or clips)
        c2 = _match_comfy(stack.get("clip_name2") or "", _comfy_choices("DualCLIPLoader", "clip_name2") or dual or clips)
        if c1:
            out["clip_name"] = c1
        if c2:
            out["clip_name2"] = c2
        return out
    c = _match_comfy(stack.get("clip_name") or "", clips)
    if c:
        out["clip_name"] = c
    return out


def _comfy_clip(
    stack: dict[str, str],
    prompt: str,
    opts: dict[str, Any],
    seed: int,
    job_id: str,
    stopped: Callable[[], bool],
) -> bytes:
    graph = _workflow(stack, prompt, opts, seed, job_id)
    try:
        queued = _http("POST", os.environ.get("ECLIPSE_COMFY", "http://127.0.0.1:8188").rstrip("/") + "/prompt", {"prompt": graph, "client_id": "eclipse-" + job_id}, timeout=30)
    except ImageError as e:
        raise VideoError(f"ComfyUI rejected the graph: {e}") from e
    err = queued.get("error") or queued.get("node_errors")
    if err:
        raise VideoError("ComfyUI rejected the graph: " + _short_comfy_err(err))
    pid = queued.get("prompt_id") or queued.get("promptId")
    if not pid:
        raise VideoError("ComfyUI did not return a prompt_id.")
    comfy = os.environ.get("ECLIPSE_COMFY", "http://127.0.0.1:8188").rstrip("/")
    deadline = time.time() + 1800
    while time.time() < deadline:
        if stopped():
            raise VideoError("Cancelled.")
        hist = _http("GET", COMFY + "/history/" + str(pid), timeout=8)
        rec = hist.get(str(pid)) or hist.get(pid) or {}
        status = rec.get("status") or {}
        if status.get("status_str") == "error" or rec.get("status_str") == "error":
            raise VideoError(_status_error(rec) or "ComfyUI job failed.")
        files = _history_images(rec) or _history_gifs(rec)
        if files:
            return _view(files[0])
        time.sleep(0.8)
    raise VideoError("ComfyUI timed out waiting for a clip.")


def _history_gifs(rec: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    outputs = rec.get("outputs") or {}
    if not isinstance(outputs, dict):
        return out
    for node in outputs.values():
        if not isinstance(node, dict):
            continue
        for key in ("gifs", "videos", "images"):
            for im in node.get(key) or []:
                if isinstance(im, dict) and im.get("filename"):
                    out.append(im)
    return out


def _workflow(stack: dict[str, str], prompt: str, opts: dict[str, Any], seed: int, job_id: str) -> dict[str, Any]:
    family = stack.get("family") or "ltxv"
    w, h, n = int(opts["width"]), int(opts["height"]), int(opts["frames"])
    fps = int(opts.get("fps") or 24)
    save = {
        "class_type": "SaveAnimatedWEBP",
        "inputs": {
            "filename_prefix": "eclipse-" + job_id,
            "fps": fps,
            "lossless": False,
            "quality": 80,
            "method": "default",
            "images": ["10", 0],
        },
    }
    if family == "ltxv":
        return _ltxv_graph(stack, prompt, opts, seed, w, h, n, fps, save)
    if family == "hunyuan":
        return _hunyuan_graph(stack, prompt, opts, seed, w, h, n, save)
    return _wan_graph(stack, prompt, opts, seed, w, h, n, save)


def _ltxv_graph(
    stack: dict[str, str],
    prompt: str,
    opts: dict[str, Any],
    seed: int,
    w: int,
    h: int,
    n: int,
    fps: int,
    save: dict[str, Any],
) -> dict[str, Any]:
    clip_node = "8"
    vae_ref: list[Any]
    model_ref = ["4", 0]
    if stack.get("kind") == "checkpoint":
        loader = {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": stack["unet_name"]}}
        vae_ref = ["4", 2]
        if stack.get("clip_name"):
            graph_clip = {
                "class_type": "CLIPLoader",
                "inputs": {"clip_name": stack["clip_name"], "type": "ltxv"},
            }
        else:
            graph_clip = None
            clip_node = "4"
    else:
        loader = {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": stack["unet_name"], "weight_dtype": stack.get("dtype") or "default"},
        }
        graph_clip = {
            "class_type": "CLIPLoader",
            "inputs": {"clip_name": stack["clip_name"], "type": "ltxv"},
        }
        vae_ref = ["9", 0]
    pos = {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": [clip_node if graph_clip else "4", 0 if graph_clip else 1]}}
    neg = {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": [clip_node if graph_clip else "4", 0 if graph_clip else 1]}}
    graph: dict[str, Any] = {
        "4": loader,
        "6": pos,
        "7": neg,
        "10": {"class_type": "VAEDecode", "inputs": {"samples": ["72", 0], "vae": vae_ref}},
        "11": save,
        "73": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
    }
    if graph_clip:
        graph["8"] = graph_clip
        graph["6"]["inputs"]["clip"] = ["8", 0]
        graph["7"]["inputs"]["clip"] = ["8", 0]
    if stack.get("kind") != "checkpoint":
        graph["9"] = {"class_type": "VAELoader", "inputs": {"vae_name": stack["vae_name"]}}
    if stack.get("image"):
        graph["41"] = {"class_type": "LoadImage", "inputs": {"image": stack["image"]}}
        graph["5"] = {
            "class_type": "LTXVImgToVideo",
            "inputs": {
                "positive": ["6", 0],
                "negative": ["7", 0],
                "vae": vae_ref,
                "image": ["41", 0],
                "width": w,
                "height": h,
                "length": n,
                "batch_size": 1,
                "strength": 1.0,
            },
        }
        graph["69"] = {
            "class_type": "LTXVConditioning",
            "inputs": {"positive": ["5", 0], "negative": ["5", 1], "frame_rate": fps},
        }
        latent = ["5", 2]
        pos_ref, neg_ref = ["69", 0], ["69", 1]
    else:
        graph["5"] = {
            "class_type": "EmptyLTXVLatentVideo",
            "inputs": {"width": w, "height": h, "length": n, "batch_size": 1},
        }
        graph["69"] = {
            "class_type": "LTXVConditioning",
            "inputs": {"positive": ["6", 0], "negative": ["7", 0], "frame_rate": fps},
        }
        latent = ["5", 0]
        pos_ref, neg_ref = ["69", 0], ["69", 1]
    graph["71"] = {
        "class_type": "LTXVScheduler",
        "inputs": {
            "steps": int(opts["steps"]),
            "max_shift": 2.05,
            "base_shift": 0.95,
            "stretch": True,
            "terminal": 0.1,
            "latent": latent,
        },
    }
    graph["72"] = {
        "class_type": "SamplerCustom",
        "inputs": {
            "model": model_ref,
            "add_noise": True,
            "noise_seed": int(seed) % (2**32),
            "cfg": float(opts["cfg"]),
            "positive": pos_ref,
            "negative": neg_ref,
            "sampler": ["73", 0],
            "sigmas": ["71", 0],
            "latent_image": latent,
        },
    }
    return graph


def _hunyuan_graph(
    stack: dict[str, str],
    prompt: str,
    opts: dict[str, Any],
    seed: int,
    w: int,
    h: int,
    n: int,
    save: dict[str, Any],
) -> dict[str, Any]:
    graph: dict[str, Any] = {
        "4": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": stack["unet_name"], "weight_dtype": stack.get("dtype") or "default"},
        },
        "8": {
            "class_type": "DualCLIPLoader",
            "inputs": {
                "clip_name1": stack["clip_name"],
                "clip_name2": stack["clip_name2"],
                "type": "hunyuan_video",
            },
        },
        "9": {"class_type": "VAELoader", "inputs": {"vae_name": stack["vae_name"]}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["8", 0]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["8", 0]}},
        "3": {
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
        },
        "10": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["9", 0]}},
        "11": save,
    }
    if stack.get("image"):
        graph["41"] = {"class_type": "LoadImage", "inputs": {"image": stack["image"]}}
        guidance = "v2 (replace)" if "replace" in (stack.get("unet_name") or "").lower() else "v1 (concat)"
        graph["5"] = {
            "class_type": "HunyuanImageToVideo",
            "inputs": {
                "positive": ["6", 0],
                "vae": ["9", 0],
                "width": w,
                "height": h,
                "length": n,
                "batch_size": 1,
                "guidance_type": guidance,
                "start_image": ["41", 0],
            },
        }
        graph["3"]["inputs"]["positive"] = ["5", 0]
        graph["3"]["inputs"]["latent_image"] = ["5", 1]
    else:
        graph["5"] = {
            "class_type": "EmptyHunyuanLatentVideo",
            "inputs": {"width": w, "height": h, "length": n, "batch_size": 1},
        }
    return graph


def _wan_graph(
    stack: dict[str, str],
    prompt: str,
    opts: dict[str, Any],
    seed: int,
    w: int,
    h: int,
    n: int,
    save: dict[str, Any],
) -> dict[str, Any]:
    graph: dict[str, Any] = {
        "4": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": stack["unet_name"], "weight_dtype": stack.get("dtype") or "default"},
        },
        "8": {"class_type": "CLIPLoader", "inputs": {"clip_name": stack["clip_name"], "type": "wan"}},
        "9": {"class_type": "VAELoader", "inputs": {"vae_name": stack["vae_name"]}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["8", 0]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["8", 0]}},
        "3": {
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
        },
        "10": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["9", 0]}},
        "11": save,
    }
    if stack.get("image"):
        graph["41"] = {"class_type": "LoadImage", "inputs": {"image": stack["image"]}}
        graph["5"] = {
            "class_type": "WanImageToVideo",
            "inputs": {
                "positive": ["6", 0],
                "negative": ["7", 0],
                "vae": ["9", 0],
                "width": w,
                "height": h,
                "length": n,
                "batch_size": 1,
                "start_image": ["41", 0],
            },
        }
        graph["3"]["inputs"]["positive"] = ["5", 0]
        graph["3"]["inputs"]["negative"] = ["5", 1]
        graph["3"]["inputs"]["latent_image"] = ["5", 2]
    else:
        graph["5"] = {
            "class_type": "EmptyHunyuanLatentVideo",
            "inputs": {"width": w, "height": h, "length": n, "batch_size": 1},
        }
    return graph


def _looks_clip(blob: bytes) -> bool:
    if len(blob) < 12:
        return False
    if blob[:4] == b"RIFF" and blob[8:12] == b"WEBP":
        return True
    if blob[:4] == b"\x1aE\xdf\xa3":
        return True
    if blob[4:8] == b"ftyp":
        return True
    return False


def _write_clip(job_id: str, blob: bytes) -> Path:
    if not blob or not _looks_clip(blob):
        raise VideoError("Runtime returned bytes that are not a clip. Nothing was faked.")
    folder = Path(DATA_DIR) / "clips"
    folder.mkdir(parents=True, exist_ok=True)
    if blob[:4] == b"RIFF":
        ext = ".webp"
    elif blob[4:8] == b"ftyp":
        ext = ".mp4"
    else:
        ext = ".webm"
    path = folder / f"{job_id}{ext}"
    path.write_bytes(blob)
    return path
