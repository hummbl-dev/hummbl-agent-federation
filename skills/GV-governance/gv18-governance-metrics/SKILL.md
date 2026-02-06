---
name: gv18-governance-metrics
description: Apply GV18 Governance Metrics to define KPIs for governance health.
version: 0.0.1
metadata: {"domain":"GV-governance","status":"experimental"}
---

# GV18 Governance Metrics

Apply the GV18 Governance Metrics transformation to measure governance effectiveness.

## What is GV18?

**GV18 (Governance Metrics)** defines the key performance indicators (KPIs) for measuring governance health and effectiveness.

## When to Use GV18

### Ideal Situations

- Building governance dashboards
- Reporting to leadership
- Identifying improvement areas

### Trigger Questions

- "How effective is our governance?"
- "What metrics should we track?"
- "How do we trend over time?"

## The GV18 Process

### Step 1: Define Metric Categories

```yaml
# Using GV18 (Governance Metrics) - Categories
categories:
  policy_health:
    - coverage_percentage
    - policies_with_owners
    - policies_reviewed_on_time

  compliance:
    - violation_rate
    - false_positive_rate
    - compliance_score_trend

  operational:
    - mean_time_to_detect (MTTD)
    - mean_time_to_remediate (MTTR)
    - escalation_rate

  self_improvement:
    - learning_proposals_accepted
    - policy_updates_from_learning
    - benchmark_alignment_trend
```

### Step 2: Define Specific Metrics

```yaml
# Using GV18 (Governance Metrics) - Definitions
metrics:
  violation_rate:
    formula: violations / (actions * 1000)
    unit: per 1000 actions
    target: "< 5"
    alert: "> 10"

  mttr:
    formula: avg(remediation_end - violation_detected)
    unit: hours
    target: "< 4h for high severity"
    alert: "> 24h"

  policy_coverage:
    formula: (systems_with_policy / total_systems) * 100
    unit: percentage
    target: "> 95%"
    alert: "< 80%"
```

### Step 3: Configure Collection

```yaml
# Using GV18 (Governance Metrics) - Collection
collection:
  schedule: hourly
  sources:
    - audit_trail: GV4
    - compliance_scores: GV5
    - violation_data: GV2

  aggregation:
    hourly: raw
    daily: avg, min, max
    weekly: trends
    monthly: summary
```

### Step 4: Visualize and Report

```yaml
# Using GV18 (Governance Metrics) - Reporting
reports:
  real_time_dashboard:
    metrics: [compliance_score, active_violations, violation_rate]
    refresh: 5m

  daily_summary:
    metrics: all
    delivery: slack, email
    schedule: "08:00 UTC"

  monthly_report:
    metrics: all + trends
    comparisons: [prev_month, prev_quarter]
    audience: leadership
```

## Sample Dashboard

```yaml
governance_dashboard:
  timestamp: 2026-02-05T12:00:00Z

  headline_metrics:
    compliance_score: 87.3 (+2.1)
    violation_rate: 3.2/1000 (-0.5)
    mttr: 2.1h (-0.3h)

  by_domain:
    code: { score: 91, violations: 2 }
    agents: { score: 85, violations: 5 }
    infrastructure: { score: 88, violations: 1 }
    human: { score: 84, violations: 3 }

  trends:
    30_day: improving
    90_day: stable
```

## Integration with Other Transformations

- **GV4 → GV18**: Audit data feeds metrics
- **GV5 → GV18**: Compliance scores are metrics
- **GV18 → GV10**: Metrics guide learning priorities
- **GV18 → GV20**: Metrics inform evolution planning

## Implementation Checklist

- [ ] Define all metric categories
- [ ] Specify formulas and targets
- [ ] Configure collection pipeline
- [ ] Build dashboards
- [ ] Set up alerting

## Common Pitfalls

- Too many metrics (noise)
- Metrics without targets
- Not acting on metric insights

## Best Practices

- Focus on actionable metrics
- Set targets and alert thresholds
- Review metrics definitions quarterly

---
*Apply GV18 to measure what matters in governance.*
