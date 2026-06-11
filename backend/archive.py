"""
Archive storage: read, write, list alignment archives on the filesystem.
"""

import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

ARCHIVES_DIR = Path(os.environ.get("ARCHIVES_DIR", Path(__file__).resolve().parent.parent / "archives"))


def slugify(title: str) -> str:
    """Convert a title to a safe directory name."""
    slug = re.sub(r"[^\w\s-]", "", title).strip().lower()
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug or "untitled"


def save_archive(title: str, transcript_text: str, alignment_json: dict,
                 sentences: list[dict], audio_path: Path) -> str:
    """Save all alignment artifacts into archives/{slug}/. Returns the slug."""
    slug = slugify(title)
    archive_dir = ARCHIVES_DIR / slug
    archive_dir.mkdir(parents=True, exist_ok=True)

    # Write text
    (archive_dir / "transcript.txt").write_text(transcript_text, encoding="utf-8")

    # Write Gentle raw alignment
    (archive_dir / "alignment.json").write_text(
        json.dumps(alignment_json, ensure_ascii=False, indent=2), encoding="utf-8")

    # Write sentence groups
    (archive_dir / "sentences.json").write_text(
        json.dumps({"title": title, "sentences": sentences}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    # Copy audio (preserve original extension)
    ext = audio_path.suffix or ".mp3"
    dest = archive_dir / f"audio{ext}"
    shutil.copy2(audio_path, dest)

    # Metadata
    meta = {
        "title": title,
        "slug": slug,
        "created": datetime.now(timezone.utc).isoformat(),
        "word_count": len(alignment_json.get("words", [])),
        "sentence_count": len(sentences),
        "duration": _extract_duration(alignment_json),
    }
    (archive_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    return slug


def list_archives() -> list[dict]:
    """Return list of all saved archives with metadata, sorted by number prefix."""
    result = []
    if not ARCHIVES_DIR.exists():
        return result
    for entry in sorted(ARCHIVES_DIR.iterdir()):
        if not entry.is_dir() or entry.name == ".gitkeep":
            continue
        meta_path = entry / "meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        else:
            meta = {"title": entry.name, "slug": entry.name, "created": "", "sentence_count": 0}
        # Extract number prefix from slug (e.g., "01_xxx")
        m = re.match(r"^(\d{2,3})_", entry.name)
        if m:
            meta["num"] = int(m.group(1))
        result.append(meta)
    # Sort by number if present, otherwise by slug
    result.sort(key=lambda m: m.get("num", 9999))
    return result


def get_archive(slug: str) -> dict | None:
    """Load sentences.json for a given archive slug."""
    path = ARCHIVES_DIR / slug / "sentences.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def get_audio_path(slug: str) -> Path | None:
    """Find the audio file inside an archive directory."""
    archive_dir = ARCHIVES_DIR / slug
    if not archive_dir.exists():
        return None
    for ext in (".mp3", ".wav", ".m4a", ".ogg"):
        candidate = archive_dir / f"audio{ext}"
        if candidate.exists():
            return candidate
    return None


def _extract_duration(alignment: dict) -> float:
    words = alignment.get("words", [])
    if not words:
        return 0.0
    ends = [w.get("end", 0) for w in words if w.get("end")]
    return max(ends) if ends else 0.0
