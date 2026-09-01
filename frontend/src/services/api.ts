/**
 * Centralized API client wrapper with JWT token propagation (Phase 10).
 */

import { getApiUrl } from '../config/env';

export interface ApiError {
  code: string;
  message: string;
  request_id?: string;
  status_code: number;
  details?: string[];
}

export class ApiException extends Error {
  error: ApiError;

  constructor(error: ApiError) {
    super(error.message);
    this.name = 'ApiException';
    this.error = error;
  }
}

interface RequestOptions extends RequestInit {
  timeoutMs?: number;
}

export async function apiClient<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { timeoutMs = 45000, headers = {}, ...rest } = options;
  const url = getApiUrl(endpoint);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const isFormData = rest.body instanceof FormData;
    const defaultHeaders: Record<string, string> = isFormData
      ? {}
      : {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        };

    // Inject Bearer token if present
    const savedToken = localStorage.getItem('payroll_guardian_token');
    if (savedToken) {
      defaultHeaders['Authorization'] = `Bearer ${savedToken}`;
    }

    const response = await fetch(url, {
      ...rest,
      headers: {
        ...defaultHeaders,
        ...(headers as Record<string, string>),
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorData: any;
      try {
        errorData = await response.json();
      } catch {
        errorData = {
          error: {
            code: `HTTP_${response.status}`,
            message: response.statusText || 'An unexpected API error occurred.',
            status_code: response.status,
          },
        };
      }

      const apiError: ApiError = errorData.error || {
        code: `HTTP_${response.status}`,
        message: errorData.detail || response.statusText || 'Request failed',
        status_code: response.status,
      };

      throw new ApiException(apiError);
    }

    return (await response.json()) as T;
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err instanceof ApiException) {
      throw err;
    }
    if (err.name === 'AbortError') {
      throw new ApiException({
        code: 'TIMEOUT',
        message: `Request timed out after ${timeoutMs / 1000}s.`,
        status_code: 408,
      });
    }
    throw new ApiException({
      code: 'NETWORK_ERROR',
      message: err.message || 'Unable to connect to AI Payroll Guardian API.',
      status_code: 0,
    });
  }
}
