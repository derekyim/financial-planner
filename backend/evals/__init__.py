"""Evaluation subsystem for the Dysprosium Financial Planner.

Provides RAG evaluation, agent evaluation, and test dataset generation
using the RAGAS framework.
"""

from evals.rag_evals import RAGEvalRunner
from evals.agent_evals import AgentEvalRunner

__all__ = ["RAGEvalRunner", "AgentEvalRunner"]
