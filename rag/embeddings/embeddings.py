"""Modular embedding provider interface for AI Payroll Guardian RAG (Phase 5).

Supports SentenceTransformer neural embeddings with a robust deterministic TF-IDF/BM25
dense vectorizer fallback.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Union
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


class BaseEmbeddingProvider(ABC):
    """Abstract base class for all RAG embedding models."""

    def __init__(self, model_name: str, dimension: int):
        self.model_name = model_name
        self.dimension = dimension

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """Compute embeddings for a list of document strings."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> np.ndarray:
        """Compute embedding vector for a query string."""
        pass


class TFIDFEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic dense n-gram TF-IDF embedding provider."""

    def __init__(self, max_features: int = 256):
        super().__init__(model_name="tfidf-dense-ngram-256", dimension=max_features)
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=(1, 2),
            sublinear_tf=True,
            stop_words="english",
        )
        self.is_fitted: bool = False

    def fit(self, texts: List[str]) -> "TFIDFEmbeddingProvider":
        """Fit vocabulary on the knowledge corpus."""
        self.vectorizer.fit(texts)
        self.is_fitted = True
        self.dimension = len(self.vectorizer.get_feature_names_out())
        return self

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """Embed list of documents."""
        if not self.is_fitted:
            self.fit(texts)
        dense = self.vectorizer.transform(texts).toarray().astype(np.float32)
        # Normalize L2 norm
        norms = np.linalg.norm(dense, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return dense / norms

    def embed_query(self, text: str) -> np.ndarray:
        """Embed query string."""
        if not self.is_fitted:
            raise RuntimeError("TFIDFEmbeddingProvider must be fitted before embedding queries.")
        dense = self.vectorizer.transform([text]).toarray().astype(np.float32)[0]
        norm = np.linalg.norm(dense)
        if norm > 0:
            dense = dense / norm
        return dense


class SentenceTransformerEmbeddingProvider(BaseEmbeddingProvider):
    """SentenceTransformer neural embedding provider with graceful local fallback."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        super().__init__(model_name=model_name, dimension=384)
        self.model = None
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
        except Exception:
            # Fallback to TFIDF if torch/sentence_transformers weights unavailable
            self.fallback = TFIDFEmbeddingProvider(max_features=384)
        else:
            self.fallback = None

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        if self.model is not None:
            emb = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
            return emb.astype(np.float32)
        return self.fallback.embed_documents(texts)

    def embed_query(self, text: str) -> np.ndarray:
        if self.model is not None:
            emb = self.model.encode([text], convert_to_numpy=True, normalize_embeddings=True)[0]
            return emb.astype(np.float32)
        return self.fallback.embed_query(text)
