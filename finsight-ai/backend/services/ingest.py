
"""
FinSight AI — Document Ingestion CLI
Parses PDF/TXT documents, chunks text into overlapping segments,
embeds each chunk via Gemini text-embedding-004, and stores into ChromaDB.

Usage:
    python -m services.ingest --path ./documents/
    python -m services.ingest --path ./documents/drhp.pdf
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

from loguru import logger

# Ensure backend root is on sys.path so sibling imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ── Text chunking ────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping character-based chunks.

    Args:
        text: Raw text content to chunk.
        chunk_size: Maximum characters per chunk.
        overlap: Number of overlapping characters between consecutive chunks.

    Returns:
        List of text chunks.
    """
    if not text or not text.strip():
        return []

    text = text.strip()
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size

        # Try to break at a sentence boundary within the last 20% of the chunk
        if end < len(text):
            boundary_zone = text[start + int(chunk_size * 0.8) : end]
            for sep in [". ", ".\n", "? ", "! ", "\n\n", "\n"]:
                last_sep = boundary_zone.rfind(sep)
                if last_sep >= 0:
                    end = start + int(chunk_size * 0.8) + last_sep + len(sep)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Advance start, keeping overlap
        start = end - overlap if end < len(text) else end

    return chunks


# ── File reading ─────────────────────────────────────────────

def read_pdf(file_path: Path) -> str:
    """Extract text from a PDF using pypdf."""
    try:
        from pypdf import PdfReader
    except ImportError:
        logger.error("pypdf not installed. Install with: pip install pypdf")
        return ""

    try:
        reader = PdfReader(str(file_path))
        pages = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                pages.append(page_text)
        return "\n\n".join(pages)
    except Exception as e:
        logger.error(f"Error reading PDF {file_path.name}: {e}")
        return ""


def read_txt(file_path: Path) -> str:
    """Read a plain-text file."""
    try:
        return file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        logger.error(f"Error reading TXT {file_path.name}: {e}")
        return ""


# ── Ingestion pipeline ──────────────────────────────────────

async def ingest_file(file_path: Path, chunk_size: int = 500, overlap: int = 50) -> dict:
    """
    Ingest a single PDF or TXT file into the ChromaDB vector store.

    Returns dict: {filename, chunks_count, status, error}
    """
    from services.rag import get_collection
    from services.gemini import get_embeddings_batch

    filename = file_path.name
    doc_id = file_path.stem

    # Read file content
    if file_path.suffix.lower() == ".pdf":
        text = read_pdf(file_path)
    elif file_path.suffix.lower() == ".txt":
        text = read_txt(file_path)
    else:
        return {"filename": filename, "chunks_count": 0, "status": "skipped", "error": f"Unsupported file type: {file_path.suffix}"}

    if not text or not text.strip():
        return {"filename": filename, "chunks_count": 0, "status": "failed", "error": "No text extracted"}

    # Chunk the text
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    if not chunks:
        return {"filename": filename, "chunks_count": 0, "status": "failed", "error": "Chunking produced no output"}

    logger.info(f"📄 {filename}: {len(text)} chars → {len(chunks)} chunks")

    # Generate embeddings
    try:
        embeddings = await get_embeddings_batch(chunks)
    except Exception as e:
        return {"filename": filename, "chunks_count": 0, "status": "failed", "error": f"Embedding error: {e}"}

    # Prepare IDs and metadata
    timestamp = datetime.now().isoformat()
    ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "doc_id": doc_id,
            "source_filename": filename,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "ingested_at": timestamp,
        }
        for i in range(len(chunks))
    ]

    # Store in ChromaDB
    try:
        collection = get_collection()
        collection.upsert(
            ids=ids,
            documents=chunks,
            embeddings=embeddings if all(embeddings) else None,
            metadatas=metadatas,
        )
    except Exception as e:
        return {"filename": filename, "chunks_count": 0, "status": "failed", "error": f"ChromaDB error: {e}"}

    return {"filename": filename, "chunks_count": len(chunks), "status": "success", "error": None}


async def ingest_path(path: str, chunk_size: int = 500, overlap: int = 50) -> dict:
    """
    Ingest a file or directory of files into the vector store.

    Returns summary dict with total documents, chunks, and failures.
    """
    target = Path(path)

    if not target.exists():
        logger.error(f"Path does not exist: {path}")
        return {"error": f"Path does not exist: {path}"}

    # Collect files
    files: list[Path] = []
    if target.is_file():
        files = [target]
    elif target.is_dir():
        for ext in ("*.pdf", "*.txt"):
            files.extend(target.glob(ext))
        # Also search recursively
        for ext in ("**/*.pdf", "**/*.txt"):
            for f in target.glob(ext):
                if f not in files:
                    files.append(f)

    if not files:
        logger.warning(f"No .pdf or .txt files found in {path}")
        return {"total_documents": 0, "total_chunks": 0, "failures": 0, "details": []}

    logger.info(f"📂 Found {len(files)} document(s) to ingest")

    results = []
    total_chunks = 0
    failures = 0

    for file_path in files:
        logger.info(f"  → Processing: {file_path.name}")
        result = await ingest_file(file_path, chunk_size=chunk_size, overlap=overlap)
        results.append(result)

        if result["status"] == "success":
            total_chunks += result["chunks_count"]
        else:
            failures += 1
            if result.get("error"):
                logger.error(f"    ✗ {file_path.name}: {result['error']}")

    summary = {
        "total_documents": len(files),
        "total_chunks": total_chunks,
        "failures": failures,
        "details": results,
    }

    return summary


# ── CLI entry point ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="FinSight AI — Ingest PDF/TXT documents into the RAG vector store"
    )
    parser.add_argument(
        "--path",
        required=True,
        help="Path to a single file or directory of .pdf/.txt documents",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        help="Maximum characters per chunk (default: 500)",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=50,
        help="Overlap between consecutive chunks (default: 50)",
    )
    args = parser.parse_args()

    # Load .env for API keys
    from dotenv import load_dotenv
    load_dotenv()

    logger.info("═" * 50)
    logger.info("FinSight AI — Document Ingestion Pipeline")
    logger.info("═" * 50)
    logger.info(f"Path:       {args.path}")
    logger.info(f"Chunk size: {args.chunk_size} chars")
    logger.info(f"Overlap:    {args.overlap} chars")
    logger.info("═" * 50)

    summary = asyncio.run(ingest_path(args.path, chunk_size=args.chunk_size, overlap=args.overlap))

    if summary.get("error"):
        logger.error(summary["error"])
        sys.exit(1)

    # Print summary
    print("\n" + "=" * 50)
    print("INGESTION SUMMARY")
    print("=" * 50)
    print(f"  Total documents processed: {summary['total_documents']}")
    print(f"  Total chunks embedded:     {summary['total_chunks']}")
    print(f"  Failures:                  {summary['failures']}")
    print("=" * 50)

    for detail in summary.get("details", []):
        status_icon = "✅" if detail["status"] == "success" else "❌" if detail["status"] == "failed" else "⏭️"
        print(f"  {status_icon} {detail['filename']}: {detail['chunks_count']} chunks ({detail['status']})")
        if detail.get("error"):
            print(f"     Error: {detail['error']}")

    print()


if __name__ == "__main__":
    main()
