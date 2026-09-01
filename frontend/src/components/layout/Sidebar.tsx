import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  ShieldAlert,
  LayoutDashboard,
  UploadCloud,
  FileSearch,
  BookOpen,
  Bot,
  Activity,
} from 'lucide-react';
import { healthApi } from '../../services/healthApi';
import { HealthResponse } from '../../types/api';

export const Sidebar: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isOffline, setIsOffline] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const fetchStatus = async () => {
      try {
        const data = await healthApi.getHealth();
        if (isMounted) {
          setHealth(data);
          setIsOffline(false);
        }
      } catch {
        if (isMounted) setIsOffline(true);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const navItems = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/payroll/upload', label: 'Upload Payroll', icon: UploadCloud },
    { to: '/analysis', label: 'Anomaly Audit', icon: FileSearch },
    { to: '/compliance', label: 'Compliance RAG', icon: BookOpen },
    { to: '/assistant', label: 'AI Assistant', icon: Bot },
  ];

  return (
    <aside className="w-64 bg-slate-900/90 border-r border-slate-800 flex flex-col h-screen shrink-0 sticky top-0">
      {/* Brand Header */}
      <div className="p-6 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-gradient-to-tr from-brand-600 to-brand-400 text-white shadow-lg shadow-brand-600/30">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-bold text-white tracking-tight text-base leading-tight">
              Payroll Guardian
            </h1>
            <p className="text-xs text-slate-400 font-medium tracking-wide uppercase mt-0.5">
              AI Audit Platform
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
        <div className="px-3 py-2 text-[10px] font-bold uppercase tracking-wider text-slate-500">
          Core Modules
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-brand-600/15 text-brand-400 border border-brand-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Live System Status */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/40">
        <div className="flex items-center justify-between mb-3 px-1">
          <span className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-brand-400" />
            System Status
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
            v1.0.0
          </span>
        </div>

        <div className="space-y-2 bg-slate-900/80 rounded-xl p-3 border border-slate-800 text-xs">
          <div className="flex items-center justify-between">
            <span className="text-slate-400">AI Detector</span>
            <span className="flex items-center gap-1.5 font-mono text-[11px] text-emerald-400">
              <span className={`w-2 h-2 rounded-full ${!isOffline && health?.services.ai === 'available' ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
              {!isOffline ? health?.services.ai || 'Ready' : 'Offline'}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-slate-400">Compliance RAG</span>
            <span className="flex items-center gap-1.5 font-mono text-[11px] text-emerald-400">
              <span className={`w-2 h-2 rounded-full ${!isOffline && health?.services.rag === 'available' ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
              {!isOffline ? health?.services.rag || 'Ready' : 'Offline'}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-slate-400">Grounded LLM</span>
            <span className="flex items-center gap-1.5 font-mono text-[11px] text-emerald-400">
              <span className={`w-2 h-2 rounded-full ${!isOffline && health?.services.llm === 'available' ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
              {!isOffline ? health?.services.llm || 'Ready' : 'Offline'}
            </span>
          </div>
        </div>

        {/* Auditor Session Badge */}
        <div className="mt-3 flex items-center gap-2.5 px-2 py-1.5 text-xs text-slate-400">
          <div className="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-brand-400 text-xs">
            PA
          </div>
          <div className="truncate">
            <p className="text-slate-200 font-medium truncate text-xs">Payroll Auditor</p>
            <p className="text-[10px] text-slate-500 truncate">Enterprise Session</p>
          </div>
        </div>
      </div>
    </aside>
  );
};
