# 📚 AI Payroll Guardian — RAG Knowledge System Architecture

**Document Version**: `v1.0.0-phase5`  
**Date**: August 2026  
**Status**: VALIDATED & GROUNDED  

---

## 1. 🏗️ High-Level System Architecture

The AI Payroll Guardian RAG Knowledge Layer provides the regulatory grounding and policy comprehension necessary to interpret detected payroll anomalies. It operates strictly downstream of the ML & deterministic detection layer:

```
                          PAYROLL DISBURSEMENT RUN
                                     ↓
                          HybridPayrollDetector_V2
                                     ↓
                         STRUCTURED EVIDENCE CARD
           (risk_score, confidence, rule_violations, anomaly_types)
                                     ↓
                           RAG RETRIEVAL ENGINE
                   (src/rag/retriever.py: PayrollRAGRetriever)
                                     ↓
                      ┌──────────────┼──────────────┐
                      ↓              ↓              ↓
                 Dense Vector   Lexical BM25    Hard Metadata
                  Similarity     Term Match       Filtering
                      ↓              ↓              ↓
                      └──────────────┼──────────────┘
                                     ↓
                         AUTHORITY-AWARE RERANKER
                    (Tier 1 Gov > Tier 2 Policy > Tier 3 Ref)
                                     ↓
                         TRACEABLE CITATION BADGES
                      [EPFO_ACT_1952, Section 6, v2.4]
                                     ↓
                    STRUCTURED COMPLIANCE EVIDENCE CHUNKS
                                     ↓
                      [PHASE 6 — LLM EXPLANATION LAYER]
```

---

## 2. 🏛️ Three-Tier Knowledge Source Taxonomy

| Authority Tier | Designation | Examples | Use Case & Constraints |
| :--- | :--- | :--- | :--- |
| **Tier 1** | **AUTHORITATIVE** | EPFO Act 1952, ESIC Act 1948, Income Tax Section 192, State PT Schedules | Legally binding statutory claims; strictly takes precedence over all other tiers. |
| **Tier 2** | **COMPANY_POLICY** | Enterprise Overtime Policy, Leave/LOP SOP, Annual Bonus Guidelines | Internal organizational rules (rates, approval caps, appraisal cycles). |
| **Tier 3** | **REFERENCE** | General HR software guides, educational payroll articles | Contextual assistance; never presented as authoritative law. |
| **Tier 4** | **UNVERIFIED** | Random blogs, unverified web snippets | Strictly banned from compliance claims (`UNVERIFIED` status). |

---

## 3. 📅 Date & Jurisdiction-Aware Filtering Rules

### 1. Date Applicability Guarantee
Every document maintains `effective_from` and `effective_until` timestamps.
- When querying for payroll period `2024-06-01`, a notification with `effective_until = "2023-12-31"` is **strictly excluded** from active search.
- Historical notifications are only retrieved when historical comparative context is requested.

### 2. Geographic Jurisdiction Isolation
Every document specifies legal jurisdiction (`INDIA`, `MAHARASHTRA`, `KARNATAKA`, `DELHI`, `UTTAR_PRADESH`).
- Queries with `jurisdiction = MAHARASHTRA` are isolated from Karnataka/UP state schedules.
- If `jurisdiction = UNKNOWN`, the retriever returns `status = "JURISDICTION_UNKNOWN"`, preventing misleading legal claims.

---

## 4. 🔗 Integration with Phase 4 Evidence Cards

The query builder translates structured evidence signals into targeted compliance queries:

```json
{
  "input_anomaly": ["SUBTLE_PF_MISMATCH"],
  "rule_violations": ["RULE_PF_MISMATCH"],
  "generated_query": "EPFO Provident Fund statutory 12 percent basic wage contribution ceiling calculation",
  "retrieved_citation": "[EPFO_ACT_1952, Section: 3. Statutory Wage Ceiling Threshold, Version: v2.4, Jurisdiction: INDIA, Effective: 1952-11-01 to CURRENT]"
}
```
