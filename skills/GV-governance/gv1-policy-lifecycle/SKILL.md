---
name: gv1-policy-lifecycle
description: Apply GV1 Policy Lifecycle to manage the full creation, enforcement, and retirement flow of governance policies.
version: 0.0.1
metadata: {"domain":"GV-governance","status":"experimental"}
---

# GV1 Policy Lifecycle

Apply the GV1 Policy Lifecycle transformation to manage governance policies from creation through enforcement to retirement.

## What is GV1?

**GV1 (Policy Lifecycle)** defines the complete lifecycle of a governance policy: drafting, review, activation, enforcement, monitoring, and eventual retirement or replacement.

## When to Use GV1

### Ideal Situations

- Creating a new governance policy from scratch
- Reviewing existing policies for updates or retirement
- Establishing policy versioning and change management

### Trigger Questions

- "How should we structure this new policy?"
- "When should this policy be retired?"
- "What's the approval flow for policy changes?"

## The GV1 Process

### Step 1: Draft Policy

```yaml
# Using GV1 (Policy Lifecycle) - Draft phase
policy:
  id: POL-{domain}-{sequence}
  version: 0.1.0-draft
  status: draft
  owner: {owner}
  created: {timestamp}
```

### Step 2: Review and Approve

```yaml
# Using GV1 (Policy Lifecycle) - Review phase
review:
  reviewers: [{list}]
  approval_threshold: {n} approvers
  deadline: {timestamp}
```

### Step 3: Activate and Enforce

```yaml
# Using GV1 (Policy Lifecycle) - Activation
status: active
activated: {timestamp}
enforcement: automatic | advisory
```

### Step 4: Monitor and Evolve

```yaml
# Using GV1 (Policy Lifecycle) - Monitoring
metrics:
  violations_30d: {count}
  false_positives: {count}
  review_due: {timestamp}
```

### Step 5: Retire or Replace

```yaml
# Using GV1 (Policy Lifecycle) - Retirement
status: deprecated | retired
replaced_by: {new_policy_id} | null
retirement_date: {timestamp}
```

## Integration with Other Transformations

- **GV1 → GV2**: Use GV2 to classify violations during enforcement
- **GV1 → GV14**: Apply GV14 for policy inheritance hierarchies
- **GV1 → GV10**: Feed enforcement data into GV10 learning integration

## Implementation Checklist

- [ ] Define policy scope and ownership
- [ ] Establish review and approval workflow
- [ ] Set enforcement mode (automatic/advisory)
- [ ] Configure monitoring and metrics
- [ ] Plan retirement criteria

## Common Pitfalls

- Creating policies without clear ownership
- Skipping the review phase for "urgent" policies
- Never retiring outdated policies

## Best Practices

- Version all policies with semantic versioning
- Require at least two reviewers for policy changes
- Set explicit review dates for all active policies

---
*Apply GV1 to ensure governance policies are well-managed throughout their lifecycle.*
