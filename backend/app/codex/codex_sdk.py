import asyncio
import logging
from typing import AsyncIterator

from openai import AsyncOpenAI

from app.codex.context_assembler import ContextAssembler
from app.codex.driver import CodexDriver, CodexEvent

LOGGER = logging.getLogger(__name__)


class CodexSDKDriver(CodexDriver):
    """Driver that uses the OpenAI Responses API for Codex-compatible models."""

    def __init__(self):
        """Initialize the SDK driver and its session state."""
        self.client = AsyncOpenAI()
        self.tasks = {}
        self.queues = {}

    async def start_session(self, session_id: str, config: dict) -> None:
        """Start a streaming session with repository context.

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
                prompt = self._build_prompt(
                    config["goal"],
                    config.get("workspace", "."),
                    context,
                )

                await queue.put({
                    "type": "plan",
                    "content": f"Goal: {config['goal']}"
                })

                response = await self.client.responses.create(
                    model="gpt-4.1-mini",  # placeholder Codex-capable model
                    input=[
                        {
                            "role": "user",
                            "content": prompt
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

            except Exception as exc:
                LOGGER.exception("Codex SDK session failed.")
                await queue.put({
                    "type": "error",
                    "content": str(exc)
                })

        self.tasks[session_id] = asyncio.create_task(run())

    async def send(self, session_id: str, message: str) -> None:
        """Send interactive input to an existing session."""
        # Interactive input later (not needed yet)
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
        """Stop a running SDK session."""
        task = self.sessions.get(session_id)
        if task:
            task.cancel()

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
