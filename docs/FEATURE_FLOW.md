# Feature Flow

This document describes the current, implemented flow for running Codex-style
sessions and orchestration runs through the control plane. The flow mirrors the
backend modules and API endpoints in this repository.

## Session Flow (Single Driver Session)

1. **Create a session**
   - The client posts configuration to `POST /sessions`.
   - The server registers the session and stores driver metadata in
     `backend/app/codex/session.py`.

2. **Start the session run**
   - The client calls `POST /sessions/{session_id}/run`.
   - The session is marked `running`, and the selected driver is instructed to
     start via `CodexDriver.start_session`.

3. **Stream session events**
   - The client connects to `GET /sessions/{session_id}/events`.
   - Events are streamed as server-sent events (SSE). Keep-alive frames are sent
     every 15 seconds while the driver is idle.

4. **Finalize session state**
   - When the event stream ends, the session status is updated to `completed`,
     `cancelled`, or `error` based on the final event types.

## Orchestration Flow (Multiple Sessions)

1. **Create an orchestration plan**
   - The client posts a task specification to `POST /orchestrations/plan`.
   - The orchestration manager builds an ordered plan with definition-of-done
     steps using `OrchestrationManager.create_plan`.

2. **Start an orchestration run**
   - The client posts to `POST /orchestrations/run` with a plan ID or task
     spec and optional per-session overrides.
   - Each session is registered and started through the standard session
     registry, preserving the driver interface rule.

3. **Stream aggregated events**
   - The client connects to `GET /orchestrations/{run_id}/events`.
   - Events from all sessions are merged into a single SSE stream. Each event
     includes `meta.session_id` to identify the source session.

4. **Collect metrics and close sessions**
   - The orchestration manager records event statistics (counts, errors, file
     references) using `MetricsAccumulator`.
   - When streaming ends, each session is marked complete or failed based on its
     final event types.

## Event Types

Drivers emit structured events with `type`, `content`, and optional `meta`
fields. The GUI renders these events directly; it does not infer model intent.

Common event types include:

- `plan`
- `tool`
- `diff`
- `thought`
- `status`
- `final`
- `cancelled`
- `error`

## Related Documentation

- `docs/context-assembly.md` covers how the bounded prompt context is assembled.
- `docs/model-adapters.md` describes local model adapters and configuration.
- `docs/orchestration.md` details orchestration planning, metrics, and
  definition-of-done evaluation.
