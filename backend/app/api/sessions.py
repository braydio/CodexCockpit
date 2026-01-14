# backend/app/api/sessions.py
from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel
import uuid

from app.codex.session import get_config, get_status, register, stop

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
        "model": req.model or "codex-default",
        "workspace": req.workspace or ".",
    }

    try:
        await register(session_id, config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "session_id": session_id,
        "goal": req.goal,
        "model": config["model"],
        "status": get_status(session_id),
    }

@router.get("/{session_id}")
def get_session(session_id: str):
    cfg = get_config(session_id)
    if not cfg:
        return {"error": "Session not found"}
    return {"session_id": session_id, "config": cfg, "status": get_status(session_id)}


@router.post("/{session_id}/stop")
async def stop_session(session_id: str):
    if not get_config(session_id):
        return {"error": "Session not found"}
    await stop(session_id)
    return {"session_id": session_id, "status": get_status(session_id)}
