"""RAG Pipeline for Strategic Guidance Agent.

Implements vector store setup, document ingestion, and retrieval
using the same tech stack as the reference notebooks:
- OpenAI text-embedding-3-small embeddings
- Qdrant vector store (in-memory)
- RecursiveCharacterTextSplitter for chunking

Supports two retrieval modes controlled by the ADVANCED_RETRIEVAL env var:
- Dense-only (default): Standard Qdrant cosine similarity search
- Hybrid (advanced): BM25 sparse + dense retrieval fused via Reciprocal Rank Fusion
  with NLTK tokenization (stop-word removal, Porter stemming, punctuation stripping),
  BM25 score thresholding, and asymmetric RRF weighting (dense 1.5x).
"""

import os
import re
from pathlib import Path
from typing import Optional

from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams


# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
COLLECTION_NAME = "business_knowledge"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMS = 1536
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
RETRIEVAL_K = 5

ADVANCED_RETRIEVAL = os.environ.get("ADVANCED_RETRIEVAL", "false").lower() == "true"


class RAGPipeline:
    """RAG pipeline for business knowledge retrieval.
    
    Handles document loading, embedding, storage, and retrieval.
    When advanced_retrieval is True, combines dense vector search with
    BM25 sparse retrieval using Reciprocal Rank Fusion (RRF).
    """
    
    def __init__(
        self,
        data_dir: Optional[Path] = None,
        collection_name: str = COLLECTION_NAME,
        embedding_model: str = EMBEDDING_MODEL,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP,
        advanced_retrieval: bool = False,
    ):
        """Initialize the RAG pipeline.
        
        Args:
            data_dir: Directory containing knowledge documents.
            collection_name: Name for the Qdrant collection.
            embedding_model: OpenAI embedding model to use.
            chunk_size: Size of text chunks.
            chunk_overlap: Overlap between chunks.
            advanced_retrieval: If True, use hybrid BM25+dense retrieval with RRF.
        """
        self.data_dir = data_dir or DATA_DIR
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.advanced_retrieval = advanced_retrieval
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        
        # Initialize Qdrant client (in-memory)
        self.qdrant_client = QdrantClient(":memory:")
        
        # Create collection
        self.qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=EMBEDDING_DIMS, distance=Distance.COSINE),
        )
        
        # Initialize vector store
        self.vector_store = QdrantVectorStore(
            client=self.qdrant_client,
            collection_name=collection_name,
            embedding=self.embeddings,
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        
        self._is_loaded = False
        
        # BM25 components (populated during ingest when advanced_retrieval=True)
        self._bm25 = None
        self._bm25_docs: list[Document] = []
    
    def load_documents(self) -> list[Document]:
        """Load documents from the data directory.
        
        Returns:
            List of loaded documents.
        """
        if not self.data_dir.exists():
            print(f"Data directory not found: {self.data_dir}")
            print("Run 'python scrape_data.py' to create sample documents.")
            return []
        
        documents = []
        for pattern in ["**/*.txt", "**/*.md"]:
            loader = DirectoryLoader(
                str(self.data_dir),
                glob=pattern,
                loader_cls=TextLoader,
                loader_kwargs={"encoding": "utf-8"},
            )
            documents.extend(loader.load())
        
        print(f"Loaded {len(documents)} documents from {self.data_dir}")
        
        return documents
    
    def split_documents(self, documents: list[Document]) -> list[Document]:
        """Split documents into chunks.
        
        Args:
            documents: List of documents to split.
            
        Returns:
            List of document chunks.
        """
        chunks = self.text_splitter.split_documents(documents)
        print(f"Split into {len(chunks)} chunks")
        return chunks
    
    def add_documents(self, documents: list[Document]) -> None:
        """Add documents to the vector store.
        
        Args:
            documents: List of document chunks to add.
        """
        if not documents:
            print("No documents to add")
            return
        
        self.vector_store.add_documents(documents=documents)
        print(f"Added {len(documents)} documents to vector store")
    
    def ingest(self) -> int:
        """Load, split, and add all documents to the vector store.
        
        When advanced_retrieval is enabled, also builds a BM25 index
        over the same chunks for hybrid retrieval.
        
        Returns:
            Number of chunks ingested.
        """
        documents = self.load_documents()
        if not documents:
            return 0
        
        chunks = self.split_documents(documents)
        self.add_documents(chunks)
        self._is_loaded = True
        
        if self.advanced_retrieval:
            self._build_bm25_index(chunks)
            print(f"[RAG] Advanced retrieval enabled: BM25 index built over {len(chunks)} chunks")
        
        return len(chunks)
    
    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Tokenize text with punctuation stripping, stop-word removal, and stemming."""
        from nltk.stem import PorterStemmer
        from nltk.corpus import stopwords

        _stemmer = PorterStemmer()
        _stop_words = set(stopwords.words("english"))

        tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
        return [_stemmer.stem(t) for t in tokens if t not in _stop_words and len(t) > 1]

    def _build_bm25_index(self, chunks: list[Document]) -> None:
        """Build a BM25 sparse index over ingested chunks with proper NLP tokenization."""
        from rank_bm25 import BM25Okapi

        tokenized = [self._tokenize(doc.page_content) for doc in chunks]
        self._bm25_docs = chunks
        self._bm25 = BM25Okapi(tokenized)
    
    def get_retriever(self, k: int = RETRIEVAL_K):
        """Get a retriever for the vector store.
        
        Args:
            k: Number of documents to retrieve.
            
        Returns:
            A retriever instance.
        """
        if not self._is_loaded:
            self.ingest()
        
        return self.vector_store.as_retriever(search_kwargs={"k": k})
    
    def retrieve(self, query: str, k: int = RETRIEVAL_K) -> list[Document]:
        """Retrieve relevant documents for a query.
        
        Uses hybrid retrieval (BM25 + dense with RRF) when advanced_retrieval
        is enabled, otherwise falls back to dense-only retrieval.
        
        Args:
            query: The search query.
            k: Number of documents to retrieve.
            
        Returns:
            List of relevant documents.
        """
        if self.advanced_retrieval and self._bm25 is not None:
            return self._hybrid_retrieve(query, k)
        retriever = self.get_retriever(k=k)
        return retriever.invoke(query)
    
    def _hybrid_retrieve(self, query: str, k: int) -> list[Document]:
        """Combine dense vector search with BM25 using Reciprocal Rank Fusion.
        
        Retrieves 2*k candidates from dense, score-thresholded candidates from
        BM25, then fuses with asymmetric weighting (dense 1.5x).
        """
        if not self._is_loaded:
            self.ingest()

        dense_results = self.vector_store.similarity_search(query, k=k * 2)

        tokenized_query = self._tokenize(query)
        bm25_scores = self._bm25.get_scores(tokenized_query)

        if len(bm25_scores) == 0:
            return dense_results[:k]

        mean_score = float(sum(bm25_scores)) / len(bm25_scores)
        std_score = (sum((s - mean_score) ** 2 for s in bm25_scores) / len(bm25_scores)) ** 0.5
        threshold = mean_score + std_score

        scored = [(i, bm25_scores[i]) for i in range(len(bm25_scores)) if bm25_scores[i] > threshold]
        scored.sort(key=lambda x: x[1], reverse=True)
        sparse_results = [self._bm25_docs[i] for i, _ in scored[:k * 2]]

        return self._reciprocal_rank_fusion(dense_results, sparse_results, k, dense_weight=1.5)
    
    @staticmethod
    def _reciprocal_rank_fusion(
        list_a: list[Document],
        list_b: list[Document],
        k: int,
        rrf_k: int = 60,
        dense_weight: float = 1.0,
    ) -> list[Document]:
        """Merge two ranked document lists using RRF scoring.
        
        Args:
            list_a: Dense retrieval results (weighted by dense_weight).
            list_b: Sparse (BM25) retrieval results (weight 1.0).
            k: Number of results to return.
            rrf_k: RRF constant (default 60).
            dense_weight: Multiplier for dense scores (>1.0 favors dense).
        """
        scores: dict[str, float] = {}
        doc_map: dict[str, Document] = {}

        for rank, doc in enumerate(list_a):
            key = doc.page_content[:100]
            scores[key] = scores.get(key, 0.0) + dense_weight / (rrf_k + rank + 1)
            doc_map[key] = doc

        for rank, doc in enumerate(list_b):
            key = doc.page_content[:100]
            scores[key] = scores.get(key, 0.0) + 1.0 / (rrf_k + rank + 1)
            if key not in doc_map:
                doc_map[key] = doc

        ranked_keys = sorted(scores, key=scores.get, reverse=True)[:k]
        return [doc_map[key] for key in ranked_keys]
    
    def similarity_search(self, query: str, k: int = RETRIEVAL_K) -> list[Document]:
        """Perform similarity search on the vector store.
        
        Args:
            query: The search query.
            k: Number of results.
            
        Returns:
            List of similar documents.
        """
        if not self._is_loaded:
            self.ingest()
        
        return self.vector_store.similarity_search(query, k=k)
    
    def similarity_search_with_score(
        self, query: str, k: int = RETRIEVAL_K
    ) -> list[tuple[Document, float]]:
        """Perform similarity search with relevance scores.
        
        Args:
            query: The search query.
            k: Number of results.
            
        Returns:
            List of (document, score) tuples.
        """
        if not self._is_loaded:
            self.ingest()
        
        return self.vector_store.similarity_search_with_score(query, k=k)


# Module-level singleton for easy access
_rag_pipeline: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create the RAG pipeline singleton.
    
    Reads ADVANCED_RETRIEVAL env var to decide retrieval mode.
    
    Returns:
        The RAG pipeline instance.
    """
    global _rag_pipeline
    if _rag_pipeline is None:
        use_advanced = os.environ.get("ADVANCED_RETRIEVAL", "false").lower() == "true"
        _rag_pipeline = RAGPipeline(advanced_retrieval=use_advanced)
        _rag_pipeline.ingest()
    return _rag_pipeline


def retrieve_context(query: str, k: int = RETRIEVAL_K) -> str:
    """Retrieve context for a query as a formatted string.
    
    Args:
        query: The search query.
        k: Number of documents to retrieve.
        
    Returns:
        Formatted context string.
    """
    pipeline = get_rag_pipeline()
    docs = pipeline.retrieve(query, k=k)
    
    if not docs:
        return "No relevant context found."
    
    context_parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "Unknown")
        context_parts.append(f"[Source {i}: {source}]\n{doc.page_content}")
    
    return "\n\n---\n\n".join(context_parts)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test the RAG pipeline
    print("Testing RAG Pipeline...")
    print("=" * 60)
    
    pipeline = RAGPipeline()
    num_chunks = pipeline.ingest()
    
    if num_chunks > 0:
        # Test queries
        test_queries = [
            "What is EBITDA and how is it calculated?",
            "How do I optimize my Amazon listings?",
            "What are the best strategies for reducing shipping costs?",
        ]
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            print("-" * 40)
            
            results = pipeline.similarity_search_with_score(query, k=3)
            for doc, score in results:
                print(f"Score: {score:.3f}")
                print(f"Content: {doc.page_content[:200]}...")
                print()
