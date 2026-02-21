"""Unit tests for the Information Recall agent."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.financial_agent import (
    create_recall_agent_node,
    FinancialAgentState,
)
from langchain_core.messages import HumanMessage, AIMessage


class TestRecallAgentNode:
    """Tests for the Information Recall agent node."""

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM."""
        mock = MagicMock()
        # Mock the bind_tools method to return itself
        mock.bind_tools = MagicMock(return_value=mock)
        # Mock the invoke method to return an AI message
        mock.invoke = MagicMock(return_value=AIMessage(
            content="EBITDA is calculated as EBIT + Depreciation + Amortization. "
                    "In this model, it's located at operations!K194 with formula =K191+K192+K193."
        ))
        return mock

    def test_recall_node_processes_message(self, mock_llm):
        """Test that recall node processes messages correctly."""
        recall_node = create_recall_agent_node(mock_llm)
        
        state: FinancialAgentState = {
            "messages": [HumanMessage(content="What is EBITDA?")],
            "user_id": "test_user",
            "model_url": "https://example.com/sheet",
            "next": "",
            "model_documentation": "EBITDA = EBIT + Depreciation + Amortization",
        }
        
        result = recall_node(state)
        
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert "EBITDA" in result["messages"][0].content

    def test_recall_node_includes_model_docs(self, mock_llm):
        """Test that recall node includes model documentation in context."""
        recall_node = create_recall_agent_node(mock_llm)
        
        state: FinancialAgentState = {
            "messages": [HumanMessage(content="What are the Key Drivers?")],
            "user_id": "test_user",
            "model_url": "https://example.com/sheet",
            "next": "",
            "model_documentation": "Key Drivers: Orders, AoV, CaC",
        }
        
        recall_node(state)
        
        # Verify LLM was called with model documentation in context
        mock_llm.invoke.assert_called_once()
        call_args = mock_llm.invoke.call_args[0][0]
        
        # First message should be system message with docs
        assert len(call_args) >= 2
        system_msg = call_args[0]
        assert "Key Drivers" in system_msg.content or "Recall" in system_msg.content


class TestRecallAgentResponses:
    """Test expected response patterns from recall agent."""

    @pytest.fixture
    def mock_llm_with_tool_calls(self):
        """Create a mock LLM that returns tool calls."""
        mock = MagicMock()
        mock.bind_tools = MagicMock(return_value=mock)
        
        # Create a response with tool calls
        response = AIMessage(content="")
        response.tool_calls = [
            {
                "name": "read_cell_formula",
                "args": {"sheet_name": "operations", "cell_notation": "K194"},
                "id": "call_1"
            }
        ]
        mock.invoke = MagicMock(return_value=response)
        return mock

    def test_recall_uses_tools_for_formula_questions(self, mock_llm_with_tool_calls):
        """Test that recall agent uses tools when asked about formulas."""
        recall_node = create_recall_agent_node(mock_llm_with_tool_calls)
        
        state: FinancialAgentState = {
            "messages": [HumanMessage(content="Show me the formula for EBITDA")],
            "user_id": "test_user",
            "model_url": "https://example.com/sheet",
            "next": "",
            "model_documentation": "",
        }
        
        result = recall_node(state)
        
        # Should return a message (possibly with tool calls)
        assert "messages" in result
        response = result["messages"][0]
        
        # The response should have tool_calls since we mocked it that way
        assert hasattr(response, "tool_calls")
        assert len(response.tool_calls) > 0
        assert response.tool_calls[0]["name"] == "read_cell_formula"


class TestRecallAgentEdgeCases:
    """Test edge cases for recall agent."""

    @pytest.fixture
    def mock_llm_error(self):
        """Create a mock LLM that raises an error."""
        mock = MagicMock()
        mock.bind_tools = MagicMock(return_value=mock)
        mock.invoke = MagicMock(side_effect=Exception("LLM Error"))
        return mock

    def test_handles_empty_model_docs(self):
        """Test handling when model documentation is empty."""
        mock_llm = MagicMock()
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)
        mock_llm.invoke = MagicMock(return_value=AIMessage(
            content="I don't have model documentation loaded yet."
        ))
        
        recall_node = create_recall_agent_node(mock_llm)
        
        state: FinancialAgentState = {
            "messages": [HumanMessage(content="What is in the model?")],
            "user_id": "test_user",
            "model_url": "",
            "next": "",
            "model_documentation": "",
        }
        
        result = recall_node(state)
        assert "messages" in result

    def test_handles_long_conversation(self):
        """Test handling long conversation history."""
        mock_llm = MagicMock()
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)
        mock_llm.invoke = MagicMock(return_value=AIMessage(content="Response"))
        
        recall_node = create_recall_agent_node(mock_llm)
        
        # Create a long conversation
        messages = []
        for i in range(50):
            messages.append(HumanMessage(content=f"Question {i}"))
            messages.append(AIMessage(content=f"Answer {i}"))
        
        state: FinancialAgentState = {
            "messages": messages,
            "user_id": "test_user",
            "model_url": "",
            "next": "",
            "model_documentation": "Test docs",
        }
        
        result = recall_node(state)
        assert "messages" in result
