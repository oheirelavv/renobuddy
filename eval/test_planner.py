"""Test suite for Plan My Reno — 7 scenarios."""

from __future__ import annotations

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).parent.parent / ".env")

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.planner import generate_plan

TEST_SCENARIOS = [
    {
        "id": "P1",
        "name": "BTO bathroom renovation",
        "flat_type": "BTO (new flat)",
        "engagement": "Interior Designer (ID)",
        "works": ["Bathroom"],
    },
    {
        "id": "P2",
        "name": "Resale wall hacking",
        "flat_type": "Resale flat",
        "engagement": "Direct contractor",
        "works": ["Wall hacking"],
    },
    {
        "id": "P3",
        "name": "Multiple renovation works",
        "flat_type": "BTO (new flat)",
        "engagement": "Interior Designer (ID)",
        "works": ["Wall hacking", "Bathroom", "Electrical", "Air-conditioning"],
    },
    {
        "id": "P4",
        "name": "ID engagement — flooring + windows",
        "flat_type": "Resale flat",
        "engagement": "Interior Designer (ID)",
        "works": ["Flooring", "Windows"],
    },
    {
        "id": "P5",
        "name": "Contractor engagement — kitchen + plumbing",
        "flat_type": "Resale flat",
        "engagement": "Direct contractor",
        "works": ["Kitchen", "Plumbing"],
    },
    {
        "id": "P6",
        "name": "Unsupported work type",
        "flat_type": "BTO (new flat)",
        "engagement": "Haven't decided yet",
        "works": ["Other"],
    },
    {
        "id": "P7",
        "name": "Missing inputs (no works)",
        "flat_type": "— Select —",
        "engagement": "— Select —",
        "works": [],
    },
]


def run_tests():
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    results = []

    for s in TEST_SCENARIOS:
        print(f"\n{'='*70}")
        print(f"{s['id']}: {s['name']}")
        print(f"  Flat: {s['flat_type']} | Engagement: {s['engagement']} | Works: {s['works']}")
        print(f"{'='*70}")

        if not s["works"] or s["flat_type"] == "— Select —":
            print("\n  [SKIPPED — validation would catch missing inputs in Streamlit UI]")
            results.append({"id": s["id"], "name": s["name"], "status": "skipped_validation"})
            continue

        result = generate_plan(
            openai_client=client,
            flat_type=s["flat_type"],
            engagement=s["engagement"],
            selected_works=s["works"],
        )

        print(f"\nStatus: {result['status']}")
        print(f"Evidence: {result['evidence_by_work']}")
        if result.get("usage"):
            u = result["usage"]
            print(f"Tokens: {u['prompt_tokens']} in / {u['completion_tokens']} out / {u['total_tokens']} total")

        plan = result["plan"]
        print(f"\n--- PLAN ({len(plan)} chars) ---")
        print(plan[:2000])
        if len(plan) > 2000:
            print(f"\n... [{len(plan) - 2000} more chars]")

        # Quick quality checks
        checks = {
            "has_summary": "summary" in plan.lower() or "renovation summary" in plan.lower(),
            "has_checklist": "checklist" in plan.lower() or "☐" in plan or "- [" in plan or "checkbox" in plan.lower(),
            "has_citations": "hdb.gov.sg" in plan,
            "has_questions": "question" in plan.lower() or "ask" in plan.lower(),
            "has_sources": "source" in plan.lower() or "reference" in plan.lower(),
        }
        print(f"\nQuality checks: {checks}")

        results.append({
            "id": s["id"],
            "name": s["name"],
            "status": result["status"],
            "plan_length": len(plan),
            "evidence": result["evidence_by_work"],
            "usage": result.get("usage"),
            "checks": checks,
        })

    out_path = Path(__file__).parent / "planner_test_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    total_tokens = sum(r["usage"]["total_tokens"] for r in results if r.get("usage"))
    print(f"\n\n{'='*70}")
    print(f"SUMMARY: {len(results)} tests | Total tokens: {total_tokens:,}")
    est_cost = (sum(r["usage"]["prompt_tokens"] for r in results if r.get("usage")) / 1e6 * 0.40 +
                sum(r["usage"]["completion_tokens"] for r in results if r.get("usage")) / 1e6 * 1.60)
    print(f"Estimated cost: ${est_cost:.4f}")


if __name__ == "__main__":
    run_tests()
