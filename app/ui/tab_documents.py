import streamlit as st
import requests


def render_documents_tab(FASTAPI_URL: str):
    st.header("📄 Document Upload")

    # --------------- UPLOAD --------------------
    uploaded_pdf = st.file_uploader("Upload PDF file", type=["pdf"])

    if uploaded_pdf:
        st.info(f"Selected: {uploaded_pdf.name}")
        if st.button("📤 Upload & Rebuild Index"):
            with st.spinner("Processing and rebuilding index..."):
                try:
                    files = {
                        "file": (uploaded_pdf.name, uploaded_pdf.getvalue(), "application/pdf")
                    }
                    r = requests.post(f"{FASTAPI_URL}/upload/pdf", files=files)
                    if r.status_code == 200:
                        st.success("Document uploaded and FAISS index rebuilt!")
                        st.json(r.json())
                    else:
                        st.error(r.text)
                except Exception as e:
                    st.error(f"Upload failed: {e}")

    st.markdown("---")

    # --------------- LIST DOCUMENTS --------------------
    st.subheader("📁 Documents in Corpus")

    try:
        res = requests.get(f"{FASTAPI_URL}/documents/list")
        docs = res.json().get("documents", [])
    except:
        st.error("Failed to fetch document list")
        return

    if not docs:
        st.info("No documents uploaded yet.")
        return

    for doc in docs:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"📄 {doc}")
        with col2:
            if st.button("🗑️ Delete", key=f"del_{doc}"):
                try:
                    r = requests.delete(f"{FASTAPI_URL}/documents/delete/{doc}")
                    if r.status_code == 200:
                        st.success(f"{doc} deleted and FAISS rebuilt!")
                        st.experimental_rerun()
                    else:
                        st.error(r.text)
                except Exception as e:
                    st.error(f"Failed to delete: {e}")
