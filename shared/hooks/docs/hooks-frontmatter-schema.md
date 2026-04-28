# Hooks Frontmatter Schema for SKILL.md Files

> **Version**: 5.0.0
> **Last Updated**: 2026-01-24

This document defines the hooks frontmatter schema for sf-skills SKILL.md files. Starting with v5.0.0, hooks are defined directly in each skill's SKILL.md frontmatter instead of separate `hooks/hooks.json` files.

---

## Quick Reference

```yaml
---
name: sf-apex
description: >
  Your skill description here
license: MIT
metadata:
  version: "1.0.0"
  author: "Author Name"
hooks:
  SessionStart:
    - type: command
      command: "${SHARED_HOOKS}/scripts/session-init.py"
      timeout: 5000
  PreToolUse:
    - matcher: Bash
      hooks:
        - type: command
          command: "${SHARED_HOOKS}/scripts/validator-dispatcher.py"
          timeout: 5000
  PostToolUse:
    - matcher: "Write|Edit"
      hooks:
        - type: command
          command: "${SKILL_HOOKS}/apex-lsp-validate.py"
          timeout: 15000
---
```

---

## Hook Event Types

| Event | When It Fires | Use Cases |
|-------|---------------|-----------|
| `SessionStart` | Claude Code session begins | Environment validation, org authentication checks |
| `PreToolUse` | Before a tool executes | Guardrails, input validation, auto-fix |
| `PostToolUse` | After a tool completes | Validation, notifications |
| `PermissionRequest` | User permission needed | Auto-approval for safe operations |

---

## Path Variables

These variables are resolved at runtime:

| Variable | Resolves To | Example |
|----------|-------------|---------|
| `${SHARED_HOOKS}` | `~/.claude/hooks` | Shared hook scripts |
| `${SKILL_HOOKS}` | `~/.claude/skills/<skill>/hooks/scripts` | Skill-specific scripts |
| `${CLAUDE_PLUGIN_ROOT}` | Current skill's root directory | Same as SKILL_HOOKS parent |

---

## Hook Structure

### Basic Hook (No Matcher)

For events that don't need tool matching (SessionStart):

```yaml
hooks:
  SessionStart:
    - type: command
      command: "${SHARED_HOOKS}/scripts/session-init.py"
      timeout: 5000
```

### Matcher-Based Hook

For tool-specific events (PreToolUse, PostToolUse):

```yaml
hooks:
  PostToolUse:
    - matcher: "Write|Edit"  # Regex pattern for tool names
      hooks:
        - type: command
          command: "python3 ${SKILL_HOOKS}/validate.py"
          timeout: 15000
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python3 ${SKILL_HOOKS}/parse-output.py"
          timeout: 30000
```

---

## Hook Configuration Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | `"command"` or `"prompt"` |
| `command` | string | If type=command | Shell command to execute |
| `prompt` | string | If type=prompt | LLM prompt for evaluation |
| `timeout` | number | No | Timeout in milliseconds (default: 5000) |
| `matcher` | string | For tool hooks | Regex pattern for tool names |

---

## Common Hook Patterns

### 1. Environment Validation (SessionStart)

```yaml
hooks:
  SessionStart:
    - type: command
      command: "${SHARED_HOOKS}/scripts/session-init.py"
      timeout: 5000
```

### 2. PreToolUse Guardrails

```yaml
hooks:
  PreToolUse:
    - matcher: Bash
      hooks:
        - type: command
          command: "python3 ${SHARED_HOOKS}/scripts/validator-dispatcher.py"
          timeout: 5000
```

### 3. Code Validation (PostToolUse)

```yaml
hooks:
  PostToolUse:
    - matcher: "Write|Edit"
      hooks:
        - type: command
          command: "python3 ${SKILL_HOOKS}/apex-lsp-validate.py"
          timeout: 15000
        - type: command
          command: "python3 ${SKILL_HOOKS}/post-tool-validate.py"
          timeout: 120000
```

### 4. Test/Build Output Parsing (PostToolUse on Bash)

```yaml
hooks:
  PostToolUse:
    - matcher: Bash
      hooks:
        - type: command
          command: "python3 ${SKILL_HOOKS}/parse-test-results.py"
          timeout: 30000
```

---

## Complete Example: sf-apex

```yaml
---
name: sf-apex
description: >
  Generates and reviews Salesforce Apex code with 2025 best practices and 150-point
  scoring. Use when writing Apex classes, triggers, test classes, batch jobs, or
  reviewing existing Apex code for bulkification, security, and SOLID principles.
license: MIT
metadata:
  version: "1.0.0"
  author: "Jag Valaiyapathy"
  scoring: "150 points across 8 categories"
hooks:
  SessionStart:
    - type: command
      command: "${SHARED_HOOKS}/scripts/session-init.py"
      timeout: 5000
  PreToolUse:
    - matcher: Bash
      hooks:
        - type: command
          command: "python3 ${SHARED_HOOKS}/scripts/validator-dispatcher.py"
          timeout: 5000
  PostToolUse:
    - matcher: "Write|Edit"
      hooks:
        - type: command
          command: "python3 ${SKILL_HOOKS}/apex-lsp-validate.py"
          timeout: 15000
        - type: command
          command: "python3 ${SKILL_HOOKS}/post-tool-validate.py"
          timeout: 120000
---
```

---

## Hook Output Formats

### PreToolUse Output (Block/Allow/Modify)

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "DELETE without WHERE detected",
    "updatedInput": {
      "command": "sf data query --query 'SELECT Id FROM Account LIMIT 200'"
    },
    "additionalContext": "Warning message for user"
  }
}
```

### PostToolUse Output (Context Injection)

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "Validation passed. Next: /sf-testing"
  }
}
```

### PermissionRequest Output (Auto-Approval)

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "autoApprove": true,
    "reason": "Safe read-only operation"
  }
}
```

---

## Migration from hooks/hooks.json

### Before (hooks/hooks.json):

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write",
      "hooks": [{
        "type": "command",
        "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate.py"
      }]
    }]
  }
}
```

### After (SKILL.md frontmatter):

```yaml
---
name: my-skill
hooks:
  PostToolUse:
    - matcher: Write
      hooks:
        - type: command
          command: "python3 ${SKILL_HOOKS}/validate.py"
          timeout: 15000
---
```

### Migration Steps

1. Open skill's `hooks/hooks.json`
2. Copy hook configuration
3. Convert JSON to YAML format
4. Add to SKILL.md frontmatter under `hooks:` key
5. Update path variables (`${CLAUDE_PLUGIN_ROOT}` → `${SKILL_HOOKS}`)
6. Delete `hooks/hooks.json` file (keep `hooks/scripts/` directory)

---

## Troubleshooting

### Hook Not Firing

1. Check YAML syntax (use a YAML validator)
2. Verify path variables resolve correctly
3. Check timeout isn't too short
4. Ensure script is executable (`chmod +x script.py`)

### Hook Failing Silently

1. Add debug output to script (`print("DEBUG: ...", file=sys.stderr)`)
2. Check `/tmp/sf-skills-*.log` for errors
3. Test script manually: `echo '{}' | python3 script.py`

### Path Resolution Issues

1. Use absolute paths for debugging
2. Check `${SHARED_HOOKS}` resolves to: `~/.claude/hooks`
3. Check `${SKILL_HOOKS}` resolves to: `~/.claude/skills/<skill>/hooks/scripts`

---

## Best Practices

1. **Keep timeouts reasonable**: 5s for simple checks, 15-30s for validation, 120s max for complex operations
2. **Fail gracefully**: Hooks should never break the user experience - exit 0 on errors
3. **Use shared hooks**: For common patterns, use `${SHARED_HOOKS}` scripts
4. **Order matters**: Hooks execute in order - put fast checks first
5. **Cache when possible**: Registry loading, file parsing - cache to reduce latency
6. **Provide context**: Output helpful messages, not just pass/fail

---

## Related Documentation

- [skills-registry.json](../skills-registry.json) - Skill registry and metadata
- [shared/hooks/README.md](../README.md) - Shared hooks documentation
- [Claude Code Hooks](https://docs.anthropic.com/claude-code/hooks) - Official hooks reference
