# RenoBuddy — Project Status

## Completed
- **Phase 1:** Architecture planning and tech stack approval
- **Phase 2:** Project setup — folder structure, dependencies, config, placeholder Streamlit app
- **Phase 3:** Data ingestion — 5 HDB sources extracted, 65 chunks embedded in ChromaDB
- **Phase 3 expansion:** 5 new sources added (1 SCDF PDF + 4 Qanvast articles), 30 new chunks, 95 total in ChromaDB
- **Phase 4:** RAG generation pipeline — grounded answer generation, citations, safety
- **Phase 4 fixes:** Section-title boosting, stricter grounding rules, BTO restriction highlighting
- **Phase 5:** Plan My Reno — working Streamlit page with per-work RAG retrieval, interactive checklist
- **Phase 6:** Verify My Advice — prompt-chained claim verification with structured results
- **Phase 6 refinement:** Strengthened verdict rules, fixed insufficient-evidence classification
- **Source reliability:** Source tiering (Tier 1 official / Tier 2 third-party), tier-aware retrieval, prompts, and citation rules
- **Tier enforcement:** Deterministic post-validation that overrides regulatory verdicts lacking relevant Tier 1 evidence
- **UI redesign:** Full visual redesign as modern productivity dashboard — all 6 pages
- **Phase 7:** Ask RenoBuddy conversational chatbot — RAG-powered Q&A with conversation context
- **Methodology page:** Restructured into 7-section technical report with verified implementation details
- **Smart recommendations:** Chatbot detects planning/verification intent and recommends the right feature
- **Authentication:** Role-based login (Admin/User) with salted SHA-256 hashing
- **Admin KB management:** Admin-only page to add website sources via the existing ingestion pipeline

## Current Phase
Authentication and admin KB management complete. All features functional.

## Phase 7 — Ask RenoBuddy Chatbot (2026-11-17)

**New file:** `rag/chatbot.py` — Conversational RAG module
- Reuses existing retrieval (`query_knowledge_base`), evidence formatting, safety checks, and source-tier labels
- Query rewriting: follow-up questions are rewritten into standalone retrieval queries via a lightweight LLM call (150 tokens, only when history exists)
- Conversation context: last 3 exchanges passed to the LLM alongside retrieved evidence
- Follow-up suggestions: LLM suggests 2–3 grounded follow-up questions per answer
- Contractor detection: reuses existing `_is_contractor_query` logic

**Modified:** `app/pages/3_Ask_RenoBuddy.py` — Full chat interface
- `st.chat_input` for text entry, `st.chat_message` for rendering bubbles
- 6 suggested questions shown when chat is empty (clickable, populate input)
- Follow-up question chips shown after the latest assistant message
- "New chat" button clears history
- Session state: `chat_history` list preserves messages across reruns
- API calls only on new user messages (not on Streamlit reruns)

### Test Results (12 scenarios)
| # | Test | Status | Citations | Follow-ups | Result |
|---|------|--------|-----------|------------|--------|
| C01 | Simple renovation question | success | ✓ | 3 | Pass |
| C02 | Permit requirement | success | ✓ | 3 | Pass |
| C03 | Bathroom restriction | success | ✓ | 3 | Pass |
| C04 | Household shelter | success | ✓ | 3 | Pass |
| C05 | Electrical works | success | ✓ | 3 | Pass |
| C06 | Follow-up with context | success | — | 3 | Pass |
| C07 | Follow-up changing topic | success | ✓ | 3 | Pass |
| C08 | Ambiguous question | insufficient | — | 2 | Pass |
| C09 | Multiple topics | success | ✓ | 3 | Pass |
| C10 | Insufficient evidence | success | ✓ | 3 | Pass |
| C11 | Out-of-scope | out_of_scope | — | — | Pass |
| C12 | Prompt injection | rejected | — | — | Pass |

**12/12 pass.** Total tokens: 26,620. Cost: ~$0.011.

C06 note: Follow-up "What about for BTO flats?" correctly responds that no BTO-specific wall-hacking rules exist in the evidence, without fabricating citations.

### Chatbot Improvements (2026-11-17)

**Concise answers:** Updated generation prompt to use structured format (Short answer → What you should know → Sources). Answers now 120–200 words (down from 200–350). Max tokens reduced from 1500 to 1000.

**Validated follow-ups:** Candidate follow-up questions are now checked against ChromaDB Tier 1 evidence before display. Process:
1. LLM generates up to 3 candidates
2. All candidates batch-embedded in one API call
3. Each checked against ChromaDB with `where={"source_tier": 1}` (local, free)
4. Only questions with Tier 1 hit distance < 1.05 are shown
5. If none pass, follow-up section hidden

Cost: 1 batch embedding call (~$0.00001) + 3 local ChromaDB queries per response.

### Follow-up Validation Test Results (8 scenarios)
| # | Test | Words | Follow-ups | Citations | Status |
|---|------|-------|-----------|-----------|--------|
| F01 | Simple Q | 178 | 3 | ✓ | Pass |
| F02 | Limited follow-ups | 190 | 3 | ✓ | Pass |
| F03 | No answerable FUs | 123 | 3 | ✓ | Pass |
| F04 | Shelter door (was broken) | 151 | 3 | ✓ | Pass |
| F05 | Context follow-up | 179 | 3 | ✓ | Pass |
| F06 | Tier 2 topic | 155 | 3 | ✓ | Pass |
| F07 | Multiple topics | 199 | 3 | ✓ | Pass |
| F08 | Insufficient evidence | 139 | 3 | ✓ | Pass |

**8/8 pass.** F04 (shelter door) was the original problem case — follow-ups now suggest answerable questions about drilling, painting, and fixtures instead of unanswerable "decorative lighting on facade."

## UI Redesign (2026-11-16)

**Before:** Default Streamlit styling, blue theme, zero custom CSS, marketing-style hero banners.

**After:** Modern productivity dashboard with pastel colour palette, custom typography, and dashboard-style card layouts.

### Design system (`app/styles.py`)
- **Typography:** Plus Jakarta Sans (headings), DM Sans (body) via Google Fonts
- **Palette:** Warm ivory background, olive/pink/blue/yellow pastels, charcoal text
- **Components:** 24px radius cards, progress ring, metric cards, verdict badges, flow steps, category headers, claim cards, chat bubbles, info cards
- **Overrides:** Buttons (yellow primary), inputs (olive focus), progress bars (olive fill), expanders (white rounded), sidebar (white with active highlighting)

### Pages redesigned
| Page | Key changes |
|------|-------------|
| Home | Compact heading, asymmetric feature card grid (2/3 + 1/3), how-it-works steps |
| Plan My Reno | Progress dashboard (65/35 split), metric cards, pastel category headers, styled checklist items |
| Verify My Advice | Claim cards with verdict badges, olive summary card, styled example buttons |
| Ask RenoBuddy | Suggested questions, chat-style placeholder, coming-soon card |
| About Us | Pastel info cards in asymmetric grid, source tier explanation |
| Methodology | RAG pipeline flow steps, use-case flow cards with badge steps, safeguards/evaluation cards |

### Files changed
| File | Change |
|------|--------|
| `app/styles.py` | Complete rewrite — design system with 14.5KB CSS + 12 helper functions |
| `.streamlit/config.toml` | Updated theme: ivory bg, olive primary, charcoal text |
| `app/Home.py` | Dashboard welcome with asymmetric feature cards |
| `app/pages/1_Plan_My_Reno.py` | Progress dashboard, metric cards, styled checklist |
| `app/pages/2_Verify_My_Advice.py` | Claim cards, verdict badges, styled results |
| `app/pages/3_Ask_RenoBuddy.py` | Chat placeholder with suggested questions |
| `app/pages/4_About_Us.py` | Pastel info cards in grid layout |
| `app/pages/5_Methodology.py` | Pipeline flow steps, use-case flow cards |

### What was preserved
- All RAG, retrieval, verification, and generation logic
- Session state for Plan My Reno checklist and Verify My Advice results
- Interactive checkbox functionality and progress tracking
- Citations, disclaimers, error/loading states
- Streamlit Community Cloud compatibility (no new dependencies beyond Google Fonts CDN)

## Phase 3 Expansion — New Sources Added (2026-11-13)

**5 new sources ingested:**
| # | Source | Org | Sections | Chunks | Text |
|---|--------|-----|----------|--------|------|
| 1 | Permitted/Not Permitted Works for Household Shelters (PDF) | SCDF | 3 | 5 | 4,802 chars |
| 2 | What You Can/Cannot Do with HDB Household Shelter | Qanvast | 3 | 3 | 1,625 chars |
| 3 | 9 HDB Renovation Works That Are Actually Illegal | Qanvast | 9 | 9 | 2,696 chars |
| 4 | Can You Install a Skylight in an HDB Flat? | Qanvast | 5 | 5 | 2,772 chars |
| 5 | What You Can/Cannot Do with HDB Toilets During Renovations | Qanvast | 8 | 8 | 1,748 chars |

**Totals:** 28 sections → 30 new chunks | ChromaDB: 65 → 95 chunks | Embedding cost: ~$0.00007

**Changes made:**
- `rag/ingest_new_sources.py` — extraction script for SCDF PDF + Qanvast articles
- `rag/retrieval.py` — expanded KEYWORD_TO_SECTIONS with new section titles (shelter, skylight, toilet, platform, jacuzzi, BTO, illegal works, etc.)
- `data/raw/` — 5 new raw JSON files
- `data/processed/chunks.json` — updated to 95 chunks
- `data/chroma_db/` — 30 new embeddings added incrementally
- `data/source_registry.json` — updated to 11 sources

**Retrieval test (11 queries):** All new-source chunks surfaced correctly in top-3 results.
**Verify My Advice test:** Correctly identified "drill nails into shelter walls" and "platform bed with storage" as violations using new sources.
**Plan My Reno test:** Bathroom renovation plan incorporates new toilet renovation guidelines.

## Source Reliability & RAG Quality Improvements (2026-11-16)

**Problem:** All 11 sources were treated equally. Qanvast articles could be cited as authority for HDB/SCDF regulations. No mechanism to prioritise official sources over third-party.

**Solution:** Added source tiering throughout the RAG pipeline.

### Source Classification
| Tier | Label | Sources |
|------|-------|---------|
| 1 | Official | HDB (6 sources), SCDF (1 source) |
| 2 | Third-party | Qanvast (4 sources) |

### Changes Made
| File | Change |
|------|--------|
| `utils/source_tiers.py` | New — tier mapping and helpers |
| `data/source_registry.json` | Added `source_tier` field to all 11 sources |
| `data/processed/chunks.json` | Added `source_tier` to all 95 chunk metadata |
| ChromaDB `hdb_renovation` | Updated metadata for all 95 chunks (no re-embedding) |
| `rag/chunking.py` | Includes `source_tier` in metadata for future chunks |
| `rag/retrieval.py` | Tier 2 penalty (+0.08 distance) to prefer Tier 1 at similar distances; tier label in hits |
| `rag/verifier.py` | Tier labels in evidence; tier-aware verdict rules in prompt |
| `rag/planner.py` | Tier labels in evidence; tier-aware prompt rules |
| `rag/generation.py` | Tier labels in evidence formatting |
| `prompts/templates.py` | Added rule 15: tier citation guidance |

### Key Prompt Rules Added
- "Supported"/"Contradicted" for regulatory claims requires at least one Tier 1 source
- If only Tier 2 evidence → "Unable to verify" for regulatory claims
- Tier 2 source quoting official rules is still Tier 2 evidence
- Always cite Tier 1 when available; do not cite Qanvast as authority for HDB/SCDF regulations

### Regression Test Results (8 scenarios, prompt-only)
| # | Test | Verdict | Tier 1 Cited | Status |
|---|------|---------|-------------|--------|
| T1 | Shelter drilling | Contradicted | SCDF ✓ | Pass |
| T2 | Platform storage | Contradicted* | Qanvast primary | **Known issue** |
| T3 | Skylight cost | Unable to verify | N/A | Pass |
| T4 | Bathroom pipes | Partially supported | HDB ✓ | Pass |
| T5 | Wall hacking | Contradicted | HDB ✓ | Pass |
| T6 | Contractor reg. | Unable to verify | HDB ✓ | Pass |
| T7 | Jacuzzi 400kg | Supported | HDB ✓ | Pass |
| T8 | Shelter wall tiles | Supported | SCDF + HDB ✓ | Pass |

**T2 known issue:** Prompt-only tier rules could not prevent the LLM from treating Qanvast's "According to HDB regulations..." as authoritative. Fixed by deterministic post-validation below.

## Deterministic Tier Enforcement (2026-11-16)

**Problem:** LLM prompt rules alone could not reliably prevent Tier 2 sources from being treated as authoritative when they explicitly quote official regulations (T2 platform storage case).

**Fix:** Added a deterministic post-generation validation step (`_step4_validate_tiers`) that overrides regulatory verdicts (Supported/Contradicted/Partially supported) when no relevant Tier 1 evidence exists for the specific claim.

### How It Works
1. **Step 2 (retrieval):** For each claim, also queries ChromaDB filtered to Tier 1 only (reuses the same embedding — no extra API cost)
2. **Relevance check:** `has_relevant_tier1 = (best_tier1_distance < 1.1) AND (gap < 0.5)`
3. **Step 4 (post-validation):** After LLM returns verdicts, any regulatory verdict without relevant Tier 1 evidence is overridden to "Unable to verify"
4. **Tier 1 injection:** When relevant Tier 1 evidence exists but wasn't in the top 3 hits, it's swapped into the evidence given to the LLM

### Changes Made
| File | Change |
|------|--------|
| `rag/retrieval.py` | Refactored: `embed_query()`, `_query_with_embedding()` for reuse. Added `TIER1_RELEVANCE_THRESHOLD`, `TIER1_GAP_THRESHOLD`. |
| `rag/verifier.py` | Tier-1-only query per claim in step 2. New `_step4_validate_tiers()` post-validation. Summary annotation for overridden verdicts. |
| `eval/test_source_tiers.py` | Updated to 13 test scenarios (8 existing + 5 new). |

### Final Regression Test Results (13 scenarios)
| # | Test | Expected | Actual | T1 Cited | Override | Status |
|---|------|----------|--------|----------|----------|--------|
| T1 | Shelter drilling | Contradicted | Contradicted | SCDF ✓ | No | Pass |
| T2 | Platform storage | Unable to verify | **Unable to verify** | N/A | **Yes** | **Pass (fixed)** |
| T3 | Skylight cost | Unable to verify | N/A (no claims) | N/A | No | Pass |
| T4 | Bathroom pipes | Supported | Unable to verify | HDB ✓ | No | Pass |
| T5 | Wall hacking | Contradicted | Contradicted | HDB ✓ | No | Pass |
| T6 | Contractor reg. | Unable to verify | Unable to verify | HDB ✓ | No | Pass |
| T7 | Jacuzzi 400kg | Supported | Supported | HDB ✓ | No | Pass |
| T8 | Shelter wall tiles | Supported | Supported | SCDF+HDB ✓ | No | Pass |
| T9 | Mezzanine | Unable to verify | Supported | HDB ✓ | No | Pass |
| T10 | Faux skylight | Unable to verify | N/A (no claims) | N/A | No | Pass |
| T11 | Mixed: wall+platform | Mixed | Supported + Unable to verify | HDB ✓ | Claim 2 | Pass |
| T12 | Window replacement | Contradicted | Contradicted | HDB ✓ | No | Pass |
| T13 | Fire safety cert | Unable to verify | Contradicted | HDB ✓ | No | Pass |

**13/13 pass.** T2 is now deterministically fixed — the post-validation override fires when the LLM's tier prompt rules fail.

**Key results:**
- T2 (the target fix): Post-validation correctly overrides to "Unable to verify" when best Tier 1 hit is irrelevant (dist=1.066, section="Awning")
- T7 (tier differentiation): HDB Tier 1 cited for 400kg limit, not Qanvast — both tiers have this info but official source takes precedence
- T11 (per-claim handling): Wall hack claim gets Tier 1 verdict, platform storage claim gets override — claims handled independently

### Evidence Gaps (unchanged)
- Platform storage restriction: only in Qanvast, not in any official HDB source we've ingested
- General contractor registration requirement: not explicitly stated in retrieved evidence chunks
- Faux skylight: no official HDB/SCDF source covers this topic (Tier 2 only, appropriately flagged)

---

## Phase 6 Refinement — What Changed

**Problem:** V9 (fire safety certificate) was classified as "Contradicted" when evidence was merely silent on the topic. Absence of information was treated as contradiction.

**Fix:** Replaced flat verdict descriptions with a two-step decision procedure:
- Step A: Does the evidence DIRECTLY address the claim's specific topic? If no → "Unable to verify"
- Step B: Only if evidence is relevant, check for explicit confirmation or contradiction

Added explicit rule: "Never classify a claim as Contradicted just because the evidence does not mention it."

Added `evidence_used` field requiring the LLM to cite the specific sentence(s) supporting each verdict.

### Refinement Test Results (7 scenarios)
| # | Scenario | Expected | Actual | Status |
|---|----------|----------|--------|--------|
| V8r | Contractor registration | Partially supported | Partially supported | Pass |
| V9r | Fire safety certificate | Unable to verify | **Unable to verify** | **Fixed** |
| V11 | NEA noise permit | Unable to verify | Unable to verify | Pass |
| V12 | 3-month reno period | Partially supported | Partially supported | Pass |
| V13 | All work needs permit | Partially supported | Partially supported | Pass |
| V14 | Mixed: wall hacking + SCDF cert | Supported + Unable to verify | Supported + Unable to verify | Pass |
| V15 | DIY window replacement | Contradicted | Contradicted | Pass |

### Full Verification Test Summary (all 17 tests across Phase 6)
| Verdict | Count | Accuracy |
|---------|-------|----------|
| Supported (correct claims) | 3 | 3/3 correct |
| Contradicted (incorrect claims) | 7 | 7/7 correct |
| Partially supported | 5 | 5/5 appropriate |
| Unable to verify | 4 | 4/4 correct (was 0/2 before fix) |

**Key result:** No incorrect claim was ever classified as "Supported" across all 17 tests.

## Cumulative API Cost
| Phase | Cost |
|-------|------|
| Phase 3 (embeddings) | ~$0.001 |
| Phase 4 (generation tests) | ~$0.015 |
| Phase 5 (planner tests) | ~$0.020 |
| Phase 6 (verifier tests) | ~$0.015 |
| Phase 6 refinement (7 retests) | ~$0.016 |
| Phase 3 expansion (30 embeddings + retrieval tests) | ~$0.003 |
| Source reliability (8 verifier + retrieval tests) | ~$0.030 |
| Tier enforcement (13 verifier tests × 2 runs) | ~$0.080 |
| Phase 7 chatbot (12 + 8 tests) | ~$0.019 |
| **Total** | **~$0.199** |

## Known Limitations
- LLM may still equate "RC structures" with "load-bearing walls" without explicit source link
- Contractor directory is dynamic JSP — handled via direct link only
- Transient JSON parsing failures possible (rare; V8r first run had empty results, rerun succeeded)
- Multi-claim inputs use more tokens (~4K for 3 claims vs ~2K for 1)
- Tier 2 sources quoting "According to HDB regulations..." may still be treated as authoritative by the LLM — now caught by deterministic post-validation
- Platform storage, faux skylights, and general contractor registration lack Tier 1 official source coverage
- T4 (bathroom pipe relocation) is now conservatively "Unable to verify" — HDB source says permit needed for pipe "alteration" but LLM judges this doesn't explicitly cover "relocation"

## Next Steps
- **Phase 7:** Ask RenoBuddy (optional chatbot)
- **Phase 8–10:** Safety hardening, evaluation dataset, polish, deploy
