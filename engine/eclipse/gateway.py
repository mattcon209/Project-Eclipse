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
from eclipse.acquire import AcquireError
from eclipse.acquire import run as acquire_run
from eclipse.acquire import scan_folder
from eclipse.scan import scan_machine
from eclipse.library import get_item, list_items, summary as library_summary
from eclipse.library import LIB
from eclipse.orchestrator import make_image, session, set_ladder, set_mode, use_model
from eclipse.resource_os import OS
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


class AcquireIn(BaseModel):
    url: str = Field(default="", max_length=2000)
    confirm: bool = False


class ScanIn(BaseModel):
    path: str = Field(default="", max_length=2000)


class SearchIn(BaseModel):
    extra: str = Field(default="", max_length=2000)


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
        "phase": 1,
        "engine": "running",
        "paired": is_paired(),
        "pairing": pair_status(),
        "resources": snap,
        "session": sess,
        "watchdog": wd_snapshot(),
        "calibrated": bool(cal_get().get("at")),
        "jobs": len(list_jobs()),
        "library": library_summary(),
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
    return {"ok": True, "version": __version__, "phase": 1}


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
    allowed = {"home", "image", "chat", "audio", "edit", "video", "talk", "train", "jobs", "library", "gallery"}
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


@app.get("/api/kpis")
def kpis(authorization: str | None = Header(default=None)) -> dict:
    _auth(authorization)
    return OS.kpis()


@app.get("/api/library")
def library_list(authorization: str | None = Header(default=None)) -> dict:
    _auth(authorization)
    return {"items": list_items(), **library_summary()}


@app.post("/api/library/acquire")
def library_acquire(body: AcquireIn, authorization: str | None = Header(default=None)) -> dict:
    _auth(authorization)
    try:
        result = acquire_run(body.url.strip(), confirm=body.confirm)
    except AcquireError as e:
        raise HTTPException(400, str(e)) from e
    if result.get("refused"):
        return JSONResponse(result, status_code=409)
    return result


@app.post("/api/library/scan")
def library_scan(body: ScanIn, authorization: str | None = Header(default=None)) -> dict:
    _auth(authorization)
    try:
        items = scan_folder(body.path.strip())
    except AcquireError as e:
        raise HTTPException(400, str(e)) from e
    return {"ok": True, "items": items}


@app.post("/api/library/search")
def library_search(body: SearchIn | None = None, authorization: str | None = Header(default=None)) -> dict:
    _auth(authorization)
    extra = (body.extra if body else "") or ""
    return scan_machine(extra=extra.strip() or None)


@app.get("/api/library/{item_id}")
def library_one(item_id: str, authorization: str | None = Header(default=None)) -> dict:
    _auth(authorization)
    rec = get_item(item_id)
    if not rec:
        raise HTTPException(404, "No such library item.")
    return rec


@app.post("/api/library/{item_id}/use")
def library_use(item_id: str, authorization: str | None = Header(default=None)) -> dict:
    _auth(authorization)
    try:
        return use_model(item_id)
    except ValueError as e:
        raise HTTPException(409, str(e)) from e


@app.delete("/api/library/{item_id}")
def library_delete(item_id: str, authorization: str | None = Header(default=None)) -> dict:
    _auth(authorization)
    rec = LIB.remove(item_id)
    if not rec:
        raise HTTPException(404, "No such library item.")
    return {"ok": True, "id": item_id}


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
