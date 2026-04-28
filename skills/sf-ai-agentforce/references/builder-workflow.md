# Agentforce Builder Workflow

This reference expands the Setup UI / Agent Builder workflow for `sf-ai-agentforce`.

## Recommended order

1. Confirm this is Builder metadata work, not `.agent` authoring
2. Identify agent type: Service Agent vs Employee Agent
3. For Service Agents, provision the running user (prefer `sf org create agent-user`)
4. For Employee Agents, plan visibility with a Permission Set that contains `<agentAccesses>`
5. Define topics and topic scope
6. Prepare supporting actions (Flow, Apex, Prompt Builder template)
7. Configure action inputs and outputs
8. Configure agent-level instructions and messages
9. Validate supporting metadata and template status
10. Publish and activate

## Builder checklist

### Topics
- Topic descriptions must be concrete and routeable
- Scope should say what the topic can and cannot do
- Instructions should be procedural, not vague brand copy

### Actions
- Flow actions are the safest default for Builder-based agents
- Apex actions must expose `@InvocableMethod`
- Prompt Builder templates should be used when the goal is generated content, not deterministic business logic

### Prompt Builder templates
- In the UI, users will usually say **Prompt Template**
- In source metadata, use **`GenAiPromptTemplate`**
- Prefer `genAiPromptTemplates/*.genAiPromptTemplate-meta.xml`
- Flex templates should stay within the **5-input maximum**
- Use published template versions before wiring dependent actions

### Inputs / Outputs
- Input names must match the target contract exactly
- Output names should be meaningful to the planner
- Displayable outputs should be user-facing and concise

### Agent-level settings
- System instructions should be stable and role-defining
- Welcome message should orient the user quickly
- Error message should explain fallback behavior
- Service Agents should use a running user provisioned with `sf org create agent-user` when possible
- Employee Agents need end-user visibility via Permission Sets containing `<agentAccesses>`

## Publish sequence

1. Deploy supporting metadata (`GenAiPromptTemplate`, `GenAiFunction`, `GenAiPlugin`, Flow, Apex, etc.)
2. Save / publish the agent in Builder, or deploy the relevant Builder metadata
3. Activate the target version
4. For Employee Agents, verify visibility via Permission Set `<agentAccesses>`

Publishing does **not** activate the new version automatically.

> `sf agent publish authoring-bundle` is part of the Agent Script workflow and belongs to `sf-ai-agentscript`, not the default Builder metadata workflow.

## Deep references

- CLI lifecycle: [cli-commands.md](cli-commands.md)
- Metadata details: [metadata-reference.md](metadata-reference.md)
- GenAI prompt metadata: [genaiprompttemplate.md](genaiprompttemplate.md)
- Prompt terminology: [prompt-templates.md](prompt-templates.md)
- Models API: [models-api.md](models-api.md)
- Custom Lightning types: [custom-lightning-types.md](custom-lightning-types.md)
- Employee Agent visibility: [../../sf-permissions/references/agent-access-guide.md](../../sf-permissions/references/agent-access-guide.md)
- Service Agent running user: [../../sf-ai-agentscript/references/agent-user-setup.md](../../sf-ai-agentscript/references/agent-user-setup.md)
