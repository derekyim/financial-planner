"""Memory type implementations for the financial analysis agent.

This module provides classes for working with each of the 5 memory types
adapted from the CoALA framework for financial modeling context.
"""

from typing import Any, Optional
from dataclasses import dataclass
from langgraph.store.base import BaseStore
from langchain_core.messages import BaseMessage, trim_messages
from langchain_openai import ChatOpenAI


@dataclass
class ShortTermMemory:
    """Short-term memory manages conversation context within a thread.

    Short-term memory is automatically handled by LangGraph's checkpointer.
    This class provides utilities for working with the message history.

    Attributes:
        messages: The list of messages in the current conversation.
    """

    messages: list[BaseMessage]

    def get_recent(self, n: int = 10) -> list[BaseMessage]:
        """Get the n most recent messages.

        Args:
            n: Number of recent messages to return.

        Returns:
            List of the n most recent messages.
        """
        return self.messages[-n:] if len(self.messages) > n else self.messages

    def trim(
        self,
        max_tokens: int = 4000,
        llm: Optional[ChatOpenAI] = None,
        include_system: bool = True,
    ) -> list[BaseMessage]:
        """Trim messages to fit within a token limit.

        Args:
            max_tokens: Maximum number of tokens to keep.
            llm: The LLM to use for token counting.
            include_system: Whether to always keep system messages.

        Returns:
            Trimmed list of messages.
        """
        if llm is None:
            llm = ChatOpenAI(model="gpt-4o-mini")

        trimmer = trim_messages(
            max_tokens=max_tokens,
            strategy="last",
            token_counter=llm,
            include_system=include_system,
            allow_partial=False,
        )
        return trimmer.invoke(self.messages)


class LongTermMemory:
    """Long-term memory stores user information across sessions.

    For financial analysis, this includes user preferences like:
    - Preferred metrics to track
    - Risk tolerance levels
    - Notification thresholds
    - Historical analysis preferences
    """

    def __init__(self, store: BaseStore, user_id: str):
        """Initialize long-term memory for a user.

        Args:
            store: The memory store to use.
            user_id: The unique identifier for the user.
        """
        self.store = store
        self.user_id = user_id
        self.profile_namespace = (user_id, "profile")
        self.preferences_namespace = (user_id, "preferences")

    def get_profile(self) -> dict[str, Any]:
        """Get the user's financial analysis profile.

        Returns:
            Dictionary containing the user's profile data.
        """
        items = list(self.store.search(self.profile_namespace))
        return {item.key: item.value for item in items}

    def set_profile(self, key: str, value: dict[str, Any]) -> None:
        """Set a profile attribute for the user.

        Args:
            key: The profile attribute key (e.g., "risk_tolerance", "company").
            value: The value to store.
        """
        self.store.put(self.profile_namespace, key, value)

    def get_preferences(self) -> dict[str, Any]:
        """Get the user's preferences.

        Returns:
            Dictionary containing the user's preferences.
        """
        items = list(self.store.search(self.preferences_namespace))
        return {item.key: item.value for item in items}

    def set_preference(self, key: str, value: dict[str, Any]) -> None:
        """Set a preference for the user.

        Args:
            key: The preference key (e.g., "preferred_metrics", "alert_thresholds").
            value: The value to store.
        """
        self.store.put(self.preferences_namespace, key, value)


class SemanticMemory:
    """Semantic memory stores and retrieves facts by meaning.

    For financial analysis, this stores:
    - Key Drivers and their relationships
    - Key Results and their formulas
    - Formula chains and dependencies
    - Model structure information
    """

    def __init__(self, store: BaseStore, namespace: tuple[str, ...] = ("financial", "model_facts")):
        """Initialize semantic memory.

        Args:
            store: The memory store with embedding support.
            namespace: The namespace for storing facts.
        """
        self.store = store
        self.namespace = namespace

    def store_fact(self, key: str, text: str, metadata: Optional[dict] = None) -> None:
        """Store a fact in semantic memory.

        Args:
            key: Unique identifier for the fact.
            text: The text content of the fact (used for embedding).
            metadata: Optional additional metadata (e.g., cell_reference, formula).
        """
        value = {"text": text}
        if metadata:
            value.update(metadata)
        self.store.put(self.namespace, key, value)

    def store_key_driver(
        self,
        driver_id: str,
        name: str,
        description: str,
        cell_reference: str,
        current_value: Optional[str] = None,
    ) -> None:
        """Store a Key Driver in semantic memory.

        Args:
            driver_id: Unique identifier for the driver.
            name: Friendly name of the driver.
            description: Description of what this driver controls.
            cell_reference: Cell reference (e.g., "M - Monthly!K5").
            current_value: Current value if known.
        """
        text = f"Key Driver: {name}. {description}"
        metadata = {
            "type": "key_driver",
            "name": name,
            "cell_reference": cell_reference,
            "current_value": current_value,
        }
        self.store_fact(driver_id, text, metadata)

    def store_key_result(
        self,
        result_id: str,
        name: str,
        description: str,
        cell_reference: str,
        formula: Optional[str] = None,
        current_value: Optional[str] = None,
    ) -> None:
        """Store a Key Result in semantic memory.

        Args:
            result_id: Unique identifier for the result.
            name: Friendly name of the result.
            description: Description of what this result measures.
            cell_reference: Cell reference (e.g., "M - Monthly!K92").
            formula: The formula used to calculate this result.
            current_value: Current value if known.
        """
        text = f"Key Result: {name}. {description}"
        metadata = {
            "type": "key_result",
            "name": name,
            "cell_reference": cell_reference,
            "formula": formula,
            "current_value": current_value,
        }
        self.store_fact(result_id, text, metadata)

    def store_formula_chain(
        self,
        chain_id: str,
        target_metric: str,
        chain_description: str,
        cells_involved: list[str],
    ) -> None:
        """Store a formula dependency chain.

        Args:
            chain_id: Unique identifier for the chain.
            target_metric: The metric this chain calculates.
            chain_description: Human-readable description of the chain.
            cells_involved: List of cell references in the chain.
        """
        text = f"Formula chain for {target_metric}: {chain_description}"
        metadata = {
            "type": "formula_chain",
            "target_metric": target_metric,
            "cells_involved": cells_involved,
        }
        self.store_fact(chain_id, text, metadata)

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search for facts related to a query.

        Args:
            query: The search query.
            limit: Maximum number of results to return.

        Returns:
            List of relevant facts with their similarity scores.
        """
        results = self.store.search(self.namespace, query=query, limit=limit)
        return [
            {
                "key": r.key,
                "text": r.value.get("text", ""),
                "score": getattr(r, "score", None),
                **{k: v for k, v in r.value.items() if k != "text"},
            }
            for r in results
        ]

    def get_all_key_drivers(self) -> list[dict[str, Any]]:
        """Get all stored Key Drivers.

        Returns:
            List of all Key Driver facts.
        """
        results = self.search("Key Driver", limit=50)
        return [r for r in results if r.get("type") == "key_driver"]

    def get_all_key_results(self) -> list[dict[str, Any]]:
        """Get all stored Key Results.

        Returns:
            List of all Key Result facts.
        """
        results = self.search("Key Result", limit=50)
        return [r for r in results if r.get("type") == "key_result"]


class EpisodicMemory:
    """Episodic memory stores past experiences for few-shot learning.

    For financial analysis, this stores:
    - Past successful analyses
    - What-if scenarios that worked well
    - Goal seek solutions that satisfied constraints
    """

    def __init__(self, store: BaseStore, namespace: tuple[str, ...] = ("financial", "episodes")):
        """Initialize episodic memory.

        Args:
            store: The memory store with embedding support.
            namespace: The namespace for storing episodes.
        """
        self.store = store
        self.namespace = namespace

    def store_episode(
        self,
        key: str,
        situation: str,
        user_query: str,
        analysis_result: str,
        success: bool = True,
        metadata: Optional[dict] = None,
    ) -> None:
        """Store a successful analysis as an episode.

        Args:
            key: Unique identifier for the episode.
            situation: Description of the situation (used for semantic search).
            user_query: The user's original query.
            analysis_result: The analysis result or response.
            success: Whether this was a successful interaction.
            metadata: Optional additional metadata.
        """
        value = {
            "text": situation,
            "situation": situation,
            "user_query": user_query,
            "analysis_result": analysis_result,
            "success": success,
        }
        if metadata:
            value.update(metadata)
        self.store.put(self.namespace, key, value)

    def store_goal_seek_solution(
        self,
        key: str,
        goals: list[dict],
        solution: dict[str, Any],
        driver_values: dict[str, float],
    ) -> None:
        """Store a successful goal seek solution.

        Args:
            key: Unique identifier for the solution.
            goals: List of goals that were satisfied.
            solution: The solution details.
            driver_values: The Key Driver values that achieved the goals.
        """
        goals_text = ", ".join([f"{g['metric']}={g['target']}" for g in goals])
        situation = f"Goal Seek: Achieved targets {goals_text}"
        self.store_episode(
            key=key,
            situation=situation,
            user_query=f"Goal seek for: {goals_text}",
            analysis_result=str(solution),
            success=True,
            metadata={"type": "goal_seek", "goals": goals, "driver_values": driver_values},
        )

    def find_similar(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        """Find episodes similar to the current situation.

        Args:
            query: The current user query or situation description.
            limit: Maximum number of episodes to return.

        Returns:
            List of similar episodes with their details.
        """
        results = self.store.search(self.namespace, query=query, limit=limit)
        return [
            {
                "situation": r.value.get("situation", ""),
                "user_query": r.value.get("user_query", ""),
                "analysis_result": r.value.get("analysis_result", ""),
                "success": r.value.get("success", True),
                "score": getattr(r, "score", None),
                **{k: v for k, v in r.value.items() if k not in ["text", "situation", "user_query", "analysis_result", "success"]},
            }
            for r in results
        ]

    def format_as_few_shot(self, episodes: list[dict[str, Any]], max_examples: int = 2) -> str:
        """Format episodes as few-shot examples for prompts.

        Args:
            episodes: List of episodes to format.
            max_examples: Maximum number of examples to include.

        Returns:
            Formatted string suitable for inclusion in prompts.
        """
        if not episodes:
            return "No similar past analyses found."

        examples = []
        for i, ep in enumerate(episodes[:max_examples], 1):
            example = f"""Example {i}:
Situation: {ep['situation']}
User Query: {ep['user_query']}
Analysis: {ep['analysis_result']}"""
            examples.append(example)

        return "\n\n".join(examples)


class ProceduralMemory:
    """Procedural memory stores and updates agent instructions (playbooks).

    For financial analysis, this stores playbook templates for:
    - Information Recall
    - Goal Seek
    - Sensitivity Analysis
    - What-If Analysis
    - Forecast Projection
    """

    DEFAULT_PLAYBOOKS = {
        "information_recall": """You are an Information Recall agent for financial model analysis.

PLAYBOOK:
1. Parse the user's question to identify which metric(s) they're asking about
2. Search semantic memory for relevant Key Drivers or Key Results
3. If not found in memory, read from the "Key Drivers and Results" tab
4. For each metric, trace the formula chain to understand how it's calculated
5. Explain the metric with cell references and formula logic
6. Write the action to the AuditLog tab

Always cite specific cell references and formulas in your explanations.""",

        "goal_seek": """You are a Goal Seek agent for financial model optimization.

PLAYBOOK:
1. Parse the user's goals: extract up to 3 targets with (metric_name, end_date, target_value)
2. Identify which Key Drivers can influence each target metric
3. For each Key Driver, understand its formula impact on the targets
4. Generate test scenarios using Latin hypercube sampling across driver ranges
5. For each scenario: write driver values to cells, read resulting target values
6. Identify top 3 combinations that satisfy all constraints
7. ALWAYS restore original values after testing
8. Return the solutions with explanations of trade-offs
9. Write results to the AuditLog tab

Be careful to restore original values even if errors occur.""",

        "sensitivity_analysis": """You are a Sensitivity Analysis agent for financial modeling.

PLAYBOOK:
1. Identify the input variables (Key Drivers) to vary
2. Identify the output variable (Key Result) to monitor
3. Define the range of variation (e.g., +/- 25% in 5% increments)
4. Generate multipliers for each combination
5. Run each scenario and capture results
6. Create a sensitivity table showing input variations vs output
7. Restore original values
8. Write results to the AuditLog tab""",

        "what_if": """You are a What-If Analysis agent for financial modeling.

PLAYBOOK:
1. Parse the user's hypothetical scenario
2. Identify which Key Drivers need to change
3. Calculate the new values based on the scenario
4. Trace formulas to predict impact on Key Results
5. Explain the cascading effects through the model
6. Write the analysis to the AuditLog tab

Focus on explaining cause-and-effect relationships.""",

        "forecast": """You are a Forecast Projection agent for financial modeling.

PLAYBOOK:
1. Identify the metric to forecast
2. Analyze historical trends from Actual periods
3. Identify growth rates and patterns
4. Project values forward into Forecast periods
5. Consider seasonality if applicable
6. Write the projections to the AuditLog tab""",
    }

    def __init__(
        self,
        store: BaseStore,
        namespace: tuple[str, ...] = ("financial", "playbooks"),
    ):
        """Initialize procedural memory.

        Args:
            store: The memory store.
            namespace: The namespace for storing playbooks.
        """
        self.store = store
        self.namespace = namespace

    def initialize_default_playbooks(self) -> None:
        """Initialize the store with default playbook templates."""
        for playbook_name, playbook_content in self.DEFAULT_PLAYBOOKS.items():
            item = self.store.get(self.namespace, playbook_name)
            if item is None:
                self.store.put(
                    self.namespace,
                    playbook_name,
                    {"instructions": playbook_content, "version": 1},
                )

    def get_playbook(self, playbook_name: str) -> tuple[str, int]:
        """Get a playbook's instructions.

        Args:
            playbook_name: Name of the playbook (e.g., "information_recall").

        Returns:
            Tuple of (instructions_text, version_number).
        """
        item = self.store.get(self.namespace, playbook_name)
        if item is None:
            # Return default if not in store
            default = self.DEFAULT_PLAYBOOKS.get(playbook_name, "")
            return default, 0
        return item.value.get("instructions", ""), item.value.get("version", 0)

    def update_playbook(self, playbook_name: str, new_instructions: str) -> int:
        """Update a playbook's instructions.

        Args:
            playbook_name: Name of the playbook.
            new_instructions: The new instructions text.

        Returns:
            The new version number.
        """
        _, current_version = self.get_playbook(playbook_name)
        new_version = current_version + 1

        self.store.put(
            self.namespace,
            playbook_name,
            {
                "instructions": new_instructions,
                "version": new_version,
            },
        )
        return new_version

    def reflect_and_update(
        self,
        playbook_name: str,
        feedback: str,
        llm: Optional[ChatOpenAI] = None,
    ) -> tuple[str, int]:
        """Reflect on feedback and update playbook instructions.

        Args:
            playbook_name: Name of the playbook to update.
            feedback: User feedback about the agent's performance.
            llm: The LLM to use for reflection.

        Returns:
            Tuple of (new_instructions, new_version).
        """
        if llm is None:
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        current_instructions, _ = self.get_playbook(playbook_name)

        reflection_prompt = f"""You are improving a financial analysis agent's playbook based on user feedback.

Current Playbook ({playbook_name}):
{current_instructions}

User Feedback:
{feedback}

Based on this feedback, provide improved instructions. Keep the same general format but incorporate the feedback.
Only output the new instructions, nothing else."""

        response = llm.invoke(reflection_prompt)
        new_instructions = response.content

        new_version = self.update_playbook(playbook_name, new_instructions)
        return new_instructions, new_version
