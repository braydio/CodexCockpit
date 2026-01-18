# CodexCockpit

CodexCockpit is a control plane and UI for running Codex-style workflows through
an API-driven, session-scoped driver interface.

## Context Assembly

Codex driver prompts now include a bounded repository context assembled from the
session workspace. The assembly step summarizes source files and extracts
keyword-matched snippets before building the prompt. See
[`docs/context-assembly.md`](docs/context-assembly.md) for details.

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

## UI Theme

The desktop UI ships with a terminal-inspired theme system that supports
dark/light modes and reusable layout utilities. See
[`docs/ui-theme.md`](docs/ui-theme.md) for the full token and utility catalog.
