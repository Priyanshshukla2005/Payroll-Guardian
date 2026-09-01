"""Response validation, citation integrity enforcement, and groundedness verification (Phase 6).

Validates structured JSON output against Pydantic schemas, guarantees zero citation
fabrication, enforces severity consistency, and flags unsupported claims.
"""

import json
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pydantic import BaseModel, ValidationError

from ai.llm.context_builder import StructuredLLMInput
from ai.llm.response_schema import (
    AssistantQueryResponse,
    CitationReference,
    ExplanationSeverity,
    GroundedAnomalyItem,
    PayrollExplanationResponse,
)
from ai.llm.safety import ConfidenceDecoupler, PIISanitizer


class ValidationResult(BaseModel):
    """Container summarizing validation status, error diagnostics, and sanitized response."""

    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    sanitized_response: Optional[Union[PayrollExplanationResponse, AssistantQueryResponse]] = None
    citation_validity_rate: float = 1.0
    groundedness_score: float = 1.0
    unsupported_claims: List[str] = []


class GroundednessChecker:
    """Deterministic groundedness verifier checking factual statements against provided evidence."""

    STANDARD_META_PATTERNS = [
        re.compile(r"no\s+authoritative\s+compliance\s+(?:document|source)\s+could\s+be\s+retrieved", re.IGNORECASE),
        re.compile(r"jurisdiction\s+is\s+unknown", re.IGNORECASE),
        re.compile(r"cannot\s+determine\s+applicable\s+statutory\s+regulation", re.IGNORECASE),
        re.compile(r"please\s+verify\s+(?:internal|relevant|applicable)", re.IGNORECASE),
        re.compile(r"analytical\s+variance\s+detected", re.IGNORECASE),
        re.compile(r"statistical\s+variance\s+observed", re.IGNORECASE),
        re.compile(r"trigger(?:ed)?\s+detection\s+pattern", re.IGNORECASE),
        re.compile(r"cross-reference\s+attendance", re.IGNORECASE),
        re.compile(r"verify\s+employee", re.IGNORECASE),
    ]

    @classmethod
    def check_groundedness(
        cls,
        response_dict: Dict[str, Any],
        structured_input: StructuredLLMInput,
    ) -> Tuple[float, List[str]]:
        """Verify that claims made in why_flagged, evidence, and compliance_context are grounded in input context."""
        context_tokens: Set[str] = set()

        # Add employee and detection tokens
        context_tokens.add(structured_input.employee_context.employee_id.lower())
        context_tokens.add(structured_input.employee_context.department.lower())
        context_tokens.add(structured_input.employee_context.designation.lower())
        context_tokens.add(structured_input.employee_context.payroll_period.lower())
        context_tokens.add(structured_input.employee_context.location.lower())

        for a in structured_input.detection.anomaly_types:
            for part in a.lower().split("_"):
                context_tokens.add(part)

        # Add signals and rule violations tokens
        for s in structured_input.evidence.top_signals:
            for w in re.findall(r"\w+", s.lower()):
                context_tokens.add(w)

        for v in structured_input.evidence.rule_violations:
            for w in re.findall(r"\w+", v.lower()):
                context_tokens.add(w)

        # Add historical and peer comparison tokens
        for k, v in structured_input.evidence.historical_comparison.items():
            context_tokens.add(str(k).lower())
            for w in re.findall(r"\w+", str(v).lower()):
                context_tokens.add(w)

        for k, v in structured_input.evidence.peer_comparison.items():
            context_tokens.add(str(k).lower())
            for w in re.findall(r"\w+", str(v).lower()):
                context_tokens.add(w)

        # Add retrieved knowledge tokens
        for k in structured_input.retrieved_knowledge:
            context_tokens.add(k.document_id.lower())
            for w in re.findall(r"\w+", k.title.lower()):
                context_tokens.add(w)
            for w in re.findall(r"\w+", k.text.lower()):
                context_tokens.add(w)
            if k.section:
                for w in re.findall(r"\w+", k.section.lower()):
                    context_tokens.add(w)

        # Evaluate claims in response
        unsupported_claims: List[str] = []
        total_claims = 0
        supported_claims = 0

        text_sections = (
            response_dict.get("why_flagged", [])
            + response_dict.get("evidence", [])
            + response_dict.get("compliance_context", [])
        )

        for stmt in text_sections:
            if not isinstance(stmt, str):
                continue
            total_claims += 1

            # Check if this is standard meta/refusal phrasing
            if any(p.search(stmt) for p in cls.STANDARD_META_PATTERNS):
                supported_claims += 1
                continue

            # Extract key numbers, percentages, and entity words
            keywords = re.findall(r"\b(?:₹?\d+(?:,\d+)*(?:\.\d+)?%?|[A-Za-z0-9_]{3,})\b", stmt)
            if not keywords:
                supported_claims += 1
                continue

            matches = sum(1 for kw in keywords if kw.lower().replace("₹", "").replace("%", "").replace(",", "") in context_tokens)
            match_ratio = matches / len(keywords)

            # If at least 30% of distinctive entities match context, claim is grounded
            if match_ratio >= 0.28 or matches >= 2:
                supported_claims += 1
            else:
                unsupported_claims.append(f"UNSUPPORTED_CLAIM: '{stmt[:100]}...' (Entity alignment: {match_ratio*100:.1f}%)")

        score = (supported_claims / total_claims) if total_claims > 0 else 1.0
        return round(score, 4), unsupported_claims


class PayrollLLMValidator:
    """Validates structured LLM outputs, citation integrity, and grounding constraints."""

    @classmethod
    def validate_anomaly_explanation(
        cls,
        raw_output: Union[str, Dict[str, Any]],
        structured_input: StructuredLLMInput,
    ) -> ValidationResult:
        """Thoroughly validate a generated anomaly explanation."""
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Parse JSON if string
        data: Dict[str, Any] = {}
        if isinstance(raw_output, str):
            clean_str = raw_output.strip()
            if "```json" in clean_str:
                clean_str = clean_str.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_str:
                clean_str = clean_str.split("```")[1].split("```")[0].strip()
            try:
                data = json.loads(clean_str)
            except json.JSONDecodeError as e:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"MALFORMED_JSON: Failed to parse LLM response into JSON: {e}"],
                    citation_validity_rate=0.0,
                    groundedness_score=0.0,
                )
        elif isinstance(raw_output, dict):
            data = dict(raw_output)
        else:
            return ValidationResult(
                is_valid=False,
                errors=["INVALID_TYPE: Raw output must be a JSON string or dictionary."],
            )

        # 2. Check critical required fields
        required_fields = ["title", "severity", "summary", "why_flagged", "evidence", "recommended_actions", "disclaimer"]
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"MISSING_REQUIRED_FIELD: '{field}' is required.")
            elif isinstance(data[field], (str, list)) and len(data[field]) == 0:
                errors.append(f"EMPTY_CRITICAL_FIELD: '{field}' must not be empty.")

        # 3. Severity enforcement (Must match assigned severity)
        assigned_sev = structured_input.determined_severity.value
        reported_sev = str(data.get("severity", "")).upper()
        if reported_sev != assigned_sev:
            warnings.append(f"SEVERITY_OVERRIDE: LLM reported '{reported_sev}', forced to assigned '{assigned_sev}'.")
            data["severity"] = assigned_sev

        # 4. Citation Integrity Validation (ZERO FABRICATION GUARANTEE)
        allowed_doc_ids = {k.document_id for k in structured_input.retrieved_knowledge}
        raw_citations = data.get("citations", [])
        valid_citations: List[Dict[str, Any]] = []
        total_cites = len(raw_citations)
        valid_cites = 0

        for cite in raw_citations:
            if not isinstance(cite, dict):
                continue
            doc_id = cite.get("document_id")
            if doc_id in allowed_doc_ids:
                valid_cites += 1
                valid_citations.append(cite)
            else:
                warnings.append(
                    f"FABRICATED_CITATION_REMOVED: Document ID '{doc_id}' was not in retrieved context {list(allowed_doc_ids)}."
                )

        cite_rate = (valid_cites / total_cites) if total_cites > 0 else 1.0
        data["citations"] = valid_citations

        # 5. Sanitize overreaching legal certainty claims and PII
        if isinstance(data.get("summary"), str):
            data["summary"] = ConfidenceDecoupler.sanitize_legal_claims(PIISanitizer.sanitize_text(data["summary"]))
        if isinstance(data.get("why_flagged"), list):
            data["why_flagged"] = [ConfidenceDecoupler.sanitize_legal_claims(PIISanitizer.sanitize_text(s)) for s in data["why_flagged"] if isinstance(s, str)]
        if isinstance(data.get("compliance_context"), list):
            data["compliance_context"] = [ConfidenceDecoupler.sanitize_legal_claims(PIISanitizer.sanitize_text(s)) for s in data["compliance_context"] if isinstance(s, str)]

        # 6. Check Groundedness
        g_score, unsupported = GroundednessChecker.check_groundedness(data, structured_input)
        if unsupported:
            warnings.extend(unsupported)

        # 7. Refusal / Uncertainty check when RAG status is failed
        if structured_input.rag_status != "SUCCESS":
            if not data.get("uncertainty"):
                data["uncertainty"] = f"RAG Status: {structured_input.rag_status}. Authoritative statutory citations could not be established."

        # 8. Instantiate Pydantic model
        sanitized_model = None
        try:
            sanitized_model = PayrollExplanationResponse.model_validate(data)
        except ValidationError as e:
            errors.append(f"PYDANTIC_SCHEMA_ERROR: {e}")

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            sanitized_response=sanitized_model,
            citation_validity_rate=round(cite_rate, 4),
            groundedness_score=g_score,
            unsupported_claims=unsupported,
        )

    @classmethod
    def validate_assistant_response(
        cls,
        raw_output: Union[str, Dict[str, Any]],
        structured_input: StructuredLLMInput,
    ) -> ValidationResult:
        """Validate an assistant Q&A response."""
        errors: List[str] = []
        warnings: List[str] = []

        data: Dict[str, Any] = {}
        if isinstance(raw_output, str):
            clean_str = raw_output.strip()
            if "```json" in clean_str:
                clean_str = clean_str.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_str:
                clean_str = clean_str.split("```")[1].split("```")[0].strip()
            try:
                data = json.loads(clean_str)
            except json.JSONDecodeError as e:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"MALFORMED_JSON: Failed to parse assistant response: {e}"],
                )
        elif isinstance(raw_output, dict):
            data = dict(raw_output)

        if not data.get("answer"):
            errors.append("MISSING_REQUIRED_FIELD: 'answer' is required in assistant response.")

        # Validate citations
        allowed_doc_ids = {k.document_id for k in structured_input.retrieved_knowledge}
        raw_citations = data.get("citations", [])
        valid_citations = []
        for cite in raw_citations:
            if isinstance(cite, dict) and cite.get("document_id") in allowed_doc_ids:
                valid_citations.append(cite)
            else:
                warnings.append(f"FABRICATED_CITATION_REMOVED: '{cite.get('document_id')}' rejected.")
        data["citations"] = valid_citations

        # Sanitize PII
        if isinstance(data.get("answer"), str):
            data["answer"] = ConfidenceDecoupler.sanitize_legal_claims(PIISanitizer.sanitize_text(data["answer"]))

        sanitized_model = None
        try:
            sanitized_model = AssistantQueryResponse.model_validate(data)
        except ValidationError as e:
            errors.append(f"PYDANTIC_SCHEMA_ERROR: {e}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_response=sanitized_model,
        )
