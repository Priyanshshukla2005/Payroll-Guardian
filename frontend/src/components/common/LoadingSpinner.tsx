import React from 'react';
import { Loader2 } from 'lucide-react';

interface Props {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const LoadingSpinner: React.FC<Props> = ({ message = 'Processing...', size = 'md' }) => {
  const sizeMap = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-10 h-10',
  };

  return (
    <div className="flex flex-col items-center justify-center p-8 text-slate-400 space-y-3" role="status">
      <Loader2 className={`${sizeMap[size]} animate-spin text-brand-400`} />
      {message && <p className="text-sm font-medium text-slate-300">{message}</p>}
      <span className="sr-only">Loading</span>
    </div>
  );
};
