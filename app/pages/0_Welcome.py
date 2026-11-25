import streamlit as st
from styles import page_head, COLORS

page_head(
    "Your renovation journey starts here",
    "Plan your HDB renovation with confidence using official government sources.",
)

st.markdown("")

# --- Mandatory disclaimer ---
with st.expander("Important Notice — Please Read", expanded=False):
    st.markdown(
        "**IMPORTANT NOTICE:** This web application is a prototype developed for "
        "**educational purposes only.** The information provided here is **NOT "
        "intended for real-world usage** and should not be relied upon for making "
        "any decisions, especially those related to financial, legal, or healthcare matters.\n\n"
        "**Furthermore, please be aware that the LLM may generate inaccurate or "
        "incorrect information. You assume full responsibility for how you use any "
        "generated output.**\n\n"
        "Always consult with qualified professionals for accurate and personalised advice."
    )

st.markdown("")

# ---------------------------------------------------------------------------
# Roadmap — circles on top with connecting line, text below
# ---------------------------------------------------------------------------

milestones = [
    ("1", "Plan your renovation", "Understand your planned works and applicable requirements.", COLORS["olive_light"]),
    ("2", "Check the advice", "Verify claims from your ID or contractor against official guidance.", COLORS["pink_light"]),
    ("3", "Move forward confidently", "Know what to clarify before proceeding.", COLORS["blue_light"]),
]

# Build milestone circles + text columns
_circles = ""
_texts = ""
for i, (num, title, desc, color) in enumerate(milestones):
    _circles += (
        f'<div style="flex:1; display:flex; justify-content:center; position:relative; z-index:1;">'
        f'<div style="width:40px; height:40px; border-radius:50%; background:{color}; '
        f'display:flex; align-items:center; justify-content:center; '
        f"font-family:'Plus Jakarta Sans',sans-serif; font-weight:700; font-size:0.95rem; "
        f'color:#252525;">{num}</div>'
        f'</div>'
    )
    _texts += (
        f'<div style="flex:1; text-align:center; padding:0 0.5rem;">'
        f"<div style=\"font-family:'Plus Jakarta Sans',sans-serif; font-weight:600; "
        f'font-size:0.88rem; color:#252525; margin-bottom:0.15rem;">{title}</div>'
        f"<div style=\"font-family:'DM Sans',sans-serif; font-size:0.8rem; "
        f'color:#858585; line-height:1.45;">{desc}</div>'
        f'</div>'
    )

st.markdown(
    '<div style="background:#FFFFFF; border-radius:24px; border:1px solid #E8E5DF; '
    'padding:1.5rem 2rem 1.5rem;">'
    "<p style=\"font-family:'DM Sans',sans-serif; font-size:0.82rem; "
    'color:#858585; margin:0 0 1.25rem 0;">From your first idea to a more confident renovation.</p>'
    # Circles row with curved SVG path behind
    '<div style="position:relative; margin-bottom:0.75rem;">'
    # SVG curved S-path behind circles
    '<svg viewBox="0 0 600 50" preserveAspectRatio="none" '
    'style="position:absolute; top:0; left:16.7%; width:66.6%; height:50px; z-index:0; overflow:visible;">'
    '<path d="M 0,25 C 75,0 125,50 150,25 S 225,0 300,25 S 375,50 450,25 S 525,0 600,25" '
    'fill="none" stroke="#C8C5B9" stroke-width="2" stroke-dasharray="6,5" />'
    '</svg>'
    # Circles on top
    f'<div style="display:flex; position:relative; z-index:1;">{_circles}</div>'
    '</div>'
    # Text row
    f'<div style="display:flex;">{_texts}</div>'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown("")

# ---------------------------------------------------------------------------
# Feature cards with buttons inside (equal height via CSS)
# ---------------------------------------------------------------------------

ICON_PLAN = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" '
    'fill="none" stroke="#252525" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
    '<rect width="8" height="4" x="8" y="2" rx="1" ry="1"/>'
    '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>'
    '<path d="M12 11h4"/><path d="M12 16h4"/>'
    '<path d="M8 11h.01"/><path d="M8 16h.01"/>'
    '</svg>'
)
ICON_VERIFY = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" '
    'fill="none" stroke="#252525" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>'
    '<path d="m9 12 2 2 4-4"/>'
    '</svg>'
)
ICON_ASK = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" '
    'fill="none" stroke="#252525" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22z"/>'
    '</svg>'
)

_h = "display:flex; align-items:center; gap:0.6rem; margin:0 0 0.5rem 0;"
_h3 = "font-family:'Plus Jakarta Sans',sans-serif; font-weight:700; font-size:1.1rem; color:#252525; margin:0;"
_p = "font-family:'DM Sans',sans-serif; font-size:0.88rem; line-height:1.5; color:#252525; margin:0 0 1rem 0; flex-grow:1;"
_card = "border-radius:24px; padding:1.5rem 1.5rem 1.25rem; display:flex; flex-direction:column; min-height:220px;"

c1, c2, c3 = st.columns(3, gap="medium")

with c1:
    st.markdown(
        f'<div style="background:{COLORS["olive_light"]}; {_card}">'
        f'<div style="{_h}">{ICON_PLAN}<h3 style="{_h3}">Plan My Reno</h3></div>'
        f'<p style="{_p}">Get a personalised checklist covering permits, '
        f'requirements, and key questions for your ID or contractor.</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if st.button("Start planning →", key="nav_plan", type="primary", use_container_width=True):
        st.switch_page("pages/1_Plan_My_Reno.py")

with c2:
    st.markdown(
        f'<div style="background:{COLORS["pink_light"]}; {_card}">'
        f'<div style="{_h}">{ICON_VERIFY}<h3 style="{_h3}">Verify the Advice</h3></div>'
        f'<p style="{_p}">Check claims from your ID or contractor against '
        f'official HDB, SCDF, and BCA sources.</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if st.button("Verify advice →", key="nav_verify", type="primary", use_container_width=True):
        st.switch_page("pages/2_Verify_My_Advice.py")

with c3:
    st.markdown(
        f'<div style="background:{COLORS["blue_light"]}; {_card}">'
        f'<div style="{_h}">{ICON_ASK}<h3 style="{_h3}">Ask RenoBuddy</h3></div>'
        f'<p style="{_p}">Ask any renovation question and get grounded '
        f'answers with citations.</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if st.button("Ask a question →", key="nav_ask", type="primary", use_container_width=True):
        st.switch_page("pages/3_Ask_RenoBuddy.py")

st.markdown("")

st.caption(
    "**Disclaimer:** RenoBuddy provides general guidance based on publicly "
    "available HDB, SCDF, and BCA sources. It does not constitute official "
    "approval, legal advice, or professional consultation. Always confirm "
    "critical decisions with the relevant authority or a licensed professional."
)
