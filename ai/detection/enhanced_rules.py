"""Enhanced deterministic rule engine for AI Payroll Guardian (Phase 4).

Performs strict arithmetic reconciliation, fine-grained statutory tolerance checks,
and attendance constraint validation.
"""

from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


class EnhancedRuleDetector:
    """Enhanced deterministic rule engine with fine-grained statutory and arithmetic validation."""

    def __init__(
        self,
        pf_tolerance: float = 0.50,
        esi_tolerance: float = 0.50,
        reconciliation_tolerance: float = 0.50,
    ):
        self.pf_tolerance = pf_tolerance
        self.esi_tolerance = esi_tolerance
        self.reconciliation_tolerance = reconciliation_tolerance

    def evaluate_rules(self, df: pd.DataFrame) -> pd.DataFrame:
        """Evaluate deterministic rules returning a boolean flag DataFrame."""
        flags = pd.DataFrame(index=df.index)

        # Helper to safely extract numeric series
        def _get_num(col: str) -> pd.Series:
            if col in df.columns:
                return pd.to_numeric(df[col], errors="coerce").fillna(0.0)
            return pd.Series(0.0, index=df.index)

        basic_sal = _get_num("basic_salary")
        gross_sal = _get_num("gross_salary")
        net_sal = _get_num("net_salary")
        allowances = _get_num("allowances")
        ot_amt = _get_num("overtime_amount")
        bon = _get_num("bonus")
        pf = _get_num("pf")
        esi = _get_num("esi")
        tot_ded = _get_num("total_deductions")
        other_ded = _get_num("other_deductions")
        ot_hours = _get_num("overtime_hours")
        pres_days = _get_num("present_days")
        work_days = _get_num("working_days")
        leave_days = _get_num("leave_days")

        # 1. Exact PF Calculation Check
        if "pf" in df.columns and "basic_salary" in df.columns:
            expected_pf = (basic_sal * 0.12).round(2)
            flags["RULE_PF_MISMATCH"] = (pf - expected_pf).abs() > self.pf_tolerance
        else:
            flags["RULE_PF_MISMATCH"] = False

        # 2. Exact ESI Calculation Check
        if "esi" in df.columns and "gross_salary" in df.columns:
            esi_ineligible = (gross_sal > 21_000.0) & (esi > self.esi_tolerance)
            expected_esi = np.where(gross_sal <= 21_000.0, (gross_sal * 0.0075).round(2), 0.0)
            esi_wrong = (esi - expected_esi).abs() > self.esi_tolerance
            flags["RULE_ESI_MISMATCH"] = esi_ineligible | esi_wrong
        else:
            flags["RULE_ESI_MISMATCH"] = False

        # 3. Gross Earnings Reconciliation Check
        if {"gross_salary", "basic_salary", "allowances"}.issubset(df.columns):
            expected_gross = basic_sal + allowances + ot_amt + bon
            flags["RULE_GROSS_RECONCILIATION_FAIL"] = (gross_sal - expected_gross).abs() > self.reconciliation_tolerance
        else:
            flags["RULE_GROSS_RECONCILIATION_FAIL"] = False

        # 4. Net Salary Reconciliation Check
        if {"net_salary", "gross_salary", "total_deductions"}.issubset(df.columns):
            expected_net = gross_sal - tot_ded
            flags["RULE_NET_RECONCILIATION_FAIL"] = (net_sal - expected_net).abs() > self.reconciliation_tolerance
        else:
            flags["RULE_NET_RECONCILIATION_FAIL"] = False

        # 5. Impossible Attendance Check
        if {"present_days", "working_days"}.issubset(df.columns):
            flags["RULE_IMPOSSIBLE_ATTENDANCE"] = (
                (pres_days > work_days) | ((pres_days + leave_days) > work_days)
            )
        else:
            flags["RULE_IMPOSSIBLE_ATTENDANCE"] = False

        # 6. Duplicate Employee / Payment Record Check
        if {"employee_id", "payroll_month"}.issubset(df.columns):
            flags["RULE_DUPLICATE_RECORD"] = df.duplicated(subset=["employee_id", "payroll_month"], keep=False)
        else:
            flags["RULE_DUPLICATE_RECORD"] = False

        # 7. Excessive Overtime Check
        if "overtime_hours" in df.columns:
            flags["RULE_EXCESSIVE_OVERTIME"] = ot_hours >= 60.0
        else:
            flags["RULE_EXCESSIVE_OVERTIME"] = False

        # 8. Abnormal Deductions Check
        if "other_deductions" in df.columns:
            flags["RULE_ABNORMAL_DEDUCTION"] = other_ded > 5000.0
        elif "deduction_to_gross_ratio" in df.columns:
            ded_ratio = _get_num("deduction_to_gross_ratio")
            flags["RULE_ABNORMAL_DEDUCTION"] = ded_ratio > 0.45
        else:
            flags["RULE_ABNORMAL_DEDUCTION"] = False

        return flags.fillna(False).astype(bool)

    def compute_rule_risk_scores(self, df: pd.DataFrame) -> np.ndarray:
        """Compute continuous rule violation score in [0, 1].

        Hard arithmetic/statutory violations return 1.0; zero violations return 0.0.
        """
        flags = self.evaluate_rules(df)
        violation_counts = flags.sum(axis=1).values
        # Any critical violation maps to 1.0
        return np.where(violation_counts > 0, 1.0, 0.0)

    def get_violation_reasons(self, df: pd.DataFrame) -> List[List[str]]:
        """Return list of violated rule codes per row."""
        flags = self.evaluate_rules(df)
        reasons = []
        for idx in range(len(df)):
            row = flags.iloc[idx]
            triggered = [col for col in flags.columns if row[col]]
            reasons.append(triggered)
        return reasons
