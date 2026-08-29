"""Hard-case dataset generator for AI Payroll Guardian (Phase 4).

Generates subtle statutory discrepancies, cold-start employee scenarios,
legitimate large revisions, compound anomalies, and camouflaged progressive anomalies.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from backend.config.settings import Settings, get_settings
from data_pipeline.generator import generate_synthetic_payroll_dataset


class HardCaseScenario(BaseModel):
    """Metadata describing a generated hard-case test scenario."""

    scenario_name: str
    category: str
    target_records: int
    ground_truth_anomalous: bool
    description: str


class HardCaseGenerator:
    """Generates rigorous challenge datasets for model hardening and sensitivity evaluation."""

    def __init__(self, random_seed: int = 42, settings: Optional[Settings] = None):
        self.random_seed = random_seed
        self.settings = settings or get_settings()
        self.rng = np.random.default_rng(random_seed)

    def generate_hard_case_suite(
        self,
        num_employees: int = 2000,
        num_months: int = 12,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Generate a complete hard-case challenge dataset with audit metadata.

        Returns:
            Tuple of (hard_case_df, audit_metadata_df).
        """
        # Step 1: Generate clean baseline multi-month population
        df_clean = generate_synthetic_payroll_dataset(
            settings=self.settings,
            num_employees=num_employees,
            num_months=num_months,
            random_seed=self.random_seed,
        )

        df = df_clean.copy(deep=True)
        df["is_anomaly"] = 0
        df["anomaly_type"] = "NONE"
        df["anomaly_severity"] = "NONE"
        df["challenge_category"] = "NORMAL_BASELINE"
        df["anomaly_magnitude"] = 0.0

        audit_records = []
        unique_emp_ids = sorted(df["employee_id"].unique().tolist())
        n_emps = len(unique_emp_ids)
        all_months = sorted(df["payroll_month"].unique().tolist())
        n_m = len(all_months)

        month_pf = all_months[min(n_m - 1, n_m // 2)]
        month_esi = all_months[min(n_m - 1, n_m // 2 + 1)]
        month_compound = all_months[max(0, n_m - 2)]
        month_legit = all_months[-1]

        # -------------------------------------------------------------
        # 1. Subtle PF Errors (Varied magnitudes: ₹1, ₹5, ₹10, ₹15, ₹25, ₹50, ₹100)
        # -------------------------------------------------------------
        pf_emps = unique_emp_ids[0 : int(n_emps * 0.12)]
        pf_magnitudes = [1.0, -1.0, 5.0, -5.0, 10.0, -10.0, 15.0, 25.0, 50.0, 100.0]

        for i, emp_id in enumerate(pf_emps):
            mag = pf_magnitudes[i % len(pf_magnitudes)]
            emp_mask = (df["employee_id"] == emp_id) & (df["payroll_month"] == month_pf)
            if emp_mask.any():
                idx = df[emp_mask].index[0]
                orig_pf = df.at[idx, "pf"]
                new_pf = max(round(orig_pf + mag, 2), 0.0)
                df.at[idx, "pf"] = new_pf
                df.at[idx, "total_deductions"] = round(df.at[idx, "total_deductions"] + (new_pf - orig_pf), 2)
                df.at[idx, "net_salary"] = round(df.at[idx, "gross_salary"] - df.at[idx, "total_deductions"], 2)
                df.at[idx, "is_anomaly"] = 1
                df.at[idx, "anomaly_type"] = "SUBTLE_PF_MISMATCH"
                df.at[idx, "anomaly_severity"] = "LOW" if abs(mag) <= 10.0 else "MEDIUM"
                df.at[idx, "challenge_category"] = "SUBTLE_STATUTORY"
                df.at[idx, "anomaly_magnitude"] = abs(mag)

                audit_records.append({
                    "employee_id": emp_id,
                    "payroll_month": month_pf,
                    "anomaly_type": "SUBTLE_PF_MISMATCH",
                    "challenge_category": "SUBTLE_STATUTORY",
                    "magnitude": abs(mag),
                    "pre_value": orig_pf,
                    "post_value": new_pf,
                    "description": f"Subtle PF deviation of ₹{mag:+.2f} relative to statutory 12%",
                })

        # -------------------------------------------------------------
        # 2. Subtle ESI Errors (₹2, ₹5, ₹10, ₹25, ₹50)
        # -------------------------------------------------------------
        esi_emps = unique_emp_ids[int(n_emps * 0.12) : int(n_emps * 0.24)]
        esi_magnitudes = [2.0, -2.0, 5.0, -5.0, 10.0, 25.0, 50.0]

        for i, emp_id in enumerate(esi_emps):
            mag = esi_magnitudes[i % len(esi_magnitudes)]
            emp_mask = (df["employee_id"] == emp_id) & (df["payroll_month"] == month_esi)
            if emp_mask.any():
                idx = df[emp_mask].index[0]
                orig_esi = df.at[idx, "esi"]
                new_esi = max(round(orig_esi + mag, 2), 0.0)
                df.at[idx, "esi"] = new_esi
                df.at[idx, "total_deductions"] = round(df.at[idx, "total_deductions"] + (new_esi - orig_esi), 2)
                df.at[idx, "net_salary"] = round(df.at[idx, "gross_salary"] - df.at[idx, "total_deductions"], 2)
                df.at[idx, "is_anomaly"] = 1
                df.at[idx, "anomaly_type"] = "SUBTLE_ESI_MISMATCH"
                df.at[idx, "anomaly_severity"] = "LOW" if abs(mag) <= 10.0 else "MEDIUM"
                df.at[idx, "challenge_category"] = "SUBTLE_STATUTORY"
                df.at[idx, "anomaly_magnitude"] = abs(mag)

                audit_records.append({
                    "employee_id": emp_id,
                    "payroll_month": month_esi,
                    "anomaly_type": "SUBTLE_ESI_MISMATCH",
                    "challenge_category": "SUBTLE_STATUTORY",
                    "magnitude": abs(mag),
                    "pre_value": orig_esi,
                    "post_value": new_esi,
                    "description": f"Subtle ESI discrepancy of ₹{mag:+.2f}",
                })

        # -------------------------------------------------------------
        # 3. Cold-Start Employees with Injected Anomalies (0, 1, 2 prior months)
        # -------------------------------------------------------------
        cold_emps = unique_emp_ids[int(n_emps * 0.24) : int(n_emps * 0.36)]
        for i, emp_id in enumerate(cold_emps):
            target_month = all_months[i % min(n_m, 3)]
            emp_mask = (df["employee_id"] == emp_id) & (df["payroll_month"] == target_month)
            if emp_mask.any():
                idx = df[emp_mask].index[0]
                if i % 2 == 0:
                    orig_ot = df.at[idx, "overtime_hours"]
                    new_ot = 75.0
                    df.at[idx, "overtime_hours"] = new_ot
                    df.at[idx, "overtime_amount"] = round(new_ot * (df.at[idx, "basic_salary"] / (26 * 8)) * 1.5, 2)
                    df.at[idx, "gross_salary"] = round(df.at[idx, "basic_salary"] + df.at[idx, "allowances"] + df.at[idx, "overtime_amount"], 2)
                    df.at[idx, "net_salary"] = round(df.at[idx, "gross_salary"] - df.at[idx, "total_deductions"], 2)
                    anom_type = "COLD_START_EXCESSIVE_OVERTIME"
                else:
                    orig_sal = df.at[idx, "basic_salary"]
                    df.at[idx, "basic_salary"] = round(orig_sal * 1.80, 2)
                    df.at[idx, "gross_salary"] = round(df.at[idx, "basic_salary"] + df.at[idx, "allowances"], 2)
                    df.at[idx, "net_salary"] = round(df.at[idx, "gross_salary"] - df.at[idx, "total_deductions"], 2)
                    anom_type = "COLD_START_SALARY_SPIKE"

                df.at[idx, "is_anomaly"] = 1
                df.at[idx, "anomaly_type"] = anom_type
                df.at[idx, "anomaly_severity"] = "HIGH"
                df.at[idx, "challenge_category"] = "COLD_START"
                df.at[idx, "anomaly_magnitude"] = float(i % min(n_m, 3))

                audit_records.append({
                    "employee_id": emp_id,
                    "payroll_month": target_month,
                    "anomaly_type": anom_type,
                    "challenge_category": "COLD_START",
                    "magnitude": float(i % min(n_m, 3)),
                    "pre_value": 0.0,
                    "post_value": 1.0,
                    "description": f"Cold-start anomaly with only {i % min(n_m, 3)} prior historical observation(s)",
                })

        # -------------------------------------------------------------
        # 4. Legitimate Large Bonuses & Salary Revisions (Ground Truth: Normal = 0)
        # -------------------------------------------------------------
        legit_emps = unique_emp_ids[int(n_emps * 0.36) : int(n_emps * 0.50)]
        for i, emp_id in enumerate(legit_emps):
            emp_mask = (df["employee_id"] == emp_id) & (df["payroll_month"] == month_legit)
            if emp_mask.any():
                idx = df[emp_mask].index[0]
                if i % 2 == 0:
                    bonus_val = float(self.rng.uniform(80_000.0, 220_000.0))
                    df.at[idx, "bonus"] = round(bonus_val, 2)
                    df.at[idx, "gross_salary"] = round(df.at[idx, "basic_salary"] + df.at[idx, "allowances"] + df.at[idx, "bonus"], 2)
                    df.at[idx, "net_salary"] = round(df.at[idx, "gross_salary"] - df.at[idx, "total_deductions"], 2)
                    df.at[idx, "challenge_category"] = "LEGITIMATE_LARGE_BONUS"
                else:
                    orig_sal = df.at[idx, "basic_salary"]
                    inc_sal = round(orig_sal * float(self.rng.uniform(1.30, 1.45)), 2)
                    for m in all_months[-3:]:
                        sub_mask = (df["employee_id"] == emp_id) & (df["payroll_month"] == m)
                        if sub_mask.any():
                            s_idx = df[sub_mask].index[0]
                            df.at[s_idx, "basic_salary"] = inc_sal
                            df.at[s_idx, "allowances"] = round(inc_sal * 1.22, 2)
                            df.at[s_idx, "gross_salary"] = round(df.at[s_idx, "basic_salary"] + df.at[s_idx, "allowances"], 2)
                            df.at[s_idx, "pf"] = round(inc_sal * 0.12, 2)
                            df.at[s_idx, "total_deductions"] = round(df.at[s_idx, "pf"] + df.at[s_idx, "tds"] + df.at[s_idx, "other_deductions"], 2)
                            df.at[s_idx, "net_salary"] = round(df.at[s_idx, "gross_salary"] - df.at[s_idx, "total_deductions"], 2)
                            df.at[s_idx, "challenge_category"] = "LEGITIMATE_PROMOTION"

                df.at[idx, "is_anomaly"] = 0
                df.at[idx, "anomaly_type"] = "NONE"

        # -------------------------------------------------------------
        # 5. Compound Simultaneous Multi-Anomalies
        # -------------------------------------------------------------
        compound_emps = unique_emp_ids[int(n_emps * 0.50) : int(n_emps * 0.65)]
        for i, emp_id in enumerate(compound_emps):
            emp_mask = (df["employee_id"] == emp_id) & (df["payroll_month"] == month_compound)
            if emp_mask.any():
                idx = df[emp_mask].index[0]
                if i % 3 == 0:
                    df.at[idx, "basic_salary"] = round(df.at[idx, "basic_salary"] * 1.75, 2)
                    df.at[idx, "overtime_hours"] = 80.0
                    df.at[idx, "overtime_amount"] = round(80.0 * (df.at[idx, "basic_salary"] / (26 * 8)) * 1.5, 2)
                    df.at[idx, "gross_salary"] = round(df.at[idx, "basic_salary"] + df.at[idx, "allowances"] + df.at[idx, "overtime_amount"], 2)
                    df.at[idx, "net_salary"] = round(df.at[idx, "gross_salary"] - df.at[idx, "total_deductions"], 2)
                    anom_type = "SUDDEN_SALARY_INCREASE,EXCESSIVE_OVERTIME"
                elif i % 3 == 1:
                    df.at[idx, "present_days"] = df.at[idx, "working_days"]
                    df.at[idx, "gross_salary"] = round(df.at[idx, "basic_salary"] * 0.40, 2)
                    df.at[idx, "net_salary"] = round(df.at[idx, "gross_salary"] + 15_000.0, 2)
                    anom_type = "ATTENDANCE_PAY_MISMATCH,ABNORMAL_NET_SALARY"
                else:
                    df.at[idx, "pf"] = 0.0
                    df.at[idx, "esi"] = 1200.0
                    anom_type = "INCORRECT_PF,INCORRECT_ESI"

                df.at[idx, "is_anomaly"] = 1
                df.at[idx, "anomaly_type"] = anom_type
                df.at[idx, "anomaly_severity"] = "CRITICAL"
                df.at[idx, "challenge_category"] = "COMPOUND_ANOMALY"

                audit_records.append({
                    "employee_id": emp_id,
                    "payroll_month": month_compound,
                    "anomaly_type": anom_type,
                    "challenge_category": "COMPOUND_ANOMALY",
                    "magnitude": 2.0,
                    "pre_value": 0.0,
                    "post_value": 2.0,
                    "description": f"Simultaneous multi-anomaly event: {anom_type}",
                })

        # -------------------------------------------------------------
        # 6. Camouflaged / Adversarial Anomalies (Gradual Creeps)
        # -------------------------------------------------------------
        adv_emps = unique_emp_ids[int(n_emps * 0.65) : int(n_emps * 0.80)]
        all_months = sorted(df["payroll_month"].unique().tolist())
        creep_months = all_months[-4:] if len(all_months) >= 4 else all_months

        for i, emp_id in enumerate(adv_emps):
            emp_records = df[df["employee_id"] == emp_id]
            if emp_records.empty:
                continue
            base_sal = emp_records["basic_salary"].iloc[0]

            if i % 2 == 0:
                # Gradual Salary Creep (+11% each month)
                cur_sal = base_sal
                for m_idx, cm in enumerate(creep_months):
                    cur_sal = round(cur_sal * 1.11, 2)
                    c_mask = (df["employee_id"] == emp_id) & (df["payroll_month"] == cm)
                    if c_mask.any():
                        c_idx = df[c_mask].index[0]
                        df.at[c_idx, "basic_salary"] = cur_sal
                        df.at[c_idx, "gross_salary"] = round(cur_sal + df.at[c_idx, "allowances"], 2)
                        df.at[c_idx, "net_salary"] = round(df.at[c_idx, "gross_salary"] - df.at[c_idx, "total_deductions"], 2)
                        df.at[c_idx, "is_anomaly"] = 1
                        df.at[c_idx, "anomaly_type"] = "CAMOUFLAGED_SALARY_CREEP"
                        df.at[c_idx, "anomaly_severity"] = "MEDIUM" if m_idx < 2 else "HIGH"
                        df.at[c_idx, "challenge_category"] = "CAMOUFLAGED_ADVERSARIAL"
                        df.at[c_idx, "anomaly_magnitude"] = round(((cur_sal - base_sal) / base_sal) * 100, 1)

                        audit_records.append({
                            "employee_id": emp_id,
                            "payroll_month": cm,
                            "anomaly_type": "CAMOUFLAGED_SALARY_CREEP",
                            "challenge_category": "CAMOUFLAGED_ADVERSARIAL",
                            "magnitude": round(((cur_sal - base_sal) / base_sal) * 100, 1),
                            "pre_value": base_sal,
                            "post_value": cur_sal,
                            "description": f"Gradual unapproved salary creeping step {m_idx+1}/4 (+{((cur_sal-base_sal)/base_sal)*100:.1f}% cumulative)",
                        })
            else:
                # Gradual Overtime Creep (+15h each month)
                cur_ot = 10.0
                for m_idx, cm in enumerate(creep_months):
                    cur_ot += 15.0
                    c_mask = (df["employee_id"] == emp_id) & (df["payroll_month"] == cm)
                    if c_mask.any():
                        c_idx = df[c_mask].index[0]
                        df.at[c_idx, "overtime_hours"] = cur_ot
                        df.at[c_idx, "overtime_amount"] = round(cur_ot * (df.at[c_idx, "basic_salary"] / (26 * 8)) * 1.5, 2)
                        df.at[c_idx, "gross_salary"] = round(df.at[c_idx, "basic_salary"] + df.at[c_idx, "allowances"] + df.at[c_idx, "overtime_amount"], 2)
                        df.at[c_idx, "net_salary"] = round(df.at[c_idx, "gross_salary"] - df.at[c_idx, "total_deductions"], 2)
                        df.at[c_idx, "is_anomaly"] = 1
                        df.at[c_idx, "anomaly_type"] = "CAMOUFLAGED_OVERTIME_CREEP"
                        df.at[c_idx, "anomaly_severity"] = "MEDIUM" if cur_ot < 55.0 else "HIGH"
                        df.at[c_idx, "challenge_category"] = "CAMOUFLAGED_ADVERSARIAL"
                        df.at[c_idx, "anomaly_magnitude"] = cur_ot

                        audit_records.append({
                            "employee_id": emp_id,
                            "payroll_month": cm,
                            "anomaly_type": "CAMOUFLAGED_OVERTIME_CREEP",
                            "challenge_category": "CAMOUFLAGED_ADVERSARIAL",
                            "magnitude": cur_ot,
                            "pre_value": 10.0,
                            "post_value": cur_ot,
                            "description": f"Gradual overtime creeping step {m_idx+1}/4 ({cur_ot} hours)",
                        })

        audit_df = pd.DataFrame(audit_records)
        return df, audit_df
