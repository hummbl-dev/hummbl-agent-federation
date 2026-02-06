/**
 * Violation Capture and Storage
 * Tracks policy violations for learning and escalation
 */

import type {
  Violation,
  ViolationType,
  ViolationSeverity,
  ViolationResolution,
} from './types';

// In-memory violation store (production would use persistent storage)
const violations: Map<string, Violation> = new Map();

// Capture a new violation
export const captureViolation = (violation: Violation): string => {
  violations.set(violation.id, violation);
  return violation.id;
};

// Get violation by ID
export const getViolation = (id: string): Violation | undefined => {
  return violations.get(id);
};

// Get all violations
export const getAllViolations = (): Violation[] => {
  return Array.from(violations.values());
};

// Get violations by type
export const getViolationsByType = (type: ViolationType): Violation[] => {
  return getAllViolations().filter((v) => v.violation_type === type);
};

// Get violations by severity
export const getViolationsBySeverity = (severity: ViolationSeverity): Violation[] => {
  return getAllViolations().filter((v) => v.severity === severity);
};

// Get violations by action
export const getViolationsByAction = (actionId: string): Violation[] => {
  return getAllViolations().filter((v) => v.action_id === actionId);
};

// Get unresolved violations
export const getUnresolvedViolations = (): Violation[] => {
  return getAllViolations().filter((v) => !v.resolution);
};

// Resolve a violation
export const resolveViolation = (
  id: string,
  resolution: ViolationResolution
): boolean => {
  const violation = violations.get(id);
  if (!violation) return false;

  violation.resolution = resolution;
  violations.set(id, violation);
  return true;
};

// Get violation statistics
export const getViolationStats = (): ViolationStats => {
  const all = getAllViolations();
  const unresolved = getUnresolvedViolations();

  const byType: Record<ViolationType, number> = {
    MRCC_EXCEEDED: 0,
    FORBIDDEN_ACTION: 0,
    AUTHORITY_MISSING: 0,
    SCOPE_EXCEEDED: 0,
    RATE_LIMIT: 0,
    EPOCH_VIOLATION: 0,
    POLICY_MISMATCH: 0,
  };

  const bySeverity: Record<ViolationSeverity, number> = {
    LOW: 0,
    MEDIUM: 0,
    HIGH: 0,
    CRITICAL: 0,
  };

  for (const v of all) {
    byType[v.violation_type]++;
    bySeverity[v.severity]++;
  }

  return {
    total: all.length,
    unresolved: unresolved.length,
    byType,
    bySeverity,
  };
};

export interface ViolationStats {
  total: number;
  unresolved: number;
  byType: Record<ViolationType, number>;
  bySeverity: Record<ViolationSeverity, number>;
}

// Analyze violation patterns for learning
export const analyzePatterns = (): ViolationPattern[] => {
  const all = getAllViolations();
  const patterns: Map<string, ViolationPattern> = new Map();

  for (const v of all) {
    const key = `${v.action_id}:${v.violation_type}`;
    const existing = patterns.get(key);

    if (existing) {
      existing.count++;
      existing.last_occurrence = v.timestamp;
    } else {
      patterns.set(key, {
        action_id: v.action_id,
        violation_type: v.violation_type,
        count: 1,
        first_occurrence: v.timestamp,
        last_occurrence: v.timestamp,
        should_escalate: false,
      });
    }
  }

  // Mark patterns that should escalate (frequency >= 3)
  for (const pattern of patterns.values()) {
    if (pattern.count >= 3) {
      pattern.should_escalate = true;
    }
  }

  return Array.from(patterns.values()).sort((a, b) => b.count - a.count);
};

export interface ViolationPattern {
  action_id: string;
  violation_type: ViolationType;
  count: number;
  first_occurrence: string;
  last_occurrence: string;
  should_escalate: boolean;
}

// Get violations within time range
export const getViolationsInRange = (
  startTime: Date,
  endTime: Date
): Violation[] => {
  return getAllViolations().filter((v) => {
    const ts = new Date(v.timestamp);
    return ts >= startTime && ts <= endTime;
  });
};

// Clear violations (for testing)
export const clearViolations = (): void => {
  violations.clear();
};

// Export violations to JSONL format
export const exportViolations = (): string => {
  return getAllViolations()
    .map((v) => JSON.stringify(v))
    .join('\n');
};

// Import violations from JSONL format
export const importViolations = (jsonl: string): number => {
  const lines = jsonl.split('\n').filter((line) => line.trim());
  let imported = 0;

  for (const line of lines) {
    try {
      const violation = JSON.parse(line) as Violation;
      violations.set(violation.id, violation);
      imported++;
    } catch {
      // Skip invalid lines
    }
  }

  return imported;
};
