# AI Payroll Guardian — API Request & Response Examples (Phase 7)

This document provides sample cURL commands and JSON payloads for all API endpoints exposed by AI Payroll Guardian.

---

## 1. Analyze JSON Payroll Batch

### Request
```bash
curl -X POST "http://localhost:8000/api/v1/payroll/analyze" \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: req_audit_batch_001" \
  -d '{
    "payroll_period": "2024-06",
    "jurisdiction": "INDIA",
    "records": [
      {
        "employee_id": "EMP_1001",
        "payroll_month": "2024-06",
        "basic_salary": 50000.0,
        "gross_salary": 75000.0,
        "net_salary": 68800.0,
        "allowances": 25000.0,
        "bonus": 0.0,
        "total_deductions": 6200.0,
        "pf_deduction": 6000.0,
        "esi": 0.0,
        "professional_tax": 200.0,
        "working_days": 26,
        "present_days": 26,
        "leave_days": 0,
        "overtime_hours": 0.0,
        "department": "Engineering",
        "designation": "Senior",
        "location": "KARNATAKA"
      },
      {
        "employee_id": "EMP_1002",
        "payroll_month": "2024-06",
        "basic_salary": 40000.0,
        "gross_salary": 60000.0,
        "net_salary": 58600.0,
        "allowances": 20000.0,
        "bonus": 0.0,
        "total_deductions": 1400.0,
        "pf_deduction": 1200.0,
        "esi": 0.0,
        "professional_tax": 200.0,
        "working_days": 26,
        "present_days": 26,
        "leave_days": 0,
        "overtime_hours": 0.0,
        "department": "Operations",
        "designation": "Associate",
        "location": "MAHARASHTRA"
      }
    ]
  }'
```

### Response (`HTTP 200 OK`)
```json
{
  "request_id": "req_audit_batch_001",
  "analysis_id": "anl_34b7fa6829e",
  "status": "COMPLETED",
  "payroll_period": "2024-06",
  "summary": {
    "records_analyzed": 2,
    "records_flagged": 1,
    "critical_risk": 0,
    "high_risk": 1,
    "medium_risk": 0,
    "low_risk": 1
  },
  "anomalies": [
    {
      "employee_id": "EMP_1002",
      "payroll_month": "2024-06",
      "department": "Operations",
      "designation": "Associate",
      "anomaly_types": [
        "INCORRECT_PF"
      ],
      "risk_score": 0.94,
      "severity": "HIGH",
      "evidence": [
        "Deduction-to-Gross ratio deviated significantly (observed: 0.0233 vs cohort expected: 0.0933)"
      ],
      "rule_violations": [
        "RULE_PF_MISMATCH"
      ],
      "historical_comparison": {},
      "peer_comparison": {},
      "compliance": {
        "status": "FOUND",
        "sources": [
          {
            "document_id": "EPFO_ACT_1952",
            "title": "Employees' Provident Funds and Miscellaneous Provisions Act, 1952",
            "authority_level": "STATUTORY_ACT",
            "section": "Section 6",
            "page": 12,
            "citation": "[EPFO_ACT_1952, Section 6, p.12]"
          }
        ],
        "no_answer_reason": null
      },
      "explanation": {
        "title": "Severe Provident Fund Under-Deduction Detected",
        "summary": "Employee EMP_1002 had a PF deduction of INR 1,200 (3.0% of basic pay INR 40,000), violating the mandatory 12.0% statutory rate.",
        "why_flagged": [
          "Provident fund deduction (INR 1,200) is substantially lower than statutory 12% (INR 4,800)."
        ],
        "recommended_actions": [
          "Reconcile employee PF contribution against statutory EPFO 12% slab."
        ],
        "uncertainty": null,
        "fallback_mode": false
      }
    }
  ],
  "model_version": "HybridPayrollDetector_V2",
  "disclaimer": "AI-assisted payroll analysis. Not legal advice.",
  "duration_ms": 284.5
}
```

---

## 2. Upload Payroll CSV File

### Request
```bash
curl -X POST "http://localhost:8000/api/v1/payroll/upload" \
  -F "file=@june_2024_payroll.csv;type=text/csv" \
  -F "payroll_period=2024-06" \
  -F "jurisdiction=INDIA"
```

### Response (`HTTP 200 OK`)
Returns the standard `AnalysisResponse` JSON object with aggregated summary and detected anomalies.

---

## 3. Retrieve Analysis by ID

### Request
```bash
curl -X GET "http://localhost:8000/api/v1/payroll/analysis/anl_34b7fa6829e"
```

### Response (`HTTP 200 OK`)
Returns the cached `AnalysisResponse` object for that analysis ID.

---

## 4. Search Compliance Knowledge Base

### Request
```bash
curl -X POST "http://localhost:8000/api/v1/compliance/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "EPFO statutory employee contribution 12 percent basic salary",
    "jurisdiction": "INDIA",
    "payroll_date": "2024-06-01",
    "topic": "PF",
    "top_n": 2
  }'
```

### Response (`HTTP 200 OK`)
```json
{
  "query": "EPFO statutory employee contribution 12 percent basic salary",
  "jurisdiction": "INDIA",
  "payroll_date": "2024-06-01",
  "topic": "PF",
  "results": [
    {
      "document_id": "EPFO_ACT_1952",
      "title": "Employees' Provident Funds and Miscellaneous Provisions Act, 1952",
      "authority_level": "STATUTORY_ACT",
      "section": "Section 6",
      "page": 12,
      "citation": "[EPFO_ACT_1952, Section 6, p.12]"
    }
  ],
  "total_found": 1,
  "status": "SUCCESS",
  "no_answer_reason": null
}
```

---

## 5. Ask Grounded AI Assistant

### Request
```bash
curl -X POST "http://localhost:8000/api/v1/assistant/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Why was EMP_1002 flagged and what actions should HR take?",
    "analysis_id": "anl_34b7fa6829e",
    "employee_id": "EMP_1002"
  }'
```

### Response (`HTTP 200 OK`)
```json
{
  "question": "Why was EMP_1002 flagged and what actions should HR take?",
  "answer": "Employee EMP_1002 was flagged due to an apparent PF deduction mismatch where only INR 1,200 was deducted instead of the required statutory 12% (INR 4,800) under Section 6 of the EPFO Act 1952.",
  "grounded_facts": [
    "Recorded PF deduction: INR 1,200",
    "Mandatory statutory PF rate: 12.0% of basic wage"
  ],
  "evidence_sources": [
    "HybridPayrollDetector_V2 Evidence Card",
    "EPFO_ACT_1952"
  ],
  "citations": [
    {
      "document_id": "EPFO_ACT_1952",
      "section": "Section 6",
      "page": 12,
      "citation": "[EPFO_ACT_1952, Section 6, p.12]"
    }
  ],
  "category_distinction": {
    "statutory_requirements": [
      "Mandatory 12% employee contribution under Section 6 of EPFO Act 1952"
    ],
    "analytical_observations": [
      "Deduction-to-Gross ratio lower than expected"
    ]
  },
  "suggested_next_steps": [
    "Review payroll register with finance department",
    "Adjust arrears in subsequent payroll run if required"
  ],
  "uncertainty_or_refusal": null,
  "disclaimer": "AI-assisted payroll analysis. Must be verified with official statutory regulations and internal policies."
}
```

---

## 6. Error Handling: Missing Compliance Source

### Request
```bash
curl -X POST "http://localhost:8000/api/v1/compliance/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "State municipal tax deductions in Unknown Country",
    "jurisdiction": "UNKNOWN",
    "payroll_date": "2024-06-01"
  }'
```

### Response (`HTTP 200 OK`)
```json
{
  "query": "State municipal tax deductions in Unknown Country",
  "jurisdiction": "UNKNOWN",
  "payroll_date": "2024-06-01",
  "topic": null,
  "results": [],
  "total_found": 0,
  "status": "JURISDICTION_UNKNOWN",
  "no_answer_reason": "The geographic jurisdiction 'UNKNOWN' is not supported in the authoritative knowledge corpus."
}
```

---

## 7. Error Handling: Security & Malformed Files

### Request (Uploading executable or invalid file)
```bash
curl -X POST "http://localhost:8000/api/v1/payroll/upload" \
  -F "file=@malicious_script.sh"
```

### Response (`HTTP 400 Bad Request`)
```json
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "Unsupported file extension '.sh'. Allowed extensions: ['.csv', '.json', '.parquet'].",
    "request_id": "req_88f9104b2c",
    "status_code": 400
  }
}
```
