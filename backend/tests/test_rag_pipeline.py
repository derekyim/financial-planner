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


class TestHybridRetrieval:
    """Tests for BM25 + dense hybrid retrieval with RRF."""

    @patch("agents.rag_pipeline.QdrantClient")
    @patch("agents.rag_pipeline.OpenAIEmbeddings")
    @patch("agents.rag_pipeline.QdrantVectorStore")
    def test_advanced_flag_sets_attribute(self, mock_vs, mock_emb, mock_qc):
        from agents.rag_pipeline import RAGPipeline

        pipeline = RAGPipeline(advanced_retrieval=True)
        assert pipeline.advanced_retrieval is True
        assert pipeline._bm25 is None  # not built until ingest

    @patch("agents.rag_pipeline.QdrantClient")
    @patch("agents.rag_pipeline.OpenAIEmbeddings")
    @patch("agents.rag_pipeline.QdrantVectorStore")
    def test_default_is_not_advanced(self, mock_vs, mock_emb, mock_qc):
        from agents.rag_pipeline import RAGPipeline

        pipeline = RAGPipeline()
        assert pipeline.advanced_retrieval is False

    def test_rrf_merges_two_lists(self):
        from agents.rag_pipeline import RAGPipeline

        doc_a = Document(page_content="Alpha document about finance", metadata={})
        doc_b = Document(page_content="Beta document about shipping", metadata={})
        doc_c = Document(page_content="Charlie document about ads", metadata={})

        list_a = [doc_a, doc_b]
        list_b = [doc_c, doc_a]

        result = RAGPipeline._reciprocal_rank_fusion(list_a, list_b, k=3)
        assert len(result) == 3
        # doc_a appears in both lists so should rank highest
        assert result[0].page_content == doc_a.page_content

    def test_rrf_respects_k_limit(self):
        from agents.rag_pipeline import RAGPipeline

        docs = [
            Document(page_content=f"Document number {i}" + " padding" * 20, metadata={})
            for i in range(10)
        ]
        result = RAGPipeline._reciprocal_rank_fusion(docs[:5], docs[3:8], k=3)
        assert len(result) == 3

    @patch("agents.rag_pipeline.QdrantClient")
    @patch("agents.rag_pipeline.OpenAIEmbeddings")
    @patch("agents.rag_pipeline.QdrantVectorStore")
    def test_build_bm25_index(self, mock_vs, mock_emb, mock_qc):
        from agents.rag_pipeline import RAGPipeline

        pipeline = RAGPipeline(advanced_retrieval=True)
        chunks = [
            Document(page_content="EBITDA is earnings before interest", metadata={}),
            Document(page_content="Amazon selling strategy guide", metadata={}),
            Document(page_content="Shopify store optimization tips", metadata={}),
        ]
        pipeline._build_bm25_index(chunks)
        assert pipeline._bm25 is not None
        assert len(pipeline._bm25_docs) == 3

    @patch("agents.rag_pipeline.QdrantClient")
    @patch("agents.rag_pipeline.OpenAIEmbeddings")
    @patch("agents.rag_pipeline.QdrantVectorStore")
    def test_hybrid_retrieve_uses_bm25_and_dense(self, mock_vs, mock_emb, mock_qc):
        from agents.rag_pipeline import RAGPipeline

        pipeline = RAGPipeline(advanced_retrieval=True)
        chunks = [
            Document(page_content="EBITDA is earnings before interest taxes", metadata={}),
            Document(page_content="Amazon FBA fulfillment strategy guide", metadata={}),
            Document(page_content="Shopify store optimization and growth", metadata={}),
        ]
        pipeline._build_bm25_index(chunks)
        pipeline._is_loaded = True

        # Mock the dense retrieval
        pipeline.vector_store.similarity_search = MagicMock(return_value=[chunks[1], chunks[0]])

        results = pipeline._hybrid_retrieve("EBITDA earnings", k=2)
        assert len(results) == 2
        pipeline.vector_store.similarity_search.assert_called_once()


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
