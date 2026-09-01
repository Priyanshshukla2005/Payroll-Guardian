import React from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';
import { AnalysisSummary } from '../../types/api';
import { SEVERITY_CONFIG } from '../../utils/severity';

interface Props {
  summary?: AnalysisSummary;
}

export const RiskSeverityChart: React.FC<Props> = ({ summary }) => {
  if (!summary || summary.records_flagged === 0) {
    return (
      <div className="card-glass rounded-2xl p-6 flex flex-col items-center justify-center min-h-[300px] text-slate-500">
        <p className="text-sm">No flagged anomalies in current analysis.</p>
      </div>
    );
  }

  const data = [
    { name: 'Critical Risk', value: summary.critical_risk, color: SEVERITY_CONFIG.CRITICAL.hexColor },
    { name: 'High Risk', value: summary.high_risk, color: SEVERITY_CONFIG.HIGH.hexColor },
    { name: 'Medium Risk', value: summary.medium_risk, color: SEVERITY_CONFIG.MEDIUM.hexColor },
    { name: 'Low Risk', value: summary.low_risk, color: SEVERITY_CONFIG.LOW.hexColor },
  ].filter((d) => d.value > 0);

  return (
    <div className="card-glass rounded-2xl p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-bold text-white text-base">Risk Severity Breakdown</h3>
          <p className="text-xs text-slate-400 mt-0.5">Distribution of flagged records by calibrated risk tier</p>
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={85}
              paddingAngle={4}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} stroke="#0f172a" strokeWidth={2} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '0.75rem',
                color: '#f8fafc',
                fontSize: '12px',
              }}
            />
            <Legend
              verticalAlign="bottom"
              height={36}
              formatter={(value, entry: any) => (
                <span className="text-xs text-slate-300 font-medium mr-2">
                  {value} ({entry.payload.value})
                </span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
