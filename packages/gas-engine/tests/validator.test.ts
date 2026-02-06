/**
 * Validator Tests
 */

import { describe, it, expect, beforeEach } from 'vitest';
import {
  validateAction,
  validateActions,
  getAllowedActions,
} from '../src/validator';
import type { ActionSpace } from '../src/types';

const testActionSpace: ActionSpace = {
  version: '1.0.0',
  actions: [
    {
      id: 'read_policy',
      caes: 'C0-A0-E0-S1',
      description: 'Read a policy',
      authority: 'A0-SELF',
      status: 'ALLOWED',
    },
    {
      id: 'flag_violation',
      caes: 'C2-A1-E2-S2',
      description: 'Flag a violation',
      authority: 'A1-NOTIFY',
      status: 'ALLOWED',
    },
    {
      id: 'block_action',
      caes: 'C3-A1-E3-S3',
      description: 'Block an action',
      authority: 'A1-NOTIFY',
      status: 'ALLOWED',
    },
    {
      id: 'expand_autonomy',
      caes: 'C5-A4-E5-S4',
      description: 'Expand autonomy',
      authority: 'A4-MULTI',
      status: 'FORBIDDEN_WITHOUT_OVERRIDE',
    },
    {
      id: 'modify_own_boundaries',
      caes: 'C5-A4-E5-S0',
      description: 'Modify own boundaries',
      authority: 'A4-MULTI',
      status: 'FORBIDDEN',
    },
  ],
  mrcc: {
    max_classification: 'C3',
    max_scope: 'S3',
    max_effect: 'E3',
    forbidden_actions: ['expand_autonomy', 'modify_own_boundaries'],
    rate_limits: {
      C3_per_hour: 10,
      total_per_minute: 60,
    },
  },
  ncc: {
    default_classification: 'C2',
    default_scope: 'S2',
    default_effect: 'E2',
    preferred_actions: ['read_policy', 'flag_violation'],
    discouraged_actions: ['block_action'],
  },
  current_epoch: {
    id: '2026-02-05-001',
    started: '2026-02-05T00:00:00Z',
    policy_hash: 'sha256:test',
    monotonic_properties: [
      'autonomy_level_cannot_increase',
      'forbidden_stays_forbidden',
    ],
  },
};

describe('validateAction', () => {
  it('validates allowed action', () => {
    const result = validateAction('read_policy', testActionSpace, {
      actor: 'test',
    });
    expect(result.valid).toBe(true);
    expect(result.violations).toHaveLength(0);
  });

  it('rejects action not in space', () => {
    const result = validateAction('unknown_action', testActionSpace, {
      actor: 'test',
    });
    expect(result.valid).toBe(false);
    expect(result.checks[0].check).toBe('action_exists');
    expect(result.checks[0].ok).toBe(false);
  });

  it('rejects forbidden action', () => {
    const result = validateAction('modify_own_boundaries', testActionSpace, {
      actor: 'test',
    });
    expect(result.valid).toBe(false);
    expect(result.violations.length).toBeGreaterThan(0);
    expect(result.violations[0].violation_type).toBe('FORBIDDEN_ACTION');
  });

  it('rejects action in MRCC forbidden list', () => {
    const result = validateAction('expand_autonomy', testActionSpace, {
      actor: 'test',
    });
    expect(result.valid).toBe(false);
  });

  it('adds recommendations for discouraged actions', () => {
    const result = validateAction('block_action', testActionSpace, {
      actor: 'test',
    });
    expect(result.valid).toBe(true);
    expect(result.recommendations).toBeDefined();
    expect(result.recommendations?.[0]).toContain('discouraged');
  });

  it('checks rate limits when provided', () => {
    const result = validateAction('block_action', testActionSpace, {
      actor: 'test',
      rate_counts: {
        C3_per_hour: 15, // Exceeds limit of 10
      },
    });
    expect(result.valid).toBe(false);
    expect(result.violations.some((v) => v.violation_type === 'RATE_LIMIT')).toBe(true);
  });
});

describe('validateActions', () => {
  it('validates multiple actions', () => {
    const results = validateActions(
      ['read_policy', 'flag_violation'],
      testActionSpace,
      { actor: 'test' }
    );
    expect(results).toHaveLength(2);
    expect(results.every((r) => r.valid)).toBe(true);
  });
});

describe('getAllowedActions', () => {
  it('returns only allowed actions within MRCC', () => {
    const allowed = getAllowedActions(testActionSpace);
    expect(allowed.map((a) => a.id)).toContain('read_policy');
    expect(allowed.map((a) => a.id)).toContain('flag_violation');
    expect(allowed.map((a) => a.id)).toContain('block_action');
    expect(allowed.map((a) => a.id)).not.toContain('expand_autonomy');
    expect(allowed.map((a) => a.id)).not.toContain('modify_own_boundaries');
  });
});
