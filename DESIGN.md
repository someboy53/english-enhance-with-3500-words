# English Enhancement Tool — Technical Design Document

## 1. Overview & Goal

A two-page web tool for English learners:
1. **Align Page** — Upload text + audio, run MMS forced alignment, save as a titled archive.
2. **Player Page** — Browse numbered archives in a sidebar, click sentences to seek & play audio.

Two deployment modes:
- **Full** (local workstation) — Align + Player with PyTorch/MMS model.
- **Player-only** (VPS) — Lightweight, no ML deps, serves pre-aligned archives.

---

## 2. Architecture

```
┌─────────────────────────┐     ┌──────────────────────────┐
│  Frontend (two pages)   │────▶│  Python Backend (FastAPI) │
│  align.html / player.html│◀────│  + MMS CTC Aligner       │
└─────────────────────────┘     └──────────────────────────┘
                                          │
                                          ▼
                                ┌──────────────────┐
                                │  Archive Dir     │
                                │  01_title/ ...   │
                                │  40_title/       │
                                └──────────────────┘
```

### 2.1 Forced Alignment Engine
- **Library:** `ctc-forced-aligner` (Python-native, no Docker/Kaldi).
- **Model:** Facebook MMS-1B (`torchaudio.pipelines.MMS_FA`).
- **Model cache:** `~/.cache/torch/hub/checkpoints/model.pt` (~1.18 GB, one-time download).

### 2.2 Two Backend Apps

| App | File | Use | Deps |
|-----|------|-----|------|
| **Full** | `backend/app.py` | Align + Player | PyTorch, torchaudio, ctc-forced-aligner |
| **Player** | `backend/player_app.py` | Archive browse + audio serve only | FastAPI only |

### 2.3 Endpoints

| Method | Path | Full | Player | Description |
|--------|------|------|--------|-------------|
| GET | `/` | ✓ | ✓ | Redirect to `/player.html` |
| GET | `/player.html` | ✓ | ✓ | Player page |
| GET | `/align.html` | ✓ | ✓ | Align page (disabled in player mode) |
| GET | `/style.css` | ✓ | ✓ | Styles |
| GET | `/app.js` | ✓ | ✓ | Shared JS |
| POST | `/align` | ✓ | — | Upload text+audio, run alignment, save archive |
| GET | `/api/archives` | ✓ | ✓ | List all archives (numbered, sorted) |
| GET | `/api/archive/{slug}` | ✓ | ✓ | Get sentences for an archive |
| GET | `/audio/{slug}` | ✓ | ✓ | Stream audio file |

### 2.4 Archive Storage Format

```
archives/
├── 01_fall-in-love-with-english/
│   ├── transcript.txt
│   ├── alignment.json       # Raw MMS word-level output
│   ├── sentences.json       # Sentence groups with timestamps
│   ├── meta.json            # {title, slug, num, created, word_count, sentence_count}
│   └── audio.mp3
├── 02_different-countries-...
├── ...
└── 40_when-giving-a-lecture-...
```

### 2.5 Frontend

**Align Page** — text input, audio upload, title field, "Start Alignment" button with spinner, success summary with "Open in Player" link.

**Player Page** — left sidebar (numbered titles), main transcript area (clickable sentences with play highlight), bottom audio bar. Auto-highlight follows playback.

---

## 3. Data Flow

### Alignment
```
Upload text + audio + title → POST /align
  → ctc_forced_aligner.get_word_stamps() → word-level timestamps
  → group_sentences() maps to original text sentences
  → save_archive() writes to archives/{NN}_slug/
```

### Playback
```
GET /api/archives → sidebar lists 01-40
Click "05. As the founder..." → GET /api/archive/05_as-the-founder...
  → renders sentences, sets <audio src="/audio/05_as-the-founder...">
Click sentence → audio.currentTime = sentence.start; audio.play()
```

---

## 4. Project Structure

```
eng-enhance/
├── DESIGN.md
├── DEPLOY.md
├── run.sh                    # ./run.sh [full|player]
├── deploy_vps.sh             # Deploy player-only to VPS
├── batch_align.py            # Batch align all text+mp3 pairs
├── rename_archives.py        # Add NN_ prefix to archive dirs
├── backend/
│   ├── app.py                # Full app (align + player)
│   ├── player_app.py         # Player-only app (no torch)
│   ├── aligner.py            # MMS CTC forced alignment
│   ├── archive.py            # Archive read/write (shared)
│   ├── requirements.txt      # Full deps (torch, etc.)
│   └── requirements_player.txt  # Lightweight deps
├── frontend/
│   ├── align.html
│   ├── player.html
│   ├── style.css
│   └── app.js
├── archives/                 # 01_title/ ... 40_title/
└── test/                     # Sample files
```

---

## 5. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| MMS CTC over Gentle | No Docker/Kaldi, pure Python, works on CPU |
| Dual backend apps | VPS runs player-only without 1.2 GB model |
| `NN_` prefix on slugs | Natural sort order matches source material |
| Original text for sentences | MMS strips punctuation/numbers; we preserve them |
| Filesystem as database | Zero-config, survives restarts, rsync-friendly |

---

## 6. Future

- Delete/rename archives from sidebar
- Waveform visualization (wavesurfer.js)
- Export SRT/VTT subtitles
- Search across transcripts
- More languages via MMS multilingual support
