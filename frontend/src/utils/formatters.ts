/**
 * Utility functions for currency, numbers, and dates.
 */

export const formatCurrencyINR = (amount: number | undefined | null): string => {
  if (amount === undefined || amount === null || isNaN(amount)) return '₹0';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount);
};

export const formatPercentage = (value: number | undefined | null): string => {
  if (value === undefined || value === null || isNaN(value)) return '0.0%';
  return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;
};

export const formatRiskScore = (score: number | undefined | null): string => {
  if (score === undefined || score === null || isNaN(score)) return '0.00';
  return (score * 100).toFixed(0) + '%';
};

export const formatShortDate = (dateStr: string | undefined | null): string => {
  if (!dateStr) return 'N/A';
  try {
    const d = new Date(dateStr);
    return isNaN(d.getTime()) ? dateStr : d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return dateStr;
  }
};
