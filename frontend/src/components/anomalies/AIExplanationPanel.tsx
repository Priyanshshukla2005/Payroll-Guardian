import React from 'react';
import { Sparkles, HelpCircle, CheckCircle, AlertTriangle, ShieldCheck } from 'lucide-react';
import { ExplanationItem } from '../../types/api';

interface Props {
  explanation: ExplanationItem;
}

export const AIExplanationPanel: React.FC<Props> = ({ explanation }) => {
  return (
    <div className="card-glass rounded-2xl p-6 space-y-6 border-brand-500/30 shadow-xl shadow-brand-950/20 relative overflow-hidden">
      {/* Glow highlight */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-brand-500/5 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-brand-500/10 text-brand-400 border border-brand-500/20">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-white text-base">Grounded AI Audit Explanation</h3>
            <p className="text-[11px] text-slate-400">
              Grounded exclusively in structured anomaly evidence and retrieved compliance knowledge
            </p>
          </div>
        </div>

        {explanation.fallback_mode ? (
          <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono border border-slate-700">
            Deterministic Fallback Mode
          </span>
        ) : (
          <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-brand-500/10 text-brand-300 font-semibold border border-brand-500/30 flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-brand-400" />
            Zero-Fabrication Verified
          </span>
        )}
      </div>

      {/* Explanation Title & Summary */}
      <div className="space-y-2">
        {explanation.title && (
          <h4 className="text-base font-bold text-slate-100">{explanation.title}</h4>
        )}
        <p className="text-sm text-slate-300 leading-relaxed bg-slate-900/60 p-4 rounded-xl border border-slate-800/80">
          {explanation.summary}
        </p>
      </div>

      {/* Why Flagged */}
      {explanation.why_flagged.length > 0 && (
        <div>
          <h5 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
            <HelpCircle className="w-3.5 h-3.5 text-brand-400" />
            Why Was This Record Flagged?
          </h5>
          <ul className="space-y-1.5">
            {explanation.why_flagged.map((item, idx) => (
              <li
                key={idx}
                className="text-xs text-slate-300 flex items-start gap-2 bg-slate-900/40 p-2.5 rounded-lg border border-slate-800/40"
              >
                <span className="text-brand-400 font-bold">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommended Actions */}
      {explanation.recommended_actions.length > 0 && (
        <div>
          <h5 className="text-xs font-semibold uppercase tracking-wider text-emerald-400 mb-2 flex items-center gap-1.5">
            <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
            Recommended Verification Steps
          </h5>
          <ul className="space-y-1.5">
            {explanation.recommended_actions.map((action, idx) => (
              <li
                key={idx}
                className="text-xs text-slate-200 flex items-start gap-2 bg-emerald-500/5 border border-emerald-500/20 p-2.5 rounded-lg"
              >
                <span className="text-emerald-400 font-bold">✓</span>
                <span>{action}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Uncertainty Note */}
      {explanation.uncertainty && (
        <div className="flex items-start gap-2 text-xs text-amber-300 bg-amber-500/10 border border-amber-500/20 p-3 rounded-xl">
          <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400 mt-0.5" />
          <span>{explanation.uncertainty}</span>
        </div>
      )}

      {/* Disclaimer */}
      <div className="pt-2 border-t border-slate-800/80 text-[11px] text-slate-500 italic">
        ⚠️ AI-assisted explanation for payroll auditor review. Must be verified with official statutory regulations and internal policies. Not legal advice.
      </div>
    </div>
  );
};
