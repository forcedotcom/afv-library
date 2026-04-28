---
name: sf-ai-agentforce
description: >
  Agentforce Builder metadata path for Builder-managed topics/actions, Prompt
  Builder templates, GenAiFunction/GenAiPlugin, Models API, and custom
  Lightning types.
  TRIGGER when: user maintains or configures Builder metadata agents,
  creates topics/actions, works with Prompt Builder templates, or touches
  .genAiFunction, .genAiPlugin, or .genAiPromptTemplate metadata XML files.
  DO NOT TRIGGER when: Agent Script DSL .agent files (use sf-ai-agentscript),
  agent testing (use sf-ai-agentforce-testing), or persona design
  (use sf-ai-agentforce-persona).
license: MIT
compatibility: "Requires API v66.0+ (Spring '26)"
metadata:
  version: "2.2.0"
  author: "Jag Valaiyapathy"
---

# sf-ai-agentforce: Standard Agentforce Platform Development

Use this skill for the **Setup UI / Agent Builder** path: declarative topics, Builder-managed actions, `GenAiFunction` / `GenAiPlugin` metadata, **Prompt Builder templates stored as `GenAiPromptTemplate` metadata**, Models API usage from Apex, and custom Lightning types.

> For new code-first agent development, prefer [sf-ai-agentscript](../sf-ai-agentscript/SKILL.md).
>
> If the work produces or edits a `.agent` file — including Builder Script / Canvas work that results in an authoring bundle — use [sf-ai-agentscript](../sf-ai-agentscript/SKILL.md).

## When This Skill Owns the Task

Use `sf-ai-agentforce` when the user is:
- maintaining existing Builder-based agents
- working in Setup → Agentforce → Agents
- creating or fixing `GenAiFunction`, `GenAiPlugin`, or `GenAiPromptTemplate` metadata
- wiring Builder topics to Flow / Apex / Prompt Builder actions
- using Models API or LightningTypeBundle in the context of Builder-based agents

Do **not** use it for:
- `.agent` files or deterministic FSM design → [sf-ai-agentscript](../sf-ai-agentscript/SKILL.md)
- agent test suites and coverage loops → [sf-ai-agentforce-testing](../sf-ai-agentforce-testing/SKILL.md)
- persona / voice design → [sf-ai-agentforce-persona](../sf-ai-agentforce-persona/SKILL.md)

---

## Required Context to Gather First

Ask for or infer:
- whether this is a Builder / Setup UI project or a code-first Agent Script project
- whether the user is editing Builder metadata or a `.agent` authoring bundle
- agent type: Service Agent or Employee Agent
- whether the work targets topics, actions, Prompt Builder templates, Models API, or custom Lightning types
- what supporting Flow / Apex / metadata dependencies already exist
- whether the user needs authoring help, publish help, or troubleshooting

---

## Two Agentforce Paths

| Path | Skill | Best fit |
|---|---|---|
| Builder metadata path | `sf-ai-agentforce` | Declarative maintenance, existing Builder agents, metadata-driven action registration |
| Agent Script authoring bundle path | `sf-ai-agentscript` | Code-first `.agent` authoring, deterministic routing, version-controlled agent logic |

If the user is starting from scratch and wants strong control over flow/state, route to Agent Script.

---

## Builder Workflow Summary

1. Confirm this is a **Builder / Setup UI** project
2. Pick Service Agent vs Employee Agent
3. For Service Agents, provision the running user (prefer `sf org create agent-user`)
4. For Employee Agents, plan visibility with a Permission Set containing `<agentAccesses>`
5. Define topics with strong descriptions, scope, and instructions
6. Prepare supporting actions (Flow, Apex, Prompt Builder template)
7. Configure inputs / outputs carefully
8. Validate dependencies and template status
9. Publish, then activate

Expanded workflow: [references/builder-workflow.md](references/builder-workflow.md)

---

## Key Platform Rules

### Topic quality matters
Topic descriptions are routing instructions for the planner. They must be:
- specific
- scenario-based
- non-overlapping with sibling topics

### Actions are wrappers around real targets
| Target type | Typical use | Registered via |
|---|---|---|
| Flow | safest default for Builder actions | `GenAiFunction` |
| Apex | complex business logic via `@InvocableMethod` | `GenAiFunction` |
| Prompt Builder template | generated summaries / drafts / recommendations | `GenAiFunction` |

### Prompt Template vs GenAiPromptTemplate
- **Prompt Template** is the plain-English / UI term used in Prompt Builder.
- **`GenAiPromptTemplate`** is the current Metadata API type for source-driven template work.
- Prefer current source format: `genAiPromptTemplates/*.genAiPromptTemplate-meta.xml`.
- For flexible Prompt Builder templates, plan around the **5-input maximum** and consolidate inputs when needed.
- Prompt content should reference inputs with the current merge-field shape, e.g. `{!$Input:TargetRecord}` or `{!$Input:AdditionalContext}`.

### Supporting metadata deploys first
Before publishing the agent itself, deploy the supporting stack:
1. metadata / fields if needed
2. Apex if needed
3. Flows if needed
4. `GenAiPromptTemplate` / `GenAiFunction` / `GenAiPlugin`
5. then publish the agent

### Service Agent running user
For Service Agents, prefer the native GA command:
`sf org create agent-user --target-org <alias> --json`
Use the returned username in the running-user configuration.

### Employee Agent visibility
For Employee Agents, ensure end users receive a Permission Set containing `<agentAccesses>`. Without this, the agent can be active but still invisible in Lightning Experience.
See [../sf-permissions/references/agent-access-guide.md](../sf-permissions/references/agent-access-guide.md).

### Publish does not activate
After publish, run `sf agent activate` separately.
For automation, prefer `sf agent activate --api-name <AgentName> --version <n> --target-org <alias> --json` so the rollout is deterministic and machine-readable.

---

## Metadata Guidance

### GenAiFunction
Use when registering a single callable action. Validate:
- target exists
- target is active / deployable
- input names match the target contract
- output names match the target contract
- capability text clearly says when the action should be used

### GenAiPlugin
Use when grouping related functions into one logical package.

### GenAiPromptTemplate
Use for generated content, not deterministic business rules.

Prefer the current metadata shape:
- metadata type: `GenAiPromptTemplate`
- folder: `genAiPromptTemplates/`
- file suffix: `.genAiPromptTemplate-meta.xml`
- content lives under `templateVersions`
- use published template versions before wiring actions that depend on them

### Models API
Use when the solution belongs in Apex-driven AI orchestration rather than Builder-only actions.

### Custom Lightning Types
Use when the action needs richer structured input or output presentation.

Expanded references:
- [references/metadata-reference.md](references/metadata-reference.md)
- [references/genaiprompttemplate.md](references/genaiprompttemplate.md)

---

## Cross-Skill Integration

### Recommended Orchestration Order

```text
sf-metadata → sf-apex → sf-flow → sf-ai-agentforce → sf-deploy
```

### Required delegations
| Requirement | Delegate to | Why |
|---|---|---|
| Create / fix Flows | [sf-flow](../sf-flow/SKILL.md) | Action target creation and Flow validation |
| Create / fix Apex actions | [sf-apex](../sf-apex/SKILL.md) | `@InvocableMethod` and Apex correctness |
| Deploy / publish | [sf-deploy](../sf-deploy/SKILL.md) | Deployment orchestration |
| Test the agent | [sf-ai-agentforce-testing](../sf-ai-agentforce-testing/SKILL.md) | Formal test execution and assertions |
| Employee Agent visibility / access | [sf-permissions](../sf-permissions/SKILL.md) | Permission Set `<agentAccesses>` setup |

---

## High-Signal Failure Patterns

| Symptom | Likely cause | Read next |
|---|---|---|
| Action not available in Builder | target metadata missing or not deployed | [references/metadata-reference.md](references/metadata-reference.md) |
| Prompt action fails during publish or activation | template is Draft, missing inputs, or old metadata shape is being used | [references/genaiprompttemplate.md](references/genaiprompttemplate.md) |
| Need more than 5 template inputs | flex template input limit hit | [references/genaiprompttemplate.md](references/genaiprompttemplate.md) |
| Apex AI logic times out | Models API work placed in the wrong context | [references/models-api.md](references/models-api.md) |
| Rich input/output UI not rendering | Lightning type config or prerequisites are incomplete | [references/custom-lightning-types.md](references/custom-lightning-types.md) |
| Agent publishes but is not usable | forgot explicit activation | [references/cli-commands.md](references/cli-commands.md) |
| Service Agent publish/runtime failure | missing or invalid running user | [../sf-ai-agentscript/references/agent-user-setup.md](../sf-ai-agentscript/references/agent-user-setup.md) |
| Employee Agent active but not visible to users | missing `<agentAccesses>` permission set | [../sf-permissions/references/agent-access-guide.md](../sf-permissions/references/agent-access-guide.md) |

---

## Reference Map

### Start here
- [references/builder-workflow.md](references/builder-workflow.md)
- [references/metadata-reference.md](references/metadata-reference.md)
- [references/genaiprompttemplate.md](references/genaiprompttemplate.md)
- [references/cli-commands.md](references/cli-commands.md)

### Terminology and template planning
- [references/prompt-templates.md](references/prompt-templates.md)
- [references/models-api.md](references/models-api.md)
- [references/custom-lightning-types.md](references/custom-lightning-types.md)

### Rubric
- [references/scoring-rubric.md](references/scoring-rubric.md)

### Cross-skill reads
- [sf-ai-agentscript](../sf-ai-agentscript/SKILL.md)
- [sf-ai-agentforce-testing](../sf-ai-agentforce-testing/SKILL.md)
- [sf-flow](../sf-flow/SKILL.md)
- [sf-apex](../sf-apex/SKILL.md)
- [sf-permissions](../sf-permissions/SKILL.md)
- [sf-deploy](../sf-deploy/SKILL.md)

---

## Score Guide

| Score | Meaning |
|---|---|
| 90+ | Ready to deploy |
| 80–89 | Strong, minor cleanup only |
| 70–79 | Review before deploy |
| 60–69 | Needs work |
| < 60 | Block deployment |

Full rubric: [references/scoring-rubric.md](references/scoring-rubric.md)
