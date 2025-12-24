
import asyncio
import json
from typing import AsyncIterator
from openai import AsyncOpenAI

from app.codex.driver import CodexDriver, CodexEvent

class CodexSDKDriver(CodexDriver):
    def __init__(self):
        self.client = AsyncOpenAI()
        self.sessions = {}
        self.queues = {}

    async def start_session(self, session_id: str, config: dict) -> None:
        queue = asyncio.Queue()
        self.queues[session_id] = queue

        async def run():
            try:
                await queue.put({
                    "type": "plan",
                    "content": f"Goal: {config['goal']}"
                })

                response = await self.client.responses.create(
                    model="gpt-4.1-mini",  # placeholder Codex-capable model
                    input=[
                        {
                            "role": "user",
                            "content": config["goal"]
                        }
                    ],
                    stream=True,
                )

                async for event in response:
                    if event.type == "response.output_text.delta":
                        await queue.put({
                            "type": "thought",
                            "content": event.delta
                        })

                await queue.put({
                    "type": "final",
                    "content": "Codex run complete."
                })

            except Exception as e:
                await queue.put({
                    "type": "error",
                    "content": str(e)
                })

        self.sessions[session_id] = asyncio.create_task(run())

    async def send(self, session_id: str, message: str) -> None:
        # Interactive input later (not needed yet)
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
