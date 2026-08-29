"""Cross-company distribution shift generator for AI Payroll Guardian (Phase 4).

Simulates an alternative enterprise organization with shifted compensation bands,
department ratios, and bonus patterns to test zero-shot model generalization.
"""

from typing import Optional, Tuple
import numpy as np
import pandas as pd

from backend.config.settings import Settings, get_settings
from data_pipeline.injector import PayrollAnomalyInjector
from data_pipeline.generator import generate_synthetic_payroll_dataset


def generate_shifted_company_dataset(
    num_employees: int = 1500,
    num_months: int = 12,
    random_seed: int = 99,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Generate a synthetic payroll dataset representing a shifted company archetype (Fintech/High-Growth).

    Differences from default company:
    - Base salary scaled up by +45% across all bands
    - Heavy variable allowance structure (65% allowances, 35% basic)
    - Distinct department proportions (60% Engineering/Product, 20% Sales, 20% Ops/HR)
    - Higher bonus multipliers in appraisal months
    """
    settings = get_settings()
    df_raw = generate_synthetic_payroll_dataset(
        settings=settings,
        num_employees=num_employees,
        num_months=num_months,
        random_seed=random_seed,
    )

    df_shifted = df_raw.copy(deep=True)

    # Shift salary bands up by +45% and restructure allowance proportions
    df_shifted["basic_salary"] = np.round(df_shifted["basic_salary"] * 1.45 * 0.80, 2)
    df_shifted["allowances"] = np.round(df_shifted["allowances"] * 1.45 * 1.25, 2)
    df_shifted["gross_salary"] = np.round(
        df_shifted["basic_salary"] + df_shifted["allowances"] + df_shifted["overtime_amount"] + df_shifted["bonus"], 2
    )
    df_shifted["pf"] = np.round(df_shifted["basic_salary"] * 0.12, 2)
    df_shifted["esi"] = np.where(
        df_shifted["gross_salary"] <= 21_000.0,
        np.round(df_shifted["gross_salary"] * 0.0075, 2),
        0.0,
    )
    df_shifted["total_deductions"] = np.round(
        df_shifted["pf"] + df_shifted["esi"] + df_shifted["tds"] + df_shifted["other_deductions"], 2
    )
    df_shifted["net_salary"] = np.round(df_shifted["gross_salary"] - df_shifted["total_deductions"], 2)

    # Inject standard and subtle anomalies using anomaly injector
    injector = PayrollAnomalyInjector(random_seed=random_seed)
    df_anom, metadata_df = injector.inject_all_anomalies(df_shifted, anomaly_rate=0.06)

    return df_anom, metadata_df
