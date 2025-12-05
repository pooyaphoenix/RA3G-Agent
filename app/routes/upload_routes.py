# routes/upload_routes.py

import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from datetime import datetime
import pymupdf, fitz

router = APIRouter()

CORPUS_DIR = "data/corpus"
os.makedirs(CORPUS_DIR, exist_ok=True)


@router.post("/upload/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF, extract text, save it into data/corpus/*.txt
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    try:
        pdf_bytes = await file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read PDF: {str(e)}")

    # Extract plain text
    extracted_text_list = []
    for page in doc:
        extracted_text_list.append(page.get_text("text"))

    extracted_text = "\n".join(extracted_text_list).strip()

    if not extracted_text:
        raise HTTPException(status_code=422, detail="No extractable text found in PDF.")

    # Create output filename
    base_name = file.filename.rsplit(".", 1)[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    txt_file_path = f"{CORPUS_DIR}/{base_name}_{timestamp}.txt"

    # Save text to corpus directory
    with open(txt_file_path, "w", encoding="utf-8") as f:
        f.write(extracted_text)

    return {
        "message": "PDF processed and saved successfully",
        "output_file": txt_file_path,
        "pages": len(doc),
        "characters": len(extracted_text)
    }
