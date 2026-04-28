<!-- Parent: sf-flow/SKILL.md -->
# Multi-Skill Orchestration: sf-flow Perspective

This document details how sf-flow fits into the multi-skill workflow for Salesforce development.

---

## Standard Orchestration Order

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  STANDARD MULTI-SKILL ORCHESTRATION ORDER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. sf-metadata                                                             │
│     └── Create object/field definitions (LOCAL files)                       │
│                                                                             │
│  2. sf-flow  ◀── YOU ARE HERE                                              │
│     └── Create flow definitions (LOCAL files)                               │
│                                                                             │
│  3. sf-deploy                                                               │
│     └── Deploy all metadata (REMOTE)                                        │
│                                                                             │
│  4. sf-data                                                                 │
│     └── Create test data (REMOTE - objects must exist!)                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Why sf-flow Depends on sf-metadata

| sf-flow Uses | From sf-metadata | What Fails Without It |
|--------------|------------------|----------------------|
| Object references | Custom Objects | `Invalid reference: Quote__c` |
| Field references | Custom Fields | `Field does not exist: Status__c` |
| Picklist values | Picklist Fields | Flow decision uses non-existent value |
| Record Types | Record Type metadata | `Invalid record type: Inquiry` |

**Rule**: If your Flow references custom objects or fields, create them with sf-metadata FIRST.

---

## sf-flow's Role in the Triangle Architecture

Flow acts as the **orchestrator** in the Flow-LWC-Apex triangle:

```
                    ┌─────────────────────┐
                    │       FLOW          │◀── YOU ARE HERE
                    │  (Orchestrator)     │
                    └──────────┬──────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     │
┌─────────────────┐   ┌─────────────────┐           │
│   LWC Screen    │   │  Apex Invocable │           │
│   Component     │   │     Action      │           │
└────────┬────────┘   └────────┬────────┘           │
         │    @AuraEnabled     │                     │
         └──────────┬──────────┘                     │
                    ▼                                │
         ┌─────────────────────┐                     │
         │   Apex Controller   │─────────────────────┘
         └─────────────────────┘   Results back to Flow
```

See `references/triangle-pattern.md` for detailed Flow XML patterns.

---

## Integration + Agentforce Extended Order

When building agents with Flow actions:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  AGENTFORCE FLOW ORCHESTRATION                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. sf-metadata                                                             │
│     └── Create object/field definitions                                     │
│                                                                             │
│  2. sf-connected-apps (if external API)                                     │
│     └── Create OAuth Connected App                                          │
│                                                                             │
│  3. sf-integration (if external API)                                        │
│     └── Create Named Credential + External Service                          │
│                                                                             │
│  4. sf-apex (if custom logic needed)                                        │
│     └── Create @InvocableMethod classes                                     │
│                                                                             │
│  5. sf-flow  ◀── YOU ARE HERE                                              │
│     └── Create Flow (HTTP Callout, Apex wrapper, or standard)               │
│                                                                             │
│  6. sf-deploy                                                               │
│     └── Deploy all metadata                                                 │
│                                                                             │
│  7. sf-ai-agentforce                                                        │
│     └── Create agent with flow:// target                                    │
│                                                                             │
│  8. sf-deploy                                                               │
│     └── Publish agent (sf agent publish authoring-bundle)                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Flows for Agentforce: Critical Requirements

When creating Flows that will be called by Agentforce agents:

### 1. Variable Name Matching

Agent Script input/output names MUST match Flow variable API names exactly:

```xml
<!-- Flow variable -->
<variables>
    <name>inp_AccountId</name>
    <dataType>String</dataType>
    <isInput>true</isInput>
</variables>
```

```yaml
# Agent Script action - names must match!
actions:
  - name: GetAccountDetails
    target: flow://Get_Account_Details
    inputs:
      - name: inp_AccountId  # Must match Flow variable name
        source: slot
```

### 2. Flow Requirements for Agents

| Requirement | Why |
|-------------|-----|
| Autolaunched or Screen Flow | Record-triggered flows cannot be called directly |
| `isInput: true` for inputs | Agent needs to pass values |
| `isOutput: true` for outputs | Agent needs to read results |
| Descriptive variable names | Agent uses these in responses |

### 3. Common Integration Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "Internal Error" on publish | Variable name mismatch | Match Flow var names exactly |
| "Flow not found" | Flow not deployed | sf-deploy before sf-ai-agentforce |
| Agent can't read output | Missing `isOutput: true` | Add output flag to Flow variable |

---

## Cross-Skill Integration Table

| From Skill | To sf-flow | When |
|------------|------------|------|
| sf-ai-agentforce | → sf-flow | "Create Autolaunched Flow for agent action" |
| sf-apex | → sf-flow | "Create Flow wrapper for Apex logic" |
| sf-integration | → sf-flow | "Create HTTP Callout Flow" |

| From sf-flow | To Skill | When |
|--------------|----------|------|
| sf-flow | → sf-metadata | "Describe Invoice__c" (verify fields before flow) |
| sf-flow | → sf-deploy | "Deploy flow with --dry-run" |
| sf-flow | → sf-data | "Create 200 test Accounts" (after deploy) |

---

## Deployment Order for Flow Dependencies

When deploying Flows that reference Apex or LWC:

```
1. APEX CLASSES        (if @InvocableMethod called)
   └── Deploy first

2. LWC COMPONENTS      (if used in Screen Flow)
   └── Deploy second

3. FLOWS               ◀── Deploy LAST
   └── References deployed Apex/LWC
```

---

## Best Practices

1. **Always verify objects exist** before creating Flow references
2. **Use sf-metadata describe** to confirm field API names
3. **Deploy as Draft first** for complex flows
4. **Test with 251 records** for bulk safety
5. **Match variable names exactly** when creating for Agentforce

---

## Related Documentation

| Topic | Location |
|-------|----------|
| Triangle pattern (Flow perspective) | `sf-flow/references/triangle-pattern.md` |
| LWC integration | `sf-flow/references/lwc-integration-guide.md` |
| Apex action template | `sf-flow/assets/apex-action-template.xml` |
| sf-ai-agentforce | `sf-ai-agentforce/SKILL.md` |
