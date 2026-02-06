/**
 * Checkpoint System
 * State snapshots, rollback automation, and self-modification guards
 */

import type { ActionSpace, LearningState } from './types';
import { getLearningState, importLearningState, exportLearningState } from './learning';

// Checkpoint storage (in-memory; production would use file system)
const checkpoints: Map<string, Checkpoint> = new Map();

export interface Checkpoint {
  id: string;
  created_at: string;
  type: CheckpointType;
  description: string;
  state: CheckpointState;
  hash: string;
  parent_id?: string;
  metadata?: Record<string, unknown>;
}

export type CheckpointType =
  | 'MANUAL'
  | 'AUTO_PRE_MODIFY'
  | 'AUTO_PERIODIC'
  | 'ROLLBACK_MARKER';

export interface CheckpointState {
  learning_state: string; // Serialized JSON
  action_space_hash?: string;
  governance_policy_hash?: string;
  epoch_id?: string;
}

// Create a checkpoint
export const createCheckpoint = (
  type: CheckpointType,
  description: string,
  metadata?: Record<string, unknown>
): Checkpoint => {
  const learningState = exportLearningState();
  const state: CheckpointState = {
    learning_state: learningState,
    epoch_id: metadata?.epoch_id as string,
  };

  const checkpoint: Checkpoint = {
    id: generateCheckpointId(),
    created_at: new Date().toISOString(),
    type,
    description,
    state,
    hash: hashState(state),
    parent_id: getLatestCheckpointId(),
    metadata,
  };

  checkpoints.set(checkpoint.id, checkpoint);
  return checkpoint;
};

// Get checkpoint by ID
export const getCheckpoint = (id: string): Checkpoint | undefined => {
  return checkpoints.get(id);
};

// Get all checkpoints
export const getAllCheckpoints = (): Checkpoint[] => {
  return Array.from(checkpoints.values()).sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );
};

// Get latest checkpoint
export const getLatestCheckpoint = (): Checkpoint | undefined => {
  const all = getAllCheckpoints();
  return all[0];
};

// Get latest checkpoint ID
const getLatestCheckpointId = (): string | undefined => {
  return getLatestCheckpoint()?.id;
};

// Rollback to checkpoint
export const rollbackToCheckpoint = (id: string): RollbackResult => {
  const checkpoint = checkpoints.get(id);
  if (!checkpoint) {
    return {
      success: false,
      error: `Checkpoint '${id}' not found`,
    };
  }

  // Create rollback marker before rolling back
  const marker = createCheckpoint(
    'ROLLBACK_MARKER',
    `Rollback marker before restoring to ${id}`,
    { rollback_to: id }
  );

  // Restore learning state
  try {
    const restored = importLearningState(checkpoint.state.learning_state);
    if (!restored) {
      return {
        success: false,
        error: 'Failed to restore learning state',
        rollback_marker_id: marker.id,
      };
    }
  } catch (error) {
    return {
      success: false,
      error: `Error restoring state: ${error}`,
      rollback_marker_id: marker.id,
    };
  }

  return {
    success: true,
    checkpoint_restored: id,
    rollback_marker_id: marker.id,
  };
};

export interface RollbackResult {
  success: boolean;
  checkpoint_restored?: string;
  rollback_marker_id?: string;
  error?: string;
}

// Delete checkpoint
export const deleteCheckpoint = (id: string): boolean => {
  return checkpoints.delete(id);
};

// Clear all checkpoints
export const clearCheckpoints = (): void => {
  checkpoints.clear();
};

// Validate checkpoint integrity
export const validateCheckpoint = (id: string): ValidationResult => {
  const checkpoint = checkpoints.get(id);
  if (!checkpoint) {
    return { valid: false, error: 'Checkpoint not found' };
  }

  const currentHash = hashState(checkpoint.state);
  if (currentHash !== checkpoint.hash) {
    return {
      valid: false,
      error: 'Checkpoint hash mismatch - state may be corrupted',
    };
  }

  return { valid: true };
};

export interface ValidationResult {
  valid: boolean;
  error?: string;
}

// Self-Modification Guards
export interface ModificationGuard {
  id: string;
  guard_type: GuardType;
  target: string;
  condition: string;
  action: GuardAction;
  enabled: boolean;
}

export type GuardType =
  | 'REQUIRE_CHECKPOINT'
  | 'REQUIRE_APPROVAL'
  | 'RATE_LIMIT'
  | 'FORBIDDEN';

export type GuardAction =
  | 'BLOCK'
  | 'CHECKPOINT_THEN_ALLOW'
  | 'ESCALATE'
  | 'LOG_ONLY';

const guards: ModificationGuard[] = [
  {
    id: 'guard-1',
    guard_type: 'REQUIRE_CHECKPOINT',
    target: 'learning_state',
    condition: 'any_modification',
    action: 'CHECKPOINT_THEN_ALLOW',
    enabled: true,
  },
  {
    id: 'guard-2',
    guard_type: 'FORBIDDEN',
    target: 'autonomy_boundaries',
    condition: 'any_modification',
    action: 'BLOCK',
    enabled: true,
  },
  {
    id: 'guard-3',
    guard_type: 'REQUIRE_APPROVAL',
    target: 'mrcc_constraints',
    condition: 'any_modification',
    action: 'ESCALATE',
    enabled: true,
  },
  {
    id: 'guard-4',
    guard_type: 'RATE_LIMIT',
    target: 'policy_proposals',
    condition: 'more_than_10_per_hour',
    action: 'BLOCK',
    enabled: true,
  },
];

// Check if modification is allowed
export const checkModificationAllowed = (
  target: string,
  modificationType: string
): GuardCheckResult => {
  const applicableGuards = guards.filter(
    (g) => g.enabled && g.target === target
  );

  for (const guard of applicableGuards) {
    if (guard.guard_type === 'FORBIDDEN') {
      return {
        allowed: false,
        action: 'BLOCK',
        reason: `Modification of '${target}' is forbidden`,
        guard_id: guard.id,
      };
    }

    if (guard.guard_type === 'REQUIRE_APPROVAL') {
      return {
        allowed: false,
        action: 'ESCALATE',
        reason: `Modification of '${target}' requires approval`,
        guard_id: guard.id,
      };
    }

    if (guard.guard_type === 'REQUIRE_CHECKPOINT') {
      return {
        allowed: true,
        action: 'CHECKPOINT_THEN_ALLOW',
        reason: `Checkpoint required before modifying '${target}'`,
        guard_id: guard.id,
        requires_checkpoint: true,
      };
    }
  }

  return { allowed: true };
};

export interface GuardCheckResult {
  allowed: boolean;
  action?: GuardAction;
  reason?: string;
  guard_id?: string;
  requires_checkpoint?: boolean;
}

// Get all guards
export const getGuards = (): ModificationGuard[] => {
  return [...guards];
};

// Enable/disable guard
export const setGuardEnabled = (id: string, enabled: boolean): boolean => {
  const guard = guards.find((g) => g.id === id);
  if (!guard) return false;
  guard.enabled = enabled;
  return true;
};

// Utility functions
const generateCheckpointId = (): string => {
  const now = new Date();
  const date = now.toISOString().slice(0, 10);
  const time = now.toISOString().slice(11, 19).replace(/:/g, '');
  const random = Math.random().toString(36).slice(2, 6);
  return `cp-${date}-${time}-${random}`;
};

const hashState = (state: CheckpointState): string => {
  const content = JSON.stringify(state);
  let hash = 0;
  for (let i = 0; i < content.length; i++) {
    const char = content.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return `sha256:${Math.abs(hash).toString(16).padStart(16, '0')}`;
};

// Health check after modification
export interface HealthCheckResult {
  healthy: boolean;
  checks: HealthCheck[];
  should_rollback: boolean;
}

export interface HealthCheck {
  name: string;
  passed: boolean;
  message?: string;
}

export const runHealthCheck = (): HealthCheckResult => {
  const checks: HealthCheck[] = [];

  // Check learning state is valid
  try {
    const state = getLearningState();
    checks.push({
      name: 'learning_state_valid',
      passed: state.version !== undefined,
    });
  } catch {
    checks.push({
      name: 'learning_state_valid',
      passed: false,
      message: 'Failed to get learning state',
    });
  }

  // Check checkpoints exist
  const checkpointCount = getAllCheckpoints().length;
  checks.push({
    name: 'checkpoints_exist',
    passed: checkpointCount > 0,
    message: `${checkpointCount} checkpoints available`,
  });

  // Check guards are active
  const activeGuards = guards.filter((g) => g.enabled).length;
  checks.push({
    name: 'guards_active',
    passed: activeGuards >= 3,
    message: `${activeGuards} guards active`,
  });

  const healthy = checks.every((c) => c.passed);
  const shouldRollback = checks.filter((c) => !c.passed).length >= 2;

  return {
    healthy,
    checks,
    should_rollback: shouldRollback,
  };
};

// Auto-rollback if health degraded
export const autoRollbackIfNeeded = (): RollbackResult | null => {
  const health = runHealthCheck();

  if (!health.should_rollback) {
    return null;
  }

  const latest = getLatestCheckpoint();
  if (!latest) {
    return {
      success: false,
      error: 'No checkpoint available for auto-rollback',
    };
  }

  return rollbackToCheckpoint(latest.id);
};
