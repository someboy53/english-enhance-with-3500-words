# English Enhancement Tool — Deployment Guide

## Quick Start (Local)

```bash
# Full stack (align + player):
./run.sh

# Player only (lightweight):
./run.sh player
```

Opens at **http://127.0.0.1:8000** → redirects to Player page.

---

## Prerequisites

| Component | Version | Check |
|-----------|---------|-------|
| Python | 3.10+ | `python3 --version` |

**Full mode also needs:**
- ~1.2 GB free disk (MMS model download, one-time)
- ~4 GB RAM (model loads into memory during alignment)

**Player mode only needs:**
- ~50 MB RAM, ~100 MB disk (archives + deps)

---

## Manual Setup

### Full Stack (Align + Player)

```bash
pip install --break-system-packages -r backend/requirements.txt
cd backend
python3 -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

First run downloads the MMS model (~1.18 GB) to `~/.cache/torch/hub/checkpoints/`.

### Player Only

```bash
pip install --break-system-packages -r backend/requirements_player.txt
cd backend
python3 -m uvicorn player_app:app --host 0.0.0.0 --port 8000
```

No ML dependencies. Serves pre-aligned archives from `archives/`.

---

## VPS Deployment (Player Only)

The `deploy_vps.sh` script syncs archives + player code to a remote server:

```bash
./deploy_vps.sh root@12.34.56.78:/opt/eng-enhance
```

It does:
1. Creates the remote directory
2. Rsyncs `archives/`, `backend/` (player files only), `frontend/`, `run.sh`
3. Installs `requirements_player.txt` on the remote
4. Starts `player_app` on port 8000 with `nohup`

**What's NOT sent to VPS:** PyTorch deps, aligner.py, app.py, test files, batch scripts.

### Manual VPS Setup

If you prefer to do it manually:

```bash
# On VPS:
mkdir -p /opt/eng-enhance

# From local:
rsync -avz --exclude '__pycache__' --exclude 'aligner.py' --exclude 'app.py' \
    --exclude 'requirements.txt' --exclude 'batch_align.py' \
    archives/ backend/ frontend/ run.sh \
    root@12.34.56.78:/opt/eng-enhance/

# On VPS:
cd /opt/eng-enhance
pip install --break-system-packages -r backend/requirements_player.txt
cd backend
nohup python3 -m uvicorn player_app:app --host 0.0.0.0 --port 8000 > /tmp/eng-enhance.log 2>&1 &
```

### Systemd Service (VPS)

```ini
# /etc/systemd/system/eng-enhance.service
[Unit]
Description=English Enhancement Player
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/eng-enhance/backend
ExecStart=/usr/bin/python3 -m uvicorn player_app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now eng-enhance
```

### Nginx Reverse Proxy (Optional)

```nginx
server {
    listen 80;
    server_name eng.yourdomain.com;

    client_max_body_size 200M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 600s;
    }
}
```

---

## Data Management

### Adding new archives

Align on your local machine, then sync to VPS:

```bash
# After aligning new articles locally:
rsync -avz archives/ root@12.34.56.78:/opt/eng-enhance/archives/
```

Or re-sync the rename script's renumbered version if needed:

```bash
python3 rename_archives.py
rsync -avz archives/ root@12.34.56.78:/opt/eng-enhance/archives/
```

### Backup

```bash
tar -czf archives-backup-$(date +%Y%m%d).tar.gz archives/
```

### Restore

```bash
tar -xzf archives-backup-YYYYMMDD.tar.gz
```

---

## Troubleshooting

### Alignment returns empty words
- Audio should be clear speech, 16kHz mono preferred.
- Text must match the audio exactly.

### CUDA warnings
Harmless — the tool falls back to CPU. For GPU, install NVIDIA drivers + CUDA toolkit.

### Model download fails
```bash
wget -O ~/.cache/torch/hub/checkpoints/model.pt \
  https://dl.fbaipublicfiles.com/mms/torchaudio/ctc_alignment_mling_uroman/model.pt
```

### Port already in use
```bash
pkill -f uvicorn
# Then restart
```

---

## Verification

```bash
# Player only:
curl http://127.0.0.1:8000/api/archives        # → 40 archives with num/title
curl http://127.0.0.1:8000/player.html          # → 200
curl http://127.0.0.1:8000/audio/01_fall-in...  # → 200 (audio stream)

# Full stack:
curl -X POST http://127.0.0.1:8000/align \
  -F "text=hello world" \
  -F "title=Test" \
  -F "audio=@test.mp3"                          # → 200 with word count
```
