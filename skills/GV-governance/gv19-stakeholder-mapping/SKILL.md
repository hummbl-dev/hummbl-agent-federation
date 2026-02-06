---
name: gv19-stakeholder-mapping
description: Apply GV19 Stakeholder Mapping to define who owns and approves governance.
version: 0.0.1
metadata: {"domain":"GV-governance","status":"experimental"}
---

# GV19 Stakeholder Mapping

Apply the GV19 Stakeholder Mapping transformation to clarify governance ownership and responsibility.

## What is GV19?

**GV19 (Stakeholder Mapping)** defines who owns, approves, and is responsible for different aspects of governance.

## When to Use GV19

### Ideal Situations

- Establishing policy ownership
- Defining approval workflows
- Clarifying escalation contacts

### Trigger Questions

- "Who owns this policy?"
- "Who approves exceptions?"
- "Who should be notified about this?"

## The GV19 Process

### Step 1: Identify Stakeholder Roles

```yaml
# Using GV19 (Stakeholder Mapping) - Roles
roles:
  policy_owner:
    responsibility: "Owns policy lifecycle"
    authority: approve_changes, approve_exceptions
    accountability: policy_effectiveness

  security_reviewer:
    responsibility: "Reviews security implications"
    authority: block_risky_changes
    accountability: security_posture

  domain_expert:
    responsibility: "Provides domain context"
    authority: advise
    accountability: accuracy_of_advice

  leadership:
    responsibility: "Strategic governance decisions"
    authority: override, budget
    accountability: organizational_compliance
```

### Step 2: Map Ownership

```yaml
# Using GV19 (Stakeholder Mapping) - Ownership
ownership:
  policies:
    process-policy.allowlist:
      owner: platform-team
      reviewers: [security, ops]

    network-policy.json:
      owner: security-team
      reviewers: [platform, infrastructure]

    secrets-policy.json:
      owner: security-team
      reviewers: [platform, compliance]

  domains:
    code: platform-team
    agents: ai-team
    infrastructure: ops-team
    human: compliance-team
```

### Step 3: Define Approval Matrix

```yaml
# Using GV19 (Stakeholder Mapping) - Approvals
approval_matrix:
  policy_change:
    low_impact: [policy_owner]
    high_impact: [policy_owner, security_reviewer]
    cross_domain: [policy_owner, affected_domain_owners]

  exception:
    low_risk: [policy_owner]
    medium_risk: [policy_owner, security_reviewer]
    high_risk: [policy_owner, security_reviewer, leadership]

  autonomy_change:
    any: [policy_owner, security_reviewer, leadership]
```

### Step 4: Map Notification Paths

```yaml
# Using GV19 (Stakeholder Mapping) - Notifications
notifications:
  violation_detected:
    low: [policy_owner]
    medium: [policy_owner, security_reviewer]
    high: [policy_owner, security_reviewer, leadership]
    critical: all + pager

  policy_expiring:
    30_days: [policy_owner]
    7_days: [policy_owner, leadership]

  exception_expiring:
    7_days: [requestor, policy_owner]
```

## Stakeholder Registry

```yaml
registry:
  platform-team:
    members: [alice, bob]
    email: platform@org.com
    slack: #platform
    pager: platform-oncall

  security-team:
    members: [carol, dave]
    email: security@org.com
    slack: #security
    pager: security-oncall
```

## Integration with Other Transformations

- **GV19 → GV1**: Owners manage GV1 policy lifecycle
- **GV19 → GV3**: Stakeholders are escalation targets
- **GV19 → GV13**: Owners approve GV13 exceptions
- **P2 → GV19**: GV19 applies P2 stakeholder mapping

## Implementation Checklist

- [ ] Define all stakeholder roles
- [ ] Map every policy to an owner
- [ ] Create approval matrix
- [ ] Configure notification paths
- [ ] Maintain stakeholder registry

## Common Pitfalls

- Orphan policies (no owner)
- Unclear approval authority
- Outdated stakeholder contacts

## Best Practices

- Every policy must have an owner
- Review ownership quarterly
- Keep contact info current

---
*Apply GV19 to know who's responsible for what in governance.*
