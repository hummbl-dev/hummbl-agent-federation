# Federation

Universal Model Router for Governance-as-a-Service (GaaS)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> *"One API for 50+ model providers. Quality-first routing with enterprise governance."*

---

## Features

- **Universal Router** — Route tasks to optimal providers across 50+ options
- **Quality-First** — Weights: Quality (50%) > Speed (30%) > Cost (10%) > Reliability (10%)
- **Enterprise Governance** — SOC2, GDPR, HIPAA compliance built-in
- **Cost Optimization** — Automatic savings vs single-provider strategies
- **Health Monitoring** — Circuit breakers, failover, real-time dashboards
- **Multi-Tenant** — SaaS-ready with tenant isolation

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/hummbl-dev/hummbl-agent-federation.git
cd hummbl-agent-federation

# Install with Poetry
poetry install

# Or with pip
pip install -e .
```

### Initialize a Project

```bash
# Create a new federation project
federation init

# This creates:
# config/
# └── providers.yaml    # Your provider configurations
```

### Route Your First Task

```bash
# Route a task (dry-run)
federation route "Implement JWT authentication" --dry-run

# Output:
# ┌─ Routing Decision ──────────────────────────────┐
# │ deepseek                                        │
# │                                                 │
# │ Confidence: 92%                                 │
# │ Est. Cost: $0.05                                │
# │ Est. Latency: 2100ms                            │
# └─────────────────────────────────────────────────┘

# See why this provider was chosen
federation route explain "Implement JWT authentication"
```

### List Providers

```bash
federation provider list

# Output:
# ╭─ Federation Providers ────────────────────────╮
# │ Provider    Status  Models  Latency  Cost/Mtok │
# ├────────────────────────────────────────────────┤
# │ 🅾️ OpenAI    ●       12      1.2s    $2.50     │
# │ 🅰️ Anthropic  ●        8      1.5s    $3.00     │
# │ 🐋 DeepSeek   ●        4      2.1s    $0.14     │
# │ ⚡ Groq       ●       15      0.3s    $0.59     │
# │ 🏠 Ollama     ●        3      0.1s    $0.00     │
# ╰────────────────────────────────────────────────╯
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         TASK INPUT                               │
│    "Implement authentication middleware with JWT"               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FEDERATION ROUTER                            │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Intent    │  │   Filter    │  │        Score            │ │
│  │  Classifier │─▶│   Engine    │─▶│   Quality: 50%          │ │
│  │             │  │             │  │   Speed:   30%          │ │
│  │ code_impl   │  │ GDPR? SOC2? │  │   Cost:    10%          │ │
│  └─────────────┘  └─────────────┘  │   Reliability: 10%      │ │
│                                     └─────────────────────────┘ │
└────────────────────┬────────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌──────────────┐ ┌──────────┐ ┌─────────────┐
│   DeepSeek   │ │   Groq   │ │   OpenAI    │
│  $0.05/task  │ │ $0.12/t  │ │  $2.50/task │
│  Quality:88% │ │ Quality  │ │  Quality:95%│
└──────────────┘ └──────────┘ └─────────────┘
```

---

## Provider Support

### Tier 1: Frontier Labs
- **OpenAI** — GPT-4o, o1, o3-mini
- **Anthropic** — Claude 3.5/4 Sonnet, Opus
- **Google DeepMind** — Gemini 1.5/2.0 Pro
- **Meta** — Llama 3.1/3.2/3.3 (via aggregators)
- **xAI** — Grok-2, Grok-3
- **Cohere** — Command R, Embed
- **Mistral AI** — Mistral Large, Codestral

### Tier 2: Chinese Frontier
- **DeepSeek** — V3, R1 (reasoning)
- **Alibaba** — Qwen2.5 series
- **Moonshot AI** — Kimi (long context)
- And 7 more...

### Tier 3: Cloud Aggregators
- **OpenRouter** — 300+ models, one API
- **Together AI** — Fast inference
- **Groq** — 800+ tokens/sec
- **Fireworks** — Production inference
- And 6 more...

### Tier 4-7: Cloud Marketplaces, Specialized, Open Source, Emerging
50+ total providers supported.

---

## Governance-as-a-Service

### Compliance Policies

```yaml
policy:
  name: soc2-strict
  rules:
    - all_requests_logged: true
    - pii_exclusion_required: true
    - data_residency: [us, eu]
    - retention_days: 2555  # 7 years
    - encryption: aes-256-gcm
```

### Enterprise Features

- **Immutable Audit Trails** — Every request logged with provenance
- **Data Residency** — Route to providers in specific regions
- **PII Detection** — Automatic exclusion of sensitive data
- **RBAC** — Role-based access control per tenant
- **Budget Controls** — Hard limits with alerts

---

## Development

### Setup

```bash
# Install dev dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src

# Format code
poetry run black src/ tests/
poetry run ruff check src/ tests/

# Type checking
poetry run mypy src/
```

### Project Structure

```
federation/
├── src/
│   ├── registry/          # Provider registry
│   │   ├── models.py      # Provider dataclasses
│   │   ├── loader.py      # Config loading
│   │   └── store.py       # SQLite/Redis storage
│   ├── engine/            # Routing engine
│   │   ├── classifier.py  # Intent classification
│   │   ├── router.py      # Main routing logic
│   │   └── cost.py        # Cost tracking
│   ├── adapters/          # Provider API adapters
│   ├── governance/        # GaaS policy engine
│   ├── telemetry/         # Observability
│   ├── security/          # Vault, encryption
│   ├── tenant/            # Multi-tenancy
│   ├── cli/               # Command line interface
│   └── patterns/          # MapReduce, Debate, etc.
├── tests/                 # Test suite
├── docs/                  # Documentation
└── config/                # Provider configurations
```

---

## Roadmap

### Phase 1: Foundation ✅
- [x] Provider registry
- [x] Routing engine
- [x] CLI scaffolding
- [ ] Provider adapters (in progress)

### Phase 2: Intelligence
- [ ] Adaptive learning
- [ ] Real-time dashboard
- [ ] Cost optimization
- [ ] A/B testing framework

### Phase 3: Scale
- [ ] Kubernetes deployment
- [ ] Multi-region routing
- [ ] Advanced security
- [ ] Workflow patterns

### Phase 4: Ecosystem
- [ ] SDKs (Python, TS, Go)
- [ ] IDE extensions
- [ ] Consulting methodology
- [ ] Training curriculum

---

## Business Model

### Service Tiers

| Tier | Price | Target | Features |
|------|-------|--------|----------|
| **Community** | Free | Developers | 1K requests/mo, 5 providers |
| **Pro** | $99/mo | Startups | 100K requests, 20 providers |
| **Enterprise** | Custom | Large orgs | Unlimited, SOC2, consulting |
| **Consulting** | Project | Transformation | Base120 implementation |

### Revenue Split
- Platform Usage: 70%
- Consulting Services: 20%
- Education: 10%

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT License — See [LICENSE](LICENSE)

---

## Contact

- **GitHub:** [hummbl-dev/hummbl-agent-federation](https://github.com/hummbl-dev/hummbl-agent-federation)
- **Email:** reuben@hummbl.io

---

<p align="center">
  <em>Built with ❤️ by the HUMMBL Agent Federation</em>
</p>
