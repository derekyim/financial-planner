"""Unit tests for the RAG pipeline."""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.documents import Document


class TestRAGPipelineInit:
    """Tests for RAGPipeline initialization."""

    @patch("agents.rag_pipeline.QdrantClient")
    @patch("agents.rag_pipeline.OpenAIEmbeddings")
    @patch("agents.rag_pipeline.QdrantVectorStore")
    def test_creates_in_memory_qdrant(self, mock_vs, mock_emb, mock_qc):
        from agents.rag_pipeline import RAGPipeline

        pipeline = RAGPipeline()
        mock_qc.assert_called_once_with(":memory:")
        assert pipeline.chunk_size == 500
        assert pipeline.chunk_overlap == 50

    @patch("agents.rag_pipeline.QdrantClient")
    @patch("agents.rag_pipeline.OpenAIEmbeddings")
    @patch("agents.rag_pipeline.QdrantVectorStore")
    def test_custom_chunk_params(self, mock_vs, mock_emb, mock_qc):
        from agents.rag_pipeline import RAGPipeline

        pipeline = RAGPipeline(chunk_size=1000, chunk_overlap=100)
        assert pipeline.chunk_size == 1000
        assert pipeline.chunk_overlap == 100


class TestRAGPipelineDocuments:
    """Tests for document loading and splitting."""

    @patch("agents.rag_pipeline.QdrantClient")
    @patch("agents.rag_pipeline.OpenAIEmbeddings")
    @patch("agents.rag_pipeline.QdrantVectorStore")
    def test_load_documents_missing_dir(self, mock_vs, mock_emb, mock_qc):
        from agents.rag_pipeline import RAGPipeline

        pipeline = RAGPipeline(data_dir=Path("/nonexistent/path"))
        docs = pipeline.load_documents()
        assert docs == []

    @patch("agents.rag_pipeline.QdrantClient")
    @patch("agents.rag_pipeline.OpenAIEmbeddings")
    @patch("agents.rag_pipeline.QdrantVectorStore")
    def test_split_documents(self, mock_vs, mock_emb, mock_qc):
        from agents.rag_pipeline import RAGPipeline

        pipeline = RAGPipeline()
        long_text = "This is a test sentence. " * 100
        docs = [Document(page_content=long_text, metadata={"source": "test"})]
        chunks = pipeline.split_documents(docs)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.page_content) <= 500 + 50

    @patch("agents.rag_pipeline.QdrantClient")
    @patch("agents.rag_pipeline.OpenAIEmbeddings")
    @patch("agents.rag_pipeline.QdrantVectorStore")
    def test_add_documents_empty(self, mock_vs, mock_emb, mock_qc):
        from agents.rag_pipeline import RAGPipeline

        pipeline = RAGPipeline()
        pipeline.add_documents([])
        pipeline.vector_store.add_documents.assert_not_called()

    @patch("agents.rag_pipeline.QdrantClient")
    @patch("agents.rag_pipeline.OpenAIEmbeddings")
    @patch("agents.rag_pipeline.QdrantVectorStore")
    def test_add_documents_calls_vector_store(self, mock_vs, mock_emb, mock_qc):
        from agents.rag_pipeline import RAGPipeline

        pipeline = RAGPipeline()
        docs = [Document(page_content="test", metadata={"source": "x"})]
        pipeline.add_documents(docs)
        pipeline.vector_store.add_documents.assert_called_once_with(documents=docs)


class TestRetrieveContext:
    """Tests for the retrieve_context convenience function."""

    @patch("agents.rag_pipeline.get_rag_pipeline")
    def test_returns_formatted_string(self, mock_get):
        from agents.rag_pipeline import retrieve_context

        mock_pipeline = MagicMock()
        mock_pipeline.retrieve.return_value = [
            Document(page_content="EBITDA info", metadata={"source": "glossary.txt"}),
            Document(page_content="Revenue info", metadata={"source": "finance.txt"}),
        ]
        mock_get.return_value = mock_pipeline

        result = retrieve_context("What is EBITDA?", k=2)
        assert "EBITDA info" in result
        assert "Revenue info" in result
        assert "[Source 1" in result
        assert "[Source 2" in result

    @patch("agents.rag_pipeline.get_rag_pipeline")
    def test_returns_no_context_message(self, mock_get):
        from agents.rag_pipeline import retrieve_context

        mock_pipeline = MagicMock()
        mock_pipeline.retrieve.return_value = []
        mock_get.return_value = mock_pipeline

        result = retrieve_context("nonsense query")
        assert "No relevant context found" in result
