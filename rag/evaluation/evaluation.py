"""RAG evaluation suite and benchmark engine for AI Payroll Guardian (Phase 5).

Evaluates Recall@K, MRR, Authority Accuracy, Jurisdiction Accuracy,
Date Applicability Accuracy, and negative constraint enforcement.
"""

from typing import Any, Dict, List, Optional
import numpy as np
from pydantic import BaseModel, Field

from rag.metadata import AuthorityLevel, Jurisdiction, Topic
from rag.retrieval.retriever import PayrollRAGRetriever


class RAGEvalQuery(BaseModel):
    """Ground truth query specification for RAG evaluation."""

    query: str
    target_jurisdiction: Jurisdiction
    target_payroll_date: str  # YYYY-MM-DD
    target_topic: Optional[Topic] = None
    expected_document_id: str
    expected_authority: AuthorityLevel
    is_negative_test: bool = False
    unacceptable_document_id: Optional[str] = None
    description: str


class RAGEvaluationReport(BaseModel):
    """Summary report containing RAG retrieval benchmarks."""

    total_queries: int
    recall_at_1: float
    recall_at_3: float
    recall_at_5: float
    mrr: float
    authority_accuracy: float
    jurisdiction_accuracy: float
    date_applicability_accuracy: float
    negative_test_pass_rate: float
    query_details: List[Dict[str, Any]] = Field(default_factory=list)


def get_default_eval_dataset() -> List[RAGEvalQuery]:
    """Curated ground-truth test queries spanning positive, negative, date, and jurisdiction challenges."""
    return [
        # 1. Statutory PF Contribution Query (India)
        RAGEvalQuery(
            query="statutory 12 percent basic salary employee provident fund contribution rate",
            target_jurisdiction=Jurisdiction.INDIA,
            target_payroll_date="2024-06-01",
            target_topic=Topic.PF,
            expected_document_id="EPFO_ACT_1952",
            expected_authority=AuthorityLevel.AUTHORITATIVE,
            description="Authoritative PF contribution rate in India",
        ),
        # 2. ESIC Wage Ceiling and Exemption Threshold
        RAGEvalQuery(
            query="ESI wage ceiling threshold 21000 eligibility and 0.75 percent contribution rate",
            target_jurisdiction=Jurisdiction.INDIA,
            target_payroll_date="2024-06-01",
            target_topic=Topic.ESI,
            expected_document_id="ESIC_ACT_1948",
            expected_authority=AuthorityLevel.AUTHORITATIVE,
            description="ESIC wage ceiling and contribution rates",
        ),
        # 3. Income Tax Salary TDS Deduction
        RAGEvalQuery(
            query="Section 192 employer obligation to deduct monthly TDS on estimated annual salary",
            target_jurisdiction=Jurisdiction.INDIA,
            target_payroll_date="2024-06-01",
            target_topic=Topic.TDS,
            expected_document_id="INCOME_TAX_SEC_192",
            expected_authority=AuthorityLevel.AUTHORITATIVE,
            description="Income Tax Section 192 TDS rules",
        ),
        # 4. Maharashtra Professional Tax Slabs & Feb Surcharge
        RAGEvalQuery(
            query="Maharashtra state professional tax 200 per month and 300 rupees in February",
            target_jurisdiction=Jurisdiction.MAHARASHTRA,
            target_payroll_date="2024-02-01",
            target_topic=Topic.PROFESSIONAL_TAX,
            expected_document_id="MAHARASHTRA_PT_ACT_1975",
            expected_authority=AuthorityLevel.AUTHORITATIVE,
            description="Maharashtra Professional Tax February surcharge",
        ),
        # 5. Karnataka Professional Tax Exemption Threshold
        RAGEvalQuery(
            query="Karnataka professional tax 200 rupees exemption for salary under 15000",
            target_jurisdiction=Jurisdiction.KARNATAKA,
            target_payroll_date="2024-06-01",
            target_topic=Topic.PROFESSIONAL_TAX,
            expected_document_id="KARNATAKA_PT_ACT_1976",
            expected_authority=AuthorityLevel.AUTHORITATIVE,
            description="Karnataka Professional Tax 15k threshold",
        ),
        # 6. Company Overtime 1.5x Rate and Cap Policy
        RAGEvalQuery(
            query="Company overtime compensation hourly basic rate 1.5x monthly 40 hour limit",
            target_jurisdiction=Jurisdiction.INDIA,
            target_payroll_date="2024-06-01",
            target_topic=Topic.OVERTIME,
            expected_document_id="COMPANY_OVERTIME_BONUS_POLICY_2024",
            expected_authority=AuthorityLevel.COMPANY_POLICY,
            description="Company Overtime Policy (Tier 2)",
        ),
        # 7. Company Working Days and Loss of Pay LOP Rule
        RAGEvalQuery(
            query="26 working days attendance reconciliation and loss of pay LOP salary deduction formula",
            target_jurisdiction=Jurisdiction.INDIA,
            target_payroll_date="2024-06-01",
            target_topic=Topic.LEAVE,
            expected_document_id="COMPANY_LEAVE_ATTENDANCE_POLICY_2024",
            expected_authority=AuthorityLevel.COMPANY_POLICY,
            description="Company Leave and LOP Policy",
        ),
        # 8. Negative Test: Maharashtra Query should NEVER return Karnataka PT as authoritative
        RAGEvalQuery(
            query="Professional Tax deduction rules for Mumbai office employees",
            target_jurisdiction=Jurisdiction.MAHARASHTRA,
            target_payroll_date="2024-06-01",
            target_topic=Topic.PROFESSIONAL_TAX,
            expected_document_id="MAHARASHTRA_PT_ACT_1975",
            expected_authority=AuthorityLevel.AUTHORITATIVE,
            is_negative_test=True,
            unacceptable_document_id="KARNATAKA_PT_ACT_1976",
            description="Negative Jurisdiction Test: Maharashtra query must not retrieve Karnataka PT",
        ),
        # 9. Negative Test: 2024 Payroll Query should NOT retrieve historical expired 2014 notification
        RAGEvalQuery(
            query="Current PF wage ceiling rules for 2024 payroll disbursement",
            target_jurisdiction=Jurisdiction.INDIA,
            target_payroll_date="2024-06-01",
            target_topic=Topic.PF,
            expected_document_id="EPFO_ACT_1952",
            expected_authority=AuthorityLevel.AUTHORITATIVE,
            is_negative_test=True,
            unacceptable_document_id="EPFO_HISTORICAL_NOTIFICATION_2014",
            description="Negative Date Test: 2024 query must not retrieve expired historical 2014 document",
        ),
    ]


class RAGEvaluator:
    """Evaluates RAG retriever accuracy and negative constraint compliance."""

    def __init__(self, retriever: PayrollRAGRetriever):
        self.retriever = retriever

    def evaluate(self, test_queries: Optional[List[RAGEvalQuery]] = None) -> RAGEvaluationReport:
        """Run evaluation benchmark across all test queries."""
        queries = test_queries or get_default_eval_dataset()

        r_at_1 = []
        r_at_3 = []
        r_at_5 = []
        rr_list = []
        auth_acc = []
        jur_acc = []
        date_acc = []
        neg_pass = []

        details = []

        for q in queries:
            resp = self.retriever.retrieve(
                query=q.query,
                jurisdiction=q.target_jurisdiction,
                payroll_date=q.target_payroll_date,
                topic=q.target_topic,
                top_k=5,
                top_n=5,
            )

            retrieved_doc_ids = [r.document_id for r in resp.results]

            # Compute Recall@K
            hit_1 = 1.0 if (len(retrieved_doc_ids) > 0 and retrieved_doc_ids[0] == q.expected_document_id) else 0.0
            hit_3 = 1.0 if q.expected_document_id in retrieved_doc_ids[:3] else 0.0
            hit_5 = 1.0 if q.expected_document_id in retrieved_doc_ids[:5] else 0.0

            r_at_1.append(hit_1)
            r_at_3.append(hit_3)
            r_at_5.append(hit_5)

            # Reciprocal Rank
            if q.expected_document_id in retrieved_doc_ids:
                rank = retrieved_doc_ids.index(q.expected_document_id) + 1
                rr_list.append(1.0 / rank)
            else:
                rr_list.append(0.0)

            # Check Top-1 Authority, Jurisdiction, and Date correctness
            if resp.results:
                top_1 = resp.results[0]
                auth_ok = 1.0 if top_1.authority_level == q.expected_authority else 0.0
                jur_ok = 1.0 if top_1.jurisdiction in (q.target_jurisdiction, Jurisdiction.ALL, Jurisdiction.INDIA) else 0.0
                # Date applicability
                d_ok = 1.0 if (q.target_payroll_date >= top_1.effective_from and (top_1.effective_until is None or q.target_payroll_date <= top_1.effective_until)) else 0.0
            else:
                auth_ok, jur_ok, d_ok = 0.0, 0.0, 0.0

            auth_acc.append(auth_ok)
            jur_acc.append(jur_ok)
            date_acc.append(d_ok)

            # Negative test check
            if q.is_negative_test and q.unacceptable_document_id:
                neg_ok = 1.0 if q.unacceptable_document_id not in retrieved_doc_ids[:3] else 0.0
                neg_pass.append(neg_ok)

            details.append({
                "query": q.query,
                "expected": q.expected_document_id,
                "retrieved": retrieved_doc_ids,
                "hit_at_1": bool(hit_1),
                "hit_at_3": bool(hit_3),
                "top_1_score": resp.results[0].rerank_score if resp.results else 0.0,
            })

        report = RAGEvaluationReport(
            total_queries=len(queries),
            recall_at_1=round(float(np.mean(r_at_1)), 4),
            recall_at_3=round(float(np.mean(r_at_3)), 4),
            recall_at_5=round(float(np.mean(r_at_5)), 4),
            mrr=round(float(np.mean(rr_list)), 4),
            authority_accuracy=round(float(np.mean(auth_acc)), 4),
            jurisdiction_accuracy=round(float(np.mean(jur_acc)), 4),
            date_applicability_accuracy=round(float(np.mean(date_acc)), 4),
            negative_test_pass_rate=round(float(np.mean(neg_pass)) if neg_pass else 1.0, 4),
            query_details=details,
        )

        return report
