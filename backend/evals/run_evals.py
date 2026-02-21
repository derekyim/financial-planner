"""CLI script to run the full evaluation suite.

Usage:
    python -m evals.run_evals --rag          # RAG evals only
    python -m evals.run_evals --agent        # Agent evals only
    python -m evals.run_evals --all          # Both

Each invocation creates a new LangSmith Experiment for graphical comparison.
"""

import sys
import os
from pathlib import Path

_backend_dir = str(Path(__file__).resolve().parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from shared.config import load_env
load_env()

import argparse
import asyncio
import json
from datetime import datetime, timezone

import nest_asyncio
nest_asyncio.apply()

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, AIMessage
from langsmith import Client
from langsmith.evaluation import evaluate as ls_evaluate

from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.metrics import (
    LLMContextRecall,
    LLMContextPrecisionWithReference,
    Faithfulness,
    FactualCorrectness,
    ResponseRelevancy,
    ContextEntityRecall,
    NoiseSensitivity,
)
from ragas.dataset_schema import SingleTurnSample

from evals.agent_evals import AgentEvalRunner
from agents.rag_pipeline import retrieve_context, ADVANCED_RETRIEVAL


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def retriever_fn(question: str) -> list[str]:
    """Retrieve context strings for a question."""
    context = retrieve_context(question, k=5)
    return [context] if context else []


def _ensure_dataset(client: Client, test_cases: list[dict]) -> str:
    """Create or update the LangSmith dataset for RAG evaluation."""
    dataset_name = "rag-eval-test-cases"
    try:
        ds = client.read_dataset(dataset_name=dataset_name)
        existing = list(client.list_examples(dataset_id=ds.id))
        if len(existing) == len(test_cases):
            return dataset_name
        client.delete_dataset(dataset_id=ds.id)
    except Exception:
        pass

    ds = client.create_dataset(
        dataset_name,
        description=f"RAG evaluation — {len(test_cases)} test cases",
    )
    for tc in test_cases:
        client.create_example(
            inputs={"question": tc["question"]},
            outputs={"reference": tc["reference"]},
            dataset_id=ds.id,
        )
    print(f"Created LangSmith dataset '{dataset_name}' with {len(test_cases)} examples")
    return dataset_name


def _make_ragas_evaluator(metric_name, metric):
    """Create a LangSmith evaluator wrapping a single RAGAS metric."""
    def evaluator(run, example):
        reference = example.outputs.get("reference", "")
        sample = SingleTurnSample(
            user_input=example.inputs["question"],
            response=reference,
            retrieved_contexts=run.outputs.get("retrieved_contexts", []),
            reference=reference,
        )
        try:
            loop = asyncio.new_event_loop()
            try:
                score = loop.run_until_complete(metric.single_turn_ascore(sample))
            finally:
                loop.close()
            return {"key": metric_name, "score": float(score) if score is not None else 0.0}
        except Exception as e:
            print(f"  [warn] {metric_name} failed on '{example.inputs['question'][:50]}': {e}")
            return {"key": metric_name, "score": 0.0}
    evaluator.__name__ = metric_name
    return evaluator


def run_rag_evals():
    """Run RAG evaluation as a LangSmith Experiment."""
    retrieval_mode = "hybrid" if ADVANCED_RETRIEVAL else "dense"
    experiment_prefix = f"rag-eval-{retrieval_mode}"

    print("=" * 60)
    print(f"RAG Evaluation  [mode={retrieval_mode}]")
    print(f"Experiment prefix: {experiment_prefix}")
    print("=" * 60)

    client = Client()

    test_data_path = Path(__file__).parent.parent / "test_data" / "manual_test_cases.json"
    with open(test_data_path) as f:
        test_cases = json.load(f)
    print(f"Loaded {len(test_cases)} test cases")

    dataset_name = _ensure_dataset(client, test_cases)
    print(f"LangSmith dataset: {dataset_name}")

    print("Ingesting documents into vector store...")
    _ = retriever_fn("warmup")
    print("Ingestion complete.\n")

    def rag_target(inputs: dict) -> dict:
        contexts = retriever_fn(inputs["question"])
        return {"retrieved_contexts": contexts}

    eval_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o-mini"))
    eval_embeddings = LangchainEmbeddingsWrapper(
        OpenAIEmbeddings(model="text-embedding-3-small")
    )

    ragas_metrics = [
        ("LLMContextRecall", LLMContextRecall(llm=eval_llm)),
        ("LLMContextPrecision", LLMContextPrecisionWithReference(llm=eval_llm)),
        ("Faithfulness", Faithfulness(llm=eval_llm)),
        ("FactualCorrectness", FactualCorrectness(llm=eval_llm)),
        ("ResponseRelevancy", ResponseRelevancy(llm=eval_llm, embeddings=eval_embeddings)),
        ("ContextEntityRecall", ContextEntityRecall(llm=eval_llm)),
        ("NoiseSensitivity", NoiseSensitivity(llm=eval_llm)),
    ]
    evaluators = [_make_ragas_evaluator(name, m) for name, m in ragas_metrics]

    print(f"Running LangSmith Experiment with {len(evaluators)} RAGAS metrics...")
    print(f"  {len(test_cases)} test cases × {len(evaluators)} metrics = {len(test_cases) * len(evaluators)} evaluations")
    print(f"  View at: https://smith.langchain.com\n")

    results = ls_evaluate(
        rag_target,
        data=dataset_name,
        evaluators=evaluators,
        experiment_prefix=experiment_prefix,
        metadata={"retrieval_mode": retrieval_mode, "timestamp": _timestamp()},
        max_concurrency=1,
    )

    print(f"\nExperiment complete: {experiment_prefix}")
    print("Open LangSmith → Datasets → rag-eval-test-cases → Experiments to compare runs.")

    return results


async def run_agent_evals():
    """Run agent evaluation suite with sample conversations."""
    experiment_name = f"agent-eval-{_timestamp()}"

    print("=" * 60)
    print("Agent Evaluation")
    print(f"Experiment: {experiment_name}")
    print("=" * 60)

    os.environ["LANGCHAIN_PROJECT"] = experiment_name

    runner = AgentEvalRunner()

    sample_messages = [
        HumanMessage(content="What is EBITDA and how is it calculated?"),
        AIMessage(content=(
            "EBITDA stands for Earnings Before Interest, Taxes, Depreciation, "
            "and Amortization. In this model, it is calculated as "
            "EBIT + Depreciation + Amortization (Row 194 of operations)."
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
