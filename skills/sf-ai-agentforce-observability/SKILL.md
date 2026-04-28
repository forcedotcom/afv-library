---
name: sf-ai-agentforce-observability
description: >
  Agentforce session tracing extraction and analysis.
  TRIGGER when: user extracts STDM data from Data Cloud, analyzes agent session
  traces, debugs agent conversations via telemetry, or works with .parquet files
  from Agentforce.
  DO NOT TRIGGER when: testing agents (use sf-ai-agentforce-testing), Apex debug
  logs (use sf-debug), or building agents (use sf-ai-agentforce).
license: MIT
compatibility: "Requires Data 360 enabled org with Agentforce Session Tracing"
metadata:
  version: "1.0.0"
  author: "Jag Valaiyapathy"
  data_model: "Session Tracing Data Model (STDM)"
  storage_format: "Parquet (via PyArrow)"
  analysis_library: "Polars"
---

# sf-ai-agentforce-observability: Agentforce Session Tracing Extraction & Analysis

Use this skill when the user needs **trace-based observability**, not just testing: extract Session Tracing Data Model (STDM) records, work with Parquet datasets, reconstruct session timelines, analyze topic/action latency, or debug agent behavior from Data 360 telemetry.

## When This Skill Owns the Task

Use `sf-ai-agentforce-observability` when the work involves:
- Data 360 / Session Tracing extraction
- `.parquet` files from Agentforce telemetry
- session timeline reconstruction
- trace-driven debugging of topic routing, action failures, or latency
- Polars / PyArrow-based analysis of large telemetry datasets

Delegate elsewhere when the user is:
- formally testing agents → [sf-ai-agentforce-testing](../sf-ai-agentforce-testing/SKILL.md)
- debugging Apex logs → [sf-debug](../sf-debug/SKILL.md)
- authoring or reconfiguring the agent itself → [sf-ai-agentforce](../sf-ai-agentforce/SKILL.md) or [sf-ai-agentscript](../sf-ai-agentscript/SKILL.md)

---

## Prerequisites That Must Exist

Before extraction, verify:
- Data 360 is enabled
- Session Tracing is enabled
- the Salesforce Standard Data Model version is sufficient
- Einstein / Agentforce capabilities are enabled in the org
- JWT / ECA auth for Data 360 access is configured

If auth is missing, hand off to:
- [sf-connected-apps](../sf-connected-apps/SKILL.md)

Deep setup guide:
- [references/auth-setup.md](references/auth-setup.md)

---

## What This Skill Works With

### Core storage / analysis model
- extraction via Data 360 APIs
- Parquet for storage efficiency
- Polars for large-scale lazy analysis

### Core STDM entities
At minimum, expect work around:
- session
- interaction / turn
- interaction step
- moment
- message

GenAI Trust Layer / audit records may also be relevant for content-quality and generation debugging.

Full schema:
- [references/data-model-reference.md](references/data-model-reference.md)

---

## Required Context to Gather First

Ask for or infer:
- target org alias
- time window or date range
- agent filter, if any
- whether the goal is extraction, summary analysis, or single-session debugging
- output location for extracted data
- whether the user already has Parquet files on disk

---

## Recommended Workflow

### 1. Verify setup and auth
Confirm Data 360 tracing exists and JWT/ECA auth is working.

### 2. Choose the extraction mode
| Need | Default approach |
|---|---|
| recent telemetry snapshot | extract last N days |
| focused investigation | filtered extraction by date and agent |
| one broken conversation | extract or debug a single session tree |
| ongoing usage analytics | incremental extraction |

### 3. Extract to Parquet
Use the provided scripts under `scripts/` rather than reimplementing extraction logic.

### 4. Analyze with Polars
Common analysis goals:
- session volume and duration
- topic distribution
- action step failures
- latency hotspots
- abandonment / escalation patterns
- session-level timeline reconstruction

### 5. Convert findings into next actions
Typical outcomes:
- topic mismatch → improve routing or descriptions
- action failure → inspect Flow / Apex implementation
- latency issue → optimize downstream action path
- test gap → add targeted agent tests

---

## High-Signal Operational Rules

- treat STDM as **read-only telemetry**
- expect ingestion lag; this is not perfect real-time debugging
- use date filters and focused extraction to avoid unnecessary volume / query cost
- prefer Parquet over ad hoc JSON for durable analysis
- use lazy Polars patterns for large datasets

Common pitfalls:
- assuming missing data means no issue, when tracing may simply not be enabled
- running huge broad queries without date or agent filters
- trying to fix the agent inside this skill instead of handing off to authoring / testing skills

---

## Output Format

When finishing, report in this order:
1. **What data was extracted or analyzed**
2. **Scope** (org, dates, agent filter, session IDs)
3. **Key findings**
4. **Likely root causes**
5. **Recommended next skill / next action**

Suggested shape:

```text
Observability task: <extract / analyze / debug-session>
Scope: <org, dates, agents, session ids>
Artifacts: <directories / parquet files>
Findings: <latency, routing, action, quality, abandonment patterns>
Root cause: <best current explanation>
Next step: <testing, agent fix, flow fix, apex fix>
```

---

## Cross-Skill Integration

| Need | Delegate to | Reason |
|---|---|---|
| auth / JWT setup | [sf-connected-apps](../sf-connected-apps/SKILL.md) | Data 360 access |
| fix agent routing / behavior | [sf-ai-agentscript](../sf-ai-agentscript/SKILL.md) | authoring corrections |
| formal regression / coverage tests | [sf-ai-agentforce-testing](../sf-ai-agentforce-testing/SKILL.md) | reproducible test loops |
| Flow-backed action debugging | [sf-flow](../sf-flow/SKILL.md) | declarative repair |
| Apex-backed action debugging | [sf-debug](../sf-debug/SKILL.md) or [sf-apex](../sf-apex/SKILL.md) | code / log investigation |

---

## Reference Map

### Start here
- [README.md](README.md)
- [references/basic-extraction.md](references/basic-extraction.md)
- [references/filtered-extraction.md](references/filtered-extraction.md)
- [references/cli-reference.md](references/cli-reference.md)

### Data model / querying
- [references/data-model-reference.md](references/data-model-reference.md)
- [references/query-patterns.md](references/query-patterns.md)
- [references/client-demo-queries.md](references/client-demo-queries.md)

### Analysis / debugging
- [references/analysis-cookbook.md](references/analysis-cookbook.md)
- [references/analysis-examples.md](references/analysis-examples.md)
- [references/debugging-sessions.md](references/debugging-sessions.md)
- [references/polars-cheatsheet.md](references/polars-cheatsheet.md)
- [references/agent-execution-lifecycle.md](references/agent-execution-lifecycle.md)

### Auth / troubleshooting
- [references/auth-setup.md](references/auth-setup.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [references/billing-and-troubleshooting.md](references/billing-and-troubleshooting.md)
- [references/builder-trace-api.md](references/builder-trace-api.md)
- [scripts/](scripts/)

---

## Score Guide

| Score | Meaning |
|---|---|
| 90+ | strong telemetry-backed diagnosis |
| 75–89 | useful analysis with minor gaps |
| 60–74 | partial visibility only |
| < 60 | insufficient evidence; gather more telemetry |
