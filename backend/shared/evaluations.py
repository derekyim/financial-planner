"""RAGAS Evaluation Framework for Financial Analysis Agents.

Implements both RAG evaluation and Agent evaluation metrics using the RAGAS library.

RAG Metrics:
- LLMContextRecall: Did we retrieve relevant context?
- LLMContextPrecisionWithReference: Is the retrieved context precise (not noisy)?
- Faithfulness: Is the response grounded in context?
- FactualCorrectness: Are facts accurate?
- ResponseRelevancy: Does response address the question?

Agent Metrics:
- ToolCallAccuracy: Did agent call correct tools with correct args?
- AgentGoalAccuracyWithReference: Did agent achieve user's goal?
- TopicAdherenceScore: Did agent stay on financial topics?
"""

import os
from typing import Optional
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.metrics import (
    LLMContextRecall,
    LLMContextPrecisionWithReference,
    Faithfulness,
    FactualCorrectness,
    ResponseRelevancy,
    ContextEntityRecall,
)
from ragas.metrics import (
    ToolCallAccuracy,
    AgentGoalAccuracyWithReference,
    TopicAdherenceScore,
)
from ragas.dataset_schema import SingleTurnSample, MultiTurnSample, EvaluationDataset
from ragas.integrations.langgraph import convert_to_ragas_messages
from ragas import evaluate, RunConfig
import ragas.messages as r

from langchain_openai import OpenAIEmbeddings


# Configuration
DEFAULT_EVALUATOR_MODEL = "gpt-4o-mini"
DEFAULT_TIMEOUT = 360


@dataclass
class RAGEvaluationResult:
    """Results from RAG evaluation."""
    context_recall: float
    context_precision: float
    faithfulness: float
    factual_correctness: float
    response_relevancy: float
    context_entity_recall: float
    
    def __str__(self) -> str:
        return f"""RAG Evaluation Results:
  Context Recall:        {self.context_recall:.3f}
  Context Precision:     {self.context_precision:.3f}
  Faithfulness:          {self.faithfulness:.3f}
  Factual Correctness:   {self.factual_correctness:.3f}
  Response Relevancy:    {self.response_relevancy:.3f}
  Context Entity Recall: {self.context_entity_recall:.3f}"""


@dataclass
class AgentEvaluationResult:
    """Results from agent evaluation."""
    tool_call_accuracy: float
    goal_accuracy: float
    topic_adherence: float
    
    def __str__(self) -> str:
        return f"""Agent Evaluation Results:
  Tool Call Accuracy: {self.tool_call_accuracy:.3f}
  Goal Accuracy:      {self.goal_accuracy:.3f}
  Topic Adherence:    {self.topic_adherence:.3f}"""


class RAGASEvaluator:
    """Evaluator for RAG and Agent systems using RAGAS metrics."""
    
    def __init__(
        self,
        evaluator_model: str = DEFAULT_EVALUATOR_MODEL,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """Initialize the evaluator.
        
        Args:
            evaluator_model: Model to use for evaluation.
            timeout: Timeout for evaluation runs.
        """
        self.evaluator_model = evaluator_model
        self.timeout = timeout
        
        # Initialize LLM and embeddings wrappers
        self.llm = LangchainLLMWrapper(ChatOpenAI(model=evaluator_model))
        self.embeddings = LangchainEmbeddingsWrapper(
            OpenAIEmbeddings(model="text-embedding-3-small")
        )
        
        # Run configuration
        self.run_config = RunConfig(timeout=timeout)
        
        # Initialize RAG metrics
        self._init_rag_metrics()
        
        # Initialize Agent metrics
        self._init_agent_metrics()
    
    def _init_rag_metrics(self):
        """Initialize RAG evaluation metrics."""
        self.context_recall = LLMContextRecall()
        self.context_precision = LLMContextPrecisionWithReference()
        self.faithfulness = Faithfulness()
        self.factual_correctness = FactualCorrectness()
        self.response_relevancy = ResponseRelevancy()
        self.context_entity_recall = ContextEntityRecall()
        
        self.rag_metrics = [
            self.context_recall,
            self.context_precision,
            self.faithfulness,
            self.factual_correctness,
            self.response_relevancy,
            self.context_entity_recall,
        ]
    
    def _init_agent_metrics(self):
        """Initialize Agent evaluation metrics."""
        self.tool_call_accuracy = ToolCallAccuracy()
        self.tool_call_accuracy.llm = ChatOpenAI(model=self.evaluator_model)
        
        self.goal_accuracy = AgentGoalAccuracyWithReference()
        self.goal_accuracy.llm = self.llm
        
        self.topic_adherence = TopicAdherenceScore(llm=self.llm, mode="precision")
    
    def create_rag_sample(
        self,
        question: str,
        response: str,
        retrieved_contexts: list[str],
        reference: Optional[str] = None,
    ) -> SingleTurnSample:
        """Create a RAG evaluation sample.
        
        Args:
            question: The user's question.
            response: The system's response.
            retrieved_contexts: List of retrieved context strings.
            reference: Optional reference answer.
            
        Returns:
            A SingleTurnSample for evaluation.
        """
        return SingleTurnSample(
            user_input=question,
            response=response,
            retrieved_contexts=retrieved_contexts,
            reference=reference,
        )
    
    def evaluate_rag(
        self,
        samples: list[SingleTurnSample],
    ) -> dict:
        """Evaluate RAG performance on a set of samples.
        
        Args:
            samples: List of RAG samples to evaluate.
            
        Returns:
            Evaluation results dictionary.
        """
        # Convert to evaluation dataset
        dataset = EvaluationDataset(samples=samples)
        
        # Run evaluation
        results = evaluate(
            dataset=dataset,
            metrics=self.rag_metrics,
            llm=self.llm,
            embeddings=self.embeddings,
            run_config=self.run_config,
        )
        
        return results
    
    async def evaluate_tool_call_accuracy(
        self,
        messages: list,
        reference_tool_calls: list[r.ToolCall],
    ) -> float:
        """Evaluate tool call accuracy for an agent interaction.
        
        Args:
            messages: List of LangChain messages from the interaction.
            reference_tool_calls: List of expected tool calls.
            
        Returns:
            Tool call accuracy score (0-1).
        """
        # Convert to RAGAS format
        ragas_trace = convert_to_ragas_messages(messages)
        
        sample = MultiTurnSample(
            user_input=ragas_trace,
            reference_tool_calls=reference_tool_calls,
        )
        
        return await self.tool_call_accuracy.multi_turn_ascore(sample)
    
    async def evaluate_goal_accuracy(
        self,
        messages: list,
        reference_goal: str,
    ) -> float:
        """Evaluate if the agent achieved the user's goal.
        
        Args:
            messages: List of LangChain messages from the interaction.
            reference_goal: Description of the expected goal.
            
        Returns:
            Goal accuracy score (0 or 1).
        """
        ragas_trace = convert_to_ragas_messages(messages)
        
        sample = MultiTurnSample(
            user_input=ragas_trace,
            reference=reference_goal,
        )
        
        return await self.goal_accuracy.multi_turn_ascore(sample)
    
    async def evaluate_topic_adherence(
        self,
        messages: list,
        reference_topics: list[str],
    ) -> float:
        """Evaluate if the agent stayed on topic.
        
        Args:
            messages: List of LangChain messages from the interaction.
            reference_topics: List of allowed topics.
            
        Returns:
            Topic adherence score (0-1).
        """
        ragas_trace = convert_to_ragas_messages(messages)
        
        sample = MultiTurnSample(
            user_input=ragas_trace,
            reference_topics=reference_topics,
        )
        
        return await self.topic_adherence.multi_turn_ascore(sample)
    
    async def evaluate_agent(
        self,
        messages: list,
        reference_goal: str,
        reference_topics: list[str],
        reference_tool_calls: Optional[list[r.ToolCall]] = None,
    ) -> AgentEvaluationResult:
        """Full agent evaluation with all metrics.
        
        Args:
            messages: List of LangChain messages from the interaction.
            reference_goal: Description of the expected goal.
            reference_topics: List of allowed topics.
            reference_tool_calls: Optional list of expected tool calls.
            
        Returns:
            AgentEvaluationResult with all scores.
        """
        # Evaluate tool calls if provided
        tool_score = 0.0
        if reference_tool_calls:
            tool_score = await self.evaluate_tool_call_accuracy(
                messages, reference_tool_calls
            )
        
        # Evaluate goal accuracy
        goal_score = await self.evaluate_goal_accuracy(messages, reference_goal)
        
        # Evaluate topic adherence
        topic_score = await self.evaluate_topic_adherence(messages, reference_topics)
        
        return AgentEvaluationResult(
            tool_call_accuracy=tool_score,
            goal_accuracy=goal_score,
            topic_adherence=topic_score,
        )


# Convenience functions for quick evaluations

def create_evaluator(model: str = DEFAULT_EVALUATOR_MODEL) -> RAGASEvaluator:
    """Create a RAGAS evaluator instance.
    
    Args:
        model: Model to use for evaluation.
        
    Returns:
        Configured RAGASEvaluator.
    """
    return RAGASEvaluator(evaluator_model=model)


def evaluate_single_rag_response(
    question: str,
    response: str,
    contexts: list[str],
    reference: Optional[str] = None,
    evaluator: Optional[RAGASEvaluator] = None,
) -> dict:
    """Evaluate a single RAG response.
    
    Args:
        question: The user's question.
        response: The system's response.
        contexts: Retrieved context strings.
        reference: Optional reference answer.
        evaluator: Optional evaluator instance.
        
    Returns:
        Evaluation results.
    """
    if evaluator is None:
        evaluator = create_evaluator()
    
    sample = evaluator.create_rag_sample(
        question=question,
        response=response,
        retrieved_contexts=contexts,
        reference=reference,
    )
    
    return evaluator.evaluate_rag([sample])


# Test the evaluations
if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    
    load_dotenv()
    
    print("RAGAS Evaluation Framework Test")
    print("=" * 60)
    
    # Create evaluator
    evaluator = create_evaluator()
    
    # Test RAG evaluation
    print("\n--- RAG Evaluation Test ---")
    sample = evaluator.create_rag_sample(
        question="What is EBITDA?",
        response="EBITDA stands for Earnings Before Interest, Taxes, Depreciation, and Amortization. It's a measure of operating performance that shows profitability before accounting for financial decisions and tax effects.",
        retrieved_contexts=[
            "EBITDA: Earnings Before Interest, Taxes, Depreciation, and Amortization. A measure of operating performance.",
            "Net Income: The bottom line profit after all expenses, interest, and taxes.",
        ],
        reference="EBITDA is Earnings Before Interest, Taxes, Depreciation, and Amortization.",
    )
    
    results = evaluator.evaluate_rag([sample])
    print(f"Results: {results}")
    
    # Test Agent evaluation
    print("\n--- Agent Evaluation Test ---")
    messages = [
        HumanMessage(content="What is the current price of copper?"),
        AIMessage(content="Based on the current market data, the price of copper is $8.50 per pound."),
    ]
    
    async def test_agent_eval():
        result = await evaluator.evaluate_agent(
            messages=messages,
            reference_goal="Get the current price of copper",
            reference_topics=["metals", "commodities", "pricing"],
        )
        print(result)
    
    asyncio.run(test_agent_eval())
