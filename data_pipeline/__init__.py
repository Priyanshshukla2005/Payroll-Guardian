"""Data engineering, generation, anomaly injection, and validation pipeline."""

from data_pipeline.cleaner import (
    ValidationReport,
    ValidationViolation,
    clean_payroll_dataset,
    validate_payroll_dataset,
    validate_payroll_dataset_stream,
)
from data_pipeline.company_shift import generate_shifted_company_dataset
from data_pipeline.generator import (
    SyntheticEmployeePopulation,
    generate_population_month_slice,
    generate_synthetic_payroll_chunks,
    generate_synthetic_payroll_dataset,
)
from data_pipeline.hard_cases import HardCaseGenerator
from data_pipeline.injector import PayrollAnomalyInjector
from data_pipeline.loader import (
    EXPECTED_SCHEMA_COLUMNS,
    NUMERIC_COLUMNS,
    iter_payroll_batches,
    load_payroll_data,
    save_payroll_data,
)

__all__ = [
    "load_payroll_data",
    "save_payroll_data",
    "iter_payroll_batches",
    "EXPECTED_SCHEMA_COLUMNS",
    "NUMERIC_COLUMNS",
    "validate_payroll_dataset",
    "validate_payroll_dataset_stream",
    "clean_payroll_dataset",
    "ValidationReport",
    "ValidationViolation",
    "SyntheticEmployeePopulation",
    "generate_population_month_slice",
    "generate_synthetic_payroll_dataset",
    "generate_synthetic_payroll_chunks",
    "PayrollAnomalyInjector",
    "HardCaseGenerator",
    "generate_shifted_company_dataset",
]
