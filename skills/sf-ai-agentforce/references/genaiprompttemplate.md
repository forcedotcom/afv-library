<!-- Parent: sf-ai-agentforce/SKILL.md -->
# GenAiPromptTemplate Reference

Use this guide when creating or reviewing Prompt Builder templates as source metadata.

## Prompt Template vs `GenAiPromptTemplate`

| Concept | Meaning |
|---|---|
| Prompt Template | Plain-English / UI term in Prompt Builder |
| `GenAiPromptTemplate` | Current Metadata API type used in source control and deploy/retrieve workflows |

## Use the current source shape

| Element | Current guidance |
|---|---|
| Metadata type | `GenAiPromptTemplate` |
| Directory | `genAiPromptTemplates/` |
| File suffix | `.genAiPromptTemplate-meta.xml` |
| Content container | `templateVersions` |
| Content field | `content` |
| Status | publish the version used by downstream actions |
| Flexible type | `einstein_gpt__flex` |

## Core template structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<GenAiPromptTemplate xmlns="http://soap.sforce.com/2006/04/metadata">
    <developerName>Account_Briefing_Template</developerName>
    <masterLabel>Account Briefing Template</masterLabel>
    <type>einstein_gpt__flex</type>

    <templateVersions>
        <content>
Summarize {!$Input:TargetAccount.Name} using the notes below.

Notes:
{!$Input:AdditionalContext}
        </content>

        <inputs>
            <apiName>TargetAccount</apiName>
            <definition>SOBJECT://Account</definition>
            <masterLabel>Target Account</masterLabel>
            <referenceName>Input:TargetAccount</referenceName>
            <required>true</required>
        </inputs>

        <inputs>
            <apiName>AdditionalContext</apiName>
            <definition>primitive://String</definition>
            <masterLabel>Additional Context</masterLabel>
            <referenceName>Input:AdditionalContext</referenceName>
            <required>false</required>
        </inputs>

        <primaryModel>sfdc_ai__DefaultAnthropic</primaryModel>
        <status>Published</status>
    </templateVersions>
</GenAiPromptTemplate>
```

## Input rules

### Flex template limit
Flex templates should be designed around a **maximum of 5 inputs**.

When a request appears to need more than 5, prefer one of these strategies:
- consolidate related text into a single structured context input
- pass an SObject input and read multiple fields from it
- move pre-aggregation into Flow or Apex before invoking the template
- reduce optional inputs to the minimum needed for quality output

### Common input definitions

| Need | Definition example |
|---|---|
| Record input | `SOBJECT://Account` |
| Free-text input | `primitive://String` |

## Merge-field guidance

### Current prompt references
Use current-style input references in prompt content:
- `{!$Input:TargetAccount}`
- `{!$Input:TargetAccount.Name}`
- `{!$Input:AdditionalContext}`

### Common mistake
Do not default to older examples that only use `{!variableName}` when you are authoring current `GenAiPromptTemplate` metadata.

## Deployment order

Deploy dependencies before the template or agent that depends on them:
1. objects / fields
2. Apex
3. Flows
4. `GenAiPromptTemplate`
5. `GenAiFunction` / `GenAiPlugin`
6. publish / activate the agent

## Validation checklist

- [ ] Metadata uses `GenAiPromptTemplate`
- [ ] Template file lives under `genAiPromptTemplates/`
- [ ] Flex template has **5 or fewer inputs**
- [ ] Each input has the correct `definition`
- [ ] Prompt content references current input names with `{!$Input:...}`
- [ ] Template version used by downstream actions is published
- [ ] Supporting Flow / Apex / object dependencies already exist in the org

## Common mistakes

| Mistake | Safer approach |
|---|---|
| Using `PromptTemplate` as the metadata type | Use `GenAiPromptTemplate` |
| Storing templates under `promptTemplates/` | Use `genAiPromptTemplates/` |
| Designing flex templates with too many inputs | Consolidate to 5 or fewer |
| Wiring an action to a Draft template | Publish the template version first |
| Treating prompt templates like deterministic logic | Move strict business logic to Flow or Apex |

## Related references

- [prompt-templates.md](prompt-templates.md)
- [metadata-reference.md](metadata-reference.md)
- [builder-workflow.md](builder-workflow.md)
