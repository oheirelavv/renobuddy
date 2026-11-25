import streamlit as st

from styles import COLORS

# --- Session state ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

SUGGESTIONS = [
    "Can I hack a wall in my HDB flat?",
    "Do I need a permit to replace my windows?",
    "What are the rules for household shelters?",
    "Can I install a bathtub in my HDB bathroom?",
]

ICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" '
    'fill="none" stroke="#252525" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22z"/></svg>'
)

# ── One unified chat window ─────────────────────────────
with st.container(key="renobuddy_chat", border=True):

    # ── Header with New Chat ──
    hdr_left, hdr_right = st.columns([5, 1])
    with hdr_left:
        st.markdown(
            f'<div class="rb-msg-header">'
            f'<div class="rb-msg-avatar">{ICON_SVG}</div>'
            f'<div class="info"><h3>Ask RenoBuddy</h3>'
            f'<p>Your renovation assistant</p></div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with hdr_right:
        if st.session_state.chat_history:
            if st.button("＋ New Chat", key="new_chat", type="secondary", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

    # ── Conversation area (scrollable) ──
    msg_area = st.container(height=460)

    with msg_area:
        if not st.session_state.chat_history:
            st.markdown(
                '<div class="rb-chat-welcome">'
                '<p style="font-size:1.5rem; margin:0;">🏠</p>'
                '<h3>How can I help with your renovation?</h3>'
                '<p>Ask me about HDB renovation rules, permits, '
                'restrictions, or contractor requirements.</p>'
                '</div>',
                unsafe_allow_html=True,
            )

            cols = st.columns(2)
            for i, q in enumerate(SUGGESTIONS):
                with cols[i % 2]:
                    if st.button(q, key=f"suggest_{i}", use_container_width=True):
                        st.session_state.chat_history.append({"role": "user", "content": q})
                        st.rerun()
        else:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    with st.chat_message("user"):
                        st.markdown(msg["content"])
                else:
                    with st.chat_message("assistant", avatar="🏠"):
                        st.markdown(msg["content"])

                    msg_status = msg.get("status", "success")
                    if msg is st.session_state.chat_history[-1]:
                        if msg_status == "recommend_planning":
                            if st.button("Go to Plan My Reno →", key="rec_plan", type="primary"):
                                st.switch_page("pages/1_Plan_My_Reno.py")
                        elif msg_status == "recommend_verification":
                            rec_text = msg.get("recommend_text", "")
                            if rec_text:
                                st.session_state.verify_input = rec_text
                            if st.button("Go to Verify the Advice →", key="rec_verify", type="primary"):
                                st.switch_page("pages/2_Verify_My_Advice.py")

                    follow_ups = msg.get("follow_ups", [])
                    if follow_ups and msg is st.session_state.chat_history[-1]:
                        fu_cols = st.columns(min(len(follow_ups), 3))
                        for j, fu in enumerate(follow_ups):
                            with fu_cols[j]:
                                if st.button(fu, key=f"fu_{j}_{len(st.session_state.chat_history)}", use_container_width=True):
                                    st.session_state.chat_history.append({"role": "user", "content": fu})
                                    st.rerun()

            if st.session_state.chat_history[-1]["role"] == "user":
                user_msg = st.session_state.chat_history[-1]["content"]
                prior = st.session_state.chat_history[:-1]

                with st.chat_message("assistant", avatar="🏠"):
                    with st.spinner("Searching official sources..."):
                        from utils.config import get_openai_client
                        from rag.chatbot import chat

                        client = get_openai_client()
                        result = chat(client, user_msg, prior)

                    st.markdown(result["answer"])

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": result["answer"],
                    "follow_ups": result.get("follow_ups", []),
                    "status": result.get("status", "success"),
                    "recommend_text": result.get("recommend_text", ""),
                })
                st.rerun()

    # ── Composer (inline inside the same container) ──
    if prompt := st.chat_input("Ask a renovation question...", key="chat_composer"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.rerun()

st.caption(
    "**Disclaimer:** RenoBuddy provides general guidance based on publicly "
    "available HDB, SCDF, and BCA sources. It does not constitute official "
    "approval, legal advice, or professional consultation."
)
