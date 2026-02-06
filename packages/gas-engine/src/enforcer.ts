/**
 * Cross-Domain Policy Enforcer
 * Enforces policies across multiple governance domains
 */

import type {
  ActionSpace,
  ActionDefinition,
  AuditEvent,
  Violation,
} from './types';
import { validateAction, type ValidatorContext } from './validator';
import { captureViolation } from './violations';
import { parseCAES, getLevel } from './caes';

export type EnforcementOutcome = 'ALLOWED' | 'BLOCKED' | 'ESCALATED';

export interface EnforcementResult {
  action_id: string;
  outcome: EnforcementOutcome;
  audit_event: AuditEvent;
  violations: Violation[];
  requires_approval?: string[];
  checkpoint_required?: boolean;
}

export interface EnforcerConfig {
  actionSpace: ActionSpace;
  policyRefs: string[];
  base120Refs?: string[];
}

// Enforce an action and produce audit trail
export const enforceAction = (
  actionId: string,
  config: EnforcerConfig,
  context: ValidatorContext
): EnforcementResult => {
  const { actionSpace, policyRefs, base120Refs } = config;

  // Validate action
  const validation = validateAction(actionId, actionSpace, context);

  // Capture any violations
  for (const violation of validation.violations) {
    captureViolation(violation);
  }

  // Determine outcome
  let outcome: EnforcementOutcome;
  const requiresApproval: string[] = [];
  let checkpointRequired = false;

  if (!validation.valid) {
    // Check if escalation is possible
    const action = actionSpace.actions.find((a) => a.id === actionId);
    if (action?.escalates_to) {
      outcome = 'ESCALATED';
    } else {
      outcome = 'BLOCKED';
    }
  } else {
    const action = actionSpace.actions.find((a) => a.id === actionId);
    if (action) {
      // Check if approval is required
      if (action.status === 'RESTRICTED') {
        requiresApproval.push(action.authority);
        outcome = 'ESCALATED';
      } else {
        outcome = 'ALLOWED';
      }

      // Check if checkpoint is required (C >= 2)
      const caes = parseCAES(action.caes);
      if (caes && getLevel(caes.classification) >= 2) {
        checkpointRequired = true;
      }
    } else {
      outcome = 'BLOCKED';
    }
  }

  // Create audit event
  const auditEvent = createAuditEvent(
    actionId,
    actionSpace.actions.find((a) => a.id === actionId),
    outcome,
    context,
    policyRefs,
    base120Refs
  );

  return {
    action_id: actionId,
    outcome,
    audit_event: auditEvent,
    violations: validation.violations,
    requires_approval: requiresApproval.length > 0 ? requiresApproval : undefined,
    checkpoint_required: checkpointRequired,
  };
};

// Create audit event
const createAuditEvent = (
  actionId: string,
  action: ActionDefinition | undefined,
  outcome: EnforcementOutcome,
  context: ValidatorContext,
  policyRefs: string[],
  base120Refs?: string[]
): AuditEvent => {
  return {
    id: crypto.randomUUID(),
    timestamp: new Date().toISOString(),
    action_id: actionId,
    caes: action?.caes ?? 'UNKNOWN',
    actor: context.actor,
    outcome,
    policy_refs: policyRefs,
    base120_refs: base120Refs,
    provenance: {},
  };
};

// Batch enforce multiple actions
export const enforceActions = (
  actionIds: string[],
  config: EnforcerConfig,
  context: ValidatorContext
): EnforcementResult[] => {
  return actionIds.map((id) => enforceAction(id, config, context));
};

// Cross-domain policy check
export interface DomainPolicy {
  domain: string;
  actionSpace: ActionSpace;
  priority: number;
}

export const enforceCrossDomain = (
  actionId: string,
  domains: DomainPolicy[],
  context: ValidatorContext
): EnforcementResult => {
  // Sort by priority (higher = more restrictive = checked first)
  const sorted = [...domains].sort((a, b) => b.priority - a.priority);

  for (const domain of sorted) {
    const result = enforceAction(
      actionId,
      {
        actionSpace: domain.actionSpace,
        policyRefs: [`${domain.domain}:policy`],
      },
      context
    );

    // If blocked by any domain, return immediately
    if (result.outcome === 'BLOCKED') {
      return result;
    }

    // If escalated, continue checking but note the escalation
    if (result.outcome === 'ESCALATED') {
      // Check remaining domains
      const remaining = sorted.slice(sorted.indexOf(domain) + 1);
      for (const rem of remaining) {
        const remResult = enforceAction(
          actionId,
          {
            actionSpace: rem.actionSpace,
            policyRefs: [`${rem.domain}:policy`],
          },
          context
        );
        if (remResult.outcome === 'BLOCKED') {
          return remResult;
        }
      }
      return result;
    }
  }

  // All domains allow the action
  return enforceAction(
    actionId,
    {
      actionSpace: sorted[0]?.actionSpace ?? { version: '0', actions: [], mrcc: {}, ncc: {} },
      policyRefs: sorted.map((d) => `${d.domain}:policy`),
    },
    context
  );
};

// Get enforcement summary
export interface EnforcementSummary {
  total_enforced: number;
  allowed: number;
  blocked: number;
  escalated: number;
  violations_captured: number;
}

const enforcementCounts = {
  total: 0,
  allowed: 0,
  blocked: 0,
  escalated: 0,
  violations: 0,
};

export const recordEnforcementResult = (result: EnforcementResult): void => {
  enforcementCounts.total++;
  switch (result.outcome) {
    case 'ALLOWED':
      enforcementCounts.allowed++;
      break;
    case 'BLOCKED':
      enforcementCounts.blocked++;
      break;
    case 'ESCALATED':
      enforcementCounts.escalated++;
      break;
  }
  enforcementCounts.violations += result.violations.length;
};

export const getEnforcementSummary = (): EnforcementSummary => {
  return {
    total_enforced: enforcementCounts.total,
    allowed: enforcementCounts.allowed,
    blocked: enforcementCounts.blocked,
    escalated: enforcementCounts.escalated,
    violations_captured: enforcementCounts.violations,
  };
};

export const resetEnforcementCounts = (): void => {
  enforcementCounts.total = 0;
  enforcementCounts.allowed = 0;
  enforcementCounts.blocked = 0;
  enforcementCounts.escalated = 0;
  enforcementCounts.violations = 0;
};
