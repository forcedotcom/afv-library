---
name: sf-debug
description: >
  Salesforce debug log analysis and troubleshooting with 100-point scoring.
  TRIGGER when: user analyzes debug logs, hits governor limits, reads stack traces,
  or touches .log files from Salesforce orgs.
  DO NOT TRIGGER when: running Apex tests (use sf-testing), fixing Apex code
  (use sf-apex), or Agentforce session tracing (use sf-ai-agentforce-observability).
license: MIT
metadata:
  version: "1.1.0"
  author: "Jag Valaiyapathy"
  scoring: "100 points across 5 categories"
---

# sf-debug: Salesforce Debug Log Analysis & Troubleshooting

Use this skill when the user needs **root-cause analysis from debug logs**: governor-limit diagnosis, stack-trace interpretation, slow-query investigation, heap / CPU pressure analysis, or a reproduction-to-fix loop based on log evidence.

## When This Skill Owns the Task

Use `sf-debug` when the work involves:
- `.log` files from Salesforce
- stack traces and exception analysis
- governor limits
- SOQL / DML / CPU / heap troubleshooting
- query-plan or performance evidence extracted from logs

Delegate elsewhere when the user is:
- running or repairing Apex tests → [sf-testing](../sf-testing/SKILL.md)
- implementing the code fix → [sf-apex](../sf-apex/SKILL.md)
- debugging Agentforce session traces / parquet telemetry → [sf-ai-agentforce-observability](../sf-ai-agentforce-observability/SKILL.md)

---

## Required Context to Gather First

Ask for or infer:
- org alias
- failing transaction / user flow / test name
- approximate timestamp or transaction window
- user / record / request ID if known
- whether the goal is diagnosis only or diagnosis + fix loop

---

## Recommended Workflow

### 1. Retrieve logs
```bash
sf apex list log --target-org <alias> --json
sf apex get log --log-id <id> --target-org <alias>
sf apex tail log --target-org <alias> --color
```

### 2. Analyze in this order
1. entry point and transaction type
2. exceptions / fatal errors
3. governor limits
4. repeated SOQL / DML patterns
5. CPU / heap hotspots
6. callout timing and external failures

### 3. Classify severity
- **Critical** — runtime failure, hard limit, corruption risk
- **Warning** — near-limit, non-selective query, slow path
- **Info** — optimization opportunity or hygiene issue

### 4. Recommend the smallest correct fix
Prefer fixes that are:
- root-cause oriented
- bulk-safe
- testable
- easy to verify with a rerun

Expanded workflow: [references/analysis-playbook.md](references/analysis-playbook.md)

---

## High-Signal Issue Patterns

| Issue | Primary signal | Default fix direction |
|---|---|---|
| SOQL in loop | repeating `SOQL_EXECUTE_BEGIN` in a repeated call path | query once, use maps / grouped collections |
| DML in loop | repeated `DML_BEGIN` patterns | collect rows, bulk DML once |
| Non-selective query | high rows scanned / poor selectivity | add indexed filters, reduce scope |
| CPU pressure | CPU usage approaching sync limit | reduce algorithmic complexity, cache, async where valid |
| Heap pressure | heap usage approaching sync limit | stream with SOQL for-loops, reduce in-memory data |
| Null pointer / fatal error | `EXCEPTION_THROWN` / `FATAL_ERROR` | guard null assumptions, fix empty-query handling |

Expanded examples: [references/common-issues.md](references/common-issues.md)

---

## Output Format

When finishing analysis, report in this order:

1. **What failed**
2. **Where it failed** (class / method / line / transaction stage)
3. **Why it failed** (root cause, not just symptom)
4. **How severe it is**
5. **Recommended fix**
6. **Verification step**

Suggested shape:

```text
Issue: <summary>
Location: <class / line / transaction>
Root cause: <explanation>
Severity: Critical | Warning | Info
Fix: <specific action>
Verify: <test or rerun step>
```

---

## Cross-Skill Integration

| Need | Delegate to | Reason |
|---|---|---|
| Implement Apex fix | [sf-apex](../sf-apex/SKILL.md) | code change generation / review |
| Reproduce via tests | [sf-testing](../sf-testing/SKILL.md) | test execution and coverage loop |
| Deploy fix | [sf-deploy](../sf-deploy/SKILL.md) | deployment orchestration |
| Create debugging data | [sf-data](../sf-data/SKILL.md) | targeted seed / repro data |

---

## Reference Map

### Start here
- [references/analysis-playbook.md](references/analysis-playbook.md)
- [references/common-issues.md](references/common-issues.md)
- [references/cli-commands.md](references/cli-commands.md)

### Deep references
- [references/debug-log-reference.md](references/debug-log-reference.md)
- [references/log-analysis-tools.md](references/log-analysis-tools.md)
- [references/benchmarking-guide.md](references/benchmarking-guide.md)

### Rubric
- [references/scoring-rubric.md](references/scoring-rubric.md)

---

## Score Guide

| Score | Meaning |
|---|---|
| 90+ | Expert analysis with strong fix guidance |
| 80–89 | Good analysis with minor gaps |
| 70–79 | Acceptable but may miss secondary issues |
| 60–69 | Partial diagnosis only |
| < 60 | Incomplete analysis |
