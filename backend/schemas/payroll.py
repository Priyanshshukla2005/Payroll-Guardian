"""Pydantic schemas for payroll records and batch analysis requests (Phase 7)."""

from typing import List, Optional
from pydantic import BaseModel, Field


class PayrollRecordInput(BaseModel):
    """Schema representing an individual monthly payroll row for an employee."""

    employee_id: str = Field(description="Unique employee identifier (e.g., EMP001)")
    payroll_month: str = Field(description="Payroll period in YYYY-MM format")
    basic_salary: float = Field(ge=0.0, description="Monthly basic salary in INR")
    gross_salary: float = Field(ge=0.0, description="Total gross earnings in INR")
    net_salary: float = Field(ge=0.0, description="Net take-home pay in INR")
    allowances: float = Field(default=0.0, ge=0.0, description="Special allowances")
    bonus: float = Field(default=0.0, ge=0.0, description="Bonus / discretionary payout")
    total_deductions: float = Field(default=0.0, ge=0.0, description="Total deductions")
    pf_deduction: float = Field(default=0.0, ge=0.0, description="Provident Fund deduction")
    esi: float = Field(default=0.0, ge=0.0, description="ESI deduction")
    professional_tax: float = Field(default=0.0, ge=0.0, description="Professional Tax deduction")
    working_days: int = Field(default=26, ge=1, le=31, description="Total working days in month")
    present_days: int = Field(default=26, ge=0, le=31, description="Days present / credited")
    leave_days: int = Field(default=0, ge=0, le=31, description="Approved leave days")
    overtime_hours: float = Field(default=0.0, ge=0.0, description="Approved overtime hours")
    department: str = Field(default="General", description="Department name")
    designation: str = Field(default="Staff", description="Employee designation")
    location: str = Field(default="INDIA", description="Geographic jurisdiction / state")


class PayrollBatchAnalyzeRequest(BaseModel):
    """Request payload for JSON batch payroll analysis."""

    records: List[PayrollRecordInput] = Field(min_length=1, description="List of payroll records to analyze")
    payroll_period: Optional[str] = Field(default=None, description="Optional target payroll period override")
    jurisdiction: Optional[str] = Field(default="INDIA", description="Optional jurisdiction override")
