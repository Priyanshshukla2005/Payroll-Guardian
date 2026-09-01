import React from 'react';
import { Users, AlertTriangle, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { AnalysisSummary } from '../../types/api';
import { StatCard } from '../common/StatCard';

interface Props {
  summary?: AnalysisSummary;
}

export const MetricCards: React.FC<Props> = ({ summary }) => {
  if (!summary) return null;

  const flaggedPct = summary.records_analyzed > 0
    ? ((summary.records_flagged / summary.records_analyzed) * 100).toFixed(1)
    : '0.0';

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
      <StatCard
        title="Total Records Analyzed"
        value={summary.records_analyzed.toLocaleString()}
        subtitle="Current payroll batch size"
        icon={Users}
        color="blue"
      />
      <StatCard
        title="Flagged Anomaly Records"
        value={summary.records_flagged.toLocaleString()}
        subtitle={`${flaggedPct}% of analyzed batch`}
        icon={AlertTriangle}
        color="amber"
        badge={`${flaggedPct}%`}
      />
      <StatCard
        title="Critical & High Risk"
        value={(summary.critical_risk + summary.high_risk).toLocaleString()}
        subtitle="Requires immediate audit sign-off"
        icon={ShieldAlert}
        color="rose"
        badge="Priority"
      />
      <StatCard
        title="Compliant Records"
        value={(summary.records_analyzed - summary.records_flagged).toLocaleString()}
        subtitle="Passed ML & deterministic rules"
        icon={CheckCircle2}
        color="emerald"
      />
    </div>
  );
};
