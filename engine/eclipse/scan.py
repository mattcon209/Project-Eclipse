"""Search this PC — catalog models where they already live. No copy."""

from __future__ import annotations

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
}

WEIGHT_SUFFIXES = {".gguf", ".ggml"}


def default_roots(home: Path | None = None) -> list[Path]:
    home = Path(home) if home is not None else Path.home()
    local = home / "AppData" / "Local"
    roaming = home / "AppData" / "Roaming"
    env: list[Path] = []
    for key in ("HF_HOME", "HUGGINGFACE_HUB_CACHE", "OLLAMA_MODELS"):
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
        home / ".ollama" / "models",
        home / ".lmstudio" / "models",
        home / ".cache" / "lm-studio",
        local / "lm-studio" / "models",
        roaming / "LM Studio" / "models",
        local / "nomic.ai" / "GPT4All",
        home / ".cache" / "gpt4all",
        home / "Documents" / "LM Studio" / "models",
        home / "OneDrive" / "Documents" / "LM Studio" / "models",
        home / "models",
        home / "ComfyUI" / "models",
        home / "stable-diffusion-webui" / "models",
        home / "automatic1111" / "models",
        home / "text-generation-webui" / "models",
        home / "llama.cpp" / "models",
        home / "koboldcpp",
        home / "Downloads",
        home / "OneDrive" / "Downloads",
        home / "Desktop",
        home / "OneDrive" / "Desktop",
    ]
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
        for fn in filenames:
            if fn.endswith(".part"):
                continue
            fp = p / fn
            low = fn.lower()
            if Path(low).suffix in WEIGHT_SUFFIXES:
                found.append(fp)
            elif p.name.lower() == "blobs" and _looks_gguf(fp):
                found.append(fp)
            if len(found) >= limit:
                return found
        if len(found) >= limit:
            break
    return found


def _looks_gguf(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return f.read(4) == b"GGUF"
    except OSError:
        return False


def ingest(paths: Iterable[Path], lib: Library) -> tuple[list[dict[str, Any]], int, int]:
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
        if resolved.is_file():
            try:
                size = resolved.stat().st_size
            except OSError:
                size = 0
        else:
            size = sum(f.stat().st_size for f in resolved.rglob("*") if f.is_file())
        rec = lib.add(
            {
                "name": info["name"],
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
    items, _, _ = ingest(find_candidates(root), lib)
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
    append_log(job["id"], f"Looking in {len(roots)} folder(s) on this PC — files stay where they are.", state="running", progress=5)
    found: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        for cand in find_candidates(root):
            key = str(cand)
            if key in seen:
                continue
            seen.add(key)
            found.append(cand)
    items, new, dup = ingest(found, lib)
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
