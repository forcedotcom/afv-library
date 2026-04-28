# Agentforce Metadata Reference

Use this document for the metadata-heavy parts of `sf-ai-agentforce` that do not need to live in the activation path.

## GenAiFunction

A `GenAiFunction` registers one callable agent action.

### Common target types
- `flow`
- `apex`
- `prompt`

### Validate before deploy
- target exists
- target is active / deployable
- input names match the target contract
- output names match the target contract
- capability text explains when the planner should use the action

## GenAiPlugin

A `GenAiPlugin` groups related `GenAiFunction` records.

Use it when:
- multiple functions belong to one business domain
- you want cleaner packaging for Builder-based actions

## Prompt Builder template integration

Use Prompt Builder templates when:
- the output is generated content
- the user needs a draft, summary, rewrite, or recommendation

Do not use prompt templates as a substitute for deterministic business logic.

### Current source format
For modern metadata work, use:
- metadata type: `GenAiPromptTemplate`
- folder: `genAiPromptTemplates/`
- suffix: `.genAiPromptTemplate-meta.xml`
- versioned content under `templateVersions`

### High-signal rules
- Treat **Prompt Template** as the UI term and **`GenAiPromptTemplate`** as the metadata type.
- Flex templates should stay within the **5-input maximum**.
- Prompt content should reference inputs with the current merge-field shape such as `{!$Input:TargetRecord}`.
- Publish / activate the template version before wiring downstream actions that depend on it.

## Models API

Use `aiplatform.ModelsAPI` when:
- the requirement is Apex-driven AI logic
- the work belongs in custom server-side orchestration
- Builder-only action patterns are insufficient

## Custom Lightning Types

Use `LightningTypeBundle` when actions need:
- structured input collection
- richer output rendering
- UI-driven agent interaction patterns

## Deployment rule of thumb

Supporting metadata first:
- objects / fields
- Apex
- Flows
- `GenAiPromptTemplate` / `GenAiFunction` / `GenAiPlugin`
- then publish the agent

## Deep references

- Builder workflow: [builder-workflow.md](builder-workflow.md)
- GenAI prompt metadata: [genaiprompttemplate.md](genaiprompttemplate.md)
- Prompt terminology: [prompt-templates.md](prompt-templates.md)
- Models API: [models-api.md](models-api.md)
- Custom Lightning types: [custom-lightning-types.md](custom-lightning-types.md)
- CLI lifecycle: [cli-commands.md](cli-commands.md)
