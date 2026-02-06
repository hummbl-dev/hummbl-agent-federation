/**
 * Learning Engine
 * Violation pattern analysis, feedback integration, and policy proposals
 */

import type {
  Violation,
  ViolationType,
  ActionSpace,
  ActionDefinition,
} from './types';
import { analyzePatterns, type ViolationPattern } from './violations';

// Learning State
export interface LearningState {
  version: string;
  updated_at: string;
  patterns: LearnedPattern[];
  feedback: FeedbackRecord[];
  weights: WeightAdjustments;
  proposals: PolicyProposal[];
  benchmarks: BenchmarkResult[];
}

export interface LearnedPattern {
  id: string;
  pattern_type: PatternType;
  action_id: string;
  violation_type: ViolationType;
  frequency: number;
  first_seen: string;
  last_seen: string;
  confidence: number;
  suggested_action: SuggestedAction;
}

export type PatternType =
  | 'RECURRING_VIOLATION'
  | 'POLICY_GAP'
  | 'AUTHORITY_MISMATCH'
  | 'SCOPE_CREEP'
  | 'RATE_ABUSE';

export type SuggestedAction =
  | 'UPDATE_POLICY'
  | 'ADJUST_THRESHOLD'
  | 'ADD_EXCEPTION'
  | 'ESCALATE_TO_OWNER'
  | 'NO_ACTION';

// Feedback from overrides and approvals
export interface FeedbackRecord {
  id: string;
  timestamp: string;
  action_id: string;
  feedback_type: FeedbackType;
  source: string;
  reason?: string;
  weight_adjustment: number;
}

export type FeedbackType =
  | 'OVERRIDE_APPROVED'
  | 'OVERRIDE_REJECTED'
  | 'ESCALATION_RESOLVED'
  | 'POLICY_UPDATED'
  | 'FALSE_POSITIVE'
  | 'TRUE_POSITIVE';

// Weight adjustments for actions
export interface WeightAdjustments {
  actions: Record<string, number>; // action_id -> weight (-1 to 1)
  types: Record<ViolationType, number>; // violation type -> weight
}

// Policy proposal
export interface PolicyProposal {
  id: string;
  created_at: string;
  status: ProposalStatus;
  proposal_type: ProposalType;
  action_id?: string;
  current_value?: string;
  proposed_value?: string;
  rationale: string;
  evidence: string[];
  confidence: number;
  gitops_branch?: string;
}

export type ProposalStatus =
  | 'DRAFT'
  | 'PENDING_REVIEW'
  | 'APPROVED'
  | 'REJECTED'
  | 'IMPLEMENTED';

export type ProposalType =
  | 'ADJUST_CLASSIFICATION'
  | 'ADJUST_AUTHORITY'
  | 'ADD_ACTION'
  | 'REMOVE_ACTION'
  | 'UPDATE_MRCC'
  | 'UPDATE_NCC'
  | 'ADD_EXCEPTION';

// Benchmark result
export interface BenchmarkResult {
  id: string;
  timestamp: string;
  benchmark_type: BenchmarkType;
  standard: string;
  score: number;
  gaps: BenchmarkGap[];
}

export type BenchmarkType = 'SOC2' | 'ISO27001' | 'NIST' | 'CUSTOM';

export interface BenchmarkGap {
  control_id: string;
  description: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH';
  remediation?: string;
}

// In-memory learning state
let learningState: LearningState = createInitialState();

function createInitialState(): LearningState {
  return {
    version: '1.0.0',
    updated_at: new Date().toISOString(),
    patterns: [],
    feedback: [],
    weights: {
      actions: {},
      types: {
        MRCC_EXCEEDED: 0,
        FORBIDDEN_ACTION: 0,
        AUTHORITY_MISSING: 0,
        SCOPE_EXCEEDED: 0,
        RATE_LIMIT: 0,
        EPOCH_VIOLATION: 0,
        POLICY_MISMATCH: 0,
      },
    },
    proposals: [],
    benchmarks: [],
  };
}

// Get current learning state
export const getLearningState = (): LearningState => {
  return { ...learningState };
};

// Update learning state
export const updateLearningState = (
  update: Partial<LearningState>
): LearningState => {
  learningState = {
    ...learningState,
    ...update,
    updated_at: new Date().toISOString(),
  };
  return learningState;
};

// Reset learning state
export const resetLearningState = (): void => {
  learningState = createInitialState();
};

// Learn from violation patterns
export const learnFromViolations = (): LearnedPattern[] => {
  const patterns = analyzePatterns();
  const learned: LearnedPattern[] = [];

  for (const pattern of patterns) {
    if (pattern.should_escalate) {
      const learnedPattern: LearnedPattern = {
        id: crypto.randomUUID(),
        pattern_type: determinePatternType(pattern),
        action_id: pattern.action_id,
        violation_type: pattern.violation_type,
        frequency: pattern.count,
        first_seen: pattern.first_occurrence,
        last_seen: pattern.last_occurrence,
        confidence: calculateConfidence(pattern),
        suggested_action: determineSuggestedAction(pattern),
      };
      learned.push(learnedPattern);
    }
  }

  // Update state
  learningState.patterns = [
    ...learningState.patterns.filter(
      (p) => !learned.some((l) => l.action_id === p.action_id && l.violation_type === p.violation_type)
    ),
    ...learned,
  ];
  learningState.updated_at = new Date().toISOString();

  return learned;
};

const determinePatternType = (pattern: ViolationPattern): PatternType => {
  switch (pattern.violation_type) {
    case 'MRCC_EXCEEDED':
    case 'SCOPE_EXCEEDED':
      return 'SCOPE_CREEP';
    case 'AUTHORITY_MISSING':
      return 'AUTHORITY_MISMATCH';
    case 'RATE_LIMIT':
      return 'RATE_ABUSE';
    case 'POLICY_MISMATCH':
      return 'POLICY_GAP';
    default:
      return 'RECURRING_VIOLATION';
  }
};

const calculateConfidence = (pattern: ViolationPattern): number => {
  // Higher frequency = higher confidence
  const freqScore = Math.min(pattern.count / 10, 1);

  // More recent = higher confidence
  const lastSeen = new Date(pattern.last_occurrence);
  const daysSince = (Date.now() - lastSeen.getTime()) / (1000 * 60 * 60 * 24);
  const recencyScore = Math.max(0, 1 - daysSince / 30);

  return Math.round((freqScore * 0.6 + recencyScore * 0.4) * 100) / 100;
};

const determineSuggestedAction = (pattern: ViolationPattern): SuggestedAction => {
  if (pattern.count >= 10) {
    return 'UPDATE_POLICY';
  }
  if (pattern.count >= 5) {
    return 'ESCALATE_TO_OWNER';
  }
  if (pattern.violation_type === 'RATE_LIMIT') {
    return 'ADJUST_THRESHOLD';
  }
  if (pattern.violation_type === 'AUTHORITY_MISSING') {
    return 'ADD_EXCEPTION';
  }
  return 'NO_ACTION';
};

// Record feedback
export const recordFeedback = (
  actionId: string,
  feedbackType: FeedbackType,
  source: string,
  reason?: string
): FeedbackRecord => {
  const weight = calculateWeightAdjustment(feedbackType);

  const feedback: FeedbackRecord = {
    id: crypto.randomUUID(),
    timestamp: new Date().toISOString(),
    action_id: actionId,
    feedback_type: feedbackType,
    source,
    reason,
    weight_adjustment: weight,
  };

  learningState.feedback.push(feedback);

  // Apply weight adjustment
  const currentWeight = learningState.weights.actions[actionId] ?? 0;
  learningState.weights.actions[actionId] = Math.max(
    -1,
    Math.min(1, currentWeight + weight)
  );

  learningState.updated_at = new Date().toISOString();

  return feedback;
};

const calculateWeightAdjustment = (feedbackType: FeedbackType): number => {
  switch (feedbackType) {
    case 'OVERRIDE_APPROVED':
      return 0.1; // Slightly increase tolerance
    case 'OVERRIDE_REJECTED':
      return -0.1; // Slightly decrease tolerance
    case 'FALSE_POSITIVE':
      return 0.2; // Increase tolerance more
    case 'TRUE_POSITIVE':
      return -0.2; // Decrease tolerance more
    case 'POLICY_UPDATED':
      return 0; // Neutral
    default:
      return 0;
  }
};

// Generate policy proposal
export const generateProposal = (
  pattern: LearnedPattern,
  actionSpace: ActionSpace
): PolicyProposal | null => {
  if (pattern.confidence < 0.5) {
    return null; // Not confident enough
  }

  const action = actionSpace.actions.find((a) => a.id === pattern.action_id);
  if (!action) {
    return null;
  }

  let proposal: PolicyProposal;

  switch (pattern.suggested_action) {
    case 'UPDATE_POLICY':
      proposal = createPolicyUpdateProposal(pattern, action);
      break;
    case 'ADJUST_THRESHOLD':
      proposal = createThresholdProposal(pattern, action);
      break;
    case 'ADD_EXCEPTION':
      proposal = createExceptionProposal(pattern, action);
      break;
    default:
      return null;
  }

  learningState.proposals.push(proposal);
  learningState.updated_at = new Date().toISOString();

  return proposal;
};

const createPolicyUpdateProposal = (
  pattern: LearnedPattern,
  action: ActionDefinition
): PolicyProposal => {
  return {
    id: crypto.randomUUID(),
    created_at: new Date().toISOString(),
    status: 'DRAFT',
    proposal_type: 'ADJUST_CLASSIFICATION',
    action_id: action.id,
    current_value: action.caes,
    proposed_value: adjustClassification(action.caes, pattern),
    rationale: `Action '${action.id}' has ${pattern.frequency} violations of type ${pattern.violation_type}. Adjusting classification to reduce friction.`,
    evidence: [
      `Violation frequency: ${pattern.frequency}`,
      `Pattern type: ${pattern.pattern_type}`,
      `First seen: ${pattern.first_seen}`,
      `Last seen: ${pattern.last_seen}`,
    ],
    confidence: pattern.confidence,
  };
};

const createThresholdProposal = (
  pattern: LearnedPattern,
  action: ActionDefinition
): PolicyProposal => {
  return {
    id: crypto.randomUUID(),
    created_at: new Date().toISOString(),
    status: 'DRAFT',
    proposal_type: 'UPDATE_MRCC',
    action_id: action.id,
    rationale: `Rate limit violations for '${action.id}' suggest threshold may be too restrictive.`,
    evidence: [
      `Violation count: ${pattern.frequency}`,
      `Pattern: ${pattern.pattern_type}`,
    ],
    confidence: pattern.confidence,
  };
};

const createExceptionProposal = (
  pattern: LearnedPattern,
  action: ActionDefinition
): PolicyProposal => {
  return {
    id: crypto.randomUUID(),
    created_at: new Date().toISOString(),
    status: 'DRAFT',
    proposal_type: 'ADD_EXCEPTION',
    action_id: action.id,
    rationale: `Authority violations for '${action.id}' may warrant an exception for certain actors.`,
    evidence: [
      `Violation count: ${pattern.frequency}`,
      `Pattern: ${pattern.pattern_type}`,
    ],
    confidence: pattern.confidence,
  };
};

const adjustClassification = (caes: string, pattern: LearnedPattern): string => {
  // Simple adjustment: reduce classification by 1 if possible
  const match = caes.match(/^C(\d)/);
  if (match) {
    const currentC = parseInt(match[1], 10);
    if (currentC > 0) {
      return caes.replace(/^C\d/, `C${currentC - 1}`);
    }
  }
  return caes;
};

// Benchmark against external standards
export const runBenchmark = (
  actionSpace: ActionSpace,
  benchmarkType: BenchmarkType
): BenchmarkResult => {
  const gaps = identifyGaps(actionSpace, benchmarkType);
  const score = calculateBenchmarkScore(gaps);

  const result: BenchmarkResult = {
    id: crypto.randomUUID(),
    timestamp: new Date().toISOString(),
    benchmark_type: benchmarkType,
    standard: getStandardName(benchmarkType),
    score,
    gaps,
  };

  learningState.benchmarks.push(result);
  learningState.updated_at = new Date().toISOString();

  return result;
};

const getStandardName = (type: BenchmarkType): string => {
  switch (type) {
    case 'SOC2':
      return 'SOC 2 Type II';
    case 'ISO27001':
      return 'ISO 27001:2022';
    case 'NIST':
      return 'NIST CSF 2.0';
    case 'CUSTOM':
      return 'Custom Benchmark';
  }
};

const identifyGaps = (
  actionSpace: ActionSpace,
  benchmarkType: BenchmarkType
): BenchmarkGap[] => {
  const gaps: BenchmarkGap[] = [];

  // Check for common compliance requirements
  if (!actionSpace.current_epoch?.monotonic_properties.includes('audit_cannot_disable')) {
    gaps.push({
      control_id: `${benchmarkType}-AUDIT-01`,
      description: 'Audit trail must be immutable and cannot be disabled',
      severity: 'HIGH',
      remediation: 'Add "audit_cannot_disable" to epoch monotonic properties',
    });
  }

  if (!actionSpace.mrcc.forbidden_actions?.includes('expand_autonomy')) {
    gaps.push({
      control_id: `${benchmarkType}-AUTH-01`,
      description: 'Autonomy expansion must be explicitly forbidden',
      severity: 'HIGH',
      remediation: 'Add "expand_autonomy" to MRCC forbidden_actions',
    });
  }

  if (!actionSpace.mrcc.rate_limits) {
    gaps.push({
      control_id: `${benchmarkType}-RATE-01`,
      description: 'Rate limits must be defined to prevent abuse',
      severity: 'MEDIUM',
      remediation: 'Define rate_limits in MRCC constraints',
    });
  }

  return gaps;
};

const calculateBenchmarkScore = (gaps: BenchmarkGap[]): number => {
  if (gaps.length === 0) return 100;

  let deductions = 0;
  for (const gap of gaps) {
    switch (gap.severity) {
      case 'HIGH':
        deductions += 20;
        break;
      case 'MEDIUM':
        deductions += 10;
        break;
      case 'LOW':
        deductions += 5;
        break;
    }
  }

  return Math.max(0, 100 - deductions);
};

// Get proposals by status
export const getProposalsByStatus = (status: ProposalStatus): PolicyProposal[] => {
  return learningState.proposals.filter((p) => p.status === status);
};

// Update proposal status
export const updateProposalStatus = (
  proposalId: string,
  status: ProposalStatus
): boolean => {
  const proposal = learningState.proposals.find((p) => p.id === proposalId);
  if (!proposal) return false;

  proposal.status = status;
  learningState.updated_at = new Date().toISOString();
  return true;
};

// Export learning state
export const exportLearningState = (): string => {
  return JSON.stringify(learningState, null, 2);
};

// Import learning state
export const importLearningState = (json: string): boolean => {
  try {
    const imported = JSON.parse(json) as LearningState;
    learningState = imported;
    return true;
  } catch {
    return false;
  }
};
