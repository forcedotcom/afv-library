# sf-ai-agentforce

Standard Agentforce platform skill for **Setup UI / Agent Builder** work: Builder-managed topics and actions, `GenAiFunction` / `GenAiPlugin`, **Prompt Builder templates stored as `GenAiPromptTemplate` metadata**, Einstein Models API, and custom Lightning types.

> **For code-first Agent Script DSL development**, use [sf-ai-agentscript](../sf-ai-agentscript/).
>
> If the work ends in a `.agent` file or authoring bundle, use [sf-ai-agentscript](../sf-ai-agentscript/).

## What This Skill Covers

| Area | Description |
|------|-------------|
| **Agent Builder** | Creating and configuring agents via Setup UI / Agentforce Builder |
| **GenAiFunction** | Metadata XML for registering Flow, Apex, and Prompt Builder actions |
| **GenAiPlugin** | Grouping multiple GenAiFunctions into reusable action sets |
| **GenAiPromptTemplate** | Current Metadata API type for Prompt Builder templates |
| **Models API** | Native LLM access in Apex via `aiplatform.ModelsAPI` |
| **Custom Lightning Types** | `LightningTypeBundle` for custom agent action UIs |

## What This Skill Does NOT Cover

| Area | Use Instead |
|------|-------------|
| Agent Script DSL (`.agent` files) | [sf-ai-agentscript](../sf-ai-agentscript/) |
| Builder Script / Canvas work that results in `.agent` authoring bundles | [sf-ai-agentscript](../sf-ai-agentscript/) |
| Agent testing & coverage | [sf-ai-agentforce-testing](../sf-ai-agentforce-testing/) |
| Deployment & publishing | [sf-deploy](../sf-deploy/) |

## Requirements

| Requirement | Value |
|-------------|-------|
| API Version | **66.0+** (Spring '26 or later) |
| Licenses | Agentforce, Einstein Generative AI |
| sf CLI | v2.x with agent commands |

## Quick Start

```
Skill: sf-ai-agentforce
Request: "Set up a GenAiFunction for my Apex discount calculator"
```

## Key Current-State Guidance

- In conversation, users may say **Prompt Template**.
- In source metadata, use **`GenAiPromptTemplate`**.
- Prefer `genAiPromptTemplates/*.genAiPromptTemplate-meta.xml` for source-driven Prompt Builder work.
- Flex templates should be designed around the **5-input maximum**.
- For Service Agents, prefer `sf org create agent-user` for running-user setup.
- For Employee Agents, plan user visibility with a Permission Set that contains `<agentAccesses>`.

## Documentation

| Document | Description |
|----------|-------------|
| [SKILL.md](SKILL.md) | Entry point — full skill reference |
| [references/genaiprompttemplate.md](references/genaiprompttemplate.md) | Current `GenAiPromptTemplate` metadata guidance |
| [references/prompt-templates.md](references/prompt-templates.md) | Terminology guide: Prompt Template vs `GenAiPromptTemplate` |
| [references/models-api.md](references/models-api.md) | Einstein Models API (`aiplatform.ModelsAPI`) |
| [references/custom-lightning-types.md](references/custom-lightning-types.md) | `LightningTypeBundle` for custom agent UIs |

## Orchestration

This skill fits into the Agentforce build chain:

```
sf-metadata → sf-apex → sf-flow → sf-ai-agentforce → sf-deploy
```

## License

MIT License — See [LICENSE](LICENSE)
