import { HealthResponse } from '../types/api';
import { apiClient } from './api';

export const healthApi = {
  getHealth: () => apiClient<HealthResponse>('/health'),
  getLiveness: () => apiClient<{ status: string }>('/health/liveness'),
  getReadiness: () => apiClient<any>('/health/readiness'),
};
