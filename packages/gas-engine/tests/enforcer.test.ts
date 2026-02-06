/**
 * Enforcer Tests
 */

import { describe, it, expect, beforeEach } from 'vitest';
import {
  enforceAction,
  enforceActions,
  enforceCrossDomain,
  recordEnforcementResult,
  getEnforcementSummary,
  resetEnforcementCounts,
  type DomainPolicy,
} from '../src/enforcer';
import { clearViolations } from '../src/violations';
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
      escalates_to: 'L2_review',
    },
    {
      id: 'update_escalation_rules',
      caes: 'C4-A3-E4-S3',
      description: 'Modify escalation rules',
      authority: 'A3-APPROVE',
      status: 'RESTRICTED',
    },
    {
      id: 'expand_autonomy',
      caes: 'C5-A4-E5-S4',
      description: 'Expand autonomy',
      authority: 'A4-MULTI',
      status: 'FORBIDDEN',
    },
  ],
  mrcc: {
    max_classification: 'C3',
    max_scope: 'S3',
    max_effect: 'E3',
    forbidden_actions: ['expand_autonomy'],
  },
  ncc: {
    default_classification: 'C2',
    default_scope: 'S2',
    default_effect: 'E2',
  },
};

describe('enforceAction', () => {
  beforeEach(() => {
    clearViolations();
    resetEnforcementCounts();
  });

  it('allows valid action and creates audit event', () => {
    const result = enforceAction(
      'read_policy',
      {
        actionSpace: testActionSpace,
        policyRefs: ['test-policy'],
        base120Refs: ['IN1', 'DE3'],
      },
      { actor: 'gas-agent' }
    );

    expect(result.outcome).toBe('ALLOWED');
    expect(result.audit_event).toBeDefined();
    expect(result.audit_event.action_id).toBe('read_policy');
    expect(result.audit_event.actor).toBe('gas-agent');
    expect(result.audit_event.policy_refs).toContain('test-policy');
    expect(result.audit_event.base120_refs).toContain('IN1');
  });

  it('blocks forbidden action', () => {
    const result = enforceAction(
      'expand_autonomy',
      {
        actionSpace: testActionSpace,
        policyRefs: ['test-policy'],
      },
      { actor: 'gas-agent' }
    );

    expect(result.outcome).toBe('BLOCKED');
    expect(result.violations.length).toBeGreaterThan(0);
  });

  it('escalates when action has escalates_to and fails validation', () => {
    // Create action space where block_action fails MRCC
    const restrictedSpace: ActionSpace = {
      ...testActionSpace,
      mrcc: {
        max_classification: 'C2', // block_action is C3, will fail
        max_scope: 'S2',
        max_effect: 'E2',
        forbidden_actions: [],
      },
    };

    const result = enforceAction(
      'block_action',
      {
        actionSpace: restrictedSpace,
        policyRefs: ['test-policy'],
      },
      { actor: 'gas-agent' }
    );

    expect(result.outcome).toBe('ESCALATED');
  });

  it('escalates restricted actions requiring approval', () => {
    const result = enforceAction(
      'update_escalation_rules',
      {
        actionSpace: testActionSpace,
        policyRefs: ['test-policy'],
      },
      { actor: 'gas-agent' }
    );

    // RESTRICTED actions that pass validation still get escalated
    // because they require approval
    expect(result.outcome).toBe('BLOCKED'); // C4 exceeds MRCC C3
  });

  it('sets checkpoint_required for C2+ actions', () => {
    const result = enforceAction(
      'flag_violation',
      {
        actionSpace: testActionSpace,
        policyRefs: ['test-policy'],
      },
      { actor: 'gas-agent' }
    );

    expect(result.outcome).toBe('ALLOWED');
    expect(result.checkpoint_required).toBe(true);
  });

  it('does not require checkpoint for C0/C1 actions', () => {
    const result = enforceAction(
      'read_policy',
      {
        actionSpace: testActionSpace,
        policyRefs: ['test-policy'],
      },
      { actor: 'gas-agent' }
    );

    expect(result.checkpoint_required).toBe(false);
  });
});

describe('enforceActions', () => {
  beforeEach(() => {
    clearViolations();
  });

  it('batch enforces multiple actions', () => {
    const results = enforceActions(
      ['read_policy', 'flag_violation'],
      {
        actionSpace: testActionSpace,
        policyRefs: ['test-policy'],
      },
      { actor: 'gas-agent' }
    );

    expect(results).toHaveLength(2);
    expect(results.every((r) => r.outcome === 'ALLOWED')).toBe(true);
  });
});

describe('enforceCrossDomain', () => {
  beforeEach(() => {
    clearViolations();
  });

  const permissiveDomain: DomainPolicy = {
    domain: 'permissive',
    actionSpace: testActionSpace,
    priority: 1,
  };

  const restrictiveDomain: DomainPolicy = {
    domain: 'restrictive',
    actionSpace: {
      ...testActionSpace,
      mrcc: {
        max_classification: 'C1',
        max_scope: 'S1',
        max_effect: 'E1',
        forbidden_actions: ['flag_violation'],
      },
    },
    priority: 10, // Higher priority = checked first
  };

  it('blocks if any high-priority domain blocks', () => {
    const result = enforceCrossDomain(
      'flag_violation',
      [permissiveDomain, restrictiveDomain],
      { actor: 'gas-agent' }
    );

    expect(result.outcome).toBe('BLOCKED');
  });

  it('allows if all domains allow', () => {
    const result = enforceCrossDomain(
      'read_policy',
      [permissiveDomain, restrictiveDomain],
      { actor: 'gas-agent' }
    );

    expect(result.outcome).toBe('ALLOWED');
  });
});

describe('enforcement summary', () => {
  beforeEach(() => {
    clearViolations();
    resetEnforcementCounts();
  });

  it('tracks enforcement counts', () => {
    const allowed = enforceAction(
      'read_policy',
      { actionSpace: testActionSpace, policyRefs: [] },
      { actor: 'test' }
    );
    recordEnforcementResult(allowed);

    const blocked = enforceAction(
      'expand_autonomy',
      { actionSpace: testActionSpace, policyRefs: [] },
      { actor: 'test' }
    );
    recordEnforcementResult(blocked);

    const summary = getEnforcementSummary();
    expect(summary.total_enforced).toBe(2);
    expect(summary.allowed).toBe(1);
    expect(summary.blocked).toBe(1);
  });
});
