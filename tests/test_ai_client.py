"""Tests for the Groq-powered AI client."""

import os
from unittest.mock import MagicMock, patch

import pytest

from assistant.ai.client import ask_ai, load_api_key


class TestLoadApiKey:
    def test_returns_key_when_set(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "test-key-123")
        assert load_api_key() == "test-key-123"

    def test_raises_when_not_set(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
            load_api_key()


class TestAskAi:
    def test_calls_groq_api(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "test-key")

        mock_message = MagicMock()
        mock_message.content = "Hello from Groq!"

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch("assistant.ai.client.Groq") as MockGroq:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            MockGroq.return_value = mock_client

            result = ask_ai("test prompt")

            assert result == "Hello from Groq!"
            MockGroq.assert_called_once_with(api_key="test-key")
            mock_client.chat.completions.create.assert_called_once()
            call_kwargs = mock_client.chat.completions.create.call_args[1]
            assert call_kwargs["model"] == "llama3-70b-8192"
            assert len(call_kwargs["messages"]) == 2
            assert call_kwargs["messages"][1]["content"] == "test prompt"

    def test_custom_model(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "test-key")

        mock_message = MagicMock()
        mock_message.content = "response"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch("assistant.ai.client.Groq") as MockGroq:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            MockGroq.return_value = mock_client

            ask_ai("test", model="mixtral-8x7b-32768")
            call_kwargs = mock_client.chat.completions.create.call_args[1]
            assert call_kwargs["model"] == "mixtral-8x7b-32768"

    def test_empty_response_raises(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "test-key")

        mock_response = MagicMock()
        mock_response.choices = []

        with patch("assistant.ai.client.Groq") as MockGroq:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            MockGroq.return_value = mock_client

            with pytest.raises(RuntimeError, match="empty response"):
                ask_ai("test")

    def test_groq_error_raises_runtime(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "test-key")

        from groq import GroqError

        with patch("assistant.ai.client.Groq") as MockGroq:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = GroqError("API failure")
            MockGroq.return_value = mock_client

            with pytest.raises(RuntimeError, match="Groq API request failed"):
                ask_ai("test")

    def test_missing_key_raises(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
            ask_ai("test")
