/**
 * Audit Engine
 * Trail storage, compliance scoring, and report generation
 */

import type { AuditEvent, Violation, ActionSpace } from './types';
import { getViolationStats, getAllViolations } from './violations';
import { getEnforcementSummary } from './enforcer';

// Audit trail storage (in-memory; production would use persistent storage)
const auditTrail: Map<string, AuditEvent> = new Map();

// Store an audit event
export const storeAuditEvent = (event: AuditEvent): string => {
  auditTrail.set(event.id, event);
  return event.id;
};

// Get audit event by ID
export const getAuditEvent = (id: string): AuditEvent | undefined => {
  return auditTrail.get(id);
};

// Get all audit events
export const getAllAuditEvents = (): AuditEvent[] => {
  return Array.from(auditTrail.values());
};

// Get audit events in time range
export const getAuditEventsInRange = (
  startTime: Date,
  endTime: Date
): AuditEvent[] => {
  return getAllAuditEvents().filter((e) => {
    const ts = new Date(e.timestamp);
    return ts >= startTime && ts <= endTime;
  });
};

// Get audit events by actor
export const getAuditEventsByActor = (actor: string): AuditEvent[] => {
  return getAllAuditEvents().filter((e) => e.actor === actor);
};

// Get audit events by action
export const getAuditEventsByAction = (actionId: string): AuditEvent[] => {
  return getAllAuditEvents().filter((e) => e.action_id === actionId);
};

// Get audit events by outcome
export const getAuditEventsByOutcome = (
  outcome: AuditEvent['outcome']
): AuditEvent[] => {
  return getAllAuditEvents().filter((e) => e.outcome === outcome);
};

// Clear audit trail (for testing)
export const clearAuditTrail = (): void => {
  auditTrail.clear();
};

// Export audit trail to JSONL
export const exportAuditTrail = (): string => {
  return getAllAuditEvents()
    .map((e) => JSON.stringify(e))
    .join('\n');
};

// Import audit trail from JSONL
export const importAuditTrail = (jsonl: string): number => {
  const lines = jsonl.split('\n').filter((l) => l.trim());
  let imported = 0;
  for (const line of lines) {
    try {
      const event = JSON.parse(line) as AuditEvent;
      auditTrail.set(event.id, event);
      imported++;
    } catch {
      // Skip invalid lines
    }
  }
  return imported;
};

// Compliance Score Calculation
export interface ComplianceScore {
  overall: number; // 0-100
  breakdown: {
    policy_adherence: number;
    violation_rate: number;
    resolution_rate: number;
    audit_coverage: number;
  };
  grade: 'A' | 'B' | 'C' | 'D' | 'F';
  recommendations: string[];
}

export const calculateComplianceScore = (
  actionSpace: ActionSpace
): ComplianceScore => {
  const violationStats = getViolationStats();
  const enforcementSummary = getEnforcementSummary();
  const allViolations = getAllViolations();
  const allAuditEvents = getAllAuditEvents();

  // Calculate individual scores
  const policyAdherence = calculatePolicyAdherence(enforcementSummary);
  const violationRate = calculateViolationRate(violationStats, enforcementSummary);
  const resolutionRate = calculateResolutionRate(allViolations);
  const auditCoverage = calculateAuditCoverage(allAuditEvents, enforcementSummary);

  // Weighted overall score
  const overall = Math.round(
    policyAdherence * 0.35 +
    violationRate * 0.25 +
    resolutionRate * 0.20 +
    auditCoverage * 0.20
  );

  // Determine grade
  const grade = getGrade(overall);

  // Generate recommendations
  const recommendations = generateRecommendations({
    policyAdherence,
    violationRate,
    resolutionRate,
    auditCoverage,
  });

  return {
    overall,
    breakdown: {
      policy_adherence: policyAdherence,
      violation_rate: violationRate,
      resolution_rate: resolutionRate,
      audit_coverage: auditCoverage,
    },
    grade,
    recommendations,
  };
};

const calculatePolicyAdherence = (
  enforcement: ReturnType<typeof getEnforcementSummary>
): number => {
  if (enforcement.total_enforced === 0) return 100;
  return Math.round(
    ((enforcement.allowed + enforcement.escalated) / enforcement.total_enforced) * 100
  );
};

const calculateViolationRate = (
  violations: ReturnType<typeof getViolationStats>,
  enforcement: ReturnType<typeof getEnforcementSummary>
): number => {
  if (enforcement.total_enforced === 0) return 100;
  const rate = violations.total / enforcement.total_enforced;
  return Math.round(Math.max(0, 100 - rate * 100));
};

const calculateResolutionRate = (violations: Violation[]): number => {
  if (violations.length === 0) return 100;
  const resolved = violations.filter((v) => v.resolution).length;
  return Math.round((resolved / violations.length) * 100);
};

const calculateAuditCoverage = (
  events: AuditEvent[],
  enforcement: ReturnType<typeof getEnforcementSummary>
): number => {
  if (enforcement.total_enforced === 0) return 100;
  // Audit coverage = percentage of enforced actions with audit events
  const coverage = events.length / enforcement.total_enforced;
  return Math.round(Math.min(100, coverage * 100));
};

const getGrade = (score: number): ComplianceScore['grade'] => {
  if (score >= 90) return 'A';
  if (score >= 80) return 'B';
  if (score >= 70) return 'C';
  if (score >= 60) return 'D';
  return 'F';
};

const generateRecommendations = (breakdown: ComplianceScore['breakdown']): string[] => {
  const recommendations: string[] = [];

  if (breakdown.policy_adherence < 80) {
    recommendations.push('Review and update policies to reduce blocked actions');
  }
  if (breakdown.violation_rate < 80) {
    recommendations.push('Investigate recurring violations and address root causes');
  }
  if (breakdown.resolution_rate < 80) {
    recommendations.push('Resolve outstanding violations to improve compliance');
  }
  if (breakdown.audit_coverage < 80) {
    recommendations.push('Ensure all actions have corresponding audit events');
  }

  if (recommendations.length === 0) {
    recommendations.push('Maintain current compliance practices');
  }

  return recommendations;
};

// Report Generation
export interface ComplianceReport {
  generated_at: string;
  period: {
    start: string;
    end: string;
  };
  score: ComplianceScore;
  summary: {
    total_actions: number;
    allowed: number;
    blocked: number;
    escalated: number;
    violations: number;
    unresolved_violations: number;
  };
  top_violations: Array<{
    action_id: string;
    count: number;
    type: string;
  }>;
  audit_trail_hash: string;
}

export const generateComplianceReport = (
  actionSpace: ActionSpace,
  startTime: Date,
  endTime: Date
): ComplianceReport => {
  const score = calculateComplianceScore(actionSpace);
  const enforcement = getEnforcementSummary();
  const violationStats = getViolationStats();
  const violations = getAllViolations();

  // Get top violations by action
  const violationCounts = new Map<string, { count: number; type: string }>();
  for (const v of violations) {
    const key = v.action_id;
    const existing = violationCounts.get(key);
    if (existing) {
      existing.count++;
    } else {
      violationCounts.set(key, { count: 1, type: v.violation_type });
    }
  }

  const topViolations = Array.from(violationCounts.entries())
    .map(([action_id, { count, type }]) => ({ action_id, count, type }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);

  // Calculate audit trail hash (simplified)
  const trailContent = exportAuditTrail();
  const hash = `sha256:${hashCode(trailContent).toString(16)}`;

  return {
    generated_at: new Date().toISOString(),
    period: {
      start: startTime.toISOString(),
      end: endTime.toISOString(),
    },
    score,
    summary: {
      total_actions: enforcement.total_enforced,
      allowed: enforcement.allowed,
      blocked: enforcement.blocked,
      escalated: enforcement.escalated,
      violations: violationStats.total,
      unresolved_violations: violationStats.unresolved,
    },
    top_violations: topViolations,
    audit_trail_hash: hash,
  };
};

// Simple hash function for demo (production would use crypto)
const hashCode = (str: string): number => {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return Math.abs(hash);
};

// Format report as markdown
export const formatReportAsMarkdown = (report: ComplianceReport): string => {
  const lines: string[] = [
    '# G.A.S. Compliance Report',
    '',
    `**Generated:** ${report.generated_at}`,
    `**Period:** ${report.period.start} to ${report.period.end}`,
    '',
    '## Compliance Score',
    '',
    `**Overall:** ${report.score.overall}/100 (Grade: ${report.score.grade})`,
    '',
    '| Metric | Score |',
    '|--------|-------|',
    `| Policy Adherence | ${report.score.breakdown.policy_adherence}% |`,
    `| Violation Rate | ${report.score.breakdown.violation_rate}% |`,
    `| Resolution Rate | ${report.score.breakdown.resolution_rate}% |`,
    `| Audit Coverage | ${report.score.breakdown.audit_coverage}% |`,
    '',
    '## Summary',
    '',
    `- **Total Actions:** ${report.summary.total_actions}`,
    `- **Allowed:** ${report.summary.allowed}`,
    `- **Blocked:** ${report.summary.blocked}`,
    `- **Escalated:** ${report.summary.escalated}`,
    `- **Violations:** ${report.summary.violations}`,
    `- **Unresolved:** ${report.summary.unresolved_violations}`,
    '',
  ];

  if (report.top_violations.length > 0) {
    lines.push('## Top Violations', '');
    lines.push('| Action | Count | Type |');
    lines.push('|--------|-------|------|');
    for (const v of report.top_violations) {
      lines.push(`| ${v.action_id} | ${v.count} | ${v.type} |`);
    }
    lines.push('');
  }

  if (report.score.recommendations.length > 0) {
    lines.push('## Recommendations', '');
    for (const rec of report.score.recommendations) {
      lines.push(`- ${rec}`);
    }
    lines.push('');
  }

  lines.push('---', '');
  lines.push(`Audit Trail Hash: \`${report.audit_trail_hash}\``);

  return lines.join('\n');
};
