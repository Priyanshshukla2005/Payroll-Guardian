import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, User, Bot, Building, Briefcase, CheckCircle2, ShieldCheck } from 'lucide-react';
import { AnomalyRecordResult, AnalysisResponse } from '../types/api';
import { anomalyApi } from '../services/anomalyApi';
import { auditApi } from '../services/auditApi';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { EvidenceCard } from '../components/anomalies/EvidenceCard';
import { ComplianceSourcePanel } from '../components/anomalies/ComplianceSourcePanel';
import { AIExplanationPanel } from '../components/anomalies/AIExplanationPanel';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { formatRiskScore } from '../utils/formatters';

interface Props {
  currentAnalysis: AnalysisResponse | null;
}

export const AnomalyDetails: React.FC<Props> = ({ currentAnalysis }) => {
  const { analysisId, employeeId } = useParams<{ analysisId: string; employeeId: string }>();
  const [anomaly, setAnomaly] = useState<AnomalyRecordResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<any>(null);

  // Resolution State
  const [resolutionStatus, setResolutionStatus] = useState<'RESOLVED' | 'FALSE_POSITIVE' | 'UNDER_REVIEW'>('RESOLVED');
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [isResolving, setIsResolving] = useState(false);
  const [resolvedSuccessMsg, setResolvedSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!analysisId || !employeeId) return;

    // Check in currentAnalysis first
    if (currentAnalysis && currentAnalysis.analysis_id === analysisId) {
      const found = currentAnalysis.anomalies.find((a) => a.employee_id === employeeId);
      if (found) {
        setAnomaly(found);
        return;
      }
    }

    // Fetch from backend API
    setLoading(true);
    setError(null);
    anomalyApi
      .getEmployeeAnomaly(analysisId, employeeId)
      .then((data) => setAnomaly(data))
      .catch((err) => setError(err))
      .finally(() => setLoading(false));
  }, [analysisId, employeeId, currentAnalysis]);

  const handleResolveAnomaly = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!analysisId || !employeeId || !resolutionNotes.trim()) return;

    setIsResolving(true);
    try {
      await auditApi.resolveAnomaly(analysisId, employeeId, resolutionStatus, resolutionNotes);
      setResolvedSuccessMsg(`Anomaly status successfully updated to '${resolutionStatus}'. Audit trail logged.`);
      setResolutionNotes('');
    } catch (err: any) {
      setError(err);
    } finally {
      setIsResolving(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Retrieving employee audit evidence & citations..." size="lg" />;
  }

  if (error) {
    return <ErrorAlert title="Failed to Load Anomaly Record" error={error} />;
  }

  if (!anomaly) {
    return (
      <div className="card-glass rounded-2xl p-12 text-center text-slate-400">
        <p className="text-sm">Employee record not found in this audit analysis.</p>
        <Link
          to={analysisId ? `/analysis/${analysisId}` : '/analysis'}
          className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 text-slate-200 text-xs font-semibold"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Analysis
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Top Navigation & Header */}
      <div>
        <Link
          to={`/analysis/${analysisId}`}
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-brand-300 transition mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Audit Batch ({analysisId?.substring(0, 12)}...)</span>
        </Link>

        <div className="card-glass rounded-3xl p-6 border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-brand-600/10 border border-brand-500/30 flex items-center justify-center text-brand-400 shadow-inner">
              <User className="w-7 h-7" />
            </div>

            <div>
              <div className="flex items-center gap-2 mb-1">
                <h2 className="text-2xl font-bold text-white font-mono">{anomaly.employee_id}</h2>
                <SeverityBadge severity={anomaly.severity} size="sm" />
              </div>
              <div className="flex items-center gap-4 text-xs text-slate-400">
                <span className="flex items-center gap-1">
                  <Building className="w-3.5 h-3.5 text-slate-500" />
                  {anomaly.department}
                </span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Briefcase className="w-3.5 h-3.5 text-slate-500" />
                  {anomaly.designation}
                </span>
                <span>•</span>
                <span className="font-mono text-slate-500">{anomaly.payroll_month}</span>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-4">
            {/* Calibrated Risk Score Card */}
            <div className="p-3.5 rounded-2xl bg-slate-900/90 border border-slate-800 text-right min-w-[130px]">
              <span className="text-[10px] uppercase font-bold text-slate-500 block tracking-wider">
                Risk Score
              </span>
              <span className="text-2xl font-extrabold font-mono text-brand-400">
                {formatRiskScore(anomaly.risk_score)}
              </span>
            </div>

            {/* Launch AI Assistant button preloaded with context */}
            <Link
              to={`/assistant?analysisId=${analysisId}&employeeId=${anomaly.employee_id}`}
              className="inline-flex items-center gap-2 px-5 py-3 rounded-2xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-lg shadow-brand-600/25 transition"
            >
              <Bot className="w-4 h-4" />
              <span>Ask AI Assistant</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Main Grid: Left = Evidence & Compliance; Right = AI Explanation + Resolution */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-6 space-y-8">
          <EvidenceCard anomaly={anomaly} />
          <ComplianceSourcePanel compliance={anomaly.compliance} />
        </div>

        <div className="lg:col-span-6 space-y-8">
          <AIExplanationPanel explanation={anomaly.explanation} />

          {/* Anomaly Audit Resolution Panel */}
          <div className="card-glass rounded-3xl p-6 border-slate-800 space-y-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-emerald-600/20 text-emerald-400 border border-emerald-500/30">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Statutory Audit Resolution</h3>
                <p className="text-xs text-slate-400">Record auditor sign-off and append to audit history</p>
              </div>
            </div>

            {resolvedSuccessMsg && (
              <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-800/60 text-emerald-300 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>{resolvedSuccessMsg}</span>
              </div>
            )}

            <form onSubmit={handleResolveAnomaly} className="space-y-4">
              <div className="grid grid-cols-3 gap-2">
                {(['RESOLVED', 'FALSE_POSITIVE', 'UNDER_REVIEW'] as const).map((st) => (
                  <button
                    key={st}
                    type="button"
                    onClick={() => setResolutionStatus(st)}
                    className={`py-2 px-3 rounded-xl border text-xs font-bold transition ${
                      resolutionStatus === st
                        ? 'border-brand-500 bg-brand-950/40 text-brand-300'
                        : 'border-slate-800 bg-slate-900 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {st.replace('_', ' ')}
                  </button>
                ))}
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Resolution / Audit Justification Notes
                </label>
                <textarea
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  rows={3}
                  placeholder="Provide audit reasoning (e.g., 'Corrective payroll adjustment scheduled in next cycle' or 'Verified legitimate bonus')..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 transition"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={isResolving || !resolutionNotes.trim()}
                className="w-full py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-bold shadow-lg shadow-emerald-600/20 transition flex items-center justify-center gap-2"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>{isResolving ? 'Submitting Resolution...' : 'Sign Off & Log Event'}</span>
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
