import streamlit as st

from styles import page_head, render_verdict_badge, COLORS

VERDICT_ICONS = {
    "Supported": "✅",
    "Contradicted": "❌",
    "Partially supported": "⚠️",
    "Unable to verify": "❓",
}

EXAMPLE_CLAIMS = [
    "My contractor said no permit is needed to hack the kitchen wall since it's not a load-bearing wall.",
    "My ID told me I can replace my BTO bathroom tiles immediately after getting the keys.",
    "The contractor said I don't need a licensed plumber to change the kitchen sink pipes.",
    "My ID said window replacement doesn't need HDB approval if I use the same type of window.",
]

# --- Header with inline SVG icon ---
st.markdown(
    '<div class="rb-page-head" style="display:flex; align-items:center; gap:0.6rem;">'
    '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" '
    'fill="none" stroke="#252525" stroke-width="1.75" stroke-linecap="round" '
    'stroke-linejoin="round" style="flex-shrink:0;">'
    '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>'
    '<path d="m9 12 2 2 4-4"/>'
    "</svg>"
    "<h1>Verify the Advice</h1>"
    "</div>"
    '<p style="font-family:\'DM Sans\',sans-serif; font-size:0.92rem; '
    'color:#858585; margin:0.25rem 0 0 0;">Check what your ID or contractor told you against official HDB sources.</p>',
    unsafe_allow_html=True,
)

st.markdown("")

# --- Example claims (full text, no truncation) ---
st.markdown(
    '<p style="font-family: \'Plus Jakarta Sans\', sans-serif; font-weight: 600; '
    'font-size: 0.88rem; margin-bottom: 0.5rem;">Try an example</p>',
    unsafe_allow_html=True,
)

with st.container(key="verify_examples"):
    cols = st.columns(2)
    for i, example in enumerate(EXAMPLE_CLAIMS):
        with cols[i % 2]:
            if st.button(example, key=f"ex_{i}", use_container_width=True):
                st.session_state.verify_input = example

# --- Input ---
claim_text = st.text_area(
    "What did your ID or contractor tell you?",
    value=st.session_state.get("verify_input", ""),
    placeholder='Example: "We need to hack the bathroom wall to relocate the toilet bowl, but no permit is needed for this."',
    height=120,
    max_chars=2000,
)

st.caption(
    "**Disclaimer:** RenoBuddy checks claims against publicly available HDB "
    "guidelines. It does not provide official approval or legal advice."
)

# --- Verify button ---
if st.button("Verify this advice", type="primary", use_container_width=True):
    if not claim_text or not claim_text.strip():
        st.warning("Please enter something your ID or contractor told you.")
    else:
        from utils.safety import validate_input, is_out_of_scope, OUT_OF_SCOPE_RESPONSE
        from utils.config import get_openai_client
        from rag.verifier import verify_advice

        is_valid, error_msg = validate_input(claim_text)
        if not is_valid:
            st.warning(error_msg)
        elif is_out_of_scope(claim_text):
            st.info(OUT_OF_SCOPE_RESPONSE)
        else:
            client = get_openai_client()
            with st.spinner("Checking your advice against official HDB sources..."):
                result = verify_advice(client, claim_text)
            st.session_state.verify_result = result

# --- Results ---
result = st.session_state.get("verify_result")
if result:
    st.markdown("")

    if result["status"] == "no_claims":
        st.info(result["summary"])
    elif result["status"] == "success":
        st.markdown(
            f'<div class="rb-card rb-card-olive">'
            f'<h3>Verification summary</h3>'
            f'<p style="font-size: 0.9rem;">{result["summary"]}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

        results = result.get("results", [])
        if results:
            st.markdown("### Detailed results")

            for i, r in enumerate(results, 1):
                verdict = r.get("verdict", "Unable to verify")
                icon = VERDICT_ICONS.get(verdict, "❓")

                st.markdown(
                    f'<div class="rb-claim-card">'
                    f'<h4>{render_verdict_badge(verdict, icon)} Claim {i}</h4>'
                    f'<div class="told">{r.get("claim", "N/A")}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                with st.expander("What official sources say", expanded=True):
                    st.markdown(r.get("what_hdb_says", "No information available."))

                if r.get("what_this_means"):
                    st.markdown(f'**What this means for you:** {r.get("what_this_means")}')

                questions = r.get("questions_to_ask")
                if questions:
                    with st.expander("Questions to ask your ID/contractor"):
                        if isinstance(questions, list):
                            for q in questions:
                                st.markdown(f"- {q}")
                        else:
                            st.markdown(questions)

                sources = r.get("sources", [])
                if sources:
                    with st.expander("Official sources"):
                        for src in sources:
                            section = src.get("section", "HDB Guidelines")
                            url = src.get("url", "")
                            if url:
                                st.markdown(f"- [{section}]({url})")
                            else:
                                st.markdown(f"- {section}")

                if i < len(results):
                    st.markdown("")

        if result.get("usage"):
            with st.expander("Verification details"):
                st.markdown(f"**Claims extracted:** {len(result.get('claims', []))}")
                st.markdown(f"**Claims verified:** {len(results)}")
                u = result["usage"]
                st.markdown(f"**Tokens used:** {u['total_tokens']:,}")
