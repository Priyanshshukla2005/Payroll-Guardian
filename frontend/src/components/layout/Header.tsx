import React, { useState } from 'react';
import { Calendar, UploadCloud, Shield, History, Cpu } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { AuthUser, UserRole } from '../../types/api';
import { LoginModal } from '../auth/LoginModal';
import { AuditTimelineModal } from '../audit/AuditTimelineModal';

interface Props {
  activePeriod?: string;
  analysisId?: string;
  currentUser: AuthUser | null;
  onUserChange: (user: AuthUser) => void;
}

export const Header: React.FC<Props> = ({
  activePeriod = '2024-06',
  analysisId,
  currentUser,
  onUserChange,
}) => {
  const location = useLocation();
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [isAuditOpen, setIsAuditOpen] = useState(false);

  const getPageTitle = () => {
    const path = location.pathname;
    if (path === '/' || path === '/dashboard') return 'Audit Overview';
    if (path.startsWith('/payroll/upload')) return 'Payroll Ingestion';
    if (path.startsWith('/analysis')) return 'Anomaly Inspection';
    if (path.startsWith('/anomalies')) return 'Employee Audit Deepdive';
    if (path.startsWith('/compliance')) return 'Statutory Compliance Knowledge';
    if (path.startsWith('/assistant')) return 'Payroll AI Assistant';
    return 'Payroll Security Platform';
  };

  const getRoleBadgeStyle = (role?: UserRole) => {
    switch (role) {
      case 'ADMIN':
        return 'border-purple-500/40 bg-purple-950/40 text-purple-300';
      case 'PAYROLL_ADMIN':
        return 'border-brand-500/40 bg-brand-950/40 text-brand-300';
      case 'AUDITOR':
        return 'border-amber-500/40 bg-amber-950/40 text-amber-300';
      case 'VIEWER':
      default:
        return 'border-slate-600/40 bg-slate-800/40 text-slate-400';
    }
  };

  return (
    <>
      <header className="h-16 bg-slate-900/80 backdrop-blur-md border-b border-slate-800 px-8 flex items-center justify-between sticky top-0 z-30">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-bold text-white tracking-tight">{getPageTitle()}</h2>
          <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700 text-xs text-slate-300">
            <Calendar className="w-3.5 h-3.5 text-brand-400" />
            <span>Period: <strong className="text-white font-mono">{activePeriod}</strong></span>
          </div>

          {/* Model Versioning Badge */}
          <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-950/80 border border-slate-800 text-[10px] font-mono text-slate-400">
            <Cpu className="w-3 h-3 text-brand-400" />
            <span>HybridDetector_v2</span>
            <span className="text-slate-600">|</span>
            <span>Thr: 0.45</span>
            <span className="text-slate-600">|</span>
            <span>RAG: 2024_06</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {analysisId && (
            <button
              onClick={() => setIsAuditOpen(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-xs font-mono text-slate-300 transition"
              title="View Audit Trail for this Analysis"
            >
              <History className="w-3.5 h-3.5 text-brand-400" />
              <span>Audit Trail</span>
            </button>
          )}

          {/* Role Session Badge & Switcher */}
          <button
            onClick={() => setIsLoginOpen(true)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-medium transition hover:scale-105 ${getRoleBadgeStyle(
              currentUser?.role
            )}`}
            title="Click to Switch Role or Re-authenticate"
          >
            <Shield className="w-3.5 h-3.5" />
            <span>{currentUser?.role || 'PAYROLL_ADMIN'}</span>
          </button>

          {/* Upload Action */}
          {currentUser?.role !== 'VIEWER' ? (
            <Link
              to="/payroll/upload"
              className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-medium text-xs shadow-md shadow-brand-600/20 transition duration-150"
            >
              <UploadCloud className="w-3.5 h-3.5" />
              <span>Upload Batch</span>
            </Link>
          ) : (
            <span className="text-[11px] text-slate-500 italic px-2 py-1 bg-slate-900 rounded border border-slate-800">
              Read-Only Mode
            </span>
          )}
        </div>
      </header>

      {/* Modals */}
      <LoginModal
        isOpen={isLoginOpen}
        onClose={() => setIsLoginOpen(false)}
        currentUser={currentUser}
        onLoginSuccess={onUserChange}
      />
      <AuditTimelineModal
        isOpen={isAuditOpen}
        onClose={() => setIsAuditOpen(false)}
        analysisId={analysisId}
      />
    </>
  );
};
