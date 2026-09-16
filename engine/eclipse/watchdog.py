from __future__ import annotations

import threading
import time
from typing import Any

from eclipse.config import DATA_DIR
from eclipse.store import JsonStore

_store = JsonStore(
    DATA_DIR / "watchdog.json",
    {"alive": False, "started": None, "heartbeat": None, "restarts": 0, "degraded": False},
)
_stop = threading.Event()
_thread: threading.Thread | None = None


def snapshot() -> dict[str, Any]:
    return _store.read()


def beat() -> None:
    data = _store.read()
    data["alive"] = True
    data["heartbeat"] = time.time()
    data["degraded"] = False
    _store.write(data)


def _loop() -> None:
    while not _stop.wait(2.0):
        beat()


def start() -> None:
    global _thread
    data = _store.read()
    if data.get("started"):
        data["restarts"] = int(data.get("restarts") or 0) + 1
    data["started"] = time.time()
    data["alive"] = True
    _store.write(data)
    beat()
    _thread = threading.Thread(target=_loop, name="eclipse-watchdog", daemon=True)
    _thread.start()
