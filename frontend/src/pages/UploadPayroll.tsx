import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Code, ArrowRight, ShieldCheck } from 'lucide-react';
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
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Upload Payroll Disbursement</h2>
        <p className="text-xs text-slate-400 mt-1">
          Upload monthly payroll registers to trigger automated anomaly detection, statutory compliance matching, and grounded audit explanations.
        </p>
      </div>

      {error && <ErrorAlert title="Payroll Analysis Failed" error={error} />}

      {/* Main Upload Box */}
      <div className="card-glass rounded-3xl p-8 border-slate-800 space-y-6">
        {/* Controls Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pb-4 border-b border-slate-800">
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1.5">
              Target Payroll Month
            </label>
            <input
              type="month"
              value={payrollPeriod}
              onChange={(e) => setPayrollPeriod(e.target.value)}
              className="w-full rounded-xl bg-slate-900 border border-slate-800 px-4 py-2.5 text-xs text-slate-100 focus:outline-none focus:border-brand-500 font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1.5">
              Primary Jurisdiction
            </label>
            <select
              value={jurisdiction}
              onChange={(e) => setJurisdiction(e.target.value)}
              className="w-full rounded-xl bg-slate-900 border border-slate-800 px-4 py-2.5 text-xs text-slate-100 focus:outline-none focus:border-brand-500"
            >
              <option value="INDIA">India (Federal/Central EPFO & ESIC)</option>
              <option value="MAHARASHTRA">Maharashtra (State PT & Shops Act)</option>
              <option value="KARNATAKA">Karnataka (State PT & Shops Act)</option>
            </select>
          </div>
        </div>

        {/* Dropzone */}
        {loading ? (
          <div className="py-12 text-center space-y-4">
            <LoadingSpinner size="lg" message={loadingStage} />
            <div className="max-w-md mx-auto bg-slate-900/60 rounded-xl p-4 border border-slate-800 text-xs text-slate-400 font-mono space-y-1">
              <div className="flex items-center gap-2 text-brand-400 font-medium">
                <ShieldCheck className="w-4 h-4" />
                <span>Executing 4-tier verification pipeline...</span>
              </div>
              <p className="text-[11px] text-slate-500">
                1. Feature Engineering &bull; 2. Hybrid ML Detector &bull; 3. Compliance RAG &bull; 4. Grounded LLM
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
                className="inline-flex items-center gap-2 text-xs text-slate-400 hover:text-brand-300 font-medium transition"
              >
                <Code className="w-4 h-4" />
                <span>Paste raw JSON array instead</span>
              </button>

              <button
                type="button"
                onClick={handleUpload}
                disabled={!selectedFile || loading}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold text-xs shadow-lg shadow-brand-600/30 transition"
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
