import streamlit as st
import httpx
import json
from datetime import datetime
from typing import Dict, List, Optional

# Configuration
API_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="RAG Gateway Dashboard",
    page_icon="🔍",
    layout="wide"
)

def query_api(query: str, top_k: int = 5, session_id: str = "default") -> Optional[Dict]:
    """Query the RAG Gateway API."""
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{API_BASE_URL}/query",
                json={"query": query, "top_k": top_k},
                headers={"session_id": session_id}
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        st.error(f"API request failed: {e}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None

def get_trace_history(session_id: str = "default") -> Optional[Dict]:
    """Get trace history for a session."""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{API_BASE_URL}/trace",
                headers={"session_id": session_id}
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        st.error(f"API request failed: {e}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None

def main():
    st.title("🔍 RAG Gateway Dashboard")
    st.markdown("**Real-time visualization of reasoning traces, retrieved context, and governance results**")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        session_id = st.text_input("Session ID", value="default")
        top_k = st.slider("Top K Results", min_value=1, max_value=10, value=5)
        
        st.markdown("---")
        st.markdown("### API Status")
        
        # Check API connection
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{API_BASE_URL}/docs")
                st.success("✅ API Connected")
        except Exception as e:
            st.error(f"❌ API Unavailable")
            st.code(f"Error: {e}")
            st.info("💡 Make sure the FastAPI server is running on port 8000")
    
    # Initialize session state
    if "query_history" not in st.session_state:
        st.session_state.query_history = []
    
    # Main query interface
    st.header("💬 Query Interface")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        query_text = st.text_input(
            "Enter your query:",
            placeholder="e.g., What are the governance requirements for patient data?",
            label_visibility="collapsed"
        )
    with col2:
        submit_button = st.button("Submit", type="primary", use_container_width=True)
    
    if submit_button and query_text:
        with st.spinner("Processing query..."):
            result = query_api(query_text, top_k=top_k, session_id=session_id)
            
            if result:
                # Add to history
                timestamp = datetime.now()
                st.session_state.query_history.append({
                    "timestamp": timestamp,
                    "result": result
                })
                
                # Show results (use length as unique ID for current query)
                current_id = f"current_{len(st.session_state.query_history)}"
                display_query_result(result, unique_id=current_id)
    
    # Display query history
    if st.session_state.query_history:
        st.header("📜 Query History")
        for idx, item in enumerate(reversed(st.session_state.query_history[-5:]), 1):
            with st.expander(f"Query #{len(st.session_state.query_history) - idx + 1} - {item['timestamp'].strftime('%H:%M:%S')}", expanded=(idx == 1)):
                # Use history index as unique ID
                history_idx = len(st.session_state.query_history) - idx + 1
                unique_id = f"history_{history_idx}"
                display_query_result(item["result"], unique_id=unique_id)
    
    # Session trace history
    if st.checkbox("Show Full Session History"):
        with st.spinner("Loading session history..."):
            trace_data = get_trace_history(session_id)
            if trace_data:
                display_session_trace(trace_data)
            else:
                st.info("No trace history found for this session.")

def display_query_result(result: Dict, unique_id: str = ""):
    """Display a single query result with all details."""
    
    # Top row: Query and Answer
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("❓ Query")
        st.write(result.get("query", "N/A"))
    
    with col2:
        st.subheader("💡 Answer")
        answer = result.get("answer", "N/A")
        st.write(answer)
    
    # Governance status
    st.markdown("---")
    governance = result.get("governance", {})
    approved = governance.get("approved", False)
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if approved:
            st.success("✅ **Governance: APPROVED**")
        else:
            st.error("❌ **Governance: REJECTED**")
    
    with col2:
        confidence = result.get("confidence", 0.0)
        st.metric("Confidence Score", f"{confidence:.2f}")
    
    with col3:
        reason = governance.get("reason", "N/A")
        st.write(f"**Reason:** {reason}")
    
    # Retrieved passages
    st.markdown("---")
    st.subheader("📚 Retrieved Context")
    retrieved = result.get("retrieved", [])
    
    if retrieved:
        for idx, passage in enumerate(retrieved, 1):
            score = passage.get("score", 0.0)
            text = passage.get("text", "")
            source = passage.get("source", "")
            
            with st.container():
                st.markdown(f"**Passage {idx}** (Relevance: {score:.3f})")
                if source:
                    st.caption(f"Source: {source}")
                st.text_area(
                    label="Passage content",
                    value=text,
                    height=100,
                    key=f"passage_{unique_id}_{idx}",
                    disabled=True,
                    label_visibility="collapsed"
                )
    else:
        st.info("No retrieved passages.")
    
    # Reasoning trace
    st.markdown("---")
    st.subheader("🔬 Reasoning Trace")
    trace = result.get("trace", [])
    
    if trace:
        for idx, step in enumerate(trace, 1):
            passage_idx = step.get("index", "?")
            note = step.get("note", "No note")
            
            st.markdown(f"**Step {idx}:** Used passage {passage_idx}")
            st.caption(f"Note: {note}")
    else:
        st.info("No reasoning trace available.")

def display_session_trace(trace_data: Dict):
    """Display full session trace history."""
    st.header("📊 Session Trace History")
    
    session_id = trace_data.get("session_id", "default")
    turns = trace_data.get("turns", [])
    
    st.metric("Session ID", session_id)
    st.metric("Total Turns", len(turns))
    
    for turn_idx, turn in enumerate(turns, 1):
        with st.expander(f"Turn {turn_idx}: {turn.get('query', 'N/A')[:50]}..."):
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.write("**Query:**")
                st.write(turn.get("query", "N/A"))
            
            with col2:
                st.write("**Answer:**")
                st.write(turn.get("answer", "N/A"))
            
            trace = turn.get("trace", [])
            if trace:
                st.write("**Reasoning Trace:**")
                for step in trace:
                    st.caption(f"• {step}")

if __name__ == "__main__":
    main()

