import { describe, it, expect } from 'vitest';
import { getSeverityConfig } from '../utils/severity';

describe('severity utility', () => {
  it('resolves CRITICAL risk configuration', () => {
    const config = getSeverityConfig('CRITICAL');
    expect(config.label).toBe('Critical Risk');
    expect(config.badgeText).toContain('rose');
  });

  it('resolves HIGH risk configuration', () => {
    const config = getSeverityConfig('high');
    expect(config.label).toBe('High Risk');
    expect(config.badgeText).toContain('amber');
  });

  it('falls back to LOW risk on unknown severity', () => {
    const config = getSeverityConfig('UNKNOWN_TIER');
    expect(config.label).toBe('Low Risk');
  });
});
