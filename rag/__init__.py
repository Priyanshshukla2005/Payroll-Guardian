"""AI Payroll Guardian — Compliance & Payroll RAG Knowledge Layer."""

from rag.chunking.chunker import SemanticChunker
from rag.citations.citations import CitationFormatter
from rag.embeddings.embeddings import (
    BaseEmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
    TFIDFEmbeddingProvider,
)
from rag.evaluation.evaluation import RAGEvalQuery, RAGEvaluationReport, RAGEvaluator
from rag.ingestion.document_loader import DocumentLoader
from rag.ingestion.document_registry import DocumentRegistry
from rag.metadata import (
    AuthorityLevel,
    ChunkMetadata,
    DocumentMetadata,
    Jurisdiction,
    RetrievedChunk,
    SourceType,
    StructuredRAGResponse,
    Topic,
)
from rag.retrieval.reranker import AuthorityAwareReranker
from rag.retrieval.retriever import PayrollRAGRetriever
from rag.retrieval.vector_store import PayrollVectorStore

__all__ = [
    "AuthorityLevel",
    "SourceType",
    "Topic",
    "Jurisdiction",
    "DocumentMetadata",
    "ChunkMetadata",
    "RetrievedChunk",
    "StructuredRAGResponse",
    "DocumentRegistry",
    "DocumentLoader",
    "SemanticChunker",
    "BaseEmbeddingProvider",
    "TFIDFEmbeddingProvider",
    "SentenceTransformerEmbeddingProvider",
    "PayrollVectorStore",
    "AuthorityAwareReranker",
    "CitationFormatter",
    "PayrollRAGRetriever",
    "RAGEvaluator",
    "RAGEvalQuery",
    "RAGEvaluationReport",
]
