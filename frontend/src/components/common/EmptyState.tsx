import React from 'react';
import { LucideIcon } from 'lucide-react';
import { Link } from 'react-router-dom';

interface Props {
  icon: LucideIcon;
  title: string;
  description: string;
  actionText?: string;
  actionHref?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<Props> = ({
  icon: Icon,
  title,
  description,
  actionText,
  actionHref,
  onAction,
}) => {
  return (
    <div className="card-glass rounded-2xl p-12 text-center max-w-lg mx-auto border-dashed border-slate-800 my-8">
      <div className="mx-auto w-14 h-14 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-400 mb-4 shadow-inner">
        <Icon className="w-7 h-7 text-brand-400" />
      </div>
      <h3 className="text-lg font-bold text-white mb-2">{title}</h3>
      <p className="text-sm text-slate-400 max-w-sm mx-auto leading-relaxed mb-6">
        {description}
      </p>
      {actionText && (
        actionHref ? (
          <Link
            to={actionHref}
            className="inline-flex items-center px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-medium text-sm transition shadow-lg shadow-brand-600/20"
          >
            {actionText}
          </Link>
        ) : onAction ? (
          <button
            onClick={onAction}
            className="inline-flex items-center px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-medium text-sm transition shadow-lg shadow-brand-600/20"
          >
            {actionText}
          </button>
        ) : null
      )}
    </div>
  );
};
