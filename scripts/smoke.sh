#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  echo "⚠️  Virtualenv is not active. Recommended: source .venv/bin/activate"
fi

echo "✅ Running pytest"
pytest -q

echo "✅ Starting app for health check"
export FLASK_PORT="${FLASK_PORT:-5200}"
python "${ROOT_DIR}/run.py" >/tmp/qryer_smoke.log 2>&1 &
APP_PID=$!

cleanup() {
  kill "${APP_PID}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

sleep 2
curl -fsS "http://127.0.0.1:${FLASK_PORT}/api/health" >/dev/null
echo "✅ /api/health OK"

if [[ -n "${AUTH_TOKEN:-}" ]]; then
  echo "✅ Socket.IO smoke"
  AUTH_TOKEN="${AUTH_TOKEN}" python "${ROOT_DIR}/scripts/socket_smoke.py"
else
  echo "ℹ️  AUTH_TOKEN not set, skipping socket smoke"
fi

if command -v docker >/dev/null 2>&1; then
  echo "✅ Docker build/run smoke"
  docker build -t q-ryer "${ROOT_DIR}"
  docker run --env-file "${ROOT_DIR}/.env.local" -d -p 5200:5200 --name q-ryer-smoke q-ryer
  sleep 2
  curl -fsS "http://127.0.0.1:5200/api/health" >/dev/null
  docker rm -f q-ryer-smoke >/dev/null
else
  echo "ℹ️  docker not found, skipped"
fi
