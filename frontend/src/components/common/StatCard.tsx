import React from 'react';
import { LucideIcon } from 'lucide-react';

interface Props {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: 'blue' | 'rose' | 'amber' | 'emerald' | 'slate';
  badge?: string;
}

export const StatCard: React.FC<Props> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  color = 'blue',
  badge,
}) => {
  const colorStyles = {
    blue: 'text-brand-400 bg-brand-500/10 border-brand-500/20',
    rose: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
    amber: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    emerald: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    slate: 'text-slate-400 bg-slate-800 border-slate-700',
  };

  return (
    <div className="card-glass rounded-xl p-5 relative overflow-hidden transition-all duration-200 hover:border-slate-700">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">{title}</p>
        <div className={`p-2.5 rounded-lg border ${colorStyles[color]}`}>
          <Icon className="w-5 h-5" aria-hidden="true" />
        </div>
      </div>
      <div className="mt-4 flex items-baseline gap-2">
        <h3 className="text-2xl font-bold tracking-tight text-white">{value}</h3>
        {badge && (
          <span className="text-xs px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 font-medium border border-slate-700">
            {badge}
          </span>
        )}
      </div>
      {subtitle && <p className="mt-1 text-xs text-slate-400">{subtitle}</p>}
    </div>
  );
};
