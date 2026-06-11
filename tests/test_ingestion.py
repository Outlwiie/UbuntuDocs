# chunk size, overlap, metadata correctness
"""
Tests for ingestion.py

We test the pure Python logic only — chunking and duplicate detection.
We do NOT test the embedding or ChromaDB calls because those depend on
external services. We mock them out so tests run fast with no side effects.
"""
import pytest
from unittest.mock import patch, MagicMock


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_words(n: int) -> str:
    """Return a string of n unique words."""
    return " ".join(f"word{i}" for i in range(n))


# ── Chunking tests ─────────────────────────────────────────────────────────────

from backend.ingestion import _chunk_text


class TestChunkText:

    def test_short_text_gives_one_chunk(self):
        """Text shorter than CHUNK_SIZE should produce exactly one chunk."""
        text   = make_words(100)
        chunks = _chunk_text(text)
        assert len(chunks) == 1

    def test_long_text_gives_multiple_chunks(self):
        """Text much longer than CHUNK_SIZE should be split into several chunks."""
        text   = make_words(2000)
        chunks = _chunk_text(text)
        assert len(chunks) > 1

    def test_no_chunk_exceeds_size_limit(self):
        """No chunk should have more words than CHUNK_SIZE allows."""
        from backend.ingestion import CHUNK_SIZE
        text   = make_words(2000)
        chunks = _chunk_text(text)
        for chunk in chunks:
            assert len(chunk.split()) <= CHUNK_SIZE

    def test_overlap_between_adjacent_chunks(self):
        """The last word of chunk N should appear in chunk N+1 (overlap)."""
        from backend.ingestion import CHUNK_OVERLAP
        text   = make_words(2000)
        chunks = _chunk_text(text)

        if len(chunks) > 1:
            last_words_of_first  = set(chunks[0].split()[-CHUNK_OVERLAP:])
            first_words_of_second = set(chunks[1].split()[:CHUNK_OVERLAP])
            overlap = last_words_of_first & first_words_of_second
            assert len(overlap) > 0, "Expected overlap between adjacent chunks"

    def test_empty_text_returns_empty_list(self):
        """Empty string input should return an empty list, not crash."""
        chunks = _chunk_text("")
        assert chunks == []


# ── Duplicate detection tests ──────────────────────────────────────────────────

class TestDuplicateDetection:

    @patch("backend.ingestion._collection")
    def test_duplicate_filename_raises(self, mock_collection):
        """Ingesting the same filename twice should raise a ValueError."""
        # Simulate a non-empty result — file already exists
        mock_collection.get.return_value = {"ids": ["some-id"]}

        from backend.ingestion import _filename_exists
        assert _filename_exists("report.pdf") is True

    @patch("backend.ingestion._collection")
    def test_new_filename_is_allowed(self, mock_collection):
        """A filename not yet in the collection should return False."""
        # Simulate empty result — file does not exist
        mock_collection.get.return_value = {"ids": []}

        from backend.ingestion import _filename_exists
        assert _filename_exists("new_file.pdf") is False


# ── Ingest pipeline tests ──────────────────────────────────────────────────────

class TestIngestPdf:

    @patch("backend.ingestion._collection")
    @patch("backend.ingestion._embedder")
    @patch("backend.ingestion._extract_text")
    @patch("backend.ingestion._filename_exists")
    def test_ingest_returns_summary(
        self, mock_exists, mock_extract, mock_embedder, mock_collection
    ):
        """ingest_pdf should return document_id, filename, and chunk count."""
        mock_exists.return_value  = False
        mock_extract.return_value = make_words(1000)
        mock_embedder.encode.return_value = MagicMock(tolist=lambda: [[0.1] * 384])
        mock_collection.upsert.return_value = None

        from backend.ingestion import ingest_pdf
        result = ingest_pdf("fake/path.pdf", "report.pdf")

        assert result["filename"] == "report.pdf"
        assert "document_id" in result
        assert result["chunks"] > 0

    @patch("backend.ingestion._filename_exists")
    def test_duplicate_raises_value_error(self, mock_exists):
        """ingest_pdf should raise ValueError if filename already exists."""
        mock_exists.return_value = True

        from backend.ingestion import ingest_pdf
        with pytest.raises(ValueError, match="already been ingested"):
            ingest_pdf("fake/path.pdf", "report.pdf")