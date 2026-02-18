"""Unit tests for the FastAPI backend endpoints."""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from api.index import app


client = TestClient(app)


class TestHealthEndpoint:
    """Tests for the root health check endpoint."""

    def test_health_returns_ok(self):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestChatEndpoint:
    """Tests for the /api/chat endpoint."""

    @patch("api.index._ensure_agent")
    @patch("api.index.chat", create=True)
    def test_chat_returns_reply(self, mock_chat_fn, mock_ensure):
        """Mock the agent and verify the endpoint returns a reply."""
        with patch("agents.financial_agent.chat", return_value="EBITDA is a profitability metric."):
            with patch("api.index._agent_initialized", True):
                mock_import = MagicMock()
                mock_import.return_value = "EBITDA is a profitability metric."

                with patch.dict("sys.modules", {"agents.financial_agent": MagicMock(chat=mock_import)}):
                    response = client.post("/api/chat", json={"message": "What is EBITDA?"})
                    assert response.status_code == 200
                    data = response.json()
                    assert "reply" in data

    def test_chat_requires_message(self):
        response = client.post("/api/chat", json={})
        assert response.status_code == 422

    def test_chat_accepts_optional_thread_id(self):
        """Verify the schema accepts thread_id."""
        with patch("api.index._ensure_agent"):
            with patch("api.index._agent_initialized", True):
                with patch.dict("sys.modules", {"agents.financial_agent": MagicMock(chat=MagicMock(return_value="ok"))}):
                    response = client.post(
                        "/api/chat",
                        json={"message": "hi", "thread_id": "test-thread-123"},
                    )
                    assert response.status_code in [200, 500, 503]
