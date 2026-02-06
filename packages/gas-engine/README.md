# @hummbl/gas-engine

HUMMBL G.A.S. Agent Policy Engine - CAES-based governance enforcement.

## Overview

The GAS Engine provides:
- **CAES Classification** - Parse and validate Classification/Authority/Effect/Scope codes
- **Policy Validation** - Validate actions against MRCC/NCC constraints
- **Violation Capture** - Track and analyze policy violations
- **Cross-Domain Enforcement** - Enforce policies across multiple governance domains

## Usage

```typescript
import {
  validateAction,
  enforceAction,
  getViolationStats,
  parseCAES,
} from '@hummbl/gas-engine';

// Load action space
const actionSpace = JSON.parse(fs.readFileSync('configs/gas/action-space.json', 'utf-8'));

// Validate an action
const result = validateAction('flag_violation', actionSpace, {
  actor: 'gas-agent',
  epoch_id: '2026-02-05-001',
});

if (result.valid) {
  console.log('Action allowed');
} else {
  console.log('Action blocked:', result.violations);
}

// Enforce with full audit trail
const enforcement = enforceAction('flag_violation', {
  actionSpace,
  policyRefs: ['gas-policy-v1'],
  base120Refs: ['IN2', 'DE1'],
}, {
  actor: 'gas-agent',
});

console.log('Outcome:', enforcement.outcome);
console.log('Audit:', enforcement.audit_event);
```

## CAES Framework

| Dimension | Range | Description |
|-----------|-------|-------------|
| C (Classification) | C0-C5 | Risk level |
| A (Authority) | A0-A5 | Approval requirement |
| E (Effect) | E0-E5 | Reversibility |
| S (Scope) | S0-S5 | Blast radius |

### Constraint Hierarchy

- **MRCC** (Maximum Capability Constraints) - Hard limits, never exceeded
- **NCC** (Nominal Capability Constraints) - Default operating parameters

## API

### Validation

- `validateAction(actionId, actionSpace, context)` - Validate single action
- `validateActions(actionIds, actionSpace, context)` - Batch validation
- `getAllowedActions(actionSpace)` - Get all currently allowed actions

### Enforcement

- `enforceAction(actionId, config, context)` - Enforce with audit trail
- `enforceCrossDomain(actionId, domains, context)` - Multi-domain enforcement

### Violations

- `captureViolation(violation)` - Record a violation
- `getViolationStats()` - Get violation statistics
- `analyzePatterns()` - Find recurring violation patterns
- `resolveViolation(id, resolution)` - Mark violation as resolved

### CAES Utilities

- `parseCAES(code)` - Parse CAES string to components
- `getLevel(component)` - Extract numeric level (0-5)
- `isWithinConstraints(caes, maxC, maxS, maxE)` - Check constraint bounds
