import streamlit as st
import requests
import os

def render_documents_tab(FASTAPI_URL: str):
    st.header("📄 Document Upload")

    st.write(
        "Upload PDF documents to be added to the RAG corpus. "
        "Documents will be converted to text and stored in `data/corpus/`."
    )

    # Upload widget
    uploaded_pdf = st.file_uploader("Upload PDF file", type=["pdf"])

    if uploaded_pdf:
        st.info(f"Selected file: **{uploaded_pdf.name}**")
        if st.button("📤 Upload & Process"):
            with st.spinner("Uploading and processing the PDF..."):
                files = {"file": (uploaded_pdf.name, uploaded_pdf.getvalue(), "application/pdf")}
                try:
                    response = requests.post(f"{FASTAPI_URL}/upload/pdf", files=files)
                    if response.status_code == 200:
                        st.success("🎉 Document uploaded and processed successfully!")
                        st.json(response.json())
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"❌ Request failed: {e}")

    st.markdown("---")
    st.subheader("📁 Existing Documents")

    try:
        res = requests.get(f"{FASTAPI_URL}/documents/list")
        if res.status_code == 200:
            docs = res.json().get("documents", [])
            if docs:
                for d in docs:
                    st.write(f"- {d}")
            else:
                st.info("No documents uploaded yet.")
        else:
            st.warning("Could not fetch document list")
    except Exception as e:
        st.error(f"Failed to fetch list: {e}")
