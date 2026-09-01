"""Curated Hard Cases Dataset and Benchmark Suite for AI Payroll Guardian (Phase 10).

Includes both true anomaly violations and legitimate corporate edge cases (e.g. annual increments,
promotions) to measure Precision, Recall, and False Positive Rates.
"""

from typing import Any, Dict, List, Tuple
import pandas as pd


def get_curated_benchmark_cases() -> List[Dict[str, Any]]:
    """Return a list of curated ground-truth benchmark cases with expected labels and anomaly types."""
    return [
        # --- TRUE POSITIVE ANOMALIES ---
        {
            "record": {
                "employee_id": "HARD_CASE_PF_UNDERDEDUCTION",
                "payroll_month": "2024-06",
                "department": "Engineering",
                "designation": "Mid-level",
                "location": "Bengaluru",
                "basic_salary": 50000.0,
                "allowances": 20000.0,
                "gross_salary": 70000.0,
                "pf_deduction": 1200.0,  # Expected: 6000.0 (12%)
                "total_deductions": 1400.0,
                "net_salary": 68600.0,
                "working_days": 26,
                "present_days": 26,
                "overtime_hours": 0.0,
                "salary_change_percentage": 0.0,
            },
            "is_anomaly": True,
            "expected_types": ["INCORRECT_PF"],
            "severity": "CRITICAL",
            "description": "Statutory PF under-deduction (1,200 vs 6,000 INR required).",
        },
        {
            "record": {
                "employee_id": "HARD_CASE_ATTENDANCE_OVERFLOW",
                "payroll_month": "2024-06",
                "department": "Operations",
                "designation": "Junior",
                "location": "Mumbai",
                "basic_salary": 30000.0,
                "allowances": 10000.0,
                "gross_salary": 40000.0,
                "pf_deduction": 3600.0,
                "total_deductions": 3800.0,
                "net_salary": 36200.0,
                "working_days": 26,
                "present_days": 31,  # Impossible attendance
                "overtime_hours": 0.0,
                "salary_change_percentage": 0.0,
            },
            "is_anomaly": True,
            "expected_types": ["ATTENDANCE_MISMATCH"],
            "severity": "HIGH",
            "description": "Present days (31) exceed total monthly working days (26).",
        },
        {
            "record": {
                "employee_id": "HARD_CASE_OVERTIME_CAP_BREACH",
                "payroll_month": "2024-06",
                "department": "Support",
                "designation": "Associate",
                "location": "Delhi-NCR",
                "basic_salary": 25000.0,
                "allowances": 8000.0,
                "gross_salary": 45000.0,
                "pf_deduction": 3000.0,
                "total_deductions": 3200.0,
                "net_salary": 41800.0,
                "working_days": 26,
                "present_days": 26,
                "overtime_hours": 72.0,  # Breach >60h cap
                "salary_change_percentage": 0.0,
            },
            "is_anomaly": True,
            "expected_types": ["OVERTIME_OUTLIER"],
            "severity": "HIGH",
            "description": "Excessive overtime breach (72 hours vs 60-hour monthly limit).",
        },
        {
            "record": {
                "employee_id": "HARD_CASE_SALARY_SURGE_UNEXPLAINED",
                "payroll_month": "2024-06",
                "department": "Marketing",
                "designation": "Executive",
                "location": "Bengaluru",
                "basic_salary": 40000.0,
                "allowances": 15000.0,
                "gross_salary": 220000.0,  # 300% spike
                "pf_deduction": 4800.0,
                "total_deductions": 5000.0,
                "net_salary": 215000.0,
                "working_days": 26,
                "present_days": 26,
                "overtime_hours": 0.0,
                "salary_change_percentage": 300.0,
            },
            "is_anomaly": True,
            "expected_types": ["SALARY_SPIKE", "STATISTICAL_ANOMALY"],
            "severity": "CRITICAL",
            "description": "Sudden 300% out-of-cycle salary surge without title change.",
        },
        {
            "record": {
                "employee_id": "HARD_CASE_ARITHMETIC_MISMATCH",
                "payroll_month": "2024-06",
                "department": "Finance",
                "designation": "Analyst",
                "location": "Pune",
                "basic_salary": 60000.0,
                "allowances": 20000.0,
                "gross_salary": 80000.0,
                "pf_deduction": 7200.0,
                "total_deductions": 7400.0,
                "net_salary": 60000.0,  # Should be 72,600 (12,600 reconciliation failure)
                "working_days": 26,
                "present_days": 26,
                "overtime_hours": 0.0,
                "salary_change_percentage": 0.0,
            },
            "is_anomaly": True,
            "expected_types": ["RECONCILIATION_ERROR"],
            "severity": "HIGH",
            "description": "Net salary reconciliation mismatch (Net != Gross - Deductions).",
        },
        {
            "record": {
                "employee_id": "HARD_CASE_ESI_INELIGIBLE_DEDUCTION",
                "payroll_month": "2024-06",
                "department": "Sales",
                "designation": "Manager",
                "location": "Mumbai",
                "basic_salary": 70000.0,
                "allowances": 25000.0,
                "gross_salary": 95000.0,  # Gross > 21,000 threshold
                "pf_deduction": 8400.0,
                "esi_deduction": 712.5,  # Ineligible deduction
                "total_deductions": 9312.5,
                "net_salary": 85687.5,
                "working_days": 26,
                "present_days": 26,
                "overtime_hours": 0.0,
                "salary_change_percentage": 0.0,
            },
            "is_anomaly": True,
            "expected_types": ["INCORRECT_ESIC"],
            "severity": "MEDIUM",
            "description": "ESI contribution deducted for employee earning above statutory ceiling.",
        },
        # --- LEGITIMATE CASES (NEGATIVE CONTROLS / FALSE POSITIVE TESTS) ---
        {
            "record": {
                "employee_id": "LEGIT_CASE_STANDARD_EMPLOYEE",
                "payroll_month": "2024-06",
                "department": "Engineering",
                "designation": "Senior",
                "location": "Bengaluru",
                "basic_salary": 120000.0,
                "allowances": 40000.0,
                "gross_salary": 160000.0,
                "pf_deduction": 14400.0,  # Exactly 12%
                "total_deductions": 14600.0,  # PF + 200 PT
                "net_salary": 145400.0,  # Exactly 160,000 - 14,600
                "working_days": 26,
                "present_days": 26,
                "overtime_hours": 0.0,
                "salary_change_percentage": 0.0,
            },
            "is_anomaly": False,
            "expected_types": ["NONE"],
            "severity": "LOW",
            "description": "Standard clean senior engineer record adhering to all statutory guidelines.",
        },
        {
            "record": {
                "employee_id": "LEGIT_CASE_ANNUAL_INCREMENT",
                "payroll_month": "2024-06",
                "department": "HR",
                "designation": "Specialist",
                "location": "Delhi-NCR",
                "basic_salary": 55000.0,  # 10% raise from 50k
                "allowances": 18000.0,
                "gross_salary": 73000.0,
                "pf_deduction": 6600.0,  # Updated 12% of 55k
                "total_deductions": 6800.0,
                "net_salary": 66200.0,
                "working_days": 26,
                "present_days": 26,
                "overtime_hours": 0.0,
                "salary_change_percentage": 10.0,  # Legitimate annual hike
            },
            "is_anomaly": False,
            "expected_types": ["NONE"],
            "severity": "LOW",
            "description": "Legitimate annual appraisal increment (10% hike with proper statutory PF adjustments).",
        },
        {
            "record": {
                "employee_id": "LEGIT_CASE_PROMOTION",
                "payroll_month": "2024-06",
                "department": "Engineering",
                "designation": "Manager",  # Promoted from Senior
                "location": "Bengaluru",
                "basic_salary": 200000.0,  # 25% promotion raise
                "allowances": 60000.0,
                "gross_salary": 260000.0,
                "pf_deduction": 24000.0,  # 12% of 200k
                "total_deductions": 24200.0,
                "net_salary": 235800.0,
                "working_days": 26,
                "present_days": 26,
                "overtime_hours": 0.0,
                "salary_change_percentage": 25.0,  # Legitimate promotion hike
            },
            "is_anomaly": False,
            "expected_types": ["NONE"],
            "severity": "LOW",
            "description": "Legitimate promotion jump (Senior -> Manager, 25% bump with verified bands).",
        },
        {
            "record": {
                "employee_id": "LEGIT_CASE_ESI_ELIGIBLE_ENTRY_LEVEL",
                "payroll_month": "2024-06",
                "department": "Administration",
                "designation": "Intern",
                "location": "Pune",
                "basic_salary": 14000.0,
                "allowances": 4000.0,
                "gross_salary": 18000.0,  # Under 21,000 ceiling
                "pf_deduction": 1680.0,  # 12% of 14,000
                "esi_deduction": 135.0,  # 0.75% of 18,000
                "total_deductions": 2015.0,  # PF (1680) + ESI (135) + PT (200)
                "net_salary": 15985.0,
                "working_days": 26,
                "present_days": 26,
                "overtime_hours": 0.0,
                "salary_change_percentage": 0.0,
            },
            "is_anomaly": False,
            "expected_types": ["NONE"],
            "severity": "LOW",
            "description": "Valid entry-level intern within ESI ceiling with valid 0.75% statutory deduction.",
        },
    ]


def get_curated_benchmark_dataframe() -> Tuple[pd.DataFrame, List[bool]]:
    """Return DataFrame of curated cases and binary ground-truth anomaly labels."""
    cases = get_curated_benchmark_cases()
    records = [c["record"] for c in cases]
    labels = [c["is_anomaly"] for c in cases]
    return pd.DataFrame(records), labels
