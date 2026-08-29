"""Payroll data ingestion, batch streaming, and multi-format storage utilities."""

from pathlib import Path
from typing import Generator, List, Optional, Union
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


EXPECTED_SCHEMA_COLUMNS = [
    "employee_id",
    "payroll_month",
    "department",
    "designation",
    "joining_date",
    "employment_status",
    "location",
    "working_days",
    "present_days",
    "leave_days",
    "basic_salary",
    "allowances",
    "overtime_hours",
    "overtime_amount",
    "bonus",
    "gross_salary",
    "pf",
    "esi",
    "tds",
    "other_deductions",
    "total_deductions",
    "net_salary",
]

NUMERIC_COLUMNS = [
    "working_days",
    "present_days",
    "leave_days",
    "basic_salary",
    "allowances",
    "overtime_hours",
    "overtime_amount",
    "bonus",
    "gross_salary",
    "pf",
    "esi",
    "tds",
    "other_deductions",
    "total_deductions",
    "net_salary",
]


def load_payroll_data(
    filepath: Union[str, Path],
    parse_dates: bool = True,
    validate_schema: bool = True,
    columns: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Load payroll dataset from CSV or Parquet file with automatic format detection.

    Args:
        filepath: Path to CSV or Parquet file.
        parse_dates: Whether to parse date columns.
        validate_schema: Whether to verify required columns exist.
        columns: Optional list of specific columns to load (column projection for fast I/O).

    Returns:
        pd.DataFrame containing the payroll records.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Payroll data file not found at: {path.resolve()}")

    if path.suffix.lower() == ".parquet":
        df = pd.read_parquet(path, columns=columns)
    else:
        df = pd.read_csv(path, usecols=columns)

    if validate_schema and columns is None:
        missing = [col for col in EXPECTED_SCHEMA_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(f"Payroll dataset missing mandatory columns: {missing}")

    if parse_dates and "joining_date" in df.columns:
        df["joining_date"] = pd.to_datetime(df["joining_date"], errors="coerce")

    # Enforce numeric types
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def iter_payroll_batches(
    filepath: Union[str, Path],
    batch_size: int = 50_000,
    columns: Optional[List[str]] = None,
) -> Generator[pd.DataFrame, None, None]:
    """Stream payroll data in memory-efficient chunks without loading full dataset into RAM.

    Args:
        filepath: Path to Parquet or CSV file.
        batch_size: Number of records per chunk.
        columns: Optional column projection.

    Yields:
        pd.DataFrame chunks.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Payroll data file not found at: {path.resolve()}")

    if path.suffix.lower() == ".parquet":
        parquet_file = pq.ParquetFile(path)
        for batch in parquet_file.iter_batches(batch_size=batch_size, columns=columns):
            yield batch.to_pandas()
    else:
        for chunk in pd.read_csv(path, chunksize=batch_size, usecols=columns):
            yield chunk


def save_payroll_data(
    df: pd.DataFrame,
    filepath: Union[str, Path],
    index: bool = False,
    compression: str = "snappy",
) -> Path:
    """Save payroll dataframe to disk as CSV or Parquet based on file extension.

    Args:
        df: Dataframe to persist.
        filepath: Target output file path (.parquet or .csv).
        index: Whether to include dataframe index.
        compression: Parquet compression codec ('snappy', 'zstd', 'gzip').

    Returns:
        Path of the saved file.
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.suffix.lower() == ".parquet":
        table = pa.Table.from_pandas(df, preserve_index=index)
        pq.write_table(table, path, compression=compression)
    else:
        df.to_csv(path, index=index)

    return path
