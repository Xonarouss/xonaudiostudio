#!/usr/bin/env bash
# XonAudio Studio - Linux / WSL2 Automated Launcher
# Built by Xonarous Inc (https://xonarous.nl)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "====================================================================="
echo "               XONAUDIO STUDIO - XONAROUS INC"
echo "====================================================================="
echo ""

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 could not be found. Please install Python 3.10+."
    exit 1
fi

# 2. Virtual Environment
if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment (venv)..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install torch torchvision torchaudio
    pip install -r backend/requirements.txt
else
    source venv/bin/activate
fi

# 3. Frontend check
if [ ! -d "frontend/node_modules" ]; then
    echo "[*] Installing frontend web dependencies..."
    cd frontend && npm install && cd ..
fi

# 4. Model check & auto-update
python backend/download_models.py

# 5. Launch Servers
echo "[*] Starting FastAPI Backend on http://127.0.0.1:8000..."
python backend/main.py &
BACKEND_PID=$!

echo "[*] Starting React Frontend on http://localhost:5173..."
cd frontend && npm run dev &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT

# 6. Open Browser
sleep 3
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:5173
elif command -v open &> /dev/null; then
    open http://localhost:5173
fi

wait
