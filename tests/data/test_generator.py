"""Tests for synthetic population and payroll history generation."""

import pandas as pd
import pytest
from backend.config.settings import DatasetScale, get_settings
from data_pipeline.generator import (
    SyntheticEmployeePopulation,
    generate_synthetic_payroll_chunks,
    generate_synthetic_payroll_dataset,
)


def test_population_generation_size_and_attributes():
    """Verify synthetic population size and persistent attributes."""
    settings = get_settings()
    pop_gen = SyntheticEmployeePopulation(settings=settings, random_seed=42)
    pop = pop_gen.generate_population(num_employees=500)

    assert len(pop) == 500
    expected_cols = {
        "employee_id",
        "department",
        "designation",
        "location",
        "gender",
        "joining_date",
        "employment_status",
        "base_monthly_salary",
        "increment_month",
        "overtime_eligible",
    }
    assert expected_cols.issubset(pop.columns)
    assert pop["employee_id"].nunique() == 500
    assert (pop["base_monthly_salary"] > 0).all()


def test_dataset_size_and_multi_month_continuity():
    """Verify generation across multiple months for all employees."""
    settings = get_settings()
    n_emp = 100
    n_months = 12
    df = generate_synthetic_payroll_dataset(
        settings=settings,
        num_employees=n_emp,
        num_months=n_months,
        random_seed=42,
    )

    assert len(df) == n_emp * n_months
    assert df["employee_id"].nunique() == n_emp
    assert df["payroll_month"].nunique() == n_months


def test_generation_reproducibility():
    """Verify identical random seed produces identical dataset."""
    settings = get_settings()
    df1 = generate_synthetic_payroll_dataset(
        settings=settings,
        num_employees=50,
        num_months=6,
        random_seed=123,
    )
    df2 = generate_synthetic_payroll_dataset(
        settings=settings,
        num_employees=50,
        num_months=6,
        random_seed=123,
    )

    pd.testing.assert_frame_equal(df1, df2)


def test_chunked_streaming_generation():
    """Verify that chunked streaming produces identical total records and correct batching."""
    settings = get_settings()
    n_emp = 150
    n_months = 6
    chunk_size = 50

    chunks = list(
        generate_synthetic_payroll_chunks(
            settings=settings,
            num_employees=n_emp,
            num_months=n_months,
            chunk_size_employees=chunk_size,
            random_seed=42,
        )
    )

    assert len(chunks) == 3  # 150 employees / 50 per chunk = 3 chunks
    for c in chunks:
        assert len(c) == 50 * n_months

    df_concat = pd.concat(chunks, ignore_index=True)
    assert len(df_concat) == n_emp * n_months
    assert df_concat["employee_id"].nunique() == n_emp


def test_employee_persistent_attributes():
    """Verify employee department and joining date remain consistent across months."""
    settings = get_settings()
    df = generate_synthetic_payroll_dataset(
        settings=settings,
        num_employees=100,
        num_months=12,
        random_seed=42,
    )

    # Department per employee should have exactly 1 unique value across 12 months
    dept_counts = df.groupby("employee_id")["department"].nunique()
    assert (dept_counts == 1).all()

    # Joining date per employee should be constant
    join_counts = df.groupby("employee_id")["joining_date"].nunique()
    assert (join_counts == 1).all()


def test_salary_hierarchy_distribution():
    """Verify that average salary follows designation hierarchy."""
    settings = get_settings()
    df = generate_synthetic_payroll_dataset(
        settings=settings,
        num_employees=500,
        num_months=1,
        random_seed=42,
    )

    avg_sal_by_desig = df.groupby("designation")["basic_salary"].mean()
    assert avg_sal_by_desig["Intern"] < avg_sal_by_desig["Junior"]
    assert avg_sal_by_desig["Junior"] < avg_sal_by_desig["Mid-level"]
    assert avg_sal_by_desig["Mid-level"] < avg_sal_by_desig["Senior"]
    assert avg_sal_by_desig["Senior"] < avg_sal_by_desig["Manager"]
    assert avg_sal_by_desig["Manager"] < avg_sal_by_desig["Director"]


def test_scale_presets():
    """Verify scale preset settings configuration."""
    dev_settings = get_settings(scale=DatasetScale.DEV)
    assert dev_settings.num_employees == 10_000
    assert dev_settings.num_months == 12

    main_settings = get_settings(scale=DatasetScale.MAIN)
    assert main_settings.num_employees == 100_000
    assert main_settings.num_months == 24

    stress_settings = get_settings(scale=DatasetScale.STRESS)
    assert stress_settings.num_employees == 500_000
    assert stress_settings.num_months == 36
