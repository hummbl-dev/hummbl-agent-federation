/**
 * Learning Module Tests
 */

import { describe, it, expect, beforeEach } from 'vitest';
import {
  getLearningState,
  updateLearningState,
  resetLearningState,
  learnFromViolations,
  recordFeedback,
  generateProposal,
  getProposalsByStatus,
  updateProposalStatus,
  exportLearningState,
  importLearningState,
  runBenchmark,
  type LearnedPattern,
} from '../src/learning';
import { captureViolation, clearViolations } from '../src/violations';
import type { Violation, ActionSpace } from '../src/types';

const createTestViolation = (overrides: Partial<Violation> = {}): Violation => ({
  id: crypto.randomUUID(),
  timestamp: new Date().toISOString(),
  action_id: 'test_action',
  caes: 'C2-A1-E2-S2',
  violation_type: 'MRCC_EXCEEDED',
  severity: 'HIGH',
  context: {
    actor: 'test-agent',
  },
  ...overrides,
});

const testActionSpace: ActionSpace = {
  version: '1.0.0',
  actions: [
    {
      id: 'test_action',
      caes: 'C2-A1-E2-S2',
      description: 'Test action',
      authority: 'A1-NOTIFY',
      status: 'ALLOWED',
    },
    {
      id: 'risky_action',
      caes: 'C3-A2-E3-S3',
      description: 'Risky action',
      authority: 'A2-REVIEW',
      status: 'ALLOWED',
    },
  ],
  mrcc: {
    max_classification: 'C3',
    max_scope: 'S3',
    max_effect: 'E3',
    forbidden_actions: ['expand_autonomy'],
    rate_limits: { C3_per_hour: 10 },
  },
  ncc: {
    default_classification: 'C2',
    default_scope: 'S2',
    default_effect: 'E2',
  },
  current_epoch: {
    id: '2026-02-05-001',
    started: '2026-02-05T00:00:00Z',
    policy_hash: 'sha256:test',
    monotonic_properties: ['audit_cannot_disable'],
  },
};

describe('getLearningState', () => {
  beforeEach(() => {
    resetLearningState();
  });

  it('returns initial learning state', () => {
    const state = getLearningState();

    expect(state).toBeDefined();
    expect(state.version).toBe('1.0.0');
    expect(state.patterns).toBeDefined();
    expect(Array.isArray(state.patterns)).toBe(true);
    expect(state.feedback).toBeDefined();
    expect(state.proposals).toBeDefined();
  });
});

describe('updateLearningState', () => {
  beforeEach(() => {
    resetLearningState();
  });

  it('updates learning state', () => {
    const initial = getLearningState();
    expect(initial.patterns).toHaveLength(0);

    updateLearningState({
      patterns: [
        {
          id: 'pattern-1',
          pattern_type: 'RECURRING_VIOLATION',
          action_id: 'expand_autonomy',
          violation_type: 'FORBIDDEN_ACTION',
          frequency: 5,
          first_seen: new Date().toISOString(),
          last_seen: new Date().toISOString(),
          confidence: 0.8,
          suggested_action: 'UPDATE_POLICY',
        },
      ],
    });

    const updated = getLearningState();
    expect(updated.patterns).toHaveLength(1);
    expect(updated.patterns[0].action_id).toBe('expand_autonomy');
  });
});

describe('learnFromViolations', () => {
  beforeEach(() => {
    resetLearningState();
    clearViolations();
  });

  it('learns patterns from violations', () => {
    // Create violations with pattern (3+ of same type triggers escalation)
    for (let i = 0; i < 5; i++) {
      captureViolation(createTestViolation({
        action_id: 'risky_action',
        violation_type: 'MRCC_EXCEEDED',
      }));
    }

    const learned = learnFromViolations();

    expect(learned.length).toBeGreaterThan(0);
    expect(learned[0].action_id).toBe('risky_action');
    expect(learned[0].frequency).toBe(5);
  });

  it('returns empty array when no escalation-worthy patterns', () => {
    // Only 2 violations - not enough to trigger escalation
    captureViolation(createTestViolation());
    captureViolation(createTestViolation());

    const learned = learnFromViolations();
    expect(learned).toHaveLength(0);
  });
});

describe('recordFeedback', () => {
  beforeEach(() => {
    resetLearningState();
  });

  it('records user feedback', () => {
    const feedback = recordFeedback(
      'block_action',
      'OVERRIDE_APPROVED',
      'admin',
      'Emergency situation required override'
    );

    expect(feedback.id).toBeDefined();
    expect(feedback.action_id).toBe('block_action');
    expect(feedback.feedback_type).toBe('OVERRIDE_APPROVED');
    expect(feedback.source).toBe('admin');
    expect(feedback.reason).toBe('Emergency situation required override');

    const state = getLearningState();
    expect(state.feedback).toHaveLength(1);
  });

  it('applies weight adjustments', () => {
    const initialState = getLearningState();
    const initialWeight = initialState.weights.actions['test_action'] ?? 0;

    recordFeedback('test_action', 'OVERRIDE_APPROVED', 'admin');

    const updatedState = getLearningState();
    const newWeight = updatedState.weights.actions['test_action'];
    expect(newWeight).toBeGreaterThan(initialWeight);
  });

  it('records multiple feedback entries', () => {
    for (let i = 0; i < 5; i++) {
      recordFeedback(`action_${i}`, 'POLICY_UPDATED', 'admin');
    }

    const state = getLearningState();
    expect(state.feedback).toHaveLength(5);
  });
});

describe('generateProposal', () => {
  beforeEach(() => {
    resetLearningState();
  });

  it('generates policy proposal from high-confidence pattern', () => {
    const pattern: LearnedPattern = {
      id: 'pattern-1',
      pattern_type: 'RECURRING_VIOLATION',
      action_id: 'test_action',
      violation_type: 'MRCC_EXCEEDED',
      frequency: 10,
      first_seen: new Date().toISOString(),
      last_seen: new Date().toISOString(),
      confidence: 0.8,
      suggested_action: 'UPDATE_POLICY',
    };

    const proposal = generateProposal(pattern, testActionSpace);

    expect(proposal).not.toBeNull();
    expect(proposal?.status).toBe('DRAFT');
    expect(proposal?.action_id).toBe('test_action');
    expect(proposal?.confidence).toBe(0.8);
  });

  it('returns null for low-confidence patterns', () => {
    const pattern: LearnedPattern = {
      id: 'pattern-1',
      pattern_type: 'RECURRING_VIOLATION',
      action_id: 'test_action',
      violation_type: 'MRCC_EXCEEDED',
      frequency: 3,
      first_seen: new Date().toISOString(),
      last_seen: new Date().toISOString(),
      confidence: 0.3, // Below 0.5 threshold
      suggested_action: 'UPDATE_POLICY',
    };

    const proposal = generateProposal(pattern, testActionSpace);
    expect(proposal).toBeNull();
  });

  it('returns null for unknown action', () => {
    const pattern: LearnedPattern = {
      id: 'pattern-1',
      pattern_type: 'RECURRING_VIOLATION',
      action_id: 'unknown_action',
      violation_type: 'MRCC_EXCEEDED',
      frequency: 10,
      first_seen: new Date().toISOString(),
      last_seen: new Date().toISOString(),
      confidence: 0.8,
      suggested_action: 'UPDATE_POLICY',
    };

    const proposal = generateProposal(pattern, testActionSpace);
    expect(proposal).toBeNull();
  });
});

describe('proposal management', () => {
  beforeEach(() => {
    resetLearningState();
  });

  it('filters proposals by status', () => {
    const pattern1: LearnedPattern = {
      id: 'pattern-1',
      pattern_type: 'RECURRING_VIOLATION',
      action_id: 'test_action',
      violation_type: 'MRCC_EXCEEDED',
      frequency: 10,
      first_seen: new Date().toISOString(),
      last_seen: new Date().toISOString(),
      confidence: 0.8,
      suggested_action: 'UPDATE_POLICY',
    };

    const pattern2: LearnedPattern = {
      ...pattern1,
      id: 'pattern-2',
      action_id: 'risky_action',
    };

    const p1 = generateProposal(pattern1, testActionSpace);
    generateProposal(pattern2, testActionSpace);

    expect(p1).not.toBeNull();
    updateProposalStatus(p1!.id, 'APPROVED');

    const approved = getProposalsByStatus('APPROVED');
    const draft = getProposalsByStatus('DRAFT');

    expect(approved).toHaveLength(1);
    expect(draft).toHaveLength(1);
  });

  it('updates proposal status', () => {
    const pattern: LearnedPattern = {
      id: 'pattern-1',
      pattern_type: 'RECURRING_VIOLATION',
      action_id: 'test_action',
      violation_type: 'MRCC_EXCEEDED',
      frequency: 10,
      first_seen: new Date().toISOString(),
      last_seen: new Date().toISOString(),
      confidence: 0.8,
      suggested_action: 'UPDATE_POLICY',
    };

    const proposal = generateProposal(pattern, testActionSpace);
    expect(proposal).not.toBeNull();
    expect(proposal?.status).toBe('DRAFT');

    updateProposalStatus(proposal!.id, 'PENDING_REVIEW');
    expect(getProposalsByStatus('PENDING_REVIEW')).toHaveLength(1);

    updateProposalStatus(proposal!.id, 'APPROVED');
    expect(getProposalsByStatus('APPROVED')).toHaveLength(1);
  });
});

describe('runBenchmark', () => {
  beforeEach(() => {
    resetLearningState();
  });

  it('runs benchmark against SOC2', () => {
    const result = runBenchmark(testActionSpace, 'SOC2');

    expect(result.benchmark_type).toBe('SOC2');
    expect(result.standard).toBe('SOC 2 Type II');
    expect(result.score).toBeDefined();
    expect(result.gaps).toBeDefined();
  });

  it('identifies gaps in action space', () => {
    // Action space without forbidden expand_autonomy
    const incompleteActionSpace: ActionSpace = {
      ...testActionSpace,
      mrcc: {
        ...testActionSpace.mrcc,
        forbidden_actions: [], // Missing expand_autonomy
      },
    };

    const result = runBenchmark(incompleteActionSpace, 'NIST');
    expect(result.gaps.some(g => g.control_id.includes('AUTH'))).toBe(true);
  });
});

describe('export/import learning state', () => {
  beforeEach(() => {
    resetLearningState();
  });

  it('exports and imports learning state as JSON', () => {
    recordFeedback('action1', 'OVERRIDE_APPROVED', 'admin');

    const exported = exportLearningState();
    expect(typeof exported).toBe('string');

    const parsed = JSON.parse(exported);
    expect(parsed.feedback).toHaveLength(1);

    resetLearningState();
    expect(getLearningState().feedback).toHaveLength(0);

    const success = importLearningState(exported);
    expect(success).toBe(true);
    expect(getLearningState().feedback).toHaveLength(1);
  });

  it('returns false for invalid JSON', () => {
    const success = importLearningState('invalid json');
    expect(success).toBe(false);
  });
});
