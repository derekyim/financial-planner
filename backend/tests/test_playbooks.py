"""Unit tests for agent playbook prompts."""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.playbooks import (
    PLANNER_SYSTEM_PROMPT,
    RECALL_AGENT_PROMPT,
    GOAL_SEEK_AGENT_PROMPT,
    STRATEGIC_GUIDANCE_PROMPT,
)


class TestPlannerPrompt:
    """Tests for the supervisor/planner system prompt."""

    def test_contains_routing_options(self):
        assert "recall" in PLANNER_SYSTEM_PROMPT
        assert "goal_seek" in PLANNER_SYSTEM_PROMPT
        assert "strategic" in PLANNER_SYSTEM_PROMPT

    def test_contains_model_documentation_instructions(self):
        assert "Model Documentation" in PLANNER_SYSTEM_PROMPT

    def test_is_nonempty_string(self):
        assert isinstance(PLANNER_SYSTEM_PROMPT, str)
        assert len(PLANNER_SYSTEM_PROMPT) > 100


class TestRecallPrompt:
    """Tests for the recall agent prompt."""

    def test_contains_key_concepts(self):
        assert "Key Driver" in RECALL_AGENT_PROMPT or "Key Result" in RECALL_AGENT_PROMPT

    def test_contains_formula_instructions(self):
        prompt_lower = RECALL_AGENT_PROMPT.lower()
        assert "formula" in prompt_lower

    def test_is_nonempty_string(self):
        assert isinstance(RECALL_AGENT_PROMPT, str)
        assert len(RECALL_AGENT_PROMPT) > 100


class TestGoalSeekPrompt:
    """Tests for the goal seek agent prompt."""

    def test_contains_optimization_concepts(self):
        prompt_lower = GOAL_SEEK_AGENT_PROMPT.lower()
        has_optimize = "optim" in prompt_lower
        has_target = "target" in prompt_lower
        has_goal = "goal" in prompt_lower
        assert has_optimize or has_target or has_goal

    def test_contains_scenario_instructions(self):
        prompt_lower = GOAL_SEEK_AGENT_PROMPT.lower()
        assert "scenario" in prompt_lower or "combination" in prompt_lower

    def test_is_nonempty_string(self):
        assert isinstance(GOAL_SEEK_AGENT_PROMPT, str)
        assert len(GOAL_SEEK_AGENT_PROMPT) > 100


class TestStrategicGuidancePrompt:
    """Tests for the strategic guidance agent prompt."""

    def test_contains_rag_context_instructions(self):
        prompt_lower = STRATEGIC_GUIDANCE_PROMPT.lower()
        has_context = "context" in prompt_lower
        has_knowledge = "knowledge" in prompt_lower
        assert has_context or has_knowledge

    def test_contains_business_domain(self):
        prompt_lower = STRATEGIC_GUIDANCE_PROMPT.lower()
        has_business = "business" in prompt_lower
        has_strategy = "strateg" in prompt_lower
        assert has_business or has_strategy

    def test_is_nonempty_string(self):
        assert isinstance(STRATEGIC_GUIDANCE_PROMPT, str)
        assert len(STRATEGIC_GUIDANCE_PROMPT) > 50


class TestAllPromptsConsistency:
    """Cross-prompt consistency checks."""

    def test_all_prompts_are_strings(self):
        prompts = [PLANNER_SYSTEM_PROMPT, RECALL_AGENT_PROMPT, GOAL_SEEK_AGENT_PROMPT, STRATEGIC_GUIDANCE_PROMPT]
        for prompt in prompts:
            assert isinstance(prompt, str)

    def test_no_empty_prompts(self):
        prompts = [PLANNER_SYSTEM_PROMPT, RECALL_AGENT_PROMPT, GOAL_SEEK_AGENT_PROMPT, STRATEGIC_GUIDANCE_PROMPT]
        for prompt in prompts:
            assert len(prompt.strip()) > 0

    def test_planner_references_all_agents(self):
        """The planner should know about all specialist agents it can route to."""
        for agent in ["recall", "goal_seek", "strategic"]:
            assert agent in PLANNER_SYSTEM_PROMPT
