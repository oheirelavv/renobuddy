"""RAG generation pipeline: retrieval → evidence formatting → grounded LLM answer."""

from __future__ import annotations

import re

from openai import OpenAI

from prompts.templates import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    CONTRACTOR_SUPPLEMENT,
)
from rag.retrieval import query_knowledge_base
from utils.config import LLM_MODEL
from utils.safety import (
    validate_input,
    is_out_of_scope,
    OUT_OF_SCOPE_RESPONSE,
    CONTRACTOR_DIRECTORY_URL,
)

CONTRACTOR_KEYWORDS = [
    "contractor", "registered", "hdb-registered", "directory",
    "find a contractor", "renovation company", "renovation firm",
]

MIN_RELEVANCE_CHUNKS = 1
MAX_DISTANCE_THRESHOLD = 1.3


def _is_contractor_query(question: str) -> bool:
    lower = question.lower()
    return any(kw in lower for kw in CONTRACTOR_KEYWORDS)


def _format_evidence(hits: list[dict]) -> str:
    blocks = []
    for i, hit in enumerate(hits, 1):
        m = hit["metadata"]
        tier_label = hit.get("tier_label", "Tier 2 – Third-party")
        blocks.append(
            f"[Source {i}] ({tier_label})\n"
            f"Title: {m['source_title']}\n"
            f"Section: {m['section_title']}\n"
            f"URL: {m['source_url']}\n"
            f"Content:\n{hit['text']}"
        )
    return "\n\n---\n\n".join(blocks)


def _filter_relevant(hits: list[dict]) -> list[dict]:
    return [h for h in hits if h["distance"] < MAX_DISTANCE_THRESHOLD]


def generate_answer(
    openai_client: OpenAI,
    question: str,
    n_retrieve: int = 5,
) -> dict:
    is_valid, error_msg = validate_input(question)
    if not is_valid:
        return {
            "answer": error_msg,
            "hits": [],
            "status": "rejected",
        }

    if is_out_of_scope(question):
        return {
            "answer": OUT_OF_SCOPE_RESPONSE,
            "hits": [],
            "status": "out_of_scope",
        }

    hits = query_knowledge_base(openai_client, question, n_results=n_retrieve)
    relevant_hits = _filter_relevant(hits)

    is_contractor = _is_contractor_query(question)

    if len(relevant_hits) < MIN_RELEVANCE_CHUNKS and not is_contractor:
        return {
            "answer": (
                "Based on RenoBuddy's available sources, I could not find "
                "sufficient official guidance to answer this question reliably.\n\n"
                "Please check directly with HDB at [hdb.gov.sg](https://www.hdb.gov.sg) "
                "or consult a licensed professional."
            ),
            "hits": hits,
            "status": "insufficient_evidence",
        }

    evidence = _format_evidence(relevant_hits) if relevant_hits else "No relevant evidence found."

    if is_contractor:
        evidence += "\n\n---\n\n" + CONTRACTOR_SUPPLEMENT

    user_prompt = USER_PROMPT_TEMPLATE.format(
        evidence=evidence,
        question=question,
    )

    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=1500,
    )

    answer = response.choices[0].message.content
    usage = response.usage

    return {
        "answer": answer,
        "hits": relevant_hits,
        "status": "success",
        "usage": {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
        },
    }
