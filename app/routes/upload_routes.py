from fastapi import APIRouter, UploadFile, File, HTTPException
import fitz  # PyMuPDF
import os
from pathlib import Path

from app.agents.retriever_agent import RetrieverAgent

router = APIRouter()

CORPUS_DIR = Path("data/corpus")
CORPUS_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------------------------------
# UPLOAD PDF
# -----------------------------------------------------
@router.post("/upload/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    pdf_bytes = await file.read()

    pdf_path = CORPUS_DIR / file.filename
    text_path = pdf_path.with_suffix(".txt")

    # Save PDF
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    # Convert PDF → text
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""

        for page in doc:
            text += page.get_text()

        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF parsing failed: {e}")

    # 🔥 REBUILD FAISS AUTOMATICALLY
    retriever = RetrieverAgent()
    retriever._auto_build_index()

    return {
        "status": "success",
        "message": "Uploaded, parsed, and FAISS rebuilt.",
        "pdf": file.filename,
        "txt": text_path.name,
    }


# -----------------------------------------------------
# LIST ALL DOCUMENTS
# -----------------------------------------------------
@router.get("/documents/list")
def list_documents():
    files = sorted([f.name for f in CORPUS_DIR.iterdir()])
    return {"documents": files}


# -----------------------------------------------------
# DELETE DOCUMENT + REBUILD INDEX
# -----------------------------------------------------
@router.delete("/documents/delete/{filename}")
def delete_document(filename: str):
    target = CORPUS_DIR / filename

    if not target.exists():
        raise HTTPException(status_code=404, detail="File not found")

    target.unlink()

    # Also delete paired .txt file
    txt_version = target.with_suffix(".txt")
    if txt_version.exists():
        txt_version.unlink()

    # REBUILD FAISS
    retriever = RetrieverAgent()
    retriever._auto_build_index()

    return {"status": "success", "message": f"{filename} deleted and index rebuilt"}
