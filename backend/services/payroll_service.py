"""Payroll normalization, parsing, validation, and streaming data service (Phase 10)."""

import io
import json
import re
from typing import Any, Dict, Generator, List, Tuple, Union
import pandas as pd
from pydantic import ValidationError

from backend.schemas.payroll import PayrollRecordInput

MONTH_PATTERN = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])$")


class PayrollService:
    """Handles payroll normalization, validation, and multi-format parsing (CSV, JSON, Parquet)."""

    REQUIRED_COLUMNS = [
        "employee_id",
        "payroll_month",
        "basic_salary",
        "gross_salary",
        "net_salary",
    ]

    @classmethod
    def records_to_dataframe(cls, records: List[PayrollRecordInput]) -> pd.DataFrame:
        """Convert a list of validated Pydantic records into a normalized pandas DataFrame."""
        dict_records = [rec.model_dump() for rec in records]
        df = pd.DataFrame(dict_records)
        return cls._normalize_dataframe(df)

    @classmethod
    def parse_csv(cls, file_bytes: bytes) -> pd.DataFrame:
        """Parse raw CSV file content into a validated pandas DataFrame."""
        try:
            df = pd.read_csv(io.BytesIO(file_bytes))
        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {e}") from e

        return cls._validate_and_normalize_raw_df(df)

    @classmethod
    def parse_json_bytes(cls, file_bytes: bytes) -> pd.DataFrame:
        """Parse raw JSON file content into a validated pandas DataFrame."""
        try:
            data = json.loads(file_bytes.decode("utf-8"))
            if isinstance(data, dict) and "records" in data:
                data = data["records"]
            if not isinstance(data, list):
                raise ValueError("JSON payroll payload must be an array of records.")
            df = pd.DataFrame(data)
        except Exception as e:
            raise ValueError(f"Failed to parse JSON file: {e}") from e

        return cls._validate_and_normalize_raw_df(df)

    @classmethod
    def parse_parquet(cls, file_bytes: bytes) -> pd.DataFrame:
        """Parse raw Parquet file content into a validated pandas DataFrame."""
        try:
            df = pd.read_parquet(io.BytesIO(file_bytes))
        except Exception as e:
            raise ValueError(f"Failed to parse Parquet file: {e}") from e

        return cls._validate_and_normalize_raw_df(df)

    @classmethod
    def _validate_and_normalize_raw_df(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Validate presence of required columns, schema types, and values."""
        if len(df) == 0:
            raise ValueError("Payroll dataset is empty (0 records).")

        missing = [col for col in cls.REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required payroll columns: {missing}")

        # Check for empty employee IDs
        emp_ids = df["employee_id"].astype(str).str.strip()
        if (emp_ids == "").any() or (emp_ids.str.lower() == "nan").any():
            raise ValueError("Found empty or missing employee_id in payroll records.")

        # Validate salary fields are not strictly negative
        for sal_col in ["basic_salary", "gross_salary", "net_salary"]:
            vals = pd.to_numeric(df[sal_col], errors="coerce")
            if (vals < 0).any():
                raise ValueError(f"Invalid payroll data: negative values detected in '{sal_col}'.")

        # Validate working days bounds if present
        if "working_days" in df.columns:
            w_days = pd.to_numeric(df["working_days"], errors="coerce").fillna(26)
            if (w_days < 1).any() or (w_days > 31).any():
                raise ValueError("Working days must be between 1 and 31.")

        if "present_days" in df.columns:
            p_days = pd.to_numeric(df["present_days"], errors="coerce").fillna(26)
            if (p_days < 0).any():
                raise ValueError("Present days cannot be negative.")

        return cls._normalize_dataframe(df)

    @classmethod
    def _normalize_dataframe(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure standard types and fill default numerical values."""
        res = df.copy()

        # Strings
        res["employee_id"] = res["employee_id"].astype(str).str.strip()
        res["payroll_month"] = res["payroll_month"].astype(str).str.strip()
        res["department"] = res.get("department", "General").fillna("General").astype(str)
        res["designation"] = res.get("designation", "Staff").fillna("Staff").astype(str)
        res["location"] = res.get("location", "INDIA").fillna("INDIA").astype(str)

        # Numerics
        num_defaults = {
            "basic_salary": 0.0,
            "gross_salary": 0.0,
            "net_salary": 0.0,
            "allowances": 0.0,
            "bonus": 0.0,
            "total_deductions": 0.0,
            "pf_deduction": 0.0,
            "esi": 0.0,
            "professional_tax": 0.0,
            "working_days": 26,
            "present_days": 26,
            "leave_days": 0,
            "overtime_hours": 0.0,
        }

        for col, default_val in num_defaults.items():
            if col not in res.columns:
                res[col] = default_val
            else:
                res[col] = pd.to_numeric(res[col], errors="coerce").fillna(default_val)

        return res
