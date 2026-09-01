import React, { useState } from 'react';
import { ShieldCheck, UserCheck, KeyRound, AlertCircle, X } from 'lucide-react';
import { authApi } from '../../services/authApi';
import { AuthUser, UserRole } from '../../types/api';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  currentUser: AuthUser | null;
  onLoginSuccess: (user: AuthUser) => void;
}

const PRESET_ACCOUNTS = [
  {
    role: 'ADMIN' as UserRole,
    label: 'Executive Admin',
    username: 'admin',
    password: 'AdminPassword2026!',
    badge: 'Full Access',
    color: 'border-purple-500/40 bg-purple-950/20 text-purple-300',
  },
  {
    role: 'PAYROLL_ADMIN' as UserRole,
    label: 'Payroll Officer',
    username: 'payroll_admin',
    password: 'PayrollAdmin2026!',
    badge: 'Upload & Audit',
    color: 'border-brand-500/40 bg-brand-950/20 text-brand-300',
  },
  {
    role: 'AUDITOR' as UserRole,
    label: 'Statutory Auditor',
    username: 'auditor',
    password: 'Auditor2026!',
    badge: 'Compliance & Review',
    color: 'border-amber-500/40 bg-amber-950/20 text-amber-300',
  },
  {
    role: 'VIEWER' as UserRole,
    label: 'Read-Only Viewer',
    username: 'viewer',
    password: 'Viewer2026!',
    badge: 'Dashboard Only',
    color: 'border-slate-500/40 bg-slate-900/50 text-slate-300',
  },
];

export const LoginModal: React.FC<Props> = ({ isOpen, onClose, currentUser, onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleLogin = async (userToLogin?: string, passToLogin?: string) => {
    setError(null);
    setLoading(true);
    const u = userToLogin || username;
    const p = passToLogin || password;

    try {
      const data = await authApi.login(u, p);
      const profile: AuthUser = {
        username: data.username,
        email: `${data.username}@payrollguardian.internal`,
        role: data.role,
        is_active: true,
      };
      onLoginSuccess(profile);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-brand-600/20 border border-brand-500/30 text-brand-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Enterprise Authentication</h3>
              <p className="text-xs text-slate-400">Role-Based Access Control (Phase 10)</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {error && (
            <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Quick Preset Selector */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Switch Role Session
            </label>
            <div className="grid grid-cols-2 gap-2.5">
              {PRESET_ACCOUNTS.map((acc) => (
                <button
                  key={acc.role}
                  type="button"
                  onClick={() => handleLogin(acc.username, acc.password)}
                  disabled={loading}
                  className={`p-3 rounded-xl border text-left transition flex flex-col justify-between hover:scale-[1.02] active:scale-[0.98] ${acc.color} ${currentUser?.role === acc.role ? 'ring-2 ring-brand-500' : ''}`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-xs">{acc.label}</span>
                    <span className="text-[9px] px-1.5 py-0.5 rounded-md bg-slate-900/60 border border-slate-700/50 font-mono">
                      {acc.role}
                    </span>
                  </div>
                  <span className="text-[10px] opacity-80">{acc.badge}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="relative flex items-center justify-center">
            <div className="border-t border-slate-800 w-full" />
            <span className="bg-slate-900 px-3 text-[11px] font-mono text-slate-500 uppercase tracking-widest absolute">
              Or Custom Login
            </span>
          </div>

          {/* Form */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleLogin();
            }}
            className="space-y-3.5"
          >
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Username or Email</label>
              <div className="relative">
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. admin or payroll_admin"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 transition"
                />
                <UserCheck className="w-3.5 h-3.5 text-slate-500 absolute right-3.5 top-3" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
              <div className="relative">
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter account password"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 transition"
                />
                <KeyRound className="w-3.5 h-3.5 text-slate-500 absolute right-3.5 top-3" />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !username || !password}
              className="w-full py-2.5 px-4 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-bold shadow-lg shadow-brand-600/20 transition"
            >
              {loading ? 'Authenticating...' : 'Sign In with JWT'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
