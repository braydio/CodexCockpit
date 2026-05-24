# Development Roadmap

This roadmap outlines the next steps for evolving Codex Cockpit into a central
orchestration unit. Each phase lists objectives, concrete deliverables, and
validation criteria. Update this document as milestones complete or priorities
shift.

## Phase 1: Orchestration Readiness

**Objective:** Stabilize orchestration APIs, metrics, and documentation so the
control plane can reliably coordinate multiple model sessions.

**Deliverables**
- Document orchestration APIs, task specs, and definition-of-done requirements.
- Ensure orchestration events always include `meta.session_id` for aggregation.
- Verify metrics output from `MetricsAccumulator` aligns with operator needs.
- Add examples showing plan creation, run start, and SSE consumption.

**Validation**
- Unit tests cover plan serialization, metrics accumulation, and event merging.
- Documentation in `docs/orchestration.md` and `docs/FEATURE_FLOW.md` stays
  aligned with API behavior.

## Phase 2: Definition-of-Done Evaluation

**Objective:** Formalize how the system decides when a subtask is complete.

**Deliverables**
- Add a definition-of-done evaluation module that consumes metrics summaries.
- Surface evaluation results in orchestration event streams (e.g. `status` or
  `final` events containing metric verdicts).
- Update API responses to include definition-of-done status per session.

**Validation**
- New unit tests cover pass/fail scenarios with required and optional metrics.
- Event payloads and status transitions are documented and consistent.

## Phase 3: Multi-Agent Coordination

**Objective:** Allow the controller to assign distinct objectives to minion
sessions while maintaining global visibility.

**Deliverables**
- Add scheduling logic that respects task dependencies.
- Introduce per-session constraints (e.g. capability flags, tool access).
- Provide a run summary endpoint that consolidates per-session progress.

**Validation**
- Integration tests simulate multiple sessions with dependency ordering.
- Metrics report completion status per task and at the run level.

## Phase 4: UI and Operator Experience

**Objective:** Surface orchestration progress and definition-of-done metrics in
GUI and desktop surfaces.

**Deliverables**
- Add UI panels for orchestration runs, session status, and metrics summaries.
- Provide filters for event types and session IDs.
- Ensure UI never bypasses the control plane or driver interface.

**Validation**
- UI checks confirm event rendering and metrics accuracy.
- Manual QA verifies the workflow described in `docs/FEATURE_FLOW.md`.

## Phase 5: Framework Layer (Optional)

**Objective:** Introduce declarative frameworks that map to orchestration plans.

**Deliverables**
- Define framework schema and validation rules.
- Implement plan generation from framework definitions.
- Document framework usage in `docs/FRAMEWORKS.md`.

**Validation**
- Framework validation tests ensure schema correctness and dependency checks.
- Orchestration plans derived from frameworks align with definition-of-done
  requirements.
