---
name: gv9-benchmark-alignment
description: Apply GV9 Benchmark Alignment to map governance to external standards.
version: 0.0.1
metadata: {"domain":"GV-governance","status":"experimental"}
---

# GV9 Benchmark Alignment

Apply the GV9 Benchmark Alignment transformation to align governance with external standards and frameworks.

## What is GV9?

**GV9 (Benchmark Alignment)** maps internal governance policies to external compliance frameworks (SOC2, ISO 27001, NIST, CIS) and tracks alignment gaps.

## When to Use GV9

### Ideal Situations

- Preparing for compliance audits
- Designing policies that meet external requirements
- Identifying governance gaps

### Trigger Questions

- "Does this policy meet SOC2 requirements?"
- "What's our alignment gap with NIST CSF?"
- "Which controls are we missing?"

## The GV9 Process

### Step 1: Define Target Standards

```yaml
# Using GV9 (Benchmark Alignment) - Standards
standards:
  primary:
    - SOC2_Type_II
    - ISO_27001
  secondary:
    - NIST_CSF
    - CIS_Controls_v8
```

### Step 2: Map Controls

```yaml
# Using GV9 (Benchmark Alignment) - Mapping
mapping:
  SOC2_CC6.1:  # Logical Access Controls
    internal_policy: process-policy.allowlist
    coverage: full
    evidence: audit-trail

  ISO_A.9.2.3:  # Access Rights Management
    internal_policy: secrets-policy.json
    coverage: partial
    gap: "Missing periodic access review"
```

### Step 3: Calculate Alignment Score

```yaml
# Using GV9 (Benchmark Alignment) - Scoring
alignment:
  SOC2:
    controls_mapped: 45/52
    coverage_score: 86.5%
    gaps: [CC7.2, CC8.1]

  ISO_27001:
    controls_mapped: 89/114
    coverage_score: 78.1%
    gaps: [A.12.4.1, A.14.2.8]
```

### Step 4: Track Changes

```yaml
# Using GV9 (Benchmark Alignment) - Tracking
sync:
  schedule: weekly
  sources:
    - official_standard_updates
    - internal_policy_changes

  drift_detection:
    enabled: true
    alert_on: gap_increase
```

## Gap Report Example

```yaml
gap_report:
  generated: 2026-02-05
  standard: SOC2_Type_II
  gaps:
    - control: CC7.2
      requirement: "System monitoring"
      current_state: "Partial - missing real-time alerts"
      remediation: "Implement GV16 drift detection"
      priority: high
```

## Integration with Other Transformations

- **GV9 → GV5**: Alignment feeds compliance scoring
- **GV9 → GV1**: Gaps drive policy creation via GV1
- **GV9 → GV20**: Gaps inform GV20 evolution planning

## Implementation Checklist

- [ ] Identify applicable standards
- [ ] Map controls to internal policies
- [ ] Calculate coverage scores
- [ ] Document gaps with remediation plans
- [ ] Set up sync schedule

## Common Pitfalls

- Mapping too optimistically (claiming coverage that doesn't exist)
- Not updating when standards evolve
- Ignoring secondary/emerging standards

## Best Practices

- Be conservative in coverage claims
- Sync with official standard updates weekly
- Prioritize gaps by audit timeline

---
*Apply GV9 to prove compliance with external standards.*
