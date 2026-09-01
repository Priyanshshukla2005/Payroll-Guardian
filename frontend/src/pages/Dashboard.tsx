import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, UploadCloud, FileSearch, Sparkles, AlertTriangle } from 'lucide-react';
import { AnalysisResponse } from '../types/api';
import { MetricCards } from '../components/dashboard/MetricCards';
import { RiskSeverityChart } from '../components/dashboard/RiskSeverityChart';
import { AnomalyTypeChart } from '../components/dashboard/AnomalyTypeChart';
import { EmptyState } from '../components/common/EmptyState';

interface Props {
  currentAnalysis: AnalysisResponse | null;
  onLoadDemo: () => void;
}

export const Dashboard: React.FC<Props> = ({ currentAnalysis, onLoadDemo }) => {
  return (
    <div className="space-y-8">
      {/* Top Welcome Banner */}
      <div className="bg-charcoal-900 border border-white/10 rounded-2xl p-8 relative overflow-hidden shadow-2xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="max-w-3xl space-y-3 relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-xs font-mono text-cyan-400">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Autonomous Payroll Compliance & Anomaly Audit</span>
          </div>
          <h2 className="text-2xl sm:text-4xl font-bold text-white tracking-tight leading-tight">
            Executive Audit Command Center
          </h2>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed max-w-2xl">
            Continuously audits employee compensation across supervised ML behavioral profiles, deterministic statutory rules (EPFO, ESIC, TDS), and grounded AI explanations.
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-3">
            <Link
              to="/payroll/upload"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-brand-500 hover:from-cyan-400 hover:to-brand-400 text-obsidian-950 font-bold text-xs shadow-lg shadow-cyan-500/20 transition-all duration-150 hover:scale-[1.02]"
            >
              <UploadCloud className="w-4 h-4" />
              <span>Upload Payroll Batch</span>
            </Link>

            {currentAnalysis && (
              <Link
                to={`/analysis/${currentAnalysis.analysis_id}`}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-charcoal-800 hover:bg-charcoal-700 text-slate-200 font-semibold text-xs border border-white/10 transition"
              >
                <FileSearch className="w-4 h-4 text-cyan-400" />
                <span>Inspect Current Audit ({currentAnalysis.anomalies.length} Flagged)</span>
              </Link>
            )}

            {!currentAnalysis && (
              <button
                type="button"
                onClick={onLoadDemo}
                className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-charcoal-800 hover:bg-charcoal-700 text-cyan-300 font-semibold text-xs border border-cyan-500/30 transition"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Load Sample Demo Batch</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Analysis Display or Empty State */}
      {!currentAnalysis ? (
        <EmptyState
          icon={AlertTriangle}
          title="No Payroll Batch Analyzed Yet"
          description="Upload a monthly payroll CSV or JSON batch to run automated anomaly detection, compliance checks, and grounded audit explanations."
          actionText="Upload Payroll File"
          actionHref="/payroll/upload"
        />
      ) : (
        <div className="space-y-8">
          {/* Executive Metrics Cards */}
          <MetricCards summary={currentAnalysis.summary} />

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <RiskSeverityChart summary={currentAnalysis.summary} />
            <AnomalyTypeChart anomalies={currentAnalysis.anomalies} />
          </div>

          {/* Quick Anomaly Preview CTA */}
          <div className="bg-charcoal-900 border border-white/10 rounded-2xl p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <h4 className="font-bold text-white text-base">
                Investigate Flagged Anomaly Records ({currentAnalysis.anomalies.length})
              </h4>
              <p className="text-xs text-slate-400 mt-1">
                Explore individual employee evidence cards, statutory compliance citations, and recommended audit actions.
              </p>
            </div>
            <Link
              to={`/analysis/${currentAnalysis.analysis_id}`}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-brand-500 hover:from-cyan-400 hover:to-brand-400 text-obsidian-950 font-bold text-xs shadow-md transition shrink-0"
            >
              Open Full Audit Inspection
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};
