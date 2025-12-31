# Repository Guidelines

## Project Structure & Module Organization
- `backend/` is the FastAPI control plane. Core code lives in `backend/app/` with routers under `backend/app/api/` and entrypoint `backend/app/main.py`.
- `gui/` is a minimal static cockpit UI served via `gui/index.html`.
- `codex-cockpit-desktop/` is the desktop app (Vue + Vite + Tauri). Source is in `codex-cockpit-desktop/src/`, assets in `codex-cockpit-desktop/public/`, and native shell code in `codex-cockpit-desktop/src-tauri/`.
- `docs/` and `frontend/` are currently empty.

## Build, Test, and Development Commands
- `cd backend && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt` initializes the API environment.
- `cd backend && ./run.sh` runs the FastAPI server on `http://localhost:8787` via Uvicorn.
- `cd gui && python -m http.server 8080` serves the minimal GUI at `http://localhost:8080`.
- `cd codex-cockpit-desktop && npm install` installs desktop dependencies.
- `cd codex-cockpit-desktop && npm run dev` starts the Vite dev server; `npm run build` produces a production build.
- `cd codex-cockpit-desktop && npm run tauri` runs Tauri CLI commands (build, dev, etc.).

## Coding Style & Naming Conventions
- Python: 4-space indentation, double-quoted strings, and conventional snake_case for modules and functions.
- TypeScript/Vue: double-quoted strings and semicolons as seen in `codex-cockpit-desktop/src/main.ts`.
- HTML/CSS: 2-space indentation as in `gui/index.html`.
- No formatter or linter is configured; follow the surrounding file style.

## Testing Guidelines
- No automated tests are currently present. If you add tests, document the framework and add a clear `npm` or `python` command to run them.

## Commit & Pull Request Guidelines
- Git history uses short, imperative subjects (e.g., `GUI`, `backend root`); follow this lightweight style unless a new convention is introduced.
- PRs should include a concise summary, reproduction or verification steps, and screenshots for UI changes.

## Architecture & Safety Rules
- The GUI never calls models or the filesystem directly; all intelligence and tool execution must go through the API driver interface.
- Codex execution is session-scoped and event-driven; stream progress and emit structured events, not raw blobs.
- Keep model assumptions explicit and avoid hidden environment dependencies (see `RULES.md` for full constraints).
