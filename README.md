# CodexCockpit

CodexCockpit is a control plane and UI for running Codex-style workflows through
an API-driven, session-scoped driver interface. The backend exposes endpoints to
create and run sessions, stream structured events, and orchestrate multiple
model sessions under a single run.

## Context Assembly

Codex driver prompts include a bounded repository context assembled from the
session workspace. The assembly step summarizes source files and extracts
keyword-matched snippets before building the prompt. See
[`docs/context-assembly.md`](docs/context-assembly.md) for details.

## Orchestration

The orchestration layer coordinates multiple session runs, aggregates events,
and captures definition-of-done metrics. Documentation is available in
[`docs/orchestration.md`](docs/orchestration.md), with a flow overview in
[`docs/FEATURE_FLOW.md`](docs/FEATURE_FLOW.md).

## Model Adapters

Local model runs use explicit adapter classes that wrap the chosen runtime
binary (for example Ollama). Configuration lives in
`backend/app/codex/models.py`, and documentation is available in
[`docs/model-adapters.md`](docs/model-adapters.md).

## Tests

Backend unit tests can be run with:

```
cd backend
python -m unittest discover
```

## Roadmap

The evolving development plan is tracked in
[`docs/ROADMAP.md`](docs/ROADMAP.md).

## UI Theme

The desktop UI ships with a terminal-inspired theme system that supports
dark/light modes, selectable terminal palettes, and reusable layout utilities.
See [`docs/ui-theme.md`](docs/ui-theme.md) for the full token and utility
catalog.
