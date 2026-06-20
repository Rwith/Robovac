"""FastAPI server: map upload, command API, and a live dashboard.

Run:  uvicorn server.app:app --host 0.0.0.0 --port 8000

Endpoints:
    POST /maps              upload a finished occupancy grid (multipart)
    GET  /maps/{name}.png   fetch a stored map image
    GET  /maps/{name}       fetch map metadata
    POST /commands          queue a command for the robot
    GET  /commands          robot polls queued commands (or use MQTT)
    GET  /                  the dashboard (web/index.html)
    WS   /ws                live robot pose/status stream for the dashboard
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile, WebSocket
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from server.store import db
from shared.schemas import Command, MapUpload

WEB_DIR = Path(__file__).parent / "web"
MAPS_DIR = Path(__file__).parent / "store" / "maps"
MAPS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Robovac Server")
db.init()

# A tiny in-memory command queue; swap for a table when you need persistence.
_command_queue: list[Command] = []


@app.post("/maps")
async def upload_map(meta: str = Form(...), image: UploadFile = File(...)):
    parsed = MapUpload(**json.loads(meta))
    (MAPS_DIR / f"{parsed.name}.png").write_bytes(await image.read())
    db.save_map_meta(parsed)
    return {"ok": True, "name": parsed.name}


@app.get("/maps/{name}.png")
def get_map_image(name: str):
    return FileResponse(MAPS_DIR / f"{name}.png")


@app.get("/maps/{name}")
def get_map_meta(name: str):
    return db.load_map_meta(name)


@app.post("/commands")
def queue_command(cmd: Command):
    _command_queue.append(cmd)
    return {"ok": True, "queued": len(_command_queue)}


@app.get("/commands")
def pop_commands():
    out = [c.model_dump() for c in _command_queue]
    _command_queue.clear()
    return out


@app.websocket("/ws")
async def ws(socket: WebSocket):
    # TODO(M5): bridge MQTT robovac/+/status messages to this socket so the
    # dashboard sees the robot move in real time.
    await socket.accept()
    await socket.send_text(json.dumps({"hello": "robovac"}))


@app.get("/", response_class=HTMLResponse)
def index():
    return (WEB_DIR / "index.html").read_text(encoding="utf-8")


app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")
