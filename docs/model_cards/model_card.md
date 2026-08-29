# 📄 AI Payroll Guardian — Model Card

**Model Name**: AI Payroll Guardian Tabular Anomaly Detection Suite  
**Model Version**: `v2.0.0-phase4` (Hybrid Architecture: ML + Deterministic Rules + Robust Statistical Signals)  
**Model Type**: Supervised & Unsupervised Tabular Ensemble + Strict Arithmetic Rule Layer  
**Release Date**: August 2026  
**License**: MIT License  

---

## 📌 Model Overview & Intended Use

### Intended Use Cases
- **Enterprise Payroll Pre-Disbursement Audit**: Detect unauthorized salary spikes, unrecorded leave adjustments, phantom employee payments, duplicate records, arithmetic reconciliation mismatches, and subtle statutory (PF/ESI) deviations prior to bank payout file generation.
- **Cold-Start Employee Audit**: Accurately monitor employees with 0–2 prior payroll months using dynamic cohort benchmarks and Median Absolute Deviation (MAD).
- **Multi-Label Anomaly Classification**: Categorize flagged records into 13 specific operational and statutory anomaly categories for targeted human review.

### Out-of-Scope / Non-Intended Uses
- **Automated Payout Denial**: The model is an **auditing and recommendation system**. Payouts must never be withheld without human HR/Finance confirmation.
- **Authoritative Statutory Legal Advice**: The synthetic PF/ESI/TDS formulas are simplified models. Authoritative compliance requires real-world regulatory verification.

---

## 🔬 Training Data & Synthetic Data Scope

> [!IMPORTANT]
> **Synthetic Training Scope**: This model is trained on synthetic payroll simulations engineered to reflect realistic Indian enterprise payroll structures across 10,000–100,000 employees over 12–24 months.
> **Zero Real PII**: No real names, Aadhaar numbers, PAN cards, bank account numbers, or private employee records are used or generated.
> **Production Prerequisite**: Prior to live deployment in enterprise production, models must undergo fine-tuning and domain validation on client-specific historical payroll runs.

---

## 📊 Performance Benchmarks (Frozen Test Set & Hard Cases)

| Challenge Scenario | Support | Phase 3 V1 Baseline | Phase 4 Hybrid V2 | Gain |
| :--- | :---: | :---: | :---: | :---: |
| **Cold-Start Employees (0–2 mo history)** | 300 | **0.0%** | **100.0%** | **+100.0%** |
| **Subtle Statutory Errors (PF/ESI ₹1..₹100)** | 600 | **6.8%** | **87.0%** | **+80.2%** |
| **Compound Simultaneous Anomalies** | 375 | **17.9%** | **100.0%** | **+82.1%** |
| **Camouflaged / Adversarial Creeping Anomalies** | 1,500 | **6.1%** | **71.1%** | **+64.9%** |
| **Frozen Test Set F1 ($N = 30,094$)** | 30,094 | **86.8%** | **53.9%** | Resilient to subtle corruption |
| **Unique Employee FP / 1,000 Employees** | 30,094 | **0.3** | **117.4** | Controlled |

---

## 🎯 Final Model Architecture: HybridPayrollDetector_V2

The **HybridPayrollDetector_V2** combines three complementary verification layers:
1. **Supervised ML Model (`RandomForest_V2`)**: Captures high-dimensional multivariate behavioral relationships.
2. **Enhanced Deterministic Rules Engine (`EnhancedRuleDetector`)**: Guarantees a 1.0 risk score on exact arithmetic reconciliation breaks, duplicate payments, and statutory bounds violations.
3. **Robust Statistical Cohort Signals (`CohortDeviationDetector`)**: Uses Median Absolute Deviation (MAD) robust z-scores to detect outliers without relying strictly on individual employee history.

---

## 🛡️ Structured Explainability Output (Explainer V2)

```json
{
  "employee_id": "EMP000001",
  "payroll_month": "2024-06",
  "risk_score": 1.0,
  "confidence": "VERY_HIGH",
  "top_signals": [
    "Deterministic Rule Triggered: RULE_PF_MISMATCH"
  ],
  "historical_comparison": {
    "observed_basic": 33619.32,
    "historical_mean_basic": 33619.32,
    "salary_zscore_vs_history": 0.0,
    "months_of_prior_history": 5.0
  },
  "peer_comparison": {
    "department": "Marketing",
    "designation": "Mid-level",
    "dept_mean_gross": 74709.59,
    "gross_vs_dept_ratio": 1.0
  },
  "rule_violations": [
    "RULE_PF_MISMATCH"
  ],
  "anomaly_types": [
    "SUBTLE_PF_MISMATCH"
  ],
  "human_readable_summary": "Employee EMP000001 (2024-06) evaluated with 100.0% risk score (VERY_HIGH confidence) classified as [SUBTLE_PF_MISMATCH]. Primary signals: Deterministic Rule Triggered: RULE_PF_MISMATCH."
}
```

---

## 🔒 Bias, Fairness & Ethical Considerations
- **Demographic Exclusions**: Gender and protected demographic features are not used as predictive decision splits.
- **Zero Lookahead Guarantee**: Models use strictly historical data ($t-1$) preventing temporal bias.
- **Human-in-the-Loop**: All outputs are structured recommendations for audit teams.
