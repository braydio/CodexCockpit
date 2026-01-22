import asyncio
import json
import logging
from typing import AsyncIterator

import httpx

from app.codex.driver import CodexDriver, CodexEvent
from app.codex.models import ModelSpec

LOGGER = logging.getLogger(__name__)


class OllamaDriver(CodexDriver):
    def __init__(self, model: ModelSpec):
        if not model.endpoint:
            raise ValueError("Ollama model requires an endpoint")
        self.model = model
        self.client = httpx.AsyncClient(
            base_url=model.endpoint.rstrip("/"),
            timeout=None,
        )
        self.queues = {}
        self.tasks = {}

    async def start_session(self, session_id: str, config: dict) -> None:
        if session_id in self.tasks:
            return

        queue = asyncio.Queue()
        self.queues[session_id] = queue

        async def run() -> None:
            try:
                LOGGER.info(
                    "Ollama session start",
                    extra={
                        "session_id": session_id,
                        "model": self.model.name,
                        "endpoint": self.model.endpoint,
                    },
                )
                await queue.put({"type": "plan", "content": f"Goal: {config['goal']}"})

                payload = {
                    "model": self.model.name,
                    "messages": [{"role": "user", "content": config["goal"]}],
                    "stream": True,
                }
                LOGGER.debug(
                    "Ollama payload",
                    extra={
                        "session_id": session_id,
                        "payload": {
                            "model": payload["model"],
                            "messages_len": len(payload["messages"]),
                            "stream": payload["stream"],
                        },
                    },
                )

                async with self.client.stream("POST", "/api/chat", json=payload) as resp:
                    LOGGER.info(
                        "Ollama response status",
                        extra={
                            "session_id": session_id,
                            "status_code": resp.status_code,
                        },
                    )
                    resp.raise_for_status()
                    LOGGER.debug(
                        "Ollama response headers",
                        extra={
                            "session_id": session_id,
                            "headers": dict(resp.headers),
                        },
                    )
                    async for line in resp.aiter_lines():
                        if not line:
                            LOGGER.debug(
                                "Ollama stream keep-alive",
                                extra={"session_id": session_id},
                            )
                            continue

                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError:
                            LOGGER.warning(
                                "Ollama stream non-JSON line",
                                extra={"session_id": session_id, "line": line},
                            )
                            continue
                        if data.get("error"):
                            await queue.put({"type": "error", "content": str(data["error"])})
                            return

                        content = (data.get("message") or {}).get("content")
                        if content:
                            await queue.put({"type": "thought", "content": content})

                        if data.get("done"):
                            break

                await queue.put({"type": "final", "content": "Ollama run complete."})
            except asyncio.CancelledError:
                raise
            except Exception as e:
                LOGGER.exception(
                    "Ollama session error",
                    extra={"session_id": session_id},
                )
                await queue.put({"type": "error", "content": str(e)})
            finally:
                await self.client.aclose()

        self.tasks[session_id] = asyncio.create_task(run())

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
            if event["type"] in ("final", "cancelled", "error"):
                break

    async def stop_session(self, session_id: str) -> None:
        task = self.tasks.get(session_id)
        if task and not task.done():
            task.cancel()
        queue = self.queues.get(session_id)
        if queue:
            await queue.put({"type": "cancelled", "content": "Session cancelled."})
        await self.client.aclose()
