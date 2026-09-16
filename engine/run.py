from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import uvicorn

from eclipse.config import HOST, PORT


if __name__ == "__main__":
    print(f"Eclipse engine  →  http://{HOST}:{PORT}")
    uvicorn.run("eclipse.gateway:app", host=HOST, port=PORT, reload=False)
