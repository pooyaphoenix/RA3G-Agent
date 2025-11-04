import streamlit as st
import pandas as pd
import re
from datetime import datetime

st.set_page_config(page_title="RA3G Logs Viewer", page_icon="📜", layout="wide")
st.title("📜 RA3G Log Viewer")

# --- Define paths to log files ---
LOG_FILES = {
    "Gateway": "logs/gateway.log",
    "Governance": "logs/governance.log",
    "Reasoning": "logs/reasoning.log",
    "Retriever": "logs/retriever.log",
}

# --- Sidebar file selector ---
log_choice = st.sidebar.selectbox("Select a log file to view:", list(LOG_FILES.keys()))
log_path = LOG_FILES[log_choice]

# --- Load logs safely ---
try:
    with open(log_path, "r", encoding="utf-8") as f:
        log_content = f.readlines()
except FileNotFoundError:
    st.error(f"❌ Log file not found: `{log_path}`")
    st.stop()

# --- Optional filters ---
search_term = st.sidebar.text_input("Search keyword:")
show_errors_only = st.sidebar.checkbox("Show only errors")
limit_lines = st.sidebar.slider("Limit number of lines", 50, 1000, 300)

# --- Parse logs into structured DataFrame ---
def parse_log_line(line):
    # Try to extract datetime, level, and message
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

# --- Apply filters ---
if search_term:
    df = df[df["message"].str.contains(search_term, case=False, na=False)]

if show_errors_only:
    df = df[df["level"].isin(["ERROR", "CRITICAL"])]

# --- Display DataFrame ---
st.subheader(f"📄 Viewing: {log_choice}.log")
st.caption(f"Showing last {len(df)} lines (filtered)")

if df.empty:
    st.warning("No log entries match your filters.")
else:
    st.dataframe(df, use_container_width=True, hide_index=True)

# --- Optional details ---
if st.checkbox("Show raw log file"):
    st.text("".join(log_content[-limit_lines:]))
