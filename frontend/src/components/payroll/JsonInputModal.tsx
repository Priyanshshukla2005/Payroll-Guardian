import React, { useState } from 'react';
import { Code, Check, AlertCircle } from 'lucide-react';

interface Props {
  onSubmit: (jsonRecords: any[]) => void;
  onCancel: () => void;
}

export const JsonInputModal: React.FC<Props> = ({ onSubmit, onCancel }) => {
  const defaultSample = `[
  {
    "employee_id": "EMP_DIRECT_001",
    "payroll_month": "2024-06",
    "basic_salary": 45000.0,
    "gross_salary": 65000.0,
    "net_salary": 63600.0,
    "allowances": 20000.0,
    "bonus": 0.0,
    "total_deductions": 1400.0,
    "pf_deduction": 1200.0,
    "esi": 0.0,
    "professional_tax": 200.0,
    "working_days": 26,
    "present_days": 26,
    "leave_days": 0,
    "overtime_hours": 0.0,
    "department": "Operations",
    "designation": "Associate",
    "location": "MAHARASHTRA"
  }
]`;

  const [rawText, setRawText] = useState(defaultSample);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const parsed = JSON.parse(rawText);
      const records = Array.isArray(parsed) ? parsed : parsed.records;
      if (!Array.isArray(records) || records.length === 0) {
        throw new Error('Payload must be a non-empty array of payroll objects.');
      }
      onSubmit(records);
    } catch (err: any) {
      setError(err.message || 'Malformed JSON syntax.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="card-glass rounded-2xl max-w-2xl w-full p-6 border-slate-700 shadow-2xl">
        <div className="flex items-center gap-2 mb-4">
          <Code className="w-5 h-5 text-brand-400" />
          <h3 className="font-bold text-white text-base">Direct JSON Batch Input</h3>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">
              JSON Records Array (Matching PayrollRecordInput Schema)
            </label>
            <textarea
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              rows={12}
              className="w-full rounded-xl bg-slate-900 border border-slate-800 p-4 font-mono text-xs text-slate-200 focus:outline-none focus:border-brand-500 transition"
              placeholder="Paste JSON array here..."
            />
          </div>

          {error && (
            <div className="flex items-center gap-2 text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl p-3">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 rounded-xl text-slate-400 hover:text-slate-200 text-xs font-medium transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md shadow-brand-600/20 transition flex items-center gap-1.5"
            >
              <Check className="w-3.5 h-3.5" />
              Analyze JSON Batch
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
