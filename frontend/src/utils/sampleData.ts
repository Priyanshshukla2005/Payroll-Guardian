import { AnalysisResponse } from '../types/api';

export const DEMO_ANALYSIS: AnalysisResponse = {
  request_id: "req_demo_enterprise_preview",
  analysis_id: "anl_demo_202406",
  status: "COMPLETED",
  payroll_period: "2024-06",
  summary: {
    records_analyzed: 250,
    records_flagged: 12,
    critical_risk: 2,
    high_risk: 4,
    medium_risk: 4,
    low_risk: 238,
  },
  model_version: "HybridPayrollDetector_V2",
  disclaimer: "AI-assisted payroll audit analysis. Not legal advice.",
  created_at: new Date().toISOString(),
  duration_ms: 342.1,
  anomalies: [
    {
      employee_id: "EMP_2041",
      payroll_month: "2024-06",
      department: "Operations",
      designation: "Associate",
      anomaly_types: ["INCORRECT_PF"],
      risk_score: 0.94,
      severity: "CRITICAL",
      evidence: [
        "Provident Fund deduction (₹1,200) deviated substantially from statutory 12% calculation (₹4,800 on Basic ₹40,000)",
        "Deduction-to-Gross ratio dropped to 0.023 (cohort median: 0.093)"
      ],
      rule_violations: ["RULE_PF_MISMATCH"],
      historical_comparison: {
        prev_pf: 4800.0,
        historical_mean: 4800.0,
        drop_percentage: -75.0,
      },
      peer_comparison: {
        dept_median_pf: 4800.0,
        cohort_zscore: -4.2,
      },
      compliance: {
        status: "FOUND",
        sources: [
          {
            document_id: "EPFO_ACT_1952",
            title: "Employees' Provident Funds and Miscellaneous Provisions Act, 1952",
            authority_level: "STATUTORY_ACT",
            section: "Section 6",
            page: 12,
            citation: "[EPFO_ACT_1952, Section 6, p.12]"
          }
        ]
      },
      explanation: {
        title: "Critical Provident Fund Under-Deduction",
        summary: "Employee EMP_2041 received a PF deduction of only ₹1,200 (3.0% of basic pay ₹40,000), violating the mandatory 12.0% statutory rate under the EPFO Act 1952.",
        why_flagged: [
          "Mandatory 12% PF statutory rule violation",
          "Sudden 75% drop compared to employee's historical PF contributions"
        ],
        recommended_actions: [
          "Audit payroll register deduction formulas for Operations department",
          "Recover PF shortfall of ₹3,600 and submit revised EPFO ECR return"
        ],
        uncertainty: null,
        fallback_mode: false,
      }
    },
    {
      employee_id: "EMP_1088",
      payroll_month: "2024-06",
      department: "Engineering",
      designation: "Senior Engineer",
      anomaly_types: ["SALARY_SPIKE", "OVERTIME_OUTLIER"],
      risk_score: 0.85,
      severity: "CRITICAL",
      evidence: [
        "Gross salary jumped by +62.5% Month-over-Month without recorded promotion",
        "Overtime hours logged at 65.0 hours exceeding the 60-hour statutory threshold"
      ],
      rule_violations: ["RULE_EXCESSIVE_OVERTIME"],
      historical_comparison: {
        prev_gross: 120000.0,
        current_gross: 195000.0,
        change_percentage: 62.5,
      },
      peer_comparison: {
        desig_median_gross: 125000.0,
        cohort_zscore: 4.8,
      },
      compliance: {
        status: "FOUND",
        sources: [
          {
            document_id: "FACTORIES_ACT_1948",
            title: "Factories Act, 1948 - Overtime Hours Regulation",
            authority_level: "STATUTORY_ACT",
            section: "Section 59",
            page: 18,
            citation: "[FACTORIES_ACT_1948, Section 59, p.18]"
          }
        ]
      },
      explanation: {
        title: "Unusual Overtime and Gross Payout Surge",
        summary: "Employee EMP_1088 exhibited a 62.5% increase in gross earnings driven by 65 overtime hours, breaching statutory limits.",
        why_flagged: [
          "Overtime hours logged at 65.0 hrs exceeding 60.0 hr statutory cap",
          "Gross salary z-score of +4.8 vs historical baseline"
        ],
        recommended_actions: [
          "Verify manager sign-off timesheet logs for weekend overtime sessions",
          "Ensure overtime rate calculation conforms with Section 59 statutory rules"
        ],
        uncertainty: null,
        fallback_mode: false,
      }
    },
    {
      employee_id: "EMP_1015",
      payroll_month: "2024-06",
      department: "Finance",
      designation: "Lead",
      anomaly_types: ["IMPOSSIBLE_ATTENDANCE"],
      risk_score: 0.88,
      severity: "HIGH",
      evidence: [
        "Present days logged as 31 days against 26 standard working days in month",
        "Attendance integrity violation triggered"
      ],
      rule_violations: ["RULE_IMPOSSIBLE_ATTENDANCE"],
      historical_comparison: {},
      peer_comparison: {},
      compliance: {
        status: "FOUND",
        sources: [
          {
            document_id: "SHOPS_ESTABLISHMENTS_ACT",
            title: "State Shops and Commercial Establishments Act",
            authority_level: "STATE_REGULATION",
            section: "Section 7",
            page: 9,
            citation: "[SHOPS_ESTABLISHMENTS_ACT, Section 7, p.9]"
          }
        ]
      },
      explanation: {
        title: "Impossible Attendance Logged",
        summary: "Employee EMP_1015 has recorded 31 present days in a 26-working-day calendar month.",
        why_flagged: ["Present days exceed scheduled monthly working days"],
        recommended_actions: ["Recalibrate biometric attendance logs and adjust prorated pay"],
        uncertainty: null,
        fallback_mode: false,
      }
    },
    {
      employee_id: "EMP_1028",
      payroll_month: "2024-06",
      department: "Sales",
      designation: "Manager",
      anomaly_types: ["ESI_VIOLATION"],
      risk_score: 0.76,
      severity: "HIGH",
      evidence: [
        "ESI contribution deducted on gross salary of ₹80,000 exceeding statutory ₹21,000 threshold"
      ],
      rule_violations: ["RULE_ESI_MISMATCH"],
      historical_comparison: {},
      peer_comparison: {},
      compliance: {
        status: "FOUND",
        sources: [
          {
            document_id: "ESIC_ACT_1948",
            title: "Employees' State Insurance Act, 1948",
            authority_level: "STATUTORY_ACT",
            section: "Section 2(9)",
            page: 15,
            citation: "[ESIC_ACT_1948, Section 2(9), p.15]"
          }
        ]
      },
      explanation: {
        title: "Ineligible ESI Deduction",
        summary: "Employee EMP_1028 had ESI deducted despite gross compensation exceeding the ₹21,000 wage ceiling.",
        why_flagged: ["Gross salary exceeds ESIC coverage ceiling"],
        recommended_actions: ["Refund wrongful ESI deductions and update payroll master config"],
        uncertainty: null,
        fallback_mode: false,
      }
    },
    {
      employee_id: "EMP_1042",
      payroll_month: "2024-06",
      department: "Marketing",
      designation: "Executive",
      anomaly_types: ["INCORRECT_PF"],
      risk_score: 0.78,
      severity: "HIGH",
      evidence: [
        "PF contribution ₹2,000 deviates from mandatory 12% calculation (₹4,200 on Basic ₹35,000)"
      ],
      rule_violations: ["RULE_PF_MISMATCH"],
      historical_comparison: {},
      peer_comparison: {},
      compliance: {
        status: "FOUND",
        sources: [
          {
            document_id: "EPFO_ACT_1952",
            title: "Employees' Provident Funds and Miscellaneous Provisions Act, 1952",
            authority_level: "STATUTORY_ACT",
            section: "Section 6",
            page: 12,
            citation: "[EPFO_ACT_1952, Section 6, p.12]"
          }
        ]
      },
      explanation: {
        title: "Provident Fund Under-Deduction",
        summary: "Employee EMP_1042 experienced an improper PF contribution rate calculation.",
        why_flagged: ["Statutory 12% rate underdeduction"],
        recommended_actions: ["Recompute PF liability and remit delta"],
        uncertainty: null,
        fallback_mode: false,
      }
    },
    {
      employee_id: "EMP_1065",
      payroll_month: "2024-06",
      department: "Operations",
      designation: "Technician",
      anomaly_types: ["RECONCILIATION_ERROR"],
      risk_score: 0.74,
      severity: "HIGH",
      evidence: [
        "Net salary (₹38,000) exceeds Gross salary minus deductions (₹32,440)"
      ],
      rule_violations: ["RULE_NET_RECONCILIATION_FAIL"],
      historical_comparison: {},
      peer_comparison: {},
      compliance: {
        status: "FOUND",
        sources: [
          {
            document_id: "PAYMENT_WAGES_ACT_1936",
            title: "Payment of Wages Act, 1936",
            authority_level: "STATUTORY_ACT",
            section: "Section 7",
            page: 8,
            citation: "[PAYMENT_WAGES_ACT_1936, Section 7, p.8]"
          }
        ]
      },
      explanation: {
        title: "Arithmetic Reconciliation Discrepancy",
        summary: "Net payout does not balance against gross compensation and statutory deductions.",
        why_flagged: ["Gross - Total Deductions does not equal Net Salary"],
        recommended_actions: ["Audit ledger formula mappings in ERP"],
        uncertainty: null,
        fallback_mode: false,
      }
    },
    {
      employee_id: "EMP_1077",
      payroll_month: "2024-06",
      department: "HR",
      designation: "Specialist",
      anomaly_types: ["SALARY_SPIKE"],
      risk_score: 0.68,
      severity: "MEDIUM",
      evidence: [
        "Month-over-month salary change percentage is +300.0% without designation promotion"
      ],
      rule_violations: [],
      historical_comparison: {
        change_percentage: 300.0,
      },
      peer_comparison: {},
      compliance: {
        status: "FOUND",
        sources: [
          {
            document_id: "COMPANY_COMPENSATION_POLICY",
            title: "Internal Compensation and Salary Revision Policy",
            authority_level: "COMPANY_POLICY",
            section: "Clause 3.1",
            page: 4,
            citation: "[COMPANY_COMPENSATION_POLICY, Clause 3.1, p.4]"
          }
        ]
      },
      explanation: {
        title: "Unverified Salary Revision Surge",
        summary: "Compensation increased by 300% without HR compensation committee authorization record.",
        why_flagged: ["Unusual compensation surge"],
        recommended_actions: ["Obtain signed authorization letter from compensation committee"],
        uncertainty: null,
        fallback_mode: false,
      }
    },
    {
      employee_id: "EMP_1093",
      payroll_month: "2024-06",
      department: "Engineering",
      designation: "Developer",
      anomaly_types: ["RECONCILIATION_ERROR"],
      risk_score: 0.65,
      severity: "MEDIUM",
      evidence: [
        "Net salary calculation mismatch (Recorded: ₹70,000, Expected: ₹78,000)"
      ],
      rule_violations: ["RULE_NET_RECONCILIATION_FAIL"],
      historical_comparison: {},
      peer_comparison: {},
      compliance: {
        status: "FOUND",
        sources: [
          {
            document_id: "PAYMENT_WAGES_ACT_1936",
            title: "Payment of Wages Act, 1936",
            authority_level: "STATUTORY_ACT",
            section: "Section 7",
            page: 8,
            citation: "[PAYMENT_WAGES_ACT_1936, Section 7, p.8]"
          }
        ]
      },
      explanation: {
        title: "Net Salary Arithmetic Variance",
        summary: "Employee net payout deviates by ₹8,000 from documented deduction subtractions.",
        why_flagged: ["Deduction calculation arithmetic mismatch"],
        recommended_actions: ["Reconcile taxable deduction components"],
        uncertainty: null,
        fallback_mode: false,
      }
    },
    {
      employee_id: "EMP_1105",
      payroll_month: "2024-06",
      department: "Support",
      designation: "Agent",
      anomaly_types: ["RECONCILIATION_ERROR"],
      risk_score: 0.62,
      severity: "MEDIUM",
      evidence: [
        "Gross salary (₹18,000) does not match sum of Basic (₹22,000) and Allowances (₹8,000)"
      ],
      rule_violations: ["RULE_GROSS_RECONCILIATION_FAIL"],
      historical_comparison: {},
      peer_comparison: {},
      compliance: {
        status: "FOUND",
        sources: [
          {
            document_id: "CODE_ON_WAGES_2019",
            title: "Code on Wages, 2019",
            authority_level: "STATUTORY_ACT",
            section: "Section 18",
            page: 22,
            citation: "[CODE_ON_WAGES_2019, Section 18, p.22]"
          }
        ]
      },
      explanation: {
        title: "Gross Earning Component Mismatch",
        summary: "Gross earnings logged below the stated base salary component.",
        why_flagged: ["Sum of earning components does not equal gross salary"],
        recommended_actions: ["Audit base pay setup in employee profile"],
        uncertainty: null,
        fallback_mode: false,
      }
    },
    {
      employee_id: "EMP_1118",
      payroll_month: "2024-06",
      department: "Sales",
      designation: "Representative",
      anomaly_types: ["OVERTIME_OUTLIER"],
      risk_score: 0.58,
      severity: "MEDIUM",
      evidence: [
        "Overtime hours logged at 68.0 hrs breaching 60.0 hr monthly cap"
      ],
      rule_violations: ["RULE_EXCESSIVE_OVERTIME"],
      historical_comparison: {},
      peer_comparison: {},
      compliance: {
        status: "FOUND",
        sources: [
          {
            document_id: "FACTORIES_ACT_1948",
            title: "Factories Act, 1948 - Overtime Hours Regulation",
            authority_level: "STATUTORY_ACT",
            section: "Section 59",
            page: 18,
            citation: "[FACTORIES_ACT_1948, Section 59, p.18]"
          }
        ]
      },
      explanation: {
        title: "Excessive Overtime Logged",
        summary: "Employee logged 68 hours of overtime, exceeding statutory limits.",
        why_flagged: ["Overtime hours exceed statutory ceiling"],
        recommended_actions: ["Enforce shift management caps"],
        uncertainty: null,
        fallback_mode: false,
      }
    },
    {
      employee_id: "EMP_1130",
      payroll_month: "2024-06",
      department: "Product",
      designation: "Designer",
      anomaly_types: ["INCORRECT_PF"],
      risk_score: 0.55,
      severity: "LOW",
      evidence: [
        "Provident fund deduction is ₹0.00 on eligible basic salary ₹55,000"
      ],
      rule_violations: ["RULE_PF_MISMATCH"],
      historical_comparison: {},
      peer_comparison: {},
      compliance: {
        status: "FOUND",
        sources: [
          {
            document_id: "EPFO_ACT_1952",
            title: "Employees' Provident Funds and Miscellaneous Provisions Act, 1952",
            authority_level: "STATUTORY_ACT",
            section: "Section 6",
            page: 12,
            citation: "[EPFO_ACT_1952, Section 6, p.12]"
          }
        ]
      },
      explanation: {
        title: "Missing Mandatory PF Contribution",
        summary: "Zero PF deducted for employee meeting mandatory statutory eligibility.",
        why_flagged: ["Omitted PF deduction"],
        recommended_actions: ["Enroll employee in EPFO portal with immediate effect"],
        uncertainty: null,
        fallback_mode: false,
      }
    },
    {
      employee_id: "EMP_1142",
      payroll_month: "2024-06",
      department: "Legal",
      designation: "Counsel",
      anomaly_types: ["SALARY_SPIKE", "INCORRECT_PF"],
      risk_score: 0.52,
      severity: "LOW",
      evidence: [
        "Compound anomaly: 200% salary surge with PF underdeduction (₹2,500 vs ₹13,200)"
      ],
      rule_violations: ["RULE_PF_MISMATCH"],
      historical_comparison: {
        change_percentage: 200.0,
      },
      peer_comparison: {},
      compliance: {
        status: "FOUND",
        sources: [
          {
            document_id: "EPFO_ACT_1952",
            title: "Employees' Provident Funds and Miscellaneous Provisions Act, 1952",
            authority_level: "STATUTORY_ACT",
            section: "Section 6",
            page: 12,
            citation: "[EPFO_ACT_1952, Section 6, p.12]"
          }
        ]
      },
      explanation: {
        title: "Compound Compensation Deviation",
        summary: "Employee exhibited concurrent salary surge and statutory under-deduction.",
        why_flagged: ["Multiple concurrent payroll variances"],
        recommended_actions: ["Perform complete compensation and deduction reconciliation"],
        uncertainty: null,
        fallback_mode: false,
      }
    },
  ]
};
