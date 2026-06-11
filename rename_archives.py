#!/usr/bin/env python3
"""
Rename archive directories from title-only slugs to number-prefixed slugs.
Matches each archive to its original text file (by substrings),
then prepends the serial number (01_, 02_, ...).
"""

import os
import re
import shutil

ARCHIVES_DIR = "/home/administrator/eng-enhance/archives"
TEXT_DIR = "/mnt/f/叶语凡/高中英语/背诵40篇短文记住高考3500个单词（音频）/text"


def slugify(title: str) -> str:
    """Match the slug algorithm from archive.py"""
    slug = re.sub(r"[^\w\s-]", "", title).strip().lower()
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug or "untitled"


def main():
    # Get all text files in order
    txts = sorted(f for f in os.listdir(TEXT_DIR) if f.endswith(".txt"))

    # Build mapping: slug -> (number, original_title)
    text_map = {}
    for fname in txts:
        num = fname[:2] if fname[2] == "_" else fname[:3]
        # Title from filename: strip number prefix and .txt
        if fname[2] == "_":
            title = fname[3:-4]
        else:
            title = fname[:-4]
        slug = slugify(title)
        text_map[slug] = (num, title)

    # Walk archives and rename
    renamed = 0
    for entry in sorted(os.listdir(ARCHIVES_DIR)):
        entry_path = os.path.join(ARCHIVES_DIR, entry)
        if not os.path.isdir(entry_path):
            continue
        if entry == ".gitkeep":
            continue
        if re.match(r"^\d{2,3}_", entry):
            continue  # already has number prefix

        # Find matching text file by slug
        if entry not in text_map:
            # Try fuzzy match — check if archive slug is a substring of any text slug
            found = None
            for slug_key, (num, title) in text_map.items():
                if entry in slug_key or slug_key in entry:
                    found = (num, title, slug_key)
                    break
            if not found:
                print(f"SKIP (no match): {entry}")
                continue
            num, title, slug_key = found
        else:
            num, title = text_map[entry]

        new_name = f"{num}_{slugify(title)}"
        new_path = os.path.join(ARCHIVES_DIR, new_name)

        if entry == new_name:
            continue

        if os.path.exists(new_path):
            print(f"SKIP (exists): {entry} -> {new_name}")
            continue

        shutil.move(entry_path, new_path)
        print(f"RENAMED: {entry:50s} -> {new_name}")
        renamed += 1

        # Update meta.json with the number and new slug
        meta_path = os.path.join(new_path, "meta.json")
        if os.path.exists(meta_path):
            import json
            meta = json.load(open(meta_path, "r", encoding="utf-8"))
            meta["num"] = num
            meta["slug"] = new_name
            json.dump(meta, open(meta_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"\nRenamed {renamed} archives.")


if __name__ == "__main__":
    main()
