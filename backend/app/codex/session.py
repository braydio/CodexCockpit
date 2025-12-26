
from app.codex.router import get_driver as get_model_driver

sessions = {}

async def create(session_id: str, config: dict):
    driver = get_model_driver(config["model"])
    sessions[session_id] = {
        "config": config,
        "driver": driver,
    }
    await driver.start_session(session_id, config)

def get(session_id: str):
    return sessions.get(session_id)

def get_config(session_id: str):
    session = sessions.get(session_id)
    if not session:
        return None
    return session.get("config")

def get_driver(session_id: str):
    session = sessions.get(session_id)
    if not session:
        return None
    return session.get("driver")
