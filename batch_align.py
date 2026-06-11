#!/usr/bin/env python3
"""
Batch alignment runner — pairs text files with mp3 files in sorted order,
sends each to the local FastAPI /align endpoint.

Usage: python3 batch_align.py

Place this in eng-enhance/ and run while the server is up on 127.0.0.1:8000.
"""

import os
import sys
import time
import requests

AUDIO_DIR = "/mnt/f/叶语凡/高中英语/背诵40篇短文记住高考3500个单词（音频）"
TEXT_DIR = os.path.join(AUDIO_DIR, "text")
API_URL = "http://127.0.0.1:8000/align"

SKIP_FIRST = True  # skip 01_Fall in Love with English (already done)


def main():
    # Gather sorted files
    mp3s = sorted(f for f in os.listdir(AUDIO_DIR) if f.endswith(".mp3"))
    txts = sorted(f for f in os.listdir(TEXT_DIR) if f.endswith(".txt"))

    if len(mp3s) != len(txts):
        print(f"ERROR: mp3 count ({len(mp3s)}) != txt count ({len(txts)})")
        sys.exit(1)

    pairs = list(zip(txts, mp3s))

    if SKIP_FIRST:
        pairs = pairs[1:]
        print(f"Skipping first pair ({txts[0]} / {mp3s[0]}).")
        print(f"Remaining: {len(pairs)} pairs.\n")

    total = len(pairs)
    for idx, (txt_name, mp3_name) in enumerate(pairs, start=1):
        # Title from text filename (strip number prefix and .txt)
        title = txt_name[3:][:-4] if txt_name[2] == "_" else txt_name[:-4]
        # Trim very long titles
        if len(title) > 80:
            title = title[:77] + "..."

        txt_path = os.path.join(TEXT_DIR, txt_name)
        mp3_path = os.path.join(AUDIO_DIR, mp3_name)

        print(f"[{idx}/{total}] {title}")
        print(f"  Text: {txt_name}  |  Audio: {mp3_name}")

        try:
            text = open(txt_path, "r", encoding="utf-8").read()
            with open(mp3_path, "rb") as af:
                files = {"audio": (mp3_name, af, "audio/mpeg")}
                data = {"text": text, "title": title}

                t0 = time.time()
                resp = requests.post(API_URL, data=data, files=files, timeout=600)
                elapsed = time.time() - t0

            if resp.status_code == 200:
                j = resp.json()
                print(f"  OK ({elapsed:.1f}s) — {j['word_count']} words, "
                      f"{j['sentence_count']} sentences, {j['duration']:.1f}s")
            else:
                print(f"  FAIL ({resp.status_code}): {resp.text[:200]}")
        except Exception as e:
            print(f"  ERROR: {e}")

        print()

    print(f"\nDone! Processed {total} pairs.")


if __name__ == "__main__":
    main()
