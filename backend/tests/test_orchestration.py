import unittest
from unittest.mock import AsyncMock

from app.codex.driver import CodexDriver
from app.codex.metrics import MetricsAccumulator
from app.codex.orchestration import OrchestrationManager
from app.codex.orchestration_types import DefinitionOfDone, TaskSpec


class FakeDriver(CodexDriver):
    """Test double for a Codex driver stream."""

    def __init__(self, events):
        self._events = events

    async def start_session(self, session_id: str, config: dict) -> None:
        return None

    async def send(self, session_id: str, message: str) -> None:
        return None

    async def stream_events(self, session_id: str):
        for event in self._events:
            yield event

    async def stop_session(self, session_id: str) -> None:
        return None


class MetricsAccumulatorTests(unittest.TestCase):
    """Unit tests for orchestration metrics tracking."""

    def test_records_event_counts_files_and_errors(self) -> None:
        """Ensure event counters and file tracking are updated."""
        accumulator = MetricsAccumulator()
        accumulator.record_event({"type": "plan", "content": "Plan"})
        accumulator.record_event(
            {"type": "diff", "content": "diff", "meta": {"files": ["a.py"]}}
        )
        accumulator.record_event(
            {"type": "tool", "content": "tool", "meta": {"path": "b.py"}}
        )
        accumulator.record_event({"type": "error", "content": "boom"})

        summary = accumulator.summarize()

        self.assertEqual(summary["event_counts"]["plan"], 1)
        self.assertEqual(summary["event_counts"]["diff"], 1)
        self.assertEqual(summary["event_counts"]["tool"], 1)
        self.assertEqual(summary["event_counts"]["error"], 1)
        self.assertEqual(summary["error_count"], 1)
        self.assertCountEqual(summary["files_touched"], ["a.py", "b.py"])


class OrchestrationManagerTests(unittest.IsolatedAsyncioTestCase):
    """Unit tests for orchestration planning and streaming."""

    def setUp(self) -> None:
        """Create a default task specification for tests."""
        definition = DefinitionOfDone(
            required_metrics=["tests_pass"],
            optional_metrics=["lint_pass"],
            blocking_issues=[],
            notes="All required metrics must pass.",
        )
        self.task_spec = TaskSpec(
            task_id="task-1",
            goal="Plan orchestration",
            workspace_root="/workspace/CodexCockpit",
            constraints={"require_tests": True},
            deliverables=[{"type": "document", "path": "docs/foo.md"}],
            definition_of_done=definition,
        )

    def test_create_plan_includes_expected_steps(self) -> None:
        """Ensure plan steps reflect deliverables and metrics requirements."""
        manager = OrchestrationManager(
            register_session=AsyncMock(),
            start_session=AsyncMock(),
            get_driver=lambda _: None,
        )
        plan = manager.create_plan(self.task_spec)

        self.assertIn("Verify deliverables", plan.steps)
        self.assertIn("Evaluate required metrics", plan.steps)
        self.assertIn("Evaluate optional metrics", plan.steps)
        self.assertEqual(plan.task_spec, self.task_spec)

    async def test_spawn_minion_session_registers_and_starts(self) -> None:
        """Ensure session registry is used to start minion sessions."""
        register = AsyncMock()
        start = AsyncMock()
        manager = OrchestrationManager(
            register_session=register,
            start_session=start,
            get_driver=lambda _: None,
        )

        session_id = await manager.spawn_minion_session(
            {"model": "gpt-test", "goal": "Demo"},
            session_id="minion-1",
        )

        register.assert_awaited_once()
        start.assert_awaited_once_with("minion-1")
        self.assertEqual(session_id, "minion-1")

    async def test_stream_aggregated_events_adds_session_meta(self) -> None:
        """Ensure aggregated events include session identifiers."""
        drivers = {
            "session-1": FakeDriver(
                [{"type": "plan", "content": "p1"}, {"type": "final", "content": "f1"}]
            ),
            "session-2": FakeDriver(
                [{"type": "plan", "content": "p2"}, {"type": "final", "content": "f2"}]
            ),
        }
        manager = OrchestrationManager(
            register_session=AsyncMock(),
            start_session=AsyncMock(),
            get_driver=lambda session_id: drivers.get(session_id),
        )

        events = []
        async for event in manager.stream_aggregated_events([
            "session-1",
            "session-2",
        ]):
            events.append(event)

        session_ids = {event["meta"]["session_id"] for event in events}
        self.assertEqual(session_ids, {"session-1", "session-2"})
        self.assertEqual(manager.metrics_summary()["event_counts"]["plan"], 2)
        self.assertEqual(manager.metrics_summary()["event_counts"]["final"], 2)


if __name__ == "__main__":
    unittest.main()
