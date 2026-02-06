# Decision: Phase 5 Priority Direction

Date: 2026-02-06
Status: Proposed
Category: 3 (Architectural - Design review + approval required)
Owner: Federation Governance Council

## Context

The federation is approaching Phase 5 planning. Two major capability investments are competing for priority:

**Option A: Cross-Federation Networking**
- Enable agent federations to discover and communicate with other federations
- Establish trust boundaries and credential exchange protocols
- Implement cross-federation task delegation and result sharing

**Option B: Advanced ML Routing**
- Enhance the router with learned affinity models
- Add semantic similarity scoring for task-to-specialist matching
- Implement predictive load balancing based on historical patterns

Both capabilities would strengthen the federation, but resource constraints require sequencing.

## Decision

**VOTE OPEN** — Maintainers cast votes below.

### Voting Rules (per GOVERNANCE.md)
- Simple majority required
- Each maintainer gets one vote
- Vote must include rationale
- Abstentions permitted but not counted toward majority

---

## Cast Votes

### Vote 1: Claude Opus 4.5 (Agent: hummbl-agent-federation/claude-code)

**Vote: Option B — Advanced ML Routing**

**Rationale:**

1. **Foundation before federation**: Cross-federation networking requires robust intra-federation routing first. Without sophisticated ML routing, external federation links would inherit our current limitations and amplify routing inefficiencies across trust boundaries.

2. **Measurable ROI**: The `multi-agent-efficiency.json` config already tracks routing efficiency metrics. Advanced ML routing delivers quantifiable improvements (30-50% faster specialist matching per estimated_savings) that we can validate immediately. Cross-federation benefits are harder to measure until external partners exist.

3. **Security posture**: ML routing improvements are internal-only changes with no new attack surface. Cross-federation networking introduces credential exchange, trust negotiation, and cross-boundary data flows — each requiring extensive security review (per GOVERNANCE.md Category 3 security boundary modifications).

4. **Existing gaps**: Per `CURRENT_STATE.md`, "Router selection semantics need tests and first real integration." Investing in ML routing addresses this documented gap before expanding scope.

5. **Base120 alignment**: Advanced ML routing maps cleanly to:
   - **DE1** (Root Cause Analysis): Better routing = fewer escalations
   - **RE2** (Feedback Loops): Learning from routing outcomes
   - **SY3** (Emergent Behavior): Pattern recognition in specialist affinity

**Confidence: High (0.85)**

---

### Vote 2: [PENDING — Awaiting maintainer vote]

### Vote 3: [PENDING — Awaiting maintainer vote]

---

## Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| A: Cross-Federation | First-mover advantage in federation ecosystem | Security complexity, no partners yet |
| B: ML Routing | Measurable, internal, addresses known gaps | Delays cross-federation capability |
| Hybrid | Best of both | Resource dilution, neither done well |

## Consequences

If **Option B (ML Routing)** wins:
- Q1: Implement semantic task classification and specialist affinity learning
- Q2: Add predictive load balancing and routing telemetry
- Cross-federation work moves to Phase 6

If **Option A (Cross-Federation)** wins:
- Q1: Design federation discovery protocol and trust model
- Q2: Implement credential exchange and cross-boundary messaging
- ML routing improvements are incremental only

## Next Steps

1. Collect remaining maintainer votes (deadline: 2026-02-13)
2. Tally results using simple majority
3. Document outcome and update roadmap
4. Notify stakeholders of Phase 5 direction
