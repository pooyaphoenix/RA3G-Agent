import streamlit as st
import requests
import os
from pathlib import Path


def _fmt_size(num_bytes: int) -> str:
    """Human-readable file size."""
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


def render_documents_tab(FASTAPI_URL: str):
    st.subheader("📄 Corpus Documents")

    # ── session state for delete confirmation ──
    if "pending_delete" not in st.session_state:
        st.session_state.pending_delete = None

    # --------------- UPLOAD --------------------
    with st.expander("📤 Upload New Document", expanded=True):
        uploaded_pdf = st.file_uploader(
            "Choose a PDF file", type=["pdf"], label_visibility="collapsed"
        )
        if uploaded_pdf:
            st.caption(f"Selected: **{uploaded_pdf.name}** ({_fmt_size(len(uploaded_pdf.getvalue()))})")
            if st.button("Upload & Rebuild Index", type="primary", use_container_width=True):
                with st.spinner("Processing and rebuilding index…"):
                    try:
                        files = {
                            "file": (uploaded_pdf.name, uploaded_pdf.getvalue(), "application/pdf")
                        }
                        r = requests.post(f"{FASTAPI_URL}/upload/pdf", files=files)
                        if r.status_code == 200:
                            st.success("Document uploaded and FAISS index rebuilt!")
                            st.json(r.json())
                            st.rerun()
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
    except Exception:
        st.error("Failed to fetch document list. Is the backend running?")
        return

    if not docs:
        st.info("No documents uploaded yet.")
        return

    # Resolve corpus path for file sizes (best-effort)
    corpus_dir = Path(__file__).parent.parent.parent / "data" / "corpus"

    # Show stats
    total = len(docs)
    pdf_count = sum(1 for d in docs if d.lower().endswith(".pdf"))
    txt_count = sum(1 for d in docs if d.lower().endswith(".txt"))
    st.caption(f"{total} file(s) — {pdf_count} PDF, {txt_count} TXT")

    for doc in docs:
        # File size
        fpath = corpus_dir / doc
        size_str = _fmt_size(fpath.stat().st_size) if fpath.exists() else "—"

        # Icon by type
        icon = "📄" if doc.lower().endswith(".pdf") else "📝"

        col1, col2, col3 = st.columns([5, 1, 1])
        with col1:
            st.markdown(f"{icon} **{doc}**")
            st.caption(size_str)
        with col2:
            st.write("")  # vertical spacer
        with col3:
            if st.button("🗑️", key=f"del_{doc}", help=f"Delete {doc}"):
                st.session_state.pending_delete = doc

        # Confirmation row (same card, full width)
        if st.session_state.pending_delete == doc:
            st.warning(f"Delete **{doc}**? This will rebuild the FAISS index.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Confirm Delete", key=f"confirm_{doc}", use_container_width=True):
                    try:
                        r = requests.delete(f"{FASTAPI_URL}/documents/delete/{doc}")
                        if r.status_code == 200:
                            st.success(f"{doc} deleted and index rebuilt.")
                            st.session_state.pending_delete = None
                            st.rerun()
                        else:
                            st.error(r.text)
                    except Exception as e:
                        st.error(f"Failed to delete: {e}")
            with c2:
                if st.button("❌ Cancel", key=f"cancel_{doc}", use_container_width=True):
                    st.session_state.pending_delete = None
                    st.rerun()

        st.divider()
