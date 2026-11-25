"""Conversational RAG chatbot for HDB renovation questions.

Wraps the existing retrieval and generation pipeline with conversation
context, follow-up query rewriting, and validated suggestions.
"""

from __future__ import annotations

from openai import OpenAI

from prompts.templates import SYSTEM_PROMPT, CONTRACTOR_SUPPLEMENT
from rag.generation import _format_evidence, _filter_relevant, _is_contractor_query
from rag.retrieval import (
    query_knowledge_base,
    _query_with_embedding,
    TIER1_RELEVANCE_THRESHOLD,
)
from utils.config import LLM_MODEL, EMBEDDING_MODEL
from utils.safety import validate_input, is_out_of_scope, OUT_OF_SCOPE_RESPONSE

MAX_HISTORY_EXCHANGES = 3
FOLLOWUP_DISTANCE_THRESHOLD = 1.05

# ---------------------------------------------------------------------------
# Deterministic intent detection (no API call)
# ---------------------------------------------------------------------------

PLANNING_PATTERNS = [
    r"plan\b.*\breno", r"reno.*\bplan",
    r"checklist", r"check\s*list",
    r"\bstart\b.*\breno", r"\bstart\b.*\brenovati",
    r"\bbegin\b.*\breno", r"\bbegin\b.*\brenovati",
    r"get\s*started.*\breno", r"get\s*started.*\brenovati",
    r"how\s+(do|should|can)\s+i\s+start",
    r"where\s+(do|should|can)\s+i\s+(start|begin)",
    r"help\s+me\s+plan", r"prepare\s+before\s+renovati",
    r"what\s+should\s+i\s+prepare",
    r"just\s+got\s+my\s+bto", r"got\s+my\s+keys",
    r"what\s+do\s+i\s+need\s+to\s+do\s+first",
    r"step\s+by\s+step",
]

VERIFICATION_PATTERNS = [
    r"my\s+(contractor|id|interior\s+designer|agent)\s+(said|told|mentioned|claimed|says|tells)",
    r"(contractor|id|designer|agent)\s+told\s+me",
    r"someone\s+told\s+me",
    r"is\s+(that|this|it)\s+(true|correct|accurate|right)",
    r"(check|verify)\s+(what|this|the)\s+(my|advice|claim)",
    r"is\s+(this|the)\s+(advice|claim|information)\s+(accurate|correct|true|right)",
    r"can\s+you\s+(check|verify)",
    r"(said|told\s+me)\s+(i\s+)?(don'?t|no|not)\s+need",
    r"(said|told\s+me)\s+(i\s+)?can\s+(hack|renovate|replace|install)",
]

PLANNING_RESPONSE = (
    "It sounds like you're looking to plan your renovation. "
    "**Plan My Reno** can create a personalised checklist based on your flat type "
    "and planned works — covering permits, requirements, and key questions to ask."
)

VERIFICATION_RESPONSE = (
    "It sounds like you want to verify advice from your ID or contractor. "
    "**Verify the Advice** can check specific claims against official HDB, SCDF, "
    "and BCA sources and tell you whether they're supported, contradicted, or unverifiable."
)


def detect_intent(message: str) -> str | None:
    import re as _re
    lower = message.lower().strip()
    plan_score = sum(1 for p in PLANNING_PATTERNS if _re.search(p, lower))
    verify_score = sum(1 for p in VERIFICATION_PATTERNS if _re.search(p, lower))

    if plan_score >= 1 and plan_score > verify_score:
        return "planning"
    if verify_score >= 1 and verify_score > plan_score:
        return "verification"
    return None

REWRITE_PROMPT = """Given the conversation below and the user's latest question, rewrite the question as a standalone search query about HDB renovation in Singapore. Include enough context so the query makes sense without the conversation. If the question is already standalone, return it unchanged. Return ONLY the rewritten query, nothing else.

Conversation:
{history}

Latest question: {question}

Standalone query:"""

CHAT_USER_TEMPLATE = """RETRIEVED EVIDENCE:
{evidence}

RECENT CONVERSATION:
{history}

CURRENT QUESTION:
{question}

Answer the homeowner's question using ONLY the retrieved evidence.

FORMAT — keep answers scannable:
1. **Short answer** (1–2 sentences): directly answer the question, or state uncertainty.
2. **What you should know**: key requirements, conditions or exceptions (bullets, only if relevant).
3. **What to do next**: one practical action (only if needed).
4. **Sources**: cite official links as [Section Title](URL).

Aim for 80–150 words for straightforward questions. Use more words only when accuracy requires it. Do not repeat the same point or disclaimer. Use plain English.

After your answer, on a new line write "FOLLOW_UPS:" followed by up to 3 short follow-up questions the homeowner might ask next, one per line. Only suggest questions closely related to the evidence you just used. If you cannot suggest relevant follow-ups, write "FOLLOW_UPS:" with nothing after it."""


def _format_history(history: list[dict], max_exchanges: int = MAX_HISTORY_EXCHANGES) -> str:
    recent = history[-(max_exchanges * 2):]
    lines = []
    for msg in recent:
        role = "Homeowner" if msg["role"] == "user" else "RenoBuddy"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


def _rewrite_query(client: OpenAI, question: str, history: list[dict]) -> str:
    if not history:
        return question

    hist_text = _format_history(history, max_exchanges=2)

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "user", "content": REWRITE_PROMPT.format(
                history=hist_text, question=question,
            )},
        ],
        temperature=0,
        max_tokens=150,
    )
    rewritten = response.choices[0].message.content.strip()
    return rewritten if rewritten else question


def _parse_follow_ups(answer: str) -> tuple[str, list[str]]:
    marker = "FOLLOW_UPS:"
    if marker not in answer:
        for alt in ["You might also want to ask:", "Follow-up questions:"]:
            if alt in answer:
                marker = alt
                break
        else:
            return answer.strip(), []

    parts = answer.split(marker, 1)
    main = parts[0].strip()
    follow_up_text = parts[1].strip()

    follow_ups = []
    for line in follow_up_text.split("\n"):
        line = line.strip().lstrip("-•*0123456789. ")
        if line and len(line) > 10:
            follow_ups.append(line)

    return main, follow_ups[:3]


def _validate_follow_ups(
    client: OpenAI,
    candidates: list[str],
) -> list[str]:
    if not candidates:
        return []

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=candidates,
    )
    embeddings = [e.embedding for e in response.data]

    validated = []
    for question, emb in zip(candidates, embeddings):
        hits = _query_with_embedding(emb, question, n_results=2, where={"source_tier": 1})
        if hits and hits[0]["distance"] < FOLLOWUP_DISTANCE_THRESHOLD:
            validated.append(question)

    return validated


def chat(
    openai_client: OpenAI,
    user_message: str,
    history: list[dict],
    n_retrieve: int = 5,
) -> dict:
    is_valid, error_msg = validate_input(user_message)
    if not is_valid:
        return {
            "answer": error_msg,
            "follow_ups": [],
            "hits": [],
            "status": "rejected",
            "usage": {},
        }

    if is_out_of_scope(user_message):
        return {
            "answer": OUT_OF_SCOPE_RESPONSE,
            "follow_ups": [],
            "hits": [],
            "status": "out_of_scope",
            "usage": {},
        }

    intent = detect_intent(user_message)
    if intent == "planning":
        return {
            "answer": PLANNING_RESPONSE,
            "follow_ups": [],
            "hits": [],
            "status": "recommend_planning",
            "usage": {},
        }
    if intent == "verification":
        return {
            "answer": VERIFICATION_RESPONSE,
            "follow_ups": [],
            "hits": [],
            "status": "recommend_verification",
            "recommend_text": user_message,
            "usage": {},
        }

    retrieval_query = _rewrite_query(openai_client, user_message, history)

    hits = query_knowledge_base(openai_client, retrieval_query, n_results=n_retrieve)
    relevant_hits = _filter_relevant(hits)

    is_contractor = _is_contractor_query(user_message) or _is_contractor_query(retrieval_query)

    if len(relevant_hits) < 1 and not is_contractor:
        return {
            "answer": (
                "Based on RenoBuddy's available sources, I could not find "
                "sufficient official guidance to answer this question reliably.\n\n"
                "Please check directly with HDB at [hdb.gov.sg](https://www.hdb.gov.sg) "
                "or consult a licensed professional."
            ),
            "follow_ups": [],
            "hits": hits,
            "status": "insufficient_evidence",
            "usage": {},
        }

    evidence = _format_evidence(relevant_hits) if relevant_hits else "No relevant evidence found."
    if is_contractor:
        evidence += "\n\n---\n\n" + CONTRACTOR_SUPPLEMENT

    hist_text = _format_history(history) if history else "No prior conversation."

    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": CHAT_USER_TEMPLATE.format(
                    evidence=evidence,
                    history=hist_text,
                    question=user_message,
                ),
            },
        ],
        temperature=0.2,
        max_tokens=1000,
    )

    raw_answer = response.choices[0].message.content
    usage = response.usage
    answer, candidate_follow_ups = _parse_follow_ups(raw_answer)

    validated_follow_ups = _validate_follow_ups(openai_client, candidate_follow_ups)

    return {
        "answer": answer,
        "follow_ups": validated_follow_ups,
        "hits": relevant_hits,
        "status": "success",
        "usage": {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
        },
    }
