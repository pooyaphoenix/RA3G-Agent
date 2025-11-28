import streamlit as st
import os, re
import pandas as pd
from datetime import datetime

def render_logs_tab():
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    LOG_DIR = os.path.join(BASE_DIR, "logs")

    LOG_FILES = {
        "Gateway": os.path.join(LOG_DIR, "gateway.log"),
        "Retriever": os.path.join(LOG_DIR, "retriever.log"),
        "Reasoning": os.path.join(LOG_DIR, "reasoning.log"),
        "Governance": os.path.join(LOG_DIR, "governance.log"),
    }

    st.subheader("Logs")

    if st.button("Clear All Logs", key="clear_all_logs_btn"):
        deleted_files = []
        for name, path in LOG_FILES.items():
            if os.path.exists(path):
                open(path, "w").close()
                deleted_files.append(name)
        st.success(f"Cleared logs: {', '.join(deleted_files)}") if deleted_files else st.warning("No log files found.")

    log_choice = st.selectbox("Select a log file:", list(LOG_FILES.keys()), key="log_choice_tab2")
    log_path = LOG_FILES[log_choice]

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            log_content = f.readlines()
    except FileNotFoundError:
        st.error(f"❌ Log file not found: `{log_path}`")
        return

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
    st.dataframe(df, width='stretch', hide_index=True) if not df.empty else st.warning("No log entries match your filters.")
