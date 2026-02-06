---
name: gv2-violation-taxonomy
description: Apply GV2 Violation Taxonomy to classify and categorize governance breaches systematically.
version: 0.0.1
metadata: {"domain":"GV-governance","status":"experimental"}
---

# GV2 Violation Taxonomy

Apply the GV2 Violation Taxonomy transformation to classify governance violations for consistent handling and pattern analysis.

## What is GV2?

**GV2 (Violation Taxonomy)** provides a structured classification system for governance violations, enabling consistent categorization, prioritization, and trend analysis.

## When to Use GV2

### Ideal Situations

- Categorizing a new type of violation
- Analyzing violation patterns across systems
- Prioritizing remediation efforts

### Trigger Questions

- "What type of violation is this?"
- "How severe is this breach?"
- "Is this a recurring pattern?"

## The GV2 Process

### Step 1: Identify Violation

```yaml
# Using GV2 (Violation Taxonomy) - Capture
violation:
  id: VIO-{timestamp}-{hash}
  detected: {timestamp}
  source: {system|agent|human}
  raw_event: {description}
```

### Step 2: Classify by Domain

```yaml
# Using GV2 (Violation Taxonomy) - Domain classification
domain:
  primary: process | network | secrets | agent | infrastructure | human
  secondary: [{additional domains}]
```

### Step 3: Assess Severity

```yaml
# Using GV2 (Violation Taxonomy) - Severity
severity:
  level: low | medium | high | critical
  factors:
    - data_exposure: true | false
    - system_impact: none | degraded | down
    - reversible: true | false
```

### Step 4: Categorize Pattern

```yaml
# Using GV2 (Violation Taxonomy) - Pattern
pattern:
  type: first_occurrence | recurring | escalating
  frequency: {count} in {period}
  related_violations: [{ids}]
```

## Violation Categories

| Category | Description | Example |
|----------|-------------|---------|
| ACCESS | Unauthorized access attempts | Bypassing allowlist |
| BOUNDARY | Exceeding defined limits | Rate limit exceeded |
| INTEGRITY | Data/config tampering | Policy file modified |
| DISCLOSURE | Information exposure | Secret in logs |
| COMPLIANCE | External standard breach | SOC2 control failure |

## Integration with Other Transformations

- **GV2 → GV3**: Feed severity into GV3 escalation mapping
- **GV2 → GV17**: Use category in GV17 remediation flows
- **GV2 → GV10**: Aggregate patterns for GV10 learning

## Implementation Checklist

- [ ] Capture full violation context
- [ ] Classify by domain and category
- [ ] Assess severity with explicit factors
- [ ] Link to related violations if pattern detected

## Common Pitfalls

- Classifying too broadly (losing useful detail)
- Ignoring low-severity violations (miss patterns)
- Not linking related violations

## Best Practices

- Use consistent category codes across all systems
- Always capture reversibility as a severity factor
- Review taxonomy quarterly for new categories

---
*Apply GV2 to ensure violations are classified consistently for effective governance.*
