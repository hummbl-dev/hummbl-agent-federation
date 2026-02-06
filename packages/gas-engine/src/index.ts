/**
 * HUMMBL G.A.S. Engine
 * Policy validation, violation capture, and cross-domain enforcement
 */

// Types
export * from './types';

// CAES utilities
export {
  parseCAES,
  getLevel,
  compareCAES,
  isWithinConstraints,
  formatCAES,
  getRiskDescription,
  getAuthorityDescription,
} from './caes';

// Validator
export {
  validateAction,
  validateActions,
  getAllowedActions,
  type ValidatorContext,
} from './validator';

// Violations
export {
  captureViolation,
  getViolation,
  getAllViolations,
  getViolationsByType,
  getViolationsBySeverity,
  getViolationsByAction,
  getUnresolvedViolations,
  resolveViolation,
  getViolationStats,
  analyzePatterns,
  getViolationsInRange,
  clearViolations,
  exportViolations,
  importViolations,
  type ViolationStats,
  type ViolationPattern,
} from './violations';

// Enforcer
export {
  enforceAction,
  enforceActions,
  enforceCrossDomain,
  recordEnforcementResult,
  getEnforcementSummary,
  resetEnforcementCounts,
  type EnforcementOutcome,
  type EnforcementResult,
  type EnforcerConfig,
  type DomainPolicy,
  type EnforcementSummary,
} from './enforcer';

// Audit
export {
  storeAuditEvent,
  getAuditEvent,
  getAllAuditEvents,
  getAuditEventsInRange,
  getAuditEventsByActor,
  getAuditEventsByAction,
  getAuditEventsByOutcome,
  clearAuditTrail,
  exportAuditTrail,
  importAuditTrail,
  calculateComplianceScore,
  generateComplianceReport,
  formatReportAsMarkdown,
  type ComplianceScore,
  type ComplianceReport,
} from './audit';

// Learning
export {
  getLearningState,
  updateLearningState,
  resetLearningState,
  learnFromViolations,
  recordFeedback,
  generateProposal,
  runBenchmark,
  getProposalsByStatus,
  updateProposalStatus,
  exportLearningState,
  importLearningState,
  type LearningState,
  type LearnedPattern,
  type PatternType,
  type SuggestedAction,
  type FeedbackRecord,
  type FeedbackType,
  type WeightAdjustments,
  type PolicyProposal,
  type ProposalStatus,
  type ProposalType,
  type BenchmarkResult,
  type BenchmarkType,
  type BenchmarkGap,
} from './learning';

// Checkpoint
export {
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
  autoRollbackIfNeeded,
  type Checkpoint,
  type CheckpointType,
  type CheckpointState,
  type RollbackResult,
  type ValidationResult,
  type ModificationGuard,
  type GuardType,
  type GuardAction,
  type GuardCheckResult,
  type HealthCheckResult,
  type HealthCheck,
} from './checkpoint';
