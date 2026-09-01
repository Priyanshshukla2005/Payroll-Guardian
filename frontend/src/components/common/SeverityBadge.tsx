import React from 'react';
import { getSeverityConfig } from '../../utils/severity';
import { AlertCircle, AlertTriangle, Info, CheckCircle2 } from 'lucide-react';

interface Props {
  severity: string;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

export const SeverityBadge: React.FC<Props> = ({ severity, size = 'md', showIcon = true }) => {
  const config = getSeverityConfig(severity);

  const getIcon = () => {
    switch (severity.toUpperCase()) {
      case 'CRITICAL':
        return <AlertCircle className="w-3.5 h-3.5 mr-1 text-rose-400" aria-hidden="true" />;
      case 'HIGH':
        return <AlertTriangle className="w-3.5 h-3.5 mr-1 text-amber-400" aria-hidden="true" />;
      case 'MEDIUM':
        return <Info className="w-3.5 h-3.5 mr-1 text-blue-400" aria-hidden="true" />;
      default:
        return <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-400" aria-hidden="true" />;
    }
  };

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1 font-medium',
    lg: 'text-sm px-3 py-1.5 font-semibold',
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border ${config.badgeBg} ${config.badgeText} ${config.badgeBorder} ${sizeClasses[size]}`}
      role="status"
      aria-label={config.label}
    >
      {showIcon && getIcon()}
      {config.label}
    </span>
  );
};
