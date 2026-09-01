/**
 * Frontend environment configuration.
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
export const API_PREFIX = '/api/v1';

export const getApiUrl = (path: string): string => {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  // If running with Vite dev proxy, relative paths work, but fallback to absolute base URL
  return `${API_BASE_URL}${API_PREFIX}${cleanPath}`;
};
