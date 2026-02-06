---
name: session-summary
description: Summarize the current chat session with structured output including tasks, artifacts, issues resolved, and Base120 mental model references.
metadata: {"openclaw":{"emoji":"📋","requires":{}}}
---

# Session Summary

Generate a structured summary of the current chat session for documentation, handoff, or audit purposes.

## When to use (trigger phrases)

Use this skill immediately when the user asks any of:

- "summarize this session"
- "summarize this chat"
- "what did we do?"
- "session summary"
- "wrap up this session"
- "document what we did"
- "create a session report"

## Output Structure

The summary follows **DE3** (decomposition) principles with these sections:

### 1. Session Identity
```markdown
**Agent**: [Agent name and version]
**Date**: [Session date]
**Epoch**: [If applicable]
```

### 2. Tasks Completed (**SY8** tracking)
```markdown
| Task | Status | Details |
|------|--------|---------|
| Task name | ✅/❌/⏳ | Brief description |
```

### 3. Artifacts Created (**CO5** composition)
- Source files created/modified
- Test files
- Configuration files
- State/checkpoint files

### 4. Issues Resolved (**IN2** + **DE1**)
```markdown
| Issue | Root Cause | Fix Applied |
|-------|------------|-------------|
| Error description | Why it happened | How it was fixed |
```

### 5. Base120 Models Applied (**P1** framing)
List all mental models referenced with context:
- **IN1**: Application context
- **DE3**: Application context

### 6. Pending Items (**RE2** feedback)
Any unfinished tasks or follow-up items.

## Format Options

### Markdown (default)
Full structured markdown with tables and headers.

### Compact
Single-line for logging:
```
SESSION: agent@date | Tasks: X/Y | Artifacts: N | Issues: M | Base120: IN1,DE3
```

### JSON
```json
{
  "session": { "agent": "...", "date": "..." },
  "tasks": [{ "name": "...", "status": "...", "details": "..." }],
  "artifacts": { "created": [], "modified": [] },
  "issues": [{ "issue": "...", "cause": "...", "fix": "..." }],
  "base120": ["IN1", "DE3"],
  "pending": []
}
```

## Export

To save the summary:
```bash
# Write to _state/summaries/
/summarize-session markdown "_state/summaries/YYYY-MM-DD-session.md"
```

## Workflow Integration

```
[Work Complete] --> /summarize-session
        |
[Review] --> /checkpoint create "session-end"
        |
[SITREP] --> /sitrep "Project" "Phase"
```

## Example Output

```markdown
## Session Summary

### Session Identity
**Agent**: HUMMBL G.A.S. Agent v1.0.0
**Date**: 2026-02-06
**Epoch**: 2026-02-05-001

### Tasks Completed

| Task | Status | Details |
|------|--------|---------|
| Create checkpoint | ✅ | Initial baseline established |
| Run tests | ✅ | 89 tests passing |
| Fix API mismatches | ✅ | 19 failures → 0 failures |

### Base120 Models Applied
- **IN1**: Constraint inversion for validation
- **DE3**: Test decomposition
- **SY8**: Feedback loops for iteration

### Pending Items
None - all tasks completed.
```

## Related

- `/sitrep` - Formal situation report
- `/checkpoint` - Create recovery points
- `/learn` - Extract reusable patterns
