"""
Forced alignment using Facebook MMS via ctc_forced_aligner / torchaudio.
No Docker, no Kaldi — pure Python.
"""

import re
import tempfile
from pathlib import Path


def run_alignment(audio_path: str | Path, text: str) -> dict:
    """
    Run forced alignment on audio + transcript.
    Returns a dict with word-level timestamps.
    """
    audio_path = Path(audio_path)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(text)
        transcript_path = f.name

    try:
        from ctc_forced_aligner import get_word_stamps

        word_stamps, model, _ = get_word_stamps(
            str(audio_path),
            transcript_path,
            model_type="MMS_FA",
        )

        words = []
        for entry in word_stamps:
            word_text = entry.get("text", "")
            if not word_text:
                continue
            start = entry.get("start", 0.0)
            end = entry.get("end", 0.0)
            score = entry.get("score", 1.0)

            if end - start < 0.01:
                continue

            words.append({
                "alignedWord": str(word_text),
                "start": float(start),
                "end": float(end),
                "score": float(score) if score is not None else 1.0,
                "case": "success",
            })

        return {
            "transcript": text,
            "words": words,
        }

    finally:
        Path(transcript_path).unlink(missing_ok=True)


def group_sentences(words: list[dict], original_text: str = "") -> list[dict]:
    """
    Group word-level output into sentences.

    Uses the original text to determine sentence boundaries (preserving
    original casing and punctuation), then maps aligned word timestamps
    onto those boundaries. Falls back to gap-based chunking on mismatch.
    """
    text_sentences = _split_text_into_sentences(original_text)

    if not text_sentences:
        return _group_by_gaps(words)

    # Map aligned words sequentially onto text sentences
    return _map_alignments_to_sentences(words, text_sentences)


def _split_text_into_sentences(text: str) -> list[str]:
    """Split text by sentence-ending punctuation, preserving content."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _tokenize_words(sentence: str) -> list[str]:
    """Extract lowercase word tokens from a sentence."""
    return [t.lower() for t in re.findall(r"[a-zA-Z0-9']+", sentence)]


def _map_alignments_to_sentences(
    words: list[dict], text_sentences: list[str]
) -> list[dict]:
    """
    Walk through aligned words and original sentences in parallel.
    For each text sentence, consume aligned words until the cumulative
    word count matches, then record the sentence span using the first
    word's start and last word's end.
    """
    text_word_counts = [len(_tokenize_words(s)) for s in text_sentences]
    total_text_words = sum(text_word_counts)

    if total_text_words == 0:
        return _group_by_gaps(words)

    sentences = []
    wi = 0  # index into aligned words

    for sent_idx, expected_count in enumerate(text_word_counts):
        if wi >= len(words) or expected_count == 0:
            continue

        start = words[wi]["start"]
        end = start

        # Consume words for this sentence (best-effort matching)
        consumed = 0
        while wi < len(words) and consumed < expected_count:
            end = words[wi]["end"]
            consumed += 1
            wi += 1

        # If the next text has more words than aligned, skip alignment gap
        # (e.g., digits like "60" stripped by MMS tokenizer)
        # If aligned has more words than text, just consume them

        if consumed > 0:
            text = text_sentences[sent_idx]
            sentences.append({
                "text": text,
                "start": start,
                "end": end,
            })

    return sentences


def _group_by_gaps(words: list[dict]) -> list[dict]:
    """Fallback: group words into sentence-like chunks using time gaps."""
    sentences = []
    current_words = []
    current_start = None

    for w in words:
        if w.get("case") != "success":
            continue
        word_text = w.get("alignedWord", "")
        start = w.get("start")
        end = w.get("end")
        if start is None or end is None:
            continue

        if current_start is None:
            current_start = start

        if current_words and (start - current_words[-1]["end"] > 0.5 or len(current_words) >= 30):
            sentences.append(_build_sentence(current_words, current_start))
            current_words = []
            current_start = start

        current_words.append({"text": word_text, "start": start, "end": end})

    if current_words:
        sentences.append(_build_sentence(current_words, current_start))

    return sentences


def _build_sentence(words: list[dict], start: float) -> dict:
    text = " ".join(w["text"] for w in words)
    text = re.sub(r"\s+([.!?,;:])", r"\1", text)
    end = words[-1]["end"]
    return {"text": text, "start": start, "end": end}
