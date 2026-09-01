/**
 * Audit History API client (Phase 10).
 */

import { AuditEventItem } from '../types/api';
import { apiClient } from './api';

export const auditApi = {
  async getAnalysisTimeline(analysisId: string): Promise<AuditEventItem[]> {
    return apiClient<AuditEventItem[]>(`/api/v1/audit/analysis/${analysisId}`);
  },

  async listEvents(limit: number = 50): Promise<AuditEventItem[]> {
    return apiClient<AuditEventItem[]>(`/api/v1/audit/events?limit=${limit}`);
  },

  async resolveAnomaly(
    analysisId: string,
    employeeId: string,
    status: string,
    notes: string
  ): Promise<any> {
    return apiClient<any>(`/api/v1/anomalies/${analysisId}/${employeeId}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ status, resolution_notes: notes }),
    });
  },
};
