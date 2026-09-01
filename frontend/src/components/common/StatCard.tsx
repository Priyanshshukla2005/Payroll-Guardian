import React from 'react';
import { LucideIcon } from 'lucide-react';

interface Props {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: 'cyan' | 'blue' | 'rose' | 'amber' | 'emerald' | 'indigo' | 'slate';
  badge?: string;
}

export const StatCard: React.FC<Props> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  color = 'cyan',
  badge,
}) => {
  const colorStyles: Record<string, string> = {
    cyan: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/25',
    blue: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/25',
    rose: 'text-rose-400 bg-rose-500/10 border-rose-500/25',
    amber: 'text-amber-400 bg-amber-500/10 border-amber-500/25',
    emerald: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/25',
    indigo: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/25',
    slate: 'text-slate-400 bg-white/5 border-white/10',
  };

  const activeStyle = colorStyles[color] || colorStyles.cyan;

  return (
    <div className="bg-charcoal-900/80 border border-white/5 rounded-2xl p-5 relative overflow-hidden transition-all duration-200 hover:border-cyan-500/30 group">
      <div className="flex items-center justify-between">
        <p className="text-[11px] font-mono font-semibold uppercase tracking-wider text-slate-400">
          {title}
        </p>
        <div className={`p-2.5 rounded-xl border ${activeStyle} group-hover:scale-105 transition-transform`}>
          <Icon className="w-4 h-4" aria-hidden="true" />
        </div>
      </div>
      <div className="mt-4 flex items-baseline gap-2">
        <h3 className="text-3xl font-bold font-mono tracking-tight text-white">{value}</h3>
        {badge && (
          <span className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-white/5 text-slate-300 font-medium border border-white/5">
            {badge}
          </span>
        )}
      </div>
      {subtitle && <p className="mt-1.5 text-xs text-slate-400">{subtitle}</p>}
    </div>
  );
};
