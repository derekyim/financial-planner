"""Unit tests for the evals subsystem."""

import pytest
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestRAGEvalRunner:
    """Tests for the RAG evaluation runner."""

    @patch("evals.rag_evals.OpenAIEmbeddings")
    @patch("evals.rag_evals.ChatOpenAI")
    @patch("evals.rag_evals.LangchainLLMWrapper")
    @patch("evals.rag_evals.LangchainEmbeddingsWrapper")
    def test_init(self, mock_emb_wrap, mock_llm_wrap, mock_chat, mock_emb):
        from evals.rag_evals import RAGEvalRunner

        runner = RAGEvalRunner()
        assert len(runner.metrics) == 6

    @patch("evals.rag_evals.OpenAIEmbeddings")
    @patch("evals.rag_evals.ChatOpenAI")
    @patch("evals.rag_evals.LangchainLLMWrapper")
    @patch("evals.rag_evals.LangchainEmbeddingsWrapper")
    def test_load_test_cases(self, mock_emb_wrap, mock_llm_wrap, mock_chat, mock_emb):
        from evals.rag_evals import RAGEvalRunner

        runner = RAGEvalRunner()
        test_cases = runner.load_test_cases()
        assert isinstance(test_cases, list)
        assert len(test_cases) > 0
        assert "question" in test_cases[0]

    @patch("evals.rag_evals.OpenAIEmbeddings")
    @patch("evals.rag_evals.ChatOpenAI")
    @patch("evals.rag_evals.LangchainLLMWrapper")
    @patch("evals.rag_evals.LangchainEmbeddingsWrapper")
    def test_build_samples(self, mock_emb_wrap, mock_llm_wrap, mock_chat, mock_emb):
        from evals.rag_evals import RAGEvalRunner

        runner = RAGEvalRunner()
        test_cases = [
            {"question": "What is EBITDA?", "reference": "A profitability metric."},
        ]

        def mock_retriever(q):
            return ["EBITDA context"]

        samples = runner.build_samples(test_cases, mock_retriever)
        assert len(samples) == 1
        assert samples[0].user_input == "What is EBITDA?"
        assert samples[0].retrieved_contexts == ["EBITDA context"]


class TestAgentEvalRunner:
    """Tests for the Agent evaluation runner."""

    @patch("evals.agent_evals.ChatOpenAI")
    @patch("evals.agent_evals.LangchainLLMWrapper")
    def test_init(self, mock_llm_wrap, mock_chat):
        from evals.agent_evals import AgentEvalRunner

        runner = AgentEvalRunner()
        assert runner.tool_accuracy is not None
        assert runner.goal_accuracy is not None
        assert runner.topic_adherence is not None
