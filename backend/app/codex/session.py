
from app.codex.router import get_driver

sessions = {}

async def create(session_id: str, config: dict):
    driver = get_driver(config["model"])
    sessions[session_id] = {
        "config": config,
        "driver": driver,
    }
    await driver.start_session(session_id, config)

def get(session_id: str):
    return sessions.get(session_id)

