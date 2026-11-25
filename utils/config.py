"""Application configuration and API client setup."""

import os
import streamlit as st
from openai import OpenAI

LLM_MODEL = "gpt-4.1-mini"
EMBEDDING_MODEL = "text-embedding-3-small"

def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
    if not api_key:
        st.error("OpenAI API key not found. Set it in `.env` or Streamlit Secrets.")
        st.stop()
    return OpenAI(api_key=api_key)
