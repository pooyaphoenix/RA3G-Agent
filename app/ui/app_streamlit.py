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

# Mobile-responsive CSS
st.markdown("""
<style>
    /* Compact header on small screens */
    @media (max-width: 768px) {
        .block-container { padding: 1rem 0.75rem; }
        .stColumns > div { min-width: 100% !important; flex: 1 1 100% !important; }
        .stButton > button { width: 100%; margin-bottom: 0.4rem; }
        .stTextArea textarea { font-size: 16px; }
        .stNumberInput input { font-size: 16px; }
        div[data-testid="column"] { min-width: 0; }
    }
    /* Nicer tab bar */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] { padding: 6px 12px; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

st.title("RA3G")
st.caption("Policy-Aware RAG System with Governance Control")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["💬 Chat", "📋 Logs", "⚙️ Config", "📄 Documents", "📊 Status"])

with tab1:
    render_chat_tab(FASTAPI_URL)

with tab2:
    render_logs_tab(FASTAPI_URL)

with tab3:
    render_config_tab(FASTAPI_URL)

with tab4:
    render_documents_tab(FASTAPI_URL)

with tab5:
    render_status_tab(FASTAPI_URL)
