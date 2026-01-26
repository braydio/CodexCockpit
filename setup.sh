#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<'EOF'
Usage: ./setup.sh [options]

Sets up a disposable cloud/CI machine to build + smoke-test this repo.

Options:
  --with-system       Install missing system deps via apt-get (Ubuntu/Debian).
  --skip-system       Never install system deps (default).
  --smoke             Start backend and hit /models (default).
  --no-smoke          Skip backend smoke test.
  --port <port>       Backend port for smoke test (default: 8787).
  -h, --help          Show help.
EOF
}

WITH_SYSTEM=0
SMOKE=1
PORT=8787

while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-system) WITH_SYSTEM=1; shift ;;
    --skip-system) WITH_SYSTEM=0; shift ;;
    --smoke) SMOKE=1; shift ;;
    --no-smoke) SMOKE=0; shift ;;
    --port) PORT="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

cd "$ROOT_DIR"

need_cmd() {
  command -v "$1" >/dev/null 2>&1
}

if [[ -z "${PORT}" ]]; then
  echo "Missing --port value" >&2
  exit 2
fi

if [[ "$WITH_SYSTEM" -eq 1 ]]; then
  if need_cmd apt-get; then
    if [[ "$(id -u)" -ne 0 ]] && ! need_cmd sudo; then
      echo "Need sudo (or run as root) to install system deps." >&2
      exit 1
    fi

    SUDO=()
    if [[ "$(id -u)" -ne 0 ]]; then
      SUDO=(sudo)
    fi

    "${SUDO[@]}" apt-get update -y
    "${SUDO[@]}" apt-get install -y \
      ca-certificates \
      curl \
      python3 \
      python3-venv \
      python3-pip \
      nodejs \
      npm
  else
    echo "--with-system requested, but apt-get not found; skipping system install." >&2
  fi
fi

echo "==> Backend: venv + deps"
BACKEND_DIR="$ROOT_DIR/backend"
VENV_DIR="$BACKEND_DIR/.venv"

if ! need_cmd python3; then
  echo "python3 not found. Re-run with --with-system on Ubuntu/Debian, or install Python 3.11+." >&2
  exit 1
fi

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$BACKEND_DIR/requirements.txt"

echo "==> Backend: compile check"
"$VENV_DIR/bin/python" -m compileall -q "$BACKEND_DIR/app"

echo "==> Desktop: npm install + build"
DESKTOP_DIR="$ROOT_DIR/codex-cockpit-desktop"

if ! need_cmd node || ! need_cmd npm; then
  cat >&2 <<'EOF'
node/npm not found.
- On Ubuntu/Debian: re-run with --with-system (installs distro node/npm), OR install Node.js 20 manually.
- Then re-run: ./setup.sh
EOF
  exit 1
fi

pushd "$DESKTOP_DIR" >/dev/null
if [[ -f package-lock.json ]]; then
  npm ci
else
  npm install
fi
npm run build
popd >/dev/null

if [[ "$SMOKE" -eq 1 ]]; then
  echo "==> Smoke test: start backend + GET /models"
  if ! need_cmd curl; then
    echo "curl not found; skipping smoke test. (Install curl or use --with-system.)" >&2
    exit 0
  fi

  BACKEND_PID=""
  cleanup() {
    if [[ -n "${BACKEND_PID}" ]] && kill -0 "${BACKEND_PID}" >/dev/null 2>&1; then
      kill "${BACKEND_PID}" >/dev/null 2>&1 || true
      wait "${BACKEND_PID}" >/dev/null 2>&1 || true
    fi
  }
  trap cleanup EXIT

  (
    cd "$BACKEND_DIR"
    exec "$VENV_DIR/bin/python" -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT"
  ) >/tmp/codex-cockpit-backend.log 2>&1 &
  BACKEND_PID="$!"

  for _ in {1..40}; do
    if curl -fsS "http://127.0.0.1:${PORT}/models/" >/dev/null 2>&1; then
      break
    fi
    sleep 0.25
  done

  curl -fsS "http://127.0.0.1:${PORT}/models/" | head -c 200 || {
    echo "Smoke test failed. Backend log (tail):" >&2
    tail -n 60 /tmp/codex-cockpit-backend.log >&2 || true
    exit 1
  }
  echo
  echo "==> Smoke test: OK"
fi

echo "==> Done"

