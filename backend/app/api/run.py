
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.codex.session import get_config, get_driver
import json

router = APIRouter()

@router.post("/{session_id}/run")
async def start_run(session_id: str):
    config = get_config(session_id)
    if not config:
        return {"error": "Session not found"}

    return {"status": "started"}

@router.get("/{session_id}/events")
async def stream_events(session_id: str):
    config = get_config(session_id)
    if not config:
        return {"error": "Session not found"}
    session_driver = get_driver(session_id)
    if not session_driver:
        return {"error": "Session driver not found"}

    async def event_stream():
        async for event in session_driver.stream_events(session_id):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream"
    )
