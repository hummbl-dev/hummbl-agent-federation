---
name: gv5-compliance-scoring
description: Apply GV5 Compliance Scoring to quantify governance health across systems.
version: 0.0.1
metadata: {"domain":"GV-governance","status":"experimental"}
---

# GV5 Compliance Scoring

Apply the GV5 Compliance Scoring transformation to measure and track governance health quantitatively.

## What is GV5?

**GV5 (Compliance Scoring)** provides a weighted scoring system to quantify overall governance health, enabling trend analysis and prioritization.

## When to Use GV5

### Ideal Situations

- Generating governance health dashboards
- Comparing compliance across domains
- Prioritizing remediation efforts

### Trigger Questions

- "What's our current compliance posture?"
- "Which domain needs the most attention?"
- "Are we improving or degrading?"

## The GV5 Process

### Step 1: Define Dimensions

```yaml
# Using GV5 (Compliance Scoring) - Dimensions
dimensions:
  policy_coverage:
    weight: 0.25
    measure: "% of systems with active policies"
  violation_rate:
    weight: 0.30
    measure: "violations per 1000 actions"
  remediation_time:
    weight: 0.20
    measure: "mean time to fix violations"
  audit_completeness:
    weight: 0.15
    measure: "% of actions with full trails"
  benchmark_alignment:
    weight: 0.10
    measure: "gap score vs external standards"
```

### Step 2: Calculate Scores

```yaml
# Using GV5 (Compliance Scoring) - Calculation
calculation:
  method: weighted_average
  normalization: 0-100 scale
  formula: sum(dimension_score * weight)
```

### Step 3: Set Thresholds

```yaml
# Using GV5 (Compliance Scoring) - Thresholds
thresholds:
  healthy: ">= 85"
  warning: "70-84"
  critical: "< 70"
```

### Step 4: Track Trends

```yaml
# Using GV5 (Compliance Scoring) - Trending
trending:
  period: 30 days
  metrics:
    - current_score: 87.3
    - change: +2.1
    - direction: improving
```

## Sample Output

```yaml
compliance_report:
  overall_score: 87.3
  status: healthy
  trend: +2.1 (30d)
  by_dimension:
    policy_coverage: 92.0
    violation_rate: 85.5
    remediation_time: 78.0
    audit_completeness: 95.0
    benchmark_alignment: 88.0
  top_issues:
    - "Slow remediation in agent domain"
    - "Network policy gaps"
```

## Integration with Other Transformations

- **GV2 → GV5**: Violation data feeds scoring
- **GV4 → GV5**: Audit completeness from GV4
- **GV9 → GV5**: Benchmark alignment from GV9
- **GV5 → GV18**: Scores feed GV18 metrics

## Implementation Checklist

- [ ] Define weighted dimensions
- [ ] Implement data collection for each dimension
- [ ] Set appropriate thresholds
- [ ] Build trending capabilities
- [ ] Create visualization dashboard

## Common Pitfalls

- Weighting dimensions incorrectly
- Not normalizing across different scales
- Ignoring trends in favor of point-in-time scores

## Best Practices

- Review weights quarterly
- Alert on threshold crossings
- Compare scores across domains

---
*Apply GV5 to measure governance health objectively.*
