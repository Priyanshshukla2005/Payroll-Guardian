"""Live Integration & Demo Consistency Regression Test Suite.

Verifies:
1. Deterministic demo analysis initialization.
2. Direct retrieval of demo analysis from analysis repository.
3. Assistant query against the same canonical analysis.
4. Compliance search & RAG citations in context.
5. Anomaly list & detail endpoints querying the same analysis.
6. Dashboard summary and anomaly list metrics consistency (100% matching record count).
7. Controlled structured error on nonexistent analysis query.
8. Grounded deterministic fallback when LLM is unavailable.
"""

from fastapi.testclient import TestClient
import pytest

from backend.dependencies.services import (
    AnalysisRepository,
    ModelManager,
    get_analysis_repository,
    get_model_manager,
)
from backend.main import create_app
from backend.services.demo_service import DEMO_ANALYSIS_ID, ensure_demo_analysis


@pytest.fixture
def client():
    """Create FastAPI test client with warmed lifespan context."""
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_1_create_demo_analysis(client: TestClient):
    """1. Create and verify deterministic demo analysis exists."""
    model_mgr = ModelManager.get_instance()
    repo = get_analysis_repository()

    demo = ensure_demo_analysis(repo=repo, model_manager=model_mgr)
    assert demo.analysis_id == DEMO_ANALYSIS_ID
    assert demo.summary.records_analyzed == 250
    assert demo.summary.records_flagged == 12
    assert len(demo.anomalies) == 12


def test_2_retrieve_demo_analysis_from_repository(client: TestClient):
    """2. Retrieve demo analysis from AnalysisRepository and GET /payroll/analysis/{id}."""
    resp = client.get(f"/api/v1/payroll/analysis/{DEMO_ANALYSIS_ID}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["analysis_id"] == DEMO_ANALYSIS_ID
    assert data["summary"]["records_analyzed"] == 250
    assert data["summary"]["records_flagged"] == 12
    assert len(data["anomalies"]) == 12


def test_3_assistant_can_query_same_analysis(client: TestClient):
    """3. Assistant can query the same analysis without returning Analysis Not Found."""
    # Batch-level question in the context of the demo analysis
    payload = {
        "question": "What is the statutory PF contribution formula under Section 6 of EPFO Act 1952?",
        "analysis_id": DEMO_ANALYSIS_ID,
    }
    resp = client.post("/api/v1/assistant/query", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "not found" not in data["answer"].lower()
    assert len(data["citations"]) > 0
    assert any("EPFO" in c["document_id"] for c in data["citations"])


def test_4_assistant_can_query_specific_employee_in_analysis(client: TestClient):
    """4. Assistant can query a specific flagged employee in the demo analysis."""
    payload = {
        "question": "Why was this employee flagged for under-deduction?",
        "analysis_id": DEMO_ANALYSIS_ID,
        "employee_id": "EMP_2041",
    }
    resp = client.post("/api/v1/assistant/query", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["grounded_facts"]) > 0


def test_5_anomaly_endpoint_queries_same_analysis(client: TestClient):
    """5. Anomaly list and detail endpoints query the same analysis."""
    # List anomalies
    resp_list = client.get(f"/api/v1/anomalies/{DEMO_ANALYSIS_ID}")
    assert resp_list.status_code == 200
    anomalies = resp_list.json()
    assert len(anomalies) == 12

    # Query single employee detail
    resp_emp = client.get(f"/api/v1/anomalies/{DEMO_ANALYSIS_ID}/EMP_2041")
    assert resp_emp.status_code == 200
    emp = resp_emp.json()
    assert emp["employee_id"] == "EMP_2041"
    assert emp["compliance"]["status"] in ["FOUND", "SUCCESS"]
    assert len(emp["compliance"]["sources"]) > 0


def test_6_dashboard_and_anomaly_list_use_consistent_source_data(client: TestClient):
    """6. Dashboard summary metrics and anomaly table records have 100% matching count semantics."""
    resp = client.get(f"/api/v1/payroll/analysis/{DEMO_ANALYSIS_ID}")
    assert resp.status_code == 200
    data = resp.json()

    summary = data["summary"]
    anomalies = data["anomalies"]

    # Number of records in anomaly table matches records_flagged in summary
    assert len(anomalies) == summary["records_flagged"]
    assert summary["records_analyzed"] - summary["records_flagged"] == 238

    # All unique employee IDs in table are distinct
    emp_ids = [a["employee_id"] for a in anomalies]
    assert len(emp_ids) == len(set(emp_ids))


def test_7_missing_analysis_returns_controlled_404_error(client: TestClient):
    """7. Querying a nonexistent analysis returns a controlled structured 404 error."""
    # Test Assistant route
    resp_asst = client.post(
        "/api/v1/assistant/query",
        json={"question": "What happened?", "analysis_id": "anl_nonexistent_99999"},
    )
    assert resp_asst.status_code == 404
    data_asst = resp_asst.json()
    err_msg = data_asst.get("error", {}).get("message") or data_asst.get("detail", "")
    assert "Analysis 'anl_nonexistent_99999' not found." in err_msg

    # Test Payroll route
    resp_pay = client.get("/api/v1/payroll/analysis/anl_nonexistent_99999")
    assert resp_pay.status_code == 404

    # Test Anomalies route
    resp_anom = client.get("/api/v1/anomalies/anl_nonexistent_99999")
    assert resp_anom.status_code == 404


def test_8_llm_unavailable_fallback_still_works(client: TestClient, monkeypatch):
    """8. If LLM provider raises an exception, deterministic grounded fallback activates gracefully."""
    model_mgr = ModelManager.get_instance()

    # Invalidate LLM provider generate method
    def broken_generate(*args, **kwargs):
        raise RuntimeError("Cloud LLM network timeout or offline simulation")

    monkeypatch.setattr(model_mgr.llm_client.provider, "generate_structured", broken_generate)

    payload = {
        "question": "What is the policy regarding this employee?",
        "analysis_id": DEMO_ANALYSIS_ID,
        "employee_id": "EMP_2041",
    }
    resp = client.post("/api/v1/assistant/query", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "EMP_2041" in data["answer"]
    assert len(data["grounded_facts"]) > 0
    assert "fallback" in (data.get("uncertainty_or_refusal") or "").lower()
