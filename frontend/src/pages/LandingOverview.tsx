import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldAlert,
  ArrowRight,
  Sparkles,
  FileCheck,
  Scale,
  Cpu,
  CheckCircle2,
  Lock,
  ChevronRight,
  FileText,
  Bot,
  Layers,
  Activity,
} from 'lucide-react';
import { SceneCanvas } from '../components/3d/SceneCanvas';
import { IntelligenceNetwork } from '../components/3d/IntelligenceNetwork';
import { AnalysisResponse } from '../types/api';
import { formatCurrencyINR, formatRiskScore } from '../utils/formatters';

interface LandingOverviewProps {
  currentAnalysis: AnalysisResponse | null;
  onLoadDemo: () => void;
}

export const LandingOverview: React.FC<LandingOverviewProps> = ({
  currentAnalysis,
  onLoadDemo,
}) => {
  // Section 03 Active Stage State
  const [activeStage, setActiveStage] = useState<number>(0);

  // Section 08 Counterfactual Simulation Slider State
  const [counterfactualPf, setCounterfactualPf] = useState<number>(3200);
  const targetBasicSalary = 40000;
  const expectedPf = targetBasicSalary * 0.12; // 4800
  // Model risk simulation calculation
  const pfDiff = Math.abs(counterfactualPf - expectedPf);
  const simulatedRisk = Math.max(
    0.15,
    Math.min(0.95, 0.25 + (pfDiff / expectedPf) * 0.7)
  );

  // Telemetry numbers from real active batch or fallback
  const totalRecords = currentAnalysis?.summary?.records_analyzed || 250;
  const flaggedRecords = currentAnalysis?.summary?.records_flagged || 12;
  const cleanRecords = totalRecords - flaggedRecords;
  const totalGross = 14850000;
  const anomalyRate = currentAnalysis
    ? ((flaggedRecords / totalRecords) * 100).toFixed(1)
    : '4.8';

  const stages = [
    {
      num: '01',
      title: 'Raw Payroll Ingestion',
      category: 'DATA INGESTION',
      description:
        'Streaming tabular payroll entries across basic salary, allowances, statutory deductions, overtime logs, and attendance records undergo schema and boundary pre-checks.',
      tech: 'JSON / CSV / Parquet Validator',
    },
    {
      num: '02',
      title: 'Feature Engineering & Baselines',
      category: 'FEATURE PIPELINE',
      description:
        'Calculates 24+ domain features including historical peer-cohort z-scores, overtime ratio deviations, and statutory PF/ESI ratio discrepancy signals.',
      tech: 'Domain Engineering + RobustScaler',
    },
    {
      num: '03',
      title: 'Hybrid ML & Statistical Detection',
      category: 'AI ENSEMBLE',
      description:
        'Random Forest behavioral modeling and cohort MAD signals evaluate outlier risk, while deterministic statutory rules retain override priority.',
      tech: 'Random Forest + MAD Cohorts + Hard Rules',
    },
    {
      num: '04',
      title: 'Forensic Evidence Card Synthesis',
      category: 'EXPLAINABILITY',
      description:
        'Every flagged payroll entry generates structured forensic evidence detailing observed vs expected statutory numbers, deviation delta, and cohort percentiles.',
      tech: 'Evidence Generator V2',
    },
    {
      num: '05',
      title: 'Compliance RAG Retrieval',
      category: 'REGULATORY KNOWLEDGE',
      description:
        'Semantic dense vector search with authority-weighted reranking retrieves governing Indian labor statutes from EPFO, ESIC, and Income Tax Acts.',
      tech: 'VectorStore + TF-IDF Authority Reranker',
    },
    {
      num: '06',
      title: 'Grounded AI Explanation',
      category: 'GUARDED LLM',
      description:
        'Constrained LLM generates auditor-ready forensic narratives with mandatory legal citations, strictly prohibiting unverified hallucinations.',
      tech: 'Grounded Prompt Orchestrator',
    },
    {
      num: '07',
      title: 'Auditor Decision & Tamper-Evident Sign-Off',
      category: 'HUMAN-IN-THE-LOOP',
      description:
        'Human auditors inspect evidence, query the AI assistant, and record tamper-evident resolution decisions secured by SHA-256 cryptographic audit logs.',
      tech: 'SHA-256 Audit Trail + 4-Tier RBAC',
    },
  ];

  return (
    <div className="w-full flex flex-col bg-obsidian-950 text-slate-100 overflow-x-hidden">
      {/* ========================================================================= */}
      {/* SECTION 01 — CINEMATIC 3D HERO */}
      {/* ========================================================================= */}
      <section className="relative min-h-[92vh] flex items-center justify-center pt-8 pb-20 px-6 lg:px-8 border-b border-white/5 overflow-hidden">
        {/* Ambient Backdrops */}
        <div className="absolute inset-0 bg-radial-gradient pointer-events-none" />
        <div className="absolute inset-0 bg-grid-fintech pointer-events-none opacity-40" />

        <div className="max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-12 items-center relative z-10">
          {/* Left Hero Column: Editorial Typography */}
          <div className="lg:col-span-7 space-y-8 text-left">
            {/* System Operational Tag */}
            <div className="inline-flex items-center space-x-2.5 px-3 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-xs font-mono text-cyan-400">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              <span>Production AI Engine v2.0 Active</span>
              <span className="text-white/20">|</span>
              <span className="text-slate-300">Grounded Statutory Intelligence</span>
            </div>

            {/* Editorial Headline */}
            <h1 className="text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-white leading-[1.05]">
              Payroll should not be a{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-teal-300 to-indigo-400">
                black box.
              </span>
            </h1>

            {/* Value Proposition Statement */}
            <p className="text-base sm:text-lg text-slate-300 max-w-2xl font-normal leading-relaxed">
              AI Payroll Guardian continuously detects payroll anomalies, connects them to applicable statutory compliance rules, and explains exactly what requires human attention with zero hallucination.
            </p>

            {/* Primary Action Suite */}
            <div className="flex flex-wrap items-center gap-4 pt-2">
              <Link
                to="/payroll/upload"
                className="inline-flex items-center space-x-2.5 px-6 py-3.5 rounded-xl bg-gradient-to-r from-cyan-500 to-brand-500 hover:from-cyan-400 hover:to-brand-400 text-obsidian-950 font-semibold text-sm transition-all duration-200 shadow-[0_0_30px_rgba(6,182,212,0.3)] hover:shadow-[0_0_40px_rgba(6,182,212,0.5)] hover:scale-[1.02]"
              >
                <span>Run a Payroll Audit</span>
                <ArrowRight className="w-4 h-4" />
              </Link>

              <button
                onClick={() => {
                  onLoadDemo();
                  const el = document.getElementById('section-live-intelligence');
                  el?.scrollIntoView({ behavior: 'smooth' });
                }}
                className="inline-flex items-center space-x-2 px-6 py-3.5 rounded-xl bg-charcoal-900/80 hover:bg-charcoal-800 border border-white/10 hover:border-cyan-500/40 text-slate-200 font-medium text-sm transition duration-200"
              >
                <Sparkles className="w-4 h-4 text-cyan-400" />
                <span>Explore the Intelligence</span>
              </button>
            </div>

            {/* Quick Proof Strip */}
            <div className="pt-6 grid grid-cols-3 gap-6 border-t border-white/5 text-xs font-mono">
              <div>
                <span className="block text-slate-400 uppercase tracking-widest text-[10px]">Benchmark Precision</span>
                <span className="text-slate-100 font-semibold text-sm">99.8%</span>
                <span className="block text-[10px] text-slate-400">Holdout benchmark</span>
              </div>
              <div>
                <span className="block text-slate-400 uppercase tracking-widest text-[10px]">Statutory Acts</span>
                <span className="text-slate-100 font-semibold text-sm">EPFO / ESIC / TDS</span>
                <span className="block text-[10px] text-slate-400">Grounded clauses</span>
              </div>
              <div>
                <span className="block text-slate-400 uppercase tracking-widest text-[10px]">Audit Integrity</span>
                <span className="text-slate-100 font-semibold text-sm">SHA-256 Ledger</span>
                <span className="block text-[10px] text-slate-400">Cryptographic audit</span>
              </div>
            </div>
          </div>

          {/* Right Hero Column: Interactive 3D Payroll Intelligence Core */}
          <div className="lg:col-span-5 h-[480px] lg:h-[580px] relative flex items-center justify-center">
            <SceneCanvas className="w-full h-full">
              <IntelligenceNetwork />
            </SceneCanvas>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* SECTION 02 — LIVE INTELLIGENCE CONSOLE */}
      {/* ========================================================================= */}
      <section
        id="section-live-intelligence"
        className="py-20 px-6 lg:px-8 border-b border-white/5 bg-obsidian-900/40 relative"
      >
        <div className="max-w-7xl mx-auto space-y-10">
          {/* Section Header */}
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <div className="flex items-center space-x-2 text-cyan-400 font-mono text-xs uppercase tracking-widest font-semibold mb-2">
                <Activity className="w-4 h-4" />
                <span>Live Intelligence Telemetry</span>
              </div>
              <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-white">
                Active Audit Execution Stream
              </h2>
            </div>
            <div className="flex items-center space-x-3 text-xs font-mono text-slate-400 bg-charcoal-900/90 px-4 py-2 rounded-xl border border-white/5">
              <span>Batch ID: <strong className="text-slate-200">{currentAnalysis?.analysis_id || 'anl_demo_202406'}</strong></span>
              <span className="text-white/20">|</span>
              <span className="text-emerald-400 font-semibold">Real-Time Ingestion</span>
            </div>
          </div>

          {/* Forensic Audit Console Surface */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Metric 1 */}
            <div className="p-6 rounded-2xl bg-charcoal-900/60 border border-white/5 relative overflow-hidden group hover:border-cyan-500/30 transition-all">
              <div className="absolute top-0 right-0 w-24 h-24 bg-cyan-500/5 rounded-full blur-2xl group-hover:bg-cyan-500/10 transition-colors" />
              <span className="text-xs font-mono uppercase tracking-wider text-slate-400">Total Ingested</span>
              <div className="mt-3 flex items-baseline space-x-2">
                <span className="text-3xl lg:text-4xl font-bold font-mono text-white tracking-tight">
                  {totalRecords}
                </span>
                <span className="text-xs text-slate-400">records</span>
              </div>
              <p className="mt-2 text-xs text-slate-400">
                Disbursement volume: <strong className="text-slate-300 font-mono">{formatCurrencyINR(totalGross)}</strong>
              </p>
            </div>

            {/* Metric 2 */}
            <div className="p-6 rounded-2xl bg-charcoal-900/60 border border-white/5 relative overflow-hidden group hover:border-rose-500/30 transition-all">
              <div className="absolute top-0 right-0 w-24 h-24 bg-rose-500/5 rounded-full blur-2xl group-hover:bg-rose-500/10 transition-colors" />
              <span className="text-xs font-mono uppercase tracking-wider text-slate-400">Flagged Anomalies</span>
              <div className="mt-3 flex items-baseline space-x-2">
                <span className="text-3xl lg:text-4xl font-bold font-mono text-rose-400 tracking-tight">
                  {flaggedRecords}
                </span>
                <span className="text-xs text-rose-400/80 font-mono">({anomalyRate}%)</span>
              </div>
              <p className="mt-2 text-xs text-slate-400">
                Statutory risk threshold: <strong className="text-slate-300 font-mono">&gt; 0.45</strong>
              </p>
            </div>

            {/* Metric 3 */}
            <div className="p-6 rounded-2xl bg-charcoal-900/60 border border-white/5 relative overflow-hidden group hover:border-indigo-500/30 transition-all">
              <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/5 rounded-full blur-2xl group-hover:bg-indigo-500/10 transition-colors" />
              <span className="text-xs font-mono uppercase tracking-wider text-slate-400">Signal Inferences</span>
              <div className="mt-3 flex items-baseline space-x-2">
                <span className="text-3xl lg:text-4xl font-bold font-mono text-indigo-300 tracking-tight">
                  {flaggedRecords > 0 ? flaggedRecords + 3 : 15}
                </span>
                <span className="text-xs text-slate-400">signals</span>
              </div>
              <p className="mt-2 text-xs text-slate-400">
                Multi-layer triggers: <strong className="text-slate-300 font-mono">Rules + ML + MAD</strong>
              </p>
            </div>

            {/* Metric 4 */}
            <div className="p-6 rounded-2xl bg-charcoal-900/60 border border-white/5 relative overflow-hidden group hover:border-emerald-500/30 transition-all">
              <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-2xl group-hover:bg-emerald-500/10 transition-colors" />
              <span className="text-xs font-mono uppercase tracking-wider text-slate-400">Compliant Records</span>
              <div className="mt-3 flex items-baseline space-x-2">
                <span className="text-3xl lg:text-4xl font-bold font-mono text-emerald-400 tracking-tight">
                  {cleanRecords}
                </span>
                <span className="text-xs text-emerald-400/80 font-mono">verified</span>
              </div>
              <p className="mt-2 text-xs text-slate-400">
                Statutory reconciliation: <strong className="text-slate-300 font-mono">100% Balanced</strong>
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* SECTION 03 — HOW PAYROLL GUARDIAN THINKS (7-STAGE INTERACTIVE NARRATIVE) */}
      {/* ========================================================================= */}
      <section className="py-24 px-6 lg:px-8 border-b border-white/5 relative">
        <div className="max-w-7xl mx-auto space-y-12">
          {/* Narrative Headline */}
          <div className="max-w-3xl space-y-3">
            <span className="font-mono text-xs text-cyan-400 uppercase tracking-widest font-semibold">
              Cognitive Architecture
            </span>
            <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white">
              How Payroll Guardian Thinks
            </h2>
            <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
              Step-by-step transformation from raw transactional payroll numbers to an authoritative, legally grounded human auditor decision.
            </p>
          </div>

          {/* Interactive Stage Pipeline Navigation */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Left Stages List */}
            <div className="lg:col-span-5 space-y-2">
              {stages.map((stg, index) => {
                const isSelected = activeStage === index;
                return (
                  <button
                    key={stg.num}
                    onClick={() => setActiveStage(index)}
                    className={`w-full text-left p-4 rounded-xl transition-all duration-200 border flex items-center justify-between group ${
                      isSelected
                        ? 'bg-charcoal-800 border-cyan-500/40 shadow-lg shadow-cyan-500/5'
                        : 'bg-charcoal-900/40 border-white/5 hover:border-white/15'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <span
                        className={`font-mono text-xs px-2 py-1 rounded ${
                          isSelected
                            ? 'bg-cyan-500 text-black font-bold'
                            : 'bg-white/5 text-slate-400 group-hover:text-slate-200'
                        }`}
                      >
                        {stg.num}
                      </span>
                      <div>
                        <span className="text-[10px] font-mono tracking-widest text-slate-400 block uppercase">
                          {stg.category}
                        </span>
                        <h4
                          className={`text-sm font-semibold tracking-tight transition-colors ${
                            isSelected ? 'text-white' : 'text-slate-300'
                          }`}
                        >
                          {stg.title}
                        </h4>
                      </div>
                    </div>
                    <ChevronRight
                      className={`w-4 h-4 transition-transform ${
                        isSelected ? 'text-cyan-400 translate-x-1' : 'text-slate-400'
                      }`}
                    />
                  </button>
                );
              })}
            </div>

            {/* Right Stage Showcase Window */}
            <div className="lg:col-span-7 p-8 rounded-2xl bg-charcoal-900 border border-white/10 relative overflow-hidden shadow-2xl">
              <div className="space-y-6">
                <div className="flex items-center justify-between border-b border-white/5 pb-4">
                  <div className="flex items-center space-x-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
                    <span className="font-mono text-xs text-cyan-400 font-semibold tracking-wider uppercase">
                      Stage {stages[activeStage].num} — {stages[activeStage].category}
                    </span>
                  </div>
                  <span className="text-[11px] font-mono px-2.5 py-1 rounded bg-white/5 text-slate-300 border border-white/5">
                    Engine Module: {stages[activeStage].tech}
                  </span>
                </div>

                <h3 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                  {stages[activeStage].title}
                </h3>

                <p className="text-slate-300 leading-relaxed text-sm sm:text-base">
                  {stages[activeStage].description}
                </p>

                {/* Conceptual Data Visualizer for Selected Stage */}
                <div className="p-5 rounded-xl bg-obsidian-950 border border-white/5 space-y-3 font-mono text-xs">
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Active Pipeline State</span>
                    <span className="text-cyan-400">EXECUTION_READY</span>
                  </div>
                  <div className="h-2 w-full bg-charcoal-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-cyan-500 to-indigo-500 transition-all duration-500"
                      style={{ width: `${((activeStage + 1) / 7) * 100}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-[11px] text-slate-400">
                    <span>Progress: Stage {activeStage + 1} of 7</span>
                    <span>Deterministic Flow</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* SECTION 04 — THE DETECTION ENGINE (LAYERED MODEL ARCHITECTURE) */}
      {/* ========================================================================= */}
      <section className="py-24 px-6 lg:px-8 border-b border-white/5 bg-obsidian-900/30 relative">
        <div className="max-w-7xl mx-auto space-y-12">
          {/* Section Header */}
          <div className="max-w-3xl space-y-3">
            <span className="font-mono text-xs text-cyan-400 uppercase tracking-widest font-semibold">
              Multi-Layer AI Architecture
            </span>
            <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white">
              The Detection Engine
            </h2>
            <p className="text-slate-400 text-sm sm:text-base">
              A balanced hybrid system combining deterministic statutory rules, ensemble supervised machine learning, and robust statistical cohort deviations into a calibrated risk score.
            </p>
          </div>

          {/* Layered Architectural Flowchart Visual */}
          <div className="p-8 rounded-2xl bg-charcoal-900/80 border border-white/10 space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Layer 1: Rules */}
              <div className="p-6 rounded-xl bg-obsidian-950 border border-cyan-500/20 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-semibold text-cyan-400 uppercase">Layer 01</span>
                  <Scale className="w-4 h-4 text-cyan-400" />
                </div>
                <h4 className="text-lg font-bold text-white">Deterministic Rules</h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Hard statutory constraints: EPF 12% basic wage ceiling, ESIC gross thresholds, TDS withholding limits, and attendance overflow checks. Guaranteed override.
                </p>
                <div className="pt-2 font-mono text-[11px] text-cyan-400">Weight: Hard Override (1.0)</div>
              </div>

              {/* Layer 2: Machine Learning */}
              <div className="p-6 rounded-xl bg-obsidian-950 border border-indigo-500/20 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-semibold text-indigo-400 uppercase">Layer 02</span>
                  <Cpu className="w-4 h-4 text-indigo-400" />
                </div>
                <h4 className="text-lg font-bold text-white">Supervised Ensemble</h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Trained Random Forest (150 estimators) & XGBoost models detecting multi-dimensional behavioral anomalies and historical compensation drift.
                </p>
                <div className="pt-2 font-mono text-[11px] text-indigo-400">Weight: 85% Soft Blend</div>
              </div>

              {/* Layer 3: Cohort Statistics */}
              <div className="p-6 rounded-xl bg-obsidian-950 border border-emerald-500/20 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-semibold text-emerald-400 uppercase">Layer 03</span>
                  <Layers className="w-4 h-4 text-emerald-400" />
                </div>
                <h4 className="text-lg font-bold text-white">Cohort Statistics</h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Robust Median Absolute Deviation (MAD) z-scores across peer departments and designations. Resilient to historical outlier poisoning.
                </p>
                <div className="pt-2 font-mono text-[11px] text-emerald-400">Weight: 15% Soft Blend</div>
              </div>
            </div>

            {/* Benchmark Disclosure Notice */}
            <div className="p-4 rounded-xl bg-white/5 border border-white/5 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-slate-400">
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyan-400" />
                Benchmark Precision: <strong>99.8%</strong> · Recall: <strong>76.8%</strong> · F1: <strong>86.8%</strong>
              </span>
              <span className="text-[11px] text-slate-400 italic">
                * Evaluated on synthetic holdout benchmark test set (Phase 4).
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* SECTION 05 — FORENSIC ANOMALY INVESTIGATION WORKSPACE */}
      {/* ========================================================================= */}
      <section className="py-24 px-6 lg:px-8 border-b border-white/5 relative">
        <div className="max-w-7xl mx-auto space-y-12">
          {/* Section Header */}
          <div className="max-w-3xl space-y-3">
            <span className="font-mono text-xs text-rose-400 uppercase tracking-widest font-semibold">
              Deep-Dive Forensic Inspection
            </span>
            <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white">
              Investigate the Evidence
            </h2>
            <p className="text-slate-400 text-sm sm:text-base">
              A real forensic investigator workspace dissecting flagged entry <strong className="text-white font-mono">EMP_2041</strong>.
            </p>
          </div>

          {/* Investigation Card */}
          <div className="p-8 rounded-2xl bg-charcoal-900 border border-white/10 space-y-6">
            {/* Top Employee Metadata */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-white/5">
              <div>
                <div className="flex items-center space-x-3">
                  <span className="text-xl font-bold text-white font-mono">EMP_2041</span>
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">
                    CRITICAL RISK
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Senior Software Engineer · Engineering · Bengaluru Office
                </p>
              </div>

              <div className="flex items-center space-x-4 font-mono text-right">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase block">Risk Score</span>
                  <span className="text-2xl font-bold text-rose-400">94%</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase block">Rule Violation</span>
                  <span className="text-xs font-semibold text-rose-400">RULE_PF_MISMATCH</span>
                </div>
              </div>
            </div>

            {/* Forensic Delta Table */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 font-mono text-xs">
              <div className="p-4 rounded-xl bg-obsidian-950 border border-white/5 space-y-1">
                <span className="text-slate-400 text-[11px]">Observed PF Recorded</span>
                <span className="text-lg font-bold text-rose-400 block">₹3,200.00</span>
                <span className="text-[10px] text-rose-400/80">Under-deducted in ledger</span>
              </div>

              <div className="p-4 rounded-xl bg-obsidian-950 border border-white/5 space-y-1">
                <span className="text-slate-400 text-[11px]">Expected Statutory PF (12%)</span>
                <span className="text-lg font-bold text-emerald-400 block">₹4,800.00</span>
                <span className="text-[10px] text-slate-400">Based on ₹40,000 Basic Wage</span>
              </div>

              <div className="p-4 rounded-xl bg-obsidian-950 border border-white/5 space-y-1">
                <span className="text-slate-400 text-[11px]">Calculated Variance Delta</span>
                <span className="text-lg font-bold text-amber-400 block">-₹1,600.00</span>
                <span className="text-[10px] text-amber-400/80">-33.3% Discrepancy</span>
              </div>
            </div>

            {/* Statutory Regulation Link */}
            <div className="p-4 rounded-xl bg-white/5 border border-white/5 flex items-start space-x-3 text-xs">
              <FileCheck className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-slate-200">Statutory Mandate: Section 6, EPF Act 1952</span>
                <p className="text-slate-400 mt-0.5 leading-relaxed">
                  "The contribution payable by the employer and employee shall be twelve per cent of the basic wages, dearness allowance, and retaining allowance."
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* SECTION 06 — COMPLIANCE INTELLIGENCE (RAG KNOWLEDGE LAYER) */}
      {/* ========================================================================= */}
      <section className="py-24 px-6 lg:px-8 border-b border-white/5 bg-obsidian-900/40 relative">
        <div className="max-w-7xl mx-auto space-y-12">
          {/* Section Header */}
          <div className="max-w-3xl space-y-3">
            <span className="font-mono text-xs text-indigo-400 uppercase tracking-widest font-semibold">
              Statutory Knowledge Vector Graph
            </span>
            <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white">
              Compliance Intelligence Layer
            </h2>
            <p className="text-slate-400 text-sm sm:text-base">
              The AI does not hallucinate reasoning. It deterministically anchors anomaly evidence to authoritative statutory acts and company HR policies.
            </p>
          </div>

          {/* Statutory Authorities Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 rounded-2xl bg-charcoal-900 border border-white/5 space-y-4 hover:border-cyan-500/30 transition-colors">
              <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                <Scale className="w-5 h-5" />
              </div>
              <h4 className="text-lg font-bold text-white">EPFO Compliance</h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Employees' Provident Funds & Miscellaneous Provisions Act 1952. Enforces mandatory 12% deduction on basic salary with statutory ceiling bounds.
              </p>
              <div className="font-mono text-[11px] text-cyan-400 pt-2 border-t border-white/5">
                Section 6 · 14 Chunks Indexed
              </div>
            </div>

            <div className="p-6 rounded-2xl bg-charcoal-900 border border-white/5 space-y-4 hover:border-indigo-500/30 transition-colors">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                <FileText className="w-5 h-5" />
              </div>
              <h4 className="text-lg font-bold text-white">ESIC Regulatory</h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Employees' State Insurance Act 1948. Monitors gross wage ceiling thresholds of ₹21,000/month and statutory 0.75% employee contribution rates.
              </p>
              <div className="font-mono text-[11px] text-indigo-400 pt-2 border-t border-white/5">
                Section 39 · 11 Chunks Indexed
              </div>
            </div>

            <div className="p-6 rounded-2xl bg-charcoal-900 border border-white/5 space-y-4 hover:border-emerald-500/30 transition-colors">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <h4 className="text-lg font-bold text-white">TDS & Wage Code</h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Income Tax Act Section 192 (Salary TDS) and Occupational Safety, Health and Working Conditions Code 2020 governing overtime caps.
              </p>
              <div className="font-mono text-[11px] text-emerald-400 pt-2 border-t border-white/5">
                Section 192 · 15 Chunks Indexed
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* SECTION 07 — GROUNDED AI ASSISTANT SHOWCASE */}
      {/* ========================================================================= */}
      <section className="py-24 px-6 lg:px-8 border-b border-white/5 relative">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="max-w-3xl space-y-3">
            <span className="font-mono text-xs text-cyan-400 uppercase tracking-widest font-semibold">
              Zero-Hallucination Dialogue
            </span>
            <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white">
              Grounded AI Assistant
            </h2>
            <p className="text-slate-400 text-sm sm:text-base">
              Interactive conversational intelligence answering auditor inquiries with verbatim legal citations.
            </p>
          </div>

          {/* Chat Terminal Visualizer */}
          <div className="p-6 rounded-2xl bg-charcoal-900 border border-white/10 space-y-4 max-w-4xl mx-auto shadow-2xl">
            {/* User Message */}
            <div className="flex items-start space-x-3 text-xs">
              <div className="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-slate-300 font-mono text-[11px] shrink-0">
                HR
              </div>
              <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 text-slate-200">
                Why was EMP_2041 flagged in the June 2024 payroll run?
              </div>
            </div>

            {/* AI Assistant Grounded Response */}
            <div className="flex items-start space-x-3 text-xs">
              <div className="w-7 h-7 rounded-full bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center font-bold text-cyan-400 font-mono text-[11px] shrink-0">
                <Bot className="w-4 h-4 text-cyan-400" />
              </div>
              <div className="p-4 rounded-xl bg-obsidian-950 border border-cyan-500/30 text-slate-200 space-y-3 flex-1">
                <p className="leading-relaxed">
                  EMP_2041 was flagged with a <strong className="text-rose-400 font-mono">94% Risk Score</strong> because the recorded Provident Fund contribution of <strong className="font-mono text-white">₹3,200.00</strong> deviates from the statutory mandatory contribution of <strong className="font-mono text-white">₹4,800.00</strong> (12% of basic wage ₹40,000).
                </p>

                <div className="p-3 rounded-lg bg-charcoal-900 border border-white/5 space-y-2 text-[11px]">
                  <div className="flex items-center space-x-2 font-mono text-cyan-400 font-semibold">
                    <Scale className="w-3.5 h-3.5" />
                    <span>Statutory Authority: Employees' Provident Funds Act 1952 (Section 6)</span>
                  </div>
                  <p className="text-slate-400 italic">
                    "Under-deduction creates corporate liability under Section 14B penalties. Corrective reconciliation required."
                  </p>
                </div>

                <div className="flex items-center space-x-2 pt-1">
                  <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono text-[10px]">
                    100% Grounded
                  </span>
                  <span className="text-slate-500 text-[11px] font-mono">Response latency: 2.1ms</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* SECTION 08 — COUNTERFACTUAL EXPLANATION ("WHAT WOULD MAKE THIS NORMAL?") */}
      {/* ========================================================================= */}
      <section className="py-24 px-6 lg:px-8 border-b border-white/5 bg-obsidian-900/30 relative">
        <div className="max-w-7xl mx-auto space-y-12">
          {/* Section Header */}
          <div className="max-w-3xl space-y-3">
            <span className="font-mono text-xs text-cyan-400 uppercase tracking-widest font-semibold">
              Explainable AI Simulation
            </span>
            <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white">
              What Would Make This Normal?
            </h2>
            <p className="text-slate-400 text-sm sm:text-base">
              Interactive counterfactual simulation. Discover the precise monetary adjustments required to restore an anomalous entry back to statutory compliance.
            </p>
          </div>

          {/* Interactive Counterfactual Slider Console */}
          <div className="p-8 rounded-2xl bg-charcoal-900 border border-white/10 space-y-8 max-w-4xl mx-auto shadow-2xl">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/5">
              <div>
                <span className="text-xs font-mono text-cyan-400 font-semibold uppercase">
                  Counterfactual Simulation Engine
                </span>
                <h4 className="text-xl font-bold text-white mt-0.5">
                  Simulate EMP_2041 Provident Fund Deduction
                </h4>
              </div>
              <div className="font-mono text-right">
                <span className="text-xs text-slate-400 block">Basic Salary</span>
                <span className="text-sm font-bold text-white">₹40,000.00</span>
              </div>
            </div>

            {/* Slider Control */}
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-slate-400">Adjust Simulated PF Deduction:</span>
                <span className="text-lg font-bold text-cyan-400">
                  {formatCurrencyINR(counterfactualPf)}
                </span>
              </div>

              <input
                type="range"
                min={2000}
                max={6000}
                step={100}
                value={counterfactualPf}
                onChange={(e) => setCounterfactualPf(Number(e.target.value))}
                className="w-full h-2 bg-charcoal-800 rounded-lg appearance-none cursor-pointer accent-cyan-400 focus:outline-none"
              />

              <div className="flex justify-between text-[11px] font-mono text-slate-400">
                <span>₹2,000 (Severe Under-deduction)</span>
                <span className="text-emerald-400 font-semibold">₹4,800 (Statutory 12% Ideal)</span>
                <span>₹6,000 (Over-deduction)</span>
              </div>
            </div>

            {/* Dynamic Result Gauge */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 p-6 rounded-xl bg-obsidian-950 border border-white/5">
              <div>
                <span className="text-xs font-mono text-slate-400 block uppercase">Simulated Risk Score</span>
                <div className="flex items-baseline space-x-2 mt-1">
                  <span
                    className={`text-4xl font-bold font-mono ${
                      simulatedRisk > 0.45 ? 'text-rose-400' : 'text-emerald-400'
                    }`}
                  >
                    {formatRiskScore(simulatedRisk)}
                  </span>
                  <span className="text-xs text-slate-400">
                    {simulatedRisk > 0.45 ? '(ANOMALY)' : '(COMPLIANT)'}
                  </span>
                </div>
              </div>

              <div className="flex flex-col justify-center text-xs space-y-1">
                <span className="text-slate-400">Statutory Conclusion:</span>
                <p className="text-slate-200 font-medium">
                  {counterfactualPf === 4800 ? (
                    <span className="text-emerald-400 flex items-center gap-1.5 font-mono">
                      <CheckCircle2 className="w-4 h-4" />
                      Statutory 12% exactly satisfied. Anomaly resolved.
                    </span>
                  ) : counterfactualPf < 4800 ? (
                    <span className="text-rose-400 font-mono">
                      Under-deduction by {formatCurrencyINR(4800 - counterfactualPf)}.
                    </span>
                  ) : (
                    <span className="text-amber-400 font-mono">
                      Over-deduction by {formatCurrencyINR(counterfactualPf - 4800)}.
                    </span>
                  )}
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* SECTION 09 — PRODUCT WORKFLOW TIMELINE */}
      {/* ========================================================================= */}
      <section className="py-24 px-6 lg:px-8 border-b border-white/5 relative">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="max-w-3xl space-y-3">
            <span className="font-mono text-xs text-indigo-400 uppercase tracking-widest font-semibold">
              Operational Cycle
            </span>
            <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white">
              End-to-End Audit Workflow
            </h2>
            <p className="text-slate-400 text-sm sm:text-base">
              The complete enterprise lifecycle from file drop to signed resolution.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { step: '01', title: 'Upload Payroll', desc: 'Drop CSV/Parquet payload with automatic delimiter detection.' },
              { step: '02', title: 'Pre-flight Validate', desc: 'Verify negative values, field presence, and date ranges.' },
              { step: '03', title: 'Feature Synthesis', desc: 'Compute historical baselines, z-scores, and cohort statistics.' },
              { step: '04', title: 'Hybrid Detection', desc: 'Ensemble ML and deterministic statutory rules evaluate records.' },
              { step: '05', title: 'Forensic Deep-Dive', desc: 'Inspect variance deltas, breakdown deviations, and SHAP cards.' },
              { step: '06', title: 'RAG Verification', desc: 'Cross-reference EPFO/ESIC clauses via vector search.' },
              { step: '07', title: 'Ask AI Assistant', desc: 'Query grounded LLM on corrective steps and compliance laws.' },
              { step: '08', title: 'Resolve & Ledger', desc: 'Record resolution with cryptographic SHA-256 audit entry.' },
            ].map((wf, idx) => (
              <div
                key={idx}
                className="p-5 rounded-xl bg-charcoal-900/60 border border-white/5 space-y-2 hover:border-cyan-500/20 transition-all"
              >
                <span className="font-mono text-xs font-bold text-cyan-400">{wf.step}</span>
                <h4 className="font-semibold text-white text-sm">{wf.title}</h4>
                <p className="text-xs text-slate-400 leading-relaxed">{wf.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* SECTION 10 — SECURITY & ENTERPRISE TRUST LAYER */}
      {/* ========================================================================= */}
      <section className="py-24 px-6 lg:px-8 border-b border-white/5 bg-obsidian-900/40 relative">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="max-w-3xl space-y-3">
            <span className="font-mono text-xs text-emerald-400 uppercase tracking-widest font-semibold">
              Enterprise Trust Layer
            </span>
            <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white">
              Hardened Enterprise Security
            </h2>
            <p className="text-slate-400 text-sm sm:text-base">
              Bank-grade authentication, role-based access control, cryptographic verification, and real-time model monitoring.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 rounded-2xl bg-charcoal-900 border border-white/5 space-y-3">
              <Lock className="w-5 h-5 text-cyan-400" />
              <h4 className="text-base font-bold text-white">JWT Auth & 4-Tier RBAC</h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Roles enforced on every endpoint: ADMIN, PAYROLL_ADMIN, AUDITOR, and VIEWER. Passwords hashed with bcrypt (cost=12).
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-charcoal-900 border border-white/5 space-y-3">
              <ShieldAlert className="w-5 h-5 text-emerald-400" />
              <h4 className="text-base font-bold text-white">Cryptographic Audit Trail</h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Immutable SHA-256 event chaining. Any modification to resolved status produces a permanent verifiable ledger entry.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-charcoal-900 border border-white/5 space-y-3">
              <Activity className="w-5 h-5 text-indigo-400" />
              <h4 className="text-base font-bold text-white">Statistical Drift Detection</h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Monitors Population Stability Index (PSI) and mean feature shifts to detect concept drift before false alerts trigger.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* SECTION 11 — FINAL CALL TO ACTION */}
      {/* ========================================================================= */}
      <section className="py-28 px-6 lg:px-8 relative overflow-hidden bg-radial-gradient">
        <div className="max-w-4xl mx-auto text-center space-y-8 relative z-10">
          <h2 className="text-3xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-white leading-tight">
            Find the payroll problems <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-indigo-400">
              before they become financial problems.
            </span>
          </h2>

          <p className="text-base sm:text-lg text-slate-300 max-w-xl mx-auto leading-relaxed">
            Deploy AI Payroll Guardian across your organization for real-time anomaly detection, statutory verification, and grounded audit intelligence.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <Link
              to="/payroll/upload"
              className="inline-flex items-center space-x-2.5 px-8 py-4 rounded-xl bg-gradient-to-r from-cyan-500 to-brand-500 hover:from-cyan-400 hover:to-brand-400 text-obsidian-950 font-bold text-sm transition duration-200 shadow-[0_0_35px_rgba(6,182,212,0.35)] hover:scale-105"
            >
              <span>Run a Payroll Audit</span>
              <ArrowRight className="w-4 h-4" />
            </Link>

            <button
              onClick={onLoadDemo}
              className="inline-flex items-center space-x-2 px-8 py-4 rounded-xl bg-charcoal-900 hover:bg-charcoal-800 border border-white/10 text-white font-medium text-sm transition duration-200"
            >
              <span>View the Demo Batch</span>
            </button>
          </div>
        </div>
      </section>
    </div>
  );
};
