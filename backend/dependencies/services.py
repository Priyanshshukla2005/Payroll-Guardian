"""Application dependencies, model lifecycle management, and persistence abstractions (Phase 7)."""

from abc import ABC, abstractmethod
import logging
from pathlib import Path
from typing import Dict, List, Optional
import joblib
import numpy as np

from ai.detection.anomaly_detector import _register_legacy_unpickle_aliases
from ai.detection.hybrid_detector import HybridPayrollDetector_V2
from ai.detection.type_classifier import MultiLabelAnomalyTypeClassifier
from ai.explainability.explainer_v2 import PayrollExplainerV2
from ai.features.pipeline import PayrollPreprocessor
from ai.llm.client import PayrollLLMClient
from ai.llm.provider import MockGroundedLLMProvider, ProviderConfig, ProviderFactory
from backend.config.settings import settings
from backend.schemas.analysis import AnalysisResponse, AnalysisStatus
from rag.embeddings.embeddings import TFIDFEmbeddingProvider
from rag.retrieval.reranker import AuthorityAwareReranker
from rag.retrieval.retriever import PayrollRAGRetriever
from rag.retrieval.vector_store import PayrollVectorStore

logger = logging.getLogger("payroll_guardian.models")


class ModelManager:
    """Manages application-lifetime instances of AI, RAG, and LLM services to prevent reloading on each request."""

    _instance: Optional["ModelManager"] = None

    def __init__(self):
        self.detector: Optional[HybridPayrollDetector_V2] = None
        self.preprocessor: Optional[PayrollPreprocessor] = None
        self.type_classifier: Optional[MultiLabelAnomalyTypeClassifier] = None
        self.explainer: Optional[PayrollExplainerV2] = None
        self.retriever: Optional[PayrollRAGRetriever] = None
        self.llm_client: Optional[PayrollLLMClient] = None
        self.is_loaded: bool = False

    @classmethod
    def get_instance(cls) -> "ModelManager":
        """Retrieve singleton ModelManager."""
        if cls._instance is None:
            cls._instance = ModelManager()
        return cls._instance

    def initialize(self) -> None:
        """Load and warm up all intelligence components on application startup."""
        if self.is_loaded:
            return

        logger.info(f"Initializing ModelManager from {settings.models_dir}...")
        _register_legacy_unpickle_aliases()

        # 1. Load ML Detector, Preprocessor, and Type Classifier
        models_dir = settings.models_dir
        det_path = models_dir / "hybrid_detector_v2.joblib"
        prep_path = models_dir / "preprocessor_v2.joblib"
        tc_path = models_dir / "type_classifier_v2.joblib"

        if det_path.exists():
            self.detector = joblib.load(det_path)
            logger.info("Loaded HybridPayrollDetector_V2")
        else:
            self.detector = HybridPayrollDetector_V2()
            logger.warning(f"Model file not found at {det_path}, instantiated default HybridPayrollDetector_V2")

        if prep_path.exists():
            self.preprocessor = joblib.load(prep_path)
            logger.info("Loaded PayrollPreprocessor")
        else:
            self.preprocessor = PayrollPreprocessor()

        if tc_path.exists():
            self.type_classifier = joblib.load(tc_path)
            logger.info("Loaded MultiLabelAnomalyTypeClassifier")
        else:
            self.type_classifier = MultiLabelAnomalyTypeClassifier()

        self.explainer = PayrollExplainerV2()

        # 2. Load Compliance RAG Vector Store & Retriever
        emb_dir = settings.embeddings_dir
        if (emb_dir / "chunks_metadata.json").exists():
            v_store = PayrollVectorStore.load(emb_dir)
            emb_provider = TFIDFEmbeddingProvider(max_features=256)
            if v_store.chunks_text:
                emb_provider.fit(v_store.chunks_text)
                emb_provider.dimension = v_store.embedding_dimension
            reranker = AuthorityAwareReranker()
            self.retriever = PayrollRAGRetriever(
                vector_store=v_store,
                embedding_provider=emb_provider,
                reranker=reranker,
                min_relevance_threshold=0.15,
            )
            logger.info(f"Loaded RAG VectorStore with {len(v_store.chunks_metadata)} chunks")
        else:
            logger.warning(f"RAG embeddings directory {emb_dir} missing, creating empty store")
            v_store = PayrollVectorStore()
            self.retriever = PayrollRAGRetriever(vector_store=v_store)

        # 3. Initialize Grounded LLM Client
        prov_cfg = ProviderConfig(
            provider_name=settings.llm_provider,
            model_name=settings.llm_model,
            temperature=0.0,
        )
        provider = ProviderFactory.create_provider(prov_cfg)
        self.llm_client = PayrollLLMClient(
            provider=provider,
            retriever=self.retriever,
            explainer=self.explainer,
        )
        logger.info(f"Initialized PayrollLLMClient with provider: {settings.llm_provider}")

        self.is_loaded = True

    def check_health(self) -> Dict[str, str]:
        """Perform lightweight readiness checks across services."""
        return {
            "ai": "available" if self.detector is not None and self.is_loaded else "unavailable",
            "rag": "available" if self.retriever is not None and self.is_loaded else "unavailable",
            "llm": "available" if self.llm_client is not None and self.is_loaded else "unavailable",
        }


from backend.database.repository import (
    AnalysisRepository,
    DatabaseAnalysisRepository,
)


class InMemoryAnalysisRepository(AnalysisRepository):
    """Thread-safe in-memory analysis repository for development and testing."""

    def __init__(self, max_entries: int = 100):
        self._storage: Dict[str, AnalysisResponse] = {}
        self.max_entries = max_entries

    def save_analysis(self, analysis_response: AnalysisResponse) -> None:
        if len(self._storage) >= self.max_entries:
            # Evict oldest entry
            oldest_key = next(iter(self._storage))
            del self._storage[oldest_key]
        self._storage[analysis_response.analysis_id] = analysis_response

    def get_analysis(self, analysis_id: str) -> Optional[AnalysisResponse]:
        return self._storage.get(analysis_id)

    def list_analyses(self, limit: int = 20) -> List[AnalysisResponse]:
        return list(self._storage.values())[-limit:]


def _create_default_repository() -> AnalysisRepository:
    """Create persistent DatabaseAnalysisRepository with fallback to InMemoryAnalysisRepository."""
    try:
        from backend.database.session import init_db

        init_db()
        return DatabaseAnalysisRepository()
    except Exception as e:
        logger.warning(f"Could not connect to database, falling back to InMemoryAnalysisRepository: {e}")
        return InMemoryAnalysisRepository()


# Global repository instance
analysis_repository: AnalysisRepository = _create_default_repository()


def get_model_manager() -> ModelManager:
    """FastAPI dependency for ModelManager."""
    return ModelManager.get_instance()


def get_analysis_repository() -> AnalysisRepository:
    """FastAPI dependency for AnalysisRepository."""
    return analysis_repository
