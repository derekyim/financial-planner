"""Unit tests for the Goal Seek agent."""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.financial_agent import (
    create_goal_seek_agent_node,
    FinancialAgentState,
)
from langchain_core.messages import HumanMessage, AIMessage


class TestGoalSeekAgentNode:
    """Tests for the Goal Seek agent node."""

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM."""
        mock = MagicMock()
        mock.bind_tools = MagicMock(return_value=mock)
        mock.invoke = MagicMock(return_value=AIMessage(
            content="""Based on my analysis, here are 3 solutions to increase EBITDA by 10%:

**Solution 1 (Recommended):**
- Increase Orders by 8%
- Increase AoV by 5%
- Results: EBITDA +12%

**Solution 2:**
- Decrease CaC by 15%
- Keep other drivers unchanged
- Results: EBITDA +11%

**Solution 3:**
- Increase Orders by 12%
- Results: EBITDA +10%"""
        ))
        return mock

    def test_goal_seek_node_processes_message(self, mock_llm):
        """Test that goal seek node processes messages correctly."""
        goal_seek_node = create_goal_seek_agent_node(mock_llm)
        
        state: FinancialAgentState = {
            "messages": [HumanMessage(content="Increase EBITDA by 10%")],
            "user_id": "test_user",
            "model_url": "https://example.com/sheet",
            "next": "",
            "model_documentation": "EBITDA = EBIT + Depreciation",
        }
        
        result = goal_seek_node(state)
        
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert "Solution" in result["messages"][0].content

    def test_goal_seek_includes_model_docs(self, mock_llm):
        """Test that goal seek node includes model documentation."""
        goal_seek_node = create_goal_seek_agent_node(mock_llm)
        
        state: FinancialAgentState = {
            "messages": [HumanMessage(content="Optimize for Cash")],
            "user_id": "test_user",
            "model_url": "https://example.com/sheet",
            "next": "",
            "model_documentation": "Cash calculation: ...",
        }
        
        goal_seek_node(state)
        
        mock_llm.invoke.assert_called_once()
        call_args = mock_llm.invoke.call_args[0][0]
        
        # First message should be system message
        assert len(call_args) >= 2


class TestGoalSeekAgentToolUsage:
    """Test tool usage patterns for goal seek agent."""

    @pytest.fixture
    def mock_llm_with_write_tools(self):
        """Create a mock LLM that uses write tools."""
        mock = MagicMock()
        mock.bind_tools = MagicMock(return_value=mock)
        
        response = AIMessage(content="")
        response.tool_calls = [
            {
                "name": "read_key_drivers_and_results",
                "args": {},
                "id": "call_1"
            },
            {
                "name": "write_cell_value",
                "args": {
                    "sheet_name": "M - Monthly",
                    "cell_notation": "BT5",
                    "value": "250000"
                },
                "id": "call_2"
            }
        ]
        mock.invoke = MagicMock(return_value=response)
        return mock

    def test_goal_seek_uses_write_tools(self, mock_llm_with_write_tools):
        """Test that goal seek agent can use write tools."""
        goal_seek_node = create_goal_seek_agent_node(mock_llm_with_write_tools)
        
        state: FinancialAgentState = {
            "messages": [HumanMessage(content="Find optimal driver values")],
            "user_id": "test_user",
            "model_url": "https://example.com/sheet",
            "next": "",
            "model_documentation": "",
        }
        
        result = goal_seek_node(state)
        
        response = result["messages"][0]
        assert hasattr(response, "tool_calls")
        
        # Should include write_cell_value tool
        tool_names = [tc["name"] for tc in response.tool_calls]
        assert "write_cell_value" in tool_names


class TestGoalSeekMultipleTargets:
    """Test goal seek with multiple optimization targets."""

    @pytest.fixture
    def mock_llm_multi_target(self):
        """Create a mock LLM for multi-target optimization."""
        mock = MagicMock()
        mock.bind_tools = MagicMock(return_value=mock)
        mock.invoke = MagicMock(return_value=AIMessage(
            content="""Analyzing your 3 targets:
1. EBITDA +10%
2. Gross Sales +10% YoY
3. Cash > $1M

After testing 20 scenarios using Latin hypercube sampling:

**Feasible Solution 1:**
- Orders: 240,000 (+8.5%)
- AoV: $77.50 (+2.8%)
- CaC: $41.00 (-5.7%)
- Results: EBITDA +11.2%, Gross Sales +11.5%, Cash $1.15M

**Feasible Solution 2:**
...

All solutions maintain the Cash constraint."""
        ))
        return mock

    def test_handles_multiple_targets(self, mock_llm_multi_target):
        """Test goal seek with multiple optimization targets."""
        goal_seek_node = create_goal_seek_agent_node(mock_llm_multi_target)
        
        state: FinancialAgentState = {
            "messages": [HumanMessage(
                content="I want: 1) EBITDA +10%, 2) Gross Sales +10% YoY, 3) Cash > $1M"
            )],
            "user_id": "test_user",
            "model_url": "https://example.com/sheet",
            "next": "",
            "model_documentation": "",
        }
        
        result = goal_seek_node(state)
        
        content = result["messages"][0].content
        assert "EBITDA" in content
        assert "Gross Sales" in content
        assert "Cash" in content


class TestGoalSeekEdgeCases:
    """Test edge cases for goal seek agent."""

    def test_handles_infeasible_goals(self):
        """Test handling when goals cannot be achieved."""
        mock_llm = MagicMock()
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)
        mock_llm.invoke = MagicMock(return_value=AIMessage(
            content="After analyzing the model, your targets appear to be mutually exclusive. "
                    "Increasing EBITDA by 500% while maintaining current pricing is not feasible."
        ))
        
        goal_seek_node = create_goal_seek_agent_node(mock_llm)
        
        state: FinancialAgentState = {
            "messages": [HumanMessage(content="Increase EBITDA by 500%")],
            "user_id": "test_user",
            "model_url": "",
            "next": "",
            "model_documentation": "",
        }
        
        result = goal_seek_node(state)
        
        assert "messages" in result
        content = result["messages"][0].content
        assert "not feasible" in content.lower() or "infeasible" in content.lower() or "mutually exclusive" in content.lower()

    def test_handles_single_driver_optimization(self):
        """Test optimization with a single driver constraint."""
        mock_llm = MagicMock()
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)
        mock_llm.invoke = MagicMock(return_value=AIMessage(
            content="To achieve +10% EBITDA by only changing Orders: "
                    "Increase Orders to 243,328 (+10%)"
        ))
        
        goal_seek_node = create_goal_seek_agent_node(mock_llm)
        
        state: FinancialAgentState = {
            "messages": [HumanMessage(
                content="Increase EBITDA by 10% by only changing Orders"
            )],
            "user_id": "test_user",
            "model_url": "",
            "next": "",
            "model_documentation": "",
        }
        
        result = goal_seek_node(state)
        
        assert "messages" in result
        assert "Orders" in result["messages"][0].content
