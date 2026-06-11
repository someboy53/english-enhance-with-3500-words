"""
Lightweight FastAPI app — Player only (archive browsing + audio serving).
No PyTorch/MMS dependency. Deployable on low-resource VPS.
"""

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse

app = FastAPI(title="English Enhancement — Player")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
ARCHIVES_DIR = Path(__file__).resolve().parent.parent / "archives"


# ── Frontend pages ──────────────────────────────────────────────────────


@app.get("/")
async def root():
    return RedirectResponse(url="/player.html")


@app.get("/player.html")
async def player_page():
    return FileResponse(FRONTEND_DIR / "player.html")


@app.get("/align.html")
async def align_page():
    return FileResponse(FRONTEND_DIR / "align.html")


@app.get("/style.css")
async def styles():
    return FileResponse(FRONTEND_DIR / "style.css")


@app.get("/app.js")
async def js():
    return FileResponse(FRONTEND_DIR / "app.js")


# ── Archive API ─────────────────────────────────────────────────────────


@app.get("/api/archives")
async def api_archives():
    result = []
    if not ARCHIVES_DIR.exists():
        return {"archives": result}

    for entry in sorted(ARCHIVES_DIR.iterdir()):
        if not entry.is_dir() or entry.name == ".gitkeep":
            continue
        meta_path = entry / "meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        else:
            meta = {"title": entry.name, "slug": entry.name, "created": "", "sentence_count": 0}
        # Extract number prefix for ordering
        import re
        m = re.match(r"^(\d{2,3})_", entry.name)
        if m:
            meta["num"] = int(m.group(1))
        result.append(meta)

    result.sort(key=lambda m: m.get("num", 9999))
    return {"archives": result}


@app.get("/api/archive/{slug}")
async def api_archive(slug: str):
    path = ARCHIVES_DIR / slug / "sentences.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Archive not found")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/audio/{slug}")
async def serve_audio(slug: str):
    archive_dir = ARCHIVES_DIR / slug
    if not archive_dir.exists():
        raise HTTPException(status_code=404, detail="Audio not found")
    for ext in (".mp3", ".wav", ".m4a", ".ogg"):
        candidate = archive_dir / f"audio{ext}"
        if candidate.exists():
            return FileResponse(candidate, media_type="audio/mpeg")
    raise HTTPException(status_code=404, detail="Audio not found")
