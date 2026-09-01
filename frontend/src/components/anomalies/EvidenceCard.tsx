import React from 'react';
import { ShieldAlert, Activity, CheckSquare, History, Users2 } from 'lucide-react';
import { AnomalyRecordResult } from '../../types/api';

interface Props {
  anomaly: AnomalyRecordResult;
}

export const EvidenceCard: React.FC<Props> = ({ anomaly }) => {
  return (
    <div className="card-glass rounded-2xl p-6 space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2.5">
          <ShieldAlert className="w-5 h-5 text-brand-400" />
          <h3 className="font-bold text-white text-base">Structured Evidence Card</h3>
        </div>
        <span className="text-xs font-mono text-slate-400">
          Source: HybridPayrollDetector_V2
        </span>
      </div>

      {/* Top Statistical Signals */}
      <div>
        <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
          <Activity className="w-4 h-4 text-brand-400" />
          Detected Anomaly Signals
        </h4>
        <div className="space-y-2">
          {anomaly.evidence.map((signal, idx) => (
            <div
              key={idx}
              className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 text-xs text-slate-200 flex items-start gap-2.5"
            >
              <span className="w-5 h-5 rounded-md bg-brand-500/10 text-brand-400 flex items-center justify-center font-bold text-[11px] shrink-0">
                {idx + 1}
              </span>
              <span className="leading-relaxed">{signal}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Rule Violations */}
      {anomaly.rule_violations.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider text-rose-400 mb-3 flex items-center gap-2">
            <CheckSquare className="w-4 h-4 text-rose-400" />
            Deterministic Rule Triggers
          </h4>
          <div className="flex flex-wrap gap-2">
            {anomaly.rule_violations.map((rule) => (
              <span
                key={rule}
                className="px-3 py-1 rounded-lg bg-rose-500/10 text-rose-300 border border-rose-500/20 font-mono text-xs font-semibold"
              >
                {rule}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Historical & Peer Comparison Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
        {/* Historical Context */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-slate-300">
            <History className="w-4 h-4 text-blue-400" />
            <span>Historical Baseline Comparison</span>
          </div>
          {Object.keys(anomaly.historical_comparison).length > 0 ? (
            <div className="space-y-1.5 text-xs text-slate-400 font-mono">
              {Object.entries(anomaly.historical_comparison).map(([k, v]) => (
                <div key={k} className="flex justify-between">
                  <span className="text-slate-500">{k.replace(/_/g, ' ')}:</span>
                  <span className="text-slate-200 font-semibold">{String(v)}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic">Cold-start or single historical period</p>
          )}
        </div>

        {/* Peer Group Benchmarks */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-slate-300">
            <Users2 className="w-4 h-4 text-purple-400" />
            <span>Peer Cohort Benchmark</span>
          </div>
          {Object.keys(anomaly.peer_comparison).length > 0 ? (
            <div className="space-y-1.5 text-xs text-slate-400 font-mono">
              {Object.entries(anomaly.peer_comparison).map(([k, v]) => (
                <div key={k} className="flex justify-between">
                  <span className="text-slate-500">{k.replace(/_/g, ' ')}:</span>
                  <span className="text-slate-200 font-semibold">{String(v)}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic">No peer group deviations triggered</p>
          )}
        </div>
      </div>
    </div>
  );
};
