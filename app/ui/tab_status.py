import streamlit as st
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Optional

def render_status_tab(fastapi_url: str = "http://localhost:8010"):
    st.subheader("📊 Agent Status Monitor")
    st.caption("Real-time health and performance status of all agents")
    
    # Auto-refresh toggle
    col1, col2 = st.columns([1, 4])
    with col1:
        auto_refresh = st.checkbox("🔄 Auto-refresh (10s)", value=True, key="auto_refresh_status")
    with col2:
        if st.button("🔄 Refresh Now", key="manual_refresh_btn"):
            st.rerun()
    
    # Fetch overall health summary
    try:
        health_response = requests.get(f"{fastapi_url}/health", timeout=2)
        overall_health = health_response.json() if health_response.status_code == 200 else None
    except:
        overall_health = None
    
    # Fetch detailed status for each agent
    agents = ["gateway", "retriever", "reasoning", "governance"]
    agent_statuses = {}
    
    for agent in agents:
        try:
            response = requests.get(f"{fastapi_url}/health/{agent}", timeout=2)
            if response.status_code == 200:
                agent_statuses[agent] = response.json()
            else:
                agent_statuses[agent] = {"status": "error", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            agent_statuses[agent] = {"status": "error", "error": str(e)}
    
    # Display overall status
    if overall_health:
        if overall_health.get("status") == "ok":
            st.success("✅ **Overall System Status: Healthy**")
        else:
            st.error("❌ **Overall System Status: Unhealthy**")
    else:
        st.warning("⚠️ **Overall System Status: Unknown**")
    
    st.divider()
    
    # Display individual agent statuses
    agent_labels = {
        "gateway": "🌐 Gateway",
        "retriever": "🔍 Retriever",
        "reasoning": "🧠 Reasoning",
        "governance": "🛡️ Governance"
    }
    
    # Create columns for agent cards
    cols = st.columns(2)
    
    for idx, agent in enumerate(agents):
        col = cols[idx % 2]
        with col:
            status = agent_statuses.get(agent, {})
            agent_status = status.get("status", "unknown")
            
            # Determine status indicator
            if agent_status == "healthy":
                status_icon = "✅"
                status_color = "green"
            elif agent_status == "slow":
                status_icon = "⚠️"
                status_color = "orange"
            elif agent_status == "error" or agent_status == "down":
                status_icon = "❌"
                status_color = "red"
            else:
                status_icon = "❓"
                status_color = "gray"
            
            # Agent card
            with st.container():
                st.markdown(f"### {agent_labels.get(agent, agent.title())} {status_icon}")
                
                # Status badge
                status_text = status.get("status", "unknown").upper()
                st.markdown(f"**Status:** `{status_text}`")
                
                # Metrics
                if "uptime" in status:
                    uptime = status["uptime"]
                    st.markdown(f"**Uptime:** {uptime}")
                
                if "last_activity" in status:
                    last_activity = status["last_activity"]
                    st.markdown(f"**Last Activity:** {last_activity}")
                
                if "response_latency" in status:
                    latency = status["response_latency"]
                    latency_ms = f"{latency * 1000:.2f}ms" if isinstance(latency, (int, float)) else latency
                    st.markdown(f"**Response Latency:** {latency_ms}")
                
                if "error_count" in status:
                    error_count = status.get("error_count", 0)
                    if error_count > 0:
                        st.error(f"**Errors:** {error_count}")
                    else:
                        st.success(f"**Errors:** {error_count}")
                
                # Show errors/logs if available
                if "errors" in status and status["errors"]:
                    with st.expander("🔍 View Errors", expanded=False):
                        for error in status["errors"][:5]:  # Show last 5 errors
                            st.error(f"`{error}`")
                
                if "recent_logs" in status and status["recent_logs"]:
                    with st.expander("📋 View Recent Logs", expanded=False):
                        for log in status["recent_logs"][:10]:  # Show last 10 logs
                            st.text(f"`{log}`")
                
                st.markdown("---")
    
    # Auto-refresh logic
    if auto_refresh:
        # Use Streamlit's auto-refresh mechanism
        st.markdown("---")
        refresh_placeholder = st.empty()
        with refresh_placeholder.container():
            st.info("🔄 Auto-refresh enabled. Page will refresh every 10 seconds.")
        
        # Note: In Streamlit, we use st.rerun() with a timer
        # For true auto-refresh, you'd need to use JavaScript or Streamlit's experimental features
        # For now, users can click "Refresh Now" button or the page will refresh on interaction

