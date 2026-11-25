"""Plan My Reno: per-work retrieval and structured plan generation."""

from __future__ import annotations

import json
import hashlib

from openai import OpenAI

from prompts.templates import SYSTEM_PROMPT, CONTRACTOR_SUPPLEMENT
from rag.retrieval import query_knowledge_base
from utils.config import LLM_MODEL
from utils.safety import CONTRACTOR_DIRECTORY_URL

CHECKLIST_DELIMITER = "===CHECKLIST_JSON==="

WORK_TYPE_QUERIES = {
    "Wall hacking": "wall hacking demolition permit requirements conditions HDB",
    "Flooring": "floor finishes replacement tiles permit requirements HDB",
    "Kitchen": "kitchen renovation extension sink requirements HDB",
    "Bathroom": "bathroom toilet renovation enlargement restrictions permit HDB",
    "Windows": "window replacement installation permit BCA contractor requirements HDB",
    "Electrical": "electrical works wiring power points permit requirements HDB",
    "Plumbing": "plumbing pipes water sanitary works requirements HDB",
    "Air-conditioning": "aircon air-conditioner installation compressor permit HDB",
    "Other": "HDB renovation general terms conditions permit requirements",
}


def _retrieve_per_work(
    openai_client: OpenAI,
    selected_works: list[str],
    n_per_work: int = 3,
) -> dict[str, list[dict]]:
    results = {}
    seen_ids = set()
    for work in selected_works:
        query = WORK_TYPE_QUERIES.get(work, f"{work} renovation requirements HDB")
        hits = query_knowledge_base(openai_client, query, n_results=n_per_work + 2)
        deduped = []
        for h in hits:
            if h["id"] not in seen_ids:
                seen_ids.add(h["id"])
                deduped.append(h)
            if len(deduped) >= n_per_work:
                break
        results[work] = deduped
    return results


def _format_plan_evidence(evidence_by_work: dict[str, list[dict]]) -> str:
    blocks = []
    for work, hits in evidence_by_work.items():
        blocks.append(f"## Evidence for: {work}")
        for i, hit in enumerate(hits, 1):
            m = hit["metadata"]
            tier_label = hit.get("tier_label", "Tier 2 – Third-party")
            blocks.append(
                f"[{work} Source {i}] ({tier_label})\n"
                f"Section: {m['section_title']}\n"
                f"Source: {m['source_title']}\n"
                f"URL: {m['source_url']}\n"
                f"Content:\n{hit['text']}"
            )
        blocks.append("")
    return "\n\n---\n\n".join(blocks)


PLAN_PROMPT_TEMPLATE = """HOMEOWNER PROFILE:
- Flat type: {flat_type}
- Managing renovation via: {engagement}
- Planned renovation works: {works_list}

RETRIEVED EVIDENCE (organised by renovation work):
{evidence}

Generate a personalised **RenoBuddy Renovation Plan** in TWO parts.

## PART 1 — NARRATIVE PLAN (markdown)

Write these sections:

### 1. Your Renovation Summary
Briefly recap the homeowner's flat type, engagement method, and planned works.

### 2. Important Things to Check Before Starting
Organise into subsections using #### headings. Use whichever of these apply:

#### Permits and approvals
- Actions and approvals needed before renovation begins.

#### Important restrictions
- Applicable restrictions, conditions and exceptions (e.g. 3-year BTO rules).

#### Contractor requirements
- Registration or qualification requirements to verify.

#### Before starting renovation
- Practical actions homeowners should complete.

Only include subsections with relevant content. Use citations where applicable.

### 3. Requirements for Each Renovation Work
For each selected work, use this structure:

#### [Work Name]
**Permit required?**
State clearly whether a permit or approval is needed and from which authority.

**Key conditions**
- List conditions, exceptions, dimensions, and timelines
- Note any licensed professional requirements

Use citations: [Section Name — Source Title](URL)

### 4. Official Sources
List all cited source URLs as markdown links: [Source Title — Section Name](URL)

## PART 2 — STRUCTURED CHECKLIST (JSON)

After the narrative plan, output the delimiter ===CHECKLIST_JSON=== on its own line, followed by a JSON array of checklist tasks. Each task must have:
- "category": one of "before_reno", "permits", "work_requirements", "questions"
- "task": short actionable instruction (imperative, plain English)
- "detail": one sentence of additional guidance (or null if not needed)
- "source_url": HDB URL if applicable (or null)
- "source_section": section name if applicable (or null)
- "work_type": which renovation work this relates to (or "General")
- "critical": true if this involves a permit, restriction, or safety requirement

Output 8–20 tasks covering all selected renovation works. Group by category.
Only include tasks supported by the evidence. Do not invent requirements.

RULES:
- Base every requirement on the evidence. If evidence is insufficient for a work type, say so and link to the relevant HDB page.
- Evidence is labelled by source tier. Base all regulatory requirements on Tier 1 (Official) sources only. Tier 2 (Third-party) sources may provide supplementary context (e.g. cost estimates, tips) but do not cite them as the authority for HDB/SCDF regulations. Clearly distinguish between official requirements and general renovation tips.
- Do not invent requirements. Do not assume the homeowner's BTO flat is within the 3-year restriction period — explain when the restriction applies and suggest they check their block completion date.
- Use plain English. Format the narrative for Streamlit markdown rendering.
- Do not provide legal or professional advice — recommend consulting HDB or professionals for critical decisions.
- Tailor "questions" category tasks to the engagement method: {engagement_label}."""


def _parse_response(raw: str) -> tuple[str, list[dict]]:
    if CHECKLIST_DELIMITER in raw:
        parts = raw.split(CHECKLIST_DELIMITER, 1)
        plan_text = parts[0].strip()
        json_str = parts[1].strip()
        if json_str.startswith("```"):
            json_str = json_str.split("\n", 1)[1] if "\n" in json_str else json_str[3:]
            json_str = json_str.rsplit("```", 1)[0]
        try:
            checklist = json.loads(json_str)
            for i, item in enumerate(checklist):
                stable_key = f"{item.get('category', '')}-{item.get('task', '')}"
                item["id"] = hashlib.md5(stable_key.encode()).hexdigest()[:10]
            return plan_text, checklist
        except (json.JSONDecodeError, TypeError):
            return plan_text, []
    return raw.strip(), []


def generate_plan(
    openai_client: OpenAI,
    flat_type: str,
    engagement: str,
    selected_works: list[str],
) -> dict:
    evidence_by_work = _retrieve_per_work(openai_client, selected_works)

    evidence_text = _format_plan_evidence(evidence_by_work)

    engagement_labels = {
        "Interior Designer (ID)": "Interior Designer",
        "Direct contractor": "Contractor",
        "Haven't decided yet": "ID/Contractor",
    }
    engagement_label = engagement_labels.get(engagement, "ID/Contractor")

    user_prompt = PLAN_PROMPT_TEMPLATE.format(
        flat_type=flat_type,
        engagement=engagement,
        works_list=", ".join(selected_works),
        evidence=evidence_text,
        engagement_label=engagement_label,
    )

    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=4000,
    )

    raw_answer = response.choices[0].message.content
    usage = response.usage

    plan_text, checklist = _parse_response(raw_answer)

    all_hits = []
    for hits in evidence_by_work.values():
        all_hits.extend(hits)

    return {
        "plan": plan_text,
        "checklist": checklist,
        "evidence_by_work": {w: len(h) for w, h in evidence_by_work.items()},
        "total_chunks": len(all_hits),
        "status": "success",
        "usage": {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
        },
    }
