---
name: summarize-session
description: Summarize a chat session with structured output, task tracking, and Base120 model references.
parameters:
  - name: format
    type: string
    required: false
    description: Output format (markdown, json, compact)
  - name: export
    type: string
    required: false
    description: Export path for the summary file
---

# Summarize Session Command

Generate a structured summary of the current chat session with task tracking, artifacts created, issues resolved, and Base120 mental model references.

## Usage

```bash
/summarize-session [format] [export-path]
```

## Output Structure (using **DE3** decomposition)

### 1. Session Identity
- Agent name and version
- Date and epoch
- Session duration (if available)

### 2. Tasks Completed (using **SY8** tracking)

| Task | Status | Details |
|------|--------|---------|
| Task name | ✅/❌/⏳ | Brief description |

### 3. Artifacts Created (using **CO5** composition)

List all files created or modified:
- Source files
- Test files
- Configuration files
- State/checkpoint files

### 4. Issues Resolved (using **IN2** premortem + **DE1** root cause)

| Issue | Root Cause | Fix Applied |
|-------|------------|-------------|
| Error description | Why it happened | How it was fixed |

### 5. Base120 Models Applied (using **P1** framing)

List all mental models referenced with their application context:
- **IN1**: How inversion was applied
- **DE3**: How decomposition was used
- etc.

### 6. Pending Items (using **RE2** feedback loops)

List any unfinished tasks or follow-up items.

## Format Options

### Markdown (default)
Full structured markdown with tables and headers.

### JSON
```json
{
  "session": { "agent": "...", "date": "...", "epoch": "..." },
  "tasks": [{ "name": "...", "status": "...", "details": "..." }],
  "artifacts": { "created": [], "modified": [] },
  "issues": [{ "issue": "...", "cause": "...", "fix": "..." }],
  "base120": { "applied": ["IN1", "DE3"], "context": {} },
  "pending": []
}
```

### Compact
Single-line summary for logging:
```
SESSION: agent@date | Tasks: X/Y complete | Artifacts: N | Issues: M resolved | Base120: IN1,DE3,SY8
```

## Export

When `export-path` is provided:
1. Generate summary in specified format
2. Write to `_state/summaries/{export-path}` or absolute path
3. Log export to audit trail

## Example

```bash
/summarize-session markdown "_state/summaries/2026-02-06-gas-session.md"
```

## Workflow Integration

Typical session end flow:

```
[Work Complete] --> /summarize-session
        |
[Review Summary] --> /checkpoint create "session-end"
        |
[Export] --> /summarize-session markdown "session-summary.md"
        |
[SITREP] --> /sitrep "Project" "Phase"
```

## Arguments

$ARGUMENTS:

- `format` - Output format: `markdown` (default), `json`, `compact`
- `export-path` - Optional path to export the summary

## Related Commands

- `/sitrep` - Generate formal situation report
- `/checkpoint` - Create recovery points
- `/learn` - Extract reusable patterns from session
