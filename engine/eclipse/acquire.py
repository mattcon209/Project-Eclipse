"""Paste-link acquire. Allowlisted hosts. Size-gate before the first byte."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse, unquote

from eclipse.convert import rent_test
from eclipse.detect import sniff
from eclipse.jobs import append_log, create as create_job
from eclipse.library import LIB, Library, guess_vram_mb, register_card
from eclipse.resource_os import OS, ResourceOS
from eclipse.resources import snapshot as res_snapshot

LARGE_CONFIRM_BYTES = 2 * 1024**3
ALLOWED_SUFFIXES = (
    "huggingface.co",
    "hf.co",
    "github.com",
    "githubusercontent.com",
    "civitai.com",
)
LOOPBACK = {"localhost", "127.0.0.1", "::1"}

Opener = Callable[..., Any]


class AcquireError(ValueError):
    """User-facing acquire failure (not content policy)."""


def host_allowed(host: str | None) -> bool:
    if not host:
        return False
    host = host.lower().rstrip(".")
    if host in LOOPBACK:
        return True
    return any(host == s or host.endswith("." + s) for s in ALLOWED_SUFFIXES)


def classify(raw: str) -> dict[str, Any]:
    text = (raw or "").strip().strip("\"'")
    if not text:
        raise AcquireError("Paste a Hugging Face, GitHub, or Civitai link — or a folder on this PC.")
    if text.startswith("file://"):
        text = unquote(urlparse(text).path)
    expanded = Path(text).expanduser()
    if expanded.exists():
        resolved = expanded.resolve()
        return {
            "kind": "folder" if resolved.is_dir() else "file",
            "path": str(resolved),
            "url": None,
            "host": None,
        }
    parsed = urlparse(text)
    if parsed.scheme in {"http", "https"} and parsed.hostname:
        if not host_allowed(parsed.hostname):
            raise AcquireError(
                "That site isn’t on the install list. Hugging Face, GitHub, Civitai, or a folder on this PC."
            )
        host = parsed.hostname.lower()
        if host in LOOPBACK or host.startswith("127."):
            kind = "file-url"
        elif "civitai" in host:
            kind = "civitai"
        elif "github" in host:
            kind = "github"
        else:
            kind = "hf"
        return {"kind": kind, "path": None, "url": text, "host": host}
    if "/" in text or text.startswith("~") or (len(text) > 1 and text[1] == ":"):
        raise AcquireError("That folder isn’t on this PC.")
    raise AcquireError("Paste a link or a folder on this PC.")


def _headers() -> dict[str, str]:
    h = {"User-Agent": "Eclipse/0.2 (local studio)"}
    tok = os.environ.get("ECLIPSE_HF_TOKEN") or os.environ.get("HF_TOKEN")
    if tok:
        h["Authorization"] = "Bearer " + tok
    return h


def default_opener(req: str | urllib.request.Request, timeout: int = 30) -> Any:
    if isinstance(req, str):
        req = urllib.request.Request(req, headers=_headers())
    return urllib.request.urlopen(req, timeout=timeout)


def _disk_account(ros: ResourceOS) -> None:
    snap = res_snapshot()
    disk = snap.get("disk") or {}
    total = float(disk.get("total_gb") or 0) * 1024**3
    free = float(disk.get("free_gb") or 0) * 1024**3
    pct = float(disk.get("pct") or 0)
    ros.disk_free_bytes = int(free) if free else ros.disk_free_bytes
    ros.disk_used_pct = pct if total else ros.disk_used_pct


def _size_gate(ros: ResourceOS, size_bytes: int) -> tuple[bool, str | None]:
    return ros.can_acquire(size_bytes)


def pick_gguf(siblings: list[dict[str, Any]]) -> dict[str, Any] | None:
    ggufs = [s for s in siblings if str(s.get("rfilename") or s.get("name") or "").lower().endswith(".gguf")]
    if not ggufs:
        return None

    def rank(s: dict[str, Any]) -> tuple[int, int]:
        n = str(s.get("rfilename") or s.get("name") or "").lower()
        if "q4_k_m" in n:
            r = 0
        elif "q4" in n:
            r = 1
        elif "q5" in n:
            r = 2
        else:
            r = 3
        return (r, int(s.get("size") or s.get("sizeKB") or 0))

    return sorted(ggufs, key=rank)[0]


def probe(source: dict[str, Any], opener: Opener = default_opener) -> dict[str, Any]:
    if source["kind"] in {"file", "folder"}:
        p = Path(source["path"])
        if p.is_file():
            return {"name": p.stem, "bytes": p.stat().st_size, "url": None, "filename": p.name}
        total = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
        return {"name": p.name, "bytes": total, "url": None, "filename": None}
    url = source["url"]
    parsed = urlparse(url)
    name = Path(unquote(parsed.path)).name or parsed.hostname or "download"
    if source["kind"] == "file-url" or Path(parsed.path).suffix.lower() in {".gguf", ".ggml", ".safetensors", ".onnx", ".bin", ".pt"}:
        size = _head_size(url, opener)
        return {"name": Path(name).stem, "bytes": size, "url": url, "filename": name}
    if source["kind"] == "hf":
        return _probe_hf(url, opener)
    if source["kind"] == "github":
        return _probe_github(url, opener)
    if source["kind"] == "civitai":
        return _probe_civitai(url, opener)
    size = _head_size(url, opener)
    return {"name": Path(name).stem, "bytes": size, "url": url, "filename": name}


def _head_size(url: str, opener: Opener) -> int | None:
    req = urllib.request.Request(url, method="HEAD", headers=_headers())
    try:
        with opener(req, timeout=20) as resp:
            length = resp.headers.get("Content-Length")
            if length and length.isdigit():
                return int(length)
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError):
        pass
    try:
        req = urllib.request.Request(url, method="GET", headers={**_headers(), "Range": "bytes=0-0"})
        with opener(req, timeout=20) as resp:
            cr = resp.headers.get("Content-Range") or ""
            if "/" in cr:
                total = cr.rsplit("/", 1)[-1]
                if total.isdigit():
                    return int(total)
            length = resp.headers.get("Content-Length")
            if length and length.isdigit() and resp.status != 206:
                return int(length)
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError, AttributeError):
        return None
    return None


def _hf_repo(url: str) -> str:
    parts = [p for p in urlparse(url).path.split("/") if p]
    if "datasets" in parts[:1]:
        raise AcquireError("Datasets install later — paste a model link for now.")
    if parts and parts[0] in {"models", "spaces"}:
        parts = parts[1:]
    if len(parts) < 2:
        raise AcquireError("That Hugging Face link is missing the owner/model.")
    return parts[0] + "/" + parts[1]


def _probe_hf(url: str, opener: Opener) -> dict[str, Any]:
    parsed = urlparse(url)
    path = parsed.path
    if "/resolve/" in path or "/blob/" in path or Path(path).suffix.lower() in {".gguf", ".safetensors"}:
        file_url = url.replace("/blob/", "/resolve/")
        size = _head_size(file_url, opener)
        name = Path(unquote(urlparse(file_url).path)).name
        return {"name": Path(name).stem, "bytes": size, "url": file_url, "filename": name}
    repo = _hf_repo(url)
    api = f"https://huggingface.co/api/models/{repo}?blobs=true"
    try:
        with opener(api, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code in {401, 403}:
            raise AcquireError("This repo is gated. Add a Hugging Face token in Settings.") from e
        if e.code == 404:
            raise AcquireError("Hugging Face doesn’t have that repo.") from e
        raise AcquireError("Couldn’t read that Hugging Face repo.") from e
    except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError) as e:
        raise AcquireError("Can’t reach Hugging Face. Check the PC’s internet.") from e
    siblings = data.get("siblings") or []
    picked = pick_gguf(siblings)
    if picked:
        fn = picked.get("rfilename")
        file_url = f"https://huggingface.co/{repo}/resolve/main/{fn}"
        return {
            "name": data.get("modelId") or repo.split("/")[-1],
            "bytes": int(picked.get("size") or 0) or None,
            "url": file_url,
            "filename": fn,
        }
    names = [str(s.get("rfilename") or "") for s in siblings]
    if any(n == "model_index.json" for n in names):
        raise AcquireError(
            "This is a multi-file image model. Copy the folder onto the PC and Scan, or paste a direct GGUF / safetensors link."
        )
    raise AcquireError("No GGUF in that repo. Paste a direct file link, or Scan a folder already on disk.")


def _probe_github(url: str, opener: Opener) -> dict[str, Any]:
    parsed = urlparse(url)
    path = parsed.path
    if "/releases/download/" in path or "/raw/" in path:
        size = _head_size(url, opener)
        name = Path(unquote(parsed.path)).name
        return {"name": Path(name).stem, "bytes": size, "url": url, "filename": name}
    if "/blob/" in path:
        raw = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
        size = _head_size(raw, opener)
        name = Path(unquote(urlparse(raw).path)).name
        return {"name": Path(name).stem, "bytes": size, "url": raw, "filename": name}
    parts = [p for p in path.split("/") if p]
    if len(parts) < 2:
        raise AcquireError("That GitHub link is missing the owner/repo.")
    owner, repo = parts[0], parts[1]
    api = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    try:
        with opener(api, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise AcquireError("No GitHub release to grab. Paste a direct file link.") from e
        raise AcquireError("Couldn’t read that GitHub repo.") from e
    except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError) as e:
        raise AcquireError("Can’t reach GitHub. Check the PC’s internet.") from e
    assets = data.get("assets") or []
    gguf = [a for a in assets if str(a.get("name") or "").lower().endswith(".gguf")]
    pick = gguf[0] if gguf else (assets[0] if assets else None)
    if not pick or not pick.get("browser_download_url"):
        raise AcquireError("No downloadable release asset. Paste a direct file link.")
    return {
        "name": Path(pick["name"]).stem,
        "bytes": int(pick.get("size") or 0) or None,
        "url": pick["browser_download_url"],
        "filename": pick["name"],
    }


def _probe_civitai(url: str, opener: Opener) -> dict[str, Any]:
    parts = [p for p in urlparse(url).path.split("/") if p]
    model_id = None
    if "models" in parts:
        i = parts.index("models")
        if i + 1 < len(parts) and parts[i + 1].isdigit():
            model_id = parts[i + 1]
    if not model_id:
        raise AcquireError("That Civitai link needs a model number.")
    api = f"https://civitai.com/api/v1/models/{model_id}"
    try:
        with opener(api, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code in {401, 403}:
            raise AcquireError("This Civitai model is gated.") from e
        raise AcquireError("Couldn’t read that Civitai model.") from e
    except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError) as e:
        raise AcquireError("Can’t reach Civitai. Check the PC’s internet.") from e
    versions = data.get("modelVersions") or []
    files = (versions[0].get("files") or []) if versions else []
    if not files:
        raise AcquireError("Civitai listed no files.")
    f0 = files[0]
    size = f0.get("sizeKB")
    size_b = int(float(size) * 1024) if size else None
    return {
        "name": data.get("name") or f"civitai-{model_id}",
        "bytes": size_b,
        "url": f0.get("downloadUrl"),
        "filename": f0.get("name"),
    }


def download_file(url: str, dest: Path, opener: Opener = default_opener) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers=_headers())
    with opener(req, timeout=120) as resp, part.open("wb") as out:
        while True:
            chunk = resp.read(256 * 1024)
            if not chunk:
                break
            out.write(chunk)
    part.replace(dest)
    return dest.stat().st_size


def _apply_detect(rec: dict[str, Any], target: Path, lib: Library) -> dict[str, Any]:
    info = sniff(target)
    rec["format"] = info["format"]
    rec["modality"] = info["modality"]
    rec["handler"] = info["handler"]
    rec["notes"] = info["notes"]
    if info.get("name") and rec.get("name") in {None, "", "download"}:
        rec["name"] = info["name"]
    rec["state"] = "ready" if info["known"] else "inbox"
    if rec["state"] == "ready":
        rec["vram_balanced_mb"] = guess_vram_mb(rec["modality"], int(rec.get("bytes") or 0))
        register_card(rec)
    else:
        rec["vram_balanced_mb"] = None
    return lib.save(rec)


def scan_folder(path: str | Path, lib: Library | None = None) -> list[dict[str, Any]]:
    lib = lib or LIB
    root = Path(path).expanduser().resolve()
    if not root.exists():
        raise AcquireError("That folder isn’t on this PC.")
    added: list[dict[str, Any]] = []
    candidates: list[Path] = []
    if root.is_file():
        candidates = [root]
    else:
        if (root / "model_index.json").exists() or any(root.glob("*.gguf")):
            candidates = [root]
        else:
            for child in sorted(root.iterdir()):
                if child.name.startswith(".") and child.name not in {".cache"}:
                    continue
                if child.is_dir():
                    if (child / "model_index.json").exists() or list(child.glob("*.gguf")) or list(child.glob("*.safetensors")):
                        candidates.append(child)
                    else:
                        for sub in child.iterdir() if child.is_dir() else []:
                            if sub.is_dir() and (
                                (sub / "model_index.json").exists()
                                or list(sub.glob("*.gguf"))
                                or list(sub.glob("config.json"))
                            ):
                                candidates.append(sub)
                elif child.suffix.lower() in {".gguf", ".ggml", ".safetensors"}:
                    candidates.append(child)
    for cand in candidates:
        existing = lib.by_path(str(cand.resolve()))
        if existing:
            added.append(existing)
            continue
        info = sniff(cand)
        size = cand.stat().st_size if cand.is_file() else sum(f.stat().st_size for f in cand.rglob("*") if f.is_file())
        rec = lib.add(
            {
                "name": info["name"],
                "source": str(cand),
                "source_kind": "folder",
                "path": str(cand.resolve()),
                "bytes": size,
                "managed": False,
                "state": "ready" if info["known"] else "inbox",
                "format": info["format"],
                "modality": info["modality"],
                "handler": info["handler"],
                "notes": info["notes"],
                "job_id": None,
                "error": None,
                "quant": None,
                "vram_balanced_mb": guess_vram_mb(info["modality"], size) if info["known"] else None,
            }
        )
        if rec["state"] == "ready":
            register_card(rec)
        added.append(rec)
    return added


def run(
    raw: str,
    *,
    confirm: bool = False,
    lib: Library | None = None,
    ros: ResourceOS | None = None,
    opener: Opener = default_opener,
    large_after: int = LARGE_CONFIRM_BYTES,
) -> dict[str, Any]:
    lib = lib or LIB
    ros = ros or OS
    if ros is OS:
        _disk_account(ros)
    source = classify(raw)
    if source["kind"] in {"file", "folder"}:
        probed = probe(source, opener)
        ok, reason = _size_gate(ros, int(probed["bytes"] or 0))
        if not ok:
            return {"ok": False, "refused": True, "needs_confirm": False, "reason": reason, "record": None}
        added = scan_folder(source["path"], lib=lib)
        rec = added[0] if added else None
        if rec is None:
            return {"ok": False, "refused": True, "reason": "Nothing we can detect in that folder.", "record": None}
        return {"ok": True, "refused": False, "needs_confirm": False, "reason": None, "record": rec}

    try:
        probed = probe(source, opener)
    except AcquireError:
        raise
    size = probed.get("bytes")
    if not size:
        return {
            "ok": False,
            "refused": True,
            "needs_confirm": False,
            "reason": "Size unknown — refuse until probed.",
            "record": None,
        }
    ok, reason = _size_gate(ros, int(size))
    if not ok:
        return {"ok": False, "refused": True, "needs_confirm": False, "reason": reason, "record": None}
    if int(size) >= large_after and not confirm:
        return {
            "ok": False,
            "refused": False,
            "needs_confirm": True,
            "reason": f"This is {int(size) / (1024**3):.1f} GB. Confirm to download.",
            "bytes": int(size),
            "name": probed.get("name"),
            "record": None,
        }
    if not probed.get("url"):
        raise AcquireError("No download URL.")

    rec = lib.add(
        {
            "name": probed.get("name") or "download",
            "source": raw,
            "source_kind": source["kind"],
            "path": None,
            "bytes": int(size),
            "managed": True,
            "state": "downloading",
            "format": None,
            "modality": None,
            "handler": None,
            "notes": None,
            "job_id": None,
            "error": None,
            "quant": None,
            "vram_balanced_mb": None,
        }
    )
    job = create_job("acquire", rec["name"][:80], {"url": raw, "id": rec["id"]})
    rec["job_id"] = job["id"]
    lib.save(rec)
    append_log(job["id"], f"Downloading {rec['name']}…", state="running", progress=5)
    dest_dir = lib.item_dir(rec["id"])
    filename = probed.get("filename") or (rec["name"] + ".bin")
    dest = dest_dir / Path(filename).name
    try:
        written = download_file(probed["url"], dest, opener=opener)
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError) as e:
        rec["state"] = "failed"
        rec["error"] = "Download failed."
        lib.save(rec)
        append_log(job["id"], f"Download failed: {e}", state="failed")
        return {"ok": False, "refused": False, "needs_confirm": False, "reason": rec["error"], "record": rec}
    rec["bytes"] = written
    rec["path"] = str(dest_dir)
    rec["state"] = "detecting"
    lib.save(rec)
    append_log(job["id"], "Detecting…", state="running", progress=80)
    rec = _apply_detect(rec, dest_dir, lib)
    should, why = rent_test(size_bytes=written, free_bytes=ros.disk_free_bytes)
    rec["convert"] = {"plan": should, "reason": why}
    rec = lib.save(rec)
    if rec["state"] == "ready":
        append_log(job["id"], f"Ready · {rec['modality']} · {why}", state="done", progress=100)
    else:
        append_log(job["id"], f"Inbox — {rec.get('notes') or 'identify this.'} Nothing marked Ready.", state="done", progress=100)
    return {"ok": True, "refused": False, "needs_confirm": False, "reason": None, "record": rec}
