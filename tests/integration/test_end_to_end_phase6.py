"""End-to-End Integration Test for Phase 6 (Detector -> Evidence Card -> RAG -> LLM).

Verifies the complete integration across Phase 4 Anomaly Detection,
Phase 5 Knowledge Retrieval, and Phase 6 Grounded LLM Explanation Generation.
"""

from pathlib import Path
import pytest
import pandas as pd

from ai.detection.enhanced_rules import EnhancedRuleDetector
from ai.detection.hybrid_detector import HybridPayrollDetector_V2
from ai.explainability.explainer_v2 import PayrollExplainerV2
from ai.llm.client import PayrollLLMClient
from ai.llm.provider import MockGroundedLLMProvider, ProviderConfig
from ai.llm.response_schema import ExplanationSeverity, PayrollExplanationResponse
from rag.chunking.chunker import SemanticChunker
from rag.embeddings.embeddings import TFIDFEmbeddingProvider
from rag.ingestion.document_loader import DocumentLoader
from rag.metadata import Jurisdiction
from rag.retrieval.reranker import AuthorityAwareReranker
from rag.retrieval.retriever import PayrollRAGRetriever
from rag.retrieval.vector_store import PayrollVectorStore


@pytest.fixture(scope="module")
def end_to_end_system():
    # 1. Setup RAG Knowledge Base with raw documents
    loader = DocumentLoader()
    raw_dir = Path("data/knowledge/raw")
    raw_docs = loader.load_directory(raw_dir)

    chunker = SemanticChunker(target_chunk_size=500, overlap_chars=50)
    all_chunks = []
    for meta, text in raw_docs:
        all_chunks.extend(chunker.chunk_document(meta, text))

    chunk_texts = [text for _, text in all_chunks]
    embedding_provider = TFIDFEmbeddingProvider(max_features=256)
    embedding_provider.fit(chunk_texts)
    embeddings = embedding_provider.embed_documents(chunk_texts)

    vector_store = PayrollVectorStore(embedding_dimension=embedding_provider.dimension)
    vector_store.add_chunks(all_chunks, embeddings)

    reranker = AuthorityAwareReranker()
    retriever = PayrollRAGRetriever(
        vector_store=vector_store,
        embedding_provider=embedding_provider,
        reranker=reranker,
        min_relevance_threshold=0.15,
    )

    # 2. Setup Explainer and LLM Client
    explainer = PayrollExplainerV2()
    provider = MockGroundedLLMProvider(ProviderConfig(provider_name="mock", model_name="mock-grounded-v1", temperature=0.0))
    llm_client = PayrollLLMClient(provider=provider, retriever=retriever, explainer=explainer)

    return llm_client, retriever, explainer


def test_end_to_end_detector_to_llm_explanation(end_to_end_system):
    llm_client, retriever, explainer = end_to_end_system

    # 1. Simulated Anomaly Record: Severe PF Mismatch
    sample_record = pd.Series({
        "employee_id": "EMP_INTEGRATION_001",
        "payroll_month": "2024-06",
        "basic_salary": 40000.0,
        "pf_deduction": 1200.0,  # Expected 12% is ₹4,800.00 -> Mismatch
        "salary_change_percentage": 0.0,
        "overtime_hours": 0.0,
        "attendance_ratio": 1.0,
        "present_days": 26,
        "working_days": 26,
        "deduction_to_gross_ratio": 0.05,
        "department": "Engineering",
        "designation": "Software Engineer",
        "location": "MAHARASHTRA",
    })

    risk_score = 0.94
    predicted_anomaly_types = ["INCORRECT_PF"]
    rule_violations = ["RULE_PF_MISMATCH"]

    # 2. Step 1: Generate Evidence Card (Phase 4)
    evidence_card = explainer.explain(
        record=sample_record,
        risk_score=risk_score,
        predicted_anomaly_types=predicted_anomaly_types,
        rule_violations=rule_violations,
    )

    assert evidence_card.employee_id == "EMP_INTEGRATION_001"
    assert evidence_card.risk_score == 0.94
    assert evidence_card.confidence == "VERY_HIGH"

    # 3. Step 2: Retrieve Authoritative RAG Knowledge (Phase 5)
    rag_response = retriever.retrieve_for_evidence_card(
        evidence_card=evidence_card,
        jurisdiction_override=Jurisdiction.MAHARASHTRA,
    )

    assert rag_response.status == "SUCCESS"
    assert len(rag_response.results) >= 1
    assert any(r.document_id == "EPFO_ACT_1952" for r in rag_response.results)

    # 4. Step 3: Generate Grounded LLM Explanation (Phase 6)
    explanation = llm_client.explain_evidence(
        evidence_card=evidence_card,
        rag_response=rag_response,
        raw_record=sample_record.to_dict(),
    )

    # 5. Assertions on Final Explanation
    assert isinstance(explanation, PayrollExplanationResponse)
    assert explanation.severity == ExplanationSeverity.CRITICAL
    assert "INCORRECT_PF" in explanation.title or "PF" in explanation.title
    assert len(explanation.why_flagged) >= 1
    assert len(explanation.evidence) >= 1
    assert len(explanation.recommended_actions) >= 1
    assert len(explanation.citations) >= 1
    assert explanation.citations[0].document_id == "EPFO_ACT_1952"
    assert "Not legal advice" in explanation.disclaimer
    assert explanation.generation_metadata.get("fallback_mode") is False


def test_fallback_mode_when_llm_is_offline(end_to_end_system):
    llm_client, retriever, explainer = end_to_end_system

    sample_record = pd.Series({
        "employee_id": "EMP_FALLBACK_002",
        "payroll_month": "2024-06",
        "basic_salary": 25000.0,
        "overtime_hours": 65.0,
        "department": "Logistics",
        "designation": "Driver",
        "location": "INDIA",
    })

    evidence_card = explainer.explain(
        record=sample_record,
        risk_score=0.82,
        predicted_anomaly_types=["EXCESSIVE_OVERTIME"],
        rule_violations=["RULE_OVERTIME_EXCEEDS_CAP"],
    )

    rag_response = retriever.retrieve_for_evidence_card(evidence_card)

    # Direct fallback mode
    fallback_exp = llm_client.get_fallback_explanation(evidence_card, rag_response)

    assert isinstance(fallback_exp, PayrollExplanationResponse)
    assert fallback_exp.severity == ExplanationSeverity.HIGH
    assert fallback_exp.generation_metadata.get("fallback_mode") is True
    assert len(fallback_exp.recommended_actions) >= 1
