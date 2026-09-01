import { AnomalyRecordResult } from '../types/api';
import { apiClient } from './api';

export const anomalyApi = {
  listAnomalies: (analysisId: string, severity?: string, anomalyType?: string) => {
    const params = new URLSearchParams();
    if (severity) params.append('severity', severity);
    if (anomalyType) params.append('anomaly_type', anomalyType);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return apiClient<AnomalyRecordResult[]>(`/anomalies/${analysisId}${qs}`);
  },

  getEmployeeAnomaly: (analysisId: string, employeeId: string) =>
    apiClient<AnomalyRecordResult>(`/anomalies/${analysisId}/${employeeId}`),
};
