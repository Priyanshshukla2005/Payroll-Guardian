import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Clock, Cpu, FileSearch } from 'lucide-react';
import { AnalysisResponse } from '../types/api';
import { payrollApi } from '../services/payrollApi';
import { MetricCards } from '../components/dashboard/MetricCards';
import { AnomalyTable } from '../components/anomalies/AnomalyTable';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { EmptyState } from '../components/common/EmptyState';

interface Props {
  currentAnalysis: AnalysisResponse | null;
  onSetCurrentAnalysis: (analysis: AnalysisResponse) => void;
}

export const Analysis: React.FC<Props> = ({ currentAnalysis, onSetCurrentAnalysis }) => {
  const { analysisId } = useParams<{ analysisId?: string }>();
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(currentAnalysis);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<any>(null);

  useEffect(() => {
    if (analysisId) {
      if (currentAnalysis && currentAnalysis.analysis_id === analysisId) {
        setAnalysis(currentAnalysis);
      } else {
        setLoading(true);
        setError(null);
        payrollApi
          .getAnalysis(analysisId)
          .then((data) => {
            setAnalysis(data);
            onSetCurrentAnalysis(data);
          })
          .catch((err) => setError(err))
          .finally(() => setLoading(false));
      }
    } else if (currentAnalysis) {
      setAnalysis(currentAnalysis);
    }
  }, [analysisId, currentAnalysis, onSetCurrentAnalysis]);

  if (loading) {
    return <LoadingSpinner message="Retrieving payroll audit batch..." size="lg" />;
  }

  if (error) {
    return <ErrorAlert title="Failed to Load Analysis" error={error} />;
  }

  if (!analysis) {
    return (
      <EmptyState
        icon={FileSearch}
        title="No Active Audit Batch Selected"
        description="Please upload a payroll batch or select a completed audit report to investigate anomalies."
        actionText="Upload Payroll File"
        actionHref="/payroll/upload"
      />
    );
  }

  return (
    <div className="space-y-8">
      {/* Batch Header Bar */}
      <div className="bg-charcoal-900 border border-white/10 rounded-2xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xl">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 font-bold border border-emerald-500/20">
              {analysis.status}
            </span>
            <span className="text-xs font-mono text-slate-400">
              BATCH ID: <strong className="text-slate-200">{analysis.analysis_id}</strong>
            </span>
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">
            Payroll Audit Batch — <span className="font-mono text-cyan-400">{analysis.payroll_period}</span>
          </h2>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 font-mono">
          <div className="flex items-center gap-1.5 bg-obsidian-950 px-3 py-1.5 rounded-lg border border-white/5">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span>Engine: <strong className="text-slate-200">{analysis.model_version}</strong></span>
          </div>

          <div className="flex items-center gap-1.5 bg-obsidian-950 px-3 py-1.5 rounded-lg border border-white/5">
            <Clock className="w-3.5 h-3.5 text-amber-400" />
            <span>Execution: <strong className="text-slate-200">{analysis.duration_ms.toFixed(1)}ms</strong></span>
          </div>
        </div>
      </div>

      {/* Metrics Cards */}
      <MetricCards summary={analysis.summary} />

      {/* Anomaly Table */}
      <AnomalyTable
        anomalies={analysis.anomalies}
        analysisId={analysis.analysis_id}
      />
    </div>
  );
};
