import React from 'react';
import { AlertOctagon, RefreshCw } from 'lucide-react';
import { ApiError } from '../../services/api';

interface Props {
  title?: string;
  error: ApiError | Error | string | null;
  onRetry?: () => void;
}

export const ErrorAlert: React.FC<Props> = ({ title = 'Operation Failed', error, onRetry }) => {
  if (!error) return null;

  const getErrorMessage = () => {
    if (typeof error === 'string') return error;
    if ('message' in error) return error.message;
    return 'An unknown error occurred.';
  };

  const getErrorCode = () => {
    if (typeof error === 'object' && error !== null && 'code' in error) {
      return (error as ApiError).code;
    }
    return null;
  };

  const getRequestId = () => {
    if (typeof error === 'object' && error !== null && 'request_id' in error) {
      return (error as ApiError).request_id;
    }
    return null;
  };

  return (
    <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-5 text-rose-200">
      <div className="flex items-start gap-3">
        <AlertOctagon className="w-5 h-5 text-rose-400 mt-0.5 shrink-0" />
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h4 className="font-semibold text-rose-300 text-sm">{title}</h4>
            {getErrorCode() && (
              <span className="text-xs px-2 py-0.5 rounded bg-rose-950 text-rose-400 font-mono border border-rose-800">
                {getErrorCode()}
              </span>
            )}
          </div>
          <p className="text-sm mt-1 text-rose-200/90 leading-relaxed">{getErrorMessage()}</p>
          {getRequestId() && (
            <p className="text-xs font-mono text-rose-400/70 mt-2">Request ID: {getRequestId()}</p>
          )}
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/20 text-rose-300 hover:bg-rose-500/30 text-xs font-medium border border-rose-500/40 transition"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Try Again
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
