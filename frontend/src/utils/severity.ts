import { SeverityLevel } from '../types/api';

export interface SeverityConfig {
  label: string;
  badgeBg: string;
  badgeText: string;
  badgeBorder: string;
  accentColor: string;
  dotColor: string;
  hexColor: string;
}

export const SEVERITY_CONFIG: Record<SeverityLevel, SeverityConfig> = {
  CRITICAL: {
    label: 'Critical Risk',
    badgeBg: 'bg-rose-500/10',
    badgeText: 'text-rose-400',
    badgeBorder: 'border-rose-500/30',
    accentColor: 'text-rose-400',
    dotColor: 'bg-rose-500',
    hexColor: '#f43f5e',
  },
  HIGH: {
    label: 'High Risk',
    badgeBg: 'bg-amber-500/10',
    badgeText: 'text-amber-400',
    badgeBorder: 'border-amber-500/30',
    accentColor: 'text-amber-400',
    dotColor: 'bg-amber-500',
    hexColor: '#f59e0b',
  },
  MEDIUM: {
    label: 'Medium Risk',
    badgeBg: 'bg-blue-500/10',
    badgeText: 'text-blue-400',
    badgeBorder: 'border-blue-500/30',
    accentColor: 'text-blue-400',
    dotColor: 'bg-blue-500',
    hexColor: '#3b82f6',
  },
  LOW: {
    label: 'Low Risk',
    badgeBg: 'bg-emerald-500/10',
    badgeText: 'text-emerald-400',
    badgeBorder: 'border-emerald-500/30',
    accentColor: 'text-emerald-400',
    dotColor: 'bg-emerald-500',
    hexColor: '#10b981',
  },
};

export const getSeverityConfig = (severity: string | undefined): SeverityConfig => {
  const norm = (severity || 'LOW').toUpperCase() as SeverityLevel;
  return SEVERITY_CONFIG[norm] || SEVERITY_CONFIG.LOW;
};
