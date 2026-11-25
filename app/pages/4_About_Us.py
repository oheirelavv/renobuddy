import streamlit as st

from styles import page_head, render_info_card, COLORS

page_head("About RenoBuddy", "A RAG-powered renovation assistant for Singapore HDB homeowners.")

# --- Problem + Who it's for ---
left, right = st.columns([2, 1])

with left:
    st.markdown(
        render_info_card(
            "The problem",
            "<p>HDB homeowners in Singapore face a complex renovation landscape — "
            "navigating permits, regulations, contractor claims, and official guidelines "
            "across multiple government agencies.</p>"
            "<p>Misinformation from contractors or interior designers can lead to costly "
            "mistakes, delays, or regulatory violations.</p>",
            COLORS["pink_light"],
        ),
        unsafe_allow_html=True,
    )

with right:
    st.markdown(
        render_info_card(
            "Who it's for",
            "<ul>"
            "<li>HDB homeowners (BTO and resale) planning renovations</li>"
            "<li>First-time renovators unfamiliar with regulations</li>"
            "<li>Homeowners who want to cross-check advice from their ID or contractor</li>"
            "</ul>",
            COLORS["yellow_light"],
        ),
        unsafe_allow_html=True,
    )

# --- Three features ---
ICON_CLIP = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" '
    'fill="none" stroke="#252525" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
    '<rect width="8" height="4" x="8" y="2" rx="1" ry="1"/>'
    '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>'
    '<path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/></svg>'
)
ICON_SHIELD = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" '
    'fill="none" stroke="#252525" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>'
    '<path d="m9 12 2 2 4-4"/></svg>'
)
ICON_MSG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" '
    'fill="none" stroke="#252525" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22z"/></svg>'
)

_h = "display:flex; align-items:center; gap:0.5rem; margin-bottom:0.4rem;"
_t = "font-family:'Plus Jakarta Sans',sans-serif; font-weight:700; font-size:1rem; color:#252525; margin:0;"

f1, f2, f3 = st.columns(3)

with f1:
    st.markdown(
        render_info_card(
            "",
            f'<div style="{_h}">{ICON_CLIP}<span style="{_t}">Plan My Reno</span></div>'
            "<p>Get a personalised renovation checklist based on your flat type and planned works — "
            "covering permits, requirements, and key questions to ask your ID or contractor.</p>",
            COLORS["olive_light"],
        ),
        unsafe_allow_html=True,
    )

with f2:
    st.markdown(
        render_info_card(
            "",
            f'<div style="{_h}">{ICON_SHIELD}<span style="{_t}">Verify the Advice</span></div>'
            "<p>Check claims made by your interior designer or contractor against official "
            "HDB and SCDF sources. Get clear verdicts with citations and practical explanations.</p>",
            COLORS["pink_light"],
        ),
        unsafe_allow_html=True,
    )

with f3:
    st.markdown(
        render_info_card(
            "",
            f'<div style="{_h}">{ICON_MSG}<span style="{_t}">Ask RenoBuddy</span></div>'
            "<p>Ask renovation-related questions in natural language and receive easy-to-understand "
            "answers grounded in available sources. The chatbot supports follow-up questions, "
            "provides source citations, and directs users to Plan My Reno or Verify the Advice "
            "when appropriate.</p>",
            COLORS["blue_light"],
        ),
        unsafe_allow_html=True,
    )

# --- Our Information Sources ---
st.markdown("### Our information sources")

ICON_GOV = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" '
    'fill="none" stroke="#252525" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M12 2 2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>'
)
ICON_BOOK = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" '
    'fill="none" stroke="#252525" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>'
    '<path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>'
)

s1, s2 = st.columns(2)

with s1:
    st.markdown(
        render_info_card(
            "",
            f'<div style="{_h}">{ICON_GOV}<span style="{_t}">Official sources (Tier 1)</span></div>'
            "<p style='color:#858585; font-size:0.82rem; margin-bottom:0.6rem;'>"
            "Guidance published by government authorities. RenoBuddy prioritises these sources "
            "when explaining renovation requirements, restrictions and approvals.</p>"
            "<ul>"
            '<li><a href="https://www.hdb.gov.sg/managing-my-home/renovation-and-maintenance/renovation/renovation-guidelines" '
            'target="_blank">Housing &amp; Development Board (HDB)</a> — 5 guideline pages covering '
            "building works, windows, electrical, air-conditioning, and plumbing</li>"
            '<li><a href="https://www.scdf.gov.sg" target="_blank">Singapore Civil Defence Force (SCDF)</a> '
            "— Permitted and not permitted works for household shelters</li>"
            "</ul>"
            "<p style='font-size:0.82rem; color:#858585; margin-top:0.4rem;'>"
            "Note: BCA regulations are referenced within HDB sources but are not ingested as a separate source.</p>",
            COLORS["olive_light"],
        ),
        unsafe_allow_html=True,
    )

with s2:
    st.markdown(
        render_info_card(
            "",
            f'<div style="{_h}">{ICON_BOOK}<span style="{_t}">Supplementary sources (Tier 2)</span></div>'
            "<p style='color:#858585; font-size:0.82rem; margin-bottom:0.6rem;'>"
            "Additional renovation information from third-party sources. These articles provide "
            "useful context but are not treated as official evidence of regulatory requirements.</p>"
            "<ul>"
            '<li><a href="https://qanvast.com/sg/articles/what-you-can-and-cannot-do-with-your-hdb-household-shelter-2445" '
            'target="_blank">Qanvast</a> — 4 articles covering household shelters, '
            "illegal renovation works, faux skylights, and toilet renovations</li>"
            "</ul>"
            "<p style='font-size:0.82rem; color:#858585; margin-top:0.4rem;'>"
            "Tier 2 sources may provide supplementary context but cannot independently establish "
            "regulatory requirements. Regulatory verdicts require Tier 1 evidence.</p>",
            COLORS["blue_light"],
        ),
        unsafe_allow_html=True,
    )

# --- Limitations ---
st.markdown(
    render_info_card(
        "Limitations",
        "<ul>"
        "<li>Provides <strong>guidance only</strong>, not legal or professional advice</li>"
        "<li>Based on publicly available sources — may not reflect the latest regulatory changes</li>"
        "<li>Some topics (e.g. platform storage, faux skylights) lack official source coverage</li>"
        "<li>Cannot verify individual contractor registrations in real time</li>"
        "<li>Always confirm critical decisions with HDB, SCDF, or a licensed professional</li>"
        "</ul>",
        COLORS["white"],
    ),
    unsafe_allow_html=True,
)
