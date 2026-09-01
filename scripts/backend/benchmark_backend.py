"""Scalability and throughput benchmarking script for the backend API service (Phase 7).

Benchmarks latency, throughput (records/sec), and peak memory usage across
100, 1,000, and 10,000 records.
"""

import os
import sys
import time
import tracemalloc
from pathlib import Path
import pandas as pd
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.dependencies.services import ModelManager
from backend.main import create_app


def generate_benchmark_records(n_records: int) -> list:
    """Generate n_records synthetic payroll records in memory."""
    records = []
    for i in range(n_records):
        emp_id = f"EMP_BENCH_{i:06d}"
        basic = 30000.0 + (i % 50) * 1000.0
        # Inject ~5% anomalies
        is_anom = (i % 20 == 0)
        pf = 1000.0 if is_anom else 0.12 * basic
        gross = basic * 1.5
        net = gross - pf - 200.0

        records.append({
            "employee_id": emp_id,
            "payroll_month": "2024-06",
            "basic_salary": basic,
            "gross_salary": gross,
            "net_salary": net,
            "allowances": basic * 0.5,
            "bonus": 0.0,
            "total_deductions": pf + 200.0,
            "pf_deduction": pf,
            "esi": 0.0,
            "professional_tax": 200.0,
            "working_days": 26,
            "present_days": 26,
            "leave_days": 0,
            "overtime_hours": 0.0,
            "department": "Engineering" if i % 2 == 0 else "Operations",
            "designation": "Staff",
            "location": "KARNATAKA",
        })
    return records


def run_benchmark():
    print("=" * 80)
    print("  AI PAYROLL GUARDIAN — PHASE 7 BACKEND PERFORMANCE BENCHMARK")
    print("=" * 80)

    model_mgr = ModelManager.get_instance()
    model_mgr.initialize()
    app = create_app()

    bench_sizes = [100, 1000, 10000]
    results = []

    with TestClient(app) as client:
        for size in bench_sizes:
            print(f"\n[BENCHMARK] Generating {size:,} payroll records...")
            records = generate_benchmark_records(size)

            tracemalloc.start()
            t0 = time.perf_counter()

            response = client.post("/api/v1/payroll/analyze", json={"records": records})

            total_sec = time.perf_counter() - t0
            current_mem, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            assert response.status_code == 200, f"Error: {response.text}"
            data = response.json()
            flagged = data["summary"]["records_flagged"]
            records_per_sec = size / total_sec
            peak_mb = peak_mem / (1024 * 1024)

            res_item = {
                "records": size,
                "latency_sec": round(total_sec, 3),
                "throughput_rps": round(records_per_sec, 1),
                "peak_memory_mb": round(peak_mb, 2),
                "flagged_anomalies": flagged,
            }
            results.append(res_item)

            print(f"  -> Records Analyzed : {size:,}")
            print(f"  -> Total Latency    : {total_sec:.3f} s")
            print(f"  -> Throughput       : {records_per_sec:,.1f} records/sec")
            print(f"  -> Peak Memory      : {peak_mb:.2f} MB")
            print(f"  -> Flagged Anomalies: {flagged:,}")

    print("\n" + "=" * 80)
    print("  BENCHMARK SUMMARY TABLE")
    print("=" * 80)
    print(f"{'Batch Size':<12} | {'Latency (s)':<12} | {'Throughput (rec/s)':<20} | {'Peak Memory (MB)':<18}")
    print("-" * 72)
    for r in results:
        print(f"{r['records']:<12,d} | {r['latency_sec']:<12.3f} | {r['throughput_rps']:<20,.1f} | {r['peak_memory_mb']:<18.2f}")
    print("=" * 80)


if __name__ == "__main__":
    run_benchmark()
