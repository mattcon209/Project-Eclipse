"""Search this PC — catalog models where they already live. No copy."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable

from eclipse.detect import sniff
from eclipse.jobs import append_log, create as create_job
from eclipse.library import LIB, Library, guess_vram_mb, register_card

SKIP_DIR_NAMES = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".tox",
    "Windows",
    "$Recycle.Bin",
    "System Volume Information",
    "Temp",
    "tmp",
    "INetCache",
    "Packages",
    "Microsoft",
    "OneDrive",  # scanned via explicit Downloads/Desktop roots
}

WEIGHT_SUFFIXES = {".gguf", ".ggml", ".safetensors", ".ckpt"}
SKIP_WEIGHT_HINTS = ("tokenizer", "vocab", "merges", "spiece", "sentencepiece")


def default_roots(home: Path | None = None) -> list[Path]:
    home = Path(home) if home is not None else Path.home()
    local = home / "AppData" / "Local"
    roaming = home / "AppData" / "Roaming"
    env: list[Path] = []
    for key in ("HF_HOME", "HUGGINGFACE_HUB_CACHE", "OLLAMA_MODELS", "LM_STUDIO_MODELS"):
        raw = os.environ.get(key)
        if raw:
            env.append(Path(raw).expanduser())
    extra = os.environ.get("ECLIPSE_SCAN_ROOTS") or ""
    for part in extra.split(os.pathsep):
        part = part.strip()
        if part:
            env.append(Path(part).expanduser())
    guessed = [
        home / ".cache" / "huggingface" / "hub",
        home / ".cache" / "huggingface",
        home / ".ollama",
        home / ".ollama" / "models",
        local / "Ollama",
        local / "Ollama" / "models",
        home / ".lmstudio",
        home / ".lmstudio" / "models",
        home / ".cache" / "lm-studio",
        local / "lm-studio" / "models",
        local / "LM-Studio",
        roaming / "LM Studio",
        roaming / "LM Studio" / "models",
        roaming / "Jan",
        home / "jan" / "models",
        local / "nomic.ai" / "GPT4All",
        home / ".cache" / "gpt4all",
        home / "Documents" / "LM Studio" / "models",
        home / "OneDrive" / "Documents" / "LM Studio" / "models",
        home / "models",
        home / "GameAI",
        home / "GameAI" / "ComfyUI",
        home / "GameAI" / "ComfyUI" / "models",
        home / "GameAI" / "ComfyUI" / "models" / "diffusion_models",
        home / "GameAI" / "ComfyUI" / "models" / "checkpoints",
        home / "GameAI" / "ComfyUI" / "models" / "unet",
        home / "GameAI" / "ComfyUI" / "models" / "vae",
        home / "GameAI" / "ComfyUI" / "models" / "text_encoders",
        home / "GameAI" / "ComfyUI" / "models" / "loras",
        home / "ComfyUI",
        home / "ComfyUI" / "models",
        home / "ComfyUI" / "models" / "checkpoints",
        home / "ComfyUI" / "models" / "diffusion_models",
        home / "ComfyUI" / "models" / "unet",
        home / "Documents" / "ComfyUI",
        home / "OneDrive" / "Documents" / "ComfyUI",
        home / "OneDrive" / "Desktop" / "ComfyUI",
        local / "Programs" / "ComfyUI",
        local / "ComfyUI",
        roaming / "ComfyUI",
        roaming / "StabilityMatrix",
        local / "StabilityMatrix",
        home / "Documents" / "StabilityMatrix",
        home / "ComfyUI_windows_portable" / "ComfyUI",
        home / "stable-diffusion-webui" / "models",
        home / "stable-diffusion-webui" / "models" / "Stable-diffusion",
        home / "stable-diffusion-webui-forge" / "models",
        home / "automatic1111" / "models",
        home / "text-generation-webui" / "models",
        home / "llama.cpp" / "models",
        home / "koboldcpp",
        home / "Downloads",
        home / "OneDrive" / "Downloads",
        home / "Desktop",
        home / "OneDrive" / "Desktop",
    ]
    for letter in "CDEFG":
        for tail in (
            "models",
            "Models",
            "AI",
            "LLM",
            "llms",
            "LM Studio",
            "Ollama",
            "gguf",
            "ComfyUI/models",
            "ComfyUI/models/checkpoints",
            "stable-diffusion-webui/models",
        ):
            guessed.append(Path(f"{letter}:/{tail}"))
    guessed.extend(_lmstudio_configured_dirs(home))
    guessed.extend(_comfy_configured_dirs(home, guessed))
    out: list[Path] = []
    seen: set[str] = set()
    for p in env + guessed:
        try:
            resolved = p.expanduser()
        except OSError:
            continue
        if not resolved.exists():
            continue
        key = str(resolved)
        if key in seen:
            continue
        seen.add(key)
        out.append(resolved)
    return out


COMFY_YAML_KEYS = {
    "checkpoints",
    "unet",
    "diffusion_models",
    "diffusion-models",
    "vae",
    "loras",
    "lora",
    "clip",
    "text_encoders",
    "clip_vision",
    "controlnet",
}


def _comfy_configured_dirs(home: Path, seeds: list[Path]) -> list[Path]:
    """ComfyUI extra_model_paths.yaml points at the real checkpoints folder."""
    found: list[Path] = []
    yamls: list[Path] = []
    seen_yaml: set[str] = set()
    extra_seeds = list(seeds) + [
        home / "ComfyUI",
        home / "Documents" / "ComfyUI",
        home / "OneDrive" / "Desktop" / "ComfyUI",
        home / "OneDrive" / "Documents" / "ComfyUI",
        home / "ComfyUI_windows_portable" / "ComfyUI",
    ]
    for seed in extra_seeds:
        for rel in (
            Path("extra_model_paths.yaml"),
            Path("ComfyUI") / "extra_model_paths.yaml",
            Path("models") / ".." / "extra_model_paths.yaml",
        ):
            y = seed / rel
            try:
                y = y.resolve()
            except OSError:
                continue
            key = str(y)
            if key in seen_yaml:
                continue
            seen_yaml.add(key)
            if y.is_file():
                yamls.append(y)
    for y in yamls:
        found.extend(_parse_extra_model_paths(y))
    return found


def _parse_extra_model_paths(path: Path) -> list[Path]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    out: list[Path] = []
    base: Path | None = None

    def _add(p: Path) -> None:
        try:
            if p.exists():
                out.append(p)
        except OSError:
            return

    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip() or ":" not in line:
            continue
        indent = len(line) - len(line.lstrip(" \t"))
        key, _, val = line.partition(":")
        key = key.strip().lower()
        val = val.strip().strip("\"'")
        if indent == 0:
            base = None
            continue
        if key == "base_path" and val:
            p = Path(val)
            if not p.is_absolute():
                p = (path.parent / p)
            try:
                p = p.expanduser()
            except OSError:
                continue
            base = p
            _add(p)
            _add(p / "models")
            _add(p / "models" / "checkpoints")
            _add(p / "models" / "diffusion_models")
            continue
        if key in {"is_default"} or val in {"|", ">"}:
            continue
        if key not in COMFY_YAML_KEYS and not val:
            continue
        folder = Path(val) if val else Path(key)
        if not folder.is_absolute():
            folder = (base / folder) if base else (path.parent / folder)
        _add(folder)
    return out


def _lmstudio_configured_dirs(home: Path) -> list[Path]:
    """LM Studio lets you pick a model folder. Read it if the json is there."""
    found: list[Path] = []
    for cfg in (
        home / ".lmstudio" / "settings.json",
        home / ".lmstudio" / "user-settings.json",
        home / ".lmstudio" / "config.json",
    ):
        if not cfg.is_file():
            continue
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        found.extend(_paths_in_json(data))
    return found


def _paths_in_json(obj: Any) -> list[Path]:
    out: list[Path] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = str(k).lower()
            if isinstance(v, str) and any(w in key for w in ("path", "folder", "directory", "dir")):
                p = Path(v)
                if p.exists():
                    out.append(p)
            else:
                out.extend(_paths_in_json(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_paths_in_json(v))
    return out


def ollama_blob_names(models_root: Path) -> dict[str, str]:
    """Map blob path → llama3.2:latest style name from Ollama manifests."""
    mapping: dict[str, str] = {}
    manifests = models_root / "manifests"
    blobs = models_root / "blobs"
    if not manifests.exists():
        # models_root may already be ~/.ollama
        alt = models_root / "models" / "manifests"
        blobs = models_root / "models" / "blobs" if alt.exists() else blobs
        manifests = alt if alt.exists() else manifests
    if not manifests.exists():
        return mapping
    for p in manifests.rglob("*"):
        if not p.is_file():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue
        parts = list(p.parts)
        name = p.parent.name
        if "library" in parts:
            i = parts.index("library")
            model = parts[i + 1] if i + 1 < len(parts) else name
            tag = parts[i + 2] if i + 2 < len(parts) else ""
            name = f"{model}:{tag}" if tag and tag not in {model, "latest"} else model
        elif len(parts) >= 2:
            name = parts[-2] if p.name == "latest" else p.name
        digests: list[str] = []
        for layer in data.get("layers") or []:
            if isinstance(layer, dict) and layer.get("digest"):
                digests.append(str(layer["digest"]))
        cfg = data.get("config")
        if isinstance(cfg, dict) and cfg.get("digest"):
            digests.append(str(cfg["digest"]))
        for digest in digests:
            hx = digest.split(":", 1)[-1]
            blob = blobs / f"sha256-{hx}"
            mapping[str(blob)] = name
    return mapping


def find_candidates(root: Path, *, max_depth: int = 8, limit: int = 400) -> list[Path]:
    root = Path(root)
    if not root.exists():
        return []
    if root.is_file():
        return [root]
    found: list[Path] = []
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        p = Path(dirpath)
        try:
            rel = p.relative_to(root)
            depth = 0 if str(rel) == "." else len(rel.parts)
        except ValueError:
            depth = 0
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
        if depth > max_depth:
            dirnames.clear()
            continue
        if (p / "model_index.json").exists():
            found.append(p)
            dirnames.clear()
            if len(found) >= limit:
                break
            continue
        blob_dir = p.name.lower() == "blobs"
        for fn in filenames:
            if fn.endswith(".part"):
                continue
            fp = p / fn
            low = fn.lower()
            if Path(low).suffix in WEIGHT_SUFFIXES:
                found.append(fp)
            elif blob_dir or low.startswith("sha256-"):
                if _looks_gguf(fp):
                    found.append(fp)
            if len(found) >= limit:
                return found
        if len(found) >= limit:
            break
    return found


def _weight_big_enough(path: Path, low: str) -> bool:
    if "lora" in low:
        return True
    try:
        return path.stat().st_size >= 256 * 1024
    except OSError:
        return False


def _looks_gguf(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return f.read(4) == b"GGUF"
    except OSError:
        return False


def ingest(paths: Iterable[Path], lib: Library, names: dict[str, str] | None = None) -> tuple[list[dict[str, Any]], int, int]:
    names = names or {}
    added: list[dict[str, Any]] = []
    new = 0
    dup = 0
    for cand in paths:
        try:
            resolved = cand.resolve()
        except OSError:
            continue
        existing = lib.by_path(str(resolved))
        if existing:
            added.append(existing)
            dup += 1
            continue
        info = sniff(resolved)
        display = names.get(str(resolved)) or info["name"]
        if resolved.is_file():
            try:
                size = resolved.stat().st_size
            except OSError:
                size = 0
        else:
            size = sum(f.stat().st_size for f in resolved.rglob("*") if f.is_file())
        ollama_name = names.get(str(resolved))
        rec = lib.add(
            {
                "name": display,
                "source": str(resolved),
                "source_kind": "scan",
                "path": str(resolved),
                "bytes": size,
                "managed": False,
                "state": "ready" if info["known"] else "inbox",
                "format": info["format"],
                "modality": info["modality"],
                "handler": info["handler"],
                "notes": info["notes"] + " · left on disk, not copied.",
                "job_id": None,
                "error": None,
                "quant": None,
                "vram_balanced_mb": guess_vram_mb(info["modality"], size) if info["known"] else None,
                "runtime": "ollama" if ollama_name else None,
                "ollama_name": ollama_name,
            }
        )
        if rec["state"] == "ready":
            register_card(rec)
        added.append(rec)
        new += 1
    return added, new, dup


def scan_folder(path: str | Path, lib: Library | None = None) -> list[dict[str, Any]]:
    lib = lib or LIB
    root = Path(path).expanduser()
    if not root.exists():
        raise FileNotFoundError("That folder isn’t on this PC.")
    names = ollama_blob_names(root)
    if (root / "models").exists():
        names.update(ollama_blob_names(root / "models"))
    items, _, _ = ingest(find_candidates(root), lib, names)
    return items


def scan_machine(
    *,
    lib: Library | None = None,
    home: Path | None = None,
    extra: str | None = None,
) -> dict[str, Any]:
    lib = lib or LIB
    roots = default_roots(home)
    if extra and extra.strip():
        p = Path(extra.strip()).expanduser()
        if p.exists():
            key = str(p.resolve())
            if key not in {str(r.resolve()) for r in roots}:
                roots.append(p)
    job = create_job("scan", "Search this PC", {"roots": [str(r) for r in roots]})
    append_log(
        job["id"],
        f"Looking in {len(roots)} folder(s) on this PC — files stay where they are.",
        state="running",
        progress=5,
    )
    names: dict[str, str] = {}
    for root in roots:
        names.update(ollama_blob_names(root))
    found: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        for cand in find_candidates(root):
            key = str(cand)
            if key in seen:
                continue
            seen.add(key)
            found.append(cand)
    items, new, dup = ingest(found, lib, names)
    ready = sum(1 for it in items if it.get("state") == "ready")
    append_log(
        job["id"],
        f"Found {len(found)} · added {new} · already listed {dup} · {ready} Ready.",
        state="done",
        progress=100,
    )
    return {
        "ok": True,
        "job_id": job["id"],
        "roots": [str(r) for r in roots],
        "found": len(found),
        "added": new,
        "already": dup,
        "ready": ready,
        "items": items,
    }
