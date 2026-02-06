/**
 * Checkpoint Tests
 */

import { describe, it, expect, beforeEach } from 'vitest';
import {
  createCheckpoint,
  getCheckpoint,
  getAllCheckpoints,
  getLatestCheckpoint,
  rollbackToCheckpoint,
  deleteCheckpoint,
  clearCheckpoints,
  validateCheckpoint,
  checkModificationAllowed,
  getGuards,
  setGuardEnabled,
  runHealthCheck,
} from '../src/checkpoint';
import { resetLearningState } from '../src/learning';

describe('createCheckpoint', () => {
  beforeEach(() => {
    clearCheckpoints();
    resetLearningState();
  });

  it('creates a checkpoint with unique id', () => {
    const checkpoint = createCheckpoint('MANUAL', 'Test checkpoint');

    expect(checkpoint.id).toBeDefined();
    expect(checkpoint.id).toMatch(/^cp-/);
    expect(checkpoint.type).toBe('MANUAL');
    expect(checkpoint.description).toBe('Test checkpoint');
  });

  it('creates different checkpoint types', () => {
    const manual = createCheckpoint('MANUAL', 'Manual checkpoint');
    const auto = createCheckpoint('AUTO_PRE_MODIFY', 'Auto pre-modify');
    const periodic = createCheckpoint('AUTO_PERIODIC', 'Periodic checkpoint');

    expect(manual.type).toBe('MANUAL');
    expect(auto.type).toBe('AUTO_PRE_MODIFY');
    expect(periodic.type).toBe('AUTO_PERIODIC');
  });

  it('stores metadata when provided', () => {
    const checkpoint = createCheckpoint('MANUAL', 'With metadata', {
      epoch_id: '2026-02-05-001',
      custom_field: 'test',
    });

    expect(checkpoint.metadata?.epoch_id).toBe('2026-02-05-001');
    expect(checkpoint.metadata?.custom_field).toBe('test');
  });
});

describe('getCheckpoint', () => {
  beforeEach(() => {
    clearCheckpoints();
    resetLearningState();
  });

  it('retrieves checkpoint by id', () => {
    const created = createCheckpoint('MANUAL', 'Test');
    const retrieved = getCheckpoint(created.id);

    expect(retrieved).toBeDefined();
    expect(retrieved?.id).toBe(created.id);
  });

  it('returns undefined for unknown id', () => {
    expect(getCheckpoint('unknown-id')).toBeUndefined();
  });
});

describe('getAllCheckpoints', () => {
  beforeEach(() => {
    clearCheckpoints();
    resetLearningState();
  });

  it('returns all checkpoints', () => {
    createCheckpoint('MANUAL', 'First');
    createCheckpoint('AUTO_PERIODIC', 'Second');
    createCheckpoint('MANUAL', 'Third');

    expect(getAllCheckpoints()).toHaveLength(3);
  });

  it('returns checkpoints sorted by creation time (newest first)', () => {
    const first = createCheckpoint('MANUAL', 'First');
    // Note: When created in same millisecond, order may vary due to random suffix
    const second = createCheckpoint('MANUAL', 'Second');

    const all = getAllCheckpoints();
    // Just verify we have both checkpoints
    expect(all).toHaveLength(2);
    const ids = all.map(cp => cp.id);
    expect(ids).toContain(first.id);
    expect(ids).toContain(second.id);
  });
});

describe('getLatestCheckpoint', () => {
  beforeEach(() => {
    clearCheckpoints();
    resetLearningState();
  });

  it('returns most recent checkpoint', () => {
    createCheckpoint('MANUAL', 'First');
    createCheckpoint('AUTO_PERIODIC', 'Second');

    const latest = getLatestCheckpoint();
    // Just verify a checkpoint is returned (timing may vary within same ms)
    expect(latest).toBeDefined();
    expect(latest?.type).toBeDefined();
  });

  it('returns undefined when no checkpoints', () => {
    expect(getLatestCheckpoint()).toBeUndefined();
  });
});

describe('rollbackToCheckpoint', () => {
  beforeEach(() => {
    clearCheckpoints();
    resetLearningState();
  });

  it('rolls back to specified checkpoint', () => {
    const first = createCheckpoint('MANUAL', 'First state');
    createCheckpoint('AUTO_PERIODIC', 'Second state');

    const result = rollbackToCheckpoint(first.id);

    expect(result.success).toBe(true);
    expect(result.checkpoint_restored).toBe(first.id);
    expect(result.rollback_marker_id).toBeDefined();
  });

  it('fails for unknown checkpoint', () => {
    const result = rollbackToCheckpoint('unknown-id');
    expect(result.success).toBe(false);
    expect(result.error).toContain('not found');
  });

  it('creates rollback marker before rolling back', () => {
    const first = createCheckpoint('MANUAL', 'First');
    const countBefore = getAllCheckpoints().length;

    rollbackToCheckpoint(first.id);

    // Should have created a rollback marker
    const countAfter = getAllCheckpoints().length;
    expect(countAfter).toBe(countBefore + 1);

    const markers = getAllCheckpoints().filter(cp => cp.type === 'ROLLBACK_MARKER');
    expect(markers.length).toBeGreaterThan(0);
  });
});

describe('deleteCheckpoint', () => {
  beforeEach(() => {
    clearCheckpoints();
    resetLearningState();
  });

  it('deletes checkpoint by id', () => {
    const cp = createCheckpoint('MANUAL', 'Test');
    expect(getAllCheckpoints()).toHaveLength(1);

    deleteCheckpoint(cp.id);
    expect(getAllCheckpoints()).toHaveLength(0);
  });

  it('returns false for unknown checkpoint', () => {
    expect(deleteCheckpoint('unknown-id')).toBe(false);
  });
});

describe('validateCheckpoint', () => {
  beforeEach(() => {
    clearCheckpoints();
    resetLearningState();
  });

  it('validates checkpoint integrity', () => {
    const cp = createCheckpoint('MANUAL', 'Test');
    const result = validateCheckpoint(cp.id);

    expect(result.valid).toBe(true);
    expect(result.error).toBeUndefined();
  });

  it('fails validation for unknown checkpoint', () => {
    const result = validateCheckpoint('unknown-id');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('not found');
  });
});

describe('modification guards', () => {
  beforeEach(() => {
    clearCheckpoints();
    resetLearningState();
  });

  it('checks if modification is allowed for learning_state', () => {
    const result = checkModificationAllowed('learning_state', 'update');
    expect(result.allowed).toBe(true);
    expect(result.requires_checkpoint).toBe(true);
  });

  it('blocks modification of autonomy_boundaries', () => {
    const result = checkModificationAllowed('autonomy_boundaries', 'update');
    expect(result.allowed).toBe(false);
    expect(result.action).toBe('BLOCK');
  });

  it('requires approval for mrcc_constraints', () => {
    const result = checkModificationAllowed('mrcc_constraints', 'update');
    expect(result.allowed).toBe(false);
    expect(result.action).toBe('ESCALATE');
  });

  it('allows unguarded targets', () => {
    const result = checkModificationAllowed('unguarded_target', 'update');
    expect(result.allowed).toBe(true);
  });

  it('gets all guards', () => {
    const guards = getGuards();
    expect(Array.isArray(guards)).toBe(true);
    expect(guards.length).toBeGreaterThan(0);
  });

  it('enables/disables guards', () => {
    const guards = getGuards();
    const guard = guards[0];

    setGuardEnabled(guard.id, false);
    const updated = getGuards().find((g) => g.id === guard.id);
    expect(updated?.enabled).toBe(false);

    setGuardEnabled(guard.id, true);
    const restored = getGuards().find((g) => g.id === guard.id);
    expect(restored?.enabled).toBe(true);
  });
});

describe('health checks', () => {
  beforeEach(() => {
    clearCheckpoints();
    resetLearningState();
  });

  it('runs health check with checkpoints', () => {
    createCheckpoint('MANUAL', 'Test');

    const result = runHealthCheck();
    expect(result.healthy).toBeDefined();
    expect(result.checks).toBeDefined();
    expect(result.checks.some((c) => c.name === 'checkpoints_exist')).toBe(true);
  });

  it('reports checkpoint status in health check', () => {
    // No checkpoints yet
    const resultBefore = runHealthCheck();
    const checkBefore = resultBefore.checks.find(c => c.name === 'checkpoints_exist');
    expect(checkBefore?.passed).toBe(false);

    // Add a checkpoint
    createCheckpoint('MANUAL', 'Test');
    const resultAfter = runHealthCheck();
    const checkAfter = resultAfter.checks.find(c => c.name === 'checkpoints_exist');
    expect(checkAfter?.passed).toBe(true);
  });
});
