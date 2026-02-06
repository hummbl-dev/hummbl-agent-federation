# HUMMBL Agent Workspace

AI agent coordination workspace using Base120 mental models for governed execution.

## Commands

```bash
# Session orchestration
scripts/orchestrate.sh              # Open run + generate prompts
scripts/orchestrate.sh --force      # Overwrite existing day's prompts

# Governed execution (commands must be in allowlist)
scripts/run-cmd.sh --runner claude-code -- git status --porcelain
scripts/run-cmd.sh --runner codex -- <command>

# SITREP generation
scripts/generate-sitrep.sh

# Validation
scripts/e2e-validate.sh --mode offline    # No vendor calls
scripts/e2e-validate.sh --mode live       # Requires API keys

# Linting
scripts/lint-sitrep.sh /path/to/SITREP.md
scripts/lint-evidence.sh
scripts/lint-network-policy.sh
scripts/lint-secrets-policy.sh
scripts/lint-secret-scan.sh
scripts/lint-base120-skill-map.sh
node scripts/validate-base120-refs.js
node scripts/validate-base120-canonical.js
```

## Project Structure

- `agents/` - Claude Code agents (architect, planner, sitrep-generator, etc.)
- `commands/` - Slash commands (sitrep, plan-with-base120, verify-hummbl, etc.)
- `skills/` - Base120 transformations + integration skills
  - `P-perspective/`, `IN-inversion/`, `CO-composition/`
  - `DE-decomposition/`, `RE-recursion/`, `SY-systems/`
- `packages/` - Kernel interfaces, registry, router, runners, adapters
- `configs/` - Policies and runner configs (codex, grok, moltbot)
- `scripts/` - Automation and lint scripts
- `_state/` - Run logs, artifacts, evidence (gitignored runs)
- `docs/` - Workflows, schemas, checklists

## Governed Execution

Commands run via `scripts/run-cmd.sh` must be allowlisted in `configs/process-policy.allowlist`.

Artifacts written to: `_state/runs/YYYY-MM-DD/artifacts/`
Prompts written to: `_state/runs/YYYY-MM-DD/prompts/`

## Key Policies

| Policy File | Purpose |
|-------------|---------|
| `configs/process-policy.allowlist` | Allowed shell commands |
| `configs/network-policy.json` | Network request constraints |
| `configs/secrets-policy.json` | Secret handling rules |
| `configs/experiment-policy.json` | Controlled experiment rules |

## Base120 Transformations

Six transformation domains, 20 models each (120 total):

| Code | Domain | Example |
|------|--------|---------|
| P | Perspective | P1-P20 |
| IN | Inversion | IN1-IN20 |
| CO | Composition | CO1-CO20 |
| DE | Decomposition | DE1-DE20 |
| RE | Recursion | RE1-RE20 |
| SY | Systems | SY1-SY20 |

Canonical source: `docs/base120.v1.0.canonical.json`

## Hard Rules

### Continuous Self-Improvement (MANDATORY)

**You MUST proactively create new skills when:**
1. You solve a problem that could recur (pattern detection)
2. You build a workflow that others could use (automation)
3. You discover a gap in existing skills (coverage)
4. A task requires multiple steps that could be encapsulated (composition)
5. The user asks for something that doesn't have a skill yet

**Skill Creation Triggers:**
- "If a skill doesn't exist for this, make one" → CREATE SKILL
- Repeated similar tasks in a session → CREATE SKILL
- Complex multi-step process completed → CREATE SKILL
- User says "that was useful" → Consider CREATE SKILL

**Skill Location:**
- Commands: `commands/<name>.md`
- Skills: `skills/<name>/SKILL.md`

**Daily Learning Mindset:**
- Each session should leave the codebase better than you found it
- Document patterns as skills, not just solutions
- Skills are your memory across sessions
- When in doubt, create the skill - it's easier to delete than to recreate

**Quality Bar:**
- Skills must have clear trigger phrases
- Skills must follow existing patterns (see `skills/session-summary/SKILL.md`)
- Skills must reference Base120 models where applicable

## Gotchas

- **Governed execution required** - Don't run arbitrary commands; use `scripts/run-cmd.sh`
- **Allowlist first** - Add commands to `configs/process-policy.allowlist` before execution
- **State is gitignored** - `_state/runs/*` not committed; only `.gitkeep` preserved
- **Evidence import** - Use `scripts/import-observation.sh` for governed evidence
- **No servers** - `scripts/lint-no-server.sh` enforces no control plane servers
- **API keys optional** - Claude Code works with Claude.ai subscription (no `ANTHROPIC_API_KEY` needed)

## Runners

| Runner | Config Location | Notes |
|--------|-----------------|-------|
| claude-code | `configs/claude-code/` | Primary runner |
| codex | `configs/codex/` | Can use `chatgpt` auth (no API key) |
| grok | `configs/grok/` | Prompt packet generation |

## Workflow

1. `scripts/orchestrate.sh` - Start session, generate prompts
2. Work with agents/commands as needed
3. `scripts/generate-sitrep.sh` - Document session results
4. `scripts/lint-sitrep.sh` - Validate SITREP format
5. Commit non-state artifacts

## File Conventions

- Agents: `agents/*.md` (markdown with frontmatter)
- Commands: `commands/*.md` (slash command definitions)
- Skills: `skills/<domain>/<id>.md` or `skills/<name>/`
- Configs: `configs/<runner>/` or `configs/*.json`

## Tool Selection & Routing

**Code Navigation & Search**
- **Symbol/refactoring** (find class, rename function, etc.) → Serena (`find_symbol`, `rename_symbol`, `replace_symbol_body`)
- **Semantic code search** (how does auth work? where is error handling?) → Task tool with `subagent_type=Explore`
- **PR code review comments** (Greptile reviews, trigger reviews) → Greptile MCP
- **Simple text/pattern search** (grep for string, find file by name) → Built-in Grep/Glob
- **Documentation search** (library docs, API references) → Context7 MCP

**Development & Deployment**
- **Deploy to Vercel** → Vercel plugin
- **Firebase setup** → Firebase MCP
- **Supabase operations** → Supabase plugin
- **Error monitoring** → Sentry plugin
- **Payment integration** → Stripe plugin

**Project Management**
- **Linear issues** → Linear MCP
- **Jira/Confluence** → Atlassian plugin
- **Notion pages** → Notion MCP
- **GitHub operations** → GitHub plugin
- **GitLab operations** → GitLab plugin

**Code Quality & Review**
- **PR review** → pr-review-toolkit plugin
- **Code review** → code-review plugin
- **Refactoring** → code-simplifier plugin
- **Security audit** → security-guidance plugin

**AI/ML & Data**
- **Hugging Face models/datasets** → huggingface-skills plugin
- **Vector search** → Pinecone plugin
- **Up-to-date library docs** → Context7 MCP

**Design & Frontend**
- **Figma implementation** → Figma plugin/MCP
- **Frontend design patterns** → frontend-design plugin
- **UI component generation** → frontend-design plugin

**Workflow Automation**
- **Git commits** → commit-commands plugin
- **Plugin development** → plugin-dev plugin
- **Agent development** → agent-sdk-dev plugin
- **Hook creation** → hookify plugin

**Default Hierarchy**
When multiple tools could work, prefer in this order:
1. Specialized tool (if it exists for the domain)
2. MCP server (for integrations)
3. Built-in tool (Grep/Glob/Read/Edit)

**HUMMBL-Specific**
- **Base120 transformations** → Use `/plan-with-base120` command or `apply-transformation` skill
- **SITREP generation** → Use `sitrep-generator` agent or `/sitrep` command
- **Governed execution** → Always use `scripts/run-cmd.sh` wrapper

## Routing Examples (From Actual Infrastructure)

### Example 1: Model Fallback Routing
```
Task: "Generate a SITREP for today's work"

Routing Decision (OpenClaw pattern):
1. Try primary: claude-sonnet-4-20250514
2. If rate-limited → fallback to claude-opus-4-5-20251101
3. If still unavailable → fallback to gpt-4o
4. Last resort → ollama/llama3.2 (local)
```

### Example 2: Policy-Based Skill Routing
```
Task: "Apply P1 transformation to this problem"

Control Plane Decision (hummbl-agent pattern):
1. Match authority_scope: "SKILL"
2. Evaluate policy rules (priority-sorted)
3. Check required_constraints: ["Base120_canonical_source"]
4. Select route: "skills/P-perspective/P1.md"
5. Emit provenance: {bundle_id, matched_rules, reason_codes}
```

### Example 3: Multi-Agent Delegation
```
Task: "Research this codebase AND write documentation in parallel"

Routing Decision (OpenClaw multi-agent pattern):
1. Soma (main agent) handles research
2. Soma delegates to Echo (sibling) for documentation
3. Both work concurrently (maxConcurrent: 4)
4. Results merge back to Soma for final response
```

### Example 4: Governed Execution Routing
```
Task: "Run git status"

Routing Decision (hummbl-agent governed pattern):
1. Check configs/process-policy.allowlist for "git status"
2. If allowed → route to scripts/run-cmd.sh wrapper
3. Wrapper applies sandbox constraints
4. Emit artifact to _state/runs/YYYY-MM-DD/
5. NEVER execute commands directly without allowlist check
```

### Example 5: Capability-Based Tool Selection
```
Task: "Find all references to the calculateTotal function"

Routing Decision (hummbl-agent capability filtering):
1. Parse intent: symbol reference query
2. Match against capabilities:
   - Serena: {network: none, exec: read-only, triggers: ["find symbol", "references"]}
   - Explore Agent: {network: none, exec: none, triggers: ["how does", "where is"]}
   - Built-in Grep: {network: none, exec: none, triggers: ["text search"]}
3. Score matches:
   - Serena: 0.9 (perfect capability match for symbol references)
   - Explore Agent: 0.6 (broader search, good for understanding)
   - Grep: 0.3 (misses symbol context)
4. Select: Serena.find_referencing_symbols
5. Rationale: "Symbol-level operation, read-only, no network needed"
```

### Example 6: Dispatch-Based Routing
```
Task: User message from WhatsApp group

Routing Decision (OpenClaw dispatch pattern):
1. Extract context: {channel: "whatsapp", surface: "group", provider: "baileys"}
2. Apply policy: {dmPolicy: "allowlist", groupPolicy: "allowlist"}
3. Check allowlist for sender
4. Route to appropriate handler based on message type
5. Apply debounce (debounceMs: 0 for WhatsApp)
```

## Plugin Capability Matrix

| Plugin | Network | Exec | Best For | Fallback To |
|--------|---------|------|----------|-------------|
| Serena | none | read-only | Symbol nav, refactoring | Built-in Grep |
| Greptile | external | none | PR code review (comments, triggers) | Manual review |
| Explore Agent | none | none | Semantic code questions | Serena, then Grep |
| Pinecone | external | none | Vector/embedding search | N/A |
| Context7 | external | none | Library documentation | WebSearch |
| Vercel | external | write | Deployments | Manual deploy |
| Firebase | external | write | Backend setup | Manual setup |
| Linear | external | write | Issue management | Manual tracking |
| GitHub | external | write | Git operations | Built-in Bash |

## Routing Decision Process

When facing a task with multiple tool options:

1. **Parse Intent** - What is the user actually asking for?
2. **Match Capabilities** - Which tools CAN do this?
3. **Score Matches** - Which tool is BEST suited?
4. **Check Policies** - Is the tool allowed in this context?
5. **Select Route** - Pick the highest-scoring allowed tool
6. **Explain** - State which tool and why
7. **Execute** - Use the selected tool
8. **Fallback** - If failed, try next-best option

This process mirrors the deterministic router in `openclaw/hummbl-agent/packages/router/`.
