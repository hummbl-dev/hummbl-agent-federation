---
name: gv6-boundary-definition
description: Apply GV6 Boundary Definition to set precise autonomy limits for governed systems.
version: 0.0.1
metadata: {"domain":"GV-governance","status":"experimental"}
---

# GV6 Boundary Definition

Apply the GV6 Boundary Definition transformation to establish clear autonomy boundaries for agents and systems.

## What is GV6?

**GV6 (Boundary Definition)** precisely defines what actions an autonomous system can take without human approval, and what requires escalation.

## When to Use GV6

### Ideal Situations

- Defining autonomy scope for a new agent
- Reviewing boundaries after incidents
- Expanding or restricting agent capabilities

### Trigger Questions

- "What can this agent do autonomously?"
- "Where does automation end and human review begin?"
- "What's explicitly forbidden?"

## The GV6 Process

### Step 1: Define Capability Scope

```yaml
# Using GV6 (Boundary Definition) - Capabilities
capabilities:
  allowed:
    - read: [configs, policies, audit-logs]
    - write: [audit-events, checkpoints]
    - enforce: [low-risk policies]
  restricted:
    - write: [policies]  # Requires approval
    - modify: [own-boundaries]  # Never autonomous
  forbidden:
    - delete: [audit-logs]
    - expand: [own-autonomy]
```

### Step 2: Set Resource Limits

```yaml
# Using GV6 (Boundary Definition) - Limits
limits:
  rate:
    actions_per_minute: 60
    api_calls_per_hour: 1000
  resources:
    max_memory_mb: 512
    max_cpu_percent: 25
  output:
    max_file_size_kb: 1024
    max_response_length: 10000
```

### Step 3: Define Approval Gates

```yaml
# Using GV6 (Boundary Definition) - Gates
gates:
  self_modification:
    requires: [owner, security]
    timeout: never_auto_approve
  policy_change:
    requires: [policy_owner]
    timeout: 72h
  high_risk_action:
    requires: [any_approver]
    timeout: 24h
```

### Step 4: Document Boundary Violations

```yaml
# Using GV6 (Boundary Definition) - Violation handling
on_boundary_violation:
  action: block_and_log
  escalate_to: GV3
  audit: mandatory
```

## Integration with Other Transformations

- **GV6 → GV1**: Boundaries are policy-governed via GV1
- **GV6 → GV3**: Violations escalate via GV3
- **GV6 → GV7**: Boundary changes trigger GV7 checkpoints

## Implementation Checklist

- [ ] Enumerate all capabilities with allow/restrict/forbid
- [ ] Set quantitative resource limits
- [ ] Define approval gates for sensitive actions
- [ ] Configure violation handling
- [ ] Test boundary enforcement

## Common Pitfalls

- Boundaries too broad (risk)
- Boundaries too narrow (ineffective automation)
- Not updating boundaries as system evolves

## Best Practices

- Start with minimal autonomy, expand carefully
- Require dual approval for boundary expansions
- Review boundaries after every incident

---
*Apply GV6 to define exactly where autonomy ends.*
