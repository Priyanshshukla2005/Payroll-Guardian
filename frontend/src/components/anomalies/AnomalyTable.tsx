import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Search, Filter, ArrowUpDown, ChevronRight, AlertOctagon, ChevronLeft } from 'lucide-react';
import { AnomalyRecordResult } from '../../types/api';
import { SeverityBadge } from '../common/SeverityBadge';
import { formatRiskScore } from '../../utils/formatters';

interface Props {
  anomalies: AnomalyRecordResult[];
  analysisId: string;
}

export const AnomalyTable: React.FC<Props> = ({ anomalies, analysisId }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');
  const [selectedDept, setSelectedDept] = useState<string>('ALL');
  const [sortField, setSortField] = useState<'risk_score' | 'employee_id' | 'severity'>('risk_score');
  const [sortAsc, setSortAsc] = useState<boolean>(false);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const pageSize = 10;

  // Extract unique departments
  const departments = useMemo(() => {
    const set = new Set<string>();
    anomalies.forEach((a) => a.department && set.add(a.department));
    return Array.from(set).sort();
  }, [anomalies]);

  // Filter & sort logic
  const filteredData = useMemo(() => {
    return anomalies
      .filter((item) => {
        const matchesSearch =
          item.employee_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
          item.anomaly_types.some((t) => t.toLowerCase().includes(searchTerm.toLowerCase())) ||
          item.department.toLowerCase().includes(searchTerm.toLowerCase());

        const matchesSeverity =
          selectedSeverity === 'ALL' || item.severity.toUpperCase() === selectedSeverity.toUpperCase();

        const matchesDept = selectedDept === 'ALL' || item.department === selectedDept;

        return matchesSearch && matchesSeverity && matchesDept;
      })
      .sort((a, b) => {
        let cmp = 0;
        if (sortField === 'risk_score') {
          cmp = a.risk_score - b.risk_score;
        } else if (sortField === 'employee_id') {
          cmp = a.employee_id.localeCompare(b.employee_id);
        } else if (sortField === 'severity') {
          const sevRank: Record<string, number> = { CRITICAL: 4, HIGH: 3, MEDIUM: 2, LOW: 1 };
          cmp = (sevRank[a.severity] || 0) - (sevRank[b.severity] || 0);
        }
        return sortAsc ? cmp : -cmp;
      });
  }, [anomalies, searchTerm, selectedSeverity, selectedDept, sortField, sortAsc]);

  // Pagination
  const totalPages = Math.max(1, Math.ceil(filteredData.length / pageSize));
  const paginatedData = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredData.slice(start, start + pageSize);
  }, [filteredData, currentPage]);

  const toggleSort = (field: 'risk_score' | 'employee_id' | 'severity') => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  // Unique employees and total anomaly signals count
  const uniqueEmployeesCount = useMemo(() => {
    return new Set(anomalies.map((a) => a.employee_id)).size;
  }, [anomalies]);

  const totalSignalsCount = useMemo(() => {
    return anomalies.reduce((acc, a) => acc + (a.anomaly_types?.length || 0), 0);
  }, [anomalies]);

  return (
    <div className="card-glass rounded-2xl overflow-hidden border-slate-800">
      {/* Table Header & Controls */}
      <div className="p-6 border-b border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="font-bold text-white text-base">Flagged Employee Records</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Showing {filteredData.length} of {anomalies.length} detected anomaly records ({uniqueEmployeesCount} unique employees, {totalSignalsCount} anomaly signals)
            </p>
          </div>

          {/* Search bar */}
          <div className="relative min-w-[240px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Search employee, dept, type..."
              className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-brand-500 transition"
            />
          </div>
        </div>

        {/* Filters bar */}
        <div className="flex flex-wrap items-center gap-3 pt-2">
          <div className="flex items-center gap-1.5 text-xs text-slate-400 font-medium">
            <Filter className="w-3.5 h-3.5" />
            <span>Severity:</span>
          </div>

          <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs">
            {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
              <button
                key={sev}
                onClick={() => {
                  setSelectedSeverity(sev);
                  setCurrentPage(1);
                }}
                className={`px-2.5 py-1 rounded-lg font-medium transition ${
                  selectedSeverity === sev
                    ? 'bg-brand-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>

          {departments.length > 0 && (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-400">Dept:</span>
              <select
                value={selectedDept}
                onChange={(e) => {
                  setSelectedDept(e.target.value);
                  setCurrentPage(1);
                }}
                className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-slate-300 focus:outline-none focus:border-brand-500"
              >
                <option value="ALL">All Departments</option>
                {departments.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Table Body */}
      {paginatedData.length === 0 ? (
        <div className="p-12 text-center text-slate-400">
          <AlertOctagon className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <p className="text-sm font-medium">No matching anomalous records found.</p>
          <p className="text-xs text-slate-500 mt-1">Try relaxing search terms or severity filters.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/60 text-slate-400 font-semibold uppercase tracking-wider">
                <th
                  onClick={() => toggleSort('employee_id')}
                  className="py-3 px-6 cursor-pointer hover:text-slate-200 transition"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Employee</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th className="py-3 px-6">Department</th>
                <th className="py-3 px-6">Anomaly Type</th>
                <th
                  onClick={() => toggleSort('severity')}
                  className="py-3 px-6 cursor-pointer hover:text-slate-200 transition"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Severity</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th
                  onClick={() => toggleSort('risk_score')}
                  className="py-3 px-6 cursor-pointer hover:text-slate-200 transition"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Risk Score</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th className="py-3 px-6">Compliance Source</th>
                <th className="py-3 px-6 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {paginatedData.map((item) => (
                <tr
                  key={item.employee_id}
                  className="hover:bg-slate-900/80 transition-colors duration-150 group"
                >
                  <td className="py-4 px-6 font-mono font-bold text-slate-200">
                    {item.employee_id}
                  </td>
                  <td className="py-4 px-6 text-slate-300">
                    <div>{item.department}</div>
                    <div className="text-[11px] text-slate-500">{item.designation}</div>
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex flex-wrap gap-1">
                      {item.anomaly_types.map((type) => (
                        <span
                          key={type}
                          className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 font-mono text-[10px] border border-slate-700"
                        >
                          {type.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="py-4 px-6">
                    <SeverityBadge severity={item.severity} size="sm" />
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex items-center gap-2">
                      <div className="w-12 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            item.risk_score >= 0.85
                              ? 'bg-rose-500'
                              : item.risk_score >= 0.65
                              ? 'bg-amber-500'
                              : 'bg-brand-500'
                          }`}
                          style={{ width: `${Math.min(100, item.risk_score * 100)}%` }}
                        />
                      </div>
                      <span className="font-mono font-bold text-slate-200">
                        {formatRiskScore(item.risk_score)}
                      </span>
                    </div>
                  </td>
                  <td className="py-4 px-6">
                    {item.compliance.sources.length > 0 ? (
                      <span className="text-[11px] text-brand-300 font-mono">
                        {item.compliance.sources[0].citation}
                      </span>
                    ) : (
                      <span className="text-[11px] text-slate-500 italic">No direct statute</span>
                    )}
                  </td>
                  <td className="py-4 px-6 text-right">
                    <Link
                      to={`/anomalies/${analysisId}/${item.employee_id}`}
                      className="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-slate-800 hover:bg-brand-600 text-slate-300 hover:text-white font-medium text-xs transition shadow-sm"
                    >
                      <span>Investigate</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="p-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <div>
            Page <strong className="text-white">{currentPage}</strong> of {totalPages}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
