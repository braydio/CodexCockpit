# Context Assembly

The Codex drivers now build a bounded repository context before prompting the
model. The context assembly step uses the session's explicit `workspace` root and
scans source files with an allowlist of extensions while skipping large or
irrelevant directories (for example `.venv`, `node_modules`, `dist`, `build`, and
`.git`).

## What Gets Collected

- A summary list of matching source files (bounded by a maximum count).
- Keyword-matched snippets derived from the user goal, with per-file size limits
  and per-snippet limits to keep prompts explicit and bounded.
- A controlled list of non-fatal errors (for example, unreadable files) that is
  surfaced alongside the prompt for transparency.

## Prompt Construction

The prompt includes the goal, workspace root, repository summary, and snippet
matches. The drivers instruct the model to rely only on the provided context and
request additional files when needed.

## Running Tests

Unit tests for context assembly live under `backend/tests` and can be executed
with:

```
cd backend
python -m unittest discover
```
