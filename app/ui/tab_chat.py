import streamlit as st
import requests
import re

def _highlight_terms(text: str, query: str) -> str:
    """
    Highlights query terms within the passage text.
    """
    if not query:
        return text
        
    # Split query into words, ignore small words (<= 3 chars) to avoid clutter
    terms = [re.escape(word) for word in query.split() if len(word) > 3]
    
    if not terms:
        return text

    # Create a regex pattern to find all terms (case insensitive)
    pattern = re.compile(r'\b(' + '|'.join(terms) + r')\b', re.IGNORECASE)
    
    # Highlight with yellow background and bold text
    # Note: We force color: black inside the highlight to ensure contrast
    highlighted = pattern.sub(
        r'<span style="background-color: #ffd700; color: black; padding: 0 2px; border-radius: 3px; font-weight: bold;">\1</span>', 
        text
    )
    
    return highlighted

def render_chat_tab(FASTAPI_URL):
    # Session state initialization
    if "session_id" not in st.session_state:
        st.session_state.session_id = "demo_session"
    if "history" not in st.session_state:
        st.session_state.history = []

    st.sidebar.title("⚙️ Controls")

    # --- Sidebar Controls ---
    if st.sidebar.button("Check System Health", key="check_health_btn_tab1"):
        try:
            resp = requests.get(f"{FASTAPI_URL}/health")
            if resp.status_code == 200:
                st.sidebar.success("✅ System is healthy")
                st.sidebar.json(resp.json())
            else:
                st.sidebar.error("❌ Health check failed")
        except Exception as e:
            st.sidebar.error(f"❌ Connection error: {e}")

    if st.sidebar.button("Clear Memory", key="clear_memory_btn_tab1"):
        try:
            resp = requests.delete(
                f"{FASTAPI_URL}/memory/clear", headers={"session_id": st.session_state.session_id}
            )
            if resp.status_code == 200:
                st.session_state.history = []
                st.sidebar.success("Memory cleared successfully.")
            else:
                st.sidebar.error("No memory found for this session.")
        except Exception:
            st.sidebar.error("Failed to clear memory.")

    # --- Main Inputs ---
    query = st.text_area("💬 Enter your question:", placeholder="Ask something...", key="query_input_tab1")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        top_k = st.number_input(
            "Top K Passages", 
            min_value=1, 
            max_value=20, 
            value=5, 
            step=1,
            key="topk_input_tab1"
        )

    if st.button("Submit Query", key="submit_btn_tab1"):
        if query.strip():
            payload = {"query": query, "top_k": top_k}
            headers = {"session_id": st.session_state.session_id}
            with st.spinner("🔍 Processing your query..."):
                try:
                    resp = requests.post(f"{FASTAPI_URL}/query", json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.history.append(data)
                        
                        # --- Main Answer Section ---
                        st.success("✅ Query processed successfully!")
                        st.write("### Answer:")
                        st.markdown(f"**{data['answer']}**")

                        confidence = data.get("confidence", 0)
                        st.progress(confidence)
                        st.write(f"**Confidence:** {confidence * 100:.1f}%")

                        # --- Governance Section ---
                        with st.expander("🛡️ Governance Details"):
                            gov = data.get("governance", {})
                            if gov.get("approved"):
                                st.success(f"Approved (Reason: {gov.get('reason')})")
                            else:
                                st.error(f"Rejected (Reason: {gov.get('reason')})")
                            st.json(gov)

                        # --- RETRIEVED PASSAGES UI (Consolidated HTML Fix) ---
                        with st.expander("📚 Retrieved Passages & Context", expanded=True):
                            
                            trace_indices = [t['index'] for t in data.get("trace", [])]
                            passages = data.get("retrieved", [])
                            
                            if not passages:
                                st.info("No passages retrieved.")
                            
                            for i, p in enumerate(passages):
                                score = p.get('score', 0)
                                source = p.get('source', 'unknown')
                                raw_text = p.get('text', '')
                                
                                is_used = i in trace_indices
                                formatted_text = _highlight_terms(raw_text, query)
                                
                                # Visual Logic
                                if is_used:
                                    status_label = f"🟢 Passage {i} (Used by AI)"
                                    border_color = "#28a745" # Green
                                    bg_color = "#f0fcf4"     # Light Green
                                else:
                                    status_label = f"⚪ Passage {i} (Ignored)"
                                    border_color = "#dee2e6" # Gray
                                    bg_color = "#f8f9fa"     # Light Gray (Off-white)

                                # ***FIXED HTML TEMPLATE***
                                # Consolidated the status label and the main content into one markdown call 
                                # to prevent the raw HTML from being rendered as text.
                                st.markdown(
                                    f"""
                                    <div style="margin-bottom: 20px;">
                                        <h4 style="margin-bottom: 5px;">{status_label}</h4>
                                        <div style="
                                            border: 2px solid {border_color}; 
                                            padding: 15px; 
                                            border-radius: 8px; 
                                            background-color: {bg_color};
                                            color: #212529; /* Ensures dark text on light card background */
                                            ">
                                            <div style="font-size: 0.85em; color: #6c757d; margin-bottom: 8px; font-family: monospace;">
                                                <b>ID:</b> {p.get('id')} | <b>Score:</b> {score:.4f}
                                            </div>
                                            <div style="font-size: 1em; line-height: 1.6; white-space: pre-wrap;">
                                                {formatted_text}
                                            </div>
                                            <div style="margin-top: 10px; font-size: 0.85em; color: #6c757d; border-top: 1px solid #e9ecef; padding-top: 5px;">
                                                <i>Source: {source}</i>
                                            </div>
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )

                        # --- Trace Section ---
                        with st.expander("🧠 Trace / Reasoning Steps"):
                            st.json(data["trace"])
                            
                    else:
                        st.error(f"Error processing query: {resp.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")
        else:
            st.warning("Please enter a query before submitting.")

    # --- History Display ---
    if st.session_state.history:
        st.markdown("---")
        st.subheader("🧠 Conversation History")
        for turn in reversed(st.session_state.history):
            with st.container():
                st.markdown(f"**Q:** {turn['query']}")
                st.info(f"**A:** {turn['answer']}")
                st.markdown("---")