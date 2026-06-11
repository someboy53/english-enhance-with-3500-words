"""
FastAPI backend: serves static frontend, alignment via MMS CTC, archive browsing.
No external services required — forced alignment runs locally.
"""

import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, RedirectResponse

from aligner import run_alignment, group_sentences
from archive import save_archive, list_archives, get_archive, get_audio_path

app = FastAPI(title="English Enhancement Tool")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


# ── Serve frontend pages ────────────────────────────────────────────────


@app.get("/")
async def root():
    return RedirectResponse(url="/player.html")


@app.get("/align.html")
async def align_page():
    return FileResponse(FRONTEND_DIR / "align.html")


@app.get("/player.html")
async def player_page():
    return FileResponse(FRONTEND_DIR / "player.html")


@app.get("/style.css")
async def styles():
    return FileResponse(FRONTEND_DIR / "style.css")


@app.get("/app.js")
async def js():
    return FileResponse(FRONTEND_DIR / "app.js")


# ── Alignment endpoint ──────────────────────────────────────────────────


@app.post("/align")
async def align(
    text: str = Form(...),
    title: str = Form(...),
    audio: UploadFile = File(...),
):
    # Save uploaded audio to temp file
    tmp_dir = Path(tempfile.mkdtemp())
    audio_tmp = tmp_dir / (audio.filename or "audio.mp3")
    with open(audio_tmp, "wb") as f:
        shutil.copyfileobj(audio.file, f)

    try:
        # Run forced alignment locally (MMS CTC aligner)
        alignment = run_alignment(audio_tmp, text)

        words = alignment.get("words", [])
        if not words:
            raise HTTPException(status_code=500, detail="No aligned words returned — check audio/transcript match")

        # Group into sentences
        sentences = group_sentences(words, text)

        # Save archive
        slug = save_archive(title, text, alignment, sentences, audio_tmp)

        duration = max((w.get("end", 0) for w in words), default=0.0)

        return {
            "title": title,
            "slug": slug,
            "word_count": len(words),
            "sentence_count": len(sentences),
            "duration": round(duration, 2),
        }

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ── Archive API ─────────────────────────────────────────────────────────


@app.get("/api/archives")
async def api_archives():
    return {"archives": list_archives()}


@app.get("/api/archive/{slug}")
async def api_archive(slug: str):
    data = get_archive(slug)
    if data is None:
        raise HTTPException(status_code=404, detail="Archive not found")
    return data


@app.get("/audio/{slug}")
async def serve_audio(slug: str):
    path = get_audio_path(slug)
    if path is None:
        raise HTTPException(status_code=404, detail="Audio not found")
    return FileResponse(path, media_type="audio/mpeg")
