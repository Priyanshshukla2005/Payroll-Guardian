import React from 'react';
import { BookOpen, Scale, FileText } from 'lucide-react';
import { ComplianceSearchBox } from '../components/compliance/ComplianceSearchBox';

export const Compliance: React.FC = () => {
  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-xs font-semibold text-brand-400 uppercase tracking-wider mb-1">
          <BookOpen className="w-4 h-4" />
          <span>Statutory RAG Knowledge Base</span>
        </div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Compliance & Policy Search</h2>
        <p className="text-xs text-slate-400 mt-1">
          Search indexed statutory labor acts, state tax rules, and internal enterprise policies with strict date- and jurisdiction-awareness.
        </p>
      </div>

      {/* 3-Tier Taxonomy Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center gap-2 text-brand-400 text-xs font-bold uppercase">
            <Scale className="w-4 h-4" />
            <span>Tier 1: Federal Acts</span>
          </div>
          <p className="text-xs text-slate-300 font-medium">EPFO Act 1952, ESIC Act 1948, Income Tax Sec 192</p>
          <p className="text-[11px] text-slate-500">Highest authority legal statutes governing mandatory payroll deductions.</p>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center gap-2 text-blue-400 text-xs font-bold uppercase">
            <BookOpen className="w-4 h-4" />
            <span>Tier 2: State Mandates</span>
          </div>
          <p className="text-xs text-slate-300 font-medium">Maharashtra PT Act 1975, Karnataka PT Act 1976</p>
          <p className="text-[11px] text-slate-500">State-specific tax slabs, exemptions, and compliance schedules.</p>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center gap-2 text-purple-400 text-xs font-bold uppercase">
            <FileText className="w-4 h-4" />
            <span>Tier 3: Corporate Policy</span>
          </div>
          <p className="text-xs text-slate-300 font-medium">Internal Overtime Guidelines, Festive Bonus Rules</p>
          <p className="text-[11px] text-slate-500">Organizational caps, allowance ratios, and attendance baselines.</p>
        </div>
      </div>

      {/* Interactive Search Tool */}
      <ComplianceSearchBox />
    </div>
  );
};
