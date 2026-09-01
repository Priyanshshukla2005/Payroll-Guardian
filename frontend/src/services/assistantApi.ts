import { AssistantQueryRequest, AssistantQueryResponse } from '../types/api';
import { apiClient } from './api';

export const assistantApi = {
  query: (req: AssistantQueryRequest) =>
    apiClient<AssistantQueryResponse>('/assistant/query', {
      method: 'POST',
      body: JSON.stringify(req),
    }),
};
