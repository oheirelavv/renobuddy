import json
from urllib.parse import urlparse as _urlparse

import streamlit as st

from styles import page_head, render_info_card, render_metric_card, COLORS
from utils.auth import require_admin
from utils.source_tiers import SOURCE_TIERS, is_verified_official

require_admin()

page_head("Manage Knowledge Base", "Add and manage RenoBuddy's information sources.")

# --- Persistence warning ---
st.markdown(
    '<div style="background:#FDF5D9; border-radius:14px; padding:0.85rem 1.1rem; '
    'margin-bottom:1rem; font-family:\'DM Sans\',sans-serif; font-size:0.82rem; color:#8B7420;">'
    '<strong>Deployment note:</strong> On Streamlit Community Cloud, newly added sources '
    'are stored in ephemeral local storage and will be lost on redeployment. '
    'To persist changes permanently, commit the updated data files to your repository.'
    '</div>',
    unsafe_allow_html=True,
)

# --- Current stats ---
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
REGISTRY_PATH = DATA_DIR / "source_registry.json"

registry = {"sources": []}
if REGISTRY_PATH.exists():
    with open(REGISTRY_PATH) as f:
        registry = json.load(f)

sources = registry.get("sources", [])
tier1 = sum(1 for s in sources if s.get("source_tier") == 1)
tier2 = sum(1 for s in sources if s.get("source_tier") == 2)

from rag.embeddings import get_chroma_client, COLLECTION_NAME

try:
    chroma = get_chroma_client()
    collection = chroma.get_collection(name=COLLECTION_NAME)
    chunk_count = collection.count()
except Exception:
    chunk_count = "?"

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(render_metric_card(str(len(sources)), "Total sources", accent=COLORS["olive"]), unsafe_allow_html=True)
with c2:
    st.markdown(render_metric_card(f"{tier1} / {tier2}", "Official / Supplementary", accent=COLORS["blue"]), unsafe_allow_html=True)
with c3:
    st.markdown(render_metric_card(str(chunk_count), "Chunks in ChromaDB", accent=COLORS["yellow"]), unsafe_allow_html=True)

st.markdown("")

# --- Add Website Source ---
st.markdown("### Add website source")

url_input = st.text_input(
    "Public website URL",
    placeholder="https://www.hdb.gov.sg/...",
)

source_type = st.selectbox(
    "Source type",
    ["— Select source type —", "Official Source", "Supplementary Source"],
    key="kb_source_type",
)

_TYPE_TO_TIER = {"Official Source": 1, "Supplementary Source": 2}
selected_tier = _TYPE_TO_TIER.get(source_type)

if "kb_preview" not in st.session_state:
    st.session_state.kb_preview = None

# --- Step 1: Fetch & Preview ---
can_fetch = bool(url_input) and selected_tier is not None
if st.button("Fetch & Preview", type="primary", disabled=not can_fetch):
    from rag.admin_ingest import fetch_and_preview

    with st.spinner("Fetching and extracting content..."):
        preview = fetch_and_preview(url_input)

    st.session_state.kb_preview = preview

preview = st.session_state.kb_preview

if preview:
    if preview["status"] == "error":
        st.error(f"Extraction failed: {preview['error']}")
    else:
        # --- Step 2: Preview ---
        st.markdown("---")
        st.markdown("#### Source preview")

        if preview["is_duplicate"]:
            st.warning(f"A source with ID `{preview['source_id']}` already exists. Re-ingesting will update it.")

        with st.container(border=True):
            p1, p2 = st.columns(2)
            with p1:
                st.markdown(f"**Title:** {preview['title']}")
                st.markdown(f"**URL:** {preview['url']}")
                st.markdown(f"**Organisation:** {preview['organisation']}")
            with p2:
                st.markdown(f"**Sections:** {preview['section_count']}")
                st.markdown(f"**Total text:** {preview['total_text_length']:,} chars")
                st.markdown(f"**Est. chunks:** {preview['est_chunks']}")

            st.markdown(f"**Source type:** {source_type}")
            st.markdown(f"**Est. embedding cost:** ${preview['est_cost']:.5f}")

        st.markdown("**Extracted content preview:**")
        method_label = {
            "nextjs_accordion": "Next.js accordion (HDB)",
            "generic": "Generic HTML",
        }.get(preview.get("extraction_method", "generic"), "Generic HTML")
        st.caption(
            f"Extraction method: {method_label} · "
            f"{preview['section_count']} sections · "
            f"{preview['total_text_length']:,} chars total"
        )
        for w in preview.get("warnings", []):
            st.warning(w)
        st.text_area("", value=preview["text_preview"], height=200, disabled=True, label_visibility="collapsed")
        if preview["total_text_length"] > 2000:
            st.caption(
                f"Showing partial preview. Full extracted content: "
                f"{preview['total_text_length']:,} chars across {preview['section_count']} sections."
            )

        # --- Validate Official Source selection ---
        tier_blocked = False
        if selected_tier == 1:
            _hostname = (_urlparse(preview["url"]).hostname or "").lower()
            is_official, reason = is_verified_official(_hostname, preview["organisation"])
            if not is_official:
                st.error(f"**Cannot classify as Official Source.** {reason}")
                st.info(
                    "Change the source type above to **Supplementary Source** if you "
                    "still want to add this website."
                )
                tier_blocked = True

        if selected_tier is None:
            st.warning("Select a source type above before proceeding.")
            tier_blocked = True

        # --- Step 3: Approve & Ingest ---
        if not tier_blocked:
            st.markdown("")
            if st.button("Approve & Add to Knowledge Base", type="primary", use_container_width=True):
                from utils.config import get_openai_client
                from rag.admin_ingest import ingest_source

                client = get_openai_client()

                with st.spinner("Embedding and adding to ChromaDB..."):
                    result = ingest_source(preview, selected_tier, client)

                if result["status"] == "success":
                    st.success(
                        f"Source added successfully. "
                        f"{result['chunks_added']} new chunks embedded. "
                        f"Total chunks in ChromaDB: {result['total_chunks']}."
                    )
                    st.session_state.kb_preview = None
                    st.rerun()
                else:
                    st.error(f"Ingestion failed: {result.get('error', 'Unknown error')}")

# --- Existing sources ---
st.markdown("---")
st.markdown("### Current sources")

for s in sources:
    tier_badge = (
        '<span style="background:#E8EDDA; color:#5D6E2E; padding:2px 8px; '
        'border-radius:10px; font-size:0.72rem; font-weight:600;">Official</span>'
        if s.get("source_tier") == 1
        else '<span style="background:#E8F0FA; color:#4A6B94; padding:2px 8px; '
        'border-radius:10px; font-size:0.72rem; font-weight:600;">Supplementary</span>'
    )
    st.markdown(
        f'{tier_badge} **{s["title"]}** — {s.get("total_text_length", 0):,} chars, '
        f'{s.get("sections_with_content", 0)} sections '
        f'([source]({s["url"]}))',
        unsafe_allow_html=True,
    )
