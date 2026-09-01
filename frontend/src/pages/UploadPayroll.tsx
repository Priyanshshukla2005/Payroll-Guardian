import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Code, ArrowRight, ShieldCheck, FileSpreadsheet } from 'lucide-react';
import { Dropzone } from '../components/payroll/Dropzone';
import { JsonInputModal } from '../components/payroll/JsonInputModal';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { payrollApi } from '../services/payrollApi';
import { AnalysisResponse } from '../types/api';

interface Props {
  onAnalysisSuccess: (analysis: AnalysisResponse) => void;
}

export const UploadPayroll: React.FC<Props> = ({ onAnalysisSuccess }) => {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [payrollPeriod, setPayrollPeriod] = useState('2024-06');
  const [jurisdiction, setJurisdiction] = useState('INDIA');

  const [loading, setLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState('Ingesting payroll records...');
  const [error, setError] = useState<any>(null);
  const [isJsonModalOpen, setIsJsonModalOpen] = useState(false);

  const handleUpload = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setError(null);
    setLoadingStage('Uploading & validating file structure...');

    try {
      setTimeout(() => setLoadingStage('Running ML behavioral inference & rule checks...'), 800);
      setTimeout(() => setLoadingStage('Retrieving authoritative compliance sources...'), 1800);
      setTimeout(() => setLoadingStage('Synthesizing grounded audit explanations...'), 2800);

      const res = await payrollApi.uploadFile(selectedFile, payrollPeriod, jurisdiction);
      onAnalysisSuccess(res);
      navigate(`/analysis/${res.analysis_id}`);
    } catch (err: any) {
      setError(err);
      setLoading(false);
    }
  };

  const handleJsonBatchSubmit = async (records: any[]) => {
    setIsJsonModalOpen(false);
    setLoading(true);
    setError(null);
    setLoadingStage('Analyzing JSON payroll batch...');

    try {
      const res = await payrollApi.analyzeBatch(records, payrollPeriod, jurisdiction);
      onAnalysisSuccess(res);
      navigate(`/analysis/${res.analysis_id}`);
    } catch (err: any) {
      setError(err);
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Editorial Header */}
      <div>
        <div className="flex items-center space-x-2 text-cyan-400 font-mono text-xs uppercase tracking-widest font-semibold mb-2">
          <FileSpreadsheet className="w-4 h-4" />
          <span>Ingestion Pipeline</span>
        </div>
        <h2 className="text-3xl font-bold text-white tracking-tight">Upload Payroll Disbursement</h2>
        <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
          Ingest monthly payroll registers (CSV, Parquet, or JSON) to trigger automated feature engineering, ensemble ML anomaly detection, statutory compliance matching, and grounded audit explanations.
        </p>
      </div>

      {error && <ErrorAlert title="Payroll Analysis Failed" error={error} />}

      {/* Main Upload Box */}
      <div className="bg-charcoal-900 border border-white/10 rounded-2xl p-8 space-y-6 shadow-2xl">
        {/* Controls Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pb-6 border-b border-white/5">
          <div>
            <label className="block text-xs font-mono font-semibold text-slate-400 mb-1.5 uppercase">
              Target Payroll Month
            </label>
            <input
              type="month"
              value={payrollPeriod}
              onChange={(e) => setPayrollPeriod(e.target.value)}
              className="w-full rounded-xl bg-obsidian-950 border border-white/10 px-4 py-2.5 text-xs text-slate-100 focus:outline-none focus:border-cyan-400 font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-mono font-semibold text-slate-400 mb-1.5 uppercase">
              Primary Jurisdiction
            </label>
            <select
              value={jurisdiction}
              onChange={(e) => setJurisdiction(e.target.value)}
              className="w-full rounded-xl bg-obsidian-950 border border-white/10 px-4 py-2.5 text-xs text-slate-100 focus:outline-none focus:border-cyan-400 font-mono"
            >
              <option value="INDIA">India (Federal EPFO & ESIC Acts)</option>
              <option value="MAHARASHTRA">Maharashtra (State PT & Shops Act)</option>
              <option value="KARNATAKA">Karnataka (State PT & Shops Act)</option>
            </select>
          </div>
        </div>

        {/* Dropzone */}
        {loading ? (
          <div className="py-16 text-center space-y-4">
            <LoadingSpinner size="lg" message={loadingStage} />
            <div className="max-w-md mx-auto bg-obsidian-950 rounded-xl p-5 border border-white/10 text-xs text-slate-400 font-mono space-y-2">
              <div className="flex items-center justify-center gap-2 text-cyan-400 font-semibold">
                <ShieldCheck className="w-4 h-4" />
                <span>Executing Multi-Layer Verification Pipeline</span>
              </div>
              <p className="text-[11px] text-slate-500">
                1. Schema Check &bull; 2. Feature Extraction &bull; 3. Hybrid ML Detector &bull; 4. Compliance RAG
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <Dropzone
              selectedFile={selectedFile}
              onFileSelect={setSelectedFile}
              onClearFile={() => setSelectedFile(null)}
              maxSizeMb={50}
            />

            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
              <button
                type="button"
                onClick={() => setIsJsonModalOpen(true)}
                className="inline-flex items-center gap-2 text-xs text-slate-400 hover:text-cyan-400 font-mono transition"
              >
                <Code className="w-4 h-4" />
                <span>Paste raw JSON array instead</span>
              </button>

              <button
                type="button"
                onClick={handleUpload}
                disabled={!selectedFile || loading}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl bg-gradient-to-r from-cyan-500 to-brand-500 hover:from-cyan-400 hover:to-brand-400 disabled:opacity-30 disabled:cursor-not-allowed text-obsidian-950 font-bold text-xs shadow-lg shadow-cyan-500/20 transition-all duration-200 hover:scale-[1.02]"
              >
                <span>Run Payroll Audit</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* JSON Direct Modal */}
      {isJsonModalOpen && (
        <JsonInputModal
          onSubmit={handleJsonBatchSubmit}
          onCancel={() => setIsJsonModalOpen(false)}
        />
      )}
    </div>
  );
};
