---
name: sf-apex
description: >
  Generates and reviews Salesforce Apex code with 150-point scoring.
  TRIGGER when: user writes, reviews, or fixes Apex classes, triggers, test classes,
  batch/queueable/schedulable jobs, or touches .cls/.trigger files.
  DO NOT TRIGGER when: LWC JavaScript (use sf-lwc), Flow XML (use sf-flow),
  SOQL-only queries (use sf-soql), or non-Salesforce code.
license: MIT
metadata:
  version: "1.1.0"
  author: "Jag Valaiyapathy"
  scoring: "150 points across 8 categories"
---

# sf-apex: Salesforce Apex Code Generation and Review

Use this skill when the user needs **production Apex**: new classes, triggers, selectors, services, async jobs, invocable methods, test classes, or evidence-based review of existing `.cls` / `.trigger` code.

## When This Skill Owns the Task

Use `sf-apex` when the work involves:
- Apex class generation or refactoring
- trigger design and trigger-framework decisions
- `@InvocableMethod`, Queueable, Batch, Schedulable, or test-class work
- review of bulkification, sharing, security, testing, or maintainability

Delegate elsewhere when the user is:
- editing LWC JavaScript / HTML / CSS → [sf-lwc](../sf-lwc/SKILL.md)
- building Flow XML or Flow orchestration → [sf-flow](../sf-flow/SKILL.md)
- writing SOQL only → [sf-soql](../sf-soql/SKILL.md)
- deploying or validating metadata to orgs → [sf-deploy](../sf-deploy/SKILL.md)

---

## Required Context to Gather First

Ask for or infer:
- class type: trigger, service, selector, batch, queueable, schedulable, invocable, test
- target object(s) and business goal
- whether code is net-new, refactor, or fix
- org / API constraints if known
- expected test coverage or deployment target

Before authoring, inspect the project shape:
- existing classes / triggers
- current trigger framework or handler pattern
- related tests, flows, and selectors
- whether TAF is already in use

---

## Recommended Workflow

### 1. Discover local architecture
Check for:
- existing trigger handlers / frameworks
- service-selector-domain conventions
- related tests and data factories
- invocable or async patterns already used in the repo

### 2. Choose the smallest correct pattern
| Need | Preferred pattern |
|---|---|
| simple reusable logic | service class |
| query-heavy data access | selector |
| single object trigger behavior | one trigger + handler / TAF action |
| Flow needs complex logic | `@InvocableMethod` |
| background processing | Queueable by default |
| very large datasets | Batch Apex or `Database.Cursor` patterns |
| repeatable verification | dedicated test class + test data factory |

### 3. Author with guardrails
Generate code that is:
- bulk-safe
- sharing-aware
- CRUD/FLS-safe where applicable
- testable in isolation
- consistent with project naming and layering

### 4. Validate and score
Evaluate against the 150-point rubric before handoff.

### 5. Hand off deploy/test next steps
When org validation is needed, hand off to:
- [sf-testing](../sf-testing/SKILL.md) for test execution loops
- [sf-deploy](../sf-deploy/SKILL.md) for deploy / dry-run / verification

---

## Generation Guardrails

Never generate these without explicitly stopping and explaining the problem:

| Anti-pattern | Why it blocks |
|---|---|
| SOQL in loops | governor-limit failure |
| DML in loops | governor-limit failure |
| missing sharing model | security / data exposure risk |
| hardcoded IDs | deployment and portability failure |
| empty `catch` blocks | silent failure / poor observability |
| string-built SOQL with user input | injection risk |
| tests without assertions | false-positive test suite |

Default fix direction:
- query once, operate on collections
- use `with sharing` unless justified otherwise
- use bind variables and `WITH USER_MODE` where appropriate
- create assertions for positive, negative, and bulk cases

See [references/anti-patterns.md](references/anti-patterns.md) and [references/security-guide.md](references/security-guide.md).

---

## High-Signal Build Rules

### Trigger architecture
- Prefer **one trigger per object**.
- If TAF is already installed and used, extend it instead of inventing a second trigger pattern.
- Triggers should delegate logic; avoid heavy business logic directly in trigger bodies.

### Async choice
| Scenario | Default |
|---|---|
| standard async work | Queueable |
| very large record processing | Batch Apex |
| recurring schedule | Scheduled Flow or Schedulable |
| post-job cleanup | Finalizer |
| long-running Lightning callouts | `Continuation` |

### Testing minimums
Use the **PNB** pattern for every feature:
- **Positive** path
- **Negative** / error path
- **Bulk** path (251+ records where relevant)

### Modern Apex expectations
Prefer current idioms when available:
- safe navigation: `obj?.Field__c`
- null coalescing: `value ?? fallback`
- `Assert.*` over legacy assertion style
- `WITH USER_MODE` and explicit security handling where relevant

---

## Output Format

When finishing, report in this order:
1. **What was created or reviewed**
2. **Files changed**
3. **Key design decisions**
4. **Risk / guardrail notes**
5. **Test guidance**
6. **Deployment guidance**

Suggested shape:

```text
Apex work: <summary>
Files: <paths>
Design: <pattern / framework choices>
Risks: <security, bulkification, async, dependency notes>
Tests: <what to run / add>
Deploy: <dry-run or next step>
```

---

## LSP Validation Note

This skill supports an LSP-assisted authoring loop for `.cls` and `.trigger` files:
- syntax issues can be detected immediately after write/edit
- the skill can auto-fix common syntax errors in a short loop
- semantic quality still depends on the 150-point review rubric

Full guide: [references/troubleshooting.md](references/troubleshooting.md#lsp-based-validation-auto-fix-loop)

---

## Cross-Skill Integration

| Need | Delegate to | Reason |
|---|---|---|
| describe objects / fields first | [sf-metadata](../sf-metadata/SKILL.md) | avoid coding against wrong schema |
| seed bulk or edge-case data | [sf-data](../sf-data/SKILL.md) | create realistic test datasets |
| run Apex tests / fix failing tests | [sf-testing](../sf-testing/SKILL.md) | execute and iterate on failures |
| deploy to org | [sf-deploy](../sf-deploy/SKILL.md) | validation and deployment orchestration |
| build Flow that calls Apex | [sf-flow](../sf-flow/SKILL.md) | declarative orchestration |
| build LWC that calls Apex | [sf-lwc](../sf-lwc/SKILL.md) | UI/controller integration |

---

## Reference Map

### Start here
- [references/patterns-deep-dive.md](references/patterns-deep-dive.md)
- [references/security-guide.md](references/security-guide.md)
- [references/bulkification-guide.md](references/bulkification-guide.md)
- [references/testing-patterns.md](references/testing-patterns.md)

### High-signal checklists
- [references/code-review-checklist.md](references/code-review-checklist.md)
- [references/anti-patterns.md](references/anti-patterns.md)
- [references/naming-conventions.md](references/naming-conventions.md)

### Specialized patterns
- [references/trigger-actions-framework.md](references/trigger-actions-framework.md)
- [references/automation-density-guide.md](references/automation-density-guide.md)
- [references/flow-integration.md](references/flow-integration.md)
- [references/triangle-pattern.md](references/triangle-pattern.md)
- [references/design-patterns.md](references/design-patterns.md)
- [references/solid-principles.md](references/solid-principles.md)

### Troubleshooting / validation
- [references/troubleshooting.md](references/troubleshooting.md)
- [references/llm-anti-patterns.md](references/llm-anti-patterns.md)
- [references/testing-guide.md](references/testing-guide.md)

---

## Score Guide

| Score | Meaning |
|---|---|
| 120+ | strong production-ready Apex |
| 90–119 | good implementation, review before deploy |
| 67–89 | acceptable but needs improvement |
| < 67 | block deployment |
