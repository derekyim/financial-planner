"""RAG evaluation using RAGAS metrics.

Evaluates the Strategic Guidance RAG pipeline on retrieval quality,
faithfulness, factual correctness, and relevancy.
"""

import json
from pathlib import Path
from typing import Optional

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.metrics import (
    LLMContextRecall,
    Faithfulness,
    FactualCorrectness,
    ResponseRelevancy,
    ContextEntityRecall,
    NoiseSensitivity,
)
from ragas.dataset_schema import SingleTurnSample, EvaluationDataset
from ragas import evaluate, RunConfig

EVAL_MODEL = "gpt-4o-mini"
TEST_DATA_DIR = Path(__file__).parent.parent / "test_data"


class RAGEvalRunner:
    """Runs RAGAS RAG evaluation metrics against a test dataset."""

    def __init__(self, evaluator_model: str = EVAL_MODEL, timeout: int = 360):
        self.llm = LangchainLLMWrapper(ChatOpenAI(model=evaluator_model))
        self.embeddings = LangchainEmbeddingsWrapper(
            OpenAIEmbeddings(model="text-embedding-3-small")
        )
        self.run_config = RunConfig(timeout=timeout)
        self.metrics = [
            LLMContextRecall(),
            Faithfulness(),
            FactualCorrectness(),
            ResponseRelevancy(),
            ContextEntityRecall(),
            NoiseSensitivity(),
        ]

    def load_test_cases(self, path: Optional[Path] = None) -> list[dict]:
        test_file = path or (TEST_DATA_DIR / "manual_test_cases.json")
        with open(test_file) as f:
            return json.load(f)

    def build_samples(
        self,
        test_cases: list[dict],
        retriever_fn,
    ) -> list[SingleTurnSample]:
        """Build RAGAS samples by running each test case through the retriever.

        Args:
            test_cases: List of dicts with 'question' and 'reference' keys.
            retriever_fn: Callable(question) -> list[str] returning context strings.
        """
        samples = []
        for tc in test_cases:
            contexts = retriever_fn(tc["question"])
            samples.append(
                SingleTurnSample(
                    user_input=tc["question"],
                    response=tc.get("reference", ""),
                    retrieved_contexts=contexts,
                    reference=tc.get("reference"),
                )
            )
        return samples

    def run(self, samples: list[SingleTurnSample]) -> dict:
        """Execute RAGAS evaluation and return results dict."""
        dataset = EvaluationDataset(samples=samples)
        results = evaluate(
            dataset=dataset,
            metrics=self.metrics,
            llm=self.llm,
            embeddings=self.embeddings,
            run_config=self.run_config,
        )
        return results
