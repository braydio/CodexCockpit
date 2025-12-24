

import asyncio
from typing import AsyncIterator
from app.codex.driver import CodexDriver, CodexEvent

class InProcessCodexDriver(CodexDriver):
    def __init__(self):
        self.sessions = {}
        self.queues = {}

    async def start_session(self, session_id: str, config: dict) -> None:
        queue = asyncio.Queue()
        self.queues[session_id] = queue

        async def fake_run():
            await queue.put({"type": "plan", "content": "Inspect repository structure"})
            await asyncio.sleep(0.8)

            await queue.put({
                "type": "tool",
                "content": "ls",
                "meta": {"path": config.get("workspace", ".")}
            })
            await asyncio.sleep(0.8)

            await queue.put({
                "type": "diff",
                "content": "Modified main.py",
                "meta": {"files": ["main.py"]}
            })
            await asyncio.sleep(0.8)

            await queue.put({
                "type": "final",
                "content": "Task completed successfully."
            })

        self.sessions[session_id] = asyncio.create_task(fake_run())

    async def send(self, session_id: str, message: str) -> None:
        # placeholder: future interactive input
        pass

    async def stream_events(self, session_id: str) -> AsyncIterator[CodexEvent]:
        queue = self.queues.get(session_id)
        if not queue:
            yield {"type": "error", "content": "Session not found"}
            return

        while True:
            event = await queue.get()
            yield event
            if event["type"] in ("final", "error"):
                break

    async def stop_session(self, session_id: str) -> None:
        task = self.sessions.get(session_id)
        if task:
            task.cancel()
