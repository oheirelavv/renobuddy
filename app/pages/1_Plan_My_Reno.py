import re

import streamlit as st

from styles import page_head, COLORS

# --- Session state ---
if "plan_result" not in st.session_state:
    st.session_state.plan_result = None
if "plan_inputs" not in st.session_state:
    st.session_state.plan_inputs = None
if "checklist_state" not in st.session_state:
    st.session_state.checklist_state = {}

CATEGORY_LABELS = {
    "before_reno": "Before renovation",
    "permits": "Permits & approvals",
    "work_requirements": "Work requirements",
    "questions": "Questions for your ID/contractor",
}
CATEGORY_ORDER = ["before_reno", "permits", "work_requirements", "questions"]

# --- Header ---
page_head("Plan My Reno", "Get a personalised renovation plan and interactive checklist.")

# --- Input form ---
col1, col2 = st.columns(2)
with col1:
    flat_type = st.selectbox(
        "Flat type",
        ["— Select —", "BTO", "Resale"],
    )
with col2:
    engagement = st.selectbox(
        "Renovation managed by",
        ["— Select —", "Interior Designer (ID)", "Direct contractor", "Haven't decided yet"],
    )

WORK_OPTIONS = [
    "Wall hacking", "Flooring", "Kitchen", "Bathroom",
    "Windows", "Electrical", "Plumbing", "Air-conditioning", "Not sure yet",
]
works = st.multiselect("Planned works (select all that apply)", WORK_OPTIONS)

if "Not sure yet" in works and len(works) > 1:
    works = [w for w in works if w != "Not sure yet"]
    st.info(
        '"Not sure yet" was removed because you selected specific works. '
        'Select only "Not sure yet" if you haven\'t decided.'
    )

st.caption(
    "**Disclaimer:** RenoBuddy provides general guidance based on publicly "
    "available HDB sources. It does not constitute official approval, legal advice, "
    "or professional consultation."
)

# --- Generate ---
if st.button("Generate my renovation plan", type="primary", use_container_width=True):
    if flat_type == "— Select —":
        st.warning("Please select your flat type.")
    elif engagement == "— Select —":
        st.warning("Please select who is managing your renovation.")
    elif not works:
        st.warning("Please select at least one renovation work.")
    else:
        from utils.config import get_openai_client
        from rag.planner import generate_plan

        client = get_openai_client()
        with st.spinner("Generating your personalised renovation plan..."):
            result = generate_plan(
                openai_client=client,
                flat_type=flat_type,
                engagement=engagement,
                selected_works=works,
            )

        if result["status"] == "success":
            current_inputs = f"{flat_type}|{engagement}|{'|'.join(sorted(works))}"
            prev_inputs = st.session_state.plan_inputs
            if current_inputs != prev_inputs:
                st.session_state.checklist_state = {}
                for key in list(st.session_state.keys()):
                    if key.startswith("cb_"):
                        del st.session_state[key]
            st.session_state.plan_result = result
            st.session_state.plan_inputs = current_inputs
        else:
            st.error("Something went wrong generating your plan. Please try again.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SECTION_STYLES = {
    "renovation summary": (COLORS["olive_light"], "🏠"),
    "summary": (COLORS["olive_light"], "🏠"),
    "important things": (COLORS["pink_light"], "⚠️"),
    "check before": (COLORS["pink_light"], "⚠️"),
    "permits": (COLORS["pink_light"], "⚠️"),
    "restrictions": (COLORS["blue_light"], "🔒"),
    "requirements": (COLORS["blue_light"], "🔧"),
    "official sources": (COLORS["white"], "📎"),
    "sources": (COLORS["white"], "📎"),
    "questions": (COLORS["yellow_light"], "💬"),
}


def _section_style(title: str) -> tuple[str, str]:
    t = title.lower()
    for key, (color, icon) in SECTION_STYLES.items():
        if key in t:
            return color, icon
    return COLORS["white"], ""


def _parse_narrative(plan_md: str) -> list[dict]:
    cleaned = plan_md.strip()
    # Strip PART 1 header
    cleaned = re.sub(
        r"^##\s*PART\s*1[^\n]*\n?", "", cleaned, flags=re.IGNORECASE | re.MULTILINE
    )
    # Strip PART 2 delimiter and everything after (checklist JSON instructions)
    cleaned = re.split(
        r"\n---\s*\n.*PART\s*2|===CHECKLIST_JSON===",
        cleaned,
        maxsplit=1,
        flags=re.IGNORECASE | re.DOTALL,
    )[0]

    parts = re.split(r"^###\s+", cleaned, flags=re.MULTILINE)
    sections = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        lines = part.split("\n", 1)
        title = re.sub(r"^\d+\.\s*", "", lines[0].strip())
        body = lines[1].strip() if len(lines) > 1 else ""
        if not body:
            continue
        color, icon = _section_style(title)
        sections.append({"title": title, "body": body, "color": color, "icon": icon})
    return sections


_SOURCE_LABELS = {
    "building-works": "HDB — Building Works",
    "window-works": "HDB — Window Works",
    "electrical-works": "HDB — Electrical Works",
    "air-conditioner": "HDB — Air-Conditioner Installation",
    "water-and-sanitary": "HDB — Plumbing & Gas Works",
    "registered-contractors": "HDB — Registered Contractors",
    "scdf.gov.sg": "SCDF — Household Shelter Works",
    "qanvast.com": "Qanvast",
}


def _url_label(url: str) -> str:
    for key, label in _SOURCE_LABELS.items():
        if key in url:
            return label
    m = re.match(r"https?://(?:www\.)?([^/]+)", url)
    return m.group(1) if m else url


def _md_to_html(md: str) -> str:
    html = md
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2" target="_blank">\1</a>',
        html,
    )
    html = re.sub(
        r'(?<![="\'/>])(https?://[^\s<>")\]]+)',
        lambda m: f'<a href="{m.group(1)}" target="_blank">{_url_label(m.group(1))}</a>',
        html,
    )

    out_lines = []
    in_list = False
    for line in html.split("\n"):
        stripped = line.strip()
        if stripped.startswith("- "):
            if not in_list:
                out_lines.append("<ul>")
                in_list = True
            out_lines.append(f"<li>{stripped[2:]}</li>")
        else:
            if in_list:
                out_lines.append("</ul>")
                in_list = False
            h_match = re.match(r"^#{4,5}\s+(.+)$", stripped)
            if h_match:
                out_lines.append(
                    f'<h5 class="rb-work-heading">{h_match.group(1)}</h5>'
                )
            elif stripped:
                out_lines.append(f"<p>{stripped}</p>")
    if in_list:
        out_lines.append("</ul>")
    return "\n".join(out_lines)


FLAT_TYPE_TERMS = {
    "BTO": ["BTO flat", "BTO", "new flat"],
    "Resale": ["resale flat", "Resale"],
}

ENGAGEMENT_TERMS = {
    "Interior Designer (ID)": ["interior designer", "Interior Designer"],
    "Direct contractor": ["direct contractor", "contractor"],
    "Haven't decided yet": [],
}


def _highlight_selections(html: str, selections: list[str]) -> str:
    already_wrapped = set()
    for term in sorted(selections, key=len, reverse=True):
        if not term or len(term) < 3:
            continue
        pattern = re.compile(r"(?<![<\w/])\b" + re.escape(term) + r"\b(?![^<]*>)", re.IGNORECASE)
        if term.lower() in already_wrapped:
            continue

        def _wrap(m):
            already_wrapped.add(m.group(0).lower())
            return f'<span class="rb-hl">{m.group(0)}</span>'

        html = pattern.sub(_wrap, html)
    return html


def _get_user_selections() -> list[str]:
    raw = st.session_state.get("plan_inputs", "")
    if not raw:
        return []
    parts = raw.split("|")
    if len(parts) < 2:
        return []
    ft, eng = parts[0].strip(), parts[1].strip()
    work_terms = [p.strip() for p in parts[2:] if p.strip() and p.strip() != "Not sure yet"]

    terms = []
    terms.extend(FLAT_TYPE_TERMS.get(ft, [ft] if ft != "— Select —" else []))
    terms.extend(ENGAGEMENT_TERMS.get(eng, [eng] if eng != "— Select —" else []))
    terms.extend(work_terms)
    return terms


def _get_completed_count(checklist: list[dict]) -> int:
    return sum(
        1
        for item in checklist
        if st.session_state.get(
            f"cb_{item['id']}",
            st.session_state.checklist_state.get(item["id"], False),
        )
    )


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

result = st.session_state.plan_result
if result:
    st.markdown("")

    checklist = result.get("checklist", [])
    total_tasks = len(checklist)
    completed = _get_completed_count(checklist)
    progress_pct = int((completed / total_tasks) * 100) if total_tasks > 0 else 0
    user_selections = _get_user_selections()

    # --- Two-column layout: narrative (65%) | checklist (35%) ---
    narr_col, check_col = st.columns([65, 35], gap="medium")

    # ======= LEFT: Narrative =======
    with narr_col:
        sections = _parse_narrative(result["plan"])

        if sections:
            for sec in sections:
                border = (
                    "border: 1.5px solid #E8E4DA;"
                    if sec["color"] == COLORS["white"]
                    else ""
                )
                icon_html = (
                    f'<span style="margin-right:0.3rem;">{sec["icon"]}</span>'
                    if sec["icon"]
                    else ""
                )
                body_html = _md_to_html(sec["body"])
                is_summary = "summary" in sec["title"].lower()
                if is_summary and user_selections:
                    body_html = _highlight_selections(body_html, user_selections)

                st.markdown(
                    f'<div class="rb-narr-section" style="background-color:{sec["color"]};{border}">'
                    f"<h4>{icon_html}{sec['title']}</h4>"
                    f"{body_html}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(result["plan"])

    # ======= RIGHT: Notepad checklist =======
    with check_col:
        st.markdown('<div class="rb-notepad-wrap">', unsafe_allow_html=True)

        with st.container(border=True):
            # Header
            st.markdown(
                '<div class="rb-notepad-head">'
                '<h3>📝 My reno checklist</h3>'
                f'<span class="rb-notepad-progress">{completed}/{total_tasks}</span>'
                "</div>"
                '<div class="rb-notepad-bar">'
                f'<div class="rb-notepad-bar-fill" style="width:{progress_pct}%;"></div>'
                "</div>",
                unsafe_allow_html=True,
            )

            if checklist:
                grouped = {}
                for item in checklist:
                    cat = item.get("category", "before_reno")
                    grouped.setdefault(cat, []).append(item)

                for cat_key in CATEGORY_ORDER:
                    items = grouped.get(cat_key, [])
                    if not items:
                        continue

                    st.markdown(
                        f'<div class="rb-notepad-cat">'
                        f"{CATEGORY_LABELS.get(cat_key, cat_key)}</div>",
                        unsafe_allow_html=True,
                    )

                    for item in items:
                        task_id = item["id"]
                        cb_key = f"cb_{task_id}"
                        is_critical = item.get("critical", False)
                        label = item["task"]
                        if is_critical:
                            label = f"⚠️ {label}"

                        if cb_key not in st.session_state:
                            st.session_state[cb_key] = (
                                st.session_state.checklist_state.get(task_id, False)
                            )

                        st.checkbox(label, key=cb_key)
                        st.session_state.checklist_state[task_id] = st.session_state[
                            cb_key
                        ]

                        detail = item.get("detail")
                        source_url = item.get("source_url")
                        source_section = item.get("source_section")
                        work_type = item.get("work_type", "")

                        if detail or source_url:
                            with st.expander("Details", expanded=False):
                                parts = []
                                if work_type and work_type != "General":
                                    parts.append(f"**Applies to:** {work_type}")
                                if detail:
                                    parts.append(detail)
                                if source_url and source_section:
                                    parts.append(
                                        f"**Source:** [{source_section}]({source_url})"
                                    )
                                elif source_url:
                                    parts.append(
                                        f"**Source:** [HDB Guidelines]({source_url})"
                                    )
                                st.markdown("  \n".join(parts))

                completed_final = _get_completed_count(checklist)
                if completed_final == total_tasks and total_tasks > 0:
                    st.success(
                        f"**All {total_tasks} tasks completed** — you're ready to renovate!"
                    )

        st.markdown("</div>", unsafe_allow_html=True)

    # --- Plan details ---
    with st.expander("Plan details"):
        st.markdown(f"**Evidence chunks used:** {result['total_chunks']}")
        for work, count in result["evidence_by_work"].items():
            st.markdown(f"- {work}: {count} sources retrieved")
        if result.get("usage"):
            u = result["usage"]
            st.markdown(f"**Tokens used:** {u['total_tokens']:,}")
        st.markdown(f"**Checklist items:** {len(checklist)}")
