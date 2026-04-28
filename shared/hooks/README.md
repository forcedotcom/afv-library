# Shared Hooks Architecture

This directory contains the centralized hook system for sf-skills, providing intelligent skill discovery and guardrails across all 19 Salesforce skills.

## Overview

```
shared/hooks/
├── skills-registry.json              # Single source of truth for all skill metadata
├── scripts/
│   ├── validator-dispatcher.py       # PostToolUse hook (routes to skill-specific validators)
│   ├── session-init.py               # Session initialization hook
│   ├── naming_validator.py           # Naming convention enforcement
│   ├── security_validator.py         # Security pattern detection
│   └── stdin_utils.py               # Shared stdin reading utility
├── docs/
│   ├── hook-lifecycle-diagram.md     # Visual lifecycle diagram with all SF-Skills hooks
│   └── hooks-frontmatter-schema.md   # Hook configuration format (legacy reference)
└── README.md                         # This file
```

## Architecture v5.0.0

### Proactive vs Reactive Hooks

```
┌─────────────────────────────────────────────────────────────────────────┐
│ PROACTIVE LAYER (LLM-first)                                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  User Request → PreToolUse Prompt Hook → ALLOW (+ warnings) → Executes │
│                       ↓                                                 │
│              Haiku evaluates command for:                                │
│              • Deprecated sfdx commands                                 │
│              • Old API versions (< v56)                                 │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ REACTIVE LAYER                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Tool Executes → PostToolUse Hook → Validate                            │
│                        ↓                                                │
│              validator-dispatcher.py                                     │
│                        ↓                                                │
│        ┌─────────────────────────────────┐                              │
│        │ Match file_path → run validator │                              │
│        │ .cls → apex-lsp + scoring       │                              │
│        │ .flow-meta.xml → flow-validate  │                              │
│        │ .js (lwc/) → lwc-lsp + scoring  │                              │
│        └─────────────────────────────────┘                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Hook Types

### 1. PreToolUse (Guardrails — Prompt Hook)

**Purpose:** Provide advisory warnings before execution for low-risk CLI anti-patterns.

**Type:** `prompt` (Haiku-powered semantic evaluation — no Python script)

**What it checks:**
- Deprecated `sfdx` commands (should use `sf`)
- API versions below v56

**How it works:**
The prompt hook sends the command to Haiku for semantic evaluation. It is advisory-only and always returns `ALLOW`, optionally attaching warning context for deprecated CLI usage or old API versions.

### 2. PostToolUse (Validator Dispatcher)

**Purpose:** Route Write/Edit operations to skill-specific validators based on file patterns.

**Location:** `scripts/validator-dispatcher.py`

**Architecture:** The dispatcher uses a centralized `VALIDATOR_REGISTRY` — a list of `(regex_pattern, skill_name, validator_path)` tuples. When a file is written or edited:

1. Extract `file_path` from the hook's `tool_input`
2. Match against all regex patterns in `VALIDATOR_REGISTRY`
3. Execute matching validators sequentially (8s timeout per validator)
4. Return combined validation output

**Current Registry (15 entries across 7 skills):**

| File Pattern | Skill | Validator |
|-------------|-------|-----------|
| `.agent` | sf-ai-agentscript | agentscript-syntax-validator.py |
| `.cls` | sf-apex | apex-lsp-validate.py + post-tool-validate.py |
| `.trigger` | sf-apex | apex-lsp-validate.py + post-tool-validate.py |
| `.soql` | sf-soql | post-tool-validate.py |
| `.flow-meta.xml` | sf-flow | post-tool-validate.py |
| `/lwc/**/*.js` | sf-lwc | lwc-lsp-validate.py + post-tool-validate.py |
| `/lwc/**/*.html` | sf-lwc | template_validator.py |
| `.object-meta.xml` | sf-metadata | validate_metadata.py |
| `.field-meta.xml` | sf-metadata | validate_metadata.py |
| `.permissionset-meta.xml` | sf-metadata | validate_metadata.py |
| `.namedCredential-meta.xml` | sf-integration | validate_integration.py |

---

## Skills Registry Schema (v5.0.0)

```json
{
  "version": "5.0.0",
  "description": "Skills registry for skill discovery keywords and background operation rules",
  "background_operations": { ... },
  "skills": { ... }
}
```

---

## Adding a New Skill

### 1. Add to skills-registry.json

```json
"sf-newskill": {
  "keywords": ["keyword1", "keyword2"],
  "intentPatterns": ["create.*pattern", "build.*pattern"],
  "filePatterns": ["\\.ext$"],
  "priority": "medium",
  "description": "Description of the skill"
}
```

### 2. Add validator to VALIDATOR_REGISTRY

If your skill needs PostToolUse validation, add entries to the `VALIDATOR_REGISTRY` list in `scripts/validator-dispatcher.py`:

```python
# In validator-dispatcher.py VALIDATOR_REGISTRY list:
(
    r"\.yourext$",              # File pattern regex
    "sf-newskill",              # Skill name
    "sf-newskill/hooks/scripts/your-validator.py"  # Validator path (relative to ~/.claude/skills/)
),
```

### 3. Create the validator script

Place your validator at `skills/sf-newskill/hooks/scripts/your-validator.py`. It receives hook context via stdin (JSON) and should output validation results to stdout.

---

## Design Rationale

### Why Proactive + Reactive?

1. **Catch issues early** - Surface low-risk CLI problems before execution
2. **User experience** - Warn on common anti-patterns without blocking
3. **Safety net** - PostToolUse catches issues that slip through

### Why Centralized Dispatcher?

1. **No frontmatter parsing** - Validators route by file pattern, not SKILL.md YAML
2. **Single configuration point** - All routing in one `VALIDATOR_REGISTRY` list
3. **Predictable execution** - Sequential with per-validator timeout (8s)
4. **Easy to extend** - Add a tuple to the registry, drop a validator script

### Why Advisory, Not Automatic?

1. **User agency** - Users stay in control of skill invocations
2. **Transparency** - Claude explains why it's suggesting skills
3. **Flexibility** - Users can override suggestions based on context
4. **Claude is smart** - The model follows well-structured suggestions

### Why Single Registry?

1. **DRY** - No duplicate configuration across all sf-* skills
2. **Consistency** - All skills use the same schema
3. **Maintainability** - One place to update skill metadata
4. **Discoverability** - Easy to see all skill relationships

---

## Troubleshooting

### Hook Not Firing

1. Verify the hook scripts exist and are executable:
   ```bash
   /bin/ls -la shared/hooks/scripts/validator-dispatcher.py
   ```

2. Check that the file pattern matches in `VALIDATOR_REGISTRY`:
   ```bash
   python3 -c "
   import re
   pattern = r'\.cls$'
   print(bool(re.search(pattern, 'MyClass.cls')))
   "
   ```

3. Check validator timeout — each validator has 8s; slow LSP servers may need tuning

### Guardrail Too Aggressive

1. Edit the prompt hook text in `tools/install.py` `get_hooks_config()` or directly in `~/.claude/settings.json`
2. Add exceptions to the prompt text (e.g., "ignore patterns inside heredocs")
3. The prompt hook is advisory-only — it should warn for deprecated CLI usage or old API versions without blocking execution

### Validator Not Found

The dispatcher looks for validators at `~/.claude/skills/<skill>/<path>`. Verify:
```bash
/bin/ls ~/.claude/skills/sf-apex/hooks/scripts/
```

---

## License

MIT License. See [LICENSE](../../LICENSE) file.
Copyright (c) 2024-2026 Jag Valaiyapathy
