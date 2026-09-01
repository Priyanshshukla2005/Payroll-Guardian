import { AnalysisResponse } from '../types/api';
import { apiClient } from './api';

export const payrollApi = {
  analyzeBatch: (records: any[], payroll_period?: string, jurisdiction?: string) =>
    apiClient<AnalysisResponse>('/payroll/analyze', {
      method: 'POST',
      body: JSON.stringify({ records, payroll_period, jurisdiction }),
    }),

  uploadFile: (file: File, payroll_period?: string, jurisdiction?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (payroll_period) formData.append('payroll_period', payroll_period);
    if (jurisdiction) formData.append('jurisdiction', jurisdiction);

    return apiClient<AnalysisResponse>('/payroll/upload', {
      method: 'POST',
      body: formData,
    });
  },

  getAnalysis: (analysisId: string) =>
    apiClient<AnalysisResponse>(`/payroll/analysis/${analysisId}`),
};
