#!/usr/bin/env bash
# start-dev.sh — launch both services in development mode

set -e

# ---- Backend ---------------------------------------------------------------
echo "▶ Starting FastAPI backend on :8000 ..."
cd backend
[ ! -f .env ] && cp .env.example .env && echo "  ⚠  Copied .env.example → .env  (fill in your API keys!)"
python -m venv .venv 2>/dev/null || true
source .venv/bin/activate
pip install -q -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# ---- Frontend --------------------------------------------------------------
echo "▶ Starting Vite dev server on :5173 ..."
cd frontend
npm install -q
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "  Backend  → http://localhost:8000"
echo "  Frontend → http://localhost:5173"
echo "  (Press Ctrl+C to stop both)"
echo ""

# Wait and forward signals
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait $BACKEND_PID $FRONTEND_PID
