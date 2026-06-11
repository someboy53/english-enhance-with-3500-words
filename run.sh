#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

MODE="${1:-full}"

echo "=== English Enhancement Tool ==="
echo ""

if [ "$MODE" = "player" ]; then
    echo "[1/2] Installing lightweight dependencies (Player only)..."
    pip install --break-system-packages -q -r backend/requirements_player.txt

    echo "[2/2] Starting Player on http://127.0.0.1:8000"
    echo ""
    cd backend
    python3 -m uvicorn player_app:app --host 0.0.0.0 --port 8000 --reload
else
    echo "[1/3] Starting Gentle (Docker)..."
    if command -v docker &>/dev/null; then
        docker compose up -d gentle 2>/dev/null || docker-compose up -d gentle 2>/dev/null
        echo "      Gentle API → http://127.0.0.1:8765"
    else
        echo "[!] Docker not found. Gentle must be running elsewhere at 127.0.0.1:8765"
    fi

    echo "[2/3] Installing Python dependencies..."
    pip install --break-system-packages -q -r backend/requirements.txt

    echo "[3/3] Starting backend (Align + Player) on http://127.0.0.1:8000"
    echo ""
    cd backend
    python3 -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
fi
