"""Retrieval module for querying the ChromaDB vector store."""

from __future__ import annotations

import re

from openai import OpenAI

from rag.embeddings import get_chroma_client, COLLECTION_NAME
from utils.config import EMBEDDING_MODEL
from utils.source_tiers import get_tier_label

SECTION_BOOST = 0.15
TIER2_PENALTY = 0.08
TIER1_RELEVANCE_THRESHOLD = 1.1
TIER1_GAP_THRESHOLD = 0.5

KEYWORD_TO_SECTIONS = {
    "hack": ["Walls", "Making Changes to Structural Walls"],
    "hacking": ["Walls", "Making Changes to Structural Walls"],
    "demolish": ["Walls", "Making Changes to Structural Walls"],
    "demolition": ["Walls", "Making Changes to Structural Walls"],
    "knock down": ["Walls", "Making Changes to Structural Walls"],
    "wall": ["Walls", "Wall finishes", "Making Changes to Structural Walls"],
    "bathroom": ["Bathroom and toilet", "Altering the Bathroom's Original Layout",
                  "What You Can Do – Shift the Sink Out of the Toilet",
                  "What You Can Do – Install a Bathtub",
                  "What You Cannot Do – Shift the Wet Area"],
    "toilet": ["Bathroom and toilet", "Toilet pan", "Altering the Bathroom's Original Layout",
               "What You Can Do – Shift the Sink Out of the Toilet",
               "What You Can Do – Merge Two Toilets Into One",
               "What You Cannot Do – Shift the Wet Area",
               "What You Cannot Do – Hack BTO Toilet Tiles Within 3 Years"],
    "window": ["Windows and grilles", "Installation or replacement of new aluminium windows",
                "Replacement of full height windows (including 3/4 height and bay windows)"],
    "floor": ["Floor finishes", "Raising Floor Level Past 50mm"],
    "tile": ["Floor finishes", "Wall finishes", "Raising Floor Level Past 50mm",
             "Removing BTO Bathroom Tiles Within First 3 Years",
             "What You Cannot Do – Hack BTO Toilet Tiles Within 3 Years"],
    "ceiling": ["False ceiling", "Can You Install a Faux Skylight in an HDB Flat"],
    "kitchen": ["Kitchen", "Sinks and wash basins"],
    "aircon": ["General conditions for air-conditioner installations"],
    "air-con": ["General conditions for air-conditioner installations"],
    "air conditioner": ["General conditions for air-conditioner installations"],
    "electrical": ["Electrical works that require a permit",
                    "Electrical works that do not require a permit", "Terms and conditions"],
    "wiring": ["Electrical works that require a permit",
               "Electrical works that do not require a permit"],
    "plumbing": ["Pipes", "Technical terms and conditions",
                  "What You Can Do – Conceal Pipes",
                  "Concealing Pipes Without Access Openings"],
    "pipe": ["Pipes", "What You Can Do – Conceal Pipes",
             "Concealing Pipes Without Access Openings"],
    "door": ["Door and gate"],
    "gate": ["Door and gate"],
    "shelter": ["Household shelters (HS)",
                "Permitted Works to Household Shelter",
                "Not Permitted Works to Household Shelter",
                "General – Household Shelter Purpose",
                "Works That Cannot Be Carried Out on Household Shelter",
                "Works You Can Carry Out on Household Shelter",
                "Making Changes to Your Household Shelter"],
    "awning": ["Awning"],
    "skylight": ["Can You Install a Faux Skylight in an HDB Flat",
                  "What is a Faux Skylight", "Faux Skylight Cost Breakdown",
                  "Key Considerations Before Faux Skylight Installation"],
    "platform": ["Building Platform Storage in HDB"],
    "jacuzzi": ["What You Cannot Do – Custom-Build Jacuzzis or Hot Tubs"],
    "bathtub": ["What You Can Do – Install a Bathtub",
                "What You Cannot Do – Custom-Build Jacuzzis or Hot Tubs"],
    "bto": ["Removing BTO Bathroom Tiles Within First 3 Years",
            "What You Cannot Do – Hack BTO Toilet Tiles Within 3 Years"],
    "illegal": ["Building Platform Storage in HDB", "Making Changes to Structural Walls",
                "Raising Floor Level Past 50mm",
                "Installing Fixtures or Floor Finishes Outside Your Entrance"],
    "sink": ["Sinks and wash basins", "What You Can Do – Shift the Sink Out of the Toilet"],
    "corridor": ["Installing Fixtures or Floor Finishes Outside Your Entrance"],
    "mezzanine": ["Extending Floor Area by Covering Void Areas"],
    "void": ["Extending Floor Area by Covering Void Areas"],
    "ventilation": ["Permitted Works to Household Shelter",
                     "Not Permitted Works to Household Shelter"],
    "drill": ["Permitted Works to Household Shelter",
              "Not Permitted Works to Household Shelter",
              "Works That Cannot Be Carried Out on Household Shelter"],
}


def _compute_boost(query: str, section_title: str) -> float:
    lower_q = query.lower()
    boost = 0.0
    for keyword, boosted_sections in KEYWORD_TO_SECTIONS.items():
        if keyword in lower_q and section_title in boosted_sections:
            boost += SECTION_BOOST
    return min(boost, 0.4)


def embed_query(openai_client: OpenAI, query: str) -> list[float]:
    return openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[query],
    ).data[0].embedding


def _query_with_embedding(
    embedding: list[float],
    query: str,
    n_results: int = 5,
    where: dict | None = None,
) -> list[dict]:
    chroma = get_chroma_client()
    collection = chroma.get_collection(name=COLLECTION_NAME)

    query_kwargs = {
        "query_embeddings": [embedding],
        "n_results": min(n_results + 5, 20),
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        query_kwargs["where"] = where

    results = collection.query(**query_kwargs)

    hits = []
    for i in range(len(results["ids"][0])):
        distance = results["distances"][0][i]
        metadata = results["metadatas"][0][i]
        section_title = metadata.get("section_title", "")
        source_tier = metadata.get("source_tier", 2)
        boost = _compute_boost(query, section_title)
        tier_penalty = TIER2_PENALTY if source_tier == 2 else 0.0
        hits.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": metadata,
            "distance": distance,
            "boosted_distance": distance - boost + tier_penalty,
            "source_tier": source_tier,
            "tier_label": get_tier_label(metadata.get("organisation", "")),
        })

    hits.sort(key=lambda h: h["boosted_distance"])
    return hits[:n_results]


def query_knowledge_base(
    openai_client: OpenAI,
    query: str,
    n_results: int = 5,
) -> list[dict]:
    embedding = embed_query(openai_client, query)
    return _query_with_embedding(embedding, query, n_results)


def format_results(query: str, hits: list[dict]) -> str:
    lines = [f"Query: {query}", f"Results: {len(hits)} chunks", ""]

    for i, hit in enumerate(hits, 1):
        m = hit["metadata"]
        lines.append(f"--- Result {i} (distance: {hit['distance']:.4f}) ---")
        lines.append(f"Source: {m['source_title']}")
        lines.append(f"Section: {m['section_title']}")
        lines.append(f"URL: {m['source_url']}")
        lines.append(f"Text ({len(hit['text'])} chars):")
        lines.append(hit["text"][:600])
        if len(hit["text"]) > 600:
            lines.append(f"... [{len(hit['text']) - 600} more chars]")
        lines.append("")

    return "\n".join(lines)


TEST_QUERIES = [
    "Can I hack a wall in my HDB flat?",
    "Can I renovate my BTO bathroom immediately?",
    "Do I need approval to replace my windows?",
    "Can I install additional electrical sockets?",
    "Can I relocate my aircon compressor?",
    "Can I change the plumbing in my kitchen?",
    "How do I check if my contractor is HDB-registered?",
    "Can I hack a load-bearing wall?",
]


if __name__ == "__main__":
    import os
    from pathlib import Path
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    print("=" * 70)
    print("RETRIEVAL TEST — 8 representative queries")
    print("=" * 70)

    for idx, query in enumerate(TEST_QUERIES, 1):
        hits = query_knowledge_base(client, query, n_results=5)
        print(f"\n{'='*70}")
        print(f"Q{idx}: {query}")
        print(f"{'='*70}")
        for i, hit in enumerate(hits, 1):
            m = hit["metadata"]
            print(f"\n  [{i}] distance={hit['distance']:.4f}  |  {m['section_title']}  |  {m['source_title']}")
            print(f"      URL: {m['source_url']}")
            text_preview = hit["text"].replace("\n", " ")[:250]
            print(f"      Text: {text_preview}...")
        print()
