# LLM Enablement (applying **P1** framing and **SY8** systems thinking)

## CRITICAL: NO API FEES Policy

**All LLM access must use subscription-based or free methods. Direct API access is BLOCKED by default.**

| Access Method | Cost Type | Status |
|---------------|-----------|--------|
| Claude Code (with Claude.ai subscription) | Flat-rate subscription | ALLOWED |
| ChatGPT Plus/Team | Flat-rate subscription | ALLOWED |
| Codex CLI (`chatgpt` auth) | Subscription-backed | ALLOWED |
| Ollama (local) | Free | ALLOWED |
| Grok (X Premium+) | Subscription | ALLOWED |
| Direct API Keys | Per-token fees | **BLOCKED** |

To enable API fees (REQUIRES EXPLICIT OWNER APPROVAL):
```bash
export MOLTBOT_ALLOW_API_FEES=1
```

## Allowed Access Methods

### Anthropic (Subscription-based)

Use Claude Code with a Claude.ai Max or Pro subscription:

```bash
# Claude Code uses your Claude.ai subscription - no API fees
claude --chat
```

**NOT allowed without approval:**
- Direct `ANTHROPIC_API_KEY` usage (incurs per-token fees)

### OpenAI (Subscription-based)

Use ChatGPT Plus subscription or Codex CLI with `chatgpt` auth:

```bash
# Codex with chatgpt auth - uses your ChatGPT Plus subscription
codex --provider chatgpt
```

**NOT allowed without approval:**
- Direct `OPENAI_API_KEY` usage (incurs per-token fees)

### Local Models (Free)

Use Ollama or llama.cpp for completely free local inference:

```bash
# Ollama - free local models
ollama run llama3.2
```

## Configuration Files

### Cost Policy

`configs/cost-policy.json` - Master cost control policy:
- `allow_api_fees: false` (default)
- `allowed_access_methods`: subscription and free only
- `blocked_access_methods`: api-key-direct

### LLM Configs

Both `configs/moltbot/llm.anthropic.json` and `configs/moltbot/llm.openai.json`:
- `enabled: false` (disabled by default)
- `dry_run: true` (dry-run even if enabled)
- `allowed_models: []` (empty - no models enabled)
- `blocked_models: [list]` (all paid API models blocked)
- `cost_policy.allow_api_fees: false`

### Secrets Policy

`configs/secrets-policy.json`:
- API keys moved to `restrictedSecrets`
- Requires `MOLTBOT_ALLOW_API_FEES=1` to use

## Enabling API Access (Requires Owner Approval)

If you absolutely need direct API access (incurs costs):

1. Get explicit owner approval
2. Set environment variable:
   ```bash
   export MOLTBOT_ALLOW_API_FEES=1
   ```
3. Create local override (gitignored):
   ```bash
   # configs/moltbot/llm.anthropic.local.json
   {
     "enabled": true,
     "dry_run": false,
     "allowed_models": ["claude-3-5-sonnet-latest"]
   }
   ```
4. Set API key:
   ```bash
   export MOLTBOT_ANTHROPIC_API_KEY=...
   ```
5. Enable live calls:
   ```bash
   export MOLTBOT_LIVE_LLM_CALLS=1
   ```

## Failure Codes

- `config_disabled` - LLM calls disabled
- `model_not_allowed` - Model not in allowlist
- `model_blocked` - Model in blocklist
- `live_guard_disabled` - Live calls not enabled
- `api_fees_blocked` - API fees not approved
- `auth_missing` - Missing credentials
- `cost_policy_violation` - Violates cost policy

## Routing Policy

`configs/moltbot/llm-routing-policy.json`:
- Prefers: local → subscription → api
- API vendor disabled by default
- Fallback order: ollama → subscription.anthropic → subscription.openai
