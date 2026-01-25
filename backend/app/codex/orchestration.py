from __future__ import annotations

import asyncio
import uuid
from typing import AsyncIterator, Callable, Optional

from app.codex.driver import CodexDriver, CodexEvent
from app.codex.metrics import MetricsAccumulator
from app.codex.orchestration_types import OrchestrationPlan, TaskSpec
from app.codex import session as session_store


class OrchestrationManager:
    """Coordinate orchestration planning and session event aggregation.

    Args:
        register_session: Callable used to register new sessions.
        start_session: Callable used to start registered sessions.
        get_driver: Callable used to resolve a session ID to a driver.
        metrics_accumulator: Optional metrics accumulator instance.
    """

    def __init__(
        self,
        register_session: Callable[[str, dict], asyncio.Future] = (
            session_store.register
        ),
        start_session: Callable[[str], asyncio.Future] = session_store.start,
        get_driver: Callable[[str], Optional[CodexDriver]] = (
            session_store.get_driver
        ),
        metrics_accumulator: Optional[MetricsAccumulator] = None,
    ) -> None:
        self._register_session = register_session
        self._start_session = start_session
        self._get_driver = get_driver
        self._metrics = metrics_accumulator or MetricsAccumulator()

    def create_plan(self, task_spec: TaskSpec) -> OrchestrationPlan:
        """Create an orchestration plan for a task.

        Args:
            task_spec: Task specification defining goals and requirements.

        Returns:
            ``OrchestrationPlan`` populated with ordered steps.
        """
        steps = [
            "Validate task specification",
            "Initialize session",
            "Stream and aggregate events",
        ]

        if task_spec.deliverables:
            steps.append("Verify deliverables")

        if task_spec.definition_of_done.required_metrics:
            steps.append("Evaluate required metrics")

        if task_spec.definition_of_done.optional_metrics:
            steps.append("Evaluate optional metrics")

        steps.append("Finalize definition of done")

        plan_id = f"plan-{uuid.uuid4()}"
        return OrchestrationPlan(plan_id=plan_id, task_spec=task_spec, steps=steps)

    async def spawn_minion_session(
        self,
        config: dict,
        session_id: Optional[str] = None,
    ) -> str:
        """Register and start a new session using the driver interface.

        Args:
            config: Session configuration passed through the session registry.
            session_id: Optional session identifier to reuse.

        Returns:
            The registered session identifier.
        """
        resolved_id = session_id or str(uuid.uuid4())
        await self._register_session(resolved_id, config)
        await self._start_session(resolved_id)
        return resolved_id

    async def stream_session_events(
        self, session_id: str
    ) -> AsyncIterator[CodexEvent]:
        """Stream events for a session while updating metrics.

        Args:
            session_id: Session identifier to stream from.

        Yields:
            Enriched Codex events with session metadata.
        """
        driver = self._get_driver(session_id)
        if not driver:
            error_event: CodexEvent = {
                "type": "error",
                "content": "Session driver not found",
                "meta": {"session_id": session_id},
            }
            self._metrics.record_event(error_event)
            yield error_event
            return

        async for event in driver.stream_events(session_id):
            wrapped_event = self._attach_session_meta(event, session_id)
            self._metrics.record_event(wrapped_event)
            yield wrapped_event

    async def stream_aggregated_events(
        self, session_ids: list[str]
    ) -> AsyncIterator[CodexEvent]:
        """Aggregate events from multiple sessions into a single stream.

        Args:
            session_ids: Session identifiers to stream events from.

        Yields:
            Codex events merged from all sessions.
        """
        if not session_ids:
            return

        queue: asyncio.Queue[object] = asyncio.Queue()
        sentinel = object()

        async def forward(session_id: str) -> None:
            async for event in self.stream_session_events(session_id):
                await queue.put(event)
            await queue.put((sentinel, session_id))

        tasks = [asyncio.create_task(forward(session_id)) for session_id in session_ids]
        completed = 0
        try:
            while completed < len(session_ids):
                item = await queue.get()
                if isinstance(item, tuple) and item[0] is sentinel:
                    completed += 1
                    continue
                yield item  # type: ignore[misc]
        finally:
            await asyncio.gather(*tasks, return_exceptions=True)

    def metrics_summary(self) -> dict:
        """Expose a metrics snapshot for collected session events.

        Returns:
            Dictionary containing aggregated metrics statistics.
        """
        return self._metrics.summarize()

    def _attach_session_meta(
        self, event: CodexEvent, session_id: str
    ) -> CodexEvent:
        """Ensure an event includes session metadata.

        Args:
            event: Codex event emitted by a driver.
            session_id: Session identifier that produced the event.

        Returns:
            Event copy with merged session metadata.
        """
        meta = event.get("meta")
        merged_meta = {"session_id": session_id}
        if isinstance(meta, dict):
            merged_meta.update(meta)

        return {
            "type": event.get("type"),
            "content": event.get("content"),
            "meta": merged_meta,
        }
