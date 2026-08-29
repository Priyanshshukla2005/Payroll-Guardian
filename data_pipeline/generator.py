"""High-performance synthetic payroll generator for AI Payroll Guardian.

Supports scalable generation from Development scale (120k records) to
Main ML scale (2.4M records) and Stress-Test scale (18M records) using
vectorized simulation and memory-efficient chunked streaming.
"""

from datetime import date, timedelta
from typing import Any, Dict, Generator, List, Optional, Tuple, Union
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from backend.config.settings import DatasetScale, Settings, get_settings


class SyntheticEmployeePopulation:
    """Generates and maintains a realistic population of persistent employees."""

    def __init__(self, settings: Optional[Settings] = None, random_seed: Optional[int] = None):
        self.settings = settings or get_settings()
        self.seed = random_seed if random_seed is not None else self.settings.random_seed
        self.rng = np.random.default_rng(self.seed)

    def generate_population(
        self,
        num_employees: Optional[int] = None,
        start_id_offset: int = 0,
    ) -> pd.DataFrame:
        """Generate base employee population with persistent attributes.

        Args:
            num_employees: Total employees to generate in this batch.
            start_id_offset: Starting integer offset for employee IDs.

        Returns:
            pd.DataFrame with persistent employee profiles.
        """
        n = num_employees or self.settings.num_employees
        emp_ids = [f"EMP{i:07d}" for i in range(start_id_offset + 1, start_id_offset + n + 1)]

        # Sample Departments
        dept_names = list(self.settings.department_weights.keys())
        dept_probs = np.array(list(self.settings.department_weights.values()), dtype=float)
        dept_probs = dept_probs / dept_probs.sum()
        departments = self.rng.choice(dept_names, size=n, p=dept_probs)

        # Sample Designations
        desig_names = list(self.settings.designation_weights.keys())
        desig_probs = np.array(list(self.settings.designation_weights.values()), dtype=float)
        desig_probs = desig_probs / desig_probs.sum()
        designations = self.rng.choice(desig_names, size=n, p=desig_probs)

        # Sample Locations
        locations = self.rng.choice(self.settings.locations, size=n)

        # Sample Genders
        genders = self.rng.choice(["M", "F", "Other"], size=n, p=[0.58, 0.40, 0.02])

        # Sample Joining Dates (between 2015-01-01 and 2023-11-30)
        start_dt = date(2015, 1, 1)
        max_days = (date(2023, 11, 30) - start_dt).days
        random_day_offsets = self.rng.integers(0, max_days, size=n)
        joining_dates = [start_dt + timedelta(days=int(d)) for d in random_day_offsets]

        # Annual increment month (1 to 12)
        increment_months = self.rng.integers(1, 13, size=n)

        # Sample Base Salaries according to Department and Designation bands
        base_salaries = np.zeros(n, dtype=float)
        for dept in dept_names:
            for desig in desig_names:
                mask = (departments == dept) & (designations == desig)
                count = int(mask.sum())
                if count > 0:
                    low, high = self.settings.salary_bands[dept][desig]
                    mid = (low + high) / 2.0
                    scale = (high - low) / 5.0
                    sal = self.rng.normal(mid, scale, size=count)
                    base_salaries[mask] = np.round(np.clip(sal, low, high), 2)

        # Employment status (mostly ACTIVE, small probation/notice)
        statuses = self.rng.choice(
            ["ACTIVE", "PROBATION", "NOTICE_PERIOD"],
            size=n,
            p=[0.92, 0.05, 0.03],
        )

        # Overtime eligibility (Junior/Mid/Intern in Ops, Support, Eng, Sales)
        ot_eligible = np.zeros(n, dtype=bool)
        for dept in ["Operations", "Support", "Engineering", "Sales"]:
            for desig in ["Intern", "Junior", "Mid-level"]:
                ot_eligible[(departments == dept) & (designations == desig)] = True
        for dept in ["Operations", "Support"]:
            ot_eligible[(departments == dept) & (designations == "Senior")] = True

        df_pop = pd.DataFrame({
            "employee_id": emp_ids,
            "department": departments,
            "designation": designations,
            "location": locations,
            "gender": genders,
            "joining_date": [d.strftime("%Y-%m-%d") for d in joining_dates],
            "employment_status": statuses,
            "base_monthly_salary": base_salaries,
            "increment_month": increment_months,
            "overtime_eligible": ot_eligible,
        })

        return df_pop


def _vectorized_tds(annual_gross: np.ndarray) -> np.ndarray:
    """Vectorized calculation of monthly TDS deduction on annualized gross salary."""
    tax = np.zeros_like(annual_gross, dtype=float)

    # Slab 2: 3L - 7L (5%)
    mask2 = (annual_gross > 300_000.0) & (annual_gross <= 700_000.0)
    tax[mask2] = (annual_gross[mask2] - 300_000.0) * 0.05

    # Slab 3: 7L - 12L (20k + 10%)
    mask3 = (annual_gross > 700_000.0) & (annual_gross <= 1_200_000.0)
    tax[mask3] = 20_000.0 + (annual_gross[mask3] - 700_000.0) * 0.10

    # Slab 4: 12L - 15L (70k + 15%)
    mask4 = (annual_gross > 1_200_000.0) & (annual_gross <= 1_500_000.0)
    tax[mask4] = 70_000.0 + (annual_gross[mask4] - 1_200_000.0) * 0.15

    # Slab 5: > 15L (115k + 20%)
    mask5 = annual_gross > 1_500_000.0
    tax[mask5] = 115_000.0 + (annual_gross[mask5] - 1_500_000.0) * 0.20

    return np.round(tax / 12.0, 2)


def generate_population_month_slice(
    pop: pd.DataFrame,
    month_str: str,
    calendar_month_num: int,
    std_working_days: int,
    settings: Settings,
    rng: np.random.Generator,
    current_salaries: np.ndarray,
    current_designations: np.ndarray,
) -> pd.DataFrame:
    """Generate a single month's vectorized payroll records for an employee population slice."""
    n = len(pop)
    departments = pop["department"].values
    employee_ids = pop["employee_id"].values
    joining_dates = pop["joining_date"].values
    employment_statuses = pop["employment_status"].values
    locations = pop["location"].values
    increment_months = pop["increment_month"].values
    ot_eligible = pop["overtime_eligible"].values

    desig_hierarchy = settings.designations
    desig_to_idx = {d: i for i, d in enumerate(desig_hierarchy)}

    # 1. Vectorized Annual Increment
    is_inc_month = (increment_months == calendar_month_num)
    if is_inc_month.any():
        inc_rates = rng.uniform(
            settings.annual_increment_rate_min,
            settings.annual_increment_rate_max,
            size=int(is_inc_month.sum()),
        )
        current_salaries[is_inc_month] = np.round(current_salaries[is_inc_month] * (1.0 + inc_rates), 2)

    # 2. Vectorized Career Promotion (small annual chance on increment month)
    if is_inc_month.any():
        inc_indices = np.where(is_inc_month)[0]
        prom_rolls = rng.random(len(inc_indices))
        prom_candidates = inc_indices[prom_rolls < settings.promotion_chance_per_year]

        for p_idx in prom_candidates:
            cur_desig = current_designations[p_idx]
            cur_level = desig_to_idx.get(cur_desig, -1)
            if 0 <= cur_level < len(desig_hierarchy) - 1:
                next_desig = desig_hierarchy[cur_level + 1]
                current_designations[p_idx] = next_desig
                jump_rate = rng.uniform(settings.promotion_salary_jump_min, settings.promotion_salary_jump_max)
                current_salaries[p_idx] = round(current_salaries[p_idx] * (1.0 + jump_rate), 2)

    # 3. Attendance Dynamics
    working_days = np.full(n, std_working_days, dtype=np.int32)
    leave_choices = np.array([0, 1, 2, 3, 4], dtype=np.int32)
    leave_probs = np.array([0.45, 0.30, 0.15, 0.07, 0.03], dtype=float)
    leave_days = rng.choice(leave_choices, size=n, p=leave_probs)
    present_days = working_days - leave_days

    # 4. Salary Component Breakdown
    basic_salary = np.round(current_salaries * settings.basic_salary_ratio, 2)
    allowances = np.round(current_salaries - basic_salary, 2)

    # 5. Overtime Generation
    overtime_hours = np.zeros(n, dtype=float)
    ot_candidates = np.where(ot_eligible)[0]
    if len(ot_candidates) > 0:
        ot_roll = rng.random(len(ot_candidates))
        active_ot = ot_candidates[ot_roll < 0.40]
        if len(active_ot) > 0:
            raw_hrs = rng.gamma(shape=2.5, scale=4.0, size=len(active_ot))
            clipped_hrs = np.clip(raw_hrs, 2.0, 32.0)
            overtime_hours[active_ot] = np.round(clipped_hrs, 1)

    hourly_rate = basic_salary / (working_days * 8.0)
    overtime_amount = np.where(
        overtime_hours > 0,
        np.round(hourly_rate * settings.overtime_multiplier * overtime_hours, 2),
        0.0,
    )

    # 6. Performance / Festive Bonus (March = 3, October = 10)
    bonus = np.zeros(n, dtype=float)
    if calendar_month_num in [3, 10]:
        bonus_roll = rng.random(n)
        bonus_recipients = np.where(bonus_roll < 0.35)[0]
        if len(bonus_recipients) > 0:
            bonus_frac = rng.uniform(0.10, 0.30, size=len(bonus_recipients))
            bonus[bonus_recipients] = np.round(current_salaries[bonus_recipients] * bonus_frac, 2)

    # 7. Gross Salary (exact balance)
    gross_salary = np.round(basic_salary + allowances + overtime_amount + bonus, 2)

    # 8. Deductions
    pf = np.round(basic_salary * settings.pf_rate, 2)
    esi = np.where(
        gross_salary <= settings.esi_wage_ceiling,
        np.round(gross_salary * settings.esi_rate, 2),
        0.0,
    )
    annual_gross_est = gross_salary * 12.0
    tds = _vectorized_tds(annual_gross_est)
    other_deductions = np.where(
        gross_salary >= settings.professional_tax_threshold,
        settings.professional_tax_amount,
        0.0,
    )
    total_deductions = np.round(pf + esi + tds + other_deductions, 2)

    # 9. Net Salary (exact balance)
    net_salary = np.round(gross_salary - total_deductions, 2)

    month_df = pd.DataFrame({
        "employee_id": employee_ids,
        "payroll_month": month_str,
        "department": departments,
        "designation": current_designations.copy(),
        "joining_date": joining_dates,
        "employment_status": employment_statuses,
        "location": locations,
        "working_days": working_days,
        "present_days": present_days,
        "leave_days": leave_days,
        "basic_salary": basic_salary,
        "allowances": allowances,
        "overtime_hours": overtime_hours,
        "overtime_amount": overtime_amount,
        "bonus": bonus,
        "gross_salary": gross_salary,
        "pf": pf,
        "esi": esi,
        "tds": tds,
        "other_deductions": other_deductions,
        "total_deductions": total_deductions,
        "net_salary": net_salary,
        "is_anomaly": np.zeros(n, dtype=np.int8),
        "anomaly_type": "NONE",
    })

    return month_df


def generate_synthetic_payroll_chunks(
    settings: Optional[Settings] = None,
    num_employees: Optional[int] = None,
    num_months: Optional[int] = None,
    chunk_size_employees: Optional[int] = None,
    random_seed: Optional[int] = None,
) -> Generator[pd.DataFrame, None, None]:
    """Yield multi-month payroll datasets in employee chunks for constant-memory processing.

    Args:
        settings: System Settings.
        num_employees: Total unique employees (defaults to settings.num_employees).
        num_months: Total months (defaults to settings.num_months).
        chunk_size_employees: Employee batch size (defaults to settings.chunk_size_employees).
        random_seed: Seed for reproducible random numbers.

    Yields:
        pd.DataFrame containing full multi-month history for each employee chunk.
    """
    settings = settings or get_settings()
    seed = random_seed if random_seed is not None else settings.random_seed
    rng = np.random.default_rng(seed)
    n_total_emp = num_employees or settings.num_employees
    n_months = num_months or settings.num_months
    chunk_size = chunk_size_employees or settings.chunk_size_employees

    working_days_calendar = [26, 24, 26, 25, 26, 25, 27, 26, 25, 26, 25, 26]

    # Generate list of month strings
    month_names = []
    for m_idx in range(n_months):
        year = settings.start_year + (settings.start_month + m_idx - 1) // 12
        month = (settings.start_month + m_idx - 1) % 12 + 1
        month_names.append(f"{year}-{month:02d}")

    # Process in employee batches to strictly cap memory footprint
    emp_offset = 0
    pop_gen = SyntheticEmployeePopulation(settings=settings, random_seed=seed)

    while emp_offset < n_total_emp:
        current_chunk_size = min(chunk_size, n_total_emp - emp_offset)
        pop_chunk = pop_gen.generate_population(
            num_employees=current_chunk_size,
            start_id_offset=emp_offset,
        )

        current_salaries = pop_chunk["base_monthly_salary"].values.copy()
        current_designations = pop_chunk["designation"].values.copy()

        chunk_month_dfs = []
        for m_idx, month_str in enumerate(month_names):
            cal_month_num = (settings.start_month + m_idx - 1) % 12 + 1
            std_wd = working_days_calendar[m_idx % len(working_days_calendar)]

            df_month = generate_population_month_slice(
                pop=pop_chunk,
                month_str=month_str,
                calendar_month_num=cal_month_num,
                std_working_days=std_wd,
                settings=settings,
                rng=rng,
                current_salaries=current_salaries,
                current_designations=current_designations,
            )
            chunk_month_dfs.append(df_month)

        df_chunk_full = pd.concat(chunk_month_dfs, ignore_index=True)
        yield df_chunk_full

        emp_offset += current_chunk_size


def generate_synthetic_payroll_dataset(
    settings: Optional[Settings] = None,
    num_employees: Optional[int] = None,
    num_months: Optional[int] = None,
    random_seed: Optional[int] = None,
    chunk_size_employees: Optional[int] = None,
) -> pd.DataFrame:
    """Generate multi-month clean synthetic payroll dataset in memory.

    Args:
        settings: System Settings instance.
        num_employees: Total employees.
        num_months: Total months.
        random_seed: Seed for reproducible random numbers.
        chunk_size_employees: Chunk size.

    Returns:
        pd.DataFrame containing clean multi-month payroll records.
    """
    chunks = list(
        generate_synthetic_payroll_chunks(
            settings=settings,
            num_employees=num_employees,
            num_months=num_months,
            chunk_size_employees=chunk_size_employees,
            random_seed=random_seed,
        )
    )
    return pd.concat(chunks, ignore_index=True)
