import React, { useEffect, useState } from 'react';
import { NavLink, Link } from 'react-router-dom';
import {
  ShieldAlert,
  LayoutDashboard,
  UploadCloud,
  FileSearch,
  BookOpen,
  Bot,
  Activity,
  Globe,
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
    { to: '/', label: 'Product Overview', icon: Globe },
    { to: '/dashboard', label: 'Command Center', icon: LayoutDashboard },
    { to: '/payroll/upload', label: 'Payroll Ingestion', icon: UploadCloud },
    { to: '/analysis', label: 'Batch Audit', icon: FileSearch },
    { to: '/compliance', label: 'Compliance RAG', icon: BookOpen },
    { to: '/assistant', label: 'AI Assistant', icon: Bot },
  ];

  return (
    <aside className="w-64 bg-obsidian-950 border-r border-white/5 flex flex-col h-screen shrink-0 sticky top-0 z-30">
      {/* Brand Header */}
      <div className="p-6 border-b border-white/5">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 group-hover:border-cyan-400 transition-colors">
            <ShieldAlert className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <h1 className="font-semibold text-white tracking-tight text-sm leading-tight">
              Payroll Guardian
            </h1>
            <p className="text-[10px] font-mono text-cyan-400 uppercase tracking-widest mt-0.5 font-medium">
              Enterprise AI v2.0
            </p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        <div className="px-3 py-2 text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-500">
          Core Workspaces
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-semibold shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/5 border border-transparent'
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
      <div className="p-4 border-t border-white/5 bg-obsidian-900/60">
        <div className="flex items-center justify-between mb-3 px-1">
          <span className="text-[11px] font-semibold text-slate-400 flex items-center gap-1.5 font-mono">
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
            Telemetry
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-slate-400 border border-white/5">
            ONLINE
          </span>
        </div>

        <div className="space-y-2 bg-charcoal-900 rounded-lg p-3 border border-white/5 text-xs">
          <div className="flex items-center justify-between">
            <span className="text-slate-400 text-[11px]">AI Hybrid V2</span>
            <span className="flex items-center gap-1.5 font-mono text-[11px] text-emerald-400">
              <span className={`w-1.5 h-1.5 rounded-full ${!isOffline && health?.services.ai === 'available' ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
              {!isOffline ? health?.services.ai || 'Ready' : 'Offline'}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-slate-400 text-[11px]">Statutory RAG</span>
            <span className="flex items-center gap-1.5 font-mono text-[11px] text-emerald-400">
              <span className={`w-1.5 h-1.5 rounded-full ${!isOffline && health?.services.rag === 'available' ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
              {!isOffline ? health?.services.rag || 'Ready' : 'Offline'}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-slate-400 text-[11px]">Grounded LLM</span>
            <span className="flex items-center gap-1.5 font-mono text-[11px] text-emerald-400">
              <span className={`w-1.5 h-1.5 rounded-full ${!isOffline && health?.services.llm === 'available' ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
              {!isOffline ? health?.services.llm || 'Ready' : 'Offline'}
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
};
