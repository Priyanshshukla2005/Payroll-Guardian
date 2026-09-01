"""Performance and scalability benchmarking script for AI Payroll Guardian (Phase 10).

Benchmarks 100, 1,000, 10,000, and 100,000 records across:
- Data validation
- Feature engineering
- ML inference
- Total pipeline latency
- Peak memory consumption (MB)
- Throughput (records/second)
"""

from datetime import datetime
import json
import os
from pathlib import Path
import platform
import sys
import time
import tracemalloc
import numpy as np
import pandas as pd
import psutil

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database.repository import DatabaseAnalysisRepository
from backend.dependencies.services import ModelManager
from backend.services.analysis_service import AnalysisService
from backend.services.payroll_service import PayrollService


def generate_benchmark_records(n_records: int) -> pd.DataFrame:
    """Generate deterministic synthetic payroll DataFrame of size n_records."""
    np.random.seed(42)
    depts = ["Engineering", "Operations", "Sales", "Finance", "HR", "Marketing", "Support"]
    desigs = ["Associate", "Specialist", "Senior", "Lead", "Manager"]
    locs = ["Bengaluru", "Mumbai", "Delhi-NCR", "Hyderabad", "Pune"]

    basic_salaries = np.random.uniform(25000.0, 180000.0, size=n_records)
    allowances = basic_salaries * np.random.uniform(0.20, 0.45, size=n_records)
    gross_salaries = basic_salaries + allowances
    pf_deductions = basic_salaries * 0.12
    pt_deductions = np.full(n_records, 200.0)
    total_deductions = pf_deductions + pt_deductions
    net_salaries = gross_salaries - total_deductions

    emp_ids = [f"EMP_BENCH_{i:06d}" for i in range(1, n_records + 1)]
    dept_choices = np.random.choice(depts, size=n_records)
    desig_choices = np.random.choice(desigs, size=n_records)
    loc_choices = np.random.choice(locs, size=n_records)

    df = pd.DataFrame({
        "employee_id": emp_ids,
        "payroll_month": "2024-06",
        "department": dept_choices,
        "designation": desig_choices,
        "location": loc_choices,
        "basic_salary": np.round(basic_salaries, 2),
        "allowances": np.round(allowances, 2),
        "gross_salary": np.round(gross_salaries, 2),
        "pf_deduction": np.round(pf_deductions, 2),
        "total_deductions": np.round(total_deductions, 2),
        "net_salary": np.round(net_salaries, 2),
        "working_days": 26,
        "present_days": 26,
        "leave_days": 0,
        "overtime_hours": 0.0,
        "salary_change_percentage": 0.0,
    })
    return df


def run_benchmarks():
    """Execute end-to-end performance benchmarks."""
    batch_sizes = [100, 1_000, 10_000, 100_000]
    results = []

    print("=" * 70, flush=True)
    print("AI PAYROLL GUARDIAN — PHASE 10 PERFORMANCE BENCHMARK", flush=True)
    print(f"System: {platform.system()} {platform.release()} ({platform.machine()})", flush=True)
    print(f"CPU: {platform.processor()} ({os.cpu_count()} logical cores)", flush=True)
    print(f"RAM: {psutil.virtual_memory().total / (1024**3):.1f} GB Total", flush=True)
    print(f"Python: {platform.python_version()}", flush=True)
    print("=" * 70, flush=True)

    model_mgr = ModelManager.get_instance()
    model_mgr.initialize()
    repo = DatabaseAnalysisRepository()
    analysis_service = AnalysisService(model_manager=model_mgr, repository=repo)

    for batch_size in batch_sizes:
        print(f"\n[Benchmarking Batch: {batch_size:,} records] Generating dataset...", flush=True)
        df_bench = generate_benchmark_records(batch_size)

        tracemalloc.start()
        t_start = time.perf_counter()

        # Step 1: Validation & Normalization
        t_val_start = time.perf_counter()
        df_norm = PayrollService._normalize_dataframe(df_bench)
        val_time_ms = (time.perf_counter() - t_val_start) * 1000.0

        # Step 2: Feature Engineering & Detection
        t_ml_start = time.perf_counter()
        if batch_size <= 10_000:
            detection_results = analysis_service.detection_service.detect_anomalies(df_norm)
            feat_time_ms = getattr(analysis_service.detection_service, "last_feature_time_ms", 0.0)
            infer_time_ms = getattr(analysis_service.detection_service, "last_detection_time_ms", 0.0)
        else:
            # Chunked processing for 100k to bound memory and CPU latency
            chunk_size = 20_000
            feat_time_ms = 0.0
            infer_time_ms = 0.0
            for start_idx in range(0, len(df_norm), chunk_size):
                chunk = df_norm.iloc[start_idx : start_idx + chunk_size]
                _ = analysis_service.detection_service.detect_anomalies(chunk)
                feat_time_ms += getattr(analysis_service.detection_service, "last_feature_time_ms", 0.0)
                infer_time_ms += getattr(analysis_service.detection_service, "last_detection_time_ms", 0.0)

        total_time_s = time.perf_counter() - t_start
        total_time_ms = total_time_s * 1000.0
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        throughput = batch_size / total_time_s if total_time_s > 0 else 0.0
        peak_ram_mb = peak_mem / (1024 * 1024)

        result_row = {
            "batch_size": batch_size,
            "validation_ms": round(val_time_ms, 2),
            "feature_eng_ms": round(feat_time_ms, 2),
            "ml_inference_ms": round(infer_time_ms, 2),
            "total_analysis_ms": round(total_time_ms, 2),
            "throughput_rec_per_sec": round(throughput, 1),
            "peak_ram_mb": round(peak_ram_mb, 2),
        }
        results.append(result_row)

        print(f" -> Validation: {val_time_ms:.1f}ms", flush=True)
        print(f" -> Feature Engineering: {feat_time_ms:.1f}ms", flush=True)
        print(f" -> ML Inference: {infer_time_ms:.1f}ms", flush=True)
        print(f" -> Total Latency: {total_time_ms:.1f}ms ({total_time_s:.2f}s)", flush=True)
        print(f" -> Throughput: {throughput:,.1f} records/sec", flush=True)
        print(f" -> Peak Memory: {peak_ram_mb:.2f} MB", flush=True)

    print("\n" + "=" * 70, flush=True)
    print("FINAL BENCHMARK SUMMARY TABLE", flush=True)
    print("=" * 70, flush=True)
    print(f"| {'Batch Size':>10} | {'Throughput (rec/s)':>18} | {'Total Latency':>15} | {'Peak RAM':>12} |", flush=True)
    print(f"|{'-'*12}|{'-'*20}|{'-'*17}|{'-'*14}|", flush=True)
    for r in results:
        print(
            f"| {r['batch_size']:>10,} | {r['throughput_rec_per_sec']:>18,.1f} | "
            f"{r['total_analysis_ms']:>13,.1f}ms | {r['peak_ram_mb']:>9.2f} MB |",
            flush=True,
        )
    print("=" * 70, flush=True)

    # Save benchmark results to JSON
    output_dir = PROJECT_ROOT / "docs" / "benchmarks"
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "benchmark_results_phase10.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "environment": {
                    "os": f"{platform.system()} {platform.release()}",
                    "cpu": platform.processor(),
                    "cores": os.cpu_count(),
                    "ram_gb": round(psutil.virtual_memory().total / (1024**3), 1),
                    "python": platform.python_version(),
                },
                "results": results,
            },
            f,
            indent=2,
        )
    print(f"\nBenchmark results saved to {output_dir / 'benchmark_results_phase10.json'}", flush=True)


if __name__ == "__main__":
    run_benchmarks()
