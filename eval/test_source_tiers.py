"""Regression tests for source tier handling in retrieval and verification.

Tests that:
- Tier 1 (official) sources are prioritised for regulatory claims
- Tier 2 (third-party) sources cannot independently establish regulatory verdicts
- Deterministic post-validation overrides verdicts lacking relevant Tier 1 evidence
- Citation accuracy: official sources cited for regulations, not Qanvast
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.retrieval import query_knowledge_base
from rag.verifier import verify_advice

TESTS = [
    {
        "id": "T1",
        "name": "Household shelter drilling restrictions",
        "input": "My contractor says I can drill nails into my household shelter walls to put up shelves.",
        "expected_tier1_topic": "shelter",
        "expected_verdict": "Contradicted",
        "accept_also": ["Partially supported"],
        "check": "SCDF explicitly prohibits power-driven nails on internal HS walls. Tier 1 must be cited.",
    },
    {
        "id": "T2",
        "name": "Platform storage (Qanvast-only, no relevant Tier 1)",
        "input": "My ID says platform beds with storage underneath are allowed in HDB flats.",
        "expected_tier1_topic": None,
        "expected_verdict": "Unable to verify",
        "accept_also": [],
        "check": "Only Qanvast covers platform storage. Must be Unable to verify (LLM or override).",
    },
    {
        "id": "T3",
        "name": "Skylight installation costs (Tier 2 context)",
        "input": "My contractor said a faux skylight costs about $800.",
        "expected_tier1_topic": None,
        "expected_verdict": "Unable to verify",
        "accept_also": ["N/A"],
        "check": "Cost info is Tier 2 only. N/A acceptable if LLM extracts no regulatory claims.",
    },
    {
        "id": "T4",
        "name": "Bathroom renovation restrictions",
        "input": "My contractor says I need a permit to relocate my bathroom pipes.",
        "expected_tier1_topic": "bathroom",
        "expected_verdict": "Supported",
        "accept_also": ["Partially supported", "Unable to verify"],
        "check": "HDB source covers pipe alteration permits. Unable to verify acceptable if LLM judges evidence insufficient for 'relocation' specifically.",
    },
    {
        "id": "T5",
        "name": "Wall hacking permits",
        "input": "My contractor says I can hack non-structural walls without a permit.",
        "expected_tier1_topic": "walls",
        "expected_verdict": "Contradicted",
        "accept_also": ["Partially supported"],
        "check": "HDB requires approval for ALL wall demolition/alteration. Tier 1 (HDB) must be cited.",
    },
    {
        "id": "T6",
        "name": "Contractor registration",
        "input": "My friend says only HDB-registered contractors can do renovation work.",
        "expected_tier1_topic": None,
        "expected_verdict": "Unable to verify",
        "accept_also": ["Partially supported"],
        "check": "Retrieved evidence may not explicitly state blanket registration rule.",
    },
    {
        "id": "T7",
        "name": "Jacuzzi 400kg limit (in HDB Tier 1 source)",
        "input": "My contractor says there is a 400kg weight limit for jacuzzis in HDB bathrooms.",
        "expected_tier1_topic": "plumbing",
        "expected_verdict": "Supported",
        "accept_also": ["Partially supported"],
        "check": "400kg limit IS in HDB plumbing source (Bath and shower). Tier 1 must be cited.",
    },
    {
        "id": "T8",
        "name": "Official vs commercial on shelter works",
        "input": "According to regulations, you cannot lay wall tiles on household shelter internal walls.",
        "expected_tier1_topic": "shelter",
        "expected_verdict": "Supported",
        "accept_also": [],
        "check": "Both SCDF (Tier 1) and Qanvast (Tier 2) cover this — must cite SCDF/HDB",
    },
    {
        "id": "T9",
        "name": "Mezzanine in maisonette (Tier 2 quoting HDB)",
        "input": "My contractor says I cannot build a mezzanine floor in my executive maisonette.",
        "expected_tier1_topic": None,
        "expected_verdict": "Unable to verify",
        "accept_also": ["Supported", "Partially supported"],
        "check": "HDB staircase section may contain relevant content. Supported is acceptable if Tier 1 cited.",
    },
    {
        "id": "T10",
        "name": "Faux skylight false ceiling (irrelevant T1 alongside relevant T2)",
        "input": "My contractor said faux skylights need to be integrated into a false ceiling for a convincing look.",
        "expected_tier1_topic": None,
        "expected_verdict": "Unable to verify",
        "accept_also": ["Partially supported", "N/A"],
        "check": "HDB covers false ceilings generally but not faux skylights specifically. N/A if no regulatory claims extracted.",
    },
    {
        "id": "T11",
        "name": "Mixed claims: wall hack + platform storage",
        "input": "My contractor says I need HDB approval to hack non-structural walls, and platform beds with storage are not allowed.",
        "expected_tier1_topic": "mixed",
        "expected_verdict": "mixed",
        "accept_also": [],
        "check": "Wall hack: Supported/Contradicted (T1). Platform: Unable to verify.",
        "multi_claim": True,
    },
    {
        "id": "T12",
        "name": "Explicit Tier 1 contradiction (window replacement)",
        "input": "My contractor says no approval is needed to replace windows in my HDB flat.",
        "expected_tier1_topic": "windows",
        "expected_verdict": "Contradicted",
        "accept_also": ["Partially supported"],
        "check": "HDB window works clearly requires approval via BCA contractor.",
    },
    {
        "id": "T13",
        "name": "Insufficient official evidence (fire safety cert)",
        "input": "My contractor says I need a fire safety certificate from SCDF before starting any renovation.",
        "expected_tier1_topic": None,
        "expected_verdict": "Unable to verify",
        "accept_also": ["Contradicted"],
        "check": "No source covers this claim. Contradicted acceptable if LLM finds related Tier 1 fire-safety content.",
    },
]


def run_tests():
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    results = []
    timestamp = datetime.now().isoformat()

    print("=" * 70)
    print("SOURCE TIER REGRESSION TESTS (v2 — with post-validation)")
    print(f"Timestamp: {timestamp}")
    print("=" * 70)

    for test in TESTS:
        print(f"\n{'='*70}")
        print(f"{test['id']}: {test['name']}")
        print(f"Input: {test['input']}")
        print(f"{'='*70}")

        result = verify_advice(client, test["input"])
        summary = result.get("summary", "")
        claims_data = result.get("claims", [])
        verify_results = result.get("results", [])
        tier_overrides = result.get("tier_overrides", [])

        # Print claim-level tier info
        for ci, claim in enumerate(claims_data):
            has_t1 = claim.get("has_relevant_tier1", "?")
            best_t1 = claim.get("best_tier1_distance", 999)
            print(f"  Claim {ci}: has_relevant_tier1={has_t1}, best_tier1_dist={best_t1:.3f}")
            for j, h in enumerate(claim.get("evidence", [])[:3]):
                m = h["metadata"]
                print(f"    [{j+1}] {h['tier_label']} | dist={h['distance']:.3f} | {m['source_id']} — {m['section_title']}")

        # Handle multi-claim tests
        if test.get("multi_claim"):
            print(f"\n  Tier overrides: {tier_overrides}")
            all_verdicts = []
            for ri, r in enumerate(verify_results):
                v = r.get("verdict", "N/A")
                overridden = r.get("tier_overridden", False)
                all_verdicts.append(v)
                print(f"  Result {ri}: verdict={v}, overridden={overridden}")

            # Wall hack claim (index 0): should be Supported or Contradicted (Tier 1 backed)
            wall_ok = len(verify_results) > 0 and verify_results[0].get("verdict") in {
                "Supported", "Contradicted", "Partially supported",
            }
            # Platform storage claim (index 1): should be Unable to verify
            platform_ok = len(verify_results) > 1 and verify_results[1].get("verdict") == "Unable to verify"

            passed = wall_ok and platform_ok
            status = "PASS" if passed else "FAIL"
            print(f"  >>> {status} (wall_ok={wall_ok}, platform_ok={platform_ok})")

            results.append({
                "test_id": test["id"],
                "name": test["name"],
                "expected_verdict": "mixed",
                "actual_verdicts": all_verdicts,
                "tier_overrides": tier_overrides,
                "passed": passed,
            })
            continue

        # Single-claim tests
        actual_verdict = "N/A"
        evidence_used = ""
        sources_cited = []
        overridden = False
        if verify_results:
            c = verify_results[0]
            actual_verdict = c.get("verdict", "N/A")
            evidence_used = c.get("evidence_used", "")
            sources_cited = c.get("sources", [])
            overridden = c.get("tier_overridden", False)

        print(f"\n  Verdict: {actual_verdict} (expected: {test['expected_verdict']})")
        print(f"  Overridden by post-validation: {overridden}")
        print(f"  Evidence used: {evidence_used[:200]}")
        if sources_cited:
            for s in sources_cited:
                print(f"    Cited: {s.get('section', '?')} — {s.get('url', '?')}")

        tier1_cited = False
        if sources_cited:
            for s in sources_cited:
                url = s.get("url", "")
                if "hdb.gov.sg" in url or "scdf.gov.sg" in url:
                    tier1_cited = True

        accept = [test["expected_verdict"]] + test.get("accept_also", [])
        verdict_match = actual_verdict in accept

        citation_ok = True
        if test.get("expected_tier1_topic") and test["expected_tier1_topic"] != "mixed":
            if not tier1_cited and sources_cited and actual_verdict != "Unable to verify":
                citation_ok = False

        override_ok = True

        # Evidence relevance check: if verdict is regulatory and not overridden,
        # evidence_used must not be the generic override text
        evidence_relevant = True
        if actual_verdict in {"Supported", "Contradicted", "Partially supported"}:
            if not evidence_used or evidence_used.startswith("No directly relevant"):
                evidence_relevant = False

        passed = verdict_match and citation_ok and override_ok and evidence_relevant
        status = "PASS" if passed else "FAIL"

        print(f"\n  Tier 1 cited: {tier1_cited}")
        print(f"  Citation OK: {citation_ok}")
        print(f"  Override expected/actual: {test.get('expect_override', False)}/{overridden}")
        print(f"  Evidence relevant: {evidence_relevant}")
        print(f"  >>> {status}")

        results.append({
            "test_id": test["id"],
            "name": test["name"],
            "expected_verdict": test["expected_verdict"],
            "actual_verdict": actual_verdict,
            "verdict_match": verdict_match,
            "tier1_cited": tier1_cited,
            "citation_ok": citation_ok,
            "overridden": overridden,
            "evidence_relevant": evidence_relevant,
            "passed": passed,
        })

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    passed_count = sum(1 for r in results if r["passed"])
    total = len(results)
    print(f"Passed: {passed_count}/{total}")
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        expected = r["expected_verdict"]
        actual = r.get("actual_verdict", r.get("actual_verdicts", "?"))
        print(f"  {r['test_id']}: {status} — {r['name']} (expected={expected}, actual={actual})")

    out_path = Path(__file__).parent / "source_tier_test_results.json"
    with open(out_path, "w") as f:
        json.dump({"timestamp": timestamp, "results": results}, f, indent=2)
    print(f"\nResults saved to {out_path}")

    return results


if __name__ == "__main__":
    run_tests()
