import React from 'react';
import { BookOpen, Scale, FileText } from 'lucide-react';
import { ComplianceStatusBlock } from '../../types/api';

interface Props {
  compliance: ComplianceStatusBlock;
}

export const ComplianceSourcePanel: React.FC<Props> = ({ compliance }) => {
  const isStatutory = (authority?: string) => {
    return authority?.toUpperCase().includes('STATUTORY') || authority?.toUpperCase().includes('ACT');
  };

  return (
    <div className="card-glass rounded-2xl p-6 space-y-5">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2.5">
          <BookOpen className="w-5 h-5 text-brand-400" />
          <h3 className="font-bold text-white text-base">Authoritative Compliance Context</h3>
        </div>
        <span
          className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
            compliance.status === 'FOUND'
              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
              : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
          }`}
        >
          {compliance.status === 'FOUND' ? 'Verified Statutory Match' : compliance.status}
        </span>
      </div>

      {compliance.sources.length === 0 ? (
        <div className="p-6 rounded-xl bg-slate-900/60 text-center text-slate-400 text-xs">
          <p>{compliance.no_answer_reason || 'No direct statutory mandate or internal policy matched this anomaly pattern.'}</p>
        </div>
      ) : (
        <div className="space-y-4">
          {compliance.sources.map((source, idx) => {
            const statutory = isStatutory(source.authority_level);
            return (
              <div
                key={idx}
                className={`p-4 rounded-xl border transition duration-150 ${
                  statutory
                    ? 'bg-slate-900/80 border-slate-700 hover:border-brand-500/40'
                    : 'bg-slate-900/50 border-slate-800 hover:border-purple-500/40'
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    {statutory ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-brand-500/10 text-brand-300 border border-brand-500/30 text-[11px] font-bold">
                        <Scale className="w-3 h-3" />
                        STATUTORY LAW
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/30 text-[11px] font-bold">
                        <FileText className="w-3 h-3" />
                        COMPANY POLICY
                      </span>
                    )}
                    <span className="font-mono text-xs font-bold text-slate-200">
                      {source.document_id}
                    </span>
                  </div>

                  <span className="text-xs font-mono text-brand-400 font-semibold">
                    {source.citation}
                  </span>
                </div>

                {source.title && (
                  <h5 className="text-sm font-semibold text-slate-100 mb-2">{source.title}</h5>
                )}

                <div className="flex flex-wrap gap-4 text-xs font-mono text-slate-400 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
                  {source.section && (
                    <div>
                      <span className="text-slate-500">Section: </span>
                      <span className="text-slate-300 font-semibold">{source.section}</span>
                    </div>
                  )}
                  {source.page && (
                    <div>
                      <span className="text-slate-500">Page: </span>
                      <span className="text-slate-300 font-semibold">{source.page}</span>
                    </div>
                  )}
                  {source.authority_level && (
                    <div>
                      <span className="text-slate-500">Tier: </span>
                      <span className="text-slate-300 font-semibold">{source.authority_level}</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
