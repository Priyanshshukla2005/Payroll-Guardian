"""Deterministic Demo Analysis Generator & Repository Initializer (Phase 9 Integration).

Provides a canonical, realistic 250-record monthly payroll dataset with exactly
12 verified anomalies covering statutory compliance violations, arithmetic errors,
and machine learning behavioral deviations.
"""

from datetime import datetime
import logging
from typing import Any, Dict, List
import pandas as pd

from backend.dependencies.services import AnalysisRepository, ModelManager
from backend.schemas.analysis import AnalysisResponse
from backend.services.analysis_service import AnalysisService

logger = logging.getLogger("payroll_guardian.demo")

DEMO_ANALYSIS_ID = "anl_demo_202406"
DEMO_REQUEST_ID = "req_demo_enterprise_preview"
DEMO_PERIOD = "2024-06"


def create_demo_payroll_records() -> List[Dict[str, Any]]:
    """Create a deterministic list of 250 payroll records with 12 realistic anomalies."""
    records: List[Dict[str, Any]] = []

    # 1. Exactly 12 verified anomalous records
    anomalous_definitions = [
        # Anomaly 1: Critical Statutory PF Under-deduction
        {
            "employee_id": "EMP_2041",
            "payroll_month": DEMO_PERIOD,
            "department": "Operations",
            "designation": "Associate",
            "location": "Mumbai",
            "basic_salary": 40000.0,
            "allowances": 12000.0,
            "gross_salary": 52000.0,
            "pf_deduction": 1200.0,  # Statutory expected: 4800 (12%)
            "total_deductions": 1400.0,
            "net_salary": 50600.0,
            "working_days": 26,
            "present_days": 26,
            "overtime_hours": 0.0,
            "salary_change_percentage": 0.0,
        },
        # Anomaly 2: High Overtime Outlier + Salary Surge
        {
            "employee_id": "EMP_1088",
            "payroll_month": DEMO_PERIOD,
            "department": "Engineering",
            "designation": "Senior Engineer",
            "location": "Bengaluru",
            "basic_salary": 120000.0,
            "allowances": 25000.0,
            "gross_salary": 195000.0,
            "pf_deduction": 14400.0,
            "total_deductions": 14600.0,
            "net_salary": 180400.0,
            "working_days": 26,
            "present_days": 26,
            "overtime_hours": 65.0,  # Outlier hours & >60h rule
            "salary_change_percentage": 62.5,
        },
        # Anomaly 3: Impossible Attendance (Present > Working days)
        {
            "employee_id": "EMP_1015",
            "payroll_month": DEMO_PERIOD,
            "department": "Finance",
            "designation": "Lead",
            "location": "Delhi",
            "basic_salary": 90000.0,
            "allowances": 30000.0,
            "gross_salary": 120000.0,
            "pf_deduction": 10800.0,
            "total_deductions": 11000.0,
            "net_salary": 109000.0,
            "working_days": 26,
            "present_days": 31,  # Impossible attendance
            "overtime_hours": 0.0,
            "salary_change_percentage": 0.0,
        },
        # Anomaly 4: Ineligible ESI Deduction Above Ceiling
        {
            "employee_id": "EMP_1028",
            "payroll_month": DEMO_PERIOD,
            "department": "Sales",
            "designation": "Manager",
            "location": "Mumbai",
            "basic_salary": 60000.0,
            "allowances": 20000.0,
            "gross_salary": 80000.0,
            "pf_deduction": 7200.0,
            "esi_deduction": 600.0,  # Ineligible for ESI (gross > 21,000)
            "total_deductions": 8000.0,
            "net_salary": 72000.0,
            "working_days": 26,
            "present_days": 26,
            "overtime_hours": 0.0,
            "salary_change_percentage": 0.0,
        },
        # Anomaly 5: PF Calculation Mismatch
        {
            "employee_id": "EMP_1042",
            "payroll_month": DEMO_PERIOD,
            "department": "Marketing",
            "designation": "Executive",
            "location": "Mumbai",
            "basic_salary": 35000.0,
            "allowances": 10000.0,
            "gross_salary": 45000.0,
            "pf_deduction": 2000.0,  # Expected: 4200 (12%)
            "total_deductions": 2200.0,
            "net_salary": 42800.0,
            "working_days": 26,
            "present_days": 26,
            "overtime_hours": 0.0,
            "salary_change_percentage": 0.0,
        },
        # Anomaly 6: Net Reconciliation Failure (Net > Gross)
        {
            "employee_id": "EMP_1065",
            "payroll_month": DEMO_PERIOD,
            "department": "Operations",
            "designation": "Technician",
            "location": "Bengaluru",
            "basic_salary": 28000.0,
            "allowances": 8000.0,
            "gross_salary": 36000.0,
            "pf_deduction": 3360.0,
            "total_deductions": 3560.0,
            "net_salary": 38000.0,  # Reconciliation failure
            "working_days": 26,
            "present_days": 26,
            "overtime_hours": 0.0,
            "salary_change_percentage": 0.0,
        },
        # Anomaly 7: Out-of-Cycle Salary Spike (300% surge)
        {
            "employee_id": "EMP_1077",
            "payroll_month": DEMO_PERIOD,
            "department": "HR",
            "designation": "Specialist",
            "location": "Delhi",
            "basic_salary": 45000.0,
            "allowances": 15000.0,
            "gross_salary": 180000.0,
            "pf_deduction": 5400.0,
            "total_deductions": 5600.0,
            "net_salary": 174400.0,
            "working_days": 26,
            "present_days": 26,
            "overtime_hours": 0.0,
            "salary_change_percentage": 300.0,
        },
        # Anomaly 8: Net Arithmetic Discrepancy
        {
            "employee_id": "EMP_1093",
            "payroll_month": DEMO_PERIOD,
            "department": "Engineering",
            "designation": "Developer",
            "location": "Bengaluru",
            "basic_salary": 70000.0,
            "allowances": 20000.0,
            "gross_salary": 90000.0,
            "pf_deduction": 8400.0,
            "total_deductions": 12000.0,
            "net_salary": 70000.0,  # Expected: 78000 (discrepancy of 8000)
            "working_days": 26,
            "present_days": 26,
            "overtime_hours": 0.0,
            "salary_change_percentage": 0.0,
        },
        # Anomaly 9: Gross Earnings Under-computation
        {
            "employee_id": "EMP_1105",
            "payroll_month": DEMO_PERIOD,
            "department": "Support",
            "designation": "Agent",
            "location": "Delhi",
            "basic_salary": 22000.0,
            "allowances": 8000.0,
            "gross_salary": 18000.0,  # Gross mismatch vs basic+allowances
            "pf_deduction": 2640.0,
            "total_deductions": 2840.0,
            "net_salary": 15160.0,
            "working_days": 26,
            "present_days": 26,
            "overtime_hours": 0.0,
            "salary_change_percentage": 0.0,
        },
        # Anomaly 10: Excessive Overtime Cap Breach
        {
            "employee_id": "EMP_1118",
            "payroll_month": DEMO_PERIOD,
            "department": "Sales",
            "designation": "Representative",
            "location": "Mumbai",
            "basic_salary": 32000.0,
            "allowances": 10000.0,
            "gross_salary": 57500.0,
            "pf_deduction": 3840.0,
            "total_deductions": 4040.0,
            "net_salary": 53460.0,
            "working_days": 26,
            "present_days": 26,
            "overtime_hours": 68.0,  # Rule violation: Excessive Overtime
            "salary_change_percentage": 0.0,
        },
        # Anomaly 11: Missing Mandatory PF Deduction
        {
            "employee_id": "EMP_1130",
            "payroll_month": DEMO_PERIOD,
            "department": "Product",
            "designation": "Designer",
            "location": "Bengaluru",
            "basic_salary": 55000.0,
            "allowances": 15000.0,
            "gross_salary": 70000.0,
            "pf_deduction": 0.0,  # Expected: 6600 (PF missing)
            "total_deductions": 200.0,
            "net_salary": 69800.0,
            "working_days": 26,
            "present_days": 26,
            "overtime_hours": 0.0,
            "salary_change_percentage": 0.0,
        },
        # Anomaly 12: Compound Anomaly (Salary Surge + PF Deviation)
        {
            "employee_id": "EMP_1142",
            "payroll_month": DEMO_PERIOD,
            "department": "Legal",
            "designation": "Counsel",
            "location": "Mumbai",
            "basic_salary": 110000.0,
            "allowances": 40000.0,
            "gross_salary": 220000.0,
            "pf_deduction": 2500.0,  # Expected: 13200
            "total_deductions": 2700.0,
            "net_salary": 217300.0,
            "working_days": 26,
            "present_days": 26,
            "overtime_hours": 0.0,
            "salary_change_percentage": 200.0,
        },
    ]
    records.extend(anomalous_definitions)

    # 2. Exactly 238 clean, compliant records
    for i in range(1, 239):
        basic = 30000.0 + (i % 20) * 2500.0
        allow = 10000.0 + (i % 10) * 1000.0
        gross = basic + allow
        pf = round(basic * 0.12, 2)
        tot_ded = pf + 200.0  # PF + PT
        net = gross - tot_ded

        depts = ["Engineering", "Operations", "Sales", "Finance", "HR", "Marketing", "Legal", "Support"]
        desigs = ["Associate", "Specialist", "Senior", "Lead", "Manager"]
        locs = ["Bengaluru", "Mumbai", "Delhi", "Hyderabad", "Pune"]

        records.append({
            "employee_id": f"EMP_CLEAN_{i:04d}",
            "payroll_month": DEMO_PERIOD,
            "department": depts[i % len(depts)],
            "designation": desigs[i % len(desigs)],
            "location": locs[i % len(locs)],
            "basic_salary": basic,
            "allowances": allow,
            "gross_salary": gross,
            "pf_deduction": pf,
            "total_deductions": tot_ded,
            "net_salary": net,
            "working_days": 26,
            "present_days": 26,
            "overtime_hours": 0.0,
            "salary_change_percentage": 0.0,
        })

    return records


def ensure_demo_analysis(
    repo: AnalysisRepository,
    model_manager: ModelManager,
) -> AnalysisResponse:
    """Ensure the canonical demo analysis (anl_demo_202406) exists in the repository."""
    existing = repo.get_analysis(DEMO_ANALYSIS_ID)
    if existing is not None:
        return existing

    logger.info(f"Generating canonical deterministic demo analysis: {DEMO_ANALYSIS_ID}...")
    records = create_demo_payroll_records()
    df = pd.DataFrame(records)

    analysis_service = AnalysisService(
        model_manager=model_manager,
        repository=repo,
    )

    analysis = analysis_service.analyze_payroll(
        df_records=df,
        payroll_period=DEMO_PERIOD,
        jurisdiction="INDIA",
        request_id=DEMO_REQUEST_ID,
    )

    # Force the canonical analysis_id
    analysis.analysis_id = DEMO_ANALYSIS_ID
    repo.save_analysis(analysis)
    logger.info(
        f"Demo analysis '{DEMO_ANALYSIS_ID}' initialized successfully with "
        f"{analysis.summary.records_analyzed} records ({analysis.summary.records_flagged} flagged)."
    )
    return analysis
