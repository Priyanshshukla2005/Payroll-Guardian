import React from 'react';
import { Sparkles } from 'lucide-react';

interface Props {
  onSelectPrompt: (prompt: string) => void;
}

export const PromptSuggestions: React.FC<Props> = ({ onSelectPrompt }) => {
  const suggestions = [
    'What is the statutory PF contribution formula under Section 6 of EPFO Act 1952?',
    'What are the wage limits and employee rates for ESIC deduction in India?',
    'How should an auditor reconcile overtime pay exceeding departmental thresholds?',
    'What are the state-level professional tax deduction slabs for Maharashtra and Karnataka?',
  ];

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1.5 text-xs text-slate-400 font-semibold uppercase tracking-wider">
        <Sparkles className="w-3.5 h-3.5 text-brand-400" />
        <span>Suggested Compliance Inquiries</span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {suggestions.map((s, idx) => (
          <button
            key={idx}
            onClick={() => onSelectPrompt(s)}
            className="text-left p-3 rounded-xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800 hover:border-brand-500/30 text-xs text-slate-300 transition duration-150 leading-relaxed shadow-sm"
          >
            "{s}"
          </button>
        ))}
      </div>
    </div>
  );
};
