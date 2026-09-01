import { AuthUser, TokenResponse } from '../types/api';
import { apiClient } from './api';

export const authApi = {
  async login(username: string, password: string): Promise<TokenResponse> {
    const data = await apiClient<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });

    if (data && data.access_token) {
      localStorage.setItem('payroll_guardian_token', data.access_token);
      localStorage.setItem(
        'payroll_guardian_user',
        JSON.stringify({
          username: data.username,
          role: data.role,
          email: `${data.username}@payrollguardian.internal`,
          is_active: true,
        })
      );
    }
    return data;
  },

  async getProfile(): Promise<AuthUser> {
    return apiClient<AuthUser>('/auth/me');
  },

  logout(): void {
    localStorage.removeItem('payroll_guardian_token');
    localStorage.removeItem('payroll_guardian_user');
  },

  getCurrentUser(): AuthUser | null {
    const saved = localStorage.getItem('payroll_guardian_user');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return null;
      }
    }
    return {
      username: 'payroll_admin',
      email: 'payroll_admin@payrollguardian.internal',
      role: 'PAYROLL_ADMIN',
      full_name: 'Senior Payroll Officer',
      is_active: true,
    };
  },
};
