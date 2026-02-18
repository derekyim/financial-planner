"""Unit tests for the RAGAS evaluation framework."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestRAGASEvaluatorInit:
    """Tests for RAGASEvaluator initialization."""

    @patch("shared.evaluations.OpenAIEmbeddings")
    @patch("shared.evaluations.ChatOpenAI")
    @patch("shared.evaluations.LangchainLLMWrapper")
    @patch("shared.evaluations.LangchainEmbeddingsWrapper")
    def test_creates_evaluator(self, mock_emb_wrap, mock_llm_wrap, mock_chat, mock_emb):
        from shared.evaluations import RAGASEvaluator

        evaluator = RAGASEvaluator(evaluator_model="gpt-4o-mini")
        assert evaluator.evaluator_model == "gpt-4o-mini"
        assert evaluator.timeout == 360
        assert len(evaluator.rag_metrics) == 5

    @patch("shared.evaluations.OpenAIEmbeddings")
    @patch("shared.evaluations.ChatOpenAI")
    @patch("shared.evaluations.LangchainLLMWrapper")
    @patch("shared.evaluations.LangchainEmbeddingsWrapper")
    def test_custom_timeout(self, mock_emb_wrap, mock_llm_wrap, mock_chat, mock_emb):
        from shared.evaluations import RAGASEvaluator

        evaluator = RAGASEvaluator(timeout=120)
        assert evaluator.timeout == 120


class TestRAGSampleCreation:
    """Tests for creating evaluation samples."""

    @patch("shared.evaluations.OpenAIEmbeddings")
    @patch("shared.evaluations.ChatOpenAI")
    @patch("shared.evaluations.LangchainLLMWrapper")
    @patch("shared.evaluations.LangchainEmbeddingsWrapper")
    def test_create_rag_sample(self, mock_emb_wrap, mock_llm_wrap, mock_chat, mock_emb):
        from shared.evaluations import RAGASEvaluator

        evaluator = RAGASEvaluator()
        sample = evaluator.create_rag_sample(
            question="What is EBITDA?",
            response="EBITDA is a profitability metric.",
            retrieved_contexts=["EBITDA: Earnings Before Interest..."],
            reference="EBITDA stands for Earnings Before Interest, Taxes, Depreciation, and Amortization.",
        )
        assert sample.user_input == "What is EBITDA?"
        assert sample.response == "EBITDA is a profitability metric."
        assert len(sample.retrieved_contexts) == 1
        assert sample.reference is not None

    @patch("shared.evaluations.OpenAIEmbeddings")
    @patch("shared.evaluations.ChatOpenAI")
    @patch("shared.evaluations.LangchainLLMWrapper")
    @patch("shared.evaluations.LangchainEmbeddingsWrapper")
    def test_create_rag_sample_no_reference(self, mock_emb_wrap, mock_llm_wrap, mock_chat, mock_emb):
        from shared.evaluations import RAGASEvaluator

        evaluator = RAGASEvaluator()
        sample = evaluator.create_rag_sample(
            question="test",
            response="test response",
            retrieved_contexts=["ctx"],
        )
        assert sample.reference is None


class TestEvaluationResults:
    """Tests for evaluation result dataclasses."""

    def test_rag_result_str(self):
        from shared.evaluations import RAGEvaluationResult

        result = RAGEvaluationResult(
            context_recall=0.85,
            faithfulness=0.90,
            factual_correctness=0.88,
            response_relevancy=0.92,
            context_entity_recall=0.75,
        )
        s = str(result)
        assert "0.850" in s
        assert "0.900" in s
        assert "Context Recall" in s

    def test_agent_result_str(self):
        from shared.evaluations import AgentEvaluationResult

        result = AgentEvaluationResult(
            tool_call_accuracy=0.95,
            goal_accuracy=1.0,
            topic_adherence=0.88,
        )
        s = str(result)
        assert "0.950" in s
        assert "1.000" in s
        assert "Tool Call Accuracy" in s


class TestConvenienceFunctions:
    """Tests for convenience helper functions."""

    @patch("shared.evaluations.OpenAIEmbeddings")
    @patch("shared.evaluations.ChatOpenAI")
    @patch("shared.evaluations.LangchainLLMWrapper")
    @patch("shared.evaluations.LangchainEmbeddingsWrapper")
    def test_create_evaluator(self, mock_emb_wrap, mock_llm_wrap, mock_chat, mock_emb):
        from shared.evaluations import create_evaluator, RAGASEvaluator

        evaluator = create_evaluator("gpt-4o-mini")
        assert isinstance(evaluator, RAGASEvaluator)
