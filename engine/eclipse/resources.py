from __future__ import annotations

import shutil
import socket
import subprocess
from typing import Any

import psutil


def _nvidia() -> dict[str, Any]:
    cmd = [
        "nvidia-smi",
        "--query-gpu=name,memory.used,memory.total,temperature.gpu,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    try:
        out = subprocess.check_output(cmd, timeout=2, stderr=subprocess.DEVNULL, text=True)
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        return {
            "available": False,
            "reason": "nvidia-smi not found — expected on MattsGamingPC (RTX 5060 Ti)",
            "name": None,
            "vram_used_mb": None,
            "vram_total_mb": 16384,
            "temp_c": None,
            "util_pct": None,
        }
    line = out.strip().splitlines()[0]
    parts = [p.strip() for p in line.split(",")]
    name, used, total, temp, util = (parts + ["", "", "", "", ""])[:5]

    def num(x: str) -> int | None:
        try:
            return int(float(x))
        except ValueError:
            return None

    return {
        "available": True,
        "reason": None,
        "name": name,
        "vram_used_mb": num(used),
        "vram_total_mb": num(total),
        "temp_c": num(temp),
        "util_pct": num(util),
    }


def snapshot() -> dict[str, Any]:
    vm = psutil.virtual_memory()
    du = shutil.disk_usage("/")
    gpu = _nvidia()
    return {
        "hostname": socket.gethostname(),
        "cpu": {
            "cores": psutil.cpu_count(logical=False) or 0,
            "threads": psutil.cpu_count(logical=True) or 0,
            "pct": psutil.cpu_percent(interval=None),
        },
        "ram": {
            "used_mb": int(vm.used / 1024 / 1024),
            "total_mb": int(vm.total / 1024 / 1024),
            "pct": vm.percent,
        },
        "disk": {
            "used_gb": round(du.used / 1024 / 1024 / 1024, 1),
            "total_gb": round(du.total / 1024 / 1024 / 1024, 1),
            "free_gb": round(du.free / 1024 / 1024 / 1024, 1),
            "pct": round(du.used / du.total * 100, 1),
        },
        "gpu": gpu,
    }
