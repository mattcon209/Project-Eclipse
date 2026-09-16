"""Resource OS — optimization-first leases.

Laws:
  - Residency follows the open generation mode.
  - Consecutive prompts in a mode never load/unload.
  - Swap only on mode change or model change.
  - Refuse early on VRAM/disk. Refuse never means content.
  - One heavy GPU job at a time.
  - Long disconnect (~12 min) is the only idle unload.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Literal

VRAM_TOTAL_MB = 16384  # RTX 5060 Ti
HEADROOM_MB = 1536
USABLE_VRAM_MB = VRAM_TOTAL_MB - HEADROOM_MB
DISK_WARN_PCT = 80.0
DISK_REFUSE_PCT = 92.0
LONG_DISCONNECT_SEC = 720

Ladder = Literal["fast", "balanced", "quality", "max"]

# Conservative VRAM recipes for this card (MB). Calibrator overwrites later.
LADDER_VRAM = {
    "fast": 0.70,
    "balanced": 0.90,
    "quality": 1.00,
    "max": 1.15,
}


@dataclass
class ModelCard:
    id: str
    modality: str
    vram_balanced_mb: int
    size_bytes: int
    quant: str = "native"


@dataclass
class Estimate:
    vram_mb: int
    fits: bool
    reason: str | None
    ladder: str
    model_id: str


@dataclass
class RunResult:
    warm: bool
    reloaded: bool
    first_byte_event: str
    prompt: str
    job_id: str | None
    queued: bool
    refused: bool
    refuse_reason: str | None = None


@dataclass
class ResourceOS:
    mode: str | None = None
    model_id: str | None = None
    reloads: int = 0
    unloads: int = 0
    prompts_in_mode: int = 0
    heavy_job_id: str | None = None
    connected: bool = True
    disconnected_at: float | None = None
    last_action: str = "idle"
    catalog: dict[str, ModelCard] = field(default_factory=dict)
    disk_used_pct: float = 0.0
    disk_free_bytes: int = 300 * 1024**3
    now_fn: Any = time.time

    def register(self, card: ModelCard) -> None:
        self.catalog[card.id] = card

    def estimate(self, model_id: str, ladder: Ladder) -> Estimate:
        card = self.catalog.get(model_id)
        if not card:
            return Estimate(0, False, "Model is not in the library.", ladder, model_id)
        vram = int(card.vram_balanced_mb * LADDER_VRAM[ladder])
        if vram > USABLE_VRAM_MB:
            return Estimate(
                vram,
                False,
                f"Won’t fit: ~{vram} MB VRAM, {USABLE_VRAM_MB} MB usable on the 5060 Ti (headroom {HEADROOM_MB} MB).",
                ladder,
                model_id,
            )
        return Estimate(vram, True, None, ladder, model_id)

    def can_acquire(self, size_bytes: int) -> tuple[bool, str | None]:
        if size_bytes <= 0:
            return False, "Size unknown — refuse until probed."
        if size_bytes > self.disk_free_bytes:
            return False, "Won’t fit on disk."
        # refuse at 92% after the write
        if self.disk_used_pct >= DISK_REFUSE_PCT:
            return False, "Disk is past 92% — refuse before write."
        projected = size_bytes / max(self.disk_free_bytes, 1)
        if projected > 0.98:
            return False, "Download would fill the disk."
        return True, None

    def enter_mode(self, mode: str, model_id: str | None = None) -> dict[str, Any]:
        model_id = model_id or self.model_id
        if mode == self.mode and model_id == self.model_id:
            self.last_action = "warm-stay"
            return {"warm": True, "reloaded": False, "mode": mode, "model_id": model_id}
        if self.mode and (mode != self.mode or model_id != self.model_id):
            self._unload()
        self.mode = mode
        if model_id:
            self._load(model_id)
        else:
            self.model_id = None
        self.prompts_in_mode = 0
        self.last_action = "mode-enter"
        return {"warm": False, "reloaded": bool(model_id), "mode": mode, "model_id": model_id}

    def switch_model(self, model_id: str) -> dict[str, Any]:
        if not self.mode:
            return self.enter_mode("image", model_id)
        if model_id == self.model_id:
            return {"warm": True, "reloaded": False, "mode": self.mode, "model_id": model_id}
        self._unload()
        self._load(model_id)
        self.prompts_in_mode = 0
        self.last_action = "model-switch"
        return {"warm": False, "reloaded": True, "mode": self.mode, "model_id": model_id}

    def begin_heavy(self, job_id: str) -> bool:
        if self.heavy_job_id and self.heavy_job_id != job_id:
            return False
        self.heavy_job_id = job_id
        return True

    def end_heavy(self, job_id: str) -> None:
        if self.heavy_job_id == job_id:
            self.heavy_job_id = None

    def run(self, prompt: str, ladder: Ladder = "balanced", job_id: str | None = None) -> RunResult:
        # Content is never inspected — pass through.
        if not self.mode:
            return RunResult(False, False, "", prompt, None, False, True, "No generation mode is open.")
        if not self.model_id:
            return RunResult(False, False, "", prompt, None, False, True, "No model loaded. Install one, then Make.")
        est = self.estimate(self.model_id, ladder)
        if not est.fits:
            return RunResult(False, False, "", prompt, None, False, True, est.reason)
        jid = job_id or "active"
        if self.heavy_job_id and self.heavy_job_id != jid:
            return RunResult(True, False, "", prompt, jid, True, False, None)
        owned = self.begin_heavy(jid)
        if not owned:
            return RunResult(True, False, "", prompt, jid, True, False, None)
        self.prompts_in_mode += 1
        self.last_action = "run-warm"
        first = "first_byte"
        self.end_heavy(jid)
        return RunResult(True, False, first, prompt, jid, False, False)

    def disconnect(self, at: float | None = None) -> None:
        self.connected = False
        self.disconnected_at = at if at is not None else self.now_fn()

    def reconnect(self) -> dict[str, Any]:
        self.connected = True
        self.disconnected_at = None
        return {"mode": self.mode, "model_id": self.model_id}

    def tick(self, now: float | None = None) -> None:
        now = now if now is not None else self.now_fn()
        if self.connected or self.disconnected_at is None:
            return
        if now - self.disconnected_at >= LONG_DISCONNECT_SEC:
            self._unload()
            self.mode = None
            self.last_action = "long-disconnect-unload"

    def kpis(self) -> dict[str, Any]:
        return {
            "reloads_count": self.reloads,
            "unloads_count": self.unloads,
            "prompts_in_mode": self.prompts_in_mode,
            "mode": self.mode,
            "model_id": self.model_id,
            "heavy_job": self.heavy_job_id,
        }

    def reset(self) -> None:
        self.mode = None
        self.model_id = None
        self.reloads = 0
        self.unloads = 0
        self.prompts_in_mode = 0
        self.heavy_job_id = None
        self.connected = True
        self.disconnected_at = None
        self.last_action = "idle"
        self.catalog.clear()
        self.disk_used_pct = 0.0
        self.disk_free_bytes = 300 * 1024**3

    def _load(self, model_id: str) -> None:
        self.model_id = model_id
        self.reloads += 1

    def _unload(self) -> None:
        if self.model_id or self.mode:
            self.unloads += 1
        self.model_id = None
        self.heavy_job_id = None


# Process-wide OS used by the engine.
OS = ResourceOS()
