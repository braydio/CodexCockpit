
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from fastapi import HTTPException

from app.codex.session import get_config, get_driver, get_status, mark_finished, start
import json
import logging

router = APIRouter()
LOGGER = logging.getLogger(__name__)

@router.post("/{session_id}/run")
async def start_run(session_id: str):
    config = get_config(session_id)
    if not config:
        return {"error": "Session not found"}

    try:
        await start(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"session_id": session_id, "status": get_status(session_id)}

@router.get("/{session_id}/events")
async def stream_events(session_id: str):
    config = get_config(session_id)
    if not config:
        return {"error": "Session not found"}
    if get_status(session_id) != "running":
        raise HTTPException(status_code=409, detail="Session not running; call /run first")
    session_driver = get_driver(session_id)
    if not session_driver:
        return {"error": "Session driver not found"}

    async def event_stream():
        status = "completed"
        try:
            LOGGER.info("Event stream start", extra={"session_id": session_id})
            async for event in session_driver.stream_events(session_id):
                if event.get("type") == "error":
                    status = "error"
                if event.get("type") == "cancelled":
                    status = "cancelled"
                yield f"data: {json.dumps(event)}\n\n"
        except Exception:
            status = "error"
            LOGGER.exception("Event stream error", extra={"session_id": session_id})
        finally:
            await mark_finished(session_id, status)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream"
    )
