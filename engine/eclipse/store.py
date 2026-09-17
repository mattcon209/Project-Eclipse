from __future__ import annotations

import json
import os
import time
import threading
from pathlib import Path
from typing import Any


class JsonStore:
    def __init__(self, path: Path, default: Any):
        self.path = path
        self.default = default
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.write(default)

    def read(self) -> Any:
        with self._lock:
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return json.loads(json.dumps(self.default))

    def write(self, data: Any) -> None:
        payload = json.dumps(data, indent=2)
        with self._lock:
            _atomic_write(self.path, payload)


def _atomic_write(path: Path, payload: str) -> None:
    """Windows can deny replace() on a live json (AV, explorer preview). Retry, then overwrite."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    tmp.write_text(payload, encoding="utf-8")
    last: OSError | None = None
    try:
        for i in range(10):
            try:
                os.replace(tmp, path)
                return
            except OSError as e:
                last = e
                time.sleep(0.04 * (i + 1))
        for i in range(6):
            try:
                path.write_text(payload, encoding="utf-8")
                return
            except OSError as e:
                last = e
                time.sleep(0.05 * (i + 1))
        if last:
            raise last
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
