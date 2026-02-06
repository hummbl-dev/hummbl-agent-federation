---
name: gv16-drift-detection
description: Apply GV16 Drift Detection to identify policy divergence from baselines.
version: 0.0.1
metadata: {"domain":"GV-governance","status":"experimental"}
---

# GV16 Drift Detection

Apply the GV16 Drift Detection transformation to identify when systems diverge from governance baselines.

## What is GV16?

**GV16 (Drift Detection)** continuously monitors governed systems for divergence from established policies and baselines.

## When to Use GV16

### Ideal Situations

- Continuous compliance monitoring
- Detecting unauthorized changes
- Identifying gradual policy erosion

### Trigger Questions

- "Has anything drifted from the baseline?"
- "Are all systems still compliant?"
- "What changed since the last checkpoint?"

## The GV16 Process

### Step 1: Establish Baselines

```yaml
# Using GV16 (Drift Detection) - Baselines
baselines:
  config_baseline:
    source: configs/
    hash: sha256:{hash}
    captured: {timestamp}

  policy_baseline:
    source: active_policies
    snapshot: {state}
    captured: {timestamp}

  capability_baseline:
    source: runners/*/CAPABILITIES.json
    snapshot: {state}
    captured: {timestamp}
```

### Step 2: Configure Detection

```yaml
# Using GV16 (Drift Detection) - Detection
detection:
  schedule: every 1h
  method: hash_comparison | deep_diff

  sensitivity:
    config_files: any_change
    policy_state: structural_change
    metrics: threshold_breach
```

### Step 3: Identify Drift

```yaml
# Using GV16 (Drift Detection) - Drift identified
drift:
  id: DFT-{timestamp}
  type: config | policy | capability | metric

  details:
    file: configs/network-policy.json
    baseline_hash: sha256:abc...
    current_hash: sha256:def...
    diff: |
      - "api.trusted.com"
      + "api.untrusted.com"

  severity: low | medium | high
  detected: {timestamp}
```

### Step 4: Respond to Drift

```yaml
# Using GV16 (Drift Detection) - Response
response:
  auto_actions:
    low_severity: log_and_alert
    medium_severity: alert_and_escalate
    high_severity: alert_escalate_and_block

  manual_review:
    classify: intentional | unintentional | malicious
    action: accept | remediate | rollback
```

## Drift Categories

| Category | Detection | Typical Severity |
|----------|-----------|------------------|
| Config drift | Hash change | Medium |
| Policy drift | Structure change | High |
| Capability drift | New capability | High |
| Metric drift | Threshold breach | Varies |
| Baseline drift | Expected state change | Low (if approved) |

## Integration with Other Transformations

- **GV16 → GV3**: Drift triggers GV3 escalation
- **GV16 → GV17**: Drift feeds GV17 remediation
- **GV16 → GV4**: All drift logged via GV4
- **RE2 → GV16**: GV16 implements RE2 feedback loops

## Implementation Checklist

- [ ] Establish all baselines
- [ ] Configure detection schedule
- [ ] Set severity thresholds
- [ ] Implement response automation
- [ ] Build drift reporting

## Common Pitfalls

- Too many false positives (over-sensitive)
- Missing important drifts (under-sensitive)
- Not updating baselines after approved changes

## Best Practices

- Update baseline after every approved change
- Alert immediately on high-severity drift
- Review drift patterns for systemic issues

---
*Apply GV16 to catch governance drift before it becomes a problem.*
