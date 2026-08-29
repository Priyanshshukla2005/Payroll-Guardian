"""Configuration settings, presets, and constants for AI Payroll Guardian.

Defines dataset generation parameters, scale presets (Dev 120k, Main 2.4M, Stress 18M),
department salary hierarchies, attendance defaults, and synthetic statutory rules.
"""

from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


# Base project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SYNTHETIC_DATA_DIR = DATA_DIR / "synthetic"


class DatasetScale(str, Enum):
    """Configurable dataset scale presets."""
    DEV = "dev"          # 10,000 employees x 12 months = 120,000 records
    MAIN = "main"        # 100,000 employees x 24 months = 2,400,000 records
    STRESS = "stress"    # 500,000 employees x 36 months = 18,000,000 records
    CUSTOM = "custom"    # User-defined employees and months


# Scale preset definitions: (num_employees, num_months, description)
SCALE_PRESETS: Dict[DatasetScale, Tuple[int, int, str]] = {
    DatasetScale.DEV: (
        10_000,
        12,
        "Development Dataset (~120,000 records) - Rapid dev, debugging & testing",
    ),
    DatasetScale.MAIN: (
        100_000,
        24,
        "Main ML Dataset (~2,400,000 records) - Feature engineering, ML training & validation",
    ),
    DatasetScale.STRESS: (
        500_000,
        36,
        "Stress-Test Dataset (~18,000,000 records) - Scalability, memory & throughput testing",
    ),
}


class Settings(BaseModel):
    """Global system configuration for synthetic data generation and processing."""

    # Project directories
    project_root: Path = Field(default=PROJECT_ROOT)
    data_dir: Path = Field(default=DATA_DIR)
    raw_data_dir: Path = Field(default=RAW_DATA_DIR)
    processed_data_dir: Path = Field(default=PROCESSED_DATA_DIR)
    synthetic_data_dir: Path = Field(default=SYNTHETIC_DATA_DIR)

    # Scale Configuration
    scale: DatasetScale = Field(default=DatasetScale.DEV)
    num_employees: int = Field(default=10_000, description="Total unique synthetic employees")
    num_months: int = Field(default=12, description="Multi-month history duration")
    start_year: int = Field(default=2024, description="Start year of historical payroll")
    start_month: int = Field(default=1, description="Start month (1=Jan)")
    random_seed: int = Field(default=42, description="Global random seed for reproducibility")
    anomaly_rate: float = Field(default=0.05, description="Target proportion of anomalous records (5%)")

    # Streaming / Batch Processing Parameters
    chunk_size_employees: int = Field(
        default=50_000,
        description="Number of employees generated per chunk for bounded memory usage",
    )
    storage_format: str = Field(
        default="parquet",
        description="Default storage format ('parquet', 'csv', or 'both')",
    )
    parquet_compression: str = Field(default="snappy", description="Parquet compression codec")

    # Departments
    departments: List[str] = Field(
        default=[
            "Engineering",
            "Sales",
            "HR",
            "Finance",
            "Operations",
            "Marketing",
            "Support",
            "Administration",
        ]
    )

    # Designations in career progression order
    designations: List[str] = Field(
        default=[
            "Intern",
            "Junior",
            "Mid-level",
            "Senior",
            "Manager",
            "Director",
        ]
    )

    # Department population distribution weights
    department_weights: Dict[str, float] = Field(
        default={
            "Engineering": 0.30,
            "Operations": 0.20,
            "Sales": 0.15,
            "Support": 0.12,
            "Marketing": 0.08,
            "Finance": 0.06,
            "HR": 0.05,
            "Administration": 0.04,
        }
    )

    # Designation hierarchy distribution weights (pyramid structure)
    designation_weights: Dict[str, float] = Field(
        default={
            "Intern": 0.10,
            "Junior": 0.35,
            "Mid-level": 0.30,
            "Senior": 0.15,
            "Manager": 0.07,
            "Director": 0.03,
        }
    )

    # Monthly Base Salary Ranges (INR) by Department and Designation: (min_salary, max_salary)
    salary_bands: Dict[str, Dict[str, Tuple[float, float]]] = Field(
        default={
            "Engineering": {
                "Intern": (22_000, 35_000),
                "Junior": (45_000, 75_000),
                "Mid-level": (80_000, 145_000),
                "Senior": (150_000, 260_000),
                "Manager": (240_000, 390_000),
                "Director": (380_000, 650_000),
            },
            "Sales": {
                "Intern": (18_000, 26_000),
                "Junior": (28_000, 48_000),
                "Mid-level": (52_000, 95_000),
                "Senior": (95_000, 165_000),
                "Manager": (160_000, 270_000),
                "Director": (260_000, 460_000),
            },
            "Finance": {
                "Intern": (20_000, 30_000),
                "Junior": (32_000, 56_000),
                "Mid-level": (60_000, 105_000),
                "Senior": (105_000, 185_000),
                "Manager": (175_000, 300_000),
                "Director": (290_000, 500_000),
            },
            "Operations": {
                "Intern": (16_000, 24_000),
                "Junior": (26_000, 45_000),
                "Mid-level": (48_000, 82_000),
                "Senior": (85_000, 140_000),
                "Manager": (135_000, 220_000),
                "Director": (210_000, 360_000),
            },
            "Support": {
                "Intern": (15_000, 23_000),
                "Junior": (24_000, 42_000),
                "Mid-level": (44_000, 75_000),
                "Senior": (75_000, 120_000),
                "Manager": (115_000, 185_000),
                "Director": (185_000, 310_000),
            },
            "Marketing": {
                "Intern": (18_000, 27_000),
                "Junior": (30_000, 52_000),
                "Mid-level": (55_000, 95_000),
                "Senior": (95_000, 160_000),
                "Manager": (150_000, 245_000),
                "Director": (245_000, 420_000),
            },
            "HR": {
                "Intern": (16_000, 25_000),
                "Junior": (27_000, 46_000),
                "Mid-level": (48_000, 84_000),
                "Senior": (84_000, 145_000),
                "Manager": (135_000, 225_000),
                "Director": (225_000, 390_000),
            },
            "Administration": {
                "Intern": (15_000, 22_000),
                "Junior": (24_000, 40_000),
                "Mid-level": (42_000, 70_000),
                "Senior": (70_000, 115_000),
                "Manager": (110_000, 175_000),
                "Director": (175_000, 290_000),
            },
        }
    )

    # Locations
    locations: List[str] = Field(
        default=["Bengaluru", "Mumbai", "Delhi-NCR", "Hyderabad", "Pune", "Chennai"]
    )

    # Synthetic Payroll Breakdown Ratios
    basic_salary_ratio: float = Field(default=0.45, description="Basic salary proportion of base pay")
    allowances_ratio: float = Field(default=0.55, description="Allowances proportion of base pay")

    # Synthetic Statutory & Deduction Rules
    pf_rate: float = Field(default=0.12, description="Provident Fund employee contribution rate on basic")
    esi_wage_ceiling: float = Field(default=21_000.0, description="Monthly gross wage threshold for ESI eligibility")
    esi_rate: float = Field(default=0.0075, description="Employee ESI contribution rate (0.75% of gross)")
    professional_tax_amount: float = Field(default=200.0, description="Standard monthly professional tax")
    professional_tax_threshold: float = Field(default=15_000.0, description="Min gross salary for PT deduction")

    # Career Progression Dynamics
    annual_increment_rate_min: float = Field(default=0.05)
    annual_increment_rate_max: float = Field(default=0.15)
    promotion_chance_per_year: float = Field(default=0.05)
    promotion_salary_jump_min: float = Field(default=0.15)
    promotion_salary_jump_max: float = Field(default=0.30)
    overtime_multiplier: float = Field(default=1.5)


def get_settings(scale: Optional[DatasetScale] = None) -> Settings:
    """Instantiate and return global settings with optional scale preset."""
    settings = Settings()
    if scale and scale in SCALE_PRESETS:
        n_emp, n_months, _ = SCALE_PRESETS[scale]
        settings.scale = scale
        settings.num_employees = n_emp
        settings.num_months = n_months

    # Ensure data subdirectories exist
    settings.raw_data_dir.mkdir(parents=True, exist_ok=True)
    settings.processed_data_dir.mkdir(parents=True, exist_ok=True)
    settings.synthetic_data_dir.mkdir(parents=True, exist_ok=True)
    return settings
