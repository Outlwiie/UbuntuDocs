# query returns relevant chunks, top-k works
"""
Tests for retrieval.py

We mock ChromaDB and the embedder so no real database or model is needed.
We test that retrieve() returns the right structure and handles edge cases.
"""
from unittest.mock import patch, MagicMock


class TestRetrieve:

    @patch("retrieval._collection")
    @patch("retrieval._embedder")
    def test_returns_list_of_dicts(self, mock_embedder, mock_collection):
        """retrieve() should return a list of dicts with 'text' and 'filename'."""
        mock_embedder.encode.return_value = MagicMock(tolist=lambda: [[0.1] * 384])
        mock_collection.count.return_value = 3
        mock_collection.query.return_value = {
            "documents": [["chunk one", "chunk two"]],
            "metadatas": [
                [{"filename": "a.pdf"}, {"filename": "b.pdf"}]
            ],
        }

        from retrieval import retrieve
        results = retrieve("what is the refund policy?")

        assert isinstance(results, list)
        assert len(results) == 2
        assert results[0]["text"] == "chunk one"
        assert results[0]["filename"] == "a.pdf"

    @patch("retrieval._collection")
    @patch("retrieval._embedder")
    def test_empty_collection_returns_empty_list(self, mock_embedder, mock_collection):
        """retrieve() should return [] if the collection has no documents."""
        mock_collection.count.return_value = 0

        from retrieval import retrieve
        results = retrieve("anything")

        assert results == []
        mock_collection.query.assert_not_called()

    @patch("retrieval._collection")
    @patch("retrieval._embedder")
    def test_top_k_does_not_exceed_collection_size(self, mock_embedder, mock_collection):
        """n_results passed to ChromaDB should never exceed the collection size."""
        mock_embedder.encode.return_value = MagicMock(tolist=lambda: [[0.1] * 384])
        mock_collection.count.return_value = 2  # only 2 chunks exist
        mock_collection.query.return_value = {
            "documents": [["only chunk"]],
            "metadatas": [[{"filename": "small.pdf"}]],
        }

        from retrieval import retrieve
        retrieve("test question")

        # Check that n_results was capped at 2, not the default TOP_K of 5
        call_kwargs = mock_collection.query.call_args[1]
        assert call_kwargs["n_results"] <= 2

    @patch("retrieval._collection")
    @patch("retrieval._embedder")
    def test_each_result_has_required_keys(self, mock_embedder, mock_collection):
        """Every result dict must have 'text' and 'filename' keys."""
        mock_embedder.encode.return_value = MagicMock(tolist=lambda: [[0.1] * 384])
        mock_collection.count.return_value = 1
        mock_collection.query.return_value = {
            "documents": [["some text"]],
            "metadatas": [[{"filename": "doc.pdf"}]],
        }

        from retrieval import retrieve
        results = retrieve("question")

        for r in results:
            assert "text" in r
            assert "filename" in r