"""Data validation, reconciliation, and cleaning module for payroll records.

Supports in-memory DataFrame validation and out-of-core streaming validation
for large-scale datasets (millions of records).
"""

from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Union
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from data_pipeline.loader import iter_payroll_batches


class ValidationViolation(BaseModel):
    """Details of a single validation rule violation."""

    rule_name: str
    violation_count: int
    sample_indices: List[int] = Field(default_factory=list)
    description: str


class ValidationReport(BaseModel):
    """Comprehensive validation report summarizing dataset integrity."""

    is_valid: bool
    total_records: int
    violation_count: int
    violations: List[ValidationViolation] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)


def validate_payroll_dataset(
    df: pd.DataFrame,
    tolerance: float = 0.05,
    raise_on_error: bool = False,
) -> ValidationReport:
    """Validate payroll dataset against deterministic integrity and reconciliation rules.

    Rules checked:
    1. No duplicate (employee_id, payroll_month) records.
    2. Non-null employee IDs and payroll months.
    3. Positive working days (working_days > 0).
    4. Non-negative attendance (present_days >= 0, leave_days >= 0).
    5. Attendance validity: present_days + leave_days <= working_days.
    6. Non-negative salary and overtime components.
    7. Non-negative deduction components.
    8. Gross salary reconciliation: gross == basic + allowances + overtime_amount + bonus.
    9. Deductions reconciliation: total_deductions == pf + esi + tds + other_deductions.
    10. Net salary reconciliation: net_salary == gross_salary - total_deductions.

    Args:
        df: Payroll DataFrame to validate.
        tolerance: Numerical floating point margin of error for reconciliation.
        raise_on_error: If True, raises ValueError upon any validation failure.

    Returns:
        ValidationReport containing detailed violation metrics.
    """
    total_records = len(df)
    violations: List[ValidationViolation] = []

    # 1. Duplicate employee/month records
    if "employee_id" in df.columns and "payroll_month" in df.columns:
        dups = df.duplicated(subset=["employee_id", "payroll_month"], keep=False)
        dup_count = int(dups.sum())
        if dup_count > 0:
            violations.append(
                ValidationViolation(
                    rule_name="NO_DUPLICATE_EMPLOYEE_MONTH",
                    violation_count=dup_count,
                    sample_indices=df.index[dups][:10].tolist(),
                    description=f"Found {dup_count} duplicate employee-month records.",
                )
            )

    # 2. Null mandatory IDs
    for col in ["employee_id", "payroll_month"]:
        if col in df.columns:
            nulls = df[col].isna()
            null_count = int(nulls.sum())
            if null_count > 0:
                violations.append(
                    ValidationViolation(
                        rule_name=f"NON_NULL_{col.upper()}",
                        violation_count=null_count,
                        sample_indices=df.index[nulls][:10].tolist(),
                        description=f"Found {null_count} null values in {col}.",
                    )
                )

    # 3. Working days > 0
    if "working_days" in df.columns:
        invalid_wd = (df["working_days"] <= 0) | df["working_days"].isna()
        inv_wd_count = int(invalid_wd.sum())
        if inv_wd_count > 0:
            violations.append(
                ValidationViolation(
                    rule_name="WORKING_DAYS_POSITIVE",
                    violation_count=inv_wd_count,
                    sample_indices=df.index[invalid_wd][:10].tolist(),
                    description=f"Found {inv_wd_count} records with working_days <= 0 or NaN.",
                )
            )

    # 4. Present and Leave days >= 0
    for att_col in ["present_days", "leave_days"]:
        if att_col in df.columns:
            neg_att = (df[att_col] < 0) | df[att_col].isna()
            neg_count = int(neg_att.sum())
            if neg_count > 0:
                violations.append(
                    ValidationViolation(
                        rule_name=f"NON_NEGATIVE_{att_col.upper()}",
                        violation_count=neg_count,
                        sample_indices=df.index[neg_att][:10].tolist(),
                        description=f"Found {neg_count} records with negative or NaN {att_col}.",
                    )
                )

    # 5. Impossible attendance: present_days + leave_days <= working_days
    if {"present_days", "leave_days", "working_days"}.issubset(df.columns):
        att_sum = df["present_days"] + df["leave_days"]
        impossible_att = (att_sum > df["working_days"]) | (df["present_days"] > df["working_days"])
        imp_count = int(impossible_att.sum())
        if imp_count > 0:
            violations.append(
                ValidationViolation(
                    rule_name="ATTENDANCE_BOUNDS_VALID",
                    violation_count=imp_count,
                    sample_indices=df.index[impossible_att][:10].tolist(),
                    description=f"Found {imp_count} records where present + leave > working_days or present > working_days.",
                )
            )

    # 6. Non-negative salary and overtime components
    salary_cols = ["basic_salary", "allowances", "overtime_hours", "overtime_amount", "bonus", "gross_salary"]
    for col in salary_cols:
        if col in df.columns:
            neg_sal = df[col] < 0
            neg_sal_count = int(neg_sal.sum())
            if neg_sal_count > 0:
                violations.append(
                    ValidationViolation(
                        rule_name=f"NON_NEGATIVE_{col.upper()}",
                        violation_count=neg_sal_count,
                        sample_indices=df.index[neg_sal][:10].tolist(),
                        description=f"Found {neg_sal_count} records with negative {col}.",
                    )
                )

    # 7. Non-negative deduction components
    deduction_cols = ["pf", "esi", "tds", "other_deductions", "total_deductions"]
    for col in deduction_cols:
        if col in df.columns:
            neg_ded = df[col] < 0
            neg_ded_count = int(neg_ded.sum())
            if neg_ded_count > 0:
                violations.append(
                    ValidationViolation(
                        rule_name=f"NON_NEGATIVE_{col.upper()}",
                        violation_count=neg_ded_count,
                        sample_indices=df.index[neg_ded][:10].tolist(),
                        description=f"Found {neg_ded_count} records with negative {col}.",
                    )
                )

    # 8. Gross Salary Reconciliation
    gross_components = ["basic_salary", "allowances", "overtime_amount", "bonus"]
    if set(gross_components + ["gross_salary"]).issubset(df.columns):
        expected_gross = df[gross_components].sum(axis=1)
        gross_diff = np.abs(df["gross_salary"] - expected_gross)
        gross_mismatch = gross_diff > tolerance
        gross_mis_count = int(gross_mismatch.sum())
        if gross_mis_count > 0:
            violations.append(
                ValidationViolation(
                    rule_name="GROSS_SALARY_RECONCILIATION",
                    violation_count=gross_mis_count,
                    sample_indices=df.index[gross_mismatch][:10].tolist(),
                    description=f"Found {gross_mis_count} records where gross_salary != sum of earnings components.",
                )
            )

    # 9. Total Deductions Reconciliation
    ded_components = ["pf", "esi", "tds", "other_deductions"]
    if set(ded_components + ["total_deductions"]).issubset(df.columns):
        expected_ded = df[ded_components].sum(axis=1)
        ded_diff = np.abs(df["total_deductions"] - expected_ded)
        ded_mismatch = ded_diff > tolerance
        ded_mis_count = int(ded_mismatch.sum())
        if ded_mis_count > 0:
            violations.append(
                ValidationViolation(
                    rule_name="DEDUCTIONS_RECONCILIATION",
                    violation_count=ded_mis_count,
                    sample_indices=df.index[ded_mismatch][:10].tolist(),
                    description=f"Found {ded_mis_count} records where total_deductions != sum of deduction items.",
                )
            )

    # 10. Net Salary Reconciliation
    if {"gross_salary", "total_deductions", "net_salary"}.issubset(df.columns):
        expected_net = df["gross_salary"] - df["total_deductions"]
        net_diff = np.abs(df["net_salary"] - expected_net)
        net_mismatch = net_diff > tolerance
        net_mis_count = int(net_mismatch.sum())
        if net_mis_count > 0:
            violations.append(
                ValidationViolation(
                    rule_name="NET_SALARY_RECONCILIATION",
                    violation_count=net_mis_count,
                    sample_indices=df.index[net_mismatch][:10].tolist(),
                    description=f"Found {net_mis_count} records where net_salary != gross_salary - total_deductions.",
                )
            )

    total_violation_count = sum(v.violation_count for v in violations)
    is_valid = len(violations) == 0

    report = ValidationReport(
        is_valid=is_valid,
        total_records=total_records,
        violation_count=total_violation_count,
        violations=violations,
        summary={
            "total_records": total_records,
            "rules_checked": 10,
            "rules_passed": 10 - len(violations),
            "rules_failed": len(violations),
        },
    )

    if not is_valid and raise_on_error:
        failure_msgs = [f" - {v.rule_name}: {v.description}" for v in violations]
        raise ValueError("Payroll validation failed with errors:\n" + "\n".join(failure_msgs))

    return report


def validate_payroll_dataset_stream(
    data_source: Union[str, Path, Generator[pd.DataFrame, None, None]],
    batch_size: int = 50_000,
    tolerance: float = 0.05,
) -> ValidationReport:
    """Validate a large-scale payroll dataset in streaming batches with minimal RAM overhead.

    Args:
        data_source: Path to Parquet/CSV file or a generator of DataFrame chunks.
        batch_size: Batch size when reading from file.
        tolerance: Float comparison tolerance.

    Returns:
        Aggregated ValidationReport across all batches.
    """
    if isinstance(data_source, (str, Path)):
        batches = iter_payroll_batches(data_source, batch_size=batch_size)
    else:
        batches = data_source

    total_records = 0
    rule_counts: Dict[str, int] = {}
    rule_descriptions: Dict[str, str] = {}
    sample_indices_map: Dict[str, List[int]] = {}

    for batch in batches:
        report = validate_payroll_dataset(batch, tolerance=tolerance, raise_on_error=False)
        total_records += report.total_records

        for v in report.violations:
            rule_counts[v.rule_name] = rule_counts.get(v.rule_name, 0) + v.violation_count
            rule_descriptions[v.rule_name] = v.description
            if v.rule_name not in sample_indices_map:
                sample_indices_map[v.rule_name] = v.sample_indices

    violations = [
        ValidationViolation(
            rule_name=rule,
            violation_count=count,
            sample_indices=sample_indices_map.get(rule, []),
            description=rule_descriptions.get(rule, ""),
        )
        for rule, count in rule_counts.items()
    ]

    total_violations = sum(v.violation_count for v in violations)
    is_valid = len(violations) == 0

    return ValidationReport(
        is_valid=is_valid,
        total_records=total_records,
        violation_count=total_violations,
        violations=violations,
        summary={
            "total_records": total_records,
            "rules_checked": 10,
            "rules_passed": 10 - len(violations),
            "rules_failed": len(violations),
        },
    )


def clean_payroll_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Clean payroll dataset by fixing data types, removing duplicates, and sorting."""
    cleaned = df.copy()
    cleaned = cleaned.drop_duplicates()
    if "employee_id" in cleaned.columns and "payroll_month" in cleaned.columns:
        cleaned = cleaned.drop_duplicates(subset=["employee_id", "payroll_month"], keep="first")
    if "payroll_month" in cleaned.columns and "employee_id" in cleaned.columns:
        cleaned = cleaned.sort_values(by=["payroll_month", "employee_id"]).reset_index(drop=True)
    return cleaned
