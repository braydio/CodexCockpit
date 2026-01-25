# Documentation Index

## Orchestration lifecycle

[`docs/orchestration.md`](orchestration.md) documents the session orchestration
lifecycle, including metrics evaluation and definition-of-done criteria, so
operators can understand how runs are coordinated and completed. The orchestration
module implementations live under `backend/app/codex/` for planning, metrics, and
event aggregation.

## Model metadata

The authoritative source of model metadata is the `MODEL_REGISTRY` defined in
`backend/app/codex/models.py`. API responses in `backend/app/api/models.py`
serialize their model list directly from this registry to keep names and
capabilities consistent.

## UI styling

The desktop UI theme tokens and utility classes are documented in
[`docs/ui-theme.md`](ui-theme.md).
