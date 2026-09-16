from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from eclipse import __version__
from eclipse.calibrator import get as cal_get
from eclipse.calibrator import run as cal_run
from eclipse.jobs import cancel as job_cancel
from eclipse.jobs import get as job_get
from eclipse.jobs import list_jobs
from eclipse.orchestrator import make_image, session, set_ladder, set_mode
from eclipse.pairing import check_token, is_paired, pair, status as pair_status
from eclipse.resources import snapshot as res_snapshot
from eclipse.watchdog import snapshot as wd_snapshot
from eclipse.watchdog import start as wd_start

ROOT = Path(__file__).resolve().parent.parent
ATELIER = ROOT / "atelier"

app = FastAPI(title="Eclipse Engine", version=__version__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_clients: set[WebSocket] = set()


class PairIn(BaseModel):
    code: str
    device_name: str = "Galaxy S24+"


class ModeIn(BaseModel):
    mode: str


class LadderIn(BaseModel):
    ladder: str


class MakeIn(BaseModel):
    prompt: str = Field(default="", max_length=4000)


def _auth(authorization: str | None) -> None:
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    if not is_paired():
        raise HTTPException(409, "Engine is waiting to pair.")
    if not check_token(token):
        raise HTTPException(401, "Pairing token missing or wrong.")


def public_status() -> dict[str, Any]:
    snap = res_snapshot()
    sess = session()
    gpu = snap["gpu"]
    vram = None
    if gpu.get("available") and gpu.get("vram_used_mb") is not None:
        vram = f"{gpu['vram_used_mb'] / 1024:.1f}"
    return {
        "ok": True,
        "version": __version__,
        "phase": 0,
        "engine": "running",
        "paired": is_paired(),
        "pairing": pair_status(),
        "resources": snap,
        "session": sess,
        "watchdog": wd_snapshot(),
        "calibrated": bool(cal_get().get("at")),
        "jobs": len(list_jobs()),
        "vram_chip": vram,
        "now": time.time(),
    }


@app.on_event("startup")
def _startup() -> None:
    wd_start()
    if not cal_get().get("at"):
        cal_run()
    ps = pair_status()
    if ps.get("paired"):
        print("Eclipse engine paired.", flush=True)
    else:
        print(f"Pairing code: {ps.get('code')}  (Atelier → Pair this phone)", flush=True)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "version": __version__, "phase": 0}


@app.get("/api/status")
def status() -> dict:
    return public_status()


@app.get("/api/pair")
def pair_get() -> dict:
    return pair_status()


@app.post("/api/pair")
def pair_post(body: PairIn) -> dict:
    result = pair(body.code, body.device_name)
    if not result.get("ok"):
        return JSONResponse(result, status_code=400)
    return result


@app.get("/api/resources")
def resources(authorization: str | None = Header(default=None)) -> dict:
    _auth(authorization)
    return res_snapshot()


@app.post("/api/calibrate")
def calibrate(authorization: str | None = Header(default=None)) -> dict:
    _auth(authorization)
    return cal_run()


@app.get("/api/calibration")
def calibration(authorization: str | None = Header(default=None)) -> dict:
    _auth(authorization)
    return cal_get()


@app.get("/api/jobs")
def jobs(authorization: str | None = Header(default=None)) -> dict:
    _auth(authorization)
    return {"jobs": list_jobs()}


@app.get("/api/jobs/{job_id}")
def job(job_id: str, authorization: str | None = Header(default=None)) -> dict:
    _auth(authorization)
    j = job_get(job_id)
    if not j:
        raise HTTPException(404, "No such job.")
    return j


@app.post("/api/jobs/{job_id}/cancel")
def cancel(job_id: str, authorization: str | None = Header(default=None)) -> dict:
    _auth(authorization)
    j = job_cancel(job_id)
    if not j:
        raise HTTPException(404, "No such job.")
    return j


@app.post("/api/mode")
def mode(body: ModeIn, authorization: str | None = Header(default=None)) -> dict:
    _auth(authorization)
    allowed = {"home", "image", "chat", "audio", "edit", "video", "talk", "train"}
    if body.mode not in allowed:
        raise HTTPException(400, "Unknown mode.")
    return set_mode(body.mode)


@app.post("/api/ladder")
def ladder(body: LadderIn, authorization: str | None = Header(default=None)) -> dict:
    _auth(authorization)
    try:
        return set_ladder(body.ladder)
    except ValueError:
        raise HTTPException(400, "Unknown ladder.") from None


@app.post("/api/make")
def make(body: MakeIn, authorization: str | None = Header(default=None)) -> dict:
    _auth(authorization)
    return make_image(body.prompt.strip())


@app.websocket("/api/ws")
async def ws(socket: WebSocket, token: str = "") -> None:
    await socket.accept()
    if is_paired() and not check_token(token):
        await socket.close(code=4401)
        return
    _clients.add(socket)
    try:
        while True:
            await socket.send_json({"type": "status", "payload": public_status()})
            try:
                await asyncio.wait_for(socket.receive_text(), timeout=2.0)
            except asyncio.TimeoutError:
                continue
    except WebSocketDisconnect:
        pass
    finally:
        _clients.discard(socket)


if ATELIER.exists():
    app.mount("/static", StaticFiles(directory=ATELIER), name="static")


@app.get("/")
def index() -> FileResponse:
    page = ATELIER / "index.html"
    if not page.exists():
        raise HTTPException(404, "Atelier UI missing.")
    return FileResponse(page)


@app.get("/{name}")
def atelier_file(name: str) -> FileResponse:
    if name.startswith("api"):
        raise HTTPException(404)
    path = ATELIER / name
    if path.is_file():
        return FileResponse(path)
    raise HTTPException(404)
