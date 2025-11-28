import streamlit as st
import requests

def render_chat_tab(FASTAPI_URL):
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
                st.write(f"**Confidence:** {confidence * 100:.1f}%")

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
