import React, { useState } from 'react';
import { UploadCloud, Shield, History, Cpu } from 'lucide-react';
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

  const navLinks = [
    { label: 'Overview', to: '/' },
    { label: 'Dashboard', to: '/dashboard' },
    { label: 'Ingestion', to: '/payroll/upload' },
    { label: 'Analysis', to: '/analysis' },
    { label: 'Compliance', to: '/compliance' },
    { label: 'Assistant', to: '/assistant' },
  ];

  const getRoleBadgeStyle = (role?: UserRole) => {
    switch (role) {
      case 'ADMIN':
        return 'border-purple-500/40 bg-purple-950/40 text-purple-300';
      case 'PAYROLL_ADMIN':
        return 'border-cyan-500/40 bg-cyan-950/40 text-cyan-300';
      case 'AUDITOR':
        return 'border-amber-500/40 bg-amber-950/40 text-amber-300';
      case 'VIEWER':
      default:
        return 'border-slate-700/60 bg-slate-800/40 text-slate-400';
    }
  };

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <>
      <header className="h-16 bg-obsidian-950/80 backdrop-blur-xl border-b border-white/5 px-6 lg:px-8 flex items-center justify-between sticky top-0 z-40">
        {/* Left: Brand + Navigation Pills */}
        <div className="flex items-center space-x-8">
          <Link to="/" className="flex items-center space-x-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 group-hover:border-cyan-400/60 group-hover:shadow-[0_0_15px_rgba(0,240,255,0.25)] transition-all duration-300">
              <Shield className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-semibold tracking-tight text-white flex items-center gap-1.5">
                Payroll Guardian
                <span className="hidden sm:inline-block px-1.5 py-0.2 text-[9px] font-mono rounded bg-white/10 text-slate-300 font-normal">
                  v2.0
                </span>
              </span>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center space-x-1">
            {navLinks.map((link) => {
              const active = isActive(link.to);
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-150 ${
                    active
                      ? 'bg-white/10 text-white font-semibold shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Right: Telemetry + Controls + Primary CTA */}
        <div className="flex items-center space-x-3">
          {/* Active Batch Status Badge */}
          <div className="hidden lg:flex items-center space-x-2 px-2.5 py-1 rounded-md bg-obsidian-900 border border-white/5 text-[11px] font-mono text-slate-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>Batch:</span>
            <span className="text-slate-200 font-semibold">{activePeriod}</span>
            <span className="text-white/20">|</span>
            <Cpu className="w-3 h-3 text-cyan-400" />
            <span>Hybrid v2</span>
          </div>

          {/* Audit Trail Modal Launcher */}
          {analysisId && (
            <button
              onClick={() => setIsAuditOpen(true)}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-obsidian-900 hover:bg-charcoal-800 border border-white/10 text-xs font-mono text-slate-300 transition hover:border-cyan-500/30"
              title="Inspect Cryptographic Audit Trail"
            >
              <History className="w-3.5 h-3.5 text-cyan-400" />
              <span className="hidden sm:inline">Audit Trail</span>
            </button>
          )}

          {/* Role Switcher Pill */}
          <button
            onClick={() => setIsLoginOpen(true)}
            className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg border text-xs font-mono font-medium transition duration-150 hover:brightness-110 ${getRoleBadgeStyle(
              currentUser?.role
            )}`}
            title="Switch User Role or Authenticate"
          >
            <Shield className="w-3.5 h-3.5" />
            <span>{currentUser?.role || 'PAYROLL_ADMIN'}</span>
          </button>

          {/* Primary Action Button */}
          {currentUser?.role !== 'VIEWER' ? (
            <Link
              to="/payroll/upload"
              className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-brand-500 hover:from-cyan-400 hover:to-brand-400 text-obsidian-950 font-semibold text-xs transition duration-200 shadow-[0_0_20px_rgba(6,182,212,0.25)] hover:shadow-[0_0_25px_rgba(6,182,212,0.4)]"
            >
              <UploadCloud className="w-3.5 h-3.5" />
              <span>Run Audit</span>
            </Link>
          ) : (
            <span className="text-[11px] text-slate-500 px-2.5 py-1 bg-obsidian-900 rounded border border-white/5 font-mono">
              Auditor (Read-Only)
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
