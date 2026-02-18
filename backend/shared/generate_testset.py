"""Synthetic Test Dataset Generation using RAGAS.

Generates test questions and references from the business knowledge documents
for evaluating the RAG pipeline and Strategic Guidance agent.

Uses RAGAS TestsetGenerator for automatic question generation.
"""

import os
from pathlib import Path
from typing import Optional

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader

from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.testset import TestsetGenerator

from dotenv import load_dotenv

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = Path(__file__).parent.parent / "test_data"
DEFAULT_GENERATOR_MODEL = "gpt-4o"
DEFAULT_TESTSET_SIZE = 10


class SyntheticTestsetGenerator:
    """Generator for synthetic test datasets using RAGAS."""
    
    def __init__(
        self,
        generator_model: str = DEFAULT_GENERATOR_MODEL,
        data_dir: Optional[Path] = None,
    ):
        """Initialize the testset generator.
        
        Args:
            generator_model: Model to use for question generation.
            data_dir: Directory containing source documents.
        """
        self.data_dir = data_dir or DATA_DIR
        
        # Initialize generator LLM and embeddings
        self.generator_llm = LangchainLLMWrapper(
            ChatOpenAI(model=generator_model)
        )
        self.generator_embeddings = LangchainEmbeddingsWrapper(
            OpenAIEmbeddings(model="text-embedding-3-small")
        )
        
        # Initialize RAGAS TestsetGenerator
        self.generator = TestsetGenerator(
            llm=self.generator_llm,
            embedding_model=self.generator_embeddings,
        )
    
    def load_documents(self):
        """Load documents from the data directory.
        
        Returns:
            List of loaded LangChain documents.
        """
        if not self.data_dir.exists():
            raise FileNotFoundError(
                f"Data directory not found: {self.data_dir}\n"
                "Run 'python scrape_data.py' to create sample documents."
            )
        
        loader = DirectoryLoader(
            str(self.data_dir),
            glob="**/*.txt",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
        )
        
        documents = loader.load()
        print(f"Loaded {len(documents)} documents from {self.data_dir}")
        
        return documents
    
    def generate(self, testset_size: int = DEFAULT_TESTSET_SIZE):
        """Generate a synthetic testset from the documents.
        
        Args:
            testset_size: Number of test samples to generate.
            
        Returns:
            Generated testset.
        """
        documents = self.load_documents()
        
        print(f"Generating {testset_size} test samples...")
        print("This may take a few minutes...")
        
        testset = self.generator.generate_with_langchain_docs(
            documents,
            testset_size=testset_size,
        )
        
        print(f"Generated {len(testset.samples)} test samples")
        
        return testset
    
    def save_testset(self, testset, output_path: Optional[Path] = None):
        """Save the testset to a file.
        
        Args:
            testset: The generated testset.
            output_path: Path to save the testset.
        """
        if output_path is None:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            output_path = OUTPUT_DIR / "synthetic_testset.json"
        
        # Convert to pandas and save
        df = testset.to_pandas()
        df.to_json(output_path, orient="records", indent=2)
        
        print(f"Saved testset to {output_path}")
        return output_path


def generate_testset(
    testset_size: int = DEFAULT_TESTSET_SIZE,
    save: bool = True,
):
    """Generate and optionally save a synthetic testset.
    
    Args:
        testset_size: Number of test samples to generate.
        save: Whether to save the testset to disk.
        
    Returns:
        The generated testset.
    """
    generator = SyntheticTestsetGenerator()
    testset = generator.generate(testset_size=testset_size)
    
    if save:
        generator.save_testset(testset)
    
    return testset


def create_manual_test_cases():
    """Create manual test cases for evaluation.
    
    Returns:
        List of test case dictionaries.
    """
    test_cases = [
        # Financial terminology questions
        {
            "question": "What is EBITDA and why is it important?",
            "reference": "EBITDA stands for Earnings Before Interest, Taxes, Depreciation, and Amortization. It's a measure of operating performance that shows profitability before accounting for financial decisions and tax effects.",
            "topics": ["finance", "metrics", "profitability"],
        },
        {
            "question": "How is Customer Acquisition Cost (CAC) calculated?",
            "reference": "Customer Acquisition Cost (CAC) is the total cost of acquiring a new customer, including marketing and sales expenses, divided by the number of new customers acquired.",
            "topics": ["finance", "marketing", "metrics"],
        },
        {
            "question": "What is the difference between Gross Profit and Net Income?",
            "reference": "Gross Profit is revenue minus cost of goods sold, while Net Income is the bottom line profit after all expenses, interest, and taxes are deducted.",
            "topics": ["finance", "profitability", "accounting"],
        },
        
        # Amazon selling questions
        {
            "question": "What are the key elements of Amazon listing optimization?",
            "reference": "Key elements include optimized title with keywords, compelling bullet points, high-quality images, backend keywords, and competitive pricing.",
            "topics": ["amazon", "ecommerce", "optimization"],
        },
        {
            "question": "What is the difference between FBA and FBM on Amazon?",
            "reference": "FBA (Fulfillment by Amazon) means Amazon stores and ships your products, while FBM (Fulfillment by Merchant) means you handle storage and shipping yourself.",
            "topics": ["amazon", "fulfillment", "logistics"],
        },
        
        # Advertising questions
        {
            "question": "What is a good ROAS target for Meta advertising?",
            "reference": "A good ROAS (Return on Ad Spend) target is typically 3x or higher for profitability, meaning $3 in revenue for every $1 spent on ads.",
            "topics": ["advertising", "meta", "metrics"],
        },
        {
            "question": "How should I structure my Meta ads funnel?",
            "reference": "Structure with Top of Funnel (60-70% budget) for prospecting, Middle of Funnel (20-30%) for retargeting engaged users, and Bottom of Funnel (10-20%) for conversion.",
            "topics": ["advertising", "meta", "strategy"],
        },
        
        # Operations questions
        {
            "question": "How can I reduce warehouse costs?",
            "reference": "Reduce warehouse costs through demand forecasting, ABC inventory analysis for layout optimization, batch picking, and negotiating with carriers for better shipping rates.",
            "topics": ["operations", "warehouse", "cost optimization"],
        },
        {
            "question": "What is the formula for safety stock?",
            "reference": "Safety Stock = (Max Daily Sales × Max Lead Time) - (Average Daily Sales × Average Lead Time).",
            "topics": ["operations", "inventory", "logistics"],
        },
        
        # Shopify questions
        {
            "question": "What are essential Shopify apps for ecommerce?",
            "reference": "Essential apps include email marketing (Klaviyo), reviews (Judge.me), SMS marketing (Postscript), subscriptions (Recharge), and analytics (Triple Whale).",
            "topics": ["shopify", "ecommerce", "tools"],
        },
    ]
    
    return test_cases


def save_manual_test_cases():
    """Save manual test cases to disk."""
    import json
    
    test_cases = create_manual_test_cases()
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "manual_test_cases.json"
    
    with open(output_path, "w") as f:
        json.dump(test_cases, f, indent=2)
    
    print(f"Saved {len(test_cases)} manual test cases to {output_path}")
    return output_path


if __name__ == "__main__":
    import argparse
    
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Generate synthetic test datasets")
    parser.add_argument(
        "--size",
        type=int,
        default=DEFAULT_TESTSET_SIZE,
        help=f"Number of test samples to generate (default: {DEFAULT_TESTSET_SIZE})",
    )
    parser.add_argument(
        "--manual-only",
        action="store_true",
        help="Only generate manual test cases (no synthetic generation)",
    )
    args = parser.parse_args()
    
    print("=" * 60)
    print("Test Dataset Generator")
    print("=" * 60)
    
    # Always save manual test cases
    print("\n--- Manual Test Cases ---")
    save_manual_test_cases()
    
    # Generate synthetic testset if not manual-only
    if not args.manual_only:
        print("\n--- Synthetic Test Generation ---")
        try:
            testset = generate_testset(testset_size=args.size)
            print("\nSample questions generated:")
            df = testset.to_pandas()
            for i, row in df.head(3).iterrows():
                print(f"  {i+1}. {row.get('user_input', row.get('question', 'N/A'))}")
        except Exception as e:
            print(f"Error generating synthetic testset: {e}")
            print("Manual test cases have been saved successfully.")
