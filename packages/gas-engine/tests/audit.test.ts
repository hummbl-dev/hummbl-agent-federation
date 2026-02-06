/**
 * Audit Engine Tests
 */

import { describe, it, expect, beforeEach } from 'vitest';
import {
  storeAuditEvent,
  getAuditEvent,
  getAllAuditEvents,
  getAuditEventsByActor,
  getAuditEventsByOutcome,
  clearAuditTrail,
  exportAuditTrail,
  importAuditTrail,
  calculateComplianceScore,
  generateComplianceReport,
  formatReportAsMarkdown,
} from '../src/audit';
import { clearViolations } from '../src/violations';
import { resetEnforcementCounts } from '../src/enforcer';
import type { AuditEvent, ActionSpace } from '../src/types';

const testActionSpace: ActionSpace = {
  version: '1.0.0',
  actions: [
    {
      id: 'read_policy',
      caes: 'C0-A0-E0-S1',
      description: 'Read a policy',
      authority: 'A0-SELF',
      status: 'ALLOWED',
    },
  ],
  mrcc: { max_classification: 'C3', max_scope: 'S3', max_effect: 'E3' },
  ncc: { default_classification: 'C2' },
};

const createTestEvent = (overrides: Partial<AuditEvent> = {}): AuditEvent => ({
  id: crypto.randomUUID(),
  timestamp: new Date().toISOString(),
  action_id: 'read_policy',
  caes: 'C0-A0-E0-S1',
  actor: 'test-actor',
  outcome: 'ALLOWED',
  policy_refs: ['test-policy'],
  provenance: {},
  ...overrides,
});

describe('Audit Trail Storage', () => {
  beforeEach(() => {
    clearAuditTrail();
    clearViolations();
    resetEnforcementCounts();
  });

  it('stores and retrieves audit event', () => {
    const event = createTestEvent();
    storeAuditEvent(event);

    const retrieved = getAuditEvent(event.id);
    expect(retrieved).toEqual(event);
  });

  it('gets all audit events', () => {
    storeAuditEvent(createTestEvent());
    storeAuditEvent(createTestEvent());
    storeAuditEvent(createTestEvent());

    expect(getAllAuditEvents()).toHaveLength(3);
  });

  it('filters by actor', () => {
    storeAuditEvent(createTestEvent({ actor: 'actor-1' }));
    storeAuditEvent(createTestEvent({ actor: 'actor-1' }));
    storeAuditEvent(createTestEvent({ actor: 'actor-2' }));

    expect(getAuditEventsByActor('actor-1')).toHaveLength(2);
    expect(getAuditEventsByActor('actor-2')).toHaveLength(1);
  });

  it('filters by outcome', () => {
    storeAuditEvent(createTestEvent({ outcome: 'ALLOWED' }));
    storeAuditEvent(createTestEvent({ outcome: 'ALLOWED' }));
    storeAuditEvent(createTestEvent({ outcome: 'BLOCKED' }));

    expect(getAuditEventsByOutcome('ALLOWED')).toHaveLength(2);
    expect(getAuditEventsByOutcome('BLOCKED')).toHaveLength(1);
  });
});

describe('Audit Trail Export/Import', () => {
  beforeEach(() => {
    clearAuditTrail();
  });

  it('exports to JSONL', () => {
    storeAuditEvent(createTestEvent());
    storeAuditEvent(createTestEvent());

    const jsonl = exportAuditTrail();
    const lines = jsonl.split('\n').filter((l) => l.trim());
    expect(lines).toHaveLength(2);
  });

  it('imports from JSONL', () => {
    const event1 = createTestEvent();
    const event2 = createTestEvent();
    const jsonl = [JSON.stringify(event1), JSON.stringify(event2)].join('\n');

    clearAuditTrail();
    const imported = importAuditTrail(jsonl);

    expect(imported).toBe(2);
    expect(getAllAuditEvents()).toHaveLength(2);
  });
});

describe('Compliance Scoring', () => {
  beforeEach(() => {
    clearAuditTrail();
    clearViolations();
    resetEnforcementCounts();
  });

  it('calculates score with no data', () => {
    const score = calculateComplianceScore(testActionSpace);
    expect(score.overall).toBe(100);
    expect(score.grade).toBe('A');
  });
});

describe('Report Generation', () => {
  beforeEach(() => {
    clearAuditTrail();
    clearViolations();
    resetEnforcementCounts();
  });

  it('generates compliance report', () => {
    const now = new Date();
    const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);

    const report = generateComplianceReport(testActionSpace, yesterday, now);

    expect(report.generated_at).toBeDefined();
    expect(report.period.start).toBeDefined();
    expect(report.period.end).toBeDefined();
    expect(report.score).toBeDefined();
    expect(report.summary).toBeDefined();
  });

  it('formats report as markdown', () => {
    const now = new Date();
    const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);

    const report = generateComplianceReport(testActionSpace, yesterday, now);
    const markdown = formatReportAsMarkdown(report);

    expect(markdown).toContain('# G.A.S. Compliance Report');
    expect(markdown).toContain('## Compliance Score');
    expect(markdown).toContain('## Summary');
  });
});
