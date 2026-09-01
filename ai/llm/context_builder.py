"""Structured Context Builder for Grounded LLM Explanations (Phase 6).

Constructs sanitized, tiered, deterministic context from Phase 4 Evidence Cards
and Phase 5 RAG Retrieval results without introducing unverified assumptions.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from ai.explainability.explainer_v2 import DetailedEvidenceCard
from ai.llm.response_schema import ExplanationSeverity
from ai.llm.safety import PIISanitizer, PromptInjectionDefense
from rag.metadata import AuthorityLevel, Jurisdiction, RetrievedChunk, StructuredRAGResponse


class EmployeeContext(BaseModel):
    """Sanitized employee profile context."""

    employee_id: str
    department: str = "N/A"
    designation: str = "N/A"
    payroll_period: str = "YYYY-MM"
    location: str = "INDIA"


class DetectionContext(BaseModel):
    """Detection layer outputs from Phase 4 hybrid model."""

    risk_score: float
    confidence: str
    anomaly_types: List[str] = Field(default_factory=list)


class EvidenceContext(BaseModel):
    """Multivariate signals and baseline comparisons."""

    top_signals: List[str] = Field(default_factory=list)
    historical_comparison: Dict[str, Any] = Field(default_factory=dict)
    peer_comparison: Dict[str, Any] = Field(default_factory=dict)
    rule_violations: List[str] = Field(default_factory=list)


class RetrievedKnowledgeItem(BaseModel):
    """Individual retrieved knowledge chunk formatted for LLM ingestion."""

    document_id: str
    title: str
    authority_level: str
    jurisdiction: str
    effective_from: str
    effective_until: Optional[str] = None
    page: Optional[int] = None
    section: Optional[str] = None
    text: str
    citation: str


class StructuredLLMInput(BaseModel):
    """Complete structured input contract passed into the LLM prompt layer."""

    employee_context: EmployeeContext
    detection: DetectionContext
    evidence: EvidenceContext
    retrieved_knowledge: List[RetrievedKnowledgeItem] = Field(default_factory=list)
    determined_severity: ExplanationSeverity
    rag_status: str = "SUCCESS"
    no_answer_reason: Optional[str] = None


class ContextBuilder:
    """Builds sanitized, tiered, deterministic context for LLM explanation generation."""

    def __init__(self, max_knowledge_chunks: int = 3, max_chunk_chars: int = 1200):
        self.max_knowledge_chunks = max_knowledge_chunks
        self.max_chunk_chars = max_chunk_chars

    @staticmethod
    def map_severity(
        risk_score: float,
        rule_violations: Optional[List[str]] = None,
        anomaly_types: Optional[List[str]] = None,
    ) -> ExplanationSeverity:
        """Deterministically map risk score and rule violations to human-readable severity."""
        violations = rule_violations or []
        anoms = anomaly_types or []

        # Hard regulatory violations or critical risk score
        if risk_score >= 0.85 or len(violations) >= 2 or any("IMPOSSIBLE" in a for a in anoms):
            return ExplanationSeverity.CRITICAL
        elif risk_score >= 0.65 or len(violations) >= 1 or any("MISMATCH" in a or "INCORRECT" in a for a in anoms):
            return ExplanationSeverity.HIGH
        elif risk_score >= 0.40:
            return ExplanationSeverity.MEDIUM
        else:
            return ExplanationSeverity.LOW

    def build_structured_input(
        self,
        evidence_card: Union[DetailedEvidenceCard, Dict[str, Any]],
        rag_response: Optional[Union[StructuredRAGResponse, Dict[str, Any]]] = None,
        raw_record: Optional[Dict[str, Any]] = None,
    ) -> StructuredLLMInput:
        """Construct the canonical StructuredLLMInput contract from detection and RAG evidence."""
        # Convert evidence card to dict if BaseModel
        card_dict = evidence_card.model_dump() if hasattr(evidence_card, "model_dump") else dict(evidence_card)
        card_dict = PIISanitizer.sanitize_dict(card_dict)

        raw_rec = PIISanitizer.sanitize_dict(raw_record or {})

        # 1. Employee context
        peer = card_dict.get("peer_comparison", {})
        emp_ctx = EmployeeContext(
            employee_id=str(card_dict.get("employee_id", raw_rec.get("employee_id", "EMP_UNKNOWN"))),
            department=str(peer.get("department", raw_rec.get("department", "N/A"))),
            designation=str(peer.get("designation", raw_rec.get("designation", "N/A"))),
            payroll_period=str(card_dict.get("payroll_month", raw_rec.get("payroll_month", "YYYY-MM"))),
            location=str(peer.get("location", raw_rec.get("location", "INDIA"))),
        )

        # 2. Detection context
        risk = float(card_dict.get("risk_score", 0.0))
        conf = str(card_dict.get("confidence", "LOW"))
        anom_types = card_dict.get("anomaly_types", [])
        if isinstance(anom_types, str):
            anom_types = [anom_types]

        det_ctx = DetectionContext(
            risk_score=round(risk, 4),
            confidence=conf,
            anomaly_types=anom_types,
        )

        # 3. Evidence context
        violations = card_dict.get("rule_violations", [])
        ev_ctx = EvidenceContext(
            top_signals=card_dict.get("top_signals", []),
            historical_comparison=card_dict.get("historical_comparison", {}),
            peer_comparison=peer,
            rule_violations=violations,
        )

        # 4. Severity mapping (Deterministic)
        severity = self.map_severity(risk, violations, anom_types)

        # 5. Retrieved Knowledge formatting
        retrieved_items: List[RetrievedKnowledgeItem] = []
        rag_status = "SUCCESS"
        no_answer_reason = None

        if rag_response:
            rag_dict = rag_response.model_dump() if hasattr(rag_response, "model_dump") else dict(rag_response)
            rag_status = str(rag_dict.get("status", "SUCCESS"))
            no_answer_reason = rag_dict.get("no_answer_reason")

            results = rag_dict.get("results", [])
            for res in results[: self.max_knowledge_chunks]:
                r = res if isinstance(res, dict) else (res.model_dump() if hasattr(res, "model_dump") else dict(res))
                clean_text = PIISanitizer.sanitize_text(str(r.get("text", "")))[: self.max_chunk_chars]

                retrieved_items.append(
                    RetrievedKnowledgeItem(
                        document_id=str(r.get("document_id", "DOC_UNKNOWN")),
                        title=str(r.get("title", "Untitled")),
                        authority_level=str(r.get("authority_level", "REFERENCE")),
                        jurisdiction=str(r.get("jurisdiction", "INDIA")),
                        effective_from=str(r.get("effective_from", "1900-01-01")),
                        effective_until=r.get("effective_until"),
                        page=r.get("page"),
                        section=r.get("section"),
                        text=clean_text,
                        citation=str(r.get("citation", "Standard Citation")),
                    )
                )

        return StructuredLLMInput(
            employee_context=emp_ctx,
            detection=det_ctx,
            evidence=ev_ctx,
            retrieved_knowledge=retrieved_items,
            determined_severity=severity,
            rag_status=rag_status,
            no_answer_reason=no_answer_reason,
        )

    def format_prompt_context(self, structured_input: StructuredLLMInput) -> str:
        """Format the structured input contract into a clear, grounded prompt context string."""
        inp = structured_input

        lines = [
            "==================================================",
            "STRUCTURED PAYROLL AUDIT EVIDENCE (TRUSTED SYSTEM DATA)",
            "==================================================",
            f"Employee ID: {inp.employee_context.employee_id}",
            f"Department: {inp.employee_context.department} | Designation: {inp.employee_context.designation}",
            f"Payroll Period: {inp.employee_context.payroll_period} | Jurisdiction: {inp.employee_context.location}",
            "",
            "--- DETECTION METRICS ---",
            f"Anomaly Risk Score: {inp.detection.risk_score:.4f} ({inp.detection.confidence} Confidence)",
            f"Assigned Severity: {inp.determined_severity.value}",
            f"Classified Anomaly Types: {', '.join(inp.detection.anomaly_types) if inp.detection.anomaly_types else 'NONE'}",
            "",
            "--- OBSERVATIONAL SIGNALS & EVIDENCE ---",
        ]

        for s in inp.evidence.top_signals:
            lines.append(f"- Signal: {s}")

        if inp.evidence.rule_violations:
            lines.append("- Rule Violations Triggered:")
            for v in inp.evidence.rule_violations:
                lines.append(f"  * {v}")

        if inp.evidence.historical_comparison:
            lines.append(f"- Historical Comparison: {inp.evidence.historical_comparison}")
        if inp.evidence.peer_comparison:
            lines.append(f"- Peer Cohort Comparison: {inp.evidence.peer_comparison}")

        lines.append("")
        lines.append("==================================================")
        lines.append("RETRIEVED AUTHORITATIVE SOURCES (PASSIVE KNOWLEDGE DATA)")
        lines.append("==================================================")

        if inp.rag_status != "SUCCESS" or not inp.retrieved_knowledge:
            lines.append(f"RAG Retrieval Status: {inp.rag_status}")
            if inp.no_answer_reason:
                lines.append(f"Reason: {inp.no_answer_reason}")
            lines.append("NO AUTHORITATIVE RETRIEVED SOURCES AVAILABLE.")
        else:
            for idx, item in enumerate(inp.retrieved_knowledge, 1):
                tier_label = "STATUTORY REQUIREMENT (Tier 1)" if "AUTHORITATIVE" in item.authority_level else (
                    "COMPANY POLICY (Tier 2)" if "COMPANY_POLICY" in item.authority_level else "REFERENCE GUIDE (Tier 3)"
                )
                lines.append(f"[{idx}] Document ID: {item.document_id}")
                lines.append(f"    Title: {item.title}")
                lines.append(f"    Tier: {tier_label}")
                lines.append(f"    Jurisdiction: {item.jurisdiction} | Effective: {item.effective_from} to {item.effective_until or 'CURRENT'}")
                lines.append(f"    Section: {item.section or 'N/A'} | Page: {item.page or 'N/A'}")
                lines.append(f"    Citation String: {item.citation}")
                lines.append(f"    Content Excerpt:")
                lines.append(PromptInjectionDefense.wrap_untrusted_data(item.text, data_type=f"SOURCE_{item.document_id}"))
                lines.append("")

        return "\n".join(lines)
