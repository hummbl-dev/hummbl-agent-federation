---
name: gv3-escalation-mapping
description: Apply GV3 Escalation Mapping to define when and how governance issues should be escalated.
version: 0.0.1
metadata: {"domain":"GV-governance","status":"experimental"}
---

# GV3 Escalation Mapping

Apply the GV3 Escalation Mapping transformation to establish clear escalation paths for governance issues.

## What is GV3?

**GV3 (Escalation Mapping)** defines the criteria, paths, and timelines for escalating governance issues from automated handling to human review.

## When to Use GV3

### Ideal Situations

- Designing escalation workflows for a new policy domain
- Reviewing escalation thresholds after incidents
- Coordinating multi-team response procedures

### Trigger Questions

- "When should this be escalated?"
- "Who needs to be notified?"
- "What's the response timeline?"

## The GV3 Process

### Step 1: Define Escalation Triggers

```yaml
# Using GV3 (Escalation Mapping) - Triggers
triggers:
  severity_threshold: medium | high | critical
  frequency_threshold: 3 occurrences in 24h
  impact_threshold: multi-system | data-exposure
  time_threshold: unresolved after 4h
```

### Step 2: Map Escalation Levels

```yaml
# Using GV3 (Escalation Mapping) - Levels
levels:
  L1_auto:
    handler: gas-agent
    actions: [log, enforce, notify-owner]
  L2_review:
    handler: policy-owner
    actions: [review, approve-exception, update-policy]
  L3_emergency:
    handler: security-team
    actions: [block, investigate, incident-response]
```

### Step 3: Define Notification Paths

```yaml
# Using GV3 (Escalation Mapping) - Notifications
notifications:
  channels:
    - slack: #governance-alerts
    - email: security@org.com
  timing:
    L1: immediate (automated)
    L2: within 1h
    L3: within 15m + page
```

### Step 4: Set Response SLAs

```yaml
# Using GV3 (Escalation Mapping) - SLAs
sla:
  acknowledge:
    L1: N/A (automated)
    L2: 4h
    L3: 30m
  resolve:
    L1: immediate
    L2: 24h
    L3: 4h
```

## Integration with Other Transformations

- **GV2 → GV3**: Use GV2 severity to determine escalation level
- **GV3 → GV17**: Escalation triggers GV17 remediation flows
- **GV3 → GV19**: Reference GV19 stakeholder mapping for handlers

## Implementation Checklist

- [ ] Define clear trigger criteria
- [ ] Map each level to specific handlers
- [ ] Configure notification channels
- [ ] Set and communicate SLAs
- [ ] Test escalation paths regularly

## Common Pitfalls

- Escalating too aggressively (alert fatigue)
- Unclear ownership at each level
- Missing after-hours escalation paths

## Best Practices

- Include time-based auto-escalation
- Document escalation decisions in audit trail
- Review escalation patterns monthly

---
*Apply GV3 to ensure governance issues reach the right people at the right time.*
