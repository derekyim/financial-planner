"""CLI script to run the full evaluation suite.

Usage:
    python -m evals.run_evals --rag          # RAG evals only
    python -m evals.run_evals --agent        # Agent evals only
    python -m evals.run_evals --all          # Both
"""

import sys
from pathlib import Path

_backend_dir = str(Path(__file__).resolve().parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from shared.config import load_env
load_env()

import argparse
import asyncio
import json

from langchain_core.messages import HumanMessage, AIMessage

from evals.rag_evals import RAGEvalRunner
from evals.agent_evals import AgentEvalRunner
from agents.rag_pipeline import retrieve_context


def retriever_fn(question: str) -> list[str]:
    """Retrieve context strings for a question."""
    context = retrieve_context(question, k=5)
    return [context] if context else []


def run_rag_evals():
    """Run RAG evaluation suite."""
    print("=" * 60)
    print("RAG Evaluation")
    print("=" * 60)

    runner = RAGEvalRunner()
    test_cases = runner.load_test_cases()
    print(f"Loaded {len(test_cases)} test cases")

    samples = runner.build_samples(test_cases, retriever_fn)
    print(f"Built {len(samples)} evaluation samples")

    print("Running RAGAS evaluation (this may take a few minutes)...")
    results = runner.run(samples)

    print("\nResults:")
    print(json.dumps(dict(results), indent=2, default=str))
    return results


async def run_agent_evals():
    """Run agent evaluation suite with sample conversations."""
    print("=" * 60)
    print("Agent Evaluation")
    print("=" * 60)

    runner = AgentEvalRunner()

    sample_messages = [
        HumanMessage(content="What is EBITDA and how is it calculated?"),
        AIMessage(content=(
            "EBITDA stands for Earnings Before Interest, Taxes, Depreciation, "
            "and Amortization. In this model, it is calculated as "
            "EBIT + Depreciation + Amortization (Row 194 of M - Monthly)."
        )),
    ]

    results = await runner.evaluate_all(
        messages=sample_messages,
        reference_goal="Explain EBITDA and its calculation in the financial model",
        reference_topics=["finance", "metrics", "profitability"],
    )

    print("\nResults:")
    print(json.dumps(results, indent=2, default=str))
    return results


def main():
    parser = argparse.ArgumentParser(description="Run evaluation suite")
    parser.add_argument("--rag", action="store_true", help="Run RAG evals")
    parser.add_argument("--agent", action="store_true", help="Run agent evals")
    parser.add_argument("--all", action="store_true", help="Run all evals")
    args = parser.parse_args()

    if not (args.rag or args.agent or args.all):
        args.all = True

    if args.all or args.rag:
        run_rag_evals()

    if args.all or args.agent:
        asyncio.run(run_agent_evals())

    print("\nDone.")


if __name__ == "__main__":
    main()
