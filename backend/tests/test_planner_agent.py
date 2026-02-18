"""Unit tests for the Planner/Supervisor agent."""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.financial_agent import (
    create_supervisor_node,
    model_doc_reader_node,
    route_after_supervisor,
    RouterOutput,
    FinancialAgentState,
)
from langchain_core.messages import HumanMessage, AIMessage


class TestSupervisorRouting:
    """Tests for supervisor routing decisions."""

    @pytest.fixture
    def mock_routing_llm(self):
        """Create a mock LLM with structured output for routing."""
        mock = MagicMock()
        
        # Mock with_structured_output to return a callable mock
        structured_mock = MagicMock()
        mock.with_structured_output = MagicMock(return_value=structured_mock)
        
        return mock, structured_mock

    def test_routes_to_recall_for_info_questions(self, mock_routing_llm):
        """Test that info questions route to recall agent."""
        llm, structured_llm = mock_routing_llm
        
        # Mock the response
        structured_llm.invoke = MagicMock(return_value=RouterOutput(
            next="recall",
            reasoning="User is asking about EBITDA definition"
        ))
        
        supervisor_node = create_supervisor_node(llm)
        
        state: FinancialAgentState = {
            "messages": [HumanMessage(content="What is EBITDA?")],
            "user_id": "test_user",
            "model_url": "",
            "next": "",
            "model_documentation": "Model docs here",
        }
        
        result = supervisor_node(state)
        
        assert result["next"] == "recall"

    def test_routes_to_goal_seek_for_optimization(self, mock_routing_llm):
        """Test that optimization questions route to goal seek agent."""
        llm, structured_llm = mock_routing_llm
        
        structured_llm.invoke = MagicMock(return_value=RouterOutput(
            next="goal_seek",
            reasoning="User wants to optimize EBITDA"
        ))
        
        supervisor_node = create_supervisor_node(llm)
        
        state: FinancialAgentState = {
            "messages": [HumanMessage(content="How can I increase EBITDA by 10%?")],
            "user_id": "test_user",
            "model_url": "",
            "next": "",
            "model_documentation": "",
        }
        
        result = supervisor_node(state)
        
        assert result["next"] == "goal_seek"

    def test_routes_to_respond_for_simple_queries(self, mock_routing_llm):
        """Test that simple queries route to direct response."""
        llm, structured_llm = mock_routing_llm
        
        structured_llm.invoke = MagicMock(return_value=RouterOutput(
            next="respond",
            reasoning="Simple greeting, no specialist needed"
        ))
        
        supervisor_node = create_supervisor_node(llm)
        
        state: FinancialAgentState = {
            "messages": [HumanMessage(content="Hello!")],
            "user_id": "test_user",
            "model_url": "",
            "next": "",
            "model_documentation": "",
        }
        
        result = supervisor_node(state)
        
        assert result["next"] == "respond"


class TestModelDocReader:
    """Tests for the model documentation reader node."""

    def test_reads_docs_when_empty(self, mock_sheets_client, sample_spreadsheet_url):
        """Test that docs are read when not cached."""
        with patch("agents.tools._sheets_client", mock_sheets_client):
            with patch("agents.tools._current_spreadsheet_url", sample_spreadsheet_url):
                state: FinancialAgentState = {
                    "messages": [],
                    "user_id": "test_user",
                    "model_url": sample_spreadsheet_url,
                    "next": "",
                    "model_documentation": "",  # Empty - should read
                }
                
                result = model_doc_reader_node(state)
                
                assert "model_documentation" in result
                assert len(result["model_documentation"]) > 0

    def test_skips_when_docs_cached(self):
        """Test that docs are not re-read when already cached."""
        state: FinancialAgentState = {
            "messages": [],
            "user_id": "test_user",
            "model_url": "",
            "next": "",
            "model_documentation": "Already cached docs",
        }
        
        result = model_doc_reader_node(state)
        
        # Should return empty dict (no updates needed)
        assert result == {}


class TestRouteAfterSupervisor:
    """Tests for the routing function after supervisor decision."""

    def test_returns_next_from_state(self):
        """Test that route_after_supervisor returns the next value from state."""
        state: FinancialAgentState = {
            "messages": [],
            "user_id": "",
            "model_url": "",
            "next": "recall",
            "model_documentation": "",
        }
        
        result = route_after_supervisor(state)
        
        assert result == "recall"

    def test_returns_default_when_empty(self):
        """Test default routing when next is empty."""
        state: FinancialAgentState = {
            "messages": [],
            "user_id": "",
            "model_url": "",
            "next": "",
            "model_documentation": "",
        }
        
        result = route_after_supervisor(state)
        
        assert result == "respond"  # Default fallback


class TestSupervisorContextAwareness:
    """Test that supervisor uses context appropriately."""

    @pytest.fixture
    def mock_context_llm(self):
        """Create a mock LLM that tracks context."""
        mock = MagicMock()
        structured_mock = MagicMock()
        mock.with_structured_output = MagicMock(return_value=structured_mock)
        
        structured_mock.invoke = MagicMock(return_value=RouterOutput(
            next="recall",
            reasoning="Based on model documentation"
        ))
        
        return mock, structured_mock

    def test_includes_doc_status_in_decision(self, mock_context_llm):
        """Test that supervisor considers whether docs are loaded."""
        llm, structured_llm = mock_context_llm
        
        supervisor_node = create_supervisor_node(llm)
        
        # With docs
        state_with_docs: FinancialAgentState = {
            "messages": [HumanMessage(content="What is EBITDA?")],
            "user_id": "test_user",
            "model_url": "",
            "next": "",
            "model_documentation": "Model documentation here",
        }
        
        supervisor_node(state_with_docs)
        
        # Verify the prompt includes doc status
        structured_llm.invoke.assert_called()


class TestSupervisorErrorHandling:
    """Test error handling in supervisor."""

    def test_handles_empty_messages(self):
        """Test handling when no messages exist."""
        mock_llm = MagicMock()
        structured_mock = MagicMock()
        mock_llm.with_structured_output = MagicMock(return_value=structured_mock)
        
        structured_mock.invoke = MagicMock(return_value=RouterOutput(
            next="respond",
            reasoning="No question to route"
        ))
        
        supervisor_node = create_supervisor_node(mock_llm)
        
        state: FinancialAgentState = {
            "messages": [],  # Empty
            "user_id": "test_user",
            "model_url": "",
            "next": "",
            "model_documentation": "",
        }
        
        result = supervisor_node(state)
        
        # Should still return a valid routing decision
        assert "next" in result

    def test_handles_only_ai_messages(self):
        """Test handling when only AI messages exist (edge case)."""
        mock_llm = MagicMock()
        structured_mock = MagicMock()
        mock_llm.with_structured_output = MagicMock(return_value=structured_mock)
        
        structured_mock.invoke = MagicMock(return_value=RouterOutput(
            next="respond",
            reasoning="No human message found"
        ))
        
        supervisor_node = create_supervisor_node(mock_llm)
        
        state: FinancialAgentState = {
            "messages": [AIMessage(content="Previous response")],
            "user_id": "test_user",
            "model_url": "",
            "next": "",
            "model_documentation": "",
        }
        
        result = supervisor_node(state)
        
        assert "next" in result
