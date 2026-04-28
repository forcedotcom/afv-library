<!-- Parent: sf-ai-agentscript/SKILL.md -->
# Official Sources Registry

> Canonical Salesforce documentation URLs for Agent Script. Use this registry to verify syntax, resolve errors, and stay current with platform changes.

---

## Primary References (Agent Script Documentation)

| # | Page | URL | Use When |
|---|------|-----|----------|
| 1 | Agent Script Overview | https://developer.salesforce.com/docs/ai/agentforce/guide/agent-script.html | Starting point, general concepts |
| 2 | Language Characteristics | https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-lang.html | Syntax model, whitespace rules, symbols |
| 3 | Blocks Reference | https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-blocks.html | Block structure, required fields |
| 4 | Flow of Control | https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-flow.html | Execution order, transitions, prompt construction |
| 5 | Actions Reference | https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-ref-actions.html | Action definitions, targets, I/O |
| 6 | Variables Reference | https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-ref-variables.html | Mutable, linked, types, sources |
| 7 | Tools Reference | https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-ref-tools.html | `@utils.*` utilities, transitions, topic delegation |
| 8 | Utils Reference | https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-ref-utils.html | Utility action details |
| 9 | Instructions Reference | https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-ref-instructions.html | Pipe vs arrow, resolution order |
| 10 | Expressions Reference | https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-ref-expressions.html | Conditionals and expression syntax |
| 11 | Before/After Reasoning | https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-ref-before-after-reasoning.html | Lifecycle hooks syntax |
| 12 | Operators Reference | https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-ref-operators.html | Comparison, logical, arithmetic |
| 13 | Topic Blocks | https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-blocks.html#topic-blocks | Topic structure, descriptions, reasoning/actions |
| 14 | Agent Script Reference | https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-reference.html | Keyword glossary and cross-reference hub |
| 15 | Patterns Overview | https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-patterns.html | Official pattern catalog |
| 16 | Examples | https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-example.html | Complete working examples |
| 17 | Manage Agent Script Agents | https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-manage.html | Configure, deploy, and test guidance |
| 18 | Agent DX (CLI) | https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx.html | CLI commands, bundle structure |

> **URL Prefix Note**: Agent Script docs migrated from `/docs/einstein/genai/guide/ascript-*` (older beta path) to `/docs/ai/agentforce/guide/ascript-*` (current path). Also note that some older per-topic/per-lifecycle URLs have been folded into newer pages or renamed (for example, `ascript-ref-before-after-reasoning.html` and `ascript-blocks.html#topic-blocks`).

---

## Official Pattern Pages

| # | Page | URL | Use When |
|---|------|-----|----------|
| P1 | System Overrides | https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-patterns-system-overrides.html | Topic-level `system.instructions` overrides |
| P2 | Variables Pattern | https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-patterns-variables.html | State sharing, slot filling, variable usage |
| P3 | Transitions Pattern | https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-patterns-transitions.html | `@utils.transition to`, deterministic vs LLM-selected routing |

---

## Recipe Repository

| # | Page | URL | Content |
|---|------|-----|---------|
| 1 | Recipes Overview | https://developer.salesforce.com/sample-apps/agent-script-recipes/getting-started/overview | Getting started guide |
| 2 | GitHub Repository | https://github.com/trailheadapps/agent-script-recipes | Source code, AGENT_SCRIPT.md rules |
| 3 | Hello World | https://developer.salesforce.com/sample-apps/agent-script-recipes/language-essentials/hello-world | Minimal agent example |
| 4 | Action Definitions | https://developer.salesforce.com/sample-apps/agent-script-recipes/action-configuration/action-definitions | Action config patterns |
| 5 | Multi-Topic Navigation | https://developer.salesforce.com/sample-apps/agent-script-recipes/architectural-patterns/multi-topic-navigation | Topic routing patterns |
| 6 | Error Handling | https://developer.salesforce.com/sample-apps/agent-script-recipes/architectural-patterns/error-handling | Error handling patterns |
| 7 | Bidirectional Navigation | https://developer.salesforce.com/sample-apps/agent-script-recipes/architectural-patterns/bidirectional-navigation | Two-way topic transitions |
| 8 | Advanced Input Bindings | https://developer.salesforce.com/sample-apps/agent-script-recipes/action-configuration/advanced-input-bindings | Slot-fill, fixed, variable binding |

---

## Diagnostic Decision Tree

When something fails, use this tree to determine which doc page to fetch:

```
Error or Ambiguity
       │
       ├─ Compilation / SyntaxError
       │     ├─ Block-level error → Fetch #3 (Blocks Reference)
       │     ├─ Expression error  → Fetch #10 (Expressions) + #12 (Operators)
       │     └─ Action error      → Fetch #5 (Actions Reference)
       │
       ├─ Action not executing
       │     ├─ Action defined but LLM doesn't pick it → Fetch #5 (Actions) + #7 (Tools)
       │     └─ Action target not found               → Fetch #5 (Actions) + #18 (Agent DX)
       │
       ├─ Variable not updating
       │     ├─ Linked var empty     → Fetch #6 (Variables)
       │     └─ Mutable not changing → Fetch #6 (Variables) + #9 (Instructions)
       │
       ├─ Topic transition wrong
       │     ├─ Wrong topic selected  → Fetch #13 (Topic Blocks) + #8 (Utils)
       │     └─ Transition vs delegation confusion → Fetch #7 (Tools) + #13 (Topic Blocks)
       │
       ├─ Lifecycle hook issue
       │     └─ before/after_reasoning error → Fetch #11 (Before/After)
       │
       └─ New / unfamiliar syntax
             └─ Start with #1 (Overview), then narrow to specific reference
```

---

## Fallback Search Patterns

When a specific URL 404s or doesn't have the answer:

```bash
# Primary search pattern
site:developer.salesforce.com agent script <topic>

# Recipe search
site:developer.salesforce.com sample-apps agent-script-recipes <topic>

# GitHub issues (known bugs, community solutions)
site:github.com trailheadapps agent-script-recipes <error message>

# Salesforce Stack Exchange
site:salesforce.stackexchange.com agent script <topic>
```

---

## URL Health Check

When verifying URLs, use WebFetch to confirm each resolves. If a URL redirects or 404s:

1. Try swapping the URL prefix (see note above)
2. Use the fallback search pattern
3. If consistently broken, update this file and note the date

---

*Last updated: 2026-03-12*
