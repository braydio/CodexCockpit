from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Optional

from app.codex.router import get_driver as get_model_driver

FINISHED_SESSION_TTL_SECONDS = 60 * 60

_lock = asyncio.Lock()
_sessions: Dict[str, Dict[str, Any]] = {}


def _now() -> float:
    return time.time()


def _prune_finished_locked(now: float) -> None:
    to_delete = []
    for session_id, session in _sessions.items():
        finished_at = session.get("finished_at")
        if not finished_at:
            continue
        if now - finished_at >= FINISHED_SESSION_TTL_SECONDS:
            to_delete.append(session_id)

    for session_id in to_delete:
        _sessions.pop(session_id, None)


async def register(session_id: str, config: dict) -> None:
    driver = get_model_driver(config["model"], config.get("endpoint"))
    now = _now()

    async with _lock:
        _prune_finished_locked(now)
        if session_id in _sessions:
            raise ValueError("Session already exists")
        _sessions[session_id] = {
            "config": config,
            "driver": driver,
            "status": "created",
            "created_at": now,
            "started_at": None,
            "finished_at": None,
        }


async def start(session_id: str) -> None:
    now = _now()

    async with _lock:
        _prune_finished_locked(now)
        session = _sessions.get(session_id)
        if not session:
            raise KeyError("Session not found")
        if session.get("status") == "running":
            return
        session["status"] = "running"
        session["started_at"] = now
        session["finished_at"] = None
        driver = session["driver"]
        config = session["config"]

    try:
        await driver.start_session(session_id, config)
    except Exception:
        await mark_finished(session_id, "error")
        raise


async def stop(session_id: str) -> None:
    now = _now()
    async with _lock:
        _prune_finished_locked(now)
        session = _sessions.get(session_id)
        if not session:
            raise KeyError("Session not found")
        driver = session["driver"]
        session["status"] = "cancelled"
        session["finished_at"] = now

    await driver.stop_session(session_id)


async def mark_finished(session_id: str, status: str) -> None:
    now = _now()
    async with _lock:
        session = _sessions.get(session_id)
        if not session:
            return
        session["status"] = status
        session["finished_at"] = now
        _prune_finished_locked(now)


def get(session_id: str) -> Optional[Dict[str, Any]]:
    return _sessions.get(session_id)


def get_config(session_id: str) -> Optional[dict]:
    session = _sessions.get(session_id)
    if not session:
        return None
    return session.get("config")


def get_driver(session_id: str):
    session = _sessions.get(session_id)
    if not session:
        return None
    return session.get("driver")


def get_status(session_id: str) -> Optional[str]:
    session = _sessions.get(session_id)
    if not session:
        return None
    return session.get("status")
