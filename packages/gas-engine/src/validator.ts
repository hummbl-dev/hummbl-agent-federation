/**
 * Policy Validator
 * Validates actions against ACTION SPACE constraints
 */

import type {
  ActionSpace,
  ActionDefinition,
  ConstraintSet,
  ValidationResult,
  PolicyCheck,
  Violation,
  ViolationType,
  ViolationSeverity,
} from './types';
import { parseCAES, getLevel, isWithinConstraints } from './caes';

export interface ValidatorContext {
  actor: string;
  epoch_id?: string;
  rate_counts?: Record<string, number>;
}

// Validate an action against the action space
export const validateAction = (
  actionId: string,
  actionSpace: ActionSpace,
  context: ValidatorContext
): ValidationResult => {
  const checks: PolicyCheck[] = [];
  const violations: Violation[] = [];
  const recommendations: string[] = [];

  // Find action definition
  const action = actionSpace.actions.find((a) => a.id === actionId);
  if (!action) {
    checks.push({
      check: 'action_exists',
      ok: false,
      reason: `Action '${actionId}' not found in action space`,
    });
    return { valid: false, action_id: actionId, checks, violations };
  }

  checks.push({ check: 'action_exists', ok: true });

  // Check action status
  const statusCheck = checkActionStatus(action);
  checks.push(statusCheck);
  if (!statusCheck.ok) {
    violations.push(createViolation(action, 'FORBIDDEN_ACTION', 'HIGH', context));
  }

  // Check MRCC constraints
  const mrccChecks = checkMRCC(action, actionSpace.mrcc, context);
  checks.push(...mrccChecks.checks);
  violations.push(...mrccChecks.violations);

  // Check rate limits
  if (context.rate_counts) {
    const rateCheck = checkRateLimits(action, actionSpace.mrcc, context.rate_counts);
    checks.push(rateCheck.check);
    if (rateCheck.violation) {
      violations.push(rateCheck.violation);
    }
  }

  // Check epoch monotonic properties
  if (actionSpace.current_epoch) {
    const epochCheck = checkEpochConstraints(action, actionSpace.current_epoch);
    checks.push(epochCheck);
    if (!epochCheck.ok) {
      violations.push(createViolation(action, 'EPOCH_VIOLATION', 'CRITICAL', context));
    }
  }

  // Add NCC-based recommendations
  if (actionSpace.ncc.discouraged_actions?.includes(actionId)) {
    recommendations.push(`Action '${actionId}' is discouraged by NCC. Consider alternatives.`);
  }

  const valid = checks.every((c) => c.ok);

  return {
    valid,
    action_id: actionId,
    checks,
    violations,
    recommendations: recommendations.length > 0 ? recommendations : undefined,
  };
};

// Check action status
const checkActionStatus = (action: ActionDefinition): PolicyCheck => {
  if (action.status === 'FORBIDDEN') {
    return {
      check: 'action_status',
      ok: false,
      reason: `Action '${action.id}' is FORBIDDEN`,
    };
  }
  if (action.status === 'FORBIDDEN_WITHOUT_OVERRIDE') {
    return {
      check: 'action_status',
      ok: false,
      reason: `Action '${action.id}' requires explicit override`,
    };
  }
  if (action.status === 'RESTRICTED') {
    return {
      check: 'action_status',
      ok: true,
      reason: `Action '${action.id}' is RESTRICTED (approval required)`,
    };
  }
  return { check: 'action_status', ok: true };
};

// Check MRCC constraints
const checkMRCC = (
  action: ActionDefinition,
  mrcc: ConstraintSet,
  context: ValidatorContext
): { checks: PolicyCheck[]; violations: Violation[] } => {
  const checks: PolicyCheck[] = [];
  const violations: Violation[] = [];

  const caes = parseCAES(action.caes);
  if (!caes) {
    checks.push({
      check: 'caes_parse',
      ok: false,
      reason: `Invalid CAES code: ${action.caes}`,
    });
    return { checks, violations };
  }

  checks.push({ check: 'caes_parse', ok: true });

  // Check classification limit
  if (mrcc.max_classification) {
    const actionC = getLevel(caes.classification);
    const maxC = getLevel(mrcc.max_classification);
    const ok = actionC <= maxC;
    checks.push({
      check: 'mrcc_classification',
      ok,
      reason: ok ? undefined : `${caes.classification} exceeds max ${mrcc.max_classification}`,
    });
    if (!ok) {
      violations.push(createViolation(action, 'MRCC_EXCEEDED', 'HIGH', context));
    }
  }

  // Check scope limit
  if (mrcc.max_scope) {
    const actionS = getLevel(caes.scope);
    const maxS = getLevel(mrcc.max_scope);
    const ok = actionS <= maxS;
    checks.push({
      check: 'mrcc_scope',
      ok,
      reason: ok ? undefined : `${caes.scope} exceeds max ${mrcc.max_scope}`,
    });
    if (!ok) {
      violations.push(createViolation(action, 'SCOPE_EXCEEDED', 'HIGH', context));
    }
  }

  // Check effect limit
  if (mrcc.max_effect) {
    const actionE = getLevel(caes.effect);
    const maxE = getLevel(mrcc.max_effect);
    const ok = actionE <= maxE;
    checks.push({
      check: 'mrcc_effect',
      ok,
      reason: ok ? undefined : `${caes.effect} exceeds max ${mrcc.max_effect}`,
    });
  }

  // Check forbidden actions
  if (mrcc.forbidden_actions?.includes(action.id)) {
    checks.push({
      check: 'mrcc_forbidden',
      ok: false,
      reason: `Action '${action.id}' is in MRCC forbidden list`,
    });
    violations.push(createViolation(action, 'FORBIDDEN_ACTION', 'CRITICAL', context));
  } else {
    checks.push({ check: 'mrcc_forbidden', ok: true });
  }

  return { checks, violations };
};

// Check rate limits
const checkRateLimits = (
  action: ActionDefinition,
  mrcc: ConstraintSet,
  rateCounts: Record<string, number>
): { check: PolicyCheck; violation?: Violation } => {
  if (!mrcc.rate_limits) {
    return { check: { check: 'rate_limit', ok: true } };
  }

  const caes = parseCAES(action.caes);
  if (!caes) {
    return { check: { check: 'rate_limit', ok: true } };
  }

  // Check classification-specific rate limit
  const classKey = `${caes.classification}_per_hour`;
  if (mrcc.rate_limits[classKey]) {
    const limit = mrcc.rate_limits[classKey];
    const current = rateCounts[classKey] ?? 0;
    if (current >= limit) {
      return {
        check: {
          check: 'rate_limit',
          ok: false,
          reason: `Rate limit exceeded: ${current}/${limit} for ${classKey}`,
        },
        violation: {
          id: crypto.randomUUID(),
          timestamp: new Date().toISOString(),
          action_id: action.id,
          caes: action.caes,
          violation_type: 'RATE_LIMIT',
          severity: 'MEDIUM',
          context: {
            actor: 'rate_checker',
          },
        },
      };
    }
  }

  // Check total rate limit
  if (mrcc.rate_limits['total_per_minute']) {
    const limit = mrcc.rate_limits['total_per_minute'];
    const current = rateCounts['total_per_minute'] ?? 0;
    if (current >= limit) {
      return {
        check: {
          check: 'rate_limit',
          ok: false,
          reason: `Total rate limit exceeded: ${current}/${limit}`,
        },
        violation: {
          id: crypto.randomUUID(),
          timestamp: new Date().toISOString(),
          action_id: action.id,
          caes: action.caes,
          violation_type: 'RATE_LIMIT',
          severity: 'MEDIUM',
          context: {
            actor: 'rate_checker',
          },
        },
      };
    }
  }

  return { check: { check: 'rate_limit', ok: true } };
};

// Check epoch monotonic properties
const checkEpochConstraints = (
  action: ActionDefinition,
  epoch: { monotonic_properties: string[] }
): PolicyCheck => {
  const caes = parseCAES(action.caes);
  if (!caes) {
    return { check: 'epoch_monotonic', ok: true };
  }

  // Check if action would violate monotonic properties
  if (
    epoch.monotonic_properties.includes('autonomy_level_cannot_increase') &&
    action.id === 'expand_autonomy'
  ) {
    return {
      check: 'epoch_monotonic',
      ok: false,
      reason: 'Monotonic property violation: autonomy_level_cannot_increase',
    };
  }

  if (
    epoch.monotonic_properties.includes('forbidden_stays_forbidden') &&
    action.status === 'FORBIDDEN'
  ) {
    return {
      check: 'epoch_monotonic',
      ok: false,
      reason: 'Monotonic property violation: forbidden_stays_forbidden',
    };
  }

  return { check: 'epoch_monotonic', ok: true };
};

// Create violation record
const createViolation = (
  action: ActionDefinition,
  type: ViolationType,
  severity: ViolationSeverity,
  context: ValidatorContext
): Violation => {
  return {
    id: crypto.randomUUID(),
    timestamp: new Date().toISOString(),
    action_id: action.id,
    caes: action.caes,
    violation_type: type,
    severity,
    context: {
      actor: context.actor,
      epoch_id: context.epoch_id,
    },
  };
};

// Batch validate multiple actions
export const validateActions = (
  actionIds: string[],
  actionSpace: ActionSpace,
  context: ValidatorContext
): ValidationResult[] => {
  return actionIds.map((id) => validateAction(id, actionSpace, context));
};

// Get all allowed actions for current constraints
export const getAllowedActions = (actionSpace: ActionSpace): ActionDefinition[] => {
  return actionSpace.actions.filter((action) => {
    if (action.status === 'FORBIDDEN' || action.status === 'FORBIDDEN_WITHOUT_OVERRIDE') {
      return false;
    }

    const caes = parseCAES(action.caes);
    if (!caes) return false;

    return isWithinConstraints(
      caes,
      actionSpace.mrcc.max_classification ?? 'C5',
      actionSpace.mrcc.max_scope ?? 'S5',
      actionSpace.mrcc.max_effect ?? 'E5'
    );
  });
};
