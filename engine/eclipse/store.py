from __future__ import annotations

import json
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
        with self._lock:
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
            tmp.replace(self.path)
