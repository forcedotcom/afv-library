<!-- Parent: sf-ai-agentforce/SKILL.md -->
# Prompt Templates in Agentforce

> **Terminology guide:** Salesforce users commonly say **Prompt Template** in the UI, while modern source-driven metadata work uses **`GenAiPromptTemplate`**.

## Short answer

| Term | Meaning |
|------|---------|
| **Prompt Template** | Plain-English / UI term used in Prompt Builder |
| **`GenAiPromptTemplate`** | Current Metadata API type for Prompt Builder templates |

## When to use prompt templates

Use a Prompt Builder template when the action should generate content such as:
- summaries
- drafts
- rewrites
- recommendations

Do **not** use a prompt template when the requirement is deterministic business logic or strict transactional processing.

## Current metadata direction

For source-controlled work, prefer:
- `genAiPromptTemplates/`
- `.genAiPromptTemplate-meta.xml`
- versioned content inside `templateVersions`

Flex templates should be designed around the **5-input maximum**.

## Current merge-field style

Prompt content should reference current inputs with shapes like:
- `{!$Input:TargetRecord}`
- `{!$Input:AdditionalContext}`
- `{!$Input:TargetRecord.Name}`

## Read next

- [genaiprompttemplate.md](genaiprompttemplate.md) — detailed metadata guide
- [metadata-reference.md](metadata-reference.md) — Agentforce metadata overview
- [builder-workflow.md](builder-workflow.md) — when templates fit in the Builder lifecycle
