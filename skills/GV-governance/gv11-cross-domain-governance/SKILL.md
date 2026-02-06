---
name: gv11-cross-domain-governance
description: Apply GV11 Cross-Domain Governance to manage policies spanning multiple systems.
version: 0.0.1
metadata: {"domain":"GV-governance","status":"experimental"}
---

# GV11 Cross-Domain Governance

Apply the GV11 Cross-Domain Governance transformation to coordinate policies across system boundaries.

## What is GV11?

**GV11 (Cross-Domain Governance)** manages governance that spans code, agents, infrastructure, and human workflows, ensuring consistency and handling cascading effects.

## When to Use GV11

### Ideal Situations

- Policy changes affecting multiple systems
- Coordinating governance across teams
- Analyzing cascading impacts

### Trigger Questions

- "Which other systems does this policy affect?"
- "How do we keep governance consistent across domains?"
- "What's the cascade if this policy changes?"

## The GV11 Process

### Step 1: Map Domain Dependencies

```yaml
# Using GV11 (Cross-Domain Governance) - Dependencies
domains:
  code:
    governs: [repositories, ci_cd, dependencies]
    depends_on: [agents, infrastructure]
  agents:
    governs: [runners, capabilities, execution]
    depends_on: [infrastructure, code]
  infrastructure:
    governs: [network, resources, deployment]
    depends_on: [code]
  human:
    governs: [approvals, ownership, escalation]
    depends_on: [all]
```

### Step 2: Identify Cross-Domain Policies

```yaml
# Using GV11 (Cross-Domain Governance) - Cross-domain policies
cross_domain:
  - policy: secrets-policy
    affects: [code, agents, infrastructure]
    consistency: strict  # Must be identical

  - policy: network-policy
    affects: [agents, infrastructure]
    consistency: compatible  # Can vary but must interoperate
```

### Step 3: Handle Cascades

```yaml
# Using GV11 (Cross-Domain Governance) - Cascades
cascade_scenarios:
  code_change_affects_agent:
    trigger: "New tool added to codebase"
    cascade:
      1: "Update runner CAPABILITIES.json"
      2: "Review agent boundary definitions"
      3: "Test integration"

  agent_affects_infra:
    trigger: "Runner needs new network domain"
    cascade:
      1: "Update network-policy.json"
      2: "Validate no security regressions"
      3: "Deploy infrastructure change"
```

### Step 4: Maintain Consistency

```yaml
# Using GV11 (Cross-Domain Governance) - Consistency
consistency_checks:
  schedule: daily
  checks:
    - secrets_policy_sync
    - capability_boundary_alignment
    - escalation_path_validity

  on_drift:
    action: alert_and_log
    escalate: GV3_L2
```

## Integration with Other Transformations

- **GV11 → GV1**: Cross-domain policies follow GV1 lifecycle
- **GV11 → GV3**: Cross-domain issues escalate via GV3
- **SY8 → GV11**: GV11 applies SY8 systems thinking

## Implementation Checklist

- [ ] Map all domain dependencies
- [ ] Identify cross-domain policies
- [ ] Document cascade scenarios
- [ ] Implement consistency checks
- [ ] Set up cross-domain alerting

## Common Pitfalls

- Treating domains as isolated
- Missing cascade effects
- Inconsistent policies across domains

## Best Practices

- Maintain explicit dependency graph
- Test cascades before deployment
- Review cross-domain consistency regularly

---
*Apply GV11 to govern across system boundaries coherently.*
