# Grounded LLM Explanation & Payroll AI Assistant Architecture (Phase 6)

## 1. Executive Summary & Objective

**AI Payroll Guardian Phase 6** introduces a strictly grounded, deterministic-first **Large Language Model (LLM) Explanation & Payroll AI Assistant Layer**.

> **Core System Objective**: Convert structured anomaly evidence cards (from Phase 4) and retrieved authoritative compliance knowledge chunks (from Phase 5) into clear, auditable, citation-backed natural-language explanations and interactive audit assistance for payroll administrators.

### Core Non-Negotiable System Boundaries:
- **The LLM is NOT an anomaly detector**: Anomaly detection and mathematical probability calibration are performed exclusively by Phase 4 supervised/unsupervised ML models and enhanced deterministic rules.
- **Zero Regulation/Citation Fabrication**: The LLM is strictly prohibited from inventing statutory clauses, section numbers, page numbers, or effective dates. All citations are constructed and validated deterministically from retrieved RAG documents.
- **Deterministic Severity Enforcement**: The LLM communicates severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) assigned by upstream detection signals and business logic; it cannot alter or invent severity ratings.
- **Non-Autonomous Actions**: The LLM suggests only cautious verification steps (e.g. cross-checking timesheets, verifying deduction bases). It is strictly barred from approving payroll, executing payouts, or modifying wages.
- **No Legal Advice**: All outputs carry clear disclaimers that findings are analytical audit flags, not legal determinations.

---

## 2. End-to-End System Flow

```
                      ┌────────────────────────┐
                      │     PAYROLL RECORD     │
                      └───────────┬────────────┘
                                  │
                      ┌───────────▼────────────┐
                      │  HYBRID AI DETECTOR    │ (Phase 4: ML + Rules + Stats)
                      └───────────┬────────────┘
                                  │
                      ┌───────────▼────────────┐
                      │ DETAILED EVIDENCE CARD │ (Signals, Baselines, Scores)
                      └───────────┬────────────┘
                                  │
                      ┌───────────▼────────────┐
                      │     RAG RETRIEVER      │ (Phase 5: Hybrid & Date/Jurisdiction)
                      └───────────┬────────────┘
                                  │
                      ┌───────────▼────────────┐
                      │   RETRIEVED SOURCES    │ (Authoritative Tier 1/2/3 Chunks)
                      └───────────┬────────────┘
                                  │
                      ┌───────────▼────────────┐
                      │   LLM CONTEXT BUILDER  │ ◄── PII Sanitizer &
                      │ (Structured Contract)  │     Severity Determination
                      └───────────┬────────────┘
                                  │
                      ┌───────────▼────────────┐
                      │  GROUNDED GENERATOR /  │ ◄── Prompt Injection Guard &
                      │      LLM PROVIDER      │     Low Temp (0.0) Execution
                      └───────────┬────────────┘
                                  │
                      ┌───────────▼────────────┐
                      │  RESPONSE VALIDATOR &  │ ◄── Citation Integrity &
                      │   GROUNDEDNESS CHECK   │     Pydantic Schema Check
                      └───────────┬────────────┘
                                  │ (Pass, 1-step Retry, or Fallback)
                      ┌───────────▼────────────┐
                      │ GROUNDED EXPLANATION / │
                      │   ASSISTANT RESPONSE   │
                      └────────────────────────┘
```

---

## 3. Module Hierarchy (`ai/llm/`)

```
ai/llm/
├── __init__.py               # Public API exports
├── client.py                 # Unified client facade (explain_evidence, explain_record, ask)
├── provider.py               # Provider abstraction (MockGrounded, OpenAI, Anthropic, Factory)
├── prompts.py                # Grounded prompt templates and injection defenses
├── context_builder.py        # StructuredLLMInput contract builder and context assembler
├── response_schema.py        # Pydantic schemas for explanations, citations, and assistant Q&A
├── grounded_generator.py     # End-to-end generator with retries and deterministic fallback
├── validator.py              # Schema validation, citation integrity, and groundedness verifier
├── safety.py                 # PII sanitization, prompt injection defense, refusal engine, decoupling
├── assistant.py              # Interactive grounded payroll administrator Q&A assistant
├── eval_dataset.py           # 15-case curated benchmark evaluation dataset
└── evaluator.py              # Quantitative evaluation harness & scorecard generator
```

---

## 4. Provider Abstraction & Model Configuration

The provider layer decouples model inference from business logic:
- `BaseLLMProvider` defines abstract methods `generate()` and `generate_structured()`.
- `MockGroundedLLMProvider` guarantees 100% offline, deterministic execution for test suites, CI/CD pipelines, and local development.
- `OpenAILLMProvider` supports any OpenAI-compatible endpoint (OpenAI, Azure, Groq, Ollama, vLLM, LocalAI) using standard library HTTP to avoid brittle runtime dependencies.
- `AnthropicLLMProvider` supports Claude 3/3.5 models via the Messages API.
- `ProviderFactory` resolves settings from `.env` or explicit `ProviderConfig`.

### Default Configuration:
- `temperature`: `0.0` (Strictly deterministic)
- `max_tokens`: `800` (Bounded context window)
- `timeout_seconds`: `30.0`
- `retry_count`: `2`

---

## 5. Structured Input & Output Contracts

### Input Contract (`StructuredLLMInput`):
```json
{
  "employee_context": {
    "employee_id": "EMP0001251",
    "department": "Engineering",
    "designation": "Software Engineer",
    "payroll_period": "2024-06",
    "location": "MAHARASHTRA"
  },
  "detection": {
    "risk_score": 0.94,
    "confidence": "VERY_HIGH",
    "anomaly_types": ["INCORRECT_PF"]
  },
  "evidence": {
    "top_signals": ["PF deduction recorded as ₹2,100.00 but expected 12% of basic ₹35,000.00 is ₹4,200.00"],
    "historical_comparison": {"observed_basic": 35000.0, "historical_mean_basic": 35000.0},
    "peer_comparison": {"department": "Operations", "dept_mean_gross": 42000.0},
    "rule_violations": ["RULE_PF_MISMATCH"]
  },
  "retrieved_knowledge": [
    {
      "document_id": "EPFO_ACT_1952",
      "title": "Employees' Provident Funds and Miscellaneous Provisions Act, 1952",
      "authority_level": "AUTHORITATIVE",
      "jurisdiction": "INDIA",
      "effective_from": "1952-11-01",
      "effective_until": null,
      "page": 1,
      "section": "Section 6",
      "text": "The contribution paid by employer to PF shall be 12% of basic wages.",
      "citation": "EPFO Act, 1952, Section 6"
    }
  ],
  "determined_severity": "CRITICAL"
}
```

### Output Schema (`PayrollExplanationResponse`):
```json
{
  "title": "Payroll anomaly detected: INCORRECT_PF",
  "severity": "CRITICAL",
  "summary": "Employee EMP0001251 was evaluated with assigned severity [CRITICAL] due to statutory PF calculation mismatch.",
  "why_flagged": [
    "Triggered detection pattern for INCORRECT_PF based on recorded payroll inputs.",
    "Deterministic Rule Triggered: RULE_PF_MISMATCH"
  ],
  "evidence": [
    "PF deduction recorded as ₹2,100.00 but expected 12% of basic ₹35,000.00 is ₹4,200.00"
  ],
  "compliance_context": [
    "Employees' Provident Funds Act, 1952 (STATUTORY REQUIREMENT): Section 6 dictates mandatory 12% contribution."
  ],
  "recommended_actions": [
    "Verify employee's statutory basic salary wage basis and 12% EPFO deduction calculation."
  ],
  "citations": [
    {
      "document_id": "EPFO_ACT_1952",
      "page": 1,
      "section": "Section 6",
      "citation": "EPFO Act, 1952, Section 6"
    }
  ],
  "anomaly_breakdowns": [
    {
      "anomaly_type": "INCORRECT_PF",
      "severity": "CRITICAL",
      "description": "Record flagged for Incorrect Pf.",
      "evidence_points": ["PF deduction recorded as ₹2,100.00 vs expected ₹4,200.00"],
      "applicable_rule_or_policy": "EPFO Act, 1952, Section 6"
    }
  ],
  "uncertainty": null,
  "disclaimer": "AI-assisted payroll analysis. Not legal advice. Must be verified with official statutory regulations and internal policies."
}
```

---

## 6. Safety, Privacy & Security Defenses

1. **PII Sanitization Layer (`PIISanitizer`)**:
   - Strips bank account numbers, passwords, auth tokens, PAN numbers, Aadhaar numbers, email addresses, and phone numbers before context formatting.
2. **Prompt Injection Defense (`PromptInjectionDefense`)**:
   - Detects instruction overrides ("Ignore previous instructions", "SYSTEM PROMPT OVERRIDE").
   - Encapsulates retrieved document chunks inside defensive XML `<SOURCE_*_DATA>` boundaries with explicit passive data directives.
3. **Refusal Engine (`RefusalEngine`)**:
   - Implements explicit refusal text for `NO_RELIABLE_SOURCE_FOUND` and `JURISDICTION_UNKNOWN`.
   - Attaches historical validity caveats to superseded regulations.
4. **Confidence Decoupling (`ConfidenceDecoupler`)**:
   - Enforces distinct representation between ML anomaly probability (`risk_score`), RAG retrieval similarity, and statutory applicability. Prohibits overreaching legal certainty claims.
5. **Zero-Fabrication Citation Integrity**:
   - `PayrollLLMValidator` verifies all cited document IDs against retrieved chunks. Fabricated IDs are stripped immediately.

---

## 7. Deterministic Fallback Mode

If the external LLM provider experiences network outages, rate limits, or validation errors exceeding retry limits, `GroundedExplanationGenerator.generate_fallback_explanation()` produces a fully structured, auditable explanation directly from the evidence card and RAG results without crashing.
