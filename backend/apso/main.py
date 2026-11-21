from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from apso.api.routes import router

ROOT = Path(__file__).resolve().parents[2]
STATIC = ROOT / "frontend" / "static"

app = FastAPI(title="APSO — App Support Workbench", version="0.1.0")
app.include_router(router)

if STATIC.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


@app.get("/")
def index():
    index_path = STATIC / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "APSO API up. Place frontend/static/index.html for UI."}
