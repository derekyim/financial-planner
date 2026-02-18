"""RAG Pipeline for Strategic Guidance Agent.

Implements vector store setup, document ingestion, and retrieval
using the same tech stack as the reference notebooks:
- OpenAI text-embedding-3-small embeddings
- Qdrant vector store (in-memory)
- RecursiveCharacterTextSplitter for chunking
"""

import os
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


class RAGPipeline:
    """RAG pipeline for business knowledge retrieval.
    
    Handles document loading, embedding, storage, and retrieval.
    """
    
    def __init__(
        self,
        data_dir: Optional[Path] = None,
        collection_name: str = COLLECTION_NAME,
        embedding_model: str = EMBEDDING_MODEL,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP,
    ):
        """Initialize the RAG pipeline.
        
        Args:
            data_dir: Directory containing knowledge documents.
            collection_name: Name for the Qdrant collection.
            embedding_model: OpenAI embedding model to use.
            chunk_size: Size of text chunks.
            chunk_overlap: Overlap between chunks.
        """
        self.data_dir = data_dir or DATA_DIR
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
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
    
    def load_documents(self) -> list[Document]:
        """Load documents from the data directory.
        
        Returns:
            List of loaded documents.
        """
        if not self.data_dir.exists():
            print(f"Data directory not found: {self.data_dir}")
            print("Run 'python scrape_data.py' to create sample documents.")
            return []
        
        # Load all .txt files recursively
        loader = DirectoryLoader(
            str(self.data_dir),
            glob="**/*.txt",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
        )
        
        documents = loader.load()
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
        
        Returns:
            Number of chunks ingested.
        """
        documents = self.load_documents()
        if not documents:
            return 0
        
        chunks = self.split_documents(documents)
        self.add_documents(chunks)
        self._is_loaded = True
        
        return len(chunks)
    
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
        
        Args:
            query: The search query.
            k: Number of documents to retrieve.
            
        Returns:
            List of relevant documents.
        """
        retriever = self.get_retriever(k=k)
        return retriever.invoke(query)
    
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
    
    Returns:
        The RAG pipeline instance.
    """
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
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
