import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from 'recharts';
import { AnomalyRecordResult } from '../../types/api';

interface Props {
  anomalies?: AnomalyRecordResult[];
}

export const AnomalyTypeChart: React.FC<Props> = ({ anomalies = [] }) => {
  if (!anomalies || anomalies.length === 0) {
    return (
      <div className="card-glass rounded-2xl p-6 flex flex-col items-center justify-center min-h-[300px] text-slate-500">
        <p className="text-sm">No anomaly type categories to display.</p>
      </div>
    );
  }

  // Aggregate anomaly type frequencies
  const counts: Record<string, number> = {};
  anomalies.forEach((a) => {
    a.anomaly_types.forEach((type) => {
      if (type && type !== 'NONE') {
        const cleanType = type.replace(/_/g, ' ');
        counts[cleanType] = (counts[cleanType] || 0) + 1;
      }
    });
  });

  const data = Object.entries(counts)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 6);

  const colors = ['#0c8de7', '#38bdf8', '#818cf8', '#f59e0b', '#f43f5e', '#a855f7'];

  return (
    <div className="card-glass rounded-2xl p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-bold text-white text-base">Top Anomaly Categories</h3>
          <p className="text-xs text-slate-400 mt-0.5">Most frequent statutory and behavioral triggers</p>
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
            <XAxis type="number" stroke="#64748b" fontSize={11} />
            <YAxis
              type="category"
              dataKey="name"
              stroke="#94a3b8"
              fontSize={11}
              width={110}
              tickFormatter={(v) => (v.length > 16 ? `${v.substring(0, 14)}...` : v)}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '0.75rem',
                color: '#f8fafc',
                fontSize: '12px',
              }}
              formatter={(val: number) => [`${val} records`, 'Count']}
            />
            <Bar dataKey="count" radius={[0, 6, 6, 0]}>
              {data.map((_, index) => (
                <Cell key={`bar-${index}`} fill={colors[index % colors.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
