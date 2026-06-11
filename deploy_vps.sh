#!/usr/bin/env bash
# Deploy the Player-only version to a VPS.
# Usage:
#   ./deploy_vps.sh user@vps-ip:/path/to/deploy
#
# Example:
#   ./deploy_vps.sh root@12.34.56.78:/opt/eng-enhance

set -e

if [ -z "$1" ]; then
    echo "Usage: ./deploy_vps.sh user@host:/remote/path"
    echo "Example: ./deploy_vps.sh root@12.34.56.78:/opt/eng-enhance"
    exit 1
fi

REMOTE="$1"
REMOTE_HOST="${REMOTE%%:*}"
REMOTE_PATH="${REMOTE#*:}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Deploy Player to VPS ==="
echo "Target: $REMOTE"
echo ""

# 1. Create remote directory
echo "[1/3] Creating remote directory..."
ssh "$REMOTE_HOST" "mkdir -p $REMOTE_PATH"

# 2. Rsync: archives + backend + frontend (no torch/ctc stuff)
echo "[2/3] Syncing files..."
rsync -avz --progress \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude 'aligner.py' \
    --exclude 'app.py' \
    --exclude 'requirements.txt' \
    --exclude 'docker-compose.yml' \
    --exclude 'batch_align.py' \
    --exclude 'rename_archives.py' \
    --exclude 'design*' \
    --exclude 'Design*' \
    --exclude 'DESIGN*' \
    --exclude 'deploy_vps.sh' \
    --exclude 'test' \
    archives/ \
    backend/ \
    frontend/ \
    run.sh \
    "$REMOTE"

# 3. Install and start on remote
echo ""
echo "[3/3] Installing dependencies and starting on remote..."
ssh "$REMOTE_HOST" << ENDSSH
    set -e
    cd "$REMOTE_PATH"
    
    # Install minimal Python deps
    pip install --break-system-packages -q -r backend/requirements_player.txt
    
    # Kill old process if running
    pkill -f "player_app:app" 2>/dev/null || true
    
    # Start in background
    cd backend
    nohup python3 -m uvicorn player_app:app --host 0.0.0.0 --port 8000 > /tmp/eng-enhance.log 2>&1 &
    
    sleep 2
    echo "Deployed! Check: http://$REMOTE_HOST:8000"
ENDSSH

echo ""
echo "Done. Open http://$REMOTE_HOST:8000"
