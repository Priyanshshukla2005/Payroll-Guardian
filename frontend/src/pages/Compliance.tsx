import React from 'react';
import { BookOpen, Scale, FileText } from 'lucide-react';
import { ComplianceSearchBox } from '../components/compliance/ComplianceSearchBox';

export const Compliance: React.FC = () => {
  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-xs font-mono font-semibold text-cyan-400 uppercase tracking-widest mb-1.5">
          <BookOpen className="w-4 h-4" />
          <span>Statutory RAG Knowledge Base</span>
        </div>
        <h2 className="text-3xl font-bold text-white tracking-tight">Compliance & Policy Search</h2>
        <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
          Search indexed statutory labor acts, state tax rules, and internal enterprise policies with strict date- and jurisdiction-awareness.
        </p>
      </div>

      {/* 3-Tier Taxonomy Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-5 rounded-2xl bg-charcoal-900 border border-white/10 space-y-2">
          <div className="flex items-center gap-2 text-cyan-400 text-xs font-mono font-bold uppercase">
            <Scale className="w-4 h-4" />
            <span>Tier 1: Federal Acts</span>
          </div>
          <p className="text-xs text-slate-200 font-semibold">EPFO Act 1952, ESIC Act 1948, IT Sec 192</p>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Highest authority legal statutes governing mandatory payroll deductions.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-charcoal-900 border border-white/10 space-y-2">
          <div className="flex items-center gap-2 text-indigo-400 text-xs font-mono font-bold uppercase">
            <BookOpen className="w-4 h-4" />
            <span>Tier 2: State Mandates</span>
          </div>
          <p className="text-xs text-slate-200 font-semibold">Maharashtra PT Act 1975, Karnataka PT Act 1976</p>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            State-specific tax slabs, exemptions, and compliance schedules.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-charcoal-900 border border-white/10 space-y-2">
          <div className="flex items-center gap-2 text-emerald-400 text-xs font-mono font-bold uppercase">
            <FileText className="w-4 h-4" />
            <span>Tier 3: Corporate Policy</span>
          </div>
          <p className="text-xs text-slate-200 font-semibold">Overtime Guidelines, Festive Bonus Caps</p>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Organizational caps, allowance ratios, and attendance baselines.
          </p>
        </div>
      </div>

      {/* Interactive Search Tool */}
      <ComplianceSearchBox />
    </div>
  );
};
