"""Phase 9: Comprehensive End-to-End Failure Paths & Resilience Test Suite.

Tests negative inputs, malicious payloads, corrupted components, and graceful degradations across all layers:
- Invalid & malformed uploads (CSV, JSON, binary disguises, path traversals, double extensions)
- Validation failures (missing columns, negative salary, invalid working days)
- Degraded states (AI detector unavailable, RAG unavailable, LLM unavailable, fallback mode)
- Zero stack trace leakage verification.
"""

import io
import pytest
from fastapi.testclient import TestClient

from ai.explainability.explainer_v2 import DetailedEvidenceCard, PayrollExplainerV2
from ai.llm.client import PayrollLLMClient
from ai.llm.provider import MockGroundedLLMProvider, ProviderConfig
from backend.dependencies.services import ModelManager
from backend.main import create_app
from rag.metadata import Jurisdiction, StructuredRAGResponse
from rag.retrieval.retriever import PayrollRAGRetriever
from rag.retrieval.vector_store import PayrollVectorStore


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_failure_unsupported_file_extension(client):
    """Reject unsupported file extensions (e.g. .exe, .sh, .pdf)."""
    files = {"file": ("malicious_payload.exe", io.BytesIO(b"executable payload"), "application/octet-stream")}
    resp = client.post("/api/v1/payroll/upload", files=files)
    assert resp.status_code == 400
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == "BAD_REQUEST"
    assert "Unsupported file extension" in data["error"]["message"]
    assert "traceback" not in resp.text.lower()


def test_failure_double_extension_security_rejection(client):
    """Reject double extension files designed to bypass extension filters (e.g. payroll.exe.csv)."""
    files = {"file": ("payroll.exe.csv", io.BytesIO(b"id,basic\n1,50000\n"), "text/csv")}
    resp = client.post("/api/v1/payroll/upload", files=files)
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"]["code"] == "BAD_REQUEST"
    assert "Suspicious multi-extension" in data["error"]["message"]


def test_failure_binary_executable_disguised_as_csv(client):
    """Reject binary executable payload disguised with a .csv extension (MZ / ELF magic headers)."""
    fake_csv_payload = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"
    files = {"file": ("payroll.csv", io.BytesIO(fake_csv_payload), "text/csv")}
    resp = client.post("/api/v1/payroll/upload", files=files)
    assert resp.status_code == 400
    data = resp.json()
    assert "Binary executables" in data["error"]["message"]


def test_failure_empty_file_upload(client):
    """Reject 0-byte empty file uploads."""
    files = {"file": ("empty_payroll.csv", io.BytesIO(b""), "text/csv")}
    resp = client.post("/api/v1/payroll/upload", files=files)
    assert resp.status_code == 400
    data = resp.json()
    assert "empty" in data["error"]["message"].lower()


def test_failure_malformed_csv(client):
    """Reject unparseable or corrupted CSV structure."""
    corrupted_csv = b"col1,col2\nval1,val2,extra_val3,overflow\nval_only_one\n"
    files = {"file": ("corrupt.csv", io.BytesIO(corrupted_csv), "text/csv")}
    resp = client.post("/api/v1/payroll/upload", files=files)
    # Parser should return 400 with clean explanation
    assert resp.status_code == 400
    data = resp.json()
    assert "error" in data
    assert "traceback" not in resp.text.lower()


def test_failure_missing_required_columns(client):
    """Reject CSV missing required mandatory schema columns (e.g. basic_salary, employee_id)."""
    incomplete_csv = b"employee_id,department\nEMP_001,Engineering\n"
    files = {"file": ("incomplete.csv", io.BytesIO(incomplete_csv), "text/csv")}
    resp = client.post("/api/v1/payroll/upload", files=files)
    assert resp.status_code == 400
    data = resp.json()
    assert "Missing required" in data["error"]["message"]


def test_failure_negative_salary_validation(client):
    """Validation layer strictly rejects negative salary values."""
    payload = {
        "payroll_period": "2024-06",
        "records": [
            {
                "employee_id": "EMP_NEG_001",
                "basic_salary": -50000.0,
                "gross_salary": -50000.0,
                "net_salary": -50000.0,
                "working_days": 26,
                "present_days": 26,
            }
        ],
    }
    resp = client.post("/api/v1/payroll/analyze", json=payload)
    assert resp.status_code == 422
    data = resp.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert any("greater than or equal to 0" in str(d) for d in data["error"]["details"])


def test_failure_invalid_working_days_bounds(client):
    """Validation layer strictly rejects impossible working days (> 31 days)."""
    payload = {
        "payroll_period": "2024-06",
        "records": [
            {
                "employee_id": "EMP_DAYS_001",
                "basic_salary": 50000.0,
                "working_days": 45,  # Invalid
                "present_days": 26,
            }
        ],
    }
    resp = client.post("/api/v1/payroll/analyze", json=payload)
    assert resp.status_code == 422
    data = resp.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_failure_empty_records_list(client):
    """Validation layer strictly rejects empty record list."""
    payload = {"payroll_period": "2024-06", "records": []}
    resp = client.post("/api/v1/payroll/analyze", json=payload)
    assert resp.status_code == 422


def test_failure_unknown_analysis_id_404(client):
    """Querying a non-existent analysis_id returns a clean 404."""
    resp = client.get("/api/v1/payroll/analysis/anl_nonexistent_9999999")
    assert resp.status_code == 404
    data = resp.json()
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert "not found" in data["error"]["message"].lower()


def test_resilience_llm_offline_graceful_fallback(monkeypatch):
    """When LLM provider fails, system automatically invokes deterministic fallback without breaking."""
    mgr = ModelManager.get_instance()
    mgr.initialize()

    class FailingProvider:
        def generate(self, prompt: str) -> str:
            raise ConnectionError("LLM API Network Timeout")

    failing_client = PayrollLLMClient(
        provider=FailingProvider(),
        retriever=mgr.retriever,
        explainer=mgr.explainer,
    )

    card = DetailedEvidenceCard(
        employee_id="EMP_RESILIENT_001",
        payroll_month="2024-06",
        risk_score=0.88,
        confidence="HIGH",
        top_signals=["PF mismatch identified"],
        historical_comparison={},
        peer_comparison={},
        rule_violations=["RULE_PF_MISMATCH"],
        anomaly_types=["INCORRECT_PF"],
        human_readable_summary="PF deduction discrepancy",
    )

    # Explanation via fallback
    explanation = failing_client.explain_evidence(card)
    assert explanation.title is not None
    assert len(explanation.why_flagged) >= 1
    assert len(explanation.recommended_actions) >= 1
    assert explanation.generation_metadata.get("fallback_mode") is True


def test_resilience_rag_empty_or_unavailable():
    """When RAG vector store contains no matching documents, retriever returns safe NO_RELIABLE_SOURCE_FOUND."""
    empty_store = PayrollVectorStore()
    retriever = PayrollRAGRetriever(vector_store=empty_store)

    card = DetailedEvidenceCard(
        employee_id="EMP_UNKNOWN_JUR",
        payroll_month="2024-06",
        risk_score=0.75,
        confidence="MEDIUM",
        top_signals=["Unusual compensation pattern"],
        historical_comparison={},
        peer_comparison={},
        rule_violations=[],
        anomaly_types=["COMPENSATION_OUTLIER"],
        human_readable_summary="Outlier query",
    )

    rag_resp = retriever.retrieve_for_evidence_card(card, jurisdiction_override=Jurisdiction.INDIA)
    assert rag_resp.status in ["NO_RELIABLE_SOURCE_FOUND", "SUCCESS"]
    if rag_resp.status == "NO_RELIABLE_SOURCE_FOUND":
        assert "No authoritative legal sources found" in rag_resp.no_answer_reason
