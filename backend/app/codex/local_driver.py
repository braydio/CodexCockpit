
import asyncio
from typing import AsyncIterator
from openai import AsyncOpenAI

from app.codex.driver import CodexDriver, CodexEvent
from app.codex.models import ModelSpec

class LocalModelDriver(CodexDriver):
    def __init__(self, model: ModelSpec):
        self.model = model
        self.client = AsyncOpenAI(
            base_url=model.endpoint,
            api_key="local-model"  # ignored but required
        )
        self.queues = {}

    async def start_session(self, session_id: str, config: dict) -> None:
        queue = asyncio.Queue()
        self.queues[session_id] = queue

        async def run():
            try:
                resp = await self.client.chat.completions.create(
                    model=self.model.name,
                    messages=[
                        {"role": "user", "content": config["goal"]}
                    ],
                    stream=True,
                )

                async for chunk in resp:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        await queue.put({
                            "type": "thought",
                            "content": delta
                        })

                await queue.put({
                    "type": "final",
                    "content": "Local model complete."
                })

            except Exception as e:
                await queue.put({
                    "type": "error",
                    "content": str(e)
                })

        asyncio.create_task(run())

    async def send(self, session_id: str, message: str) -> None:
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
        pass
