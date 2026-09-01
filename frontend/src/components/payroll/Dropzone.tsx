import React, { useState, useRef } from 'react';
import { UploadCloud, FileSpreadsheet, FileCode, CheckCircle, AlertCircle, X } from 'lucide-react';

interface Props {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
  onClearFile: () => void;
  maxSizeMb?: number;
}

export const Dropzone: React.FC<Props> = ({
  onFileSelect,
  selectedFile,
  onClearFile,
  maxSizeMb = 50,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const allowedExtensions = ['.csv', '.json', '.parquet'];

  const validateAndHandleFile = (file: File) => {
    setError(null);
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();

    if (!allowedExtensions.includes(ext)) {
      setError(`Unsupported file extension '${ext}'. Allowed: .csv, .json, .parquet`);
      return;
    }

    if (file.size > maxSizeMb * 1024 * 1024) {
      setError(`File size (${(file.size / (1024 * 1024)).toFixed(1)}MB) exceeds maximum ${maxSizeMb}MB limit.`);
      return;
    }

    onFileSelect(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndHandleFile(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="w-full">
      <input
        type="file"
        ref={fileInputRef}
        onChange={(e) => {
          if (e.target.files && e.target.files.length > 0) {
            validateAndHandleFile(e.target.files[0]);
          }
        }}
        accept=".csv,.json,.parquet"
        className="hidden"
      />

      {!selectedFile ? (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-200 ${
            isDragOver
              ? 'border-brand-500 bg-brand-500/10'
              : 'border-slate-800 hover:border-slate-700 bg-slate-900/40 hover:bg-slate-900/70'
          }`}
        >
          <div className="mx-auto w-16 h-16 rounded-2xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400 mb-4 shadow-lg shadow-brand-500/10">
            <UploadCloud className="w-8 h-8 animate-pulse" />
          </div>
          <h3 className="text-base font-bold text-white mb-1">
            Drag & Drop Payroll Batch File
          </h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mb-4">
            Supports <strong className="text-slate-300">CSV</strong>, <strong className="text-slate-300">JSON</strong>, or <strong className="text-slate-300">Parquet</strong> files up to {maxSizeMb}MB
          </p>
          <button
            type="button"
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition"
          >
            Browse Local File
          </button>
        </div>
      ) : (
        <div className="card-glass rounded-2xl p-6 border-slate-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-brand-500/10 border border-brand-500/20 text-brand-400">
                {selectedFile.name.endsWith('.json') ? (
                  <FileCode className="w-6 h-6" />
                ) : (
                  <FileSpreadsheet className="w-6 h-6" />
                )}
              </div>
              <div>
                <h4 className="font-semibold text-white text-sm truncate max-w-md">
                  {selectedFile.name}
                </h4>
                <div className="flex items-center gap-2 mt-1 text-xs text-slate-400">
                  <span>{formatFileSize(selectedFile.size)}</span>
                  <span>•</span>
                  <span className="text-emerald-400 flex items-center gap-1 font-medium">
                    <CheckCircle className="w-3.5 h-3.5" /> Client Validated
                  </span>
                </div>
              </div>
            </div>

            <button
              onClick={onClearFile}
              className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
              title="Remove File"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="mt-3 flex items-center gap-2 text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl p-3">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};
