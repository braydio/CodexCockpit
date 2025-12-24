# backend/app/main.py
from fastapi import FastAPI
from app.api import sessions, models, run
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="Codex Control Plane",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router, prefix="/sessions")
app.include_router(models.router, prefix="/models")
app.include_router(run.router, prefix="/sessions")

@app.get("/health")
def health():
    return {"status": "ok"}
