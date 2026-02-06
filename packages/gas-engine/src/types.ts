/**
 * HUMMBL G.A.S. Engine Core Types
 * CAES Classification Framework
 */

// Classification Levels (Risk)
export type ClassificationLevel = 'C0' | 'C1' | 'C2' | 'C3' | 'C4' | 'C5';

// Authority Levels (Approval)
export type AuthorityLevel =
  | 'A0-SELF'
  | 'A1-NOTIFY'
  | 'A2-REVIEW'
  | 'A3-APPROVE'
  | 'A4-MULTI'
  | 'A5-EMERGENCY';

// Effect Levels (Reversibility)
export type EffectLevel =
  | 'E0-PURE'
  | 'E1-REVERT'
  | 'E2-CHECKPOINT'
  | 'E3-COMPENSATE'
  | 'E4-DEFERRED'
  | 'E5-PERMANENT';

// Scope Levels (Blast Radius)
export type ScopeLevel =
  | 'S0-SELF'
  | 'S1-LOCAL'
  | 'S2-DOMAIN'
  | 'S3-CROSS'
  | 'S4-SYSTEM'
  | 'S5-EXTERNAL';

// Action Status
export type ActionStatus =
  | 'ALLOWED'
  | 'RESTRICTED'
  | 'FORBIDDEN'
  | 'FORBIDDEN_WITHOUT_OVERRIDE';

// CAES Code (combined classification)
export interface CAESCode {
  classification: ClassificationLevel;
  authority: AuthorityLevel;
  effect: EffectLevel;
  scope: ScopeLevel;
}

// Action Definition
export interface ActionDefinition {
  id: string;
  caes: string; // e.g., "C2-A1-E2-S2"
  description: string;
  authority: AuthorityLevel;
  effect?: string;
  requires?: string[];
  triggers?: string[];
  gitops?: boolean;
  ci_check?: boolean;
  cost_check?: boolean;
  status: ActionStatus;
  timeout?: string;
  escalates_to?: string;
}

// Constraint Set (MRCC/NCC)
export interface ConstraintSet {
  description?: string;
  max_classification?: ClassificationLevel;
  default_classification?: ClassificationLevel;
  max_scope?: ScopeLevel;
  default_scope?: ScopeLevel;
  max_effect?: EffectLevel;
  default_effect?: EffectLevel;
  forbidden_actions?: string[];
  preferred_actions?: string[];
  discouraged_actions?: string[];
  rate_limits?: Record<string, number>;
}

// Epoch Definition
export interface Epoch {
  id: string;
  started: string;
  policy_hash: string;
  mrcc_hash?: string;
  monotonic_properties: string[];
}

// Full Action Space
export interface ActionSpace {
  version: string;
  description?: string;
  actions: ActionDefinition[];
  mrcc: ConstraintSet;
  ncc: ConstraintSet;
  current_epoch?: Epoch;
  meta?: Record<string, unknown>;
}

// Violation Record
export interface Violation {
  id: string;
  timestamp: string;
  action_id: string;
  caes: string;
  violation_type: ViolationType;
  severity: ViolationSeverity;
  context: ViolationContext;
  resolution?: ViolationResolution;
}

export type ViolationType =
  | 'MRCC_EXCEEDED'
  | 'FORBIDDEN_ACTION'
  | 'AUTHORITY_MISSING'
  | 'SCOPE_EXCEEDED'
  | 'RATE_LIMIT'
  | 'EPOCH_VIOLATION'
  | 'POLICY_MISMATCH';

export type ViolationSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface ViolationContext {
  actor: string;
  target?: string;
  requested_caes?: string;
  allowed_caes?: string;
  policy_ref?: string;
  epoch_id?: string;
}

export interface ViolationResolution {
  resolved_at: string;
  resolved_by: string;
  resolution_type: 'APPROVED' | 'BLOCKED' | 'ESCALATED' | 'EXCEPTION';
  notes?: string;
}

// Policy Validation Result
export interface ValidationResult {
  valid: boolean;
  action_id: string;
  checks: PolicyCheck[];
  violations: Violation[];
  recommendations?: string[];
}

export interface PolicyCheck {
  check: string;
  ok: boolean;
  reason?: string;
}

// Audit Event
export interface AuditEvent {
  id: string;
  timestamp: string;
  action_id: string;
  caes: string;
  actor: string;
  target?: string;
  outcome: 'ALLOWED' | 'BLOCKED' | 'ESCALATED';
  policy_refs: string[];
  base120_refs?: string[];
  provenance: {
    input_hash?: string;
    output_hash?: string;
    checkpoint_id?: string;
  };
  duration_ms?: number;
}
