import asyncio
import logging
from typing import AsyncIterator

from app.codex.context_assembler import ContextAssembler
from app.codex.driver import CodexDriver, CodexEvent
from app.codex.model_adapters import ModelAdapter
from app.codex.models import ModelSpec

LOGGER = logging.getLogger(__name__)


class LocalModelDriver(CodexDriver):
    """Driver for local model adapters that produce Codex-style output."""

    def __init__(self, model: ModelSpec, adapter: ModelAdapter):
        """Initialize the local driver with a model specification and adapter.

        Args:
            model: Model metadata including runtime and name.
            adapter: Adapter responsible for invoking the local model.
        """
        self.model = model
        self.adapter = adapter
        self.queues = {}
        self.tasks = {}

    async def start_session(self, session_id: str, config: dict) -> None:
        """Start a streaming Codex session for a local model via the adapter.

        Args:
            session_id: Unique identifier for the session.
            config: Session configuration containing workspace and goal.
        """
        queue = asyncio.Queue()
        self.queues[session_id] = queue

        async def run():
            try:
                assembler = ContextAssembler(config.get("workspace", "."))
                context = assembler.assemble(config["goal"])
                workspace = config.get("workspace", ".")
                prompt = self._build_prompt(config["goal"], workspace, context)

                response = await asyncio.to_thread(self.adapter.generate, prompt)
                if response:
                    await queue.put({
                        "type": "thought",
                        "content": response
                    })

                await queue.put({
                    "type": "final",
                    "content": "Local model complete."
                })

            except Exception as exc:
                LOGGER.exception("Local model session failed.")
                await queue.put({
                    "type": "error",
                    "content": str(exc)
                })

        self.tasks[session_id] = asyncio.create_task(run())

    async def send(self, session_id: str, message: str) -> None:
        """Send interactive input to an existing session."""
        pass

    async def stream_events(self, session_id: str) -> AsyncIterator[CodexEvent]:
        """Stream queued events for a session."""
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
        """Stop a local session (not yet implemented)."""
        pass

    def _build_prompt(self, goal: str, workspace: str, context: dict) -> str:
        """Compose an explicit prompt with bounded repository context.

        Args:
            goal: User-supplied goal for the run.
            workspace: Workspace root for the session.
            context: Dictionary returned by ``ContextAssembler.assemble``.

        Returns:
            Prompt string that includes repository structure and snippets.
        """
        summary_lines = "\n".join(f"- {path}" for path in context["summary"])
        snippet_blocks: list[str] = []
        for snippet in context["snippets"]:
            snippet_lines = "\n".join(snippet["lines"])
            snippet_blocks.append(f"[{snippet['path']}]\n{snippet_lines}")
        snippets_text = "\n\n".join(snippet_blocks)
        error_text = "\n".join(context["errors"]) if context["errors"] else "None"
        keywords = ", ".join(context["keywords"]) if context["keywords"] else "None"

        return (
            "Codex task context (bounded):\n"
            f"Goal: {goal}\n"
            f"Workspace: {workspace}\n"
            f"Keywords: {keywords}\n\n"
            "Repository files (summary, limited):\n"
            f"{summary_lines or 'None'}\n\n"
            "Relevant snippets (keyword matches, limited):\n"
            f"{snippets_text or 'None'}\n\n"
            "Context assembly errors (non-fatal):\n"
            f"{error_text}\n\n"
            "Instructions:\n"
            "- Use only the provided files/snippets as verified context.\n"
            "- Ask for clarification or request additional files if needed.\n"
        )
