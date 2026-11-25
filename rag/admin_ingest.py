"""Admin knowledge base management — URL validation, fetch/preview, and ingestion."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import socket
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import requests
import urllib3
from bs4 import BeautifulSoup
from openai import OpenAI

from rag.chunking import chunk_source, split_section_text, stable_id, MAX_CHUNK_CHARS
from rag.embeddings import (
    get_chroma_client,
    COLLECTION_NAME,
    BATCH_SIZE,
)
from rag.ingest import html_to_text, extract_next_data, find_accordion_items
from utils.config import EMBEDDING_MODEL
from utils.source_tiers import get_tier

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REGISTRY_PATH = DATA_DIR / "source_registry.json"

BLOCKED_HOSTS = [
    "localhost", "127.0.0.1", "0.0.0.0", "::1",
    "169.254.169.254", "metadata.google.internal",
]

ALLOWED_DOMAINS = [".gov.sg", "qanvast.com"]


def _is_private_ip(hostname: str) -> bool:
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(hostname))
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except (socket.gaierror, ValueError):
        return False


def validate_url(url: str) -> tuple[bool, str]:
    if not url or not url.strip():
        return False, "URL is required."

    try:
        parsed = urlparse(url.strip())
    except Exception:
        return False, "Invalid URL format."

    if parsed.scheme != "https":
        return False, "Only HTTPS URLs are allowed."

    if not parsed.hostname:
        return False, "No hostname found in URL."

    hostname = parsed.hostname.lower()

    for blocked in BLOCKED_HOSTS:
        if blocked in hostname:
            return False, f"Blocked host: {hostname}"

    if _is_private_ip(hostname):
        return False, f"Private or internal IP address: {hostname}"

    is_known = any(hostname.endswith(d) for d in ALLOWED_DOMAINS)
    warning = "" if is_known else f" (not in known domains: {', '.join(ALLOWED_DOMAINS)})"

    return True, f"URL accepted{warning}"


def _source_id_from_url(url: str) -> str:
    parsed = urlparse(url)
    slug = re.sub(r"[^a-z0-9]+", "-", parsed.path.strip("/").lower())
    return slug[:60] or hashlib.md5(url.encode()).hexdigest()[:12]


def _detect_organisation(hostname: str) -> str:
    if "hdb.gov.sg" in hostname:
        return "Housing & Development Board (HDB)"
    if "scdf.gov.sg" in hostname:
        return "Singapore Civil Defence Force (SCDF)"
    if "bca.gov.sg" in hostname:
        return "Building and Construction Authority (BCA)"
    if "qanvast.com" in hostname:
        return "Qanvast"
    return hostname


def _build_text_preview(sections: list[dict], max_chars: int = 2000) -> str:
    parts: list[str] = []
    used = 0
    for s in sections:
        header = f"── {s['title']} ({s['text_length']:,} chars) ──"
        parts.append(header)
        used += len(header) + 1
        remaining = max_chars - used
        if remaining <= 0:
            parts.append("...")
            break
        snippet = s["body_text"][:remaining]
        if len(s["body_text"]) > remaining:
            snippet += " …"
        parts.append(snippet)
        parts.append("")
        used += len(snippet) + 1
    return "\n".join(parts).strip()


def fetch_and_preview(url: str) -> dict:
    valid, msg = validate_url(url)
    if not valid:
        return {"status": "error", "error": msg}

    try:
        r = requests.get(
            url.strip(),
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0 (compatible; RenoBuddy/1.0)"},
            verify=False,
            allow_redirects=True,
        )

        if r.url != url.strip():
            redirect_valid, redirect_msg = validate_url(r.url)
            if not redirect_valid:
                return {"status": "error", "error": f"Unsafe redirect to {r.url}: {redirect_msg}"}

        r.raise_for_status()
    except requests.RequestException as e:
        return {"status": "error", "error": f"Fetch failed: {e}"}

    html = r.text
    soup = BeautifulSoup(html, "html.parser")

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    sections: list[dict] = []
    extraction_method = "generic"

    # --- Strategy 1: Next.js __NEXT_DATA__ (HDB pages) ---
    next_data = extract_next_data(html)
    if next_data:
        items = find_accordion_items(next_data)
        if items:
            extraction_method = "nextjs_accordion"
            for item in items:
                heading = item.get("titleVal", "").strip()
                body_html = item.get("bodyContentVal", "")
                body_text = html_to_text(body_html) if body_html else ""
                if heading and body_text:
                    sections.append({
                        "title": heading,
                        "body_text": body_text,
                        "text_length": len(body_text),
                    })

    # --- Strategy 2: Generic HTML heading-based extraction ---
    if not sections:
        extraction_method = "generic"
        article = soup.find("article") or soup.find("main") or soup.find("body")
        if not article:
            return {"status": "error", "error": "Could not find page content."}

        for tag in article.find_all(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        headings = article.find_all(["h2", "h3"])
        if headings:
            for heading in headings:
                heading_text = heading.get_text(strip=True)
                if not heading_text:
                    continue
                body_parts = []
                sibling = heading.find_next_sibling()
                while sibling and sibling.name not in ["h2", "h3"]:
                    text = html_to_text(str(sibling))
                    if text:
                        body_parts.append(text)
                    sibling = sibling.find_next_sibling()
                body = "\n".join(body_parts)
                if body:
                    sections.append({
                        "title": heading_text,
                        "body_text": body,
                        "text_length": len(body),
                    })
        else:
            full_text = html_to_text(str(article))
            if full_text:
                sections.append({
                    "title": "Main Content",
                    "body_text": full_text,
                    "text_length": len(full_text),
                })

    if not sections:
        return {"status": "error", "error": "No extractable content found."}

    # --- Quality checks ---
    total_text = sum(s["text_length"] for s in sections)
    warnings: list[str] = []

    if total_text < 100:
        warnings.append(
            f"Very little content extracted ({total_text} chars). "
            "The main article content may be missing or loaded dynamically."
        )

    short_sections = sum(1 for s in sections if s["text_length"] < 50)
    if len(sections) > 2 and short_sections > len(sections) * 0.7:
        warnings.append(
            f"Most sections ({short_sections}/{len(sections)}) contain very little text. "
            "The extraction may have captured navigation elements instead of article content."
        )

    parsed = urlparse(url)
    org = _detect_organisation(parsed.hostname.lower())
    source_id = _source_id_from_url(url)

    est_chunks = sum(max(1, len(s["body_text"]) // MAX_CHUNK_CHARS + 1) for s in sections)
    est_tokens = total_text / 4
    est_cost = (est_tokens / 1_000_000) * 0.02

    existing_ids = _get_existing_source_ids()
    is_duplicate = source_id in existing_ids

    return {
        "status": "success",
        "source_id": source_id,
        "title": title,
        "url": url.strip(),
        "organisation": org,
        "sections": sections,
        "section_count": len(sections),
        "total_text_length": total_text,
        "est_chunks": est_chunks,
        "est_tokens": int(est_tokens),
        "est_cost": est_cost,
        "is_duplicate": is_duplicate,
        "text_preview": _build_text_preview(sections),
        "extraction_method": extraction_method,
        "warnings": warnings,
    }


def _get_existing_source_ids() -> set[str]:
    if not REGISTRY_PATH.exists():
        return set()
    with open(REGISTRY_PATH) as f:
        registry = json.load(f)
    return {s["source_id"] for s in registry.get("sources", [])}


def ingest_source(
    preview: dict,
    tier: int,
    openai_client: OpenAI,
) -> dict:
    source_id = preview["source_id"]

    raw_data = {
        "source_id": source_id,
        "title": preview["title"],
        "url": preview["url"],
        "organisation": preview["organisation"],
        "topics": [],
        "retrieval_date": str(date.today()),
        "status": "success",
        "sections": [
            {
                "title": s["title"],
                "description": "",
                "body_html": "",
                "body_text": s["body_text"],
                "text_length": s["text_length"],
            }
            for s in preview["sections"]
        ],
        "errors": [],
        "total_text_length": preview["total_text_length"],
        "sections_with_content": preview["section_count"],
        "total_sections": preview["section_count"],
    }

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = RAW_DIR / f"{source_id}.json"
    with open(raw_path, "w") as f:
        json.dump(raw_data, f, indent=2, ensure_ascii=False)

    chunks = chunk_source(raw_path)
    if not chunks:
        return {"status": "error", "error": "No chunks produced from extracted content."}

    for chunk in chunks:
        chunk["metadata"]["source_tier"] = tier

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    chunks_path = PROCESSED_DIR / "chunks.json"
    existing_chunks = []
    if chunks_path.exists():
        with open(chunks_path) as f:
            existing_chunks = json.load(f)

    existing_chunk_ids = {c["id"] for c in existing_chunks}
    new_chunks = [c for c in chunks if c["id"] not in existing_chunk_ids]
    all_chunks = existing_chunks + new_chunks

    with open(chunks_path, "w") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    chroma = get_chroma_client()
    collection = chroma.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "HDB renovation guidelines"},
    )

    chroma_existing = set(collection.get()["ids"])
    to_embed = [c for c in new_chunks if c["id"] not in chroma_existing]

    if to_embed:
        for i in range(0, len(to_embed), BATCH_SIZE):
            batch = to_embed[i: i + BATCH_SIZE]
            texts = [c["text"] for c in batch]

            response = openai_client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=texts,
            )

            embeddings = [e.embedding for e in response.data]

            collection.add(
                ids=[c["id"] for c in batch],
                embeddings=embeddings,
                documents=texts,
                metadatas=[c["metadata"] for c in batch],
            )

    _update_registry(raw_data, tier)

    return {
        "status": "success",
        "source_id": source_id,
        "chunks_added": len(to_embed),
        "total_chunks": collection.count(),
    }


def _update_registry(raw_data: dict, tier: int):
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH) as f:
            registry = json.load(f)
    else:
        registry = {"generated": str(date.today()), "sources": []}

    registry["sources"] = [
        s for s in registry["sources"] if s["source_id"] != raw_data["source_id"]
    ]

    registry["sources"].append({
        "source_id": raw_data["source_id"],
        "title": raw_data["title"],
        "url": raw_data["url"],
        "organisation": raw_data["organisation"],
        "topics": raw_data.get("topics", []),
        "retrieval_date": raw_data["retrieval_date"],
        "status": raw_data["status"],
        "total_sections": raw_data.get("total_sections", 0),
        "sections_with_content": raw_data.get("sections_with_content", 0),
        "total_text_length": raw_data.get("total_text_length", 0),
        "source_tier": tier,
        "errors": raw_data.get("errors", []),
    })

    registry["generated"] = str(date.today())

    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
