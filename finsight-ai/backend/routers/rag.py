"""
FinSight AI — RAG Router

Provides:
- PDF/TXT/Markdown document ingestion
- Raw text ingestion
- RAG collection statistics

The router delegates all embedding/vector database work
to services.rag.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from loguru import logger

from dependencies import get_current_user


router = APIRouter()


# ============================================================
# Configuration
# ============================================================

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".md",
}

# Prevent accidentally uploading extremely large files.
# Adjust if your project needs a larger limit.
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


# ============================================================
# Helpers
# ============================================================

def _safe_filename(filename: Optional[str]) -> str:
    """
    Return a safe basename for temporary file storage.
    """

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    # Remove any directory components.
    safe_name = Path(filename).name

    if not safe_name or safe_name in {".", ".."}:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename.",
        )

    return safe_name


async def _save_upload_temporarily(
    file: UploadFile,
) -> tuple[str, str]:
    """
    Save an uploaded file into a temporary directory.

    Returns:
        (temporary_path, safe_filename)
    """

    safe_filename = _safe_filename(
        file.filename
    )

    extension = Path(
        safe_filename
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file format: {extension or 'none'}. "
                f"Allowed formats: PDF, TXT, MD."
            ),
        )

    temp_dir = tempfile.mkdtemp(
        prefix="finsight_rag_"
    )

    temp_path = os.path.join(
        temp_dir,
        safe_filename,
    )

    total_size = 0

    try:
        with open(
            temp_path,
            "wb",
        ) as output:

            while True:

                chunk = await file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "Uploaded file is too large. "
                            "Maximum size is 20 MB."
                        ),
                    )

                output.write(chunk)

        return temp_path, safe_filename

    except Exception:
        shutil.rmtree(
            temp_dir,
            ignore_errors=True,
        )
        raise


# ============================================================
# RAG Ingestion
# ============================================================

@router.post("/rag/ingest")
async def rag_ingest(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    doc_id: Optional[str] = Form(None),
    current_user: str = Depends(
        get_current_user
    ),
):
    """
    Ingest either:
    - PDF/TXT/Markdown file
    - Raw text

    The actual embedding and ChromaDB operations are handled
    by services.rag.
    """

    if not file and not text:
        raise HTTPException(
            status_code=400,
            detail=(
                "Either a file or text must be provided."
            ),
        )

    if file and text:
        raise HTTPException(
            status_code=400,
            detail=(
                "Provide either a file or text, "
                "not both."
            ),
        )

    logger.info(
        f"RAG ingestion request from user "
        f"{current_user}"
    )

    try:
        from services.rag import (
            ingest_document,
            ingest_pdf,
        )

        # ====================================================
        # File ingestion
        # ====================================================

        if file:

            temp_path = None

            try:
                temp_path, safe_filename = (
                    await _save_upload_temporarily(
                        file
                    )
                )

                extension = Path(
                    safe_filename
                ).suffix.lower()

                document_id = (
                    doc_id.strip()
                    if doc_id and doc_id.strip()
                    else Path(
                        safe_filename
                    ).stem
                )

                if not document_id:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "A valid document ID "
                            "could not be determined."
                        ),
                    )

                logger.info(
                    f"Ingesting document "
                    f"{document_id} "
                    f"({safe_filename})"
                )

                # ------------------------------------------------
                # PDF
                # ------------------------------------------------

                if extension == ".pdf":

                    chunks = await ingest_pdf(
                        temp_path,
                        doc_id=document_id,
                    )

                # ------------------------------------------------
                # TXT / Markdown
                # ------------------------------------------------

                else:

                    with open(
                        temp_path,
                        "r",
                        encoding="utf-8",
                        errors="ignore",
                    ) as input_file:

                        file_content = (
                            input_file.read()
                        )

                    if not file_content.strip():
                        raise HTTPException(
                            status_code=400,
                            detail=(
                                "The uploaded document "
                                "is empty."
                            ),
                        )

                    metadata = {
                        "source": "uploaded_file",
                        "filename": safe_filename,
                        "document_id": document_id,
                        "uploaded_by": current_user,
                    }

                    chunks = await ingest_document(
                        document_id,
                        file_content,
                        metadata=metadata,
                    )

                logger.info(
                    f"✅ RAG ingestion completed: "
                    f"{document_id} | "
                    f"chunks={chunks}"
                )

                return {
                    "status": "success",
                    "message": (
                        f"Successfully ingested "
                        f"'{safe_filename}'."
                    ),
                    "document_id": document_id,
                    "chunks": chunks,
                }

            finally:

                # Always clean temporary data.
                if temp_path:

                    try:
                        shutil.rmtree(
                            os.path.dirname(
                                temp_path
                            ),
                            ignore_errors=True,
                        )
                    except Exception as cleanup_error:
                        logger.warning(
                            f"Temporary RAG cleanup failed: "
                            f"{cleanup_error}"
                        )

        # ====================================================
        # Raw text ingestion
        # ====================================================

        if text:

            if not doc_id or not doc_id.strip():
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "doc_id is required "
                        "for text ingestion."
                    ),
                )

            cleaned_text = text.strip()

            if not cleaned_text:
                raise HTTPException(
                    status_code=400,
                    detail="Text cannot be empty.",
                )

            document_id = doc_id.strip()

            metadata = {
                "source": "manual_text",
                "document_id": document_id,
                "uploaded_by": current_user,
            }

            chunks = await ingest_document(
                document_id,
                cleaned_text,
                metadata=metadata,
            )

            logger.info(
                f"✅ Manual RAG ingestion completed: "
                f"{document_id} | chunks={chunks}"
            )

            return {
                "status": "success",
                "message": (
                    f"Successfully ingested "
                    f"text document '{document_id}'."
                ),
                "document_id": document_id,
                "chunks": chunks,
            }

        raise HTTPException(
            status_code=400,
            detail="No valid ingestion input provided.",
        )

    except HTTPException:
        raise

    except Exception as exc:

        logger.exception(
            f"RAG ingestion failed: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to ingest the document. "
                "Please check the document format and "
                "RAG service configuration."
            ),
        )


# ============================================================
# RAG Statistics
# ============================================================

@router.get("/rag/stats")
async def rag_stats(
    current_user: str = Depends(
        get_current_user
    ),
):
    """
    Return current RAG collection statistics.
    """

    try:

        from services.rag import get_rag_stats

        stats = get_rag_stats()

        return {
            "status": "success",
            "stats": stats,
        }

    except Exception as exc:

        logger.exception(
            f"RAG stats error: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to retrieve RAG statistics."
            ),
        )