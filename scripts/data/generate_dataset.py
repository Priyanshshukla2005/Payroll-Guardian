"""CLI Script to generate scalable, reproducible synthetic clean and anomalous payroll datasets.

Supports three scale presets:
    - dev    : 10,000 employees x 12 months  (~120,000 records)
    - main   : 100,000 employees x 24 months (~2,400,000 records)
    - stress : 500,000 employees x 36 months (~18,000,000 records)
    - custom : user-defined --employees N --months M

Usage:
    python scripts/generate_dataset.py --scale dev
    python scripts/generate_dataset.py --scale main --format parquet
    python scripts/generate_dataset.py --employees 100000 --months 24 --format parquet
"""

import argparse
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from backend.config.settings import (
    SCALE_PRESETS,
    DatasetScale,
    Settings,
    get_settings,
)
from ai.features.payroll_features import compute_payroll_features
from data_pipeline.loader import save_payroll_data
from data_pipeline.cleaner import validate_payroll_dataset
from data_pipeline.injector import PayrollAnomalyInjector
from data_pipeline.generator import generate_synthetic_payroll_chunks


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI Payroll Guardian - Large-Scale Synthetic Payroll Dataset Generator"
    )
    parser.add_argument(
        "--scale",
        type=str,
        default="dev",
        choices=["dev", "main", "stress", "custom"],
        help="Dataset scale preset: dev (120k), main (2.4M), stress (18M), or custom (default: dev)",
    )
    parser.add_argument(
        "--employees",
        "--num-employees",
        type=int,
        default=None,
        help="Override employee count (e.g. 100000)",
    )
    parser.add_argument(
        "--months",
        "--num-months",
        type=int,
        default=None,
        help="Override payroll history months (e.g. 24)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible generation (default: 42)",
    )
    parser.add_argument(
        "--anomaly-rate",
        type=float,
        default=0.05,
        help="Target proportion of anomalous records (default: 0.05 / 5%%)",
    )
    parser.add_argument(
        "--format",
        type=str,
        default=None,
        choices=["parquet", "csv", "both"],
        help="Output file format: 'parquet', 'csv', or 'both' (defaults to 'both' for dev, 'parquet' for main/stress)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=50_000,
        help="Employee batch size for streaming generation (default: 50,000)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Custom output directory (default: data/synthetic)",
    )
    parser.add_argument(
        "--compute-features",
        action="store_true",
        help="Compute and save feature-engineered dataset",
    )
    return parser.parse_args()


def format_bytes(num_bytes: int) -> str:
    """Format bytes to human readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:3.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def main():
    args = parse_args()

    # Determine scale and parameters
    scale_enum = DatasetScale(args.scale)
    if scale_enum in SCALE_PRESETS:
        default_emp, default_months, scale_desc = SCALE_PRESETS[scale_enum]
    else:
        default_emp, default_months, scale_desc = (10_000, 12, "Custom Dataset Scale")

    num_employees = args.employees if args.employees is not None else default_emp
    num_months = args.months if args.months is not None else default_months

    # Default output format
    if args.format is not None:
        save_format = args.format
    elif scale_enum == DatasetScale.DEV and num_employees <= 10_000:
        save_format = "both"
    else:
        save_format = "parquet"

    settings = get_settings()
    out_dir = Path(args.output_dir) if args.output_dir else settings.synthetic_data_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    expected_total_records = num_employees * num_months

    print("=" * 75)
    print("  AI PAYROLL GUARDIAN — HIGH-PERFORMANCE DATASET GENERATION PIPELINE")
    print("=" * 75)
    print(f"Scale Preset     : {scale_enum.value.upper()} ({scale_desc})")
    print(f"Target Employees : {num_employees:,}")
    print(f"Target Months    : {num_months}")
    print(f"Expected Records : {expected_total_records:,}")
    print(f"Random Seed      : {args.seed}")
    print(f"Anomaly Rate     : {args.anomaly_rate * 100:.1f}%")
    print(f"Chunk Batch Size : {args.chunk_size:,} employees / batch")
    print(f"Storage Format   : {save_format.upper()}")
    print(f"Output Directory : {out_dir.resolve()}")
    print("-" * 75)

    tracemalloc.start()
    pipeline_start = time.time()

    # Streaming Generation and Processing Setup
    clean_parquet_path = out_dir / "clean_payroll.parquet"
    anom_parquet_path = out_dir / "anomalous_payroll.parquet"
    meta_parquet_path = out_dir / "anomaly_metadata.parquet"
    clean_csv_path = out_dir / "clean_payroll.csv"
    anom_csv_path = out_dir / "anomalous_payroll.csv"
    meta_csv_path = out_dir / "anomaly_metadata.csv"

    # Parquet writers for streaming
    clean_writer = None
    anom_writer = None
    meta_writer = None

    clean_dfs_for_csv = []
    anom_dfs_for_csv = []
    meta_dfs_for_csv = []

    total_clean_records = 0
    total_anom_records = 0
    total_metadata_records = 0
    total_anom_flagged = 0
    anomaly_type_counts: dict = {}

    injector = PayrollAnomalyInjector(random_seed=args.seed)

    print("\n[1/4] Streaming Generation & Ingestion...")
    t_gen_start = time.time()

    chunks = generate_synthetic_payroll_chunks(
        settings=settings,
        num_employees=num_employees,
        num_months=num_months,
        chunk_size_employees=args.chunk_size,
        random_seed=args.seed,
    )

    chunk_idx = 0
    for chunk_clean in chunks:
        chunk_idx += 1
        n_clean = len(chunk_clean)
        total_clean_records += n_clean

        # Validate clean chunk
        clean_report = validate_payroll_dataset(chunk_clean, raise_on_error=False)
        if not clean_report.is_valid:
            print(f"      ERROR: Clean batch #{chunk_idx} failed validation: {clean_report.violation_count} errors.")
            sys.exit(1)

        # Inject anomalies into chunk copy
        chunk_anom, chunk_meta = injector.inject_all_anomalies(
            df_clean=chunk_clean,
            anomaly_rate=args.anomaly_rate,
        )

        n_anom = len(chunk_anom)
        total_anom_records += n_anom
        total_metadata_records += len(chunk_meta)
        total_anom_flagged += int((chunk_anom["is_anomaly"] == 1).sum())

        for atype, cnt in chunk_meta["anomaly_type"].value_counts().items():
            anomaly_type_counts[atype] = anomaly_type_counts.get(atype, 0) + cnt

        # Parquet Streaming Write
        if save_format in ["parquet", "both"]:
            clean_table = pa.Table.from_pandas(chunk_clean, preserve_index=False)
            anom_table = pa.Table.from_pandas(chunk_anom, preserve_index=False)

            if clean_writer is None:
                clean_writer = pq.ParquetWriter(clean_parquet_path, clean_table.schema, compression="snappy")
                anom_writer = pq.ParquetWriter(anom_parquet_path, anom_table.schema, compression="snappy")

            clean_writer.write_table(clean_table)
            anom_writer.write_table(anom_table)

            if len(chunk_meta) > 0:
                meta_table = pa.Table.from_pandas(chunk_meta, preserve_index=False)
                if meta_writer is None:
                    meta_writer = pq.ParquetWriter(meta_parquet_path, meta_table.schema, compression="snappy")
                meta_writer.write_table(meta_table)

        # CSV Collect (if both or csv)
        if save_format in ["csv", "both"]:
            clean_dfs_for_csv.append(chunk_clean)
            anom_dfs_for_csv.append(chunk_anom)
            meta_dfs_for_csv.append(chunk_meta)

        records_so_far = total_clean_records
        elapsed_so_far = time.time() - t_gen_start
        throughput_so_far = records_so_far / max(elapsed_so_far, 0.001)
        print(f"      Processed Batch #{chunk_idx}: {records_so_far:,} / {expected_total_records:,} records ({records_so_far/expected_total_records*100:.1f}%) | Throughput: {throughput_so_far:,.0f} rec/s", end="\r")

    # Close Parquet writers
    if clean_writer:
        clean_writer.close()
    if anom_writer:
        anom_writer.close()
    if meta_writer:
        meta_writer.close()

    t_gen_total = time.time() - t_gen_start
    overall_throughput = total_clean_records / max(t_gen_total, 0.001)
    print(f"\n      Generation & Anomaly Injection Complete: {total_clean_records:,} clean records in {t_gen_total:.2f}s ({overall_throughput:,.0f} rec/s).")

    # CSV write if requested
    if save_format in ["csv", "both"]:
        print("\n[2/4] Writing CSV artifacts...")
        t_csv = time.time()
        pd.concat(clean_dfs_for_csv, ignore_index=True).to_csv(clean_csv_path, index=False)
        pd.concat(anom_dfs_for_csv, ignore_index=True).to_csv(anom_csv_path, index=False)
        if meta_dfs_for_csv:
            pd.concat(meta_dfs_for_csv, ignore_index=True).to_csv(meta_csv_path, index=False)
        print(f"      CSV artifacts written in {time.time() - t_csv:.2f}s.")

    # Optional Feature Engineering
    if args.compute_features:
        print("\n[3/4] Running Feature Engineering Pipeline...")
        t_feat = time.time()
        # Compute on sample or streaming
        sample_df = pd.read_parquet(anom_parquet_path) if save_format in ["parquet", "both"] else pd.read_csv(anom_csv_path)
        sample_features = compute_payroll_features(sample_df)
        feat_out_path = out_dir / ("features_payroll.parquet" if save_format in ["parquet", "both"] else "features_payroll.csv")
        save_payroll_data(sample_features, feat_out_path)
        print(f"      Engineered {len(sample_features.columns)} features ({len(sample_features):,} rows) in {time.time() - t_feat:.2f}s.")
    else:
        print("\n[3/4] Feature Engineering Pipeline ready (use --compute-features flag to materialize feature table).")

    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    pipeline_total_time = time.time() - pipeline_start

    # Final Telemetry & Summary
    print("\n" + "=" * 75)
    print("  DATASET GENERATION & BENCHMARK SUMMARY")
    print("=" * 75)
    print(f"Scale Mode          : {scale_enum.value.upper()}")
    print(f"Clean Records       : {total_clean_records:,}")
    print(f"Anomalous Records   : {total_anom_records:,}")
    print(f"Normal Records (0)  : {total_anom_records - total_anom_flagged:,} ({(total_anom_records - total_anom_flagged)/total_anom_records*100:.2f}%)")
    print(f"Anomaly Records (1) : {total_anom_flagged:,} ({total_anom_flagged/total_anom_records*100:.2f}%)")
    print(f"Audit Log Entries   : {total_metadata_records:,}")
    print(f"Peak RAM Usage      : {format_bytes(peak_mem)}")
    print(f"Total Throughput    : {overall_throughput:,.0f} records / second")
    print(f"Total Pipeline Time : {pipeline_total_time:.2f} seconds")

    print("\nAnomaly Breakdown by Type:")
    for atype, cnt in sorted(anomaly_type_counts.items(), key=lambda x: -x[1]):
        print(f"  - {atype:<30}: {cnt:>6,} ({cnt/total_metadata_records*100:>5.1f}%)")

    print("\nGenerated Artifacts & File Sizes:")
    if save_format in ["parquet", "both"]:
        print(f"  [Parquet] Clean Data     : {clean_parquet_path} ({format_bytes(clean_parquet_path.stat().st_size)})")
        print(f"  [Parquet] Anomalous Data : {anom_parquet_path} ({format_bytes(anom_parquet_path.stat().st_size)})")
        if meta_parquet_path.exists():
            print(f"  [Parquet] Audit Metadata : {meta_parquet_path} ({format_bytes(meta_parquet_path.stat().st_size)})")
    if save_format in ["csv", "both"]:
        print(f"  [CSV]     Clean Data     : {clean_csv_path} ({format_bytes(clean_csv_path.stat().st_size)})")
        print(f"  [CSV]     Anomalous Data : {anom_csv_path} ({format_bytes(anom_csv_path.stat().st_size)})")
        if meta_csv_path.exists():
            print(f"  [CSV]     Audit Metadata : {meta_csv_path} ({format_bytes(meta_csv_path.stat().st_size)})")

    print("=" * 75)


if __name__ == "__main__":
    main()
