from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class DefinitionOfDone:
    """Definition-of-done requirements for a task.

    Attributes:
        required_metrics: Metric identifiers that must pass.
        optional_metrics: Metric identifiers that are tracked but not required.
        blocking_issues: Issues that block completion when present.
        notes: Human-readable notes describing expectations.
    """

    required_metrics: List[str] = field(default_factory=list)
    optional_metrics: List[str] = field(default_factory=list)
    blocking_issues: List[str] = field(default_factory=list)
    notes: Optional[str] = None

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "DefinitionOfDone":
        """Create a definition-of-done object from a raw dictionary.

        Args:
            payload: Raw dictionary with optional definition-of-done keys.

        Returns:
            A populated ``DefinitionOfDone`` instance.
        """
        return cls(
            required_metrics=list(payload.get("required_metrics", [])),
            optional_metrics=list(payload.get("optional_metrics", [])),
            blocking_issues=list(payload.get("blocking_issues", [])),
            notes=payload.get("notes"),
        )


@dataclass(frozen=True)
class TaskSpec:
    """Task specification used to drive orchestration planning.

    Attributes:
        task_id: Stable task identifier provided by the caller.
        goal: Human-readable description of the task goal.
        workspace_root: Workspace root where the task executes.
        constraints: Constraints applied during execution.
        deliverables: Expected deliverables produced by the task.
        definition_of_done: Completion requirements for the task.
    """

    task_id: str
    goal: str
    workspace_root: str
    constraints: Dict[str, Any] = field(default_factory=dict)
    deliverables: List[Dict[str, Any]] = field(default_factory=list)
    definition_of_done: DefinitionOfDone = field(
        default_factory=DefinitionOfDone
    )

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "TaskSpec":
        """Build a task specification from a dictionary.

        Args:
            payload: Raw dictionary matching the task schema.

        Returns:
            A ``TaskSpec`` instance built from the provided payload.
        """
        definition = DefinitionOfDone.from_dict(
            payload.get("definition_of_done", {})
        )
        return cls(
            task_id=payload["task_id"],
            goal=payload["goal"],
            workspace_root=payload["workspace_root"],
            constraints=dict(payload.get("constraints", {})),
            deliverables=list(payload.get("deliverables", [])),
            definition_of_done=definition,
        )


@dataclass(frozen=True)
class OrchestrationPlan:
    """Plan describing how a task will be orchestrated.

    Attributes:
        plan_id: Unique plan identifier.
        task_spec: The task specification this plan is based on.
        steps: Ordered list of high-level orchestration steps.
        created_at: Timestamp for plan creation in UTC.
    """

    plan_id: str
    task_spec: TaskSpec
    steps: List[str]
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
