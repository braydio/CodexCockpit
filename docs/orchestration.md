# Orchestration

This document explains how Codex Cockpit orchestrates multiple model sessions,
tracks definition-of-done requirements, and aggregates metrics during runs. The
orchestration layer is implemented in `backend/app/codex/orchestration.py`,
`backend/app/codex/orchestration_types.py`, and
`backend/app/codex/metrics.py`.

## Core Concepts

### Task Specification

A task specification captures the goal, workspace, constraints, deliverables,
and definition-of-done requirements. It maps directly to the `TaskSpec` data
class:

```python
from app.codex.orchestration_types import TaskSpec, DefinitionOfDone

spec = TaskSpec(
    task_id="doc-update",
    goal="Document orchestration and update README",
    workspace_root="/workspace/CodexCockpit",
    constraints={"no_emojis": True},
    deliverables=[{"path": "docs/orchestration.md", "type": "doc"}],
    definition_of_done=DefinitionOfDone(
        required_metrics=["events.final"],
        optional_metrics=["events.diff"],
        blocking_issues=["error"],
        notes="All doc updates must link from the docs index.",
    ),
)
```

### Definition of Done

Definition-of-done requirements are stored in `DefinitionOfDone` and surfaced
through the API payloads. Required metrics and blocking issues let the
orchestration controller decide when a task can be marked complete.

### Orchestration Plan

The orchestration manager converts a task specification into a plan with ordered
steps. The plan is returned by `POST /orchestrations/plan` and can also be
embedded in `POST /orchestrations/run`.

```python
from app.codex.orchestration import OrchestrationManager

manager = OrchestrationManager()
plan = manager.create_plan(spec)
print(plan.steps)
```

## API Flow

### Create a Plan

```
POST /orchestrations/plan
{
  "task_spec": {
    "task_id": "doc-update",
    "goal": "Document orchestration",
    "workspace_root": "/workspace/CodexCockpit",
    "constraints": {},
    "deliverables": [{"path": "docs/orchestration.md", "type": "doc"}],
    "definition_of_done": {
      "required_metrics": ["events.final"],
      "optional_metrics": ["events.diff"],
      "blocking_issues": ["error"],
      "notes": "Document orchestration"
    }
  }
}
```

### Start a Run

```
POST /orchestrations/run
{
  "plan_id": "plan-...",
  "sessions": [
    {
      "model": "codex-default",
      "goal": "Write orchestration documentation",
      "workspace": "/workspace/CodexCockpit"
    }
  ]
}
```

### Stream Aggregated Events

```
GET /orchestrations/{run_id}/events
```

Events are streamed as SSE frames with JSON payloads. Each event includes
`meta.session_id` so consumers can track the source session.

## Metrics and Evaluation

The orchestration manager uses `MetricsAccumulator` to track event counts,
errors, and file references. These metrics can be evaluated against
`DefinitionOfDone` requirements when determining completion.

Example metrics summary payload:

```json
{
  "event_counts": {"status": 5, "final": 1},
  "files_touched": ["docs/orchestration.md"],
  "error_count": 0
}
```

## Orchestration Events and Status

Events are merged across sessions and streamed to the client. Session statuses
are updated as events close, preserving the same `completed`, `cancelled`, and
`error` semantics used for single-session runs. The orchestration layer does not
bypass the driver interface; it simply coordinates multiple sessions.
