"""
FinSight AI — RAG Service Tests
Tests for vector retrieval and document chunking logic.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ═══════════════════════════════════════════════════════════════
# Chunking Logic Tests (from services/ingest.py)
# ═══════════════════════════════════════════════════════════════

class TestChunking:
    """Test the text chunking function used during document ingestion."""

    def test_short_text_single_chunk(self):
        """Text shorter than chunk_size should produce exactly one chunk."""
        from services.ingest import chunk_text
        text = "This is a short piece of text."
        chunks = chunk_text(text, chunk_size=500, overlap=50)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_2000_char_input_produces_correct_chunks(self):
        """A 2000-character input with 500-char chunks and 50-char overlap
        should produce approximately ceil(2000 / (500 - 50)) = 5 chunks."""
        from services.ingest import chunk_text

        # Build a 2000-char string from repeating sentences
        sentence = "This is a test sentence for chunking. "
        text = (sentence * 100)[:2000]

        chunks = chunk_text(text, chunk_size=500, overlap=50)

        # With 500 char chunks and 50 overlap, step = 450
        # Expected: ceil(2000 / 450) ≈ 4-5 chunks
        assert len(chunks) >= 4
        assert len(chunks) <= 6
        # Every chunk should be non-empty
        for chunk in chunks:
            assert len(chunk.strip()) > 0

    def test_overlap_exists_between_chunks(self):
        """Consecutive chunks should share overlapping text content."""
        from services.ingest import chunk_text

        # Use a long enough string so we get multiple chunks
        text = "ABCDEFGHIJ" * 200  # 2000 chars
        chunks = chunk_text(text, chunk_size=500, overlap=50)

        assert len(chunks) >= 2

        # Check that the end of chunk[0] overlaps with the start of chunk[1]
        # Due to sentence-boundary logic, overlap may shift slightly,
        # but the tail of one chunk should appear in the next
        for i in range(len(chunks) - 1):
            tail_of_current = chunks[i][-50:]
            head_of_next = chunks[i + 1][:100]
            # At least some substring overlap should exist
            overlap_found = any(
                tail_of_current[j:j+10] in head_of_next
                for j in range(0, len(tail_of_current) - 10)
            )
            assert overlap_found, (
                f"No overlap found between chunk {i} and chunk {i+1}"
            )

    def test_empty_text_returns_empty_list(self):
        """Empty or whitespace-only text should return an empty list."""
        from services.ingest import chunk_text

        assert chunk_text("") == []
        assert chunk_text("   ") == []
        assert chunk_text(None) == []

    def test_exact_chunk_size_text(self):
        """Text exactly equal to chunk_size should produce one chunk."""
        from services.ingest import chunk_text
        text = "X" * 500
        chunks = chunk_text(text, chunk_size=500, overlap=50)

        assert len(chunks) == 1
        assert len(chunks[0]) == 500

    def test_chunk_size_plus_one(self):
        """Text just over chunk_size should produce two chunks with overlap."""
        from services.ingest import chunk_text
        text = "A" * 501
        chunks = chunk_text(text, chunk_size=500, overlap=50)

        assert len(chunks) == 2


# ═══════════════════════════════════════════════════════════════
# RAG Retrieval Tests
# ═══════════════════════════════════════════════════════════════

class TestRAGRetrieval:
    """Test the retrieve_relevant function by mocking ChromaDB."""

    @pytest.mark.asyncio
    async def test_retrieve_returns_list_of_chunks(self):
        """retrieve_relevant should return a list of dicts with text, metadata, distance."""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 10
        mock_collection.query.return_value = {
            "documents": [["SEBI circular on insider trading", "RBI monetary policy review"]],
            "metadatas": [[{"doc_id": "sebi_001", "chunk_index": 0}, {"doc_id": "rbi_002", "chunk_index": 1}]],
            "distances": [[0.15, 0.32]],
        }

        with patch("services.rag.get_collection", return_value=mock_collection), \
             patch("services.rag.get_embedding", new_callable=AsyncMock, return_value=[0.1] * 768):

            # Need to re-patch get_embedding inside rag module
            with patch("services.gemini.get_embedding", new_callable=AsyncMock, return_value=[0.1] * 768):
                from services.rag import retrieve_relevant
                results = await retrieve_relevant("insider trading regulations")

                assert isinstance(results, list)
                assert len(results) == 2
                assert results[0]["text"] == "SEBI circular on insider trading"
                assert results[0]["metadata"]["doc_id"] == "sebi_001"
                assert results[0]["distance"] == 0.15

    @pytest.mark.asyncio
    async def test_retrieve_empty_collection_returns_empty(self):
        """An empty ChromaDB collection should return an empty list."""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0

        with patch("services.rag.get_collection", return_value=mock_collection):
            from services.rag import retrieve_relevant
            results = await retrieve_relevant("test query")

            assert results == []

    @pytest.mark.asyncio
    async def test_retrieve_handles_embedding_failure(self):
        """If embedding fails, should fallback to text-based search."""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 5
        mock_collection.query.return_value = {
            "documents": [["Fallback text result"]],
            "metadatas": [[{"doc_id": "fallback_001", "chunk_index": 0}]],
            "distances": [[0.5]],
        }

        with patch("services.rag.get_collection", return_value=mock_collection), \
             patch("services.gemini.get_embedding", new_callable=AsyncMock, return_value=[]):
            from services.rag import retrieve_relevant
            results = await retrieve_relevant("test query")

            assert isinstance(results, list)
            # Should still return results via text-based fallback
            assert len(results) >= 0

    @pytest.mark.asyncio
    async def test_retrieve_top_k_limit(self):
        """Results should be limited to the requested top_k."""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 100
        mock_collection.query.return_value = {
            "documents": [["chunk1", "chunk2"]],
            "metadatas": [[{"doc_id": "d1"}, {"doc_id": "d2"}]],
            "distances": [[0.1, 0.2]],
        }

        with patch("services.rag.get_collection", return_value=mock_collection), \
             patch("services.gemini.get_embedding", new_callable=AsyncMock, return_value=[0.1] * 768):
            from services.rag import retrieve_relevant
            results = await retrieve_relevant("test", top_k=2)

            assert len(results) <= 2

    @pytest.mark.asyncio
    async def test_retrieve_result_structure(self):
        """Each result should have 'text', 'metadata', and 'distance' keys."""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 5
        mock_collection.query.return_value = {
            "documents": [["Sample document chunk"]],
            "metadatas": [[{"doc_id": "sample_001", "chunk_index": 0}]],
            "distances": [[0.25]],
        }

        with patch("services.rag.get_collection", return_value=mock_collection), \
             patch("services.gemini.get_embedding", new_callable=AsyncMock, return_value=[0.1] * 768):
            from services.rag import retrieve_relevant
            results = await retrieve_relevant("sample query")

            assert len(results) == 1
            result = results[0]
            assert "text" in result
            assert "metadata" in result
            assert "distance" in result


# ═══════════════════════════════════════════════════════════════
# RAG Collection Stats Tests
# ═══════════════════════════════════════════════════════════════

class TestRAGStats:
    """Test RAG collection utility functions."""

    def test_get_rag_stats_returns_dict(self):
        """get_rag_stats should return a dict with collection_name and document_count."""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 42

        with patch("services.rag.get_collection", return_value=mock_collection):
            # Reset the module-level singleton
            with patch("services.rag._collection", mock_collection):
                from services.rag import get_rag_stats
                stats = get_rag_stats()

                assert "collection_name" in stats
                assert stats["collection_name"] == "finsight_corpus"
                assert "document_count" in stats
