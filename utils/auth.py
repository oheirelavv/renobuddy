"""Authentication for RenoBuddy — role-based access with PBKDF2-HMAC-SHA256."""

from __future__ import annotations

import hashlib
import hmac
import os

import streamlit as st

PBKDF2_ITERATIONS = 260_000


def _hash_password(password: str, salt: bytes) -> str:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return salt.hex() + ":" + dk.hex()


def _verify_password(password: str, stored: str) -> bool:
    if ":" not in stored:
        return False
    salt_hex, hash_hex = stored.split(":", 1)
    try:
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return hmac.compare_digest(dk.hex(), hash_hex)


def hash_new_password(password: str) -> str:
    salt = os.urandom(16)
    return _hash_password(password, salt)


def _get_accounts() -> dict[str, tuple[str, str]]:
    try:
        auth = st.secrets.get("auth", {})
    except FileNotFoundError:
        return {}
    accounts = {}
    if auth.get("admin_username") and auth.get("admin_password_hash"):
        accounts[auth["admin_username"]] = ("admin", auth["admin_password_hash"])
    if auth.get("user_username") and auth.get("user_password_hash"):
        accounts[auth["user_username"]] = ("user", auth["user_password_hash"])
    return accounts


def check_password(username: str, password: str) -> str | None:
    accounts = _get_accounts()
    if username not in accounts:
        return None
    role, stored = accounts[username]
    if _verify_password(password, stored):
        return role
    return None


def require_auth() -> str:
    if "auth_role" in st.session_state and st.session_state.auth_role:
        return st.session_state.auth_role

    accounts = _get_accounts()
    if not accounts:
        st.error(
            "**Authentication not configured.** "
            "Run `python setup_auth.py` to create `.streamlit/secrets.toml`, "
            "then restart the app."
        )
        st.stop()

    st.markdown(
        "<style>"
        "[data-testid='stSidebar'],"
        "[data-testid='stSidebarCollapsedControl']"
        "{ display: none !important; }"
        ".stApp .block-container {"
        "  max-width: 420px !important;"
        "  display: flex; flex-direction: column;"
        "  align-items: center; justify-content: center;"
        "  min-height: 85vh;"
        "}"
        "</style>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="max-width:400px; margin:0 auto; text-align:center;">'
        '<p style="font-size:1.5rem; margin-bottom:0.25rem;">🏠</p>'
        "<h2 style=\"font-family:'Plus Jakarta Sans',sans-serif; font-size:1.4rem; "
        'font-weight:800; color:#252525; margin:0 0 0.25rem;">RenoBuddy</h2>'
        "<p style=\"font-family:'DM Sans',sans-serif; font-size:0.85rem; "
        'color:#858585; margin:0 0 1.5rem;">Sign in to continue</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)

    if submitted:
        role = check_password(username.strip(), password)
        if role:
            st.session_state.auth_role = role
            st.session_state.auth_user = username.strip()
            st.rerun()
        else:
            st.error("Invalid username or password.")

    st.stop()


def require_admin():
    role = require_auth()
    if role != "admin":
        st.error("Admin access required.")
        st.stop()
    return role


def logout():
    for key in ["auth_role", "auth_user"]:
        if key in st.session_state:
            del st.session_state[key]
