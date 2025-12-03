import streamlit as st
import os, re
import pandas as pd
from datetime import datetime
import requests

def render_logs_tab(fastapi_url: str = "http://localhost:8010"):
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    LOG_DIR = os.path.join(BASE_DIR, "logs")

    LOG_FILES = {
        "Gateway": os.path.join(LOG_DIR, "gateway.log"),
        "Retriever": os.path.join(LOG_DIR, "retriever.log"),
        "Reasoning": os.path.join(LOG_DIR, "reasoning.log"),
        "Governance": os.path.join(LOG_DIR, "governance.log"),
    }

    st.subheader("Logs")

    # Map display names to API log types
    LOG_TYPE_MAP = {
        "Gateway": "gateway",
        "Retriever": "retriever",
        "Reasoning": "reasoning",
        "Governance": "governance",
    }

    # Initialize session state for live logs
    if "live_logs_enabled" not in st.session_state:
        st.session_state.live_logs_enabled = False
    if "logs_paused" not in st.session_state:
        st.session_state.logs_paused = False

    # --- Button to clear all logs ---
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("Clear All Logs", key="clear_all_logs_btn"):
            deleted_files = []
            for name, path in LOG_FILES.items():
                if os.path.exists(path):
                    open(path, "w").close()
                    deleted_files.append(name)
            if deleted_files:
                st.success(f"✅ Cleared logs for: {', '.join(deleted_files)}")
                if hasattr(st.session_state, 'log_lines'):
                    st.session_state.log_lines = []
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

    # Pause/Resume button (only shown when live logs are enabled)
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
        stream_url = f"{fastapi_url}/logs/stream/{log_type}"
        
        # Escape search term for JavaScript
        search_term_escaped = search_term.replace("'", "\\'").replace("\\", "\\\\")
        show_errors_js = "true" if show_errors_only else "false"
        
        html_code = f"""
        <div id="log-container" style="font-family: monospace; background: #1e1e1e; color: #d4d4d4; padding: 10px; border-radius: 5px; max-height: 600px; overflow-y: auto;">
            <div id="log-content" style="min-height: 50px;">
                <div style="color: #888; padding: 10px;">Loading logs...</div>
            </div>
        </div>
        <script>
            (function() {{
                const logContainer = document.getElementById('log-content');
                const maxLines = {limit_lines};
                const searchTerm = '{search_term_escaped}'.toLowerCase();
                const showErrorsOnly = {show_errors_js};
                let lines = [];
                let eventSource = null;
                let renderPending = false;
                let initialLoad = true;
                
                // Batch rendering for performance
                function scheduleRender() {{
                    if (renderPending) return;
                    renderPending = true;
                    requestAnimationFrame(() => {{
                        renderLogs();
                        renderPending = false;
                    }});
                }}
                
                function addLogLine(line, isError, isWarning) {{
                    if (lines.length >= maxLines) {{
                        lines.shift();
                    }}
                    lines.push({{line: line, isError: isError, isWarning: isWarning}});
                    scheduleRender();
                }}
                
                function renderLogs() {{
                    if (initialLoad && lines.length === 0) {{
                        return; // Don't clear loading message until we have data
                    }}
                    
                    initialLoad = false;
                    let html = '';
                    let visibleCount = 0;
                    
                    lines.forEach(item => {{
                        const line = item.line;
                        const isError = item.isError;
                        const isWarning = item.isWarning;
                        
                        // Apply filters
                        if (showErrorsOnly && !isError) return;
                        if (searchTerm && !line.toLowerCase().includes(searchTerm)) return;
                        
                        visibleCount++;
                        
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
                    
                    if (html) {{
                        logContainer.innerHTML = html;
                        logContainer.scrollTop = logContainer.scrollHeight;
                    }} else if (lines.length > 0) {{
                        logContainer.innerHTML = '<div style="color: #888; padding: 10px;">No logs match your filters.</div>';
                    }}
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
                    
                    // Reset state
                    lines = [];
                    initialLoad = true;
                    logContainer.innerHTML = '<div style="color: #888; padding: 10px;">Connecting to log stream...</div>';
                    
                    eventSource = new EventSource('{stream_url}');
                    
                    eventSource.onopen = function() {{
                        console.log('SSE connection opened');
                    }};
                    
                    eventSource.onmessage = function(event) {{
                        try {{
                            const data = JSON.parse(event.data);
                            if (data.error) {{
                                logContainer.innerHTML = `<div style="color: #f48771; padding: 10px;">Error: ${{escapeHtml(data.error)}}</div>`;
                                return;
                            }}
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
                        console.error('SSE error:', event, 'readyState:', eventSource.readyState);
                        // Only reconnect if connection is actually closed
                        // CONNECTING = 0, OPEN = 1, CLOSED = 2
                        if (eventSource.readyState === EventSource.CLOSED) {{
                            logContainer.innerHTML = '<div style="color: #f48771; padding: 10px;">Connection closed. Reconnecting...</div>';
                            setTimeout(startStreaming, 2000);
                        }} else if (eventSource.readyState === EventSource.CONNECTING) {{
                            // Still connecting, don't show error yet
                            console.log('Still connecting...');
                        }}
                        // If OPEN (1), connection is fine, just a temporary error
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
        st.caption(f"📊 Live streaming active - showing last {limit_lines} lines")
    
    else:
        # Static mode (when live logs disabled or paused)
        if st.session_state.live_logs_enabled and st.session_state.logs_paused:
            st.info("💡 Live logs are paused. Click 'Resume' to continue streaming.")
        
        # Read log file for static display
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                log_content = f.readlines()
        except FileNotFoundError:
            st.error(f"❌ Log file not found: `{log_path}`")
            return

        # Process and display static logs
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
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
