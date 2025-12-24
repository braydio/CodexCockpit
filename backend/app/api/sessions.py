# backend/app/api/sessions.py
from fastapi import APIRouter
from pydantic import BaseModel
import uuid

from app.codex.session import create as codex_create, get_config

router = APIRouter()

class CreateSessionRequest(BaseModel):
    goal: str
    model: str | None = None
    workspace: str | None = None

@router.post("/")
async def create_session(req: CreateSessionRequest):
    session_id = str(uuid.uuid4())

    config = {
        "goal": req.goal,
        "model": req.model or "default",
        "workspace": req.workspace or ".",
    }

    # This is the missing piece: register + start session in the driver
    await codex_create(session_id, config)

    return {
        "session_id": session_id,
        "goal": req.goal,
        "model": config["model"],
        "status": "created",
    }

@router.get("/{session_id}")
def get_session(session_id: str):
    cfg = get_config(session_id)
    if not cfg:
        return {"error": "Session not found"}
    return {"session_id": session_id, "config": cfg}

