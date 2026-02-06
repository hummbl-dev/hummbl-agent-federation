# GAS Agent State Directory

This directory contains runtime state for the HUMMBL G.A.S. Agent.

## Structure

```
_state/gas/
├── audit/              # Audit trail storage (GV4)
│   ├── daily/          # Daily JSONL logs
│   ├── indexes/        # Query indexes
│   └── checksums/      # Daily integrity seals
├── checkpoints/        # State snapshots (GV7)
├── attestations/       # Compliance attestations (GV15)
└── learning/           # Learning state (GV10)
```

## Retention

| Directory | Retention | Notes |
|-----------|-----------|-------|
| audit/daily | 90 days hot, 1 year warm, 7 years cold | Append-only |
| checkpoints | 30 days all, 12 months monthly, indefinite tagged | Compressed |
| attestations | Indefinite | Signed |
| learning | Current only | Checkpointed before changes |

## Integrity

- All audit logs use hash chains
- Daily logs are sealed with checksums
- Checkpoints are signed
- Attestations include provenance hashes

## Note

Most contents of this directory are gitignored. Only structure files (.gitkeep, README) are tracked.
