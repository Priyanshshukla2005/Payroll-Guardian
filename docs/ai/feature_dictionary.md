# 📖 AI Payroll Guardian — Feature Dictionary

Complete audit and reference dictionary for all **66 engineered features and raw fields** in the AI Payroll Guardian data pipeline.

---

## 🛡️ Leakage & Availability Legend

- **Data Type**: `Float64`, `Int32`, `Categorical`
- **Uses History**: Whether the feature computation depends on prior calendar months for the employee.
- **Leakage Risk**: All historical features use strictly `shift(1)` (strictly prior months, $t-1, t-2, \dots$), guaranteeing **Zero Lookahead Leakage**.
- **Inference Availability**: `Yes` — the feature can be computed in real-time during monthly payroll processing runs using current input records and historical database snapshots.

---

## 1. Raw Payroll & Attendance Fields (22 Features)

| Feature Name | Type | Definition / Formula | Source Columns | Uses History | Leakage Risk | Inference Available |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| `working_days` | Int32 | Total working days in calendar month | Calendar | No | None | Yes |
| `present_days` | Int32 | Total days employee attended | Biometric / HRIS | No | None | Yes |
| `leave_days` | Int32 | Approved leave days taken | Leave system | No | None | Yes |
| `basic_salary` | Float64 | Monthly basic salary component | Payroll structure | No | None | Yes |
| `allowances` | Float64 | House rent, conveyance, and special allowances | Payroll structure | No | None | Yes |
| `overtime_hours` | Float64 | Total overtime hours logged | Timesheet system | No | None | Yes |
| `overtime_amount`| Float64 | Payout for overtime hours | Computed: hourly rate × 1.5x | No | None | Yes |
| `bonus` | Float64 | Performance or festive bonus payout | HR appraisal | No | None | Yes |
| `gross_salary` | Float64 | Total earnings: basic + allowances + overtime + bonus | Computed earnings | No | None | Yes |
| `pf` | Float64 | Provident Fund contribution (12% of basic) | Statutory rule | No | None | Yes |
| `esi` | Float64 | Employee State Insurance (0.75% of gross if <= 21k) | Statutory rule | No | None | Yes |
| `tds` | Float64 | Monthly tax deducted at source | Tax slab estimate | No | None | Yes |
| `other_deductions`| Float64 | Professional tax or authorized deductions | Statutory / HR | No | None | Yes |
| `total_deductions`| Float64 | Sum of all deduction items | Computed deductions | No | None | Yes |
| `net_salary` | Float64 | Take-home pay: gross_salary - total_deductions | Net disbursement | No | None | Yes |
| `department` | Categorical | Business unit (Engineering, Sales, HR, Finance, etc.) | Employee Master | No | None | Yes |
| `designation` | Categorical | Hierarchy level (Intern, Junior, Mid, Senior, etc.) | Employee Master | No | None | Yes |
| `employment_status`| Categorical | Status: ACTIVE, PROBATION, NOTICE_PERIOD | Employee Master | No | None | Yes |
| `location` | Categorical | Work office location | Employee Master | No | None | Yes |
| `gender` | Categorical | Demographic indicator | Employee Master | No | None | Yes |
| `is_anomaly` | Int8 | Ground truth label (0 = Normal, 1 = Anomaly) | Anomaly Engine | N/A (Target) | Excluded from X | Target Only |
| `anomaly_type` | Categorical | Specific anomaly category or NONE | Anomaly Engine | N/A (Target) | Excluded from X | Target Only |

---

## 2. Intra-Record Ratio Features (9 Features)

| Feature Name | Type | Mathematical Formula | Source Columns | Uses History | Leakage Risk | Inference Available |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| `attendance_ratio` | Float64 | $\text{present\_days} / \text{working\_days}$ | `present_days`, `working_days` | No | None | Yes |
| `leave_ratio` | Float64 | $\text{leave\_days} / \text{working\_days}$ | `leave_days`, `working_days` | No | None | Yes |
| `overtime_per_present_day` | Float64 | $\text{overtime\_hours} / \max(\text{present\_days}, 1.0)$ | `overtime_hours`, `present_days` | No | None | Yes |
| `deduction_to_gross_ratio` | Float64 | $\text{total\_deductions} / \max(\text{gross\_salary}, \epsilon)$ | `total_deductions`, `gross_salary` | No | None | Yes |
| `net_to_gross_ratio` | Float64 | $\text{net\_salary} / \max(\text{gross\_salary}, \epsilon)$ | `net_salary`, `gross_salary` | No | None | Yes |
| `basic_to_gross_ratio` | Float64 | $\text{basic\_salary} / \max(\text{gross\_salary}, \epsilon)$ | `basic_salary`, `gross_salary` | No | None | Yes |
| `allowance_to_basic_ratio`| Float64 | $\text{allowances} / \max(\text{basic\_salary}, \epsilon)$ | `allowances`, `basic_salary` | No | None | Yes |
| `pf_to_basic_ratio` | Float64 | $\text{pf} / \max(\text{basic\_salary}, \epsilon)$ | `pf`, `basic_salary` | No | None | Yes |
| `esi_to_gross_ratio` | Float64 | $\text{esi} / \max(\text{gross\_salary}, \epsilon)$ | `esi`, `gross_salary` | No | None | Yes |

---

## 3. Month-over-Month (MoM) Delta Features (14 Features)

| Feature Name | Type | Mathematical Formula | Source Columns | Uses History | Leakage Risk | Inference Available |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| `salary_change_percentage` | Float64 | $\frac{\text{basic}_t - \text{basic}_{t-1}}{\max(\|\text{basic}_{t-1}\|, 1.0)} \times 100$ | `basic_salary` (lag 1) | Yes (Lag 1) | None (`shift(1)`) | Yes |
| `prev_basic_salary` | Float64 | $\text{basic\_salary}_{t-1}$ | `basic_salary` | Yes (Lag 1) | None (`shift(1)`) | Yes |
| `gross_salary_change_percentage` | Float64 | $\frac{\text{gross}_t - \text{gross}_{t-1}}{\max(\|\text{gross}_{t-1}\|, 1.0)} \times 100$ | `gross_salary` (lag 1) | Yes (Lag 1) | None (`shift(1)`) | Yes |
| `prev_gross_salary` | Float64 | $\text{gross\_salary}_{t-1}$ | `gross_salary` | Yes (Lag 1) | None (`shift(1)`) | Yes |
| `overtime_change_percentage` | Float64 | $\frac{\text{ot}_t - \text{ot}_{t-1}}{\max(\|\text{ot}_{t-1}\|, 1.0)} \times 100$ | `overtime_hours` (lag 1) | Yes (Lag 1) | None (`shift(1)`) | Yes |
| `prev_overtime_hours` | Float64 | $\text{overtime\_hours}_{t-1}$ | `overtime_hours` | Yes (Lag 1) | None (`shift(1)`) | Yes |
| `bonus_change_percentage` | Float64 | $\frac{\text{bonus}_t - \text{bonus}_{t-1}}{\max(\|\text{bonus}_{t-1}\|, 1.0)} \times 100$ | `bonus` (lag 1) | Yes (Lag 1) | None (`shift(1)`) | Yes |
| `prev_bonus` | Float64 | $\text{bonus}_{t-1}$ | `bonus` | Yes (Lag 1) | None (`shift(1)`) | Yes |
| `deduction_change_percentage` | Float64 | $\frac{\text{ded}_t - \text{ded}_{t-1}}{\max(\|\text{ded}_{t-1}\|, 1.0)} \times 100$ | `total_deductions` (lag 1) | Yes (Lag 1) | None (`shift(1)`) | Yes |
| `prev_total_deductions` | Float64 | $\text{total\_deductions}_{t-1}$ | `total_deductions` | Yes (Lag 1) | None (`shift(1)`) | Yes |
| `net_salary_change_percentage` | Float64 | $\frac{\text{net}_t - \text{net}_{t-1}}{\max(\|\text{net}_{t-1}\|, 1.0)} \times 100$ | `net_salary` (lag 1) | Yes (Lag 1) | None (`shift(1)`) | Yes |
| `prev_net_salary` | Float64 | $\text{net\_salary}_{t-1}$ | `net_salary` | Yes (Lag 1) | None (`shift(1)`) | Yes |
| `present_days_change` | Float64 | $\text{present\_days}_t - \text{present\_days}_{t-1}$ | `present_days` (lag 1) | Yes (Lag 1) | None (`shift(1)`) | Yes |

---

## 4. Historical Rolling Window Statistics (12 Features)

*All historical features compute cumulative expanding statistics across all prior months strictly before month $t$:*

$$\mu_{<t} = \text{mean}(x_1, \dots, x_{t-1}), \quad \sigma_{<t} = \text{std}(x_1, \dots, x_{t-1})$$

| Feature Name | Type | Mathematical Formula | Source Columns | Uses History | Leakage Risk | Inference Available |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| `historical_salary_mean` | Float64 | $\mu_{<t}(\text{basic\_salary})$ | `basic_salary` | Yes | None (`shift(1).expanding()`) | Yes |
| `historical_salary_std` | Float64 | $\sigma_{<t}(\text{basic\_salary})$ | `basic_salary` | Yes | None (`shift(1).expanding()`) | Yes |
| `salary_zscore_vs_history` | Float64 | $\frac{\text{basic}_t - \mu_{<t}}{\max(\sigma_{<t}, 1.0)}$ | `basic_salary` | Yes | None | Yes |
| `historical_gross_mean` | Float64 | $\mu_{<t}(\text{gross\_salary})$ | `gross_salary` | Yes | None (`shift(1).expanding()`) | Yes |
| `historical_gross_std` | Float64 | $\sigma_{<t}(\text{gross\_salary})$ | `gross_salary` | Yes | None (`shift(1).expanding()`) | Yes |
| `gross_zscore_vs_history` | Float64 | $\frac{\text{gross}_t - \mu_{<t}}{\max(\sigma_{<t}, 1.0)}$ | `gross_salary` | Yes | None | Yes |
| `historical_overtime_mean` | Float64 | $\mu_{<t}(\text{overtime\_hours})$ | `overtime_hours` | Yes | None (`shift(1).expanding()`) | Yes |
| `historical_overtime_std` | Float64 | $\sigma_{<t}(\text{overtime\_hours})$ | `overtime_hours` | Yes | None (`shift(1).expanding()`) | Yes |
| `overtime_zscore_vs_history` | Float64 | $\frac{\text{ot}_t - \mu_{<t}}{\max(\sigma_{<t}, 1.0)}$ | `overtime_hours` | Yes | None | Yes |
| `historical_total_deductions_mean`| Float64 | $\mu_{<t}(\text{total\_deductions})$ | `total_deductions` | Yes | None (`shift(1).expanding()`) | Yes |
| `historical_total_deductions_std` | Float64 | $\sigma_{<t}(\text{total\_deductions})$ | `total_deductions` | Yes | None (`shift(1).expanding()`) | Yes |
| `total_deductions_zscore_vs_history`| Float64 | $\frac{\text{ded}_t - \mu_{<t}}{\max(\sigma_{<t}, 1.0)}$ | `total_deductions` | Yes | None | Yes |

---

## 5. Peer-Group Benchmark Features (8 Features)

| Feature Name | Type | Mathematical Formula | Source Columns | Uses History | Leakage Risk | Inference Available |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| `dept_month_gross_mean` | Float64 | Mean gross for department in current month | `department`, `gross_salary` | Current Month | None | Yes |
| `dept_month_gross_std` | Float64 | Std gross for department in current month | `department`, `gross_salary` | Current Month | None | Yes |
| `gross_vs_dept_ratio` | Float64 | $\text{gross\_salary} / \max(\text{dept\_mean}, \epsilon)$ | `gross_salary`, `dept_mean` | Current Month | None | Yes |
| `desig_month_gross_mean` | Float64 | Mean gross for designation in current month | `designation`, `gross_salary` | Current Month | None | Yes |
| `desig_month_gross_std` | Float64 | Std gross for designation in current month | `designation`, `gross_salary` | Current Month | None | Yes |
| `gross_vs_desig_ratio` | Float64 | $\text{gross\_salary} / \max(\text{desig\_mean}, \epsilon)$ | `gross_salary`, `desig_mean` | Current Month | None | Yes |
| `desig_month_overtime_mean` | Float64 | Mean overtime for designation in month | `designation`, `overtime_hours` | Current Month | None | Yes |
| `desig_month_overtime_std` | Float64 | Std overtime for designation in month | `designation`, `overtime_hours` | Current Month | None | Yes |

---

## 6. Identifier & Metadata Columns (Excluded from $X$)

| Column Name | Type | Role | Inclusion in Model Features $X$ |
| :--- | :--- | :--- | :---: |
| `employee_id` | String | Unique employee identifier | ❌ **Excluded** (Metadata only) |
| `payroll_month` | String | Payroll month timestamp (`YYYY-MM`) | ❌ **Excluded** (Temporal split & metadata) |
| `joining_date` | Date | Employee tenure reference | ❌ **Excluded** (Metadata only) |
