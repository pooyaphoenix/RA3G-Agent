import streamlit as st
import requests
import json
import os, re
from datetime import datetime
import pandas as pd

FASTAPI_PORT = os.getenv("FASTAPI_PORT", "8000")
FASTAPI_URL = f"http://localhost:{FASTAPI_PORT}"

st.set_page_config(page_title="Policy-Aware RAG", page_icon="🧠", layout="wide")
st.title("RA3G")
st.text("🧠 Policy-Aware RAG System with Governance Control")

# Tabs: Chat | Logs
tab1, tab2 = st.tabs(["💬 Chat Interface", "Logs"])

# ---------------------------------------------------
# TAB 1 — CHAT INTERFACE
# ---------------------------------------------------
with tab1:
    # Session state initialization
    if "session_id" not in st.session_state:
        st.session_state.session_id = "demo_session"
    if "history" not in st.session_state:
        st.session_state.history = []

    st.sidebar.title("⚙️ Controls")

    if st.sidebar.button("Check System Health", key="check_health_btn_tab1"):
        resp = requests.get(f"{FASTAPI_URL}/health")
        if resp.status_code == 200:
            st.sidebar.success("✅ System is healthy")
            st.sidebar.json(resp.json())
        else:
            st.sidebar.error("❌ Health check failed")

    if st.sidebar.button("Clear Memory", key="clear_memory_btn_tab1"):
        resp = requests.delete(
            f"{FASTAPI_URL}/memory/clear", headers={"session_id": st.session_state.session_id}
        )
        if resp.status_code == 200:
            st.session_state.history = []
            st.sidebar.success("Memory cleared successfully.")
        else:
            st.sidebar.error("No memory found for this session.")

    # Main chat interface
    query = st.text_area("💬 Enter your question:", placeholder="Ask something...", key="query_input_tab1")
    top_k = st.slider("Top K retrieved passages", 1, 10, 5, key="topk_slider_tab1")

    if st.button("Submit Query", key="submit_btn_tab1"):
        if query.strip():
            payload = {"query": query, "top_k": top_k}
            headers = {"session_id": st.session_state.session_id}
            with st.spinner("🔍 Processing your query..."):
                resp = requests.post(f"{FASTAPI_URL}/query", json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.history.append(data)
                st.success("✅ Query processed successfully!")
                st.write("### Answer:")
                st.markdown(f"**{data['answer']}**")

                confidence = data.get("confidence", 0)
                st.progress(confidence)
                st.write(f"**Confidence:** {confidence*100:.1f}%")

                with st.expander("Governance Details"):
                    st.json(data["governance"])
                with st.expander("Retrieved Passages"):
                    st.json(data["retrieved"])
                with st.expander("Trace / Reasoning Steps"):
                    st.json(data["trace"])
            else:
                st.error("Error processing query.")
        else:
            st.warning("Please enter a query before submitting.")

    if st.session_state.history:
        st.markdown("---")
        st.write("### 🧠 Conversation History")
        for turn in reversed(st.session_state.history):
            st.markdown(f"**Q:** {turn['query']}")
            st.markdown(f"**A:** {turn['answer']}")

# ---------------------------------------------------
# TAB 2 — LOG VIEWER
# ---------------------------------------------------
with tab2:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    LOG_DIR = os.path.join(BASE_DIR, "logs")

    LOG_FILES = {
        "Gateway": os.path.join(LOG_DIR, "gateway.log"),
        "Retriever": os.path.join(LOG_DIR, "retriever.log"),
        "Reasoning": os.path.join(LOG_DIR, "reasoning.log"),
        "Governance": os.path.join(LOG_DIR, "governance.log"),
    }

    st.subheader("Logs")

    # --- Button to clear all logs ---
    if st.button("Clear All Logs", key="clear_all_logs_btn"):
        deleted_files = []
        for name, path in LOG_FILES.items():
            if os.path.exists(path):
                open(path, "w").close()  # truncate file content
                deleted_files.append(name)
        if deleted_files:
            st.success(f"✅ Cleared logs for: {', '.join(deleted_files)}")
        else:
            st.warning("No log files found to clear.")

    # --- Log selection and display ---
    log_choice = st.selectbox("Select a log file:", list(LOG_FILES.keys()), key="log_choice_tab2")
    log_path = LOG_FILES[log_choice]

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            log_content = f.readlines()
    except FileNotFoundError:
        st.error(f"❌ Log file not found: `{log_path}`")
        st.stop()

    search_term = st.text_input("Search keyword:", key="log_search_term_tab2")
    show_errors_only = st.checkbox("Show only errors", key="errors_only_checkbox_tab2")
    limit_lines = st.slider("Limit number of lines", 50, 1000, 300, key="limit_lines_slider_tab2")

    def parse_log_line(line):
        match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),?\d*\s*-\s*(\w+)\s*-\s*(.*)", line)
        if match:
            time_str, level, msg = match.groups()
            try:
                timestamp = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                timestamp = None
            return {"time": timestamp, "level": level, "message": msg.strip()}
        return {"time": None, "level": "UNKNOWN", "message": line.strip()}

    data = [parse_log_line(line) for line in log_content[-limit_lines:]]
    df = pd.DataFrame(data)

    if search_term:
        df = df[df["message"].str.contains(search_term, case=False, na=False)]
    if show_errors_only:
        df = df[df["level"].isin(["ERROR", "CRITICAL"])]

    st.caption(f"Showing last {len(df)} lines (filtered)")

    if df.empty:
        st.warning("No log entries match your filters.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
