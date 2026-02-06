---
name: gv17-remediation-flows
description: Apply GV17 Remediation Flows to fix violations systematically.
version: 0.0.1
metadata: {"domain":"GV-governance","status":"experimental"}
---

# GV17 Remediation Flows

Apply the GV17 Remediation Flows transformation to systematically fix governance violations.

## What is GV17?

**GV17 (Remediation Flows)** defines structured processes for addressing and resolving governance violations.

## When to Use GV17

### Ideal Situations

- After detecting a violation
- When drift requires correction
- Implementing systematic fixes

### Trigger Questions

- "How do we fix this violation?"
- "What's the remediation priority?"
- "How do we prevent recurrence?"

## The GV17 Process

### Step 1: Assess Violation

```yaml
# Using GV17 (Remediation Flows) - Assessment
assessment:
  violation_id: VIO-{id}
  category: GV2_category
  severity: GV2_severity

  analysis:
    root_cause: DE1_analysis
    affected_systems: [{list}]
    business_impact: {description}

  priority:
    score: critical | high | medium | low
    sla: 4h | 24h | 72h | 7d
```

### Step 2: Select Remediation

```yaml
# Using GV17 (Remediation Flows) - Selection
remediation_options:
  - option: auto_fix
    applicable: simple_config_violations
    risk: low
    time: immediate

  - option: guided_fix
    applicable: complex_violations
    risk: medium
    time: hours

  - option: manual_fix
    applicable: critical_or_ambiguous
    risk: varies
    time: varies

selected: {option}
justification: {reason}
```

### Step 3: Execute Remediation

```yaml
# Using GV17 (Remediation Flows) - Execution
execution:
  steps:
    1_prepare:
      - create_checkpoint: GV7
      - notify_stakeholders

    2_fix:
      - apply_remediation
      - validate_fix

    3_verify:
      - run_compliance_check
      - confirm_violation_resolved

    4_document:
      - log_remediation: GV4
      - update_metrics: GV18

  rollback_ready: true
```

### Step 4: Prevent Recurrence

```yaml
# Using GV17 (Remediation Flows) - Prevention
prevention:
  analysis:
    why_occurred: {root_cause}
    why_not_prevented: {gap}

  actions:
    - policy_update: {if_needed}
    - monitoring_improvement: {if_needed}
    - training: {if_needed}

  learning:
    feed_to: GV10
    pattern_id: {if_recurring}
```

## Remediation Playbooks

```yaml
playbooks:
  secret_exposure:
    priority: critical
    steps:
      1: rotate_secret_immediately
      2: revoke_old_secret
      3: audit_access_logs
      4: notify_security_team
      5: document_incident

  policy_bypass:
    priority: high
    steps:
      1: block_bypassing_action
      2: investigate_intent
      3: enforce_policy_or_document_exception
      4: update_detection_rules
```

## Integration with Other Transformations

- **GV2 → GV17**: Violation category guides remediation
- **GV3 → GV17**: Escalation may trigger remediation
- **GV17 → GV7**: Checkpoint before remediation
- **DE1 → GV17**: Root cause analysis informs fix

## Implementation Checklist

- [ ] Define assessment criteria
- [ ] Create remediation playbooks
- [ ] Implement execution workflow
- [ ] Build prevention feedback loop
- [ ] Track remediation metrics

## Common Pitfalls

- Fixing symptoms not causes
- No prevention analysis
- Skipping checkpoint before fix

## Best Practices

- Always checkpoint before remediation
- Document root cause analysis
- Feed learnings to GV10

---
*Apply GV17 to fix violations systematically and prevent recurrence.*
