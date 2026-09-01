import React, { useState } from 'react';
import { Search } from 'lucide-react';
import { ComplianceSearchRequest, ComplianceSearchResult } from '../../types/api';
import { complianceApi } from '../../services/complianceApi';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorAlert } from '../common/ErrorAlert';

export const ComplianceSearchBox: React.FC = () => {
  const [query, setQuery] = useState('EPFO statutory 12 percent basic wage contribution ceiling');
  const [jurisdiction, setJurisdiction] = useState('INDIA');
  const [payrollDate, setPayrollDate] = useState('2024-06-01');
  const [topic, setTopic] = useState<string>('PF');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<any>(null);
  const [results, setResults] = useState<ComplianceSearchResult | null>(null);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const payload: ComplianceSearchRequest = {
        query,
        jurisdiction,
        payroll_date: payrollDate,
        topic: topic === 'ALL' ? undefined : topic,
        top_n: 5,
      };
      const res = await complianceApi.search(payload);
      setResults(res);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Search Input Box */}
      <div className="card-glass rounded-2xl p-6 border-slate-800">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="relative">
            <Search className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search statutory acts, sections, tax rules, or corporate policies..."
              className="w-full pl-12 pr-28 py-3.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition shadow-inner"
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-medium text-xs shadow-md transition"
            >
              {loading ? 'Searching...' : 'Search RAG'}
            </button>
          </div>

          {/* Filter Row */}
          <div className="flex flex-wrap items-center gap-4 text-xs">
            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-medium">Jurisdiction:</span>
              <select
                value={jurisdiction}
                onChange={(e) => setJurisdiction(e.target.value)}
                className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-200 focus:outline-none focus:border-brand-500"
              >
                <option value="INDIA">India (Federal/Central)</option>
                <option value="MAHARASHTRA">Maharashtra State</option>
                <option value="KARNATAKA">Karnataka State</option>
                <option value="UNKNOWN">Unknown / Other</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-medium">Topic:</span>
              <select
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-200 focus:outline-none focus:border-brand-500"
              >
                <option value="ALL">All Topics</option>
                <option value="PF">Provident Fund (EPFO)</option>
                <option value="ESI">Employee State Insurance (ESIC)</option>
                <option value="PROFESSIONAL_TAX">Professional Tax (PT)</option>
                <option value="TDS">TDS / Income Tax</option>
                <option value="OVERTIME">Overtime & Caps</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-medium">Applicability Date:</span>
              <input
                type="date"
                value={payrollDate}
                onChange={(e) => setPayrollDate(e.target.value)}
                className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1 text-slate-200 focus:outline-none focus:border-brand-500 font-mono"
              />
            </div>
          </div>
        </form>
      </div>

      {error && <ErrorAlert title="Knowledge Search Failed" error={error} />}

      {loading && <LoadingSpinner message="Querying date- and jurisdiction-aware knowledge base..." />}

      {/* Results */}
      {results && !loading && (
        <div className="space-y-4">
          <div className="flex items-center justify-between px-1">
            <h3 className="font-bold text-white text-base">
              Retrieved Sources ({results.total_found})
            </h3>
            <span
              className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                results.status === 'SUCCESS'
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
              }`}
            >
              Status: {results.status}
            </span>
          </div>

          {results.results.length === 0 ? (
            <div className="card-glass rounded-2xl p-8 text-center text-slate-400 text-xs">
              <p>{results.no_answer_reason || 'No matching authoritative sources found for the given criteria.'}</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {results.results.map((source, idx) => (
                <div
                  key={idx}
                  className="card-glass rounded-2xl p-5 border-slate-800 space-y-3 hover:border-brand-500/40 transition"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 rounded-md bg-brand-600/20 text-brand-400 font-bold text-xs flex items-center justify-center">
                        #{idx + 1}
                      </span>
                      <span className="font-mono font-bold text-sm text-slate-100">
                        {source.document_id}
                      </span>
                      <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 font-medium border border-slate-700">
                        {source.authority_level}
                      </span>
                    </div>

                    <span className="font-mono text-xs text-brand-400 font-semibold">
                      {source.citation}
                    </span>
                  </div>

                  {source.title && (
                    <p className="text-sm text-slate-200 font-medium">{source.title}</p>
                  )}

                  <div className="flex flex-wrap gap-4 text-xs font-mono text-slate-400 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                    {source.section && (
                      <div>
                        <span className="text-slate-500">Section: </span>
                        <span className="text-slate-200 font-bold">{source.section}</span>
                      </div>
                    )}
                    {source.page && (
                      <div>
                        <span className="text-slate-500">Page: </span>
                        <span className="text-slate-200 font-bold">{source.page}</span>
                      </div>
                    )}
                    <div>
                      <span className="text-slate-500">Jurisdiction: </span>
                      <span className="text-slate-200 font-bold">{results.jurisdiction}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
