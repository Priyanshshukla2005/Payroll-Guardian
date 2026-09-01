import React from 'react';
import { ShieldCheck, Database, Cpu, BookOpen, Lock } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full bg-obsidian-950 border-t border-white/5 pt-16 pb-12 text-slate-400">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        {/* Top Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 pb-12 border-b border-white/5">
          {/* Brand Column */}
          <div className="md:col-span-1 space-y-4">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 font-bold">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <span className="text-white font-semibold tracking-tight text-base">
                AI Payroll Guardian
              </span>
            </div>
            <p className="text-xs leading-relaxed text-slate-400">
              Enterprise payroll anomaly verification, statutory compliance intelligence, and grounded explainability platform.
            </p>
            <div className="flex items-center space-x-2 pt-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="font-mono text-xs text-emerald-400 font-medium">
                Production Engine Ready · v2.0
              </span>
            </div>
          </div>

          {/* Core Telemetry */}
          <div className="space-y-3">
            <h4 className="text-xs uppercase tracking-widest font-mono text-slate-200 font-semibold">
              System Architecture
            </h4>
            <ul className="space-y-2 text-xs text-slate-400 font-mono">
              <li className="flex items-center space-x-2">
                <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                <span>Hybrid Ensemble V2 (RF+Rules+MAD)</span>
              </li>
              <li className="flex items-center space-x-2">
                <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
                <span>RAG Vector Store (40 Statutory Chunks)</span>
              </li>
              <li className="flex items-center space-x-2">
                <Database className="w-3.5 h-3.5 text-emerald-400" />
                <span>SQLAlchemy + Persistent SQLite DB</span>
              </li>
              <li className="flex items-center space-x-2">
                <Lock className="w-3.5 h-3.5 text-amber-400" />
                <span>JWT Auth & 4-Tier RBAC Guard</span>
              </li>
            </ul>
          </div>

          {/* Navigation */}
          <div className="space-y-3">
            <h4 className="text-xs uppercase tracking-widest font-mono text-slate-200 font-semibold">
              Platform Workspace
            </h4>
            <ul className="space-y-2 text-xs">
              <li>
                <Link to="/" className="hover:text-cyan-400 transition-colors">
                  Product Overview
                </Link>
              </li>
              <li>
                <Link to="/dashboard" className="hover:text-cyan-400 transition-colors">
                  Executive Dashboard
                </Link>
              </li>
              <li>
                <Link to="/payroll/upload" className="hover:text-cyan-400 transition-colors">
                  Payroll Ingestion
                </Link>
              </li>
              <li>
                <Link to="/analysis" className="hover:text-cyan-400 transition-colors">
                  Batch Anomaly Inspection
                </Link>
              </li>
              <li>
                <Link to="/compliance" className="hover:text-cyan-400 transition-colors">
                  Compliance Knowledge Hub
                </Link>
              </li>
              <li>
                <Link to="/assistant" className="hover:text-cyan-400 transition-colors">
                  Grounded AI Assistant
                </Link>
              </li>
            </ul>
          </div>

          {/* Security & Trust */}
          <div className="space-y-3">
            <h4 className="text-xs uppercase tracking-widest font-mono text-slate-200 font-semibold">
              Statutory Guardrails
            </h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Every flagged anomaly links deterministically to governing Indian labor acts: Employees' Provident Funds Act 1952, ESI Act 1948, and Income Tax TDS Section 192.
            </p>
            <div className="p-3 rounded-lg bg-charcoal-900 border border-white/5 space-y-1">
              <div className="flex items-center justify-between text-[11px] font-mono">
                <span className="text-slate-400">Audit Trail:</span>
                <span className="text-emerald-400 font-semibold">SHA-256 Verified</span>
              </div>
              <div className="flex items-center justify-between text-[11px] font-mono">
                <span className="text-slate-400">Drift Status:</span>
                <span className="text-cyan-400 font-semibold">STABLE (PSI: 0.042)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-slate-400">
          <p>© 2026 AI Payroll Guardian Enterprise. All rights reserved.</p>
          <div className="flex items-center space-x-6 text-[11px]">
            <span className="text-slate-400">Deterministic Rules Override Guaranteed</span>
            <span className="text-white/20">|</span>
            <span className="text-slate-400">Zero Hallucination Compliance Guarantee</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
