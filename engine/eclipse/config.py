from __future__ import annotations

import os
from pathlib import Path

HOST = os.environ.get("ECLIPSE_HOST", "0.0.0.0")
PORT = int(os.environ.get("ECLIPSE_PORT", "7740"))
DATA_DIR = Path(os.environ.get("ECLIPSE_DATA", Path(__file__).resolve().parent.parent / "data"))
PROJECT_DEFAULT = os.environ.get("ECLIPSE_PROJECT", "Hollow")
IDLE_UNLOAD_SEC = int(os.environ.get("ECLIPSE_IDLE_UNLOAD_SEC", "720"))  # long disconnect only
HEADROOM_VRAM_MB = 1536
