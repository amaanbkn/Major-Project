from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional
from loguru import logger
import os
import shutil
from dependencies import get_current_user

router = APIRouter()

@router.post("/rag/ingest")
async def rag_ingest(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    doc_id: Optional[str] = Form(None),
    current_user: str = Depends(get_current_user)
):
    """
    Ingest a document (PDF/text file or raw text) into ChromaDB.
    """
    from services.rag import ingest_document, ingest_pdf
    
    if not file and not text:
        raise HTTPException(status_code=400, detail="Either file or text must be provided")
        
    try:
        if file:
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in [".pdf", ".txt", ".md"]:
                raise HTTPException(status_code=400, detail=f"Unsupported file format: {ext}")
            
            temp_dir = "./temp_ingest"
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, file.filename)
            
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                
            try:
                document_id = doc_id or os.path.splitext(file.filename)[0]
                if ext == ".pdf":
                    chunks = await ingest_pdf(temp_path, doc_id=document_id)
                else:
                    with open(temp_path, "r", encoding="utf-8", errors="ignore") as f:
                        file_content = f.read()
                    metadata = {"source": "file", "filename": file.filename}
                    chunks = await ingest_document(document_id, file_content, metadata=metadata)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
            return {
                "status": "success",
                "message": f"Successfully ingested file '{file.filename}'",
                "chunks": chunks
            }
            
        elif text:
            if not doc_id:
                raise HTTPException(status_code=400, detail="doc_id is required for text ingestion")
            
            metadata = {"source": "manual_text"}
            chunks = await ingest_document(doc_id, text, metadata=metadata)
            return {
                "status": "success",
                "message": f"Successfully ingested text document '{doc_id}'",
                "chunks": chunks
            }
            
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to ingest document: {str(e)}")

@router.get("/rag/stats")
async def rag_stats(current_user: str = Depends(get_current_user)):
    """Get RAG stats."""
    from services.rag import get_rag_stats
    try:
        return get_rag_stats()
    except Exception as e:
        logger.error(f"RAG stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
