import streamlit as st
import requests
import json
import os

FASTAPI_PORT = os.getenv("FASTAPI_PORT", "8000")
FASTAPI_URL = f"http://localhost:{FASTAPI_PORT}"

st.set_page_config(page_title="Policy-Aware RAG", page_icon="🧠", layout="wide")
st.title("RA3G")
st.text("🧠 Policy-Aware RAG System with Governance Control")
# Session state for persistent chat
if "session_id" not in st.session_state:
    st.session_state.session_id = "demo_session"

if "history" not in st.session_state:
    st.session_state.history = []

# Sidebar
st.sidebar.title("⚙️ Controls")
if st.sidebar.button("Check System Health"):
    resp = requests.get(f"{FASTAPI_URL}/health")
    if resp.status_code == 200:
        st.sidebar.success("✅ System is healthy")
        st.sidebar.json(resp.json())
    else:
        st.sidebar.error("❌ Health check failed")

if st.sidebar.button("Clear Memory"):
    resp = requests.delete(f"{FASTAPI_URL}/memory/clear", headers={"session_id": st.session_state.session_id})
    if resp.status_code == 200:
        st.session_state.history = []
        st.sidebar.success("Memory cleared successfully.")
    else:
        st.sidebar.error("No memory found for this session.")

# Main input
query = st.text_area("💬 Enter your question:", placeholder="Ask something...")

top_k = st.slider("Top K retrieved passages", 1, 10, 5)

if st.button("Submit"):
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
            st.progress(confidence)  # progress bar (0.0 - 1.0)
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

# Show previous chat
if st.session_state.history:
    st.markdown("---")
    st.write("### 🧠 Conversation History")
    for turn in reversed(st.session_state.history):
        st.markdown(f"**Q:** {turn['query']}")
        st.markdown(f"**A:** {turn['answer']}")
