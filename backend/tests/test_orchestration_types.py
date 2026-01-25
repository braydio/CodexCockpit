import unittest
from unittest.mock import AsyncMock

from app.codex.orchestration import OrchestrationManager
from app.codex.orchestration_types import DefinitionOfDone, TaskSpec


class DefinitionOfDoneTests(unittest.TestCase):
    """Unit tests for definition-of-done parsing."""

    def test_from_dict_defaults_to_empty_fields(self) -> None:
        """Ensure defaults are applied when definition-of-done fields are missing."""
        definition = DefinitionOfDone.from_dict({})

        self.assertEqual(definition.required_metrics, [])
        self.assertEqual(definition.optional_metrics, [])
        self.assertEqual(definition.blocking_issues, [])
        self.assertIsNone(definition.notes)

    def test_from_dict_populates_fields(self) -> None:
        """Ensure definition-of-done payload values are preserved."""
        payload = {
            "required_metrics": ["tests_pass"],
            "optional_metrics": ["lint_pass"],
            "blocking_issues": ["missing_docs"],
            "notes": "All required metrics must pass.",
        }

        definition = DefinitionOfDone.from_dict(payload)

        self.assertEqual(definition.required_metrics, ["tests_pass"])
        self.assertEqual(definition.optional_metrics, ["lint_pass"])
        self.assertEqual(definition.blocking_issues, ["missing_docs"])
        self.assertEqual(definition.notes, "All required metrics must pass.")


class TaskSpecTests(unittest.TestCase):
    """Unit tests for task specification parsing."""

    def test_from_dict_populates_definition_of_done(self) -> None:
        """Ensure task specs include the parsed definition-of-done values."""
        payload = {
            "task_id": "task-001",
            "goal": "Validate task spec",
            "workspace_root": "/workspace/CodexCockpit",
            "constraints": {"require_tests": True},
            "deliverables": [{"type": "doc", "path": "docs/plan.md"}],
            "definition_of_done": {"required_metrics": ["tests_pass"]},
        }

        task_spec = TaskSpec.from_dict(payload)

        self.assertEqual(task_spec.task_id, "task-001")
        self.assertEqual(task_spec.definition_of_done.required_metrics, ["tests_pass"])
        self.assertEqual(task_spec.constraints, {"require_tests": True})
        self.assertEqual(task_spec.deliverables, payload["deliverables"])

    def test_from_dict_raises_for_missing_required_fields(self) -> None:
        """Ensure missing required keys trigger a KeyError."""
        payload = {
            "goal": "Missing task id",
            "workspace_root": "/workspace/CodexCockpit",
        }

        with self.assertRaises(KeyError):
            TaskSpec.from_dict(payload)


class OrchestrationPlanCreationTests(unittest.TestCase):
    """Unit tests for orchestration plan creation."""

    def test_create_plan_omits_optional_steps_when_unused(self) -> None:
        """Ensure plan steps skip optional checks when task spec omits them."""
        task_spec = TaskSpec(
            task_id="task-002",
            goal="Plan minimal orchestration",
            workspace_root="/workspace/CodexCockpit",
            constraints={},
            deliverables=[],
            definition_of_done=DefinitionOfDone(),
        )
        manager = OrchestrationManager(
            register_session=AsyncMock(),
            start_session=AsyncMock(),
            get_driver=lambda _: None,
        )

        plan = manager.create_plan(task_spec)

        self.assertNotIn("Verify deliverables", plan.steps)
        self.assertNotIn("Evaluate required metrics", plan.steps)
        self.assertNotIn("Evaluate optional metrics", plan.steps)
        self.assertIn("Finalize definition of done", plan.steps)


if __name__ == "__main__":
    unittest.main()
