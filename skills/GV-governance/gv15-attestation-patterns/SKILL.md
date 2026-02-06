---
name: gv15-attestation-patterns
description: Apply GV15 Attestation Patterns to provide proof of compliance.
version: 0.0.1
metadata: {"domain":"GV-governance","status":"experimental"}
---

# GV15 Attestation Patterns

Apply the GV15 Attestation Patterns transformation to create verifiable compliance proofs.

## What is GV15?

**GV15 (Attestation Patterns)** defines how to generate, store, and verify attestations that prove governance compliance.

## When to Use GV15

### Ideal Situations

- Preparing for external audits
- Proving compliance to stakeholders
- Creating tamper-evident compliance records

### Trigger Questions

- "How do we prove this policy was enforced?"
- "What evidence do auditors need?"
- "How do we verify this attestation is authentic?"

## The GV15 Process

### Step 1: Define Attestation Types

```yaml
# Using GV15 (Attestation Patterns) - Types
attestation_types:
  policy_enforcement:
    claim: "Policy {id} was enforced at {time}"
    evidence: audit_event_ids

  no_violations:
    claim: "No violations in period {start} to {end}"
    evidence: audit_summary_hash

  checkpoint_integrity:
    claim: "Checkpoint {id} is intact"
    evidence: hash_verification

  compliance_score:
    claim: "Compliance score was {score} at {time}"
    evidence: scoring_inputs_hash
```

### Step 2: Generate Attestation

```yaml
# Using GV15 (Attestation Patterns) - Generation
attestation:
  id: ATT-{timestamp}-{hash}
  type: policy_enforcement

  claim:
    statement: "Network policy enforced for all requests"
    scope: agents.claude-code
    period: 2026-02-01 to 2026-02-05

  evidence:
    audit_events: [EVT-001, EVT-002, ...]
    events_hash: sha256:{hash}

  signature:
    signer: gas-agent
    algorithm: sha256
    value: {signature}

  timestamp: 2026-02-05T12:00:00Z
```

### Step 3: Store and Index

```yaml
# Using GV15 (Attestation Patterns) - Storage
storage:
  location: _state/gas/attestations/
  format: signed_json

  index:
    by_type: true
    by_period: true
    by_scope: true
```

### Step 4: Verify Attestation

```yaml
# Using GV15 (Attestation Patterns) - Verification
verification:
  steps:
    1: verify_signature
    2: verify_evidence_hash
    3: verify_evidence_exists
    4: verify_claim_matches_evidence

  result:
    valid: true | false
    reason: {explanation}
```

## Attestation Report Example

```yaml
attestation_report:
  period: 2026-02-01 to 2026-02-05

  attestations:
    - type: policy_enforcement
      count: 145
      all_valid: true

    - type: no_violations
      count: 5
      exceptions: 1  # Documented exception

    - type: compliance_score
      scores: [87, 88, 87, 89, 88]
      average: 87.8
```

## Integration with Other Transformations

- **GV4 → GV15**: Audit trails are evidence for attestations
- **GV5 → GV15**: Compliance scores become attestations
- **GV9 → GV15**: Attestations support benchmark claims

## Implementation Checklist

- [ ] Define attestation types
- [ ] Implement generation with signatures
- [ ] Set up secure storage
- [ ] Build verification tools
- [ ] Create attestation reporting

## Common Pitfalls

- Attestations without verifiable evidence
- Missing signatures or timestamps
- Not storing evidence alongside attestation

## Best Practices

- Always include hash of evidence
- Sign every attestation
- Verify attestations regularly

---
*Apply GV15 to prove governance compliance verifiably.*
