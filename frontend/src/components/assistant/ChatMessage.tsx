import React from 'react';
import { Bot, User, ShieldCheck, AlertTriangle, CheckCircle2, BookOpen } from 'lucide-react';
import { AssistantQueryResponse } from '../../types/api';
import { CitationCard } from './CitationCard';

export interface ChatEntry {
  id: string;
  sender: 'user' | 'assistant';
  text?: string;
  response?: AssistantQueryResponse;
  timestamp: string;
}

interface Props {
  entry: ChatEntry;
}

export const ChatMessage: React.FC<Props> = ({ entry }) => {
  const isUser = entry.sender === 'user';

  if (isUser) {
    return (
      <div className="flex items-start gap-3 justify-end">
        <div className="max-w-2xl bg-brand-600 text-white rounded-2xl rounded-tr-sm p-4 text-sm shadow-md">
          <p className="leading-relaxed whitespace-pre-wrap">{entry.text}</p>
          <span className="block text-[10px] text-brand-200 mt-1 text-right">{entry.timestamp}</span>
        </div>
        <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 shrink-0">
          <User className="w-4 h-4" />
        </div>
      </div>
    );
  }

  const res = entry.response;
  if (!res) return null;

  return (
    <div className="flex items-start gap-3 justify-start">
      <div className="w-8 h-8 rounded-full bg-brand-600/20 border border-brand-500/30 flex items-center justify-center text-brand-400 shrink-0">
        <Bot className="w-4 h-4" />
      </div>

      <div className="max-w-3xl card-glass rounded-2xl rounded-tl-sm p-5 space-y-4 text-sm border-slate-800 shadow-lg">
        {/* Assistant Main Answer */}
        <div className="space-y-2">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
            <span className="font-bold text-white text-xs flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-brand-400" />
              Grounded AI Response
            </span>
            <span className="text-[10px] font-mono text-slate-500">{entry.timestamp}</span>
          </div>

          <p className="text-slate-200 leading-relaxed whitespace-pre-wrap">{res.answer}</p>
        </div>

        {/* Safety / Refusal Notification */}
        {res.uncertainty_or_refusal && (
          <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="font-semibold text-amber-200">Groundedness / Boundary Notice</p>
              <p>{res.uncertainty_or_refusal}</p>
            </div>
          </div>
        )}

        {/* Category Distinctions */}
        {res.category_distinction && Object.keys(res.category_distinction).length > 0 && (
          <div className="space-y-2 pt-1">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block">
              Source Categorization
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              {Object.entries(res.category_distinction).map(([category, items]) => (
                <div key={category} className="p-2.5 rounded-lg bg-slate-900/70 border border-slate-800">
                  <span className="font-semibold text-slate-300 block mb-1 text-[11px] uppercase">
                    {category.replace(/_/g, ' ')}
                  </span>
                  <ul className="space-y-0.5 text-slate-400 text-[11px]">
                    {items.map((it, i) => (
                      <li key={i}>• {it}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Supporting Citations */}
        {res.citations && res.citations.length > 0 && (
          <div className="space-y-2 pt-1">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <BookOpen className="w-3.5 h-3.5 text-brand-400" />
              Authoritative Citations
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {res.citations.map((c, i) => (
                <CitationCard key={i} citation={c} />
              ))}
            </div>
          </div>
        )}

        {/* Suggested Next Steps */}
        {res.suggested_next_steps && res.suggested_next_steps.length > 0 && (
          <div className="space-y-1.5 pt-1">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-emerald-400 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              Suggested Verification Steps
            </span>
            <ul className="space-y-1 text-xs text-slate-300">
              {res.suggested_next_steps.map((step, i) => (
                <li key={i} className="flex items-start gap-1.5 bg-emerald-500/5 p-2 rounded-lg border border-emerald-500/20">
                  <span className="text-emerald-400 font-bold">✓</span>
                  <span>{step}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Grounded Disclaimer */}
        <p className="text-[10px] text-slate-500 italic pt-2 border-t border-slate-800/60">
          {res.disclaimer}
        </p>
      </div>
    </div>
  );
};
