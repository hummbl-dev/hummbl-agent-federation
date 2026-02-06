---
name: gv4-audit-trail-design
description: Apply GV4 Audit Trail Design to structure provenance records for governance actions.
version: 0.0.1
metadata: {"domain":"GV-governance","status":"experimental"}
---

# GV4 Audit Trail Design

Apply the GV4 Audit Trail Design transformation to create comprehensive, tamper-evident audit records.

## What is GV4?

**GV4 (Audit Trail Design)** defines the schema, storage, and integrity mechanisms for governance audit trails, ensuring every action is traceable and verifiable.

## When to Use GV4

### Ideal Situations

- Designing audit infrastructure for a new system
- Meeting compliance requirements (SOC2, ISO 27001)
- Investigating governance incidents

### Trigger Questions

- "What should we log for this action?"
- "How do we prove this wasn't tampered with?"
- "How long must we retain these records?"

## The GV4 Process

### Step 1: Define Event Schema

```yaml
# Using GV4 (Audit Trail Design) - Schema
audit_event:
  id: uuid
  timestamp: ISO8601
  actor: {agent|human}:{id}
  action: {type}
  target: {resource_path}
  context:
    policy_ref: {id}
    trigger: {reason}
  decision:
    outcome: allowed | denied | escalated
    rationale: {text}
  provenance:
    input_hash: sha256:{hash}
    output_hash: sha256:{hash}
```

### Step 2: Implement Integrity

```yaml
# Using GV4 (Audit Trail Design) - Integrity
integrity:
  hash_chain: true  # Each entry references previous
  daily_seal: true  # EOD tamper-evident seal
  external_witness: optional  # Third-party attestation
```

### Step 3: Configure Storage

```yaml
# Using GV4 (Audit Trail Design) - Storage
storage:
  location: _state/gas/audit/
  format: jsonl  # Append-only
  indexes:
    - by-policy
    - by-actor
    - by-outcome
  retention:
    hot: 90 days
    warm: 1 year
    cold: 7 years
```

### Step 4: Enable Queries

```yaml
# Using GV4 (Audit Trail Design) - Query capabilities
queries:
  - by_time_range: [start, end]
  - by_actor: {actor_id}
  - by_policy: {policy_id}
  - by_outcome: {outcome}
  - full_text: {search_term}
```

## Integration with Other Transformations

- **All GV → GV4**: Every GV action produces audit events
- **GV4 → GV15**: Audit records support GV15 attestations
- **GV4 → GV18**: Audit data feeds GV18 governance metrics

## Implementation Checklist

- [ ] Define comprehensive event schema
- [ ] Implement hash chain integrity
- [ ] Configure retention policies
- [ ] Build query interfaces
- [ ] Test tamper detection

## Common Pitfalls

- Logging too little (missing context)
- Logging too much (performance/storage)
- Not testing integrity verification

## Best Practices

- Always include provenance hashes
- Use append-only storage
- Seal daily logs with checksums
- Regularly verify integrity

---
*Apply GV4 to create audit trails that prove governance integrity.*
