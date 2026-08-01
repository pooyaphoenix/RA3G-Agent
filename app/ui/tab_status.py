import streamlit as st
import requests
import time
from datetime import datetime
from typing import Dict, Tuple

AGENTS = ["gateway", "retriever", "reasoning", "governance"]

AGENT_META = {
    "gateway":    {"icon": "🌐", "label": "Gateway"},
    "retriever":  {"icon": "🔍", "label": "Retriever"},
    "reasoning":  {"icon": "🧠", "label": "Reasoning"},
    "governance": {"icon": "🛡️", "label": "Governance"},
}


def _status_indicator(status: str) -> Tuple[str, str]:
    """Return (emoji, human label) for a status string."""
    s = (status or "unknown").lower()
    if s == "healthy":
        return "✅", "Healthy"
    if s == "slow":
        return "⚠️", "Slow"
    if s == "degraded":
        return "⚠️", "Degraded"
    if s in ("error", "down"):
        return "❌", "Down"
    if s == "not_started":
        return "💤", "Not started"
    return "❓", "Unknown"


def _fmt_latency(val) -> str:
    if val is None:
        return "—"
    ms = val * 1000
    if ms < 1:
        return "<1 ms"
    return f"{ms:.0f} ms"


def render_status_tab(fastapi_url: str = "http://localhost:8010"):
    st.subheader("📊 Agent Status Monitor")
    st.caption("Real-time health and performance of all pipeline agents")

    # ── Controls row ──────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns([2, 2, 3])
    with c1:
        auto_refresh = st.checkbox(
            "⏱ Auto-refresh (10s)", value=False, key="auto_refresh_status"
        )
    with c2:
        if st.button("🔄 Refresh Now", key="manual_refresh_btn", use_container_width=True):
            st.rerun()
    ts_slot = c3.empty()

    # ── Fetch overall summary ─────────────────────────────────────────────────
    fetch_t0 = time.time()
    try:
        r = requests.get(f"{fastapi_url}/health", timeout=5)
        overall = r.json() if r.status_code == 200 else None
    except Exception:
        overall = None

    # ── Fetch per-agent details ───────────────────────────────────────────────
    agent_data: Dict[str, dict] = {}
    for agent in AGENTS:
        try:
            r = requests.get(f"{fastapi_url}/health/{agent}", timeout=5)
            agent_data[agent] = r.json() if r.status_code == 200 else {
                "status": "error", "error": f"HTTP {r.status_code}"
            }
        except Exception as exc:
            agent_data[agent] = {"status": "error", "error": str(exc)}

    fetch_ms = (time.time() - fetch_t0) * 1000

    # ── Timestamp ─────────────────────────────────────────────────────────────
    ts_slot.caption(
        f"Last updated: **{datetime.now().strftime('%H:%M:%S')}** · "
        f"fetched in {fetch_ms:.0f} ms"
    )

    # ── Overall banner ────────────────────────────────────────────────────────
    st.divider()
    if overall is None:
        st.error("❌ **Backend unreachable** — is the API server running?")
    else:
        ov_status = overall.get("status", "unknown")
        agents_map = overall.get("agents", {})
        healthy_count = sum(1 for s in agents_map.values() if s == "healthy")
        total_count   = len(agents_map)

        if ov_status == "ok":
            st.success(f"✅ **All systems operational** — {healthy_count}/{total_count} agents healthy")
        elif ov_status == "degraded":
            st.warning(f"⚠️ **System degraded** — {healthy_count}/{total_count} agents healthy")
        else:
            st.error(f"❌ **System unhealthy** — {healthy_count}/{total_count} agents healthy")

        # Mini summary pills
        pill_cols = st.columns(len(AGENTS))
        for idx, agent in enumerate(AGENTS):
            a_status = agents_map.get(agent, "unknown")
            emoji, label = _status_indicator(a_status)
            meta = AGENT_META[agent]
            pill_cols[idx].markdown(
                f"<div style='text-align:center;font-size:1.3rem'>{meta['icon']}</div>"
                f"<div style='text-align:center;font-size:0.75rem'>{meta['label']}</div>"
                f"<div style='text-align:center'>{emoji}</div>",
                unsafe_allow_html=True,
            )

    st.divider()

    # ── Agent detail cards (2 per row) ────────────────────────────────────────
    for i in range(0, len(AGENTS), 2):
        left_agent  = AGENTS[i]
        right_agent = AGENTS[i + 1] if i + 1 < len(AGENTS) else None
        col_l, col_r = st.columns(2, gap="medium")

        with col_l:
            _render_agent_card(left_agent, agent_data.get(left_agent, {}))
        if right_agent:
            with col_r:
                _render_agent_card(right_agent, agent_data.get(right_agent, {}))

    # ── Auto-refresh: sleep remaining time, then rerun ────────────────────────
    if auto_refresh:
        remaining = max(0.0, 10.0 - (time.time() - fetch_t0))
        time.sleep(remaining)
        st.rerun()


def _render_agent_card(agent: str, data: dict):
    meta    = AGENT_META.get(agent, {"icon": "🔧", "label": agent.title()})
    status  = data.get("status", "unknown")
    emoji, label = _status_indicator(status)

    latency     = data.get("response_latency")
    uptime      = data.get("uptime") or "—"
    last_act    = data.get("last_activity") or "—"
    error_count = data.get("error_count", 0)

    with st.container(border=True):
        # Header row
        hd_left, hd_right = st.columns([3, 1])
        hd_left.markdown(f"**{meta['icon']} {meta['label']}**")
        hd_right.markdown(
            f"<div style='text-align:right;font-size:1.4rem'>{emoji}</div>",
            unsafe_allow_html=True,
        )
        st.caption(f"Status: `{label.upper()}`")

        # Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Latency", _fmt_latency(latency))
        m2.metric("Errors", error_count)
        m3.metric("Uptime", uptime if uptime != "N/A" else "—")

        st.caption(f"Last active: {last_act}")

        # Inline errors expander
        errors = data.get("errors") or []
        if errors:
            with st.expander(f"🔴 {len(errors)} error(s)", expanded=False):
                for err in errors[-5:]:
                    st.code(err, language=None)
        elif error_count == 0 and status in ("healthy", "not_started"):
            st.caption("No errors recorded.")

        # Recent logs expander
        logs = data.get("recent_logs") or []
        if logs:
            with st.expander("📋 Recent logs", expanded=False):
                st.code("\n".join(logs[-10:]), language=None)
