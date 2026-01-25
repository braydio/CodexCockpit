import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.api import orchestrations


class OrchestrationApiTests(unittest.TestCase):
    """Tests for orchestration API endpoints."""

    def setUp(self) -> None:
        """Create a test client and reset orchestration state."""
        self.client = TestClient(app)
        orchestrations._PLANS.clear()
        orchestrations._RUNS.clear()

    def tearDown(self) -> None:
        """Clean up orchestration state after each test."""
        orchestrations._PLANS.clear()
        orchestrations._RUNS.clear()

    def _task_payload(self) -> dict:
        """Build a task specification payload for API calls."""
        return {
            "task_id": "task-123",
            "goal": "Test orchestration",
            "workspace_root": "/workspace/CodexCockpit",
            "constraints": {"require_tests": True},
            "deliverables": [{"type": "report", "path": "docs/report.md"}],
            "definition_of_done": {
                "required_metrics": ["tests_pass"],
                "optional_metrics": [],
                "blocking_issues": [],
                "notes": "All required metrics must pass.",
            },
        }

    def test_create_plan_returns_serialized_plan(self) -> None:
        """Ensure the plan endpoint returns plan details."""
        response = self.client.post(
            "/orchestrations/plan",
            json={"task_spec": self._task_payload()},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("plan_id", payload)
        self.assertIn("steps", payload)
        self.assertEqual(payload["task_spec"]["goal"], "Test orchestration")

    def test_start_run_spawns_sessions(self) -> None:
        """Ensure the run endpoint returns run and session details."""
        with patch.object(
            orchestrations.ORCHESTRATION_MANAGER,
            "spawn_minion_session",
            new=AsyncMock(side_effect=["session-1", "session-2"]),
        ):
            response = self.client.post(
                "/orchestrations/run",
                json={
                    "task_spec": self._task_payload(),
                    "sessions": [{"model": "codex-default"}, {"model": "codex"}],
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("run_id", payload)
        self.assertEqual(payload["session_ids"], ["session-1", "session-2"])
        self.assertIn(payload["run_id"], orchestrations._RUNS)

    def test_stream_events_emits_sse_payloads(self) -> None:
        """Ensure the event stream includes keep-alives and data payloads."""
        run_id = "run-1"
        orchestrations._RUNS[run_id] = {
            "plan_id": "plan-1",
            "session_ids": ["session-1"],
        }

        def fake_stream(_session_ids):
            async def iterator():
                yield {
                    "type": "status",
                    "content": "ready",
                    "meta": {"session_id": "session-1"},
                }
                yield {
                    "type": "final",
                    "content": "done",
                    "meta": {"session_id": "session-1"},
                }

            return iterator()

        with patch.object(
            orchestrations.ORCHESTRATION_MANAGER,
            "stream_aggregated_events",
            side_effect=fake_stream,
        ):
            with self.client.stream(
                "GET", f"/orchestrations/{run_id}/events"
            ) as response:
                content = response.read().decode("utf-8")

        self.assertIn(": keep-alive", content)
        self.assertIn("data:", content)


class OrchestrationStatusTests(unittest.TestCase):
    """Tests for orchestration session completion tracking."""

    def test_update_session_status_marks_completed(self) -> None:
        """Ensure non-error events mark sessions as completed."""
        statuses = {}

        orchestrations._update_session_status(
            statuses,
            session_id="session-1",
            event_type="final",
        )

        self.assertEqual(statuses["session-1"], "completed")

    def test_update_session_status_keeps_terminal_errors(self) -> None:
        """Ensure error or cancel status is not overwritten."""
        statuses = {"session-1": "completed"}

        orchestrations._update_session_status(
            statuses,
            session_id="session-1",
            event_type="error",
        )

        orchestrations._update_session_status(
            statuses,
            session_id="session-1",
            event_type="final",
        )

        self.assertEqual(statuses["session-1"], "error")


if __name__ == "__main__":
    unittest.main()
