"""Unit tests for document loader, structural chunker, retriever, and evaluation engine."""

from pathlib import Path
import pytest

from rag.chunking.chunker import SemanticChunker
from rag.ingestion.document_loader import DocumentLoader
from rag.embeddings.embeddings import TFIDFEmbeddingProvider
from rag.evaluation.evaluation import RAGEvaluator
from rag.metadata import (
    AuthorityLevel,
    DocumentMetadata,
    Jurisdiction,
    SourceType,
    Topic,
)
from rag.retrieval.reranker import AuthorityAwareReranker
from rag.retrieval.retriever import PayrollRAGRetriever
from rag.retrieval.vector_store import PayrollVectorStore


def test_document_loader_parsing():
    """Verify DocumentLoader loads files and parses header metadata."""
    loader = DocumentLoader()
    raw_docs = loader.load_directory(Path("data/knowledge/raw"))
    assert len(raw_docs) >= 6

    doc_ids = [d.document_id for d, _ in raw_docs]
    assert "EPFO_ACT_1952" in doc_ids
    assert "ESIC_ACT_1948" in doc_ids
    assert "MAHARASHTRA_PT_ACT_1975" in doc_ids


def test_semantic_chunker():
    """Verify SemanticChunker splits text into structured units with bound metadata."""
    meta = DocumentMetadata(
        document_id="TEST_DOC",
        title="Test Document",
        source_name="Official",
        source_type=SourceType.GOVERNMENT_ACT,
        authority_level=AuthorityLevel.AUTHORITATIVE,
        jurisdiction=Jurisdiction.INDIA,
        topic=Topic.PF,
        effective_from="2024-01-01",
        file_hash="h1",
        content_hash="c1",
    )
    content = (
        "## Section 1: Intro\nThis is introductory paragraph.\n\n"
        "## Section 2: Details\nThis is detailed paragraph with statutory rules.\n\n"
    )

    chunker = SemanticChunker(target_chunk_size=300)
    chunks = chunker.chunk_document(meta, content)

    assert len(chunks) == 2
    c1_meta, c1_text = chunks[0]
    assert c1_meta.document_id == "TEST_DOC"
    assert c1_meta.section == "Section 1: Intro"
    assert "Section 1: Intro" in c1_text


def test_retriever_date_and_jurisdiction_filtering():
    """Verify PayrollRAGRetriever enforces date applicability and jurisdiction isolation."""
    # Build mini in-memory vector store
    loader = DocumentLoader()
    raw_docs = loader.load_directory(Path("data/knowledge/raw"))

    chunker = SemanticChunker()
    all_chunks = []
    for d, text in raw_docs:
        all_chunks.extend(chunker.chunk_document(d, text))

    texts = [t for _, t in all_chunks]
    emb = TFIDFEmbeddingProvider(max_features=256)
    emb.fit(texts)

    v_store = PayrollVectorStore(embedding_dimension=emb.dimension)
    v_store.add_chunks(all_chunks, emb.embed_documents(texts))

    retriever = PayrollRAGRetriever(
        vector_store=v_store,
        embedding_provider=emb,
        reranker=AuthorityAwareReranker(),
    )

    # 1. Maharashtra PT Query should return Maharashtra PT document
    resp_mh = retriever.retrieve(
        query="professional tax 200 per month and 300 in February",
        jurisdiction=Jurisdiction.MAHARASHTRA,
        payroll_date="2024-02-01",
        topic=Topic.PROFESSIONAL_TAX,
    )
    assert resp_mh.status == "SUCCESS"
    assert len(resp_mh.results) > 0
    assert resp_mh.results[0].document_id == "MAHARASHTRA_PT_ACT_1975"

    # 2. Unknown Jurisdiction Query must return JURISDICTION_UNKNOWN
    resp_unk = retriever.retrieve(
        query="professional tax rules",
        jurisdiction=Jurisdiction.UNKNOWN,
        payroll_date="2024-02-01",
    )
    assert resp_unk.status == "JURISDICTION_UNKNOWN"

    # 3. Full Evaluator benchmark
    evaluator = RAGEvaluator(retriever)
    report = evaluator.evaluate()
    assert report.recall_at_1 >= 0.85
    assert report.negative_test_pass_rate == 1.0
