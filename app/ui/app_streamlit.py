import streamlit as st
import os

from tab_chat import render_chat_tab
from tab_logs import render_logs_tab
from tab_config import render_config_tab

FASTAPI_PORT = os.getenv("FASTAPI_PORT", "8000")
FASTAPI_URL = f"http://localhost:{FASTAPI_PORT}"

st.set_page_config(page_title="Policy-Aware RAG", page_icon="🧠", layout="wide")
st.title("RA3G")
st.text("🧠 Policy-Aware RAG System with Governance Control")

tab1, tab2, tab3 = st.tabs(["💬 Chat Interface", " Logs", "⚙️ Configuration"])

with tab1:
    render_chat_tab(FASTAPI_URL)

with tab2:
    render_logs_tab(FASTAPI_URL)


# ---------------------------------------------------
# TAB 3 — CONFIGURATION EDITOR
# ---------------------------------------------------
with tab3:
    render_config_tab()
