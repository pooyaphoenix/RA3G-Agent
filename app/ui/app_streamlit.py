import streamlit as st
import os

from tab_chat import render_chat_tab
from tab_logs import render_logs_tab
from tab_config import render_config_tab
from tab_documents import render_documents_tab
from tab_status import render_status_tab

FASTAPI_PORT = os.getenv("FASTAPI_PORT", "8010")
FASTAPI_URL = f"http://localhost:{FASTAPI_PORT}"

st.set_page_config(page_title="RA3G-Policy-Aware RAG", page_icon="🧠", layout="wide")
st.title("RA3G")
st.text("Policy-Aware RAG System with Governance Control")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["💬 Chat Interface", " Logs", "⚙️ Configuration", "📄 Documents", "📊 Status"])

with tab1:
    render_chat_tab(FASTAPI_URL)

with tab2:
    render_logs_tab(FASTAPI_URL)

with tab3:
    render_config_tab()

with tab4:
    render_documents_tab(FASTAPI_URL)

with tab5:
    render_status_tab(FASTAPI_URL)
