import { describe, it, expect } from 'vitest';
import { getApiUrl } from '../config/env';
import { ApiException } from '../services/api';

describe('API URL resolution and Error handling', () => {
  it('constructs correct API endpoint paths', () => {
    const url = getApiUrl('/health');
    expect(url).toContain('/api/v1/health');
  });

  it('handles relative paths properly', () => {
    const url = getApiUrl('payroll/analyze');
    expect(url).toContain('/api/v1/payroll/analyze');
  });

  it('constructs ApiException with structured metadata', () => {
    const exc = new ApiException({
      code: 'VALIDATION_ERROR',
      message: 'Invalid salary field',
      status_code: 422,
      request_id: 'req_123',
    });

    expect(exc.name).toBe('ApiException');
    expect(exc.error.code).toBe('VALIDATION_ERROR');
    expect(exc.error.status_code).toBe(422);
    expect(exc.error.request_id).toBe('req_123');
  });
});
