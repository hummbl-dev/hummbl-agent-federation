/**
 * Violations Tests
 */

import { describe, it, expect, beforeEach } from 'vitest';
import {
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
  clearViolations,
  exportViolations,
  importViolations,
} from '../src/violations';
import type { Violation } from '../src/types';

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

describe('captureViolation', () => {
  beforeEach(() => {
    clearViolations();
  });

  it('captures and stores a violation', () => {
    const violation = createTestViolation();
    captureViolation(violation);

    const retrieved = getViolation(violation.id);
    expect(retrieved).toBeDefined();
    expect(retrieved?.id).toBe(violation.id);
  });

  it('captures multiple violations', () => {
    captureViolation(createTestViolation());
    captureViolation(createTestViolation());
    captureViolation(createTestViolation());

    expect(getAllViolations()).toHaveLength(3);
  });
});

describe('getViolationsByType', () => {
  beforeEach(() => {
    clearViolations();
  });

  it('filters by violation type', () => {
    captureViolation(createTestViolation({ violation_type: 'MRCC_EXCEEDED' }));
    captureViolation(createTestViolation({ violation_type: 'FORBIDDEN_ACTION' }));
    captureViolation(createTestViolation({ violation_type: 'MRCC_EXCEEDED' }));

    const mrccViolations = getViolationsByType('MRCC_EXCEEDED');
    expect(mrccViolations).toHaveLength(2);

    const forbiddenViolations = getViolationsByType('FORBIDDEN_ACTION');
    expect(forbiddenViolations).toHaveLength(1);
  });
});

describe('getViolationsBySeverity', () => {
  beforeEach(() => {
    clearViolations();
  });

  it('filters by severity', () => {
    captureViolation(createTestViolation({ severity: 'HIGH' }));
    captureViolation(createTestViolation({ severity: 'CRITICAL' }));
    captureViolation(createTestViolation({ severity: 'LOW' }));

    expect(getViolationsBySeverity('HIGH')).toHaveLength(1);
    expect(getViolationsBySeverity('CRITICAL')).toHaveLength(1);
    expect(getViolationsBySeverity('LOW')).toHaveLength(1);
  });
});

describe('getViolationsByAction', () => {
  beforeEach(() => {
    clearViolations();
  });

  it('filters by action_id', () => {
    captureViolation(createTestViolation({ action_id: 'expand_autonomy' }));
    captureViolation(createTestViolation({ action_id: 'expand_autonomy' }));
    captureViolation(createTestViolation({ action_id: 'block_action' }));

    expect(getViolationsByAction('expand_autonomy')).toHaveLength(2);
    expect(getViolationsByAction('block_action')).toHaveLength(1);
  });
});

describe('resolveViolation', () => {
  beforeEach(() => {
    clearViolations();
  });

  it('marks violation as resolved', () => {
    const violation = createTestViolation();
    captureViolation(violation);

    resolveViolation(violation.id, {
      resolved_at: new Date().toISOString(),
      resolved_by: 'admin',
      resolution_type: 'APPROVED',
      notes: 'Exception granted',
    });

    const resolved = getViolation(violation.id);
    expect(resolved?.resolution).toBeDefined();
    expect(resolved?.resolution?.resolution_type).toBe('APPROVED');
  });

  it('unresolved violations filter excludes resolved', () => {
    const v1 = createTestViolation();
    const v2 = createTestViolation();
    captureViolation(v1);
    captureViolation(v2);

    resolveViolation(v1.id, {
      resolved_at: new Date().toISOString(),
      resolved_by: 'admin',
      resolution_type: 'BLOCKED',
    });

    const unresolved = getUnresolvedViolations();
    expect(unresolved).toHaveLength(1);
    expect(unresolved[0].id).toBe(v2.id);
  });
});

describe('getViolationStats', () => {
  beforeEach(() => {
    clearViolations();
  });

  it('computes violation statistics', () => {
    captureViolation(createTestViolation({ severity: 'HIGH', violation_type: 'MRCC_EXCEEDED' }));
    captureViolation(createTestViolation({ severity: 'CRITICAL', violation_type: 'FORBIDDEN_ACTION' }));
    captureViolation(createTestViolation({ severity: 'HIGH', violation_type: 'MRCC_EXCEEDED' }));

    const stats = getViolationStats();
    expect(stats.total).toBe(3);
    expect(stats.bySeverity.HIGH).toBe(2);
    expect(stats.bySeverity.CRITICAL).toBe(1);
    expect(stats.byType.MRCC_EXCEEDED).toBe(2);
    expect(stats.byType.FORBIDDEN_ACTION).toBe(1);
  });
});

describe('analyzePatterns', () => {
  beforeEach(() => {
    clearViolations();
  });

  it('detects recurring patterns', () => {
    // Create pattern: same action violated 3+ times
    for (let i = 0; i < 5; i++) {
      captureViolation(createTestViolation({
        action_id: 'expand_autonomy',
        violation_type: 'FORBIDDEN_ACTION',
      }));
    }

    const patterns = analyzePatterns();
    expect(patterns.length).toBeGreaterThan(0);
    expect(patterns[0].action_id).toBe('expand_autonomy');
    expect(patterns[0].count).toBe(5);
    expect(patterns[0].should_escalate).toBe(true);
  });
});

describe('export/import', () => {
  beforeEach(() => {
    clearViolations();
  });

  it('exports and imports violations as JSONL', () => {
    captureViolation(createTestViolation({ action_id: 'action1' }));
    captureViolation(createTestViolation({ action_id: 'action2' }));

    const exported = exportViolations();
    expect(typeof exported).toBe('string');
    const lines = exported.split('\n').filter(l => l.trim());
    expect(lines).toHaveLength(2);

    clearViolations();
    expect(getAllViolations()).toHaveLength(0);

    const importedCount = importViolations(exported);
    expect(importedCount).toBe(2);
    expect(getAllViolations()).toHaveLength(2);
  });
});
