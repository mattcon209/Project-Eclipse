"""Start the engine. From the repo folder:  py run.py"""
from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent / "engine"
TARGET = ENGINE / "run.py"
if not TARGET.is_file():
    sys.exit("engine/run.py is missing.")
sys.path.insert(0, str(ENGINE))
os.chdir(ENGINE)
runpy.run_path(str(TARGET), run_name="__main__")
