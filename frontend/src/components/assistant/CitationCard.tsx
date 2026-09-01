import React from 'react';
import { Scale, FileText } from 'lucide-react';
import { ComplianceSourceItem } from '../../types/api';

interface Props {
  citation: ComplianceSourceItem;
}

export const CitationCard: React.FC<Props> = ({ citation }) => {
  const isStatutory = citation.authority_level?.includes('STATUTORY') || citation.document_id.includes('ACT');

  return (
    <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 text-xs space-y-1.5 hover:border-brand-500/30 transition">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          {isStatutory ? (
            <Scale className="w-3.5 h-3.5 text-brand-400" />
          ) : (
            <FileText className="w-3.5 h-3.5 text-purple-400" />
          )}
          <span className="font-mono font-bold text-slate-200">{citation.document_id}</span>
        </div>
        <span className="font-mono text-[11px] text-brand-400 font-semibold">{citation.citation}</span>
      </div>

      {citation.title && <p className="text-slate-300 font-medium">{citation.title}</p>}

      <div className="flex gap-3 text-[11px] text-slate-400 font-mono">
        {citation.section && <span>Sec: <strong className="text-slate-300">{citation.section}</strong></span>}
        {citation.page && <span>Page: <strong className="text-slate-300">{citation.page}</strong></span>}
      </div>
    </div>
  );
};
