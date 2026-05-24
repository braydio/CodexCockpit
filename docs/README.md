# Documentation Index

## Control Plane

- `docs/context-assembly.md` explains how the backend assembles bounded prompt
  context for Codex sessions.
- `docs/orchestration.md` covers orchestration planning, session aggregation,
  and definition-of-done metrics.
- `docs/FEATURE_FLOW.md` maps the runtime flow across session and orchestration
  endpoints.
- `docs/FRAMEWORKS.md` documents the current status of framework support.

## Model metadata

The authoritative source of model metadata is the `MODEL_REGISTRY` defined in
`backend/app/codex/models.py`. API responses in `backend/app/api/models.py`
serialize their model list directly from this registry to keep names and
capabilities consistent.

## UI styling

The desktop UI theme tokens and utility classes are documented in
`docs/ui-theme.md`.

## Roadmap

- `docs/ROADMAP.md` tracks the development plan for orchestration and future
  features.
