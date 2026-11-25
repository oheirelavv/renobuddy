"""Generate embeddings and populate ChromaDB.

Uses OpenAI text-embedding-3-small. Supports incremental updates
by checking chunk IDs before re-embedding.
"""

from __future__ import annotations

import json
from pathlib import Path

import chromadb
from openai import OpenAI

from utils.config import EMBEDDING_MODEL

DATA_DIR = Path(__file__).parent.parent / "data"
PROCESSED_DIR = DATA_DIR / "processed"
CHROMA_DIR = DATA_DIR / "chroma_db"
COLLECTION_NAME = "hdb_renovation"
BATCH_SIZE = 50


def get_chroma_client() -> chromadb.PersistentClient:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def load_chunks() -> list[dict]:
    chunks_path = PROCESSED_DIR / "chunks.json"
    with open(chunks_path) as f:
        return json.load(f)


def embed_and_store(openai_client: OpenAI, dry_run: bool = False):
    chunks = load_chunks()
    chroma = get_chroma_client()
    collection = chroma.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "HDB renovation guidelines"},
    )

    existing_ids = set(collection.get()["ids"])
    new_chunks = [c for c in chunks if c["id"] not in existing_ids]

    if not new_chunks:
        print("All chunks already embedded. Nothing to do.")
        return

    print(f"Existing: {len(existing_ids)} | New: {len(new_chunks)} | Total: {len(chunks)}")

    if dry_run:
        total_chars = sum(len(c["text"]) for c in new_chunks)
        est_tokens = total_chars / 4
        cost = (est_tokens / 1_000_000) * 0.02
        print(f"\n[DRY RUN] Would embed {len(new_chunks)} chunks")
        print(f"  Characters: {total_chars:,}")
        print(f"  Est. tokens: {est_tokens:,.0f}")
        print(f"  Est. cost: ${cost:.4f}")
        return

    for i in range(0, len(new_chunks), BATCH_SIZE):
        batch = new_chunks[i : i + BATCH_SIZE]
        texts = [c["text"] for c in batch]

        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts,
        )

        embeddings = [e.embedding for e in response.data]
        ids = [c["id"] for c in batch]
        documents = texts
        metadatas = [c["metadata"] for c in batch]

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        print(f"  Embedded batch {i // BATCH_SIZE + 1}: {len(batch)} chunks")

    print(f"\nDone. Collection now has {collection.count()} chunks.")


if __name__ == "__main__":
    import sys

    dry_run = "--dry-run" in sys.argv

    if dry_run:
        embed_and_store(openai_client=None, dry_run=True)
    else:
        import os
        from pathlib import Path
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent.parent / ".env")
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        embed_and_store(client, dry_run=False)
