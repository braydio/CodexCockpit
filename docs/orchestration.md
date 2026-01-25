# Orchestration Lifecycle

CodexCockpit orchestration treats every run as a session-scoped workflow driven
by structured events. The driver interface owns lifecycle coordination and keeps
execution model-neutral while the API and GUI consume explicit event payloads.

## Orchestration Modules

Orchestration support lives in the Codex control plane under
`backend/app/codex/`. The module set is intentionally thin so orchestration can
coordinate plans and metrics without bypassing the driver interface.

- `orchestration_types.py` defines the task specification, definition-of-done,
  and orchestration plan data structures.
- `orchestration.py` owns the `OrchestrationManager` that assembles plans,
  spawns sessions through the existing session registry, and aggregates events.
- `metrics.py` accumulates event counts, touched files, and error totals for
  definition-of-done evaluation and reporting.

## Orchestration API Endpoints

The control plane exposes orchestration endpoints for planning, starting runs,
and streaming aggregated events. These routes live in
`backend/app/api/orchestrations.py` and mirror the session streaming behavior
used in `backend/app/api/run.py`.

### Create a plan

`POST /orchestrations/plan` accepts a task specification payload and returns a
serialized orchestration plan.

### Start a run

`POST /orchestrations/run` accepts either a `plan_id` or a full task
specification, along with optional session overrides. The response returns the
run identifier and spawned session IDs.

### Stream aggregated events

`GET /orchestrations/{run_id}/events` streams server-sent events (SSE) that
merge session event streams. Clients should expect keep-alive comments and
`data:` payloads that wrap individual events.

## Lifecycle Stages

1. **Session initialization**
   - Create a session ID, record the workspace root, and declare model
     capabilities.
   - Emit a `status` event confirming readiness and any capability constraints.
2. **Task intake**
   - Accept a task spec that defines goals, constraints, and definition-of-done
     criteria.
   - Validate inputs and emit a `plan` event describing the initial plan.
3. **Execution and streaming**
   - Run tools and model steps through the driver interface.
   - Stream `status`, `tool`, `diff`, and `metrics` events as progress updates.
4. **Metrics evaluation**
   - Evaluate metrics against collected signals (tests, artifacts, validations).
   - Emit `metrics` events with pass/fail per metric and aggregated scores.
5. **Definition-of-done evaluation**
   - Determine completion based on metric results and required deliverables.
   - Emit a `final` or `error` event summarizing the outcome and next actions.
6. **Session closure**
   - Persist the final state, artifacts, and evaluation results for inspection.
   - Support replay or resumption per session state rules.

## Task Specification Schema

Task specifications keep orchestration deterministic by explicitly declaring
inputs, constraints, and definition-of-done requirements.

```json
{
  "task_id": "task-2024-05-21-001",
  "goal": "Document orchestration lifecycle and metrics",
  "workspace_root": "/workspace/CodexCockpit",
  "constraints": {
    "no_network": false,
    "require_tests": true,
    "formatting_required": true
  },
  "deliverables": [
    {
      "type": "document",
      "path": "docs/orchestration.md",
      "summary": "Lifecycle, metrics, and DoD guidance"
    }
  ],
  "definition_of_done": {
    "required_metrics": ["tests_pass", "doc_links_updated"],
    "optional_metrics": ["lint_pass"],
    "blocking_issues": ["unresolved_errors", "missing_deliverables"],
    "notes": "All required metrics must pass and blocking issues must be empty."
  }
}
```

## Metrics Evaluation Schema

Metrics are reported as structured results. Each metric carries a type, inputs,
expected output, and observed data so the GUI can render the evaluation trace.

```json
{
  "metric_id": "tests_pass",
  "title": "Backend test suite",
  "type": "command",
  "inputs": {
    "command": "cd backend && python -m unittest discover"
  },
  "expected": {
    "exit_code": 0
  },
  "observed": {
    "exit_code": 0,
    "stdout_excerpt": "Ran 5 tests in 0.020s",
    "stderr_excerpt": ""
  },
  "status": "pass",
  "captured_at": "2024-05-21T19:22:00Z"
}
```

## Definition-of-Done Evaluation

Definition-of-done (DoD) evaluation aggregates metric results and confirms that
all required deliverables and blocking issues are resolved.

```json
{
  "task_id": "task-2024-05-21-001",
  "required_metrics": {
    "tests_pass": "pass",
    "doc_links_updated": "pass"
  },
  "optional_metrics": {
    "lint_pass": "skipped"
  },
  "blocking_issues": [],
  "deliverables": {
    "docs/orchestration.md": "present",
    "docs/README.md": "updated",
    "README.md": "updated"
  },
  "status": "done",
  "summary": "All required metrics passed and deliverables are complete.",
  "evaluated_at": "2024-05-21T19:24:00Z"
}
```

## Event Payload Examples

Event payloads are typed and structured so the GUI can render lifecycle state
without interpreting model intent.

```json
{
  "event_id": "evt-001",
  "type": "status",
  "timestamp": "2024-05-21T19:10:00Z",
  "session_id": "session-123",
  "payload": {
    "state": "ready",
    "message": "Session initialized",
    "capabilities": {
      "tools": true,
      "streaming": true,
      "json_reliability": "high"
    }
  }
}
```

```json
{
  "event_id": "evt-009",
  "type": "metrics",
  "timestamp": "2024-05-21T19:22:00Z",
  "session_id": "session-123",
  "payload": {
    "metrics": [
      {
        "metric_id": "tests_pass",
        "status": "pass",
        "details": {
          "command": "cd backend && python -m unittest discover",
          "exit_code": 0
        }
      }
    ],
    "summary": {
      "passed": 1,
      "failed": 0
    }
  }
}
```

```json
{
  "event_id": "evt-014",
  "type": "final",
  "timestamp": "2024-05-21T19:24:00Z",
  "session_id": "session-123",
  "payload": {
    "status": "done",
    "definition_of_done": {
      "required_metrics_passed": true,
      "blocking_issues": 0,
      "deliverables_complete": true
    },
    "message": "Orchestration complete."
  }
}
```

## Metrics Evaluation Code Snippet

Use a structured evaluator that collects results and emits `metrics` events.

```python
from dataclasses import dataclass
from typing import Iterable


@dataclass
class MetricResult:
    metric_id: str
    status: str
    details: dict


def evaluate_metrics(metrics: Iterable[dict]) -> list[MetricResult]:
    results = []
    for metric in metrics:
        status = "pass" if metric["observed"]["exit_code"] == 0 else "fail"
        results.append(
            MetricResult(
                metric_id=metric["metric_id"],
                status=status,
                details=metric["observed"],
            )
        )
    return results
```

## Definition-of-Done Evaluation Code Snippet

```python
from dataclasses import dataclass
from typing import Iterable


@dataclass
class DoneEvaluation:
    status: str
    blocking_issues: list[str]
    required_metrics_passed: bool


def evaluate_definition_of_done(
    required_metric_results: Iterable[str],
    blocking_issues: list[str],
) -> DoneEvaluation:
    required_metrics_passed = all(result == "pass" for result in required_metric_results)
    status = "done" if required_metrics_passed and not blocking_issues else "blocked"
    return DoneEvaluation(
        status=status,
        blocking_issues=blocking_issues,
        required_metrics_passed=required_metrics_passed,
    )
```
