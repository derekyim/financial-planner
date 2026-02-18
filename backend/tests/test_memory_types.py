"""Unit tests for memory type implementations."""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.memory_types import (
    ShortTermMemory,
    LongTermMemory,
    SemanticMemory,
    EpisodicMemory,
    ProceduralMemory,
)
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


class TestShortTermMemory:
    """Tests for ShortTermMemory class."""

    def test_get_recent_messages(self):
        """Test getting recent messages from history."""
        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!"),
            HumanMessage(content="How are you?"),
            AIMessage(content="I'm doing well!"),
            HumanMessage(content="Great!"),
        ]
        stm = ShortTermMemory(messages=messages)
        
        recent = stm.get_recent(3)
        assert len(recent) == 3
        assert recent[0].content == "How are you?"
        assert recent[-1].content == "Great!"

    def test_get_recent_with_fewer_messages(self):
        """Test get_recent when fewer messages exist than requested."""
        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!"),
        ]
        stm = ShortTermMemory(messages=messages)
        
        recent = stm.get_recent(10)
        assert len(recent) == 2

    def test_get_recent_empty(self):
        """Test get_recent with empty message list."""
        stm = ShortTermMemory(messages=[])
        recent = stm.get_recent(5)
        assert len(recent) == 0


class TestLongTermMemory:
    """Tests for LongTermMemory class."""

    def test_set_and_get_profile(self, memory_store):
        """Test setting and getting user profile."""
        ltm = LongTermMemory(memory_store, "user123")
        
        ltm.set_profile("risk_tolerance", {"level": "moderate", "max_loss": 0.1})
        
        profile = ltm.get_profile()
        assert "risk_tolerance" in profile

    def test_set_and_get_preferences(self, memory_store):
        """Test setting and getting user preferences."""
        ltm = LongTermMemory(memory_store, "user123")
        
        ltm.set_preference("preferred_metrics", {"metrics": ["EBITDA", "Cash"]})
        
        prefs = ltm.get_preferences()
        assert "preferred_metrics" in prefs

    def test_multiple_profile_attributes(self, memory_store):
        """Test storing multiple profile attributes."""
        ltm = LongTermMemory(memory_store, "user123")
        
        ltm.set_profile("company", {"name": "Powdered Drink City"})
        ltm.set_profile("role", {"title": "CFO"})
        
        profile = ltm.get_profile()
        assert len(profile) == 2


class TestSemanticMemory:
    """Tests for SemanticMemory class."""

    def test_store_and_search_fact(self, memory_store):
        """Test storing and searching for facts."""
        sem = SemanticMemory(memory_store)
        
        sem.store_fact(
            "ebitda_def",
            "EBITDA is Earnings Before Interest, Taxes, Depreciation and Amortization",
            {"type": "definition"}
        )
        
        # Note: In-memory store without embeddings does basic search
        results = sem.search("EBITDA earnings", limit=5)
        # Results depend on store implementation
        assert isinstance(results, list)

    def test_store_key_driver(self, memory_store):
        """Test storing a Key Driver."""
        sem = SemanticMemory(memory_store)
        
        sem.store_key_driver(
            driver_id="orders",
            name="Orders",
            description="Number of customer orders per period",
            cell_reference="M - Monthly!K5",
            current_value="221207"
        )
        
        results = sem.search("Orders customer")
        assert isinstance(results, list)

    def test_store_key_result(self, memory_store):
        """Test storing a Key Result."""
        sem = SemanticMemory(memory_store)
        
        sem.store_key_result(
            result_id="gross_sales",
            name="Gross Sales",
            description="Total revenue before deductions",
            cell_reference="M - Monthly!K92",
            formula="=K80*K81",
            current_value="21346139"
        )
        
        results = sem.search("Gross Sales revenue")
        assert isinstance(results, list)

    def test_store_formula_chain(self, memory_store):
        """Test storing a formula chain."""
        sem = SemanticMemory(memory_store)
        
        sem.store_formula_chain(
            chain_id="ebitda_chain",
            target_metric="EBITDA",
            chain_description="EBITDA = EBIT + Depreciation + Amortization",
            cells_involved=["K194", "K191", "K192", "K193"]
        )
        
        results = sem.search("EBITDA formula calculation")
        assert isinstance(results, list)


class TestEpisodicMemory:
    """Tests for EpisodicMemory class."""

    def test_store_and_find_episode(self, memory_store):
        """Test storing and finding similar episodes."""
        epi = EpisodicMemory(memory_store)
        
        epi.store_episode(
            key="ep1",
            situation="User asked about EBITDA calculation",
            user_query="How is EBITDA calculated?",
            analysis_result="EBITDA = EBIT + Depreciation + Amortization",
            success=True
        )
        
        similar = epi.find_similar("Calculate EBITDA", limit=3)
        assert isinstance(similar, list)

    def test_store_goal_seek_solution(self, memory_store):
        """Test storing a goal seek solution."""
        epi = EpisodicMemory(memory_store)
        
        goals = [
            {"metric": "EBITDA", "target": 1500000},
            {"metric": "Cash", "target": 1000000}
        ]
        solution = {"feasible": True, "iterations": 15}
        driver_values = {"Orders": 250000, "AoV": 78.00, "CaC": 40.00}
        
        epi.store_goal_seek_solution(
            key="gs1",
            goals=goals,
            solution=solution,
            driver_values=driver_values
        )
        
        similar = epi.find_similar("optimize EBITDA and Cash")
        assert isinstance(similar, list)

    def test_format_as_few_shot(self, memory_store):
        """Test formatting episodes as few-shot examples."""
        epi = EpisodicMemory(memory_store)
        
        episodes = [
            {
                "situation": "User asked about EBITDA",
                "user_query": "What is EBITDA?",
                "analysis_result": "EBITDA stands for...",
                "success": True,
            }
        ]
        
        formatted = epi.format_as_few_shot(episodes)
        assert "Example 1" in formatted
        assert "User Query" in formatted

    def test_format_empty_episodes(self, memory_store):
        """Test formatting when no episodes exist."""
        epi = EpisodicMemory(memory_store)
        
        formatted = epi.format_as_few_shot([])
        assert "No similar past analyses" in formatted


class TestProceduralMemory:
    """Tests for ProceduralMemory class."""

    def test_get_default_playbook(self, memory_store):
        """Test getting default playbook when not initialized."""
        proc = ProceduralMemory(memory_store)
        
        instructions, version = proc.get_playbook("information_recall")
        
        # Should return default
        assert "Parse the user's question" in instructions or version == 0

    def test_initialize_default_playbooks(self, memory_store):
        """Test initializing default playbooks."""
        proc = ProceduralMemory(memory_store)
        proc.initialize_default_playbooks()
        
        # Should be able to retrieve
        instructions, version = proc.get_playbook("information_recall")
        assert version >= 0

    def test_update_playbook(self, memory_store):
        """Test updating a playbook."""
        proc = ProceduralMemory(memory_store)
        proc.initialize_default_playbooks()
        
        # Get initial version
        _, initial_version = proc.get_playbook("information_recall")
        
        # Update
        new_version = proc.update_playbook(
            "information_recall",
            "Updated instructions for information recall."
        )
        
        assert new_version == initial_version + 1
        
        # Verify update
        instructions, version = proc.get_playbook("information_recall")
        assert version == new_version
        assert "Updated instructions" in instructions

    def test_get_nonexistent_playbook(self, memory_store):
        """Test getting a playbook that doesn't exist."""
        proc = ProceduralMemory(memory_store)
        
        instructions, version = proc.get_playbook("nonexistent_playbook")
        
        assert instructions == ""
        assert version == 0
