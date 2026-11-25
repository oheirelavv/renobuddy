import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

st.set_page_config(
    page_title="RenoBuddy",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

from styles import inject_styles
from utils.auth import require_auth, logout

# --- Authentication gate ---
role = require_auth()

# --- Role-based navigation ---
nav = {
    "Your renovation journey": [
        st.Page("pages/0_Welcome.py", title="Home", icon=":material/home:", default=True),
        st.Page("pages/1_Plan_My_Reno.py", title="Plan My Reno", icon=":material/checklist:"),
        st.Page("pages/2_Verify_My_Advice.py", title="Verify the Advice", icon=":material/verified_user:"),
        st.Page("pages/3_Ask_RenoBuddy.py", title="Ask RenoBuddy", icon=":material/chat_bubble_outline:"),
    ],
    "Learn more": [
        st.Page("pages/4_About_Us.py", title="About Us", icon=":material/info:"),
        st.Page("pages/5_Methodology.py", title="Methodology", icon=":material/menu_book:"),
    ],
}

if role == "admin":
    nav["Administration"] = [
        st.Page("pages/6_Manage_KB.py", title="Manage Knowledge Base", icon=":material/database:"),
    ]

pg = st.navigation(nav)

# --- Sidebar ---
with st.sidebar:
    st.markdown(
        '<p style="font-family: \'Plus Jakarta Sans\', sans-serif; font-weight: 800; '
        'font-size: 1.3rem; color: #252525; margin-bottom: 0; padding: 0.25rem 0.75rem;">🏠 RenoBuddy</p>'
        '<p style="font-family: \'DM Sans\', sans-serif; font-size: 0.78rem; '
        'color: #858585; margin-top: 0; padding: 0 0.75rem 0.5rem 0.75rem;">HDB renovation assistant</p>',
        unsafe_allow_html=True,
    )

    user_label = st.session_state.get("auth_user", "")
    if user_label:
        st.caption(f"Signed in as **{user_label}**")
        if st.button("Log out", key="logout_btn", icon=":material/logout:", use_container_width=True):
            logout()
            st.rerun()

inject_styles()

pg.run()
