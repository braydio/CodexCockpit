# backend/app/codex/driver.py

from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any

class CodexEvent(Dict[str, Any]):
    """
    Example:
    {
      "type": "plan" | "tool" | "diff" | "thought" | "status" | "final" | "cancelled" | "error",
      "content": str,
      "meta": dict (optional)
    }
    """

class CodexDriver(ABC):

    @abstractmethod
    async def start_session(self, session_id: str, config: dict) -> None:
        ...

    @abstractmethod
    async def send(self, session_id: str, message: str) -> None:
        ...

    @abstractmethod
    async def stream_events(self, session_id: str) -> AsyncIterator[CodexEvent]:
        ...

    @abstractmethod
    async def stop_session(self, session_id: str) -> None:
        ...
