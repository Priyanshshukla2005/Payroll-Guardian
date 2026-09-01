import { ComplianceSearchRequest, ComplianceSearchResult } from '../types/api';
import { apiClient } from './api';

export const complianceApi = {
  search: (req: ComplianceSearchRequest) =>
    apiClient<ComplianceSearchResult>('/compliance/search', {
      method: 'POST',
      body: JSON.stringify(req),
    }),
};
