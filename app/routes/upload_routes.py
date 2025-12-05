from fastapi import APIRouter, UploadFile, File, HTTPException
import fitz  # PyMuPDF
import os

router = APIRouter()

CORPUS_DIR = "data/corpus"
os.makedirs(CORPUS_DIR, exist_ok=True)

@router.post("/upload/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    pdf_bytes = await file.read()

    # Save original PDF
    pdf_path = os.path.join(CORPUS_DIR, file.filename)
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    # Convert PDF → text
    text_path = pdf_path.replace(".pdf", ".txt")

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()

        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "status": "success",
        "message": "PDF uploaded and converted to text",
        "pdf_file": file.filename,
        "text_file": os.path.basename(text_path),
    }


@router.get("/documents/list")
def list_documents():
    try:
        files = os.listdir(CORPUS_DIR)
        return {"documents": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
