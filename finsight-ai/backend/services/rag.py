"""
FinSight AI — RAG Service (Retrieval-Augmented Generation)
ChromaDB-based vector store for financial document retrieval.
- Collection: "finsight_corpus"
- Embedding: Gemini text-embedding-004
- Documents: DRHP prospectuses, SEBI circulars, RBI docs
"""

import os
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings
from loguru import logger

# ── Singleton ChromaDB client ────────────────────────────────
_chroma_client = None
_collection = None
COLLECTION_NAME = "finsight_corpus"


def get_chroma_client():
    """Get or create the ChromaDB persistent client (Singleton)."""
    global _chroma_client
    if _chroma_client is None:
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
        _chroma_client = chromadb.PersistentClient(path=persist_dir)
        logger.info(f"✅ ChromaDB initialized at {persist_dir}")
    return _chroma_client


def get_collection():
    """Get or create the finsight_corpus collection."""
    global _collection
    if _collection is None:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "FinSight AI financial knowledge base"},
        )
        logger.info(f"✅ Collection '{COLLECTION_NAME}' ready ({_collection.count()} documents)")
    return _collection


async def ingest_document(
    doc_id: str,
    text: str,
    metadata: Optional[dict] = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> int:
    """
    Ingest a document into ChromaDB:
    1. Split text into chunks
    2. Generate embeddings via Gemini
    3. Store in ChromaDB with metadata.

    Returns: number of chunks ingested.
    """
    from services.gemini import get_embeddings_batch

    collection = get_collection()

    # Chunk the text
    chunks = _chunk_text(text, chunk_size, chunk_overlap)
    if not chunks:
        logger.warning(f"No chunks produced for document {doc_id}")
        return 0

    # Generate embeddings
    embeddings = await get_embeddings_batch(chunks)

    # Prepare IDs, metadata, and documents
    ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "doc_id": doc_id,
            "chunk_index": i,
            "total_chunks": len(chunks),
            **(metadata or {}),
        }
        for i in range(len(chunks))
    ]

    # Upsert to ChromaDB
    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings if all(embeddings) else None,
        metadatas=metadatas,
    )

    logger.info(f"✅ Ingested {len(chunks)} chunks for document '{doc_id}'")
    return len(chunks)


async def retrieve_relevant(query: str, top_k: int = 3) -> list[dict]:
    """
    Semantic search: embed query → retrieve top-k most relevant chunks.
    Returns list of {text, metadata, distance} dicts.
    """
    from services.gemini import get_embedding

    collection = get_collection()

    if collection.count() == 0:
        logger.debug("RAG collection is empty — no documents to retrieve")
        return []

    # Embed the query
    query_embedding = await get_embedding(query)

    if not query_embedding:
        # Fallback to text-based search
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
        )
    else:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

    # Format results
    retrieved = []
    if results and results["documents"]:
        for i, doc in enumerate(results["documents"][0]):
            retrieved.append({
                "text": doc,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else 0,
            })

    logger.info(f"🔍 RAG retrieved {len(retrieved)} chunks for query")
    return retrieved


async def ingest_pdf(file_path: str, doc_id: Optional[str] = None) -> int:
    """
    Ingest a PDF document into the RAG pipeline.
    Uses basic text extraction (PyPDF2 or pdfminer).
    """
    try:
        from pypdf import PdfReader

        path = Path(file_path)
        if not path.exists():
            logger.error(f"PDF not found: {file_path}")
            return 0

        reader = PdfReader(str(path))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

        if not text.strip():
            logger.warning(f"No text extracted from {file_path}")
            return 0

        doc_id = doc_id or path.stem
        metadata = {
            "source": "pdf",
            "filename": path.name,
            "file_path": str(path),
        }

        return await ingest_document(doc_id, text, metadata)

    except ImportError:
        logger.error("pypdf not installed. Install with: pip install pypdf")
        return 0
    except Exception as e:
        logger.error(f"PDF ingestion error: {e}")
        return 0


def get_rag_stats() -> dict:
    """Get RAG collection statistics."""
    collection = get_collection()
    return {
        "collection_name": COLLECTION_NAME,
        "document_count": collection.count(),
    }


def _chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """
    Split text into overlapping chunks for embedding.
    Tries to split on sentence boundaries.
    """
    if not text or len(text) < chunk_size:
        return [text] if text else []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size

        # Try to break at a sentence boundary
        if end < len(text):
            # Look for sentence-ending punctuation near the end
            for sep in [". ", ".\n", "! ", "? ", "\n\n"]:
                last_sep = text[start:end].rfind(sep)
                if last_sep > chunk_size * 0.5:
                    end = start + last_sep + len(sep)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap

    return chunks
