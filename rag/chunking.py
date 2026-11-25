"""Chunk extracted HDB guidelines into retrieval-friendly segments.

Splits by accordion section first, then by logical sub-sections within
longer sections. Keeps requirements together with their conditions.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from utils.source_tiers import get_tier

DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

MAX_CHUNK_CHARS = 1500
OVERLAP_CHARS = 200


def stable_id(source_id: str, section_title: str, chunk_index: int) -> str:
    raw = f"{source_id}::{section_title}::{chunk_index}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def split_section_text(text: str) -> list[str]:
    if len(text) <= MAX_CHUNK_CHARS:
        return [text]

    # Split on table rows (lines with " | ") keeping header with each chunk
    lines = text.split("\n")
    header_line = None
    if lines and " | " in lines[0]:
        header_line = lines[0]

    chunks = []
    current = []
    current_len = 0

    for line in lines:
        line_len = len(line) + 1
        if current_len + line_len > MAX_CHUNK_CHARS and current:
            chunks.append("\n".join(current))
            # Start new chunk with overlap: keep header + last few lines
            overlap_lines = []
            if header_line and current[0] != header_line:
                overlap_lines.append(header_line)
            overlap_len = sum(len(l) + 1 for l in overlap_lines)
            for prev_line in reversed(current):
                if overlap_len + len(prev_line) + 1 > OVERLAP_CHARS:
                    break
                overlap_lines.append(prev_line)
                overlap_len += len(prev_line) + 1
            overlap_lines.reverse()
            current = overlap_lines
            current_len = overlap_len

        current.append(line)
        current_len += line_len

    if current:
        chunks.append("\n".join(current))

    return chunks


def chunk_source(source_path: Path) -> list[dict]:
    with open(source_path) as f:
        data = json.load(f)

    if data.get("status") not in ("success",):
        return []

    source_id = data["source_id"]
    chunks = []

    for section in data["sections"]:
        body = section.get("body_text", "").strip()
        if not body:
            continue

        section_title = section["title"]
        text_parts = split_section_text(body)

        for idx, text in enumerate(text_parts):
            chunk_id = stable_id(source_id, section_title, idx)
            chunk = {
                "id": chunk_id,
                "text": text,
                "metadata": {
                    "source_id": source_id,
                    "source_title": data["title"],
                    "source_url": data["url"],
                    "organisation": data["organisation"],
                    "source_tier": get_tier(data["organisation"]),
                    "section_title": section_title,
                    "section_description": section.get("description", ""),
                    "retrieval_date": data["retrieval_date"],
                    "chunk_index": idx,
                    "total_chunks_in_section": len(text_parts),
                },
            }
            chunks.append(chunk)

    return chunks


def chunk_all() -> list[dict]:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    all_chunks = []

    for raw_file in sorted(RAW_DIR.glob("*.json")):
        chunks = chunk_source(raw_file)
        if chunks:
            print(f"{raw_file.stem}: {len(chunks)} chunks")
            all_chunks.extend(chunks)

    # Save processed chunks
    out_path = PROCESSED_DIR / "chunks.json"
    with open(out_path, "w") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print(f"\nTotal: {len(all_chunks)} chunks saved to {out_path}")
    return all_chunks


if __name__ == "__main__":
    chunks = chunk_all()

    # Estimate embedding cost
    total_chars = sum(len(c["text"]) for c in chunks)
    est_tokens = total_chars / 4  # rough estimate: 1 token ~ 4 chars
    cost = (est_tokens / 1_000_000) * 0.02  # text-embedding-3-small pricing

    print(f"\n--- Embedding Cost Estimate ---")
    print(f"Total chunks: {len(chunks)}")
    print(f"Total characters: {total_chars:,}")
    print(f"Estimated tokens: {est_tokens:,.0f}")
    print(f"Estimated cost: ${cost:.4f} (text-embedding-3-small @ $0.02/1M tokens)")
