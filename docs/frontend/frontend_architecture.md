# AI Payroll Guardian — Frontend Architecture & Design System (Phase 8)

## 1. Overview & Objectives

Phase 8 implements the enterprise user interface for **AI Payroll Guardian**. Built with React, TypeScript, Vite, and Tailwind CSS, it provides payroll auditors with an intuitive, executive-grade dashboard for detecting anomalies, reviewing structured evidence cards, tracing statutory citations, and conversing with a grounded AI assistant.

```
                                  AUDITOR / CLIENT BROWSER
                                             ↓
                                    REACT ROUTER DOM
        ┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
        ↓              ↓              ↓              ↓              ↓              ↓
   /dashboard   /payroll/upload   /analysis/:id   /anomalies/:id/:emp /compliance  /assistant
        └──────────────┴──────────────┼──────────────┴──────────────┴──────────────┘
                                      ↓
                            CENTRALIZED API CLIENT
                         (frontend/src/services/api.ts)
                                      ↓
                            FASTAPI REST BACKEND
                          (http://localhost:8000/api/v1)
```

---

## 2. Directory Structure

```
frontend/
├── index.html                  # HTML5 shell with Google Inter & JetBrains Mono fonts
├── package.json                # Dependencies: React 18, React Router 6, Recharts, Lucide React
├── tsconfig.json               # Strict TypeScript configuration
├── vite.config.ts              # Vite dev server with /api proxy to FastAPI (port 8000)
├── tailwind.config.js          # Enterprise slate/navy color tokens and typography
├── postcss.config.js           # PostCSS Tailwind processing
├── src/
│   ├── main.tsx                # React DOM root entrypoint
│   ├── App.tsx                 # Root router & persistent active analysis state
│   ├── index.css               # Tailwind directives and custom scrollbars
│   ├── types/
│   │   └── api.ts              # Strict TypeScript interfaces matching backend models
│   ├── config/
│   │   └── env.ts              # VITE_API_BASE_URL resolution
│   ├── utils/
│   │   ├── formatters.ts       # Currency (INR ₹), date, and percentage formatters
│   │   ├── severity.ts         # Accessible color, badge, and icon mappings
│   │   └── sampleData.ts       # Sample audit demo batch for isolated testing
│   ├── services/
│   │   ├── api.ts              # Fetch wrapper with timeouts and error normalization
│   │   ├── healthApi.ts        # GET /api/v1/health probes
│   │   ├── payrollApi.ts       # POST /api/v1/payroll/analyze & /upload
│   │   ├── anomalyApi.ts       # GET /api/v1/anomalies/{id} & /{id}/{empId}
│   │   ├── complianceApi.ts    # POST /api/v1/compliance/search
│   │   └── assistantApi.ts     # POST /api/v1/assistant/query
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx     # Left navigation + real-time backend service status
│   │   │   ├── Header.tsx      # Top bar with current period badge & quick CTAs
│   │   │   └── Layout.tsx      # Application shell container
│   │   ├── common/
│   │   │   ├── SeverityBadge.tsx
│   │   │   ├── StatCard.tsx
│   │   │   ├── LoadingSpinner.tsx
│   │   │   ├── ErrorAlert.tsx
│   │   │   └── EmptyState.tsx
│   │   ├── dashboard/
│   │   │   ├── MetricCards.tsx
│   │   │   ├── RiskSeverityChart.tsx
│   │   │   └── AnomalyTypeChart.tsx
│   │   ├── payroll/
│   │   │   ├── Dropzone.tsx
│   │   │   └── JsonInputModal.tsx
│   │   ├── anomalies/
│   │   │   ├── AnomalyTable.tsx
│   │   │   ├── EvidenceCard.tsx
│   │   │   ├── ComplianceSourcePanel.tsx
│   │   │   └── AIExplanationPanel.tsx
│   │   ├── compliance/
│   │   │   └── ComplianceSearchBox.tsx
│   │   └── assistant/
│   │       ├── ChatMessage.tsx
│   │       ├── CitationCard.tsx
│   │       └── PromptSuggestions.tsx
│   └── pages/
│       ├── Dashboard.tsx        # Executive summary, KPI cards & charts
│       ├── UploadPayroll.tsx    # Drag-and-drop CSV/JSON upload & live analysis
│       ├── Analysis.tsx         # Comprehensive batch audit & searchable anomaly table
│       ├── AnomalyDetails.tsx   # Evidence card, RAG citations, AI explanation & assistant CTA
│       ├── Compliance.tsx       # Interactive statutory knowledge search
│       ├── Assistant.tsx        # Conversational grounded payroll auditor chat
│       └── NotFound.tsx         # 404 page
```

---

## 3. Page Routes & User Flows

| Route | Page Component | Primary Function |
| :--- | :--- | :--- |
| `/` & `/dashboard` | `Dashboard.tsx` | Executive Risk Overview KPI cards, Risk Severity Donut Chart, and Top Anomaly Categories Bar Chart. |
| `/payroll/upload` | `UploadPayroll.tsx` | Drag & Drop CSV/JSON/Parquet upload with client validation and multi-stage analysis progress indicator. |
| `/analysis` & `/analysis/:id` | `Analysis.tsx` | Full audit batch header, risk KPIs, and interactive Anomaly Table with search, department/severity filters, sorting, and pagination. |
| `/anomalies/:id/:empId` | `AnomalyDetails.tsx` | Deep employee investigation combining Evidence Card, Compliance Source Panel, Grounded AI Explanation, and Assistant Launcher. |
| `/compliance` | `Compliance.tsx` | Searchable 3-tier statutory knowledge base (Federal Acts, State Rules, Corporate Policy) with date and jurisdiction filters. |
| `/assistant` | `Assistant.tsx` | Grounded conversational AI assistant with context pre-population, inline citation cards, and out-of-scope refusal badges. |

---

## 4. Design Language & Accessibility

- **Visual Theme**: Minimal, data-dense enterprise SaaS aesthetic using deep slate (`#020617`, `#0f172a`, `#151f32`) and brand azure accents (`#0c8de7`).
- **Accessible Risk Coding**: Severity is distinguished not only by color, but by distinct labels, icons (`AlertCircle`, `AlertTriangle`, `Info`, `CheckCircle`), and screen-reader ARIA tags:
  - **CRITICAL**: Rose `#f43f5e` + `AlertCircle`
  - **HIGH**: Amber `#f59e0b` + `AlertTriangle`
  - **MEDIUM**: Blue `#3b82f6` + `Info`
  - **LOW**: Emerald `#10b981` + `CheckCircle`
- **Zero-PII Front-End Guardrail**: Sensitive employee attributes (bank accounts, PAN, Aadhaar) are masked or omitted; only employee IDs and department classifications are rendered.

---

## 5. Build and Test Verification

- **Unit Tests (`vitest run`)**: **10 / 10 passed** (formatters, severity config, API client)
- **Production Bundling (`npm run build`)**: **100% successful** (0 TypeScript errors)
- **Regression Tests (`pytest`)**: **101 / 101 passed**
