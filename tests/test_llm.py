# prompt is built correctly, response parsed
"""
Tests for llm.py

We mock the requests.post call so no real Ollama instance is needed.
We test prompt construction, response parsing, and error handling.
"""
import pytest
from unittest.mock import patch, MagicMock


SAMPLE_CHUNKS = [
    {"text": "All sales are final except within 30 days.", "filename": "policy.pdf"},
    {"text": "Refunds are processed within 5 business days.", "filename": "policy.pdf"},
]


class TestAsk:

    @patch("backend.llm.requests.post")
    def test_returns_string_answer(self, mock_post):
        """ask() should return the LLM's response as a plain string."""
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"response": "All sales are final except within 30 days."},
        )
        mock_post.return_value.raise_for_status = lambda: None

        from backend.llm import ask
        answer = ask("what is the refund policy?", SAMPLE_CHUNKS)

        assert isinstance(answer, str)
        assert len(answer) > 0

    @patch("backend.llm.requests.post")
    def test_prompt_contains_question(self, mock_post):
        """The prompt sent to Ollama must include the user's question."""
        mock_post.return_value = MagicMock(
            json=lambda: {"response": "some answer"},
        )
        mock_post.return_value.raise_for_status = lambda: None

        from backend.llm import ask
        ask("what is the refund policy?", SAMPLE_CHUNKS)

        prompt_sent = mock_post.call_args[1]["json"]["prompt"]
        assert "what is the refund policy?" in prompt_sent

    @patch("backend.llm.requests.post")
    def test_prompt_contains_context(self, mock_post):
        """The prompt sent to Ollama must include the retrieved chunk text."""
        mock_post.return_value = MagicMock(
            json=lambda: {"response": "some answer"},
        )
        mock_post.return_value.raise_for_status = lambda: None

        from backend.llm import ask
        ask("what is the refund policy?", SAMPLE_CHUNKS)

        prompt_sent = mock_post.call_args[1]["json"]["prompt"]
        assert "All sales are final except within 30 days." in prompt_sent
        assert "policy.pdf" in prompt_sent

    def test_empty_chunks_returns_fallback(self):
        """ask() with no chunks should return a fallback message, not crash."""
        from backend.llm import ask
        answer = ask("anything", [])

        assert isinstance(answer, str)
        assert len(answer) > 0

    @patch("backend.llm.requests.post")
    def test_connection_error_raises(self, mock_post):
        """ask() should raise ConnectionError if Ollama is not reachable."""
        import requests as req
        mock_post.side_effect = req.exceptions.ConnectionError

        from backend.llm import ask
        with pytest.raises(ConnectionError):
            ask("test question", SAMPLE_CHUNKS)

    @patch("backend.llm.requests.post")
    def test_timeout_raises(self, mock_post):
        """ask() should raise TimeoutError if Ollama takes too long."""
        import requests as req
        mock_post.side_effect = req.exceptions.Timeout

        from backend.llm import ask
        with pytest.raises(TimeoutError):
            ask("test question", SAMPLE_CHUNKS)

    @patch("backend.llm.requests.post")
    def test_malformed_response_raises(self, mock_post):
        """ask() should raise RuntimeError if Ollama response has no 'response' key."""
        mock_post.return_value = MagicMock(
            json=lambda: {"unexpected_key": "something"},
        )
        mock_post.return_value.raise_for_status = lambda: None

        from backend.llm import ask
        with pytest.raises(RuntimeError):
            ask("test question", SAMPLE_CHUNKS)