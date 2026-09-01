import { describe, it, expect } from 'vitest';
import {
  formatCurrencyINR,
  formatPercentage,
  formatRiskScore,
  formatShortDate,
} from '../utils/formatters';

describe('formatters utility', () => {
  it('formats INR currency correctly', () => {
    expect(formatCurrencyINR(50000)).toContain('50,000');
    expect(formatCurrencyINR(0)).toContain('0');
    expect(formatCurrencyINR(null)).toBe('₹0');
  });

  it('formats percentages with signs', () => {
    expect(formatPercentage(12.5)).toBe('+12.5%');
    expect(formatPercentage(-5.0)).toBe('-5.0%');
    expect(formatPercentage(0)).toBe('+0.0%');
  });

  it('formats risk scores', () => {
    expect(formatRiskScore(0.85)).toBe('85%');
    expect(formatRiskScore(0.0)).toBe('0%');
    expect(formatRiskScore(null)).toBe('0.00');
  });

  it('formats dates cleanly', () => {
    expect(formatShortDate('2024-06-01')).toBe('Jun 1, 2024');
    expect(formatShortDate(null)).toBe('N/A');
  });
});
