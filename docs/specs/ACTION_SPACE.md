# HUMMBL G.A.S. Agent ACTION SPACE

Version: 1.0.0
Based on: CAES Classification Framework

## Overview

The ACTION SPACE defines all actions the G.A.S. Agent can perform, classified using the CAES framework:

- **C**lassification — Risk level and domain categorization
- **A**uthority — Who/what can authorize the action
- **E**ffect — Side effects and reversibility properties
- **S**cope — Resource boundaries and blast radius

This integrates with MRCC/NCC (Maximum/Nominal Capability Constraints) and epoch-bound monotonic governance.

---

## CAES Classification Matrix

### C — Classification Levels

| Level | Risk | Description | Examples |
|-------|------|-------------|----------|
| C0 | None | Pure observation, no state change | Read config, list policies |
| C1 | Low | Reversible, audited state changes | Update learning-state, write checkpoints |
| C2 | Medium | Significant changes, reviewable | Propose policy update, flag violation |
| C3 | High | Enforcement actions, limited reversibility | Block execution, enforce policy |
| C4 | Critical | Structural changes, requires approval | Modify boundaries, change escalation rules |
| C5 | Restricted | Self-modification, multi-approval required | Expand autonomy, modify own constraints |

### A — Authority Requirements

| Authority | Approvers | Timeout | Auto-Approve |
|-----------|-----------|---------|--------------|
| A0-SELF | gas-agent autonomous | N/A | Yes (within bounds) |
| A1-NOTIFY | gas-agent + notify owner | N/A | Yes |
| A2-REVIEW | policy-owner review | 72h | No |
| A3-APPROVE | designated-owner explicit | 24h | No |
| A4-MULTI | owner + security team | Never | No |
| A5-EMERGENCY | security-team override | Immediate | No (block default) |

### E — Effect Properties

| Effect | Reversibility | Side Effects | Audit Level |
|--------|---------------|--------------|-------------|
| E0-PURE | N/A (no change) | None | Minimal |
| E1-REVERT | Fully reversible | Local only | Standard |
| E2-CHECKPOINT | Checkpoint-recoverable | Contained | Standard |
| E3-COMPENSATE | Compensating action available | May propagate | Enhanced |
| E4-DEFERRED | Reversible within epoch | Cross-system | Full |
| E5-PERMANENT | Not reversible | Global | Full + Alert |

### S — Scope Boundaries

| Scope | Resources | Blast Radius | Isolation |
|-------|-----------|--------------|-----------|
| S0-SELF | Own state only | None | Full |
| S1-LOCAL | Single policy/config | Minimal | Container |
| S2-DOMAIN | Governance domain | Contained | Domain |
| S3-CROSS | Multiple domains | Moderate | Partial |
| S4-SYSTEM | Full system | Significant | None |
| S5-EXTERNAL | External systems | Unknown | None |

---

## Action Catalog

### Observation Actions (C0)

```yaml
action: read_policy
caes: C0-A0-E0-S1
description: Read a policy definition
authority: self
audit: minimal
```

```yaml
action: list_violations
caes: C0-A0-E0-S2
description: List recorded violations in a domain
authority: self
audit: minimal
```

```yaml
action: query_audit_log
caes: C0-A0-E0-S3
description: Query historical audit events
authority: self
audit: minimal
```

```yaml
action: inspect_checkpoint
caes: C0-A0-E0-S0
description: Examine a checkpoint state
authority: self
audit: minimal
```

### Learning Actions (C1)

```yaml
action: update_learning_state
caes: C1-A0-E1-S0
description: Update agent's learning model
authority: self
effect: reversible
checkpoint: before_update
```

```yaml
action: write_checkpoint
caes: C1-A0-E1-S0
description: Create a state checkpoint
authority: self
effect: reversible
```

```yaml
action: record_observation
caes: C1-A1-E1-S1
description: Record an observation for learning
authority: self + notify
effect: reversible
```

```yaml
action: propose_improvement
caes: C1-A1-E1-S2
description: Suggest a governance improvement
authority: self + notify
effect: reversible
requires: violation_evidence OR benchmark_gap
```

### Governance Actions (C2)

```yaml
action: flag_violation
caes: C2-A1-E2-S2
description: Flag a policy violation for review
authority: self + notify
effect: checkpoint-recoverable
triggers: escalation_check
```

```yaml
action: propose_policy_update
caes: C2-A2-E2-S2
description: Propose changes to an existing policy
authority: requires policy-owner review
effect: checkpoint-recoverable
timeout: 72h
```

```yaml
action: recommend_escalation
caes: C2-A1-E2-S2
description: Recommend escalation to higher authority
authority: self + notify
effect: checkpoint-recoverable
```

```yaml
action: trigger_benchmark
caes: C2-A1-E2-S3
description: Initiate a governance benchmark run
authority: self + notify
effect: checkpoint-recoverable
cost_check: required
```

### Enforcement Actions (C3)

```yaml
action: enforce_policy
caes: C3-A0-E3-S2
description: Enforce an established policy
authority: self (within approved policies)
effect: compensating action available
requires: policy.approved = true
```

```yaml
action: block_action
caes: C3-A1-E3-S3
description: Block a potentially violating action
authority: self + notify
effect: compensating action available
escalates_to: L2_review
timeout: until_reviewed
```

```yaml
action: apply_remediation
caes: C3-A2-E3-S2
description: Apply an approved remediation
authority: requires review
effect: compensating action available
requires: remediation.approved = true
```

```yaml
action: rollback_to_checkpoint
caes: C3-A2-E3-S3
description: Rollback to a previous checkpoint
authority: requires review
effect: compensating action available
requires: checkpoint.valid = true
```

### Structural Actions (C4)

```yaml
action: update_escalation_rules
caes: C4-A3-E4-S3
description: Modify escalation thresholds or paths
authority: requires designated-owner approval
effect: reversible within epoch
gitops: required
```

```yaml
action: add_policy_domain
caes: C4-A3-E4-S4
description: Add a new governance domain
authority: requires designated-owner approval
effect: reversible within epoch
gitops: required
```

```yaml
action: modify_approval_gate
caes: C4-A4-E4-S4
description: Change approval gate requirements
authority: requires owner + security
effect: reversible within epoch
gitops: required
ci_check: required
```

### Restricted Actions (C5)

```yaml
action: expand_autonomy
caes: C5-A4-E5-S4
description: Request expansion of autonomous boundaries
authority: requires owner + security
effect: permanent (new epoch)
gitops: required
ci_check: required
status: FORBIDDEN_WITHOUT_OVERRIDE
```

```yaml
action: modify_own_boundaries
caes: C5-A4-E5-S0
description: Attempt to modify own constraints
authority: requires owner + security
effect: permanent (new epoch)
status: FORBIDDEN
```

```yaml
action: bypass_approval_gate
caes: C5-A5-E5-S4
description: Emergency bypass of approval gate
authority: security-team only
effect: permanent
requires: active_incident
triggers: immediate_audit
```

---

## MRCC/NCC Constraints

### Maximum Capability Constraints (MRCC)

Absolute limits that cannot be exceeded:

```json
{
  "mrcc": {
    "max_classification": "C3",
    "max_scope": "S3",
    "max_effect": "E3",
    "forbidden_actions": [
      "expand_autonomy",
      "modify_own_boundaries",
      "bypass_approval_gate"
    ],
    "rate_limits": {
      "C3_per_hour": 10,
      "C2_per_hour": 100,
      "total_per_minute": 60
    }
  }
}
```

### Nominal Capability Constraints (NCC)

Default operating limits (can be elevated with approval):

```json
{
  "ncc": {
    "default_classification": "C2",
    "default_scope": "S2",
    "default_effect": "E2",
    "preferred_actions": [
      "read_policy",
      "flag_violation",
      "propose_improvement",
      "record_observation"
    ],
    "discouraged_actions": [
      "block_action",
      "rollback_to_checkpoint"
    ]
  }
}
```

---

## Epoch-Bound Governance

### Epoch Definition

An epoch represents a governance boundary with monotonic properties:

```json
{
  "epoch": {
    "id": "2026-02-05-001",
    "started": "2026-02-05T00:00:00Z",
    "policy_hash": "sha256:abc123...",
    "mrcc_hash": "sha256:def456...",
    "monotonic_properties": [
      "autonomy_level_cannot_increase",
      "scope_cannot_expand",
      "forbidden_stays_forbidden"
    ]
  }
}
```

### Epoch Transitions

New epochs require:
1. GitOps commit with policy changes
2. CI validation passing
3. Multi-approval gate (A4 minimum)
4. Audit trail of transition

---

## Action Selection Algorithm

```
1. Parse intent → candidate actions
2. Filter by MRCC (hard limits)
3. Score by NCC (preferences)
4. Check authority (A-level)
5. Verify scope (S-level)
6. Assess effect (E-level)
7. If C >= 2: create checkpoint
8. Execute with audit
9. Verify monotonic properties maintained
```

---

## Integration Points

### GV Domain Skills

| Skill | Primary Actions | CAES Range |
|-------|-----------------|------------|
| GV1-policy-lifecycle | propose_policy_update | C2-C4 |
| GV2-violation-taxonomy | flag_violation, list_violations | C0-C2 |
| GV3-escalation-logic | recommend_escalation, block_action | C2-C3 |
| GV4-audit-trails | query_audit_log, record_observation | C0-C1 |
| GV5-compliance-mapping | read_policy, trigger_benchmark | C0-C2 |
| GV8-rollback-protocols | rollback_to_checkpoint | C3 |
| GV15-checkpoint-recovery | write_checkpoint, inspect_checkpoint | C0-C1 |

### Base120 Transformation Mapping

| Transformation | Relevant Actions |
|----------------|------------------|
| P1-Framing | All observation actions (C0) |
| IN2-Premortem | propose_improvement, flag_violation |
| DE1-Root Cause | query_audit_log, list_violations |
| RE2-Feedback | update_learning_state |
| SY3-System State | inspect_checkpoint, trigger_benchmark |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-05 | Initial ACTION SPACE definition |
