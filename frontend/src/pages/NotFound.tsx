import React from 'react';
import { Link } from 'react-router-dom';
import { AlertOctagon, Home } from 'lucide-react';

export const NotFound: React.FC = () => {
  return (
    <div className="card-glass rounded-3xl p-12 text-center max-w-lg mx-auto my-12 border-slate-800">
      <AlertOctagon className="w-12 h-12 text-rose-400 mx-auto mb-4" />
      <h2 className="text-2xl font-bold text-white mb-2">404 — Page Not Found</h2>
      <p className="text-xs text-slate-400 max-w-xs mx-auto mb-6">
        The requested audit route or analysis view does not exist.
      </p>
      <Link
        to="/dashboard"
        className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-medium text-xs shadow-md transition"
      >
        <Home className="w-4 h-4" />
        Return to Dashboard
      </Link>
    </div>
  );
};
