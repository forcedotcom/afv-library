<!-- Parent: sf-metadata/SKILL.md -->
# Multi-Skill Orchestration: sf-metadata Perspective

This document details how sf-metadata fits into the multi-skill workflow for Salesforce development.

---

## Standard Orchestration Order

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  STANDARD MULTI-SKILL ORCHESTRATION ORDER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. sf-metadata  ◀── YOU ARE HERE                                          │
│     └── Create object/field definitions (LOCAL files)                       │
│                                                                             │
│  2. sf-flow                                                                 │
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

## Why sf-metadata Goes First

| Step | Depends On sf-metadata | What Fails Without It |
|------|------------------------|----------------------|
| sf-flow | ✅ Must exist | Flow references non-existent field/object |
| sf-deploy | ✅ Must exist | Nothing to deploy |
| sf-data | ✅ Must be deployed | `SObject type 'X' not supported` |

**sf-metadata creates the foundation** that all other skills build upon.

---

## Integration + Agentforce Extended Order

When building agents with external API integrations:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  INTEGRATION + AGENTFORCE ORCHESTRATION ORDER                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. sf-metadata  ◀── YOU ARE HERE                                          │
│     └── Create object/field definitions                                     │
│                                                                             │
│  2. sf-connected-apps                                                       │
│     └── Create OAuth Connected App (if external API needed)                 │
│                                                                             │
│  3. sf-integration                                                          │
│     └── Create Named Credential + External Service                          │
│                                                                             │
│  4. sf-apex                                                                 │
│     └── Create @InvocableMethod (if custom logic needed)                    │
│                                                                             │
│  5. sf-flow                                                                 │
│     └── Create Flow wrapper (HTTP Callout or Apex wrapper)                  │
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

## sf-metadata Responsibilities in Orchestration

### Before sf-flow

sf-metadata must create:
- Custom Objects (the flow will reference)
- Custom Fields (used in flow variables, assignments)
- Picklist Values (used in flow decisions)
- Record Types (used in flow record creates)

### Before sf-apex

sf-metadata must create:
- Custom Objects (Apex queries/DML targets)
- Custom Fields (referenced in SOQL, field sets)
- Custom Metadata Types (configuration storage)

### Example: Quote Builder Flow

```
sf-metadata creates:
├── Quote__c.object-meta.xml
├── Quote_Line_Item__c.object-meta.xml
├── Quote__c.Status__c.field-meta.xml (Picklist)
├── Quote_Line_Item__c.Product__c.field-meta.xml (Lookup)
└── Quote_Access.permissionset-meta.xml

sf-apex creates:
└── PricingCalculator.cls (@InvocableMethod)

sf-flow creates:
└── Quote_Builder_Flow.flow-meta.xml (references above)

sf-deploy:
└── Deploys all to org
```

---

## Common Errors from Wrong Order

| Error | Cause | Correct Order |
|-------|-------|---------------|
| `Field does not exist: Status__c` | Flow created before field | sf-metadata → sf-flow |
| `Invalid reference: Quote__c` | Flow created before object | sf-metadata → sf-flow |
| `SObject type 'Quote__c' not supported` | Data created before deploy | sf-deploy → sf-data |
| `Cannot find FlowDefinition` | Agent references missing flow | sf-flow → sf-ai-agentforce |

---

## Invocation Pattern

After creating metadata with sf-metadata:

```
# Deploy metadata
Skill(skill="sf-deploy", args="Deploy to [target-org]")

# Then create test data
Skill(skill="sf-data", args="Create 251 Quote__c records")
```

---

## Cross-Skill Integration Table

| From Skill | To sf-metadata | When |
|------------|----------------|------|
| sf-apex | → sf-metadata | "Describe Quote__c" (discover fields before coding) |
| sf-flow | → sf-metadata | "Describe object fields, record types" (verify structure) |
| sf-data | → sf-metadata | "Describe Custom_Object__c fields" (discover structure) |
| sf-ai-agentforce | → sf-metadata | "Create custom object for agent data" |

---

## Best Practices

1. **Always create Permission Sets** with object/field metadata
2. **Use sf sobject describe** to verify existing structure before creating
3. **Check sfdx-project.json** exists before generating metadata
4. **Use consistent naming** across related objects (Quote__c, Quote_Line_Item__c)
5. **Document relationships** in object descriptions

---

## Related Documentation

| Topic | Location |
|-------|----------|
| Metadata templates | `sf-metadata/assets/` |
| Field types guide | `sf-metadata/references/field-types-guide.md` |
| Naming conventions | `sf-metadata/references/naming-conventions.md` |
| sf-deploy skill | `sf-deploy/SKILL.md` |
