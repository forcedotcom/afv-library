---
name: sf-integration
description: >
  Salesforce integration architecture with 120-point scoring.
  TRIGGER when: user sets up Named Credentials, External Services, REST/SOAP
  callouts, Platform Events, CDC, or touches .namedCredential-meta.xml files.
  DO NOT TRIGGER when: Connected App/OAuth config (use sf-connected-apps),
  Apex-only logic (use sf-apex), or data import/export (use sf-data).
license: MIT
metadata:
  version: "1.2.0"
  author: "Jag Valaiyapathy"
  scoring: "120 points across 6 categories"
---

# sf-integration: Salesforce Integration Patterns Expert

Use this skill when the user needs **integration architecture and runtime plumbing**: Named Credentials, External Credentials, External Services, REST/SOAP callout patterns, Platform Events, CDC, and event-driven integration design.

## When This Skill Owns the Task

Use `sf-integration` when the work involves:
- `.namedCredential-meta.xml` or External Credential metadata
- outbound REST/SOAP callouts
- External Service registration from OpenAPI specs
- Platform Events, CDC, and event-driven architecture
- choosing sync vs async integration patterns

Delegate elsewhere when the user is:
- configuring the OAuth app itself → [sf-connected-apps](../sf-connected-apps/SKILL.md)
- writing Apex-only business logic → [sf-apex](../sf-apex/SKILL.md)
- deploying metadata → [sf-deploy](../sf-deploy/SKILL.md)
- importing/exporting data → [sf-data](../sf-data/SKILL.md)

---

## Required Context to Gather First

Ask for or infer:
- integration style: outbound callout, inbound event, External Service, CDC, platform event
- auth method
- sync vs async requirement
- system endpoint / spec details
- rate limits, retry expectations, and failure tolerance
- whether this is net-new design or repair of an existing integration

---

## Recommended Workflow

### 1. Choose the integration pattern
| Need | Default pattern |
|---|---|
| authenticated outbound API call | Named Credential / External Credential + Apex or Flow |
| spec-driven API client | External Service |
| trigger-originated callout | async callout pattern |
| decoupled event publishing | Platform Events |
| change-stream consumption | CDC |

### 2. Choose the auth model
Prefer secure runtime-managed auth:
- Named Credentials / External Credentials
- OAuth or JWT via the right credential model
- no hardcoded secrets in code

### 3. Generate from the right templates
Use the provided assets under:
- `assets/named-credentials/`
- `assets/external-credentials/`
- `assets/external-services/`
- `assets/callouts/`
- `assets/platform-events/`
- `assets/cdc/`
- `assets/soap/`

### 4. Validate operational safety
Check:
- timeout and retry handling
- async strategy for trigger-originated work
- logging / observability
- event retention and subscriber implications

### 5. Hand off deployment or implementation details
Use:
- [sf-deploy](../sf-deploy/SKILL.md) for deployment
- [sf-apex](../sf-apex/SKILL.md) for deeper service / retry code
- [sf-flow](../sf-flow/SKILL.md) for declarative HTTP callout orchestration

---

## High-Signal Rules

- never hardcode credentials
- do not do synchronous callouts from triggers
- define timeout behavior explicitly
- plan retries for transient failures
- use middleware / event-driven patterns when outbound volume is high
- prefer External Credentials architecture for new development when supported

Common anti-patterns:
- sync trigger callouts
- no retry or dead-letter strategy
- no request/response logging
- mixing auth setup responsibilities with runtime integration design

---

## Output Format

When finishing, report in this order:
1. **Integration pattern chosen**
2. **Auth model chosen**
3. **Files created or updated**
4. **Operational safeguards**
5. **Deployment / testing next step**

Suggested shape:

```text
Integration: <summary>
Pattern: <named credential / external service / event / cdc / callout>
Files: <paths>
Safety: <timeouts, retries, async, logging>
Next step: <deploy, register, test, or implement>
```

---

## Cross-Skill Integration

| Need | Delegate to | Reason |
|---|---|---|
| OAuth app setup | [sf-connected-apps](../sf-connected-apps/SKILL.md) | consumer key / cert / app config |
| advanced callout service code | [sf-apex](../sf-apex/SKILL.md) | Apex implementation |
| declarative HTTP callout / Flow wrapper | [sf-flow](../sf-flow/SKILL.md) | Flow orchestration |
| deploy integration metadata | [sf-deploy](../sf-deploy/SKILL.md) | validation and rollout |
| use integration from Agentforce | [sf-ai-agentscript](../sf-ai-agentscript/SKILL.md) | agent action composition |

---

## Reference Map

### Start here
- [references/named-credentials-guide.md](references/named-credentials-guide.md)
- [references/external-services-guide.md](references/external-services-guide.md)
- [references/callout-patterns.md](references/callout-patterns.md)
- [references/security-best-practices.md](references/security-best-practices.md)

### Event-driven / platform patterns
- [references/event-patterns.md](references/event-patterns.md)
- [references/platform-events-guide.md](references/platform-events-guide.md)
- [references/cdc-guide.md](references/cdc-guide.md)
- [references/event-driven-architecture-guide.md](references/event-driven-architecture-guide.md)
- [references/messaging-api-v2.md](references/messaging-api-v2.md)

### CLI / automation / scoring
- [references/cli-reference.md](references/cli-reference.md)
- [references/named-credentials-automation.md](references/named-credentials-automation.md)
- [references/scoring-rubric.md](references/scoring-rubric.md)
- [assets/](assets/)

---

## Score Guide

| Score | Meaning |
|---|---|
| 108+ | strong production-ready integration design |
| 90–107 | good design with some hardening left |
| 72–89 | workable but needs architectural review |
| < 72 | unsafe / incomplete for deployment |
