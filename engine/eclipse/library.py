"""Model library catalog. Ready only after detect knows the family."""

from __future__ import annotations

import shutil
import time
import uuid
from pathlib import Path
from typing import Any

from eclipse.config import DATA_DIR
from eclipse.resource_os import ModelCard, OS
from eclipse.store import JsonStore


def _root() -> Path:
    return Path(DATA_DIR) / "library"


class Library:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "items").mkdir(parents=True, exist_ok=True)
        self.store = JsonStore(self.root / "catalog.json", {"items": []})

    def items(self) -> list[dict[str, Any]]:
        return list(self.store.read().get("items") or [])

    def get(self, item_id: str) -> dict[str, Any] | None:
        for it in self.items():
            if it.get("id") == item_id:
                return it
        return None

    def by_path(self, path: str) -> dict[str, Any] | None:
        want = str(Path(path).resolve()) if path else ""
        for it in self.items():
            if str(it.get("path") or "") == want:
                return it
        return None

    def add(self, rec: dict[str, Any]) -> dict[str, Any]:
        rec = dict(rec)
        rec.setdefault("id", uuid.uuid4().hex[:10])
        rec.setdefault("created", time.time())
        rec["updated"] = time.time()
        data = self.store.read()
        data["items"].insert(0, rec)
        self.store.write(data)
        return rec

    def save(self, rec: dict[str, Any]) -> dict[str, Any]:
        rec = dict(rec)
        rec["updated"] = time.time()
        data = self.store.read()
        items = data.get("items") or []
        for i, it in enumerate(items):
            if it.get("id") == rec.get("id"):
                items[i] = rec
                data["items"] = items
                self.store.write(data)
                return rec
        return self.add(rec)

    def remove(self, item_id: str) -> dict[str, Any] | None:
        rec = self.get(item_id)
        if not rec:
            return None
        data = self.store.read()
        data["items"] = [it for it in data["items"] if it.get("id") != item_id]
        self.store.write(data)
        if rec.get("managed"):
            folder = rec.get("path")
            if folder:
                p = Path(folder)
                item_root = (self.root / "items" / item_id).resolve()
                try:
                    resolved = p.resolve()
                except OSError:
                    resolved = p
                if resolved == item_root or item_root in resolved.parents or resolved.parent == item_root:
                    shutil.rmtree(item_root, ignore_errors=True)
        return rec

    def item_dir(self, item_id: str) -> Path:
        d = self.root / "items" / item_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def reset(self) -> None:
        self.store.write({"items": []})


LIB = Library(_root())


def list_items() -> list[dict[str, Any]]:
    return LIB.items()


def get_item(item_id: str) -> dict[str, Any] | None:
    return LIB.get(item_id)


def summary() -> dict[str, int]:
    items = LIB.items()
    return {
        "count": len(items),
        "ready": sum(1 for it in items if it.get("state") == "ready"),
        "inbox": sum(1 for it in items if it.get("state") == "inbox"),
    }


def guess_vram_mb(modality: str, size_bytes: int) -> int:
    mb = max(1, int(size_bytes / (1024 * 1024))) if size_bytes else 1
    if modality == "text":
        return int(mb * 1.15) + 512
    if modality == "image":
        return 7000 if mb > 2000 else 4200
    if modality == "video":
        # 16 GB recipes are already short/small. 14000*1.15 refused Max on a 5060 Ti.
        return 11800
    if modality == "lora":
        return 0
    if modality == "speech":
        return 1500
    if modality == "audio":
        return 4000
    return mb


def register_card(rec: dict[str, Any]) -> None:
    if rec.get("state") != "ready":
        return
    vram = int(rec.get("vram_balanced_mb") or guess_vram_mb(rec.get("modality") or "unknown", int(rec.get("bytes") or 0)))
    OS.register(
        ModelCard(
            id=rec["id"],
            modality=str(rec.get("modality") or "unknown"),
            vram_balanced_mb=vram,
            size_bytes=int(rec.get("bytes") or 0),
            quant=str(rec.get("quant") or "native"),
        )
    )
