from __future__ import annotations

import platform
import time
from typing import Any

from eclipse.config import DATA_DIR
from eclipse.resources import snapshot
from eclipse.store import JsonStore

_store = JsonStore(DATA_DIR / "calibration.json", {})


def get() -> dict[str, Any]:
    return _store.read() or {}


def run() -> dict[str, Any]:
    t0 = time.time()
    snap = snapshot()
    rec = {
        "at": t0,
        "elapsed_ms": 0,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "inventory": snap,
        "notes": [
            "Phase 0 calibrator records the box. GEMM / tok-s / SDXL step probes arrive with handlers.",
            "On MattsGamingPC this should see the RTX 5060 Ti 16 GB via nvidia-smi.",
        ],
    }
    rec["elapsed_ms"] = int((time.time() - t0) * 1000)
    _store.write(rec)
    return rec
