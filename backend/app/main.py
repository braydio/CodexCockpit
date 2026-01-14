# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import sessions, models, run, workspace

app = FastAPI(
    title="Codex Control Plane",
    version="0.1.0",
)

# Keep this for dev; Tauri doesn't need it but browser dev does.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(models.router, prefix="/models", tags=["models"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(run.router, prefix="/sessions", tags=["run"])
app.include_router(workspace.router, prefix="/workspace", tags=["workspace"])

