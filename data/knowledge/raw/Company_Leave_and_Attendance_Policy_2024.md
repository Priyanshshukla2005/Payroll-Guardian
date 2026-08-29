# Enterprise Leave, Attendance & Loss of Pay (LOP) Policy

**Document ID**: `COMPANY_LEAVE_ATTENDANCE_POLICY_2024`  
**Issuing Authority**: Human Resources Department, Enterprise Operations  
**Authority Tier**: Tier 2 — Organizational Policy  
**Jurisdiction**: INDIA (All Enterprise Locations)  
**Topic**: LEAVE, WAGES  
**Effective Date**: 2024-01-01 to CURRENT  
**Document Version**: `v1.0`  

---

## Section 1: Standard Monthly Working Days and Attendance Bounds

### 1. Monthly Working Days Definition
- The standard payroll calculation month is configured based on **26 calendar working days** (excluding weekly off days).
- In any single calendar month, the sum of `present_days + leave_days` must strictly satisfy:
$$\text{present\_days} + \text{leave\_days} \le \text{working\_days}$$
- Recording `present_days > working_days` (e.g. 32 days present in a 26-day month) constitutes a mathematical impossibility and must be flagged immediately as `IMPOSSIBLE_ATTENDANCE`.

---

## Section 2: Salary Reconciliation & Loss of Pay (LOP) Deductions

### 1. Gross Salary Formula
Monthly gross salary must reconcile exactly to:
$$\text{gross\_salary} = \text{basic\_salary} + \text{allowances} + \text{overtime\_amount} + \text{bonus}$$
Any discrepancy where gross does not equal the arithmetic sum constitutes `RULE_GROSS_RECONCILIATION_FAIL`.

### 2. Net Take-Home Salary Formula
Net salary disbursed to employee bank accounts must reconcile to:
$$\text{net\_salary} = \text{gross\_salary} - \text{total\_deductions}$$
$$\text{total\_deductions} = \text{pf} + \text{esi} + \text{tds} + \text{other\_deductions}$$
Any arithmetic mismatch constitutes `ABNORMAL_NET_SALARY`.

### 3. Loss of Pay (LOP) Deduction Calculation
When an employee takes unauthorized unapproved leaves, per-day salary is deducted proportionally:
$$\text{Daily Wage Rate} = \frac{\text{Gross Monthly Salary}}{\text{Working Days (26)}}$$
$$\text{LOP Deduction} = \text{Unapproved Absent Days} \times \text{Daily Wage Rate}$$
