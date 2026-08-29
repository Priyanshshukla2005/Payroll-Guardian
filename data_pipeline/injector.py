"""Anomaly injection engine for AI Payroll Guardian.

Injects 13 distinct types of realistic payroll anomalies into a synthetic dataset,
producing a labeled anomalous dataset and a detailed anomaly audit log.
Supports in-memory processing and streaming chunked injection.
"""

from typing import Any, Dict, Generator, List, Optional, Tuple
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field


class AnomalyMetadata(BaseModel):
    """Detailed audit metadata for an injected payroll anomaly."""

    anomaly_id: str
    employee_id: str
    payroll_month: str
    anomaly_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    original_value: str
    modified_value: str
    description: str


class PayrollAnomalyInjector:
    """Engine for introducing controlled payroll anomalies into clean datasets."""

    ANOMALY_TYPES = [
        "SUDDEN_SALARY_INCREASE",
        "SUDDEN_SALARY_DECREASE",
        "EXCESSIVE_OVERTIME",
        "ATTENDANCE_PAY_MISMATCH",
        "IMPOSSIBLE_ATTENDANCE",
        "DUPLICATE_EMPLOYEE_RECORD",
        "INCORRECT_PF",
        "INCORRECT_ESI",
        "ABNORMAL_DEDUCTION",
        "ABNORMALLY_HIGH_BONUS",
        "ABNORMAL_NET_SALARY",
        "MISSING_PAYROLL_RECORD",
        "DUPLICATE_PAYMENT",
    ]

    def __init__(self, random_seed: int = 42):
        self.seed = random_seed
        self.rng = np.random.default_rng(self.seed)
        self.metadata_records: List[AnomalyMetadata] = []
        self.anomaly_counter = 0

    def _next_anomaly_id(self) -> str:
        self.anomaly_counter += 1
        return f"ANOM_{self.anomaly_counter:07d}"

    def _tag_record(
        self,
        df: pd.DataFrame,
        idx: int,
        anomaly_type: str,
        severity: str,
        orig_val: Any,
        mod_val: Any,
        desc: str,
    ):
        """Helper to tag row and create audit metadata."""
        anom_id = self._next_anomaly_id()
        emp_id = df.at[idx, "employee_id"]
        month = df.at[idx, "payroll_month"]

        # Handle multi-label anomalies if row was already tagged
        current_type = df.at[idx, "anomaly_type"]
        if current_type == "NONE" or pd.isna(current_type):
            df.at[idx, "anomaly_type"] = anomaly_type
        else:
            df.at[idx, "anomaly_type"] = f"{current_type},{anomaly_type}"

        df.at[idx, "is_anomaly"] = 1

        self.metadata_records.append(
            AnomalyMetadata(
                anomaly_id=anom_id,
                employee_id=emp_id,
                payroll_month=month,
                anomaly_type=anomaly_type,
                severity=severity,
                original_value=str(orig_val),
                modified_value=str(mod_val),
                description=desc,
            )
        )

    # 1. Sudden Salary Increase
    def inject_sudden_salary_increase(self, df: pd.DataFrame, indices: np.ndarray):
        for idx in indices:
            orig_basic = df.at[idx, "basic_salary"]
            multiplier = self.rng.uniform(1.6, 2.5)
            new_basic = round(orig_basic * multiplier, 2)
            df.at[idx, "basic_salary"] = new_basic
            diff = new_basic - orig_basic
            df.at[idx, "gross_salary"] = round(df.at[idx, "gross_salary"] + diff, 2)
            df.at[idx, "net_salary"] = round(df.at[idx, "net_salary"] + diff, 2)

            self._tag_record(
                df,
                idx,
                anomaly_type="SUDDEN_SALARY_INCREASE",
                severity="HIGH",
                orig_val=f"Basic={orig_basic}",
                mod_val=f"Basic={new_basic}",
                desc=f"Sudden unauthorized salary spike of {multiplier:.1f}x without legitimate promotion record.",
            )

    # 2. Sudden Salary Decrease
    def inject_sudden_salary_decrease(self, df: pd.DataFrame, indices: np.ndarray):
        for idx in indices:
            orig_basic = df.at[idx, "basic_salary"]
            factor = self.rng.uniform(0.35, 0.60)
            new_basic = round(orig_basic * factor, 2)
            df.at[idx, "basic_salary"] = new_basic
            diff = orig_basic - new_basic
            df.at[idx, "gross_salary"] = round(max(df.at[idx, "gross_salary"] - diff, 0.0), 2)
            df.at[idx, "net_salary"] = round(max(df.at[idx, "gross_salary"] - df.at[idx, "total_deductions"], 0.0), 2)

            self._tag_record(
                df,
                idx,
                anomaly_type="SUDDEN_SALARY_DECREASE",
                severity="HIGH",
                orig_val=f"Basic={orig_basic}",
                mod_val=f"Basic={new_basic}",
                desc=f"Unexplained steep drop in basic salary (reduction of {(1.0-factor)*100:.1f}%).",
            )

    # 3. Excessive Overtime
    def inject_excessive_overtime(self, df: pd.DataFrame, indices: np.ndarray):
        for idx in indices:
            orig_ot_hrs = df.at[idx, "overtime_hours"]
            orig_ot_amt = df.at[idx, "overtime_amount"]
            new_ot_hrs = round(float(self.rng.uniform(85.0, 140.0)), 1)
            hourly_rate = df.at[idx, "basic_salary"] / (df.at[idx, "working_days"] * 8.0)
            new_ot_amt = round(hourly_rate * 1.5 * new_ot_hrs, 2)

            df.at[idx, "overtime_hours"] = new_ot_hrs
            df.at[idx, "overtime_amount"] = new_ot_amt
            df.at[idx, "gross_salary"] = round(
                df.at[idx, "basic_salary"] + df.at[idx, "allowances"] + new_ot_amt + df.at[idx, "bonus"], 2
            )
            df.at[idx, "net_salary"] = round(df.at[idx, "gross_salary"] - df.at[idx, "total_deductions"], 2)

            self._tag_record(
                df,
                idx,
                anomaly_type="EXCESSIVE_OVERTIME",
                severity="HIGH",
                orig_val=f"OT={orig_ot_hrs}h (₹{orig_ot_amt})",
                mod_val=f"OT={new_ot_hrs}h (₹{new_ot_amt})",
                desc=f"Abnormally high overtime logged ({new_ot_hrs}h exceeds realistic threshold).",
            )

    # 4. Attendance / Pay Mismatch
    def inject_attendance_pay_mismatch(self, df: pd.DataFrame, indices: np.ndarray):
        for idx in indices:
            orig_present = df.at[idx, "present_days"]
            orig_gross = df.at[idx, "gross_salary"]
            df.at[idx, "present_days"] = df.at[idx, "working_days"]
            fraction = self.rng.uniform(0.35, 0.50)
            new_gross = round(orig_gross * fraction, 2)
            df.at[idx, "gross_salary"] = new_gross
            df.at[idx, "net_salary"] = round(max(new_gross - df.at[idx, "total_deductions"], 0.0), 2)

            self._tag_record(
                df,
                idx,
                anomaly_type="ATTENDANCE_PAY_MISMATCH",
                severity="CRITICAL",
                orig_val=f"Gross=₹{orig_gross} (Present={orig_present})",
                mod_val=f"Gross=₹{new_gross} (Present={df.at[idx, 'working_days']})",
                desc=f"Employee worked full {df.at[idx, 'working_days']} days but salary was truncated to ₹{new_gross}.",
            )

    # 5. Impossible Attendance
    def inject_impossible_attendance(self, df: pd.DataFrame, indices: np.ndarray):
        for idx in indices:
            orig_present = df.at[idx, "present_days"]
            orig_wd = df.at[idx, "working_days"]
            new_present = int(orig_wd + self.rng.integers(5, 12))
            df.at[idx, "present_days"] = new_present

            self._tag_record(
                df,
                idx,
                anomaly_type="IMPOSSIBLE_ATTENDANCE",
                severity="CRITICAL",
                orig_val=f"Present={orig_present}/{orig_wd}",
                mod_val=f"Present={new_present}/{orig_wd}",
                desc=f"Present days ({new_present}) exceeds total working days ({orig_wd}) in month.",
            )

    # 6. Duplicate Employee Record
    def inject_duplicate_employee_records(self, df: pd.DataFrame, indices: np.ndarray) -> pd.DataFrame:
        dup_rows = []
        for idx in indices:
            row_copy = df.loc[idx].copy()
            self._tag_record(
                df,
                idx,
                anomaly_type="DUPLICATE_EMPLOYEE_RECORD",
                severity="CRITICAL",
                orig_val="Single record",
                mod_val="Duplicate record injected",
                desc="Duplicate payroll entry found for the same employee in the same payroll month.",
            )
            row_copy["is_anomaly"] = 1
            row_copy["anomaly_type"] = "DUPLICATE_EMPLOYEE_RECORD"
            dup_rows.append(row_copy)

        if dup_rows:
            df = pd.concat([df, pd.DataFrame(dup_rows)], ignore_index=True)
        return df

    # 7. Incorrect PF Calculation
    def inject_incorrect_pf(self, df: pd.DataFrame, indices: np.ndarray):
        for idx in indices:
            orig_pf = df.at[idx, "pf"]
            basic = df.at[idx, "basic_salary"]
            if self.rng.random() < 0.5:
                new_pf = 0.0
            else:
                new_pf = round(basic * 0.40, 2)

            df.at[idx, "pf"] = new_pf
            df.at[idx, "total_deductions"] = round(
                new_pf + df.at[idx, "esi"] + df.at[idx, "tds"] + df.at[idx, "other_deductions"], 2
            )
            df.at[idx, "net_salary"] = round(df.at[idx, "gross_salary"] - df.at[idx, "total_deductions"], 2)

            self._tag_record(
                df,
                idx,
                anomaly_type="INCORRECT_PF",
                severity="MEDIUM",
                orig_val=f"PF=₹{orig_pf}",
                mod_val=f"PF=₹{new_pf}",
                desc=f"PF contribution (₹{new_pf}) violates synthetic 12% rule on basic (₹{basic}).",
            )

    # 8. Incorrect ESI Calculation
    def inject_incorrect_esi(self, df: pd.DataFrame, indices: np.ndarray):
        for idx in indices:
            orig_esi = df.at[idx, "esi"]
            gross = df.at[idx, "gross_salary"]
            new_esi = round(gross * 0.04, 2) if gross > 21000 else 0.0
            if new_esi == 0.0 and orig_esi == 0.0:
                new_esi = 850.0

            df.at[idx, "esi"] = new_esi
            df.at[idx, "total_deductions"] = round(
                df.at[idx, "pf"] + new_esi + df.at[idx, "tds"] + df.at[idx, "other_deductions"], 2
            )
            df.at[idx, "net_salary"] = round(df.at[idx, "gross_salary"] - df.at[idx, "total_deductions"], 2)

            self._tag_record(
                df,
                idx,
                anomaly_type="INCORRECT_ESI",
                severity="MEDIUM",
                orig_val=f"ESI=₹{orig_esi}",
                mod_val=f"ESI=₹{new_esi}",
                desc=f"Ineligible/incorrect ESI contribution (₹{new_esi}) deducted on gross wage ₹{gross}.",
            )

    # 9. Abnormal Deduction
    def inject_abnormal_deduction(self, df: pd.DataFrame, indices: np.ndarray):
        for idx in indices:
            orig_other = df.at[idx, "other_deductions"]
            inflated_ded = float(self.rng.integers(15000, 45000))
            df.at[idx, "other_deductions"] = inflated_ded
            df.at[idx, "total_deductions"] = round(
                df.at[idx, "pf"] + df.at[idx, "esi"] + df.at[idx, "tds"] + inflated_ded, 2
            )
            df.at[idx, "net_salary"] = round(max(df.at[idx, "gross_salary"] - df.at[idx, "total_deductions"], 0.0), 2)

            self._tag_record(
                df,
                idx,
                anomaly_type="ABNORMAL_DEDUCTION",
                severity="HIGH",
                orig_val=f"OtherDed=₹{orig_other}",
                mod_val=f"OtherDed=₹{inflated_ded}",
                desc=f"Spike in other deductions (₹{inflated_ded}) without documented loan or penalty authorization.",
            )

    # 10. Abnormally High Bonus
    def inject_abnormally_high_bonus(self, df: pd.DataFrame, indices: np.ndarray):
        for idx in indices:
            orig_bonus = df.at[idx, "bonus"]
            basic = df.at[idx, "basic_salary"]
            inflated_bonus = round(float(self.rng.uniform(180000.0, 450000.0)), 2)
            df.at[idx, "bonus"] = inflated_bonus
            df.at[idx, "gross_salary"] = round(
                df.at[idx, "basic_salary"] + df.at[idx, "allowances"] + df.at[idx, "overtime_amount"] + inflated_bonus, 2
            )
            df.at[idx, "net_salary"] = round(df.at[idx, "gross_salary"] - df.at[idx, "total_deductions"], 2)

            self._tag_record(
                df,
                idx,
                anomaly_type="ABNORMALLY_HIGH_BONUS",
                severity="HIGH",
                orig_val=f"Bonus=₹{orig_bonus}",
                mod_val=f"Bonus=₹{inflated_bonus}",
                desc=f"Extreme bonus of ₹{inflated_bonus} injected disproportionate to basic pay (₹{basic}).",
            )

    # 11. Abnormal Net Salary Reconciliation Discrepancy
    def inject_abnormal_net_salary(self, df: pd.DataFrame, indices: np.ndarray):
        for idx in indices:
            orig_net = df.at[idx, "net_salary"]
            expected_net = df.at[idx, "gross_salary"] - df.at[idx, "total_deductions"]
            offset = float(self.rng.choice([15000, 25000, -18000, -30000]))
            corrupted_net = round(max(expected_net + offset, 1000.0), 2)
            df.at[idx, "net_salary"] = corrupted_net

            self._tag_record(
                df,
                idx,
                anomaly_type="ABNORMAL_NET_SALARY",
                severity="CRITICAL",
                orig_val=f"Net=₹{orig_net}",
                mod_val=f"Net=₹{corrupted_net}",
                desc=f"Net salary ₹{corrupted_net} fails reconciliation with gross (₹{df.at[idx, 'gross_salary']}) and deductions (₹{df.at[idx, 'total_deductions']}).",
            )

    # 12. Missing Payroll Record (dropped rows)
    def inject_missing_payroll_records(self, df: pd.DataFrame, indices: np.ndarray) -> pd.DataFrame:
        drop_indices = []
        for idx in indices:
            emp_id = df.at[idx, "employee_id"]
            month = df.at[idx, "payroll_month"]
            anom_id = self._next_anomaly_id()
            self.metadata_records.append(
                AnomalyMetadata(
                    anomaly_id=anom_id,
                    employee_id=emp_id,
                    payroll_month=month,
                    anomaly_type="MISSING_PAYROLL_RECORD",
                    severity="CRITICAL",
                    original_value="Record Present",
                    modified_value="Record Dropped/Omitted",
                    description=f"Active employee {emp_id} omitted from payroll in {month}.",
                )
            )
            drop_indices.append(idx)

        df = df.drop(index=drop_indices).reset_index(drop=True)
        return df

    # 13. Duplicate Payment
    def inject_duplicate_payment(self, df: pd.DataFrame, indices: np.ndarray) -> pd.DataFrame:
        dup_payments = []
        for idx in indices:
            row_copy = df.loc[idx].copy()
            self._tag_record(
                df,
                idx,
                anomaly_type="DUPLICATE_PAYMENT",
                severity="CRITICAL",
                orig_val="Single Disbursement",
                mod_val="Duplicate Disbursement",
                desc="Duplicate disbursement record generated for the same employee-month.",
            )
            row_copy["is_anomaly"] = 1
            row_copy["anomaly_type"] = "DUPLICATE_PAYMENT"
            dup_payments.append(row_copy)

        if dup_payments:
            df = pd.concat([df, pd.DataFrame(dup_payments)], ignore_index=True)
        return df

    def inject_all_anomalies(
        self,
        df_clean: pd.DataFrame,
        anomaly_rate: float = 0.05,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Inject all 13 anomaly types into a clean copy of the dataset.

        Args:
            df_clean: Clean baseline payroll DataFrame.
            anomaly_rate: Proportion of total rows to target for anomalies (e.g. 0.05).

        Returns:
            Tuple of:
            1. df_anomalous: Labeled DataFrame with injected anomalies.
            2. df_metadata: DataFrame containing comprehensive audit log.
        """
        # Deep copy to ensure clean dataset remains strictly untouched
        df_anom = df_clean.copy(deep=True)
        total_rows = len(df_anom)
        target_anomalies = max(int(total_rows * anomaly_rate), len(self.ANOMALY_TYPES))

        num_types = len(self.ANOMALY_TYPES)

        # Randomly choose non-overlapping candidate row indices
        all_indices = np.arange(total_rows)
        self.rng.shuffle(all_indices)

        splits = np.array_split(all_indices[:target_anomalies], num_types)

        # 1. Perform all in-place column mutations first so indices remain unmodified
        self.inject_sudden_salary_increase(df_anom, splits[0])
        self.inject_sudden_salary_decrease(df_anom, splits[1])
        self.inject_excessive_overtime(df_anom, splits[2])
        self.inject_attendance_pay_mismatch(df_anom, splits[3])
        self.inject_impossible_attendance(df_anom, splits[4])
        self.inject_incorrect_pf(df_anom, splits[6])
        self.inject_incorrect_esi(df_anom, splits[7])
        self.inject_abnormal_deduction(df_anom, splits[8])
        self.inject_abnormally_high_bonus(df_anom, splits[9])
        self.inject_abnormal_net_salary(df_anom, splits[10])

        # 2. Append duplicate records and duplicate payments
        df_anom = self.inject_duplicate_employee_records(df_anom, splits[5])
        df_anom = self.inject_duplicate_payment(df_anom, splits[12])

        # 3. Drop missing records at the very end
        df_anom = self.inject_missing_payroll_records(df_anom, splits[11])

        metadata_dict = [m.model_dump() for m in self.metadata_records]
        df_metadata = pd.DataFrame(metadata_dict)

        return df_anom, df_metadata

    def inject_anomalies_stream(
        self,
        clean_chunks: Generator[pd.DataFrame, None, None],
        anomaly_rate: float = 0.05,
    ) -> Generator[Tuple[pd.DataFrame, pd.DataFrame], None, None]:
        """Inject anomalies chunk-by-chunk across large datasets with constant RAM overhead.

        Args:
            clean_chunks: Generator of clean DataFrame chunks.
            anomaly_rate: Proportion of rows to inject.

        Yields:
            Tuples of (anomalous_chunk_df, metadata_chunk_df).
        """
        for chunk in clean_chunks:
            self.metadata_records.clear()
            df_anom_chunk, df_meta_chunk = self.inject_all_anomalies(
                df_clean=chunk,
                anomaly_rate=anomaly_rate,
            )
            yield df_anom_chunk, df_meta_chunk
