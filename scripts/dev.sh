#!/usr/bin/env bash
# Arranca la API (FastAPI) y la web (Next.js) juntas para desarrollo.
set -e
cd "$(dirname "$0")/.."

echo "Arrancando API en http://127.0.0.1:8000 …"
.venv/bin/uvicorn backend.main:app --reload --port 8000 &
API_PID=$!

echo "Arrancando web en http://127.0.0.1:3000 …"
(cd web && npm run dev) &
WEB_PID=$!

trap 'kill $API_PID $WEB_PID 2>/dev/null || true' EXIT
wait
