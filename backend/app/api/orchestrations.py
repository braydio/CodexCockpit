"""API endpoints for orchestration planning and run streaming."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.codex.orchestration import OrchestrationManager
from app.codex.orchestration_types import DefinitionOfDone, OrchestrationPlan, TaskSpec
from app.codex.session import mark_finished

router = APIRouter()
LOGGER = logging.getLogger(__name__)
ORCHESTRATION_MANAGER = OrchestrationManager()

_PLANS: Dict[str, OrchestrationPlan] = {}
_RUNS: Dict[str, Dict[str, List[str]]] = {}


class DefinitionOfDonePayload(BaseModel):
    """Payload describing definition-of-done requirements."""

    required_metrics: List[str] = Field(default_factory=list)
    optional_metrics: List[str] = Field(default_factory=list)
    blocking_issues: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class TaskSpecPayload(BaseModel):
    """Payload describing task requirements for orchestration."""

    task_id: str
    goal: str
    workspace_root: str
    constraints: Dict[str, object] = Field(default_factory=dict)
    deliverables: List[Dict[str, object]] = Field(default_factory=list)
    definition_of_done: DefinitionOfDonePayload = Field(
        default_factory=DefinitionOfDonePayload
    )


class CreatePlanRequest(BaseModel):
    """Request body for creating orchestration plans."""

    task_spec: TaskSpecPayload


class OrchestrationSessionSpec(BaseModel):
    """Session configuration for an orchestration run."""

    session_id: Optional[str] = None
    goal: Optional[str] = None
    model: Optional[str] = None
    workspace: Optional[str] = None
    endpoint: Optional[str] = None


class StartRunRequest(BaseModel):
    """Request body for starting orchestration runs."""

    plan_id: Optional[str] = None
    task_spec: Optional[TaskSpecPayload] = None
    sessions: List[OrchestrationSessionSpec] = Field(default_factory=list)
    run_id: Optional[str] = None


def _build_task_spec(payload: TaskSpecPayload) -> TaskSpec:
    """Convert a task payload into a TaskSpec instance.

    Args:
        payload: Task specification payload.

    Returns:
        Parsed TaskSpec instance.
    """
    definition = DefinitionOfDone(
        required_metrics=payload.definition_of_done.required_metrics,
        optional_metrics=payload.definition_of_done.optional_metrics,
        blocking_issues=payload.definition_of_done.blocking_issues,
        notes=payload.definition_of_done.notes,
    )
    return TaskSpec(
        task_id=payload.task_id,
        goal=payload.goal,
        workspace_root=payload.workspace_root,
        constraints=dict(payload.constraints),
        deliverables=list(payload.deliverables),
        definition_of_done=definition,
    )


def _serialize_plan(plan: OrchestrationPlan) -> dict:
    """Serialize an orchestration plan for API responses.

    Args:
        plan: Orchestration plan to serialize.

    Returns:
        Serialized plan payload.
    """
    task_spec = plan.task_spec
    definition = task_spec.definition_of_done
    return {
        "plan_id": plan.plan_id,
        "task_spec": {
            "task_id": task_spec.task_id,
            "goal": task_spec.goal,
            "workspace_root": task_spec.workspace_root,
            "constraints": dict(task_spec.constraints),
            "deliverables": list(task_spec.deliverables),
            "definition_of_done": {
                "required_metrics": list(definition.required_metrics),
                "optional_metrics": list(definition.optional_metrics),
                "blocking_issues": list(definition.blocking_issues),
                "notes": definition.notes,
            },
        },
        "steps": list(plan.steps),
        "created_at": plan.created_at.isoformat(),
    }


def _resolve_plan(request: StartRunRequest) -> OrchestrationPlan:
    """Resolve an orchestration plan from a run request.

    Args:
        request: Run request containing a plan identifier or task spec.

    Returns:
        Resolved orchestration plan.

    Raises:
        HTTPException: If the plan cannot be resolved.
    """
    if request.plan_id:
        plan = _PLANS.get(request.plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        return plan

    if not request.task_spec:
        raise HTTPException(
            status_code=400, detail="task_spec is required when plan_id is not set"
        )
    plan = ORCHESTRATION_MANAGER.create_plan(_build_task_spec(request.task_spec))
    _PLANS[plan.plan_id] = plan
    return plan


def _merge_session_config(
    task_spec: TaskSpec,
    session_spec: OrchestrationSessionSpec,
) -> dict:
    """Build a session config from task and session payloads.

    Args:
        task_spec: Task specification providing defaults.
        session_spec: Session-specific override values.

    Returns:
        Session configuration dictionary.
    """
    return {
        "goal": session_spec.goal or task_spec.goal,
        "model": session_spec.model or "codex-default",
        "workspace": session_spec.workspace or task_spec.workspace_root,
        "endpoint": session_spec.endpoint,
    }


def _update_session_status(
    status_by_session: Dict[str, str],
    session_id: Optional[str],
    event_type: Optional[str],
) -> None:
    """Update per-session completion status based on streamed events.

    Args:
        status_by_session: Map of session IDs to status labels.
        session_id: Session identifier extracted from an event.
        event_type: Event type emitted by the driver.
    """
    if not session_id or not event_type:
        return

    current_status = status_by_session.get(session_id, "completed")
    if current_status in {"error", "cancelled"}:
        return

    if event_type == "error":
        status_by_session[session_id] = "error"
    elif event_type == "cancelled":
        status_by_session[session_id] = "cancelled"
    else:
        status_by_session[session_id] = "completed"


@router.post("/plan")
async def create_plan(request: CreatePlanRequest) -> dict:
    """Create an orchestration plan for a provided task specification.

    Args:
        request: Payload containing the task specification.

    Returns:
        Serialized orchestration plan.
    """
    task_spec = _build_task_spec(request.task_spec)
    plan = ORCHESTRATION_MANAGER.create_plan(task_spec)
    _PLANS[plan.plan_id] = plan
    return _serialize_plan(plan)


@router.post("/run")
async def start_run(request: StartRunRequest) -> dict:
    """Start an orchestration run and spawn session workers.

    Args:
        request: Run request containing session and plan details.

    Returns:
        Response payload with run details and session identifiers.
    """
    plan = _resolve_plan(request)
    task_spec = plan.task_spec
    session_specs = request.sessions or [OrchestrationSessionSpec()]

    session_ids = []
    for spec in session_specs:
        config = _merge_session_config(task_spec, spec)
        session_id = await ORCHESTRATION_MANAGER.spawn_minion_session(
            config,
            session_id=spec.session_id,
        )
        session_ids.append(session_id)

    run_id = request.run_id or f"run-{uuid.uuid4()}"
    _RUNS[run_id] = {"plan_id": plan.plan_id, "session_ids": session_ids}

    return {
        "run_id": run_id,
        "plan": _serialize_plan(plan),
        "session_ids": session_ids,
    }


@router.get("/{run_id}/events")
async def stream_aggregated_events(run_id: str) -> StreamingResponse:
    """Stream aggregated events for an orchestration run via SSE.

    Args:
        run_id: Orchestration run identifier.

    Returns:
        SSE streaming response with aggregated events.
    """
    run = _RUNS.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    session_ids = run.get("session_ids", [])
    if not session_ids:
        raise HTTPException(status_code=409, detail="Run has no sessions to stream")

    async def event_stream():
        status_by_session = {session_id: "completed" for session_id in session_ids}
        LOGGER.info("Entered orchestration event stream", extra={"run_id": run_id})
        yield ": keep-alive\n\n"
        try:
            iterator = ORCHESTRATION_MANAGER.stream_aggregated_events(
                session_ids
            ).__aiter__()
            while True:
                try:
                    event = await asyncio.wait_for(iterator.__anext__(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
                    continue
                except StopAsyncIteration:
                    break

                meta = event.get("meta")
                session_id = meta.get("session_id") if isinstance(meta, dict) else None
                _update_session_status(
                    status_by_session,
                    session_id,
                    event.get("type"),
                )
                yield f"data: {json.dumps(event)}\n\n"
        except Exception:
            for session_id in session_ids:
                status_by_session[session_id] = "error"
            LOGGER.exception(
                "Orchestration event stream error",
                extra={"run_id": run_id},
            )
        finally:
            await asyncio.gather(
                *[
                    mark_finished(session_id, status)
                    for session_id, status in status_by_session.items()
                ],
                return_exceptions=True,
            )

    return StreamingResponse(event_stream(), media_type="text/event-stream")
