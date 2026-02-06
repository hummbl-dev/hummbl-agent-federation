/**
 * CAES Parser Tests
 */

import { describe, it, expect } from 'vitest';
import {
  parseCAES,
  getLevel,
  compareCAES,
  isWithinConstraints,
  formatCAES,
} from '../src/caes';

describe('parseCAES', () => {
  it('parses simplified CAES code', () => {
    const result = parseCAES('C2-A1-E2-S2');
    expect(result).not.toBeNull();
    expect(result?.classification).toBe('C2');
  });

  it('parses full CAES code with labels', () => {
    const result = parseCAES('C2-A1-NOTIFY-E2-CHECKPOINT-S2-DOMAIN');
    expect(result).not.toBeNull();
    expect(result?.authority).toBe('A1-NOTIFY');
  });

  it('returns null for invalid code', () => {
    expect(parseCAES('invalid')).toBeNull();
    expect(parseCAES('C9-A1-E2-S2')).toBeNull();
  });
});

describe('getLevel', () => {
  it('extracts numeric level from classification', () => {
    expect(getLevel('C0')).toBe(0);
    expect(getLevel('C3')).toBe(3);
    expect(getLevel('C5')).toBe(5);
  });

  it('extracts level from full component', () => {
    expect(getLevel('A2-REVIEW')).toBe(2);
    expect(getLevel('S4-SYSTEM')).toBe(4);
  });

  it('returns -1 for invalid', () => {
    expect(getLevel('invalid')).toBe(-1);
  });
});

describe('compareCAES', () => {
  it('compares by classification first', () => {
    const a = parseCAES('C2-A1-E2-S2')!;
    const b = parseCAES('C3-A1-E2-S2')!;
    expect(compareCAES(a, b)).toBeLessThan(0);
    expect(compareCAES(b, a)).toBeGreaterThan(0);
  });

  it('compares equal codes as 0', () => {
    const a = parseCAES('C2-A1-E2-S2')!;
    const b = parseCAES('C2-A1-E2-S2')!;
    expect(compareCAES(a, b)).toBe(0);
  });
});

describe('isWithinConstraints', () => {
  it('returns true when within limits', () => {
    const caes = parseCAES('C2-A1-E2-S2')!;
    expect(isWithinConstraints(caes, 'C3', 'S3', 'E3')).toBe(true);
  });

  it('returns false when classification exceeds', () => {
    const caes = parseCAES('C4-A1-E2-S2')!;
    expect(isWithinConstraints(caes, 'C3', 'S3', 'E3')).toBe(false);
  });

  it('returns false when scope exceeds', () => {
    const caes = parseCAES('C2-A1-E2-S4')!;
    expect(isWithinConstraints(caes, 'C3', 'S3', 'E3')).toBe(false);
  });
});

describe('formatCAES', () => {
  it('formats CAES code to string', () => {
    const caes = {
      classification: 'C2' as const,
      authority: 'A1-NOTIFY' as const,
      effect: 'E2-CHECKPOINT' as const,
      scope: 'S2-DOMAIN' as const,
    };
    expect(formatCAES(caes)).toBe('C2-A1-NOTIFY-E2-CHECKPOINT-S2-DOMAIN');
  });
});
