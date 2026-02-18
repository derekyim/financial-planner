"""Agent evaluation using RAGAS multi-turn metrics.

Evaluates tool call accuracy, goal achievement, and topic adherence
for the financial analysis agent system.
"""

from typing import Optional

from langchain_openai import ChatOpenAI

from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    ToolCallAccuracy,
    AgentGoalAccuracyWithReference,
    TopicAdherenceScore,
)
from ragas.dataset_schema import MultiTurnSample
from ragas.integrations.langgraph import convert_to_ragas_messages
import ragas.messages as r

EVAL_MODEL = "gpt-4o-mini"


class AgentEvalRunner:
    """Runs RAGAS agent evaluation metrics against traced conversations."""

    def __init__(self, evaluator_model: str = EVAL_MODEL):
        self.llm = LangchainLLMWrapper(ChatOpenAI(model=evaluator_model))

        self.tool_accuracy = ToolCallAccuracy()
        self.tool_accuracy.llm = ChatOpenAI(model=evaluator_model)

        self.goal_accuracy = AgentGoalAccuracyWithReference()
        self.goal_accuracy.llm = self.llm

        self.topic_adherence = TopicAdherenceScore(llm=self.llm, mode="precision")

    async def evaluate_tool_calls(
        self,
        messages: list,
        reference_tool_calls: list[r.ToolCall],
    ) -> float:
        ragas_trace = convert_to_ragas_messages(messages)
        sample = MultiTurnSample(
            user_input=ragas_trace,
            reference_tool_calls=reference_tool_calls,
        )
        return await self.tool_accuracy.multi_turn_ascore(sample)

    async def evaluate_goal(
        self,
        messages: list,
        reference_goal: str,
    ) -> float:
        ragas_trace = convert_to_ragas_messages(messages)
        sample = MultiTurnSample(
            user_input=ragas_trace,
            reference=reference_goal,
        )
        return await self.goal_accuracy.multi_turn_ascore(sample)

    async def evaluate_topic(
        self,
        messages: list,
        reference_topics: list[str],
    ) -> float:
        ragas_trace = convert_to_ragas_messages(messages)
        sample = MultiTurnSample(
            user_input=ragas_trace,
            reference_topics=reference_topics,
        )
        return await self.topic_adherence.multi_turn_ascore(sample)

    async def evaluate_all(
        self,
        messages: list,
        reference_goal: str,
        reference_topics: list[str],
        reference_tool_calls: Optional[list[r.ToolCall]] = None,
    ) -> dict:
        tool_score = 0.0
        if reference_tool_calls:
            tool_score = await self.evaluate_tool_calls(messages, reference_tool_calls)

        goal_score = await self.evaluate_goal(messages, reference_goal)
        topic_score = await self.evaluate_topic(messages, reference_topics)

        return {
            "tool_call_accuracy": tool_score,
            "goal_accuracy": goal_score,
            "topic_adherence": topic_score,
        }
