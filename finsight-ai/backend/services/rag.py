"""
FinSight AI — RAG Service

Retrieval-Augmented Generation using ChromaDB and Gemini embeddings.

Collection:
    finsight_corpus

Pipeline:
    Document
        ↓
    Chunking
        ↓
    Gemini Embeddings
        ↓
    ChromaDB
        ↓
    Query Embedding
        ↓
    Top-K Semantic Retrieval
        ↓
    Context Assembler
        ↓
    Gemini
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Any, Optional

import chromadb
from dotenv import load_dotenv
from loguru import logger


# ============================================================
# Configuration
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env", override=True)

COLLECTION_NAME = "finsight_corpus"

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200

MAX_RETRIEVAL_CHUNKS = 3

_chroma_dir = os.getenv(
    "CHROMA_PERSIST_DIR",
    "./chroma_data",
)
CHROMA_PERSIST_DIR = (
    _chroma_dir
    if Path(_chroma_dir).is_absolute()
    else str(BACKEND_DIR / _chroma_dir)
)


# ============================================================
# Singleton ChromaDB
# ============================================================

_chroma_client = None
_collection = None


def get_chroma_client():
    """
    Return a singleton ChromaDB persistent client.
    """

    global _chroma_client

    if _chroma_client is None:

        Path(
            CHROMA_PERSIST_DIR
        ).mkdir(
            parents=True,
            exist_ok=True,
        )

        _chroma_client = (
            chromadb.PersistentClient(
                path=CHROMA_PERSIST_DIR
            )
        )

        logger.info(
            f"✅ ChromaDB initialized at "
            f"{CHROMA_PERSIST_DIR}"
        )

    return _chroma_client


def get_collection():
    """
    Get or create the FinSight financial knowledge collection.
    """

    global _collection

    if _collection is None:

        client = get_chroma_client()

        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={
                "description": (
                    "FinSight AI financial knowledge base"
                ),
                "embedding_model": (
                    "gemini-embedding-2"
                ),
            },
        )

        logger.info(
            f"✅ ChromaDB collection "
            f"'{COLLECTION_NAME}' ready "
            f"({ _collection.count() } chunks)"
        )

    return _collection


# ============================================================
# Text Cleaning
# ============================================================

def _clean_text(text: str) -> str:
    """
    Normalize extracted document text.
    """

    if not text:
        return ""

    # Normalize whitespace.
    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    # Normalize excessive newlines.
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


# ============================================================
# Chunking
# ============================================================

def _chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """
    Split text into overlapping chunks.

    Attempts to preserve sentence/paragraph boundaries.
    """

    text = _clean_text(text)

    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than zero."
        )

    if overlap < 0:
        raise ValueError(
            "chunk_overlap cannot be negative."
        )

    if overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size."
        )

    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []

    start = 0
    text_length = len(text)

    while start < text_length:

        proposed_end = min(
            start + chunk_size,
            text_length,
        )

        end = proposed_end

        if proposed_end < text_length:

            candidate = text[
                start:proposed_end
            ]

            # Prefer paragraph boundary.
            paragraph_break = candidate.rfind(
                "\n\n"
            )

            if (
                paragraph_break
                >= int(chunk_size * 0.5)
            ):
                end = (
                    start
                    + paragraph_break
                    + 2
                )

            else:

                # Prefer sentence boundary.
                sentence_matches = list(
                    re.finditer(
                        r"[.!?]\s+",
                        candidate,
                    )
                )

                if sentence_matches:

                    best = sentence_matches[-1]

                    if (
                        best.start()
                        >= int(chunk_size * 0.5)
                    ):
                        end = (
                            start
                            + best.end()
                        )

        chunk = text[
            start:end
        ].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        next_start = end - overlap

        # Prevent infinite loops.
        if next_start <= start:
            next_start = end

        start = next_start

    return chunks


# ============================================================
# Stable IDs
# ============================================================

def _chunk_id(
    doc_id: str,
    chunk_index: int,
    chunk_text: str,
) -> str:
    """
    Create deterministic ChromaDB document IDs.
    """

    content_hash = hashlib.sha1(
        chunk_text.encode(
            "utf-8",
            errors="ignore",
        )
    ).hexdigest()[:12]

    return (
        f"{doc_id}_"
        f"chunk_{chunk_index}_"
        f"{content_hash}"
    )


# ============================================================
# Document Ingestion
# ============================================================

async def ingest_document(
    doc_id: str,
    text: str,
    metadata: Optional[dict] = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> int:
    """
    Ingest a text document into ChromaDB.

    Steps:
        1. Clean text
        2. Chunk text
        3. Generate Gemini embeddings
        4. Validate embedding count
        5. Upsert into ChromaDB

    Returns:
        Number of successfully prepared chunks.
    """

    if not doc_id or not doc_id.strip():
        raise ValueError(
            "doc_id cannot be empty."
        )

    cleaned_text = _clean_text(text)

    if not cleaned_text:
        logger.warning(
            f"No text available for document "
            f"'{doc_id}'."
        )
        return 0

    from services.gemini import (
        get_embeddings_batch,
    )

    chunks = _chunk_text(
        cleaned_text,
        chunk_size=chunk_size,
        overlap=chunk_overlap,
    )

    if not chunks:

        logger.warning(
            f"No chunks produced for "
            f"'{doc_id}'."
        )

        return 0

    logger.info(
        f"📄 Document '{doc_id}' "
        f"split into {len(chunks)} chunks."
    )

    # --------------------------------------------------------
    # Generate embeddings
    # --------------------------------------------------------

    embeddings = await get_embeddings_batch(
        chunks
    )

    if len(embeddings) != len(chunks):

        logger.error(
            f"Embedding count mismatch for "
            f"'{doc_id}': "
            f"{len(chunks)} chunks, "
            f"{len(embeddings)} embeddings."
        )

        raise RuntimeError(
            "Embedding count does not match "
            "chunk count."
        )

    # Never fall back to Chroma's own embedding
    # when using Gemini embeddings.
    invalid_embeddings = [
        index
        for index, embedding in enumerate(
            embeddings
        )
        if not embedding
    ]

    if invalid_embeddings:

        logger.error(
            f"Missing embeddings for "
            f"'{doc_id}' at indexes: "
            f"{invalid_embeddings[:10]}"
        )

        raise RuntimeError(
            "One or more document embeddings "
            "could not be generated."
        )

    # --------------------------------------------------------
    # ChromaDB records
    # --------------------------------------------------------

    collection = get_collection()

    base_metadata = (
        metadata.copy()
        if metadata
        else {}
    )

    base_metadata.setdefault(
        "embedding_model",
        "gemini-embedding-2",
    )

    base_metadata.setdefault(
        "document_id",
        doc_id,
    )

    ids = []
    metadatas = []

    for index, chunk in enumerate(chunks):

        ids.append(
            _chunk_id(
                doc_id,
                index,
                chunk,
            )
        )

        metadatas.append(
            {
                **base_metadata,
                "doc_id": doc_id,
                "chunk_index": index,
                "total_chunks": len(chunks),
            }
        )

    # --------------------------------------------------------
    # Upsert
    # --------------------------------------------------------

    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    logger.info(
        f"✅ Ingested {len(chunks)} chunks "
        f"for document '{doc_id}'."
    )

    return len(chunks)


# ============================================================
# PDF Ingestion
# ============================================================

async def ingest_pdf(
    file_path: str,
    doc_id: Optional[str] = None,
) -> int:
    """
    Extract text from a PDF and ingest it.
    """

    path = Path(file_path)

    if not path.exists():
        logger.error(
            f"PDF not found: {file_path}"
        )
        return 0

    if path.suffix.lower() != ".pdf":
        logger.error(
            f"Not a PDF file: {file_path}"
        )
        return 0

    try:

        from pypdf import PdfReader

        reader = PdfReader(
            str(path)
        )

        pages: list[str] = []

        for page_number, page in enumerate(
            reader.pages,
            start=1,
        ):

            try:
                page_text = (
                    page.extract_text()
                    or ""
                )

                if page_text.strip():
                    pages.append(
                        f"\n[Page {page_number}]\n"
                        f"{page_text}"
                    )

            except Exception as exc:

                logger.warning(
                    f"Could not extract "
                    f"page {page_number} "
                    f"from {path.name}: {exc}"
                )

        text = "\n".join(
            pages
        )

        if not text.strip():

            logger.warning(
                f"No text extracted from "
                f"{path.name}."
            )

            return 0

        document_id = (
            doc_id.strip()
            if doc_id and doc_id.strip()
            else path.stem
        )

        metadata = {
            "source": "pdf",
            "filename": path.name,
            "file_path": str(path),
        }

        return await ingest_document(
            document_id,
            text,
            metadata=metadata,
        )

    except ImportError:

        logger.error(
            "pypdf is not installed. "
            "Install it with: "
            "pip install pypdf"
        )

        return 0

    except Exception as exc:

        logger.exception(
            f"PDF ingestion failed for "
            f"{path.name}: {exc}"
        )

        return 0


# ============================================================
# Retrieval
# ============================================================

async def retrieve_relevant(
    query: str,
    top_k: int = MAX_RETRIEVAL_CHUNKS,
) -> list[dict]:
    """
    Retrieve semantically relevant financial documents.

    Pipeline:
        query
          ↓
        Gemini embedding
          ↓
        ChromaDB semantic search
          ↓
        top-k chunks
    """

    if not query or not query.strip():
        return []

    top_k = max(
        1,
        min(
            int(top_k),
            10,
        ),
    )

    try:

        from services.gemini import (
            get_embedding,
        )

        collection = get_collection()

        count = collection.count()

        if count == 0:

            logger.debug(
                "RAG collection is empty."
            )

            return []

        query_embedding = await get_embedding(
            query
        )

        if not query_embedding:

            logger.error(
                "Unable to create query embedding. "
                "Skipping RAG retrieval."
            )

            return []

        results = collection.query(
            query_embeddings=[
                query_embedding
            ],
            n_results=min(
                top_k,
                count,
            ),
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )

        documents = (
            results.get(
                "documents"
            )
            or [[]]
        )

        metadatas = (
            results.get(
                "metadatas"
            )
            or [[]]
        )

        distances = (
            results.get(
                "distances"
            )
            or [[]]
        )

        if not documents or not documents[0]:
            return []

        retrieved: list[dict] = []

        for index, document in enumerate(
            documents[0]
        ):

            if not document:
                continue

            metadata = {}

            if (
                metadatas
                and metadatas[0]
                and index < len(
                    metadatas[0]
                )
            ):
                metadata = (
                    metadatas[0][index]
                    or {}
                )

            distance = None

            if (
                distances
                and distances[0]
                and index < len(
                    distances[0]
                )
            ):
                distance = (
                    distances[0][index]
                )

            retrieved.append(
                {
                    "text": document,
                    "metadata": metadata,
                    "distance": distance,
                }
            )

        logger.info(
            f"🔍 RAG retrieved "
            f"{len(retrieved)} chunks "
            f"for query."
        )

        return retrieved

    except Exception as exc:

        logger.exception(
            f"RAG retrieval failed: {exc}"
        )

        return []


# ============================================================
# Document Management
# ============================================================

def delete_document(
    doc_id: str,
) -> bool:
    """
    Delete all chunks belonging to a document.
    """

    if not doc_id:
        return False

    try:

        collection = get_collection()

        collection.delete(
            where={
                "doc_id": doc_id
            }
        )

        logger.info(
            f"🗑️ Deleted RAG document: "
            f"{doc_id}"
        )

        return True

    except Exception as exc:

        logger.exception(
            f"Failed to delete RAG document "
            f"{doc_id}: {exc}"
        )

        return False


def reset_collection() -> None:
    """
    Delete and recreate the RAG collection.

    Useful when migrating embedding models.

    WARNING:
    This removes all indexed documents.
    """

    global _collection

    client = get_chroma_client()

    try:

        client.delete_collection(
            name=COLLECTION_NAME
        )

        logger.warning(
            f"⚠️ Deleted ChromaDB collection "
            f"'{COLLECTION_NAME}'."
        )

    except Exception as exc:

        logger.debug(
            f"Collection deletion skipped: "
            f"{exc}"
        )

    _collection = None

    get_collection()

    logger.info(
        f"✅ Fresh RAG collection "
        f"'{COLLECTION_NAME}' created."
    )


# ============================================================
# Statistics
# ============================================================

def get_rag_stats() -> dict:
    """
    Return RAG collection information.
    """

    collection = get_collection()

    count = collection.count()

    return {
        "collection_name": COLLECTION_NAME,
        "document_count": count,
        "embedding_model": "gemini-embedding-2",
        "persist_directory": CHROMA_PERSIST_DIR,
        "status": (
            "ready"
            if count > 0
            else "empty"
        ),
    }


# ============================================================
# Health Check
# ============================================================

def rag_health_check() -> dict:
    """
    Basic RAG health check.
    """

    try:

        collection = get_collection()

        return {
            "healthy": True,
            "collection": COLLECTION_NAME,
            "count": collection.count(),
        }

    except Exception as exc:

        logger.exception(
            f"RAG health check failed: {exc}"
        )

        return {
            "healthy": False,
            "collection": COLLECTION_NAME,
            "count": 0,
            "error": str(exc),
        }