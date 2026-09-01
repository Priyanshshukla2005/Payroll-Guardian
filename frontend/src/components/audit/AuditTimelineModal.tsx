import React, { useEffect, useState } from 'react';
import { History, Clock, User, X } from 'lucide-react';
import { auditApi } from '../../services/auditApi';
import { AuditEventItem } from '../../types/api';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  analysisId?: string;
}

export const AuditTimelineModal: React.FC<Props> = ({ isOpen, onClose, analysisId }) => {
  const [events, setEvents] = useState<AuditEventItem[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && analysisId) {
      setLoading(true);
      auditApi
        .getAnalysisTimeline(analysisId)
        .then((data) => {
          setEvents(data || []);
        })
        .catch(() => {
          // Fallback to recent events if analysis-specific not found
          auditApi.listEvents(20).then((allEvents) => setEvents(allEvents || []));
        })
        .finally(() => setLoading(false));
    }
  }, [isOpen, analysisId]);

  if (!isOpen) return null;

  const getEventBadge = (eventType: string) => {
    if (eventType.includes('COMPLETED') || eventType.includes('RESOLVED')) {
      return 'border-emerald-500/30 bg-emerald-950/30 text-emerald-400';
    }
    if (eventType.includes('STARTED') || eventType.includes('UPLOADED')) {
      return 'border-brand-500/30 bg-brand-950/30 text-brand-400';
    }
    if (eventType.includes('ANOMALY')) {
      return 'border-amber-500/30 bg-amber-950/30 text-amber-400';
    }
    return 'border-slate-700 bg-slate-800 text-slate-300';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-brand-600/20 border border-brand-500/30 text-brand-400">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Immutable Audit Trail</h3>
              <p className="text-xs text-slate-400 font-mono">
                Analysis: {analysisId || 'Platform-Wide Events'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Timeline body */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1">
          {loading ? (
            <div className="py-12 text-center text-slate-400 text-xs">Loading audit events...</div>
          ) : events.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-xs">
              No audit events recorded for this analysis batch yet.
            </div>
          ) : (
            <div className="relative pl-6 border-l border-slate-800 space-y-6">
              {events.map((evt, idx) => (
                <div key={evt.event_id || idx} className="relative group">
                  {/* Dot */}
                  <div className="absolute -left-[31px] top-1 w-3.5 h-3.5 rounded-full bg-slate-900 border-2 border-brand-500 shadow-sm" />

                  <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded-md border ${getEventBadge(evt.event_type)}`}>
                        {evt.event_type}
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {evt.timestamp ? new Date(evt.timestamp).toLocaleString() : 'N/A'}
                      </span>
                    </div>

                    <div className="flex items-center gap-4 text-xs text-slate-400 mt-2">
                      <div className="flex items-center gap-1">
                        <User className="w-3 h-3 text-slate-500" />
                        <span>Actor: <strong className="text-slate-300 font-mono">{evt.actor_id}</strong></span>
                      </div>
                      {evt.request_id && (
                        <div className="text-[10px] font-mono text-slate-500">
                          req: {evt.request_id.substring(0, 12)}...
                        </div>
                      )}
                    </div>

                    {evt.metadata && Object.keys(evt.metadata).length > 0 && (
                      <div className="mt-2.5 p-2 rounded-lg bg-slate-900 border border-slate-800/60 font-mono text-[10px] text-slate-400">
                        {JSON.stringify(evt.metadata, null, 2)}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
