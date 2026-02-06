---
name: gv14-governance-inheritance
description: Apply GV14 Governance Inheritance to manage policy hierarchies and overrides.
version: 0.0.1
metadata: {"domain":"GV-governance","status":"experimental"}
---

# GV14 Governance Inheritance

Apply the GV14 Governance Inheritance transformation to structure policy hierarchies.

## What is GV14?

**GV14 (Governance Inheritance)** defines how policies inherit, extend, and override each other in a hierarchy.

## When to Use GV14

### Ideal Situations

- Creating organization-wide policies with team overrides
- Managing multi-environment policy variations
- Establishing default policies with specific exceptions

### Trigger Questions

- "Should this team inherit the org policy or have their own?"
- "Can a lower-level policy override this?"
- "What's the policy resolution order?"

## The GV14 Process

### Step 1: Define Hierarchy

```yaml
# Using GV14 (Governance Inheritance) - Hierarchy
hierarchy:
  levels:
    - global       # Organization-wide
    - domain       # code | agents | infrastructure
    - team         # Team-specific
    - project      # Project-specific

  resolution: bottom_up  # Most specific wins
```

### Step 2: Configure Inheritance Rules

```yaml
# Using GV14 (Governance Inheritance) - Inheritance
inheritance:
  network_policy:
    level: global
    inheritable: true
    overridable: false  # Must inherit exactly

  rate_limits:
    level: global
    inheritable: true
    overridable: true
    constraints:
      - "Can only decrease limits, not increase"

  approval_workflow:
    level: domain
    inheritable: true
    overridable: true
    constraints:
      - "Cannot reduce approval requirements"
```

### Step 3: Handle Overrides

```yaml
# Using GV14 (Governance Inheritance) - Overrides
override:
  policy: rate_limits
  parent: global.rate_limits
  level: team.platform

  changes:
    - field: actions_per_minute
      parent_value: 60
      override_value: 30  # More restrictive, allowed

  validation:
    passes: true
    reason: "Override is more restrictive"
```

### Step 4: Resolve Conflicts

```yaml
# Using GV14 (Governance Inheritance) - Resolution
resolution:
  strategy: most_restrictive | most_specific | explicit_priority

  example:
    global.timeout: 30s
    team.timeout: 15s
    resolved: 15s  # Most restrictive wins
```

## Policy Composition Example

```yaml
# Final resolved policy for team.platform
resolved_policy:
  inherits_from:
    - global.base_policy
    - domain.code_policy
  overrides:
    - team.platform_overrides

  final:
    network_policy: global  # Not overridable
    rate_limits: 30/min     # Team override
    approval: global        # Team cannot reduce
```

## Integration with Other Transformations

- **GV14 → GV1**: Inheritance is part of GV1 lifecycle
- **CO5 → GV14**: GV14 applies CO5 composition
- **GV14 → GV11**: Cross-domain via GV11

## Implementation Checklist

- [ ] Define organizational hierarchy levels
- [ ] Configure inheritance rules per policy
- [ ] Implement constraint validation
- [ ] Build resolution logic
- [ ] Document inheritance chains

## Common Pitfalls

- Unclear inheritance rules
- Overrides that weaken security
- Too many hierarchy levels

## Best Practices

- Prefer "most restrictive wins" for security
- Document why policies are not overridable
- Keep hierarchy to 3-4 levels max

---
*Apply GV14 to structure policy inheritance clearly.*
