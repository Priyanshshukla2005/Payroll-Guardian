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
      <div className="card-glass rounded-3xl p-8 relative overflow-hidden border-slate-800 bg-gradient-to-r from-slate-900/90 via-slate-900/60 to-slate-950">
        <div className="max-w-2xl space-y-3 relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-xs font-semibold text-brand-400">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Enterprise Multi-Layered AI Verification</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Autonomous Payroll Compliance & Anomaly Audit
          </h2>
          <p className="text-sm text-slate-300 leading-relaxed">
            Continuously audits employee compensation across supervised ML behavioral profiles, deterministic statutory rules (EPFO, ESIC, PT), and grounded AI explanations.
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Link
              to="/payroll/upload"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs shadow-lg shadow-brand-600/30 transition"
            >
              <UploadCloud className="w-4 h-4" />
              <span>Upload Payroll Batch</span>
            </Link>

            {currentAnalysis && (
              <Link
                to={`/analysis/${currentAnalysis.analysis_id}`}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs border border-slate-700 transition"
              >
                <FileSearch className="w-4 h-4" />
                <span>View Current Audit ({currentAnalysis.anomalies.length} Flagged)</span>
              </Link>
            )}

            {!currentAnalysis && (
              <button
                type="button"
                onClick={onLoadDemo}
                className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-800 text-brand-300 font-semibold text-xs border border-brand-500/30 transition"
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
          <div className="card-glass rounded-2xl p-6 flex flex-col sm:flex-row items-center justify-between gap-4 border-slate-800">
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
              className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs shadow-md transition shrink-0"
            >
              Open Full Audit Inspection
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};
