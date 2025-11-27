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

# Tabs: Chat | Logs | Configuration
tab1, tab2, tab3 = st.tabs(["💬 Chat Interface", " Logs", "⚙️ Configuration"])

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

    # Map display names to API log types
    LOG_TYPE_MAP = {
        "Gateway": "gateway",
        "Retriever": "retriever",
        "Reasoning": "reasoning",
        "Governance": "governance",
    }

    st.subheader("Logs")

    # Initialize session state for live logs
    if "live_logs_enabled" not in st.session_state:
        st.session_state.live_logs_enabled = False
    if "logs_paused" not in st.session_state:
        st.session_state.logs_paused = False
    if "log_lines" not in st.session_state:
        st.session_state.log_lines = []

    # --- Button to clear all logs ---
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("Clear All Logs", key="clear_all_logs_btn"):
            deleted_files = []
            for name, path in LOG_FILES.items():
                if os.path.exists(path):
                    open(path, "w").close()  # truncate file content
                    deleted_files.append(name)
            if deleted_files:
                st.success(f"✅ Cleared logs for: {', '.join(deleted_files)}")
                st.session_state.log_lines = []  # Clear in-memory logs
            else:
                st.warning("No log files found to clear.")
    
    with col2:
        # Live Logs toggle
        live_logs = st.checkbox("🔴 Live Logs", value=st.session_state.live_logs_enabled, key="live_logs_toggle")
        if live_logs != st.session_state.live_logs_enabled:
            st.session_state.live_logs_enabled = live_logs
            if not live_logs:
                st.session_state.logs_paused = False
            st.rerun()

    # --- Log selection ---
    log_choice = st.selectbox("Select a log file:", list(LOG_FILES.keys()), key="log_choice_tab2")
    log_path = LOG_FILES[log_choice]
    log_type = LOG_TYPE_MAP[log_choice]

    # Pause/Resume button and status (only shown when live logs are enabled)
    if st.session_state.live_logs_enabled:
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("⏸️ Pause" if not st.session_state.logs_paused else "▶️ Resume", key="pause_resume_btn"):
                st.session_state.logs_paused = not st.session_state.logs_paused
                st.rerun()
        with col2:
            if st.session_state.logs_paused:
                st.info("⏸️ Live logs paused - showing static view")
            else:
                st.success("🔴 Live logs streaming active")

    # Filters
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
            return {"time": timestamp, "level": level, "message": msg.strip(), "raw": line.strip()}
        return {"time": None, "level": "UNKNOWN", "message": line.strip(), "raw": line.strip()}

    # Real-time streaming mode (only when live logs enabled and not paused)
    if st.session_state.live_logs_enabled and not st.session_state.logs_paused:
        # Use HTML component with JavaScript to consume SSE
        stream_url = f"{FASTAPI_URL}/logs/stream/{log_type}"
        
        # Escape search term for JavaScript
        search_term_escaped = search_term.replace("'", "\\'").replace("\\", "\\\\")
        show_errors_js = "true" if show_errors_only else "false"
        
        html_code = f"""
        <div id="log-container" style="font-family: monospace; background: #1e1e1e; color: #d4d4d4; padding: 10px; border-radius: 5px; max-height: 600px; overflow-y: auto;">
            <div id="log-content"></div>
        </div>
        <script>
            (function() {{
                const logContainer = document.getElementById('log-content');
                const maxLines = {limit_lines};
                const searchTerm = '{search_term_escaped}'.toLowerCase();
                const showErrorsOnly = {show_errors_js};
                let lines = [];
                let eventSource = null;
                let isPaused = false;
                
                function addLogLine(line, isError, isWarning) {{
                    if (isPaused) return;
                    lines.push({{line: line, isError: isError, isWarning: isWarning}});
                    if (lines.length > maxLines) {{
                        lines.shift();
                    }}
                    renderLogs();
                }}
                
                function renderLogs() {{
                    let html = '';
                    
                    lines.forEach(item => {{
                        const line = item.line;
                        const isError = item.isError;
                        const isWarning = item.isWarning;
                        
                        // Apply filters
                        if (showErrorsOnly && !isError) return;
                        if (searchTerm && !line.toLowerCase().includes(searchTerm)) return;
                        
                        // Determine color
                        let color = '#d4d4d4';
                        let bgColor = 'transparent';
                        if (isError) {{
                            color = '#f48771';
                            bgColor = '#3c1e1e';
                        }} else if (isWarning) {{
                            color = '#dcdcaa';
                            bgColor = '#3c3c1e';
                        }}
                        
                        html += `<div style="padding: 2px 5px; background: ${{bgColor}}; color: ${{color}}; border-left: 3px solid ${{isError ? '#f48771' : isWarning ? '#dcdcaa' : 'transparent'}};">${{escapeHtml(line)}}</div>`;
                    }});
                    
                    logContainer.innerHTML = html;
                    logContainer.scrollTop = logContainer.scrollHeight;
                }}
                
                function escapeHtml(text) {{
                    const div = document.createElement('div');
                    div.textContent = text;
                    return div.innerHTML;
                }}
                
                function startStreaming() {{
                    if (eventSource) {{
                        eventSource.close();
                    }}
                    
                    eventSource = new EventSource('{stream_url}');
                    
                    eventSource.onmessage = function(event) {{
                        try {{
                            const data = JSON.parse(event.data);
                            if (data.line) {{
                                const line = data.line;
                                const isError = line.includes('ERROR') || line.includes('CRITICAL');
                                const isWarning = line.includes('WARNING') || line.includes('WARN');
                                addLogLine(line, isError, isWarning);
                            }}
                        }} catch (e) {{
                            console.error('Error parsing log data:', e);
                        }}
                    }};
                    
                    eventSource.onerror = function(event) {{
                        console.error('SSE error:', event);
                        setTimeout(startStreaming, 3000); // Reconnect after 3 seconds
                    }};
                }}
                
                startStreaming();
                
                // Cleanup on page unload
                window.addEventListener('beforeunload', function() {{
                    if (eventSource) {{
                        eventSource.close();
                    }}
                }});
            }})();
        </script>
        """
        
        st.components.v1.html(html_code, height=650, scrolling=True)
        
        # Also update session state for fallback display
        if st.session_state.log_lines:
            data = [parse_log_line(line) for line in st.session_state.log_lines[-limit_lines:]]
            df = pd.DataFrame(data)
            
            if search_term:
                df = df[df["message"].str.contains(search_term, case=False, na=False)]
            if show_errors_only:
                df = df[df["level"].isin(["ERROR", "CRITICAL"])]
            
            st.caption(f"📊 Showing last {len(df)} lines (filtered) - Live mode active")
    
    else:
        # Static mode (when live logs disabled or paused)
        if st.session_state.live_logs_enabled and st.session_state.logs_paused:
            st.info("💡 Live logs are paused. Click 'Resume' to continue streaming.")
        
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                log_content = f.readlines()
        except FileNotFoundError:
            st.error(f"❌ Log file not found: `{log_path}`")
            st.stop()

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
            # Apply styling for errors/warnings
            def style_log_row(row):
                styles = [''] * len(row)
                if row['level'] in ['ERROR', 'CRITICAL']:
                    return ['background-color: #3c1e1e; color: #f48771'] * len(row)
                elif row['level'] in ['WARNING', 'WARN']:
                    return ['background-color: #3c3c1e; color: #dcdcaa'] * len(row)
                return [''] * len(row)
            
            styled_df = df.style.apply(style_log_row, axis=1)
            st.dataframe(styled_df, width='stretch', hide_index=True)


# ---------------------------------------------------
# TAB 3 — CONFIGURATION EDITOR
# ---------------------------------------------------
with tab3:
    st.subheader("⚙️ Configuration Settings")

    CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config.yml"))

    if not os.path.exists(CONFIG_PATH):
        st.error(f"Configuration file not found: {CONFIG_PATH}")
        st.stop()

    import yaml

    # --- Load YAML config
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    st.caption("Modify the configuration values below and click **Save Changes**.")

    editable_config = {}

    # Call Ollama server to fetch available models
    def fetch_ollama_models(ollama_url):
        try:
            url = ollama_url.replace("/api/generate", "/api/tags")  # Adjust endpoint
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            model_list = [model.get("name") for model in data.get("models", []) if "name" in model]
            return model_list
        except Exception as e:
            st.error(f"⚠️ Could not fetch models from Ollama: {str(e)}")
            return []

    ollama_url = config_data.get("OLLAMA_URL", "http://localhost:11434/api/generate")
    available_models = fetch_ollama_models(ollama_url)

    for key, value in config_data.items():

        # 1️⃣ Handle OLLAMA_MODEL specially (dropdown)
        if key == "OLLAMA_MODEL":
            st.markdown("### 🧠 Select Ollama Model")
            if available_models:
                editable_config[key] = st.selectbox(
                    "Available Models from Ollama",
                    available_models,
                    index=available_models.index(value) if value in available_models else 0
                )
            else:
                st.warning("No models found. Using manual input.")
                editable_config[key] = st.text_input(key, value=str(value))

        # 2️⃣ Handle THRESHOLDS dictionary
        elif key == "THRESHOLDS" and isinstance(value, dict):
            st.markdown("### 🔍 AI Policy Thresholds")
            editable_config[key] = {}
            for sub_key, sub_value in value.items():
                editable_config[key][sub_key] = st.number_input(
                    f"{key} → {sub_key}",
                    value=float(sub_value),
                    min_value=0.0,
                    max_value=1.0,
                    step=0.01,
                    help="Confidence threshold between 0 and 1",
                )

        # 3️⃣ Handle boolean
        elif isinstance(value, bool):
            editable_config[key] = st.checkbox(key, value=value)

        # 4️⃣ Handle numbers
        elif isinstance(value, (int, float)):
            editable_config[key] = st.number_input(key, value=value)

        # 5️⃣ Handle list
        elif isinstance(value, list):
            editable_config[key] = st.text_area(
                key, value=", ".join(map(str, value)), help="Comma-separated list"
            )

        # 6️⃣ Default string handler
        else:
            editable_config[key] = st.text_input(key, value=str(value))

    # -- Save Button --
    if st.button("💾 Save Changes", key="save_config_btn"):
        for key, value in editable_config.items():
            if isinstance(config_data.get(key), list):
                editable_config[key] = [v.strip() for v in value.split(",") if v.strip()]
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                yaml.safe_dump(editable_config, f, sort_keys=False, allow_unicode=True)
            st.success("✅ Configuration saved successfully!")
            st.info("🔁 Please restart the service for changes to take effect.")
            st.json(editable_config)
        except Exception as e:
            st.error(f"❌ Failed to save configuration: {str(e)}")

    if st.button("🔄 Reload from File", key="reload_config_btn"):
        st.rerun()