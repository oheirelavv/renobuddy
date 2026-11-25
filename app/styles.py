"""RenoBuddy Design System — dashboard-style UI with pastel colour palette."""

import streamlit as st

COLORS = {
    "ivory": "#FBF3E6",
    "olive": "#9DAE68",
    "pink": "#F78FD2",
    "blue": "#B4C9EB",
    "yellow": "#F7DB69",
    "white": "#FFFFFF",
    "charcoal": "#252525",
    "grey": "#858585",
    "olive_light": "#E8EDDA",
    "pink_light": "#FDE8F6",
    "blue_light": "#E8F0FA",
    "yellow_light": "#FDF5D9",
    "red_light": "#FDDEDE",
}

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=DM+Sans:wght@400;500;600&display=swap');

:root {
    --ivory: #FBF3E6;
    --olive: #9DAE68;
    --pink: #F78FD2;
    --blue: #B4C9EB;
    --yellow: #F7DB69;
    --white: #FFFFFF;
    --charcoal: #252525;
    --grey: #858585;
    --olive-light: #E8EDDA;
    --pink-light: #FDE8F6;
    --blue-light: #E8F0FA;
    --yellow-light: #FDF5D9;
    --border: #E8E4DA;
    --radius: 24px;
    --radius-sm: 14px;
    --radius-xs: 10px;
    --font-heading: 'Plus Jakarta Sans', sans-serif;
    --font-body: 'DM Sans', sans-serif;
}

/* ============ BASE ============ */
.stApp {
    background-color: var(--ivory);
    font-family: var(--font-body);
}
.stApp [data-testid="stHeader"] {
    background-color: var(--ivory);
}
.stApp .block-container {
    max-width: 1300px;
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* ============ SIDEBAR ============ */
[data-testid="stSidebar"] {
    background-color: var(--white);
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem;
}
[data-testid="stSidebar"] [data-testid="stMarkdown"] p,
[data-testid="stSidebar"] [data-testid="stMarkdown"] span,
[data-testid="stSidebar"] a {
    font-family: var(--font-heading);
    font-size: 0.9rem;
    color: var(--charcoal);
}

/* --- st.navigation section headers (10px, muted, understated) --- */
[data-testid="stSidebarNav"] h2,
[data-testid="stSidebarNav"] [data-testid="stHeaderNoPadding"],
[data-testid="stSidebarNav"] span[data-testid="stNavigationLabel"] {
    font-family: var(--font-heading) !important;
    font-size: 10px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: var(--grey) !important;
    padding: 0.5rem 0.75rem 0.2rem 0.75rem;
    margin: 0;
    line-height: 1.4;
}

/* --- Navigation items --- */
[data-testid="stSidebarNav"] li a,
[data-testid="stSidebarNav"] a[data-testid="stSidebarNavLink"] {
    border-radius: var(--radius-xs);
    padding: 0.5rem 0.75rem;
    margin-bottom: 1px;
    font-family: var(--font-heading);
    font-size: 0.88rem;
    font-weight: 500;
    color: var(--charcoal);
    transition: background-color 0.15s ease;
    white-space: normal !important;
    height: auto !important;
    line-height: 1.4;
    align-items: flex-start;
}
[data-testid="stSidebarNav"] li a span,
[data-testid="stSidebarNav"] a[data-testid="stSidebarNavLink"] span {
    white-space: normal !important;
}
[data-testid="stSidebarNav"] li a:hover,
[data-testid="stSidebarNav"] a[data-testid="stSidebarNavLink"]:hover {
    background-color: var(--yellow-light);
}
[data-testid="stSidebarNav"] li a[aria-current="page"],
[data-testid="stSidebarNav"] a[data-testid="stSidebarNavLink"][aria-selected="true"],
[data-testid="stSidebarNav"] a[data-testid="stSidebarNavLink"].st-emotion-cache-active {
    background-color: var(--yellow-light) !important;
    font-weight: 600;
}

/* --- Nav icons: monochrome outline, 20px --- */
[data-testid="stSidebarNav"] li a span[data-testid="stIconMaterial"],
[data-testid="stSidebarNav"] a .material-symbols-outlined,
[data-testid="stSidebarNav"] a span.material-icons-outlined,
[data-testid="stSidebarNav"] a .icon {
    font-size: 20px !important;
    color: var(--grey);
    font-variation-settings: 'FILL' 0, 'wght' 200, 'GRAD' 0, 'opsz' 20;
}
[data-testid="stSidebarNav"] li a[aria-current="page"] span[data-testid="stIconMaterial"],
[data-testid="stSidebarNav"] li a[aria-current="page"] .material-symbols-outlined,
[data-testid="stSidebarNav"] a[aria-selected="true"] span[data-testid="stIconMaterial"],
[data-testid="stSidebarNav"] a[aria-selected="true"] .material-symbols-outlined {
    color: var(--charcoal);
    font-variation-settings: 'FILL' 0, 'wght' 250, 'GRAD' 0, 'opsz' 20;
}

/* --- Grey divider between nav sections --- */
[data-testid="stSidebarNav"] > ul + h2,
[data-testid="stSidebarNav"] > div + div > h2,
[data-testid="stSidebarNav"] > ul + [data-testid="stHeaderNoPadding"],
[data-testid="stSidebarNav"] > div:not(:first-child) > h2,
[data-testid="stSidebarNav"] > div:not(:first-child) > [data-testid="stHeaderNoPadding"] {
    margin-top: 0.65rem;
    padding-top: 0.75rem;
    border-top: 1px solid #D9D9D9;
}

/* ============ TYPOGRAPHY ============ */
.stApp h1 {
    font-family: var(--font-heading) !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
    color: var(--charcoal) !important;
    letter-spacing: -0.02em;
}
.stApp h2 {
    font-family: var(--font-heading) !important;
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    color: var(--charcoal) !important;
}
.stApp h3 {
    font-family: var(--font-heading) !important;
    font-size: 1.2rem !important;
    font-weight: 700 !important;
    color: var(--charcoal) !important;
}
.stApp h4 {
    font-family: var(--font-heading) !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    color: var(--charcoal) !important;
}
.stApp p, .stApp li {
    font-family: var(--font-body);
    font-size: 0.95rem;
    line-height: 1.6;
    color: var(--charcoal);
}

/* ============ BUTTONS ============ */
.stButton > button {
    font-family: var(--font-heading);
    border-radius: var(--radius-sm);
    font-weight: 600;
    font-size: 0.9rem;
    border: none;
    padding: 0.6rem 1.5rem;
    transition: all 0.2s ease;
    white-space: normal !important;
    word-wrap: break-word !important;
    height: auto !important;
    min-height: 2.5rem;
    text-align: left;
    line-height: 1.4;
}
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
    background-color: var(--yellow) !important;
    color: var(--charcoal) !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {
    background-color: #E5C94F !important;
    transform: translateY(-1px);
}
.stButton > button[kind="secondary"],
.stButton > button[data-testid="stBaseButton-secondary"] {
    background-color: var(--white) !important;
    color: var(--charcoal) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
}
.stButton > button[kind="secondary"]:hover,
.stButton > button[data-testid="stBaseButton-secondary"]:hover {
    background-color: var(--yellow-light) !important;
    border-color: var(--yellow) !important;
}

/* ============ INPUTS ============ */
[data-testid="stSelectbox"] label,
[data-testid="stMultiSelect"] label,
.stTextArea label {
    font-family: var(--font-heading);
    font-weight: 600;
    font-size: 0.85rem;
    color: var(--charcoal);
}
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div,
.stTextArea textarea {
    background-color: var(--white);
    border: 1.5px solid var(--border);
    border-radius: var(--radius-xs);
    font-family: var(--font-body);
    color: var(--charcoal);
}
[data-testid="stSelectbox"] > div > div:focus-within,
[data-testid="stMultiSelect"] > div > div:focus-within,
.stTextArea textarea:focus {
    border-color: var(--olive) !important;
    box-shadow: 0 0 0 2px rgba(157,174,104,0.15);
}

/* ============ PROGRESS BAR ============ */
.stProgress > div > div > div {
    background-color: var(--olive);
    border-radius: 20px;
}
.stProgress > div > div {
    background-color: var(--olive-light);
    border-radius: 20px;
    height: 8px;
}

/* ============ EXPANDERS ============ */
[data-testid="stExpander"] {
    background-color: var(--white);
    border: 1.5px solid var(--border);
    border-radius: var(--radius) !important;
    overflow: hidden;
}
[data-testid="stExpander"] summary {
    font-family: var(--font-heading);
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--charcoal);
}

/* ============ CHECKBOXES ============ */
[data-testid="stCheckbox"] label span {
    font-family: var(--font-body);
    color: var(--charcoal);
}

/* ============ DIVIDERS ============ */
.stApp hr {
    border-color: var(--border);
    opacity: 0.5;
    margin: 1rem 0;
}

/* ============ ALERTS ============ */
[data-testid="stAlert"] {
    border-radius: var(--radius-sm);
    font-family: var(--font-body);
}

/* ============ CAPTIONS ============ */
.stCaption, [data-testid="stCaption"] {
    color: var(--grey) !important;
    font-family: var(--font-body);
    font-size: 0.8rem !important;
}

/* ============ CUSTOM CLASSES ============ */

/* --- Cards --- */
.rb-card {
    padding: 1.75rem;
    border-radius: var(--radius);
    margin-bottom: 0.75rem;
}
.rb-card h3 {
    font-family: var(--font-heading);
    font-size: 1.15rem;
    font-weight: 700;
    margin: 0 0 0.5rem 0;
    color: var(--charcoal);
}
.rb-card p {
    font-family: var(--font-body);
    margin: 0;
    font-size: 0.9rem;
    line-height: 1.55;
    color: var(--charcoal);
}
.rb-card-olive { background-color: var(--olive-light); }
.rb-card-pink { background-color: var(--pink-light); }
.rb-card-blue { background-color: var(--blue-light); }
.rb-card-yellow { background-color: var(--yellow-light); }
.rb-card-white {
    background-color: var(--white);
    border: 1.5px solid var(--border);
}

/* --- Large feature cards --- */
.rb-feature {
    padding: 2rem;
    border-radius: var(--radius);
    min-height: 200px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.rb-feature .icon {
    font-size: 2rem;
    margin-bottom: 0.75rem;
}
.rb-feature h3 {
    font-family: var(--font-heading);
    font-size: 1.25rem;
    font-weight: 700;
    margin: 0 0 0.5rem 0;
    color: var(--charcoal);
}
.rb-feature p {
    font-family: var(--font-body);
    font-size: 0.9rem;
    line-height: 1.5;
    color: var(--charcoal);
    margin: 0 0 1rem 0;
    flex-grow: 1;
}
.rb-feature .rb-btn {
    display: inline-block;
    padding: 0.5rem 1.25rem;
    border-radius: var(--radius-xs);
    font-family: var(--font-heading);
    font-weight: 600;
    font-size: 0.85rem;
    text-decoration: none;
    color: var(--charcoal);
    background-color: rgba(255,255,255,0.6);
    border: none;
    cursor: pointer;
    transition: background-color 0.15s;
}
.rb-feature .rb-btn:hover {
    background-color: rgba(255,255,255,0.9);
}

/* --- Metric cards --- */
.rb-metric {
    background-color: var(--white);
    border: 1.5px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    text-align: center;
}
.rb-metric .value {
    font-family: var(--font-heading);
    font-size: 2.25rem;
    font-weight: 800;
    color: var(--charcoal);
    line-height: 1.1;
}
.rb-metric .label {
    font-family: var(--font-body);
    font-size: 0.82rem;
    color: var(--grey);
    margin-top: 0.35rem;
}

/* --- Progress ring --- */
.rb-progress-ring {
    width: 140px;
    height: 140px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto;
}
.rb-progress-ring .inner {
    width: 105px;
    height: 105px;
    border-radius: 50%;
    background: var(--white);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
}
.rb-progress-ring .inner .pct {
    font-family: var(--font-heading);
    font-size: 1.75rem;
    font-weight: 800;
    color: var(--charcoal);
    line-height: 1;
}
.rb-progress-ring .inner .pct-label {
    font-family: var(--font-body);
    font-size: 0.7rem;
    color: var(--grey);
    margin-top: 2px;
}

/* --- Progress dashboard card --- */
.rb-progress-dash {
    background-color: var(--olive-light);
    border-radius: var(--radius);
    padding: 2rem;
    display: flex;
    align-items: center;
    gap: 2rem;
}
.rb-progress-dash .info h3 {
    font-family: var(--font-heading);
    font-size: 1.3rem;
    font-weight: 700;
    margin: 0 0 0.35rem 0;
}
.rb-progress-dash .info p {
    font-family: var(--font-body);
    font-size: 0.9rem;
    color: var(--grey);
    margin: 0;
}

/* --- Category headers --- */
.rb-category-header {
    padding: 0.65rem 1.1rem;
    border-radius: var(--radius-sm);
    font-family: var(--font-heading);
    font-weight: 600;
    font-size: 0.92rem;
    margin: 1.5rem 0 0.75rem 0;
    color: var(--charcoal);
}

/* --- Checklist items --- */
.rb-checklist-item {
    background-color: var(--white);
    border: 1.5px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 0.5rem 0.85rem;
    margin-bottom: 0.5rem;
    border-left: 4px solid var(--olive);
}
.rb-checklist-item-critical {
    border-left-color: var(--yellow);
    background-color: var(--yellow-light);
}

/* --- Badges --- */
.rb-badge {
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 20px;
    font-family: var(--font-heading);
    font-size: 0.72rem;
    font-weight: 600;
}
.rb-badge-olive { background-color: var(--olive-light); color: #5D6E2E; }
.rb-badge-pink { background-color: var(--pink-light); color: #9E3D82; }
.rb-badge-blue { background-color: var(--blue-light); color: #4A6B94; }
.rb-badge-yellow { background-color: var(--yellow-light); color: #8B7420; }
.rb-badge-grey { background-color: #F0EDEA; color: var(--grey); }

/* --- Verdict badges --- */
.rb-verdict {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 1rem;
    border-radius: 20px;
    font-family: var(--font-heading);
    font-weight: 600;
    font-size: 0.88rem;
}
.rb-verdict-supported { background-color: var(--olive-light); color: #5D6E2E; }
.rb-verdict-contradicted { background-color: #FDDEDE; color: #8B2020; }
.rb-verdict-partial { background-color: var(--yellow-light); color: #8B7420; }
.rb-verdict-unverified { background-color: var(--blue-light); color: #4A6B94; }

/* --- Claim cards --- */
.rb-claim-card {
    background-color: var(--white);
    border: 1.5px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.rb-claim-card h4 {
    font-family: var(--font-heading);
    margin: 0 0 0.75rem 0;
}
.rb-claim-card .told {
    font-family: var(--font-body);
    font-size: 0.9rem;
    color: var(--grey);
    margin-bottom: 0.75rem;
    padding: 0.6rem 0.9rem;
    background: var(--ivory);
    border-radius: var(--radius-xs);
}
.rb-claim-card .means {
    font-family: var(--font-body);
    font-size: 0.9rem;
    margin: 0.75rem 0 0 0;
}

/* --- Page heading --- */
.rb-page-head {
    margin-bottom: 1.25rem;
}
.rb-page-head h1 {
    font-family: var(--font-heading);
    font-size: 1.75rem;
    font-weight: 800;
    color: var(--charcoal);
    margin: 0;
}
.rb-page-head p {
    font-family: var(--font-body);
    font-size: 0.92rem;
    color: var(--grey);
    margin: 0.25rem 0 0 0;
}

/* --- Info card for About / Methodology --- */
.rb-info-card {
    border-radius: var(--radius);
    padding: 1.75rem;
    margin-bottom: 1rem;
}
.rb-info-card h3 {
    font-family: var(--font-heading);
    font-size: 1.1rem;
    font-weight: 700;
    margin: 0 0 0.6rem 0;
}
.rb-info-card p, .rb-info-card li {
    font-family: var(--font-body);
    font-size: 0.9rem;
    line-height: 1.6;
}
.rb-info-card ul {
    padding-left: 1.2rem;
    margin: 0.4rem 0;
}

/* --- Flow step --- */
.rb-flow-step {
    display: flex;
    align-items: flex-start;
    gap: 0.9rem;
    margin-bottom: 1rem;
}
.rb-flow-num {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: var(--font-heading);
    font-weight: 700;
    font-size: 0.85rem;
    flex-shrink: 0;
    color: var(--charcoal);
}
.rb-flow-step .text h4 {
    font-family: var(--font-heading);
    font-size: 0.95rem;
    font-weight: 600;
    margin: 0 0 0.2rem 0;
}
.rb-flow-step .text p {
    font-size: 0.85rem;
    color: var(--grey);
    margin: 0;
}

/* ============ MESSAGING APP ============ */

/* --- Keyed chat container: force white on every layer --- */
.st-key-renobuddy_chat,
.st-key-renobuddy_chat > div,
.st-key-renobuddy_chat [data-testid="stVerticalBlockBorderWrapper"],
.st-key-renobuddy_chat [data-testid="stVerticalBlockBorderWrapper"] > div,
.st-key-renobuddy_chat [data-testid="stVerticalBlock"],
.st-key-renobuddy_chat [data-testid="stScrollableBlock"] {
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
}
.st-key-renobuddy_chat > [data-testid="stVerticalBlockBorderWrapper"] {
    border: 1.5px solid #E5E5E5 !important;
    border-radius: 24px !important;
}

/* --- Chat header --- */
.rb-msg-header {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    padding: 0.5rem 0;
}
.rb-msg-avatar {
    width: 36px; height: 36px; border-radius: 50%;
    background: var(--ivory);
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.rb-msg-header .info h3 {
    font-family: var(--font-heading);
    font-size: 0.95rem; font-weight: 700;
    color: var(--charcoal); margin: 0; line-height: 1.2;
}
.rb-msg-header .info p {
    font-family: var(--font-body);
    font-size: 0.72rem; color: var(--grey); margin: 0;
}

/* --- Remove inner borders on nested containers inside chat --- */
/* The conversation st.container(height=N) generates a bordered wrapper */
[data-testid="stVerticalBlockBorderWrapper"]
  [data-testid="stVerticalBlockBorderWrapper"] {
    border: none !important;
    border-radius: 0 !important;
    background: var(--white) !important;
}

/* --- Message bubbles --- */
[data-testid="stChatMessage"] {
    font-family: var(--font-body);
    font-size: 0.9rem;
    padding: 0.7rem 1rem;
    max-width: 80%;
    box-shadow: none !important;
    border: none !important;
}
[data-testid="stChatMessage"][data-testid-role="user"] {
    background: var(--blue-light) !important;
    border-radius: 18px 18px 4px 18px !important;
    margin-left: auto;
}
[data-testid="stChatMessage"][data-testid-role="assistant"] {
    background: #F3F3F0 !important;
    border-radius: 18px 18px 18px 4px !important;
}

/* --- Welcome state --- */
.rb-chat-welcome {
    text-align: center;
    padding: 2.5rem 1.5rem 0.75rem;
}
.rb-chat-welcome h3 {
    font-family: var(--font-heading);
    font-size: 1.05rem; font-weight: 700;
    color: var(--charcoal); margin: 0.4rem 0 0.25rem;
}
.rb-chat-welcome p {
    font-family: var(--font-body);
    font-size: 0.84rem; color: var(--grey);
    margin: 0 auto 1rem; max-width: 380px;
}

/* --- Suggestion chips --- */
.rb-suggest {
    background-color: var(--white);
    border: 1.5px solid var(--border);
    border-radius: 20px;
    padding: 0.5rem 1rem;
    font-family: var(--font-body);
    font-size: 0.82rem;
    color: var(--charcoal);
    cursor: pointer;
    transition: background-color 0.15s;
    margin-bottom: 0.35rem;
}
.rb-suggest:hover { background-color: var(--blue-light); }

/* --- Narrative section cards --- */
.rb-narrative-wrap {
    background: var(--white);
    border-radius: var(--radius);
    border: 1.5px solid var(--border);
    padding: 1.5rem;
}
.rb-narr-section {
    border-radius: var(--radius-sm);
    padding: 1.25rem 1.35rem;
    margin-bottom: 0.75rem;
}
.rb-narr-section:last-child { margin-bottom: 0; }
.rb-narr-section h4 {
    font-family: var(--font-heading);
    font-size: 0.95rem;
    font-weight: 700;
    margin: 0 0 0.6rem 0;
    color: var(--charcoal);
}
.rb-narr-section p,
.rb-narr-section li {
    font-family: var(--font-body);
    font-size: 0.88rem;
    line-height: 1.6;
    color: var(--charcoal);
}
.rb-narr-section ul { padding-left: 1.2rem; margin: 0.3rem 0; }
.rb-narr-section a { color: #4A6B94; text-decoration: underline; }

/* --- Work type headings within narrative sections --- */
.rb-narr-section h5.rb-work-heading {
    font-family: var(--font-heading);
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--charcoal);
    margin: 1.25rem 0 0.5rem 0;
    padding-top: 0.75rem;
    border-top: 1px solid #D1DCEB;
}
.rb-narr-section h5.rb-work-heading:first-of-type {
    margin-top: 0.25rem;
    border-top: none;
    padding-top: 0;
}

/* --- Notepad checklist --- */
.rb-notepad {
    background: #FEFCF7;
    border-radius: var(--radius);
    border: 1.5px solid var(--border);
    padding: 1.25rem 1.35rem;
}
.rb-notepad-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.75rem;
    padding-bottom: 0.65rem;
    border-bottom: 1.5px solid var(--border);
}
.rb-notepad-head h3 {
    font-family: var(--font-heading);
    font-size: 1rem;
    font-weight: 700;
    margin: 0;
    color: var(--charcoal);
}
.rb-notepad-progress {
    font-family: var(--font-heading);
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--grey);
}
.rb-notepad-bar {
    height: 6px;
    border-radius: 3px;
    background: var(--olive-light);
    margin-bottom: 1rem;
    overflow: hidden;
}
.rb-notepad-bar-fill {
    height: 100%;
    border-radius: 3px;
    background: var(--olive);
    transition: width 0.3s ease;
}
.rb-notepad-cat {
    font-family: var(--font-heading);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--grey);
    margin: 0.9rem 0 0.35rem 0;
    padding: 0;
}

/* Notepad container override — style the st.container(border=True) wrapper */
.rb-notepad-wrap [data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF !important;
    border-radius: var(--radius) !important;
    border: 1.5px solid var(--border) !important;
    padding: 0.25rem 0.5rem !important;
}
/* Task dividers inside notepad */
.rb-notepad-wrap [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCheckbox"] {
    border-bottom: 1px solid #E5E5E5;
    padding-bottom: 0.35rem;
    margin-bottom: 0.15rem;
}
/* Strikethrough for checked tasks */
.rb-notepad-wrap [data-testid="stCheckbox"] input:checked + label span {
    text-decoration: line-through;
    color: var(--grey);
}

/* Highlight tag for personalised info */
.rb-hl {
    font-weight: 700;
    text-decoration: underline;
    text-decoration-color: var(--yellow);
    text-underline-offset: 2px;
    text-decoration-thickness: 2px;
}

/* ============ LOGOUT BUTTON ============ */
.st-key-logout_btn {
    margin-top: 0.5rem;
    padding-top: 0.75rem;
    border-top: 1px solid #D9D9D9;
}
.st-key-logout_btn button {
    background-color: transparent !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-xs) !important;
    font-family: var(--font-heading) !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    color: var(--charcoal) !important;
    padding: 0.5rem 0.75rem !important;
    min-height: auto !important;
    height: auto !important;
}
.st-key-logout_btn button:hover {
    background-color: var(--yellow-light) !important;
    border-color: var(--yellow) !important;
}
.st-key-logout_btn button span[data-testid="stIconMaterial"] {
    font-size: 20px !important;
    color: var(--grey) !important;
    font-variation-settings: 'FILL' 0, 'wght' 200, 'GRAD' 0, 'opsz' 20 !important;
}

/* ============ RESPONSIVE ============ */
@media (max-width: 768px) {
    .rb-feature { min-height: auto; padding: 1.5rem; }
    .rb-progress-dash { flex-direction: column; text-align: center; }
    .rb-progress-ring { width: 110px; height: 110px; }
    .rb-progress-ring .inner { width: 82px; height: 82px; }
}
</style>
"""


def inject_styles():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def page_head(title: str, subtitle: str = ""):
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f'<div class="rb-page-head"><h1>{title}</h1>{sub}</div>',
        unsafe_allow_html=True,
    )


def render_card(title: str, body: str, color: str = "white", icon: str = "") -> str:
    icon_html = f'<span style="font-size:1.4rem;margin-right:0.35rem">{icon}</span>' if icon else ""
    return (
        f'<div class="rb-card rb-card-{color}">'
        f"<h3>{icon_html}{title}</h3>"
        f"<p>{body}</p>"
        f"</div>"
    )


def render_feature_card(
    title: str, body: str, color: str, icon: str, btn_label: str = "", btn_page: str = "",
) -> str:
    btn = ""
    if btn_label:
        btn = f'<span class="rb-btn">{btn_label} →</span>'
    return (
        f'<div class="rb-feature" style="background-color: {color};">'
        f'<div><div class="icon">{icon}</div>'
        f"<h3>{title}</h3>"
        f"<p>{body}</p></div>"
        f"{btn}"
        f"</div>"
    )


def render_metric_card(value: str, label: str, accent: str = "") -> str:
    top = f"border-top: 3px solid {accent};" if accent else ""
    return (
        f'<div class="rb-metric" style="{top}">'
        f'<div class="value">{value}</div>'
        f'<div class="label">{label}</div>'
        f"</div>"
    )


def render_progress_ring(percent: int, color: str = "#9DAE68") -> str:
    deg = int(percent * 3.6)
    bg = f"conic-gradient({color} {deg}deg, #E8E4DA {deg}deg)"
    return (
        f'<div class="rb-progress-ring" style="background: {bg};">'
        f'<div class="inner">'
        f'<span class="pct">{percent}%</span>'
        f'<span class="pct-label">complete</span>'
        f"</div></div>"
    )


def render_progress_dashboard(percent: int, completed: int, total: int) -> str:
    deg = int(percent * 3.6)
    bg = f"conic-gradient(#9DAE68 {deg}deg, #E8E4DA {deg}deg)"
    if percent == 100:
        msg = "All done — you're ready to renovate!"
    elif percent >= 60:
        msg = "You're making good progress."
    elif percent > 0:
        msg = "Keep going — check off tasks as you complete them."
    else:
        msg = "Start checking off tasks to track your progress."
    return (
        f'<div class="rb-progress-dash">'
        f'<div class="rb-progress-ring" style="background: {bg};">'
        f'<div class="inner">'
        f'<span class="pct">{percent}%</span>'
        f'<span class="pct-label">complete</span>'
        f"</div></div>"
        f'<div class="info">'
        f"<h3>Overall progress</h3>"
        f"<p>{completed} of {total} tasks completed — {msg}</p>"
        f"</div></div>"
    )


def render_verdict_badge(verdict: str, icon: str = "") -> str:
    cls_map = {
        "Supported": "rb-verdict-supported",
        "Contradicted": "rb-verdict-contradicted",
        "Partially supported": "rb-verdict-partial",
        "Unable to verify": "rb-verdict-unverified",
    }
    cls = cls_map.get(verdict, "rb-verdict-unverified")
    return f'<span class="rb-verdict {cls}">{icon} {verdict}</span>'


def render_category_header(label: str, color: str) -> str:
    return f'<div class="rb-category-header" style="background-color: {color};">{label}</div>'


def render_info_card(title: str, body_html: str, color: str) -> str:
    title_html = f"<h3>{title}</h3>" if title else ""
    return (
        f'<div class="rb-info-card" style="background-color: {color};">'
        f"{title_html}{body_html}</div>"
    )


def render_flow_step(num: int, title: str, desc: str, color: str) -> str:
    return (
        f'<div class="rb-flow-step">'
        f'<div class="rb-flow-num" style="background-color: {color};">{num}</div>'
        f'<div class="text"><h4>{title}</h4><p>{desc}</p></div>'
        f"</div>"
    )
