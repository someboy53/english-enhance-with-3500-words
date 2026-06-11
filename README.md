# English Enhancement with 3500 Words

A web tool that helps English learners practice listening and reading with synchronized audio-text playback — built on **40 short passages** covering the 3,500 core vocabulary words required for the Chinese college entrance exam (Gaokao).

**Click any sentence → audio jumps and plays from that exact moment.**

![](https://img.shields.io/badge/Python-3.10+-blue) ![](https://img.shields.io/badge/FastAPI-0.110+-green) ![](https://img.shields.io/badge/MMS-1B-orange)

---

## What It Does

| Page | Purpose |
|------|---------|
| **Player** | Browse 40 numbered articles in a sidebar. Each article's transcript is rendered as clickable sentences. Click one → the audio player seeks to that sentence and plays. Current sentence highlights during playback. |
| **Align** | Upload a new text transcript + matching audio, run forced alignment (MMS model), and export it as a numbered archive. |

---

## Screenshots

```
┌──────────────────────────────────────────────────────────────┐
│  [Align]  [Player]                                          │
├──────────┬───────────────────────────────────────────────────┤
│ Archives │                                                   │
│          │  01. Fall in Love with English                    │
│ 01. ...  │  Hiding behind the loose dusty curtain, a         │
│ 02. ...  │  teenager packed up his overcoat into the         │
│ 03. ...  │  suitcase.  ◀── clickable!                        │
│ 04. ...  │                                                   │
│ 05. ★   │  He planned to leave home at dusk though           │
│  ...     │  there was thunder and lightning outdoors.        │
│          │                                                   │
│          ├───────────────────────────────────────────────────┤
│          │  ▶ ───────────────●────────────────── 00:42       │
└──────────┴───────────────────────────────────────────────────┘
```

---

## How It Works

1. **Forced alignment** via Facebook's MMS (Massively Multilingual Speech) model — given audio + transcript, it finds the timestamp of every single word.
2. Words are grouped into sentences based on the original text.
3. Each alignment is saved as an archive: `archives/01_title/` containing the original text, word-level JSON, sentence-level JSON, and the audio file.
4. The Player simply reads these archives — no ML needed.

---

## Quick Start

### Player Only (Lightweight)

```bash
git clone https://github.com/someboy53/english-enhance-with-3500-words.git
cd english-enhance-with-3500-words
./run.sh player
```

Opens at **http://127.0.0.1:8000**. No GPU, no Docker, no large model downloads.

### Full Stack (Align + Player)

```bash
./run.sh
```

First run downloads the MMS model (~1.18 GB, one-time). Requires ~4 GB RAM for alignment.

---

## Usage

### Align New Content

1. Open `http://127.0.0.1:8000/align.html`
2. Paste the transcript text
3. Upload the matching audio file (mp3/wav)
4. Give it a title
5. Click **Start Alignment** — takes ~10-15 seconds per article
6. Click **Open in Player** to verify

For batch alignment:
```bash
python3 batch_align.py
```

### Play

1. Open `http://127.0.0.1:8000` (or `/player.html`)
2. Click any article in the sidebar
3. Click any sentence to play from that point
4. The current sentence auto-highlights as the audio plays

---

## Deploy to VPS (Player Only)

```bash
./deploy_vps.sh root@your-vps-ip:/opt/eng-enhance
```

This syncs archives + code, installs minimal deps, and starts the player on port 8000. See [DEPLOY.md](DEPLOY.md) for systemd and nginx setup.

---

## Project Structure

```
eng-enhance/
├── README.md
├── DESIGN.md                 # Technical architecture
├── DEPLOY.md                 # Deployment guide
├── run.sh                    # ./run.sh [full|player]
├── deploy_vps.sh             # VPS deployment script
├── batch_align.py            # Batch alignment runner
├── rename_archives.py        # Add NN_ prefix to archives
├── backend/
│   ├── app.py                # Full app (align + player)
│   ├── player_app.py         # Player-only app (no torch)
│   ├── aligner.py            # MMS CTC forced alignment
│   ├── archive.py            # Archive read/write
│   ├── requirements.txt      # Full deps
│   └── requirements_player.txt  # Lightweight deps
├── frontend/
│   ├── align.html
│   ├── player.html
│   ├── style.css
│   └── app.js
└── archives/                 # 01_title/ ... 40_title/
```

---

## Tech Stack

- **Backend:** FastAPI (Python)
- **Alignment:** `ctc-forced-aligner` + Facebook MMS-1B model
- **Frontend:** Vanilla HTML/CSS/JS (no framework)
- **Storage:** Filesystem (no database)

---

## Credits

- The 40 passages and audio are from the widely-used Chinese Gaokao English vocabulary learning material — *"背诵40篇短文记住高考3500个单词"*.
- Forced alignment powered by [Facebook MMS](https://github.com/facebookresearch/fairseq/tree/main/examples/mms) via [ctc-forced-aligner](https://github.com/MahmoudAshraf97/ctc-forced-aligner).

---

## License

MIT

---

## Have Questions or Ideas?

If you have any questions, suggestions, or want to discuss improvements, feel free to **open an issue** on this repo. Let's make English learning better together!
