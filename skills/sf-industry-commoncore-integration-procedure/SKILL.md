---
name: sf-industry-commoncore-integration-procedure
description: >
  OmniStudio Integration Procedure creation and validation with 110-point scoring.
  Use when building server-side process orchestrations that combine Data Mapper
  actions, Apex Remote Actions, HTTP callouts, and conditional logic.
  TRIGGER when: user creates Integration Procedures, adds Data Mapper steps,
  configures Remote Actions, or reviews existing IP configurations.
  DO NOT TRIGGER when: building OmniScripts (use sf-industry-commoncore-omniscript), creating Data Mappers
  directly (use sf-industry-commoncore-datamapper), or analyzing cross-component dependencies
  (use sf-industry-commoncore-omnistudio-analyze).
license: MIT
metadata:
  version: "1.0.0"
  author: "David Ryan (weytani)"
  scoring: "110 points across 6 categories"
---

# sf-industry-commoncore-integration-procedure: OmniStudio Integration Procedure Creation and Validation

Expert OmniStudio Integration Procedure (IP) builder with deep knowledge of server-side process orchestration. Create production-ready IPs that combine DataRaptor/Data Mapper actions, Apex Remote Actions, HTTP callouts, conditional logic, and nested procedure calls into declarative multi-step operations.

## Quick Reference

**Scoring**: 110 points across 6 categories. **Thresholds**: ✅ 90+ (Deploy) | ⚠️ 67-89 (Review) | ❌ <67 (Block - fix required)

---

## Core Responsibilities

1. **IP Generation**: Create well-structured Integration Procedures from requirements, selecting correct element types and wiring inputs/outputs
2. **Element Composition**: Assemble DataRaptor actions, Remote Actions, HTTP callouts, conditional blocks, loops, and nested IP calls into coherent orchestrations
3. **Dependency Analysis**: Validate that referenced DataRaptors, Apex classes, and nested IPs exist and are active before deployment
4. **Error Handling**: Enforce try/catch patterns, conditional rollback, and response validation across all data-modifying steps

---

## CRITICAL: Orchestration Order

**sf-industry-commoncore-omnistudio-analyze -> sf-industry-commoncore-datamapper -> sf-industry-commoncore-integration-procedure -> sf-industry-commoncore-omniscript -> sf-industry-commoncore-flexcard** (you are here: sf-industry-commoncore-integration-procedure)

Data Mappers referenced by the IP must exist FIRST. Build and deploy DataRaptors/Data Mappers before the IP that calls them. The IP must be active before any OmniScript or FlexCard can invoke it.

---

## Key Insights

| Insight | Details |
|---------|---------|
| **Chaining** | IPs call other IPs via Integration Procedure Action elements. Output of one step feeds input of the next via response mapping. Design data flow linearly where possible. |
| **Response Mapping** | Each element's output is namespaced under its element name in the response JSON. Use `%elementName:keyPath%` syntax to reference upstream outputs in downstream inputs. |
| **Caching** | IPs support platform cache for read-heavy orchestrations. Set `cacheType` and `cacheTTL` in the procedure's PropertySet. Avoid caching procedures that perform DML. |
| **Versioning** | Type/SubType pairs uniquely identify an IP. Use SubType for versioning (e.g., `Type=AccountOnboarding`, `SubType=v2`). Only one version can be active at a time per Type/SubType. |

**Core Namespace Discriminator**: OmniStudio Core stores both Integration Procedures and OmniScripts in the `OmniProcess` table. Use `IsIntegrationProcedure = true` or `OmniProcessType = 'Integration Procedure'` to filter IPs. Without a filter, queries return mixed results.

> **CRITICAL — Creating IPs via Data API**: When creating OmniProcess records, set `IsIntegrationProcedure = true` to make the record an Integration Procedure. The `OmniProcessType` picklist is **computed from this boolean** and cannot be set directly. Also, `Name` is a required field on `OmniProcess` (not documented in standard OmniStudio docs). Use `sf api request rest --method POST --body @file.json` for creation — the `sf data create record --values` flag cannot handle JSON textarea fields like `PropertySetConfig`.

---

## Workflow Design (5-Phase Pattern)

### Phase 1: Requirements Gathering

**Before building, evaluate alternatives**: Sometimes a single DataRaptor, an Apex service, or a Flow is the better choice. IPs are optimal when you need declarative multi-step orchestration with branching, error handling, and mixed data sources.

**Ask the user** to gather:
- Purpose and business process being orchestrated
- Target objects and data sources (Salesforce objects, external APIs, or both)
- Type/SubType naming (e.g., `Type=OrderProcessing`, `SubType=Standard`)
- Target org alias for deployment

**Then**: Check existing IPs via CLI query (see CLI Commands below), identify reusable DataRaptors/Data Mappers, and review dependent components with sf-industry-commoncore-omnistudio-analyze.

### Phase 2: Design & Element Selection

| Element Type | Use Case | PropertySet Key |
|--------------|----------|-----------------|
| DataRaptor Extract Action | Read Salesforce data | `bundle` |
| DataRaptor Load Action | Write Salesforce data | `bundle` |
| DataRaptor Transform Action | Data shaping/mapping | `bundle` |
| Remote Action | Call Apex class method | `remoteClass`, `remoteMethod` |
| Integration Procedure Action | Call nested IP | `ipMethod` (format: `Type_SubType`) |
| HTTP Action | External API callout | `path`, `method` |
| Conditional Block | Branching logic | -- |
| Loop Block | Iterate over collections | -- |
| Set Values | Assign variables/constants | -- |

**Naming Convention**: `[Type]_[SubType]` using PascalCase. Element names within the IP should describe their action clearly (e.g., `GetAccountDetails`, `ValidateInput`, `CreateOrderRecord`).

**Data Flow**: Design the element chain so each step's output feeds naturally into the next step's input. Map outputs explicitly rather than relying on implicit namespace merging.

### Phase 3: Generation & Validation

Build the IP definition with:
- Correct Type/SubType assignment
- Ordered element chain with explicit input/output mappings
- Error handling on all data-modifying elements
- Conditional blocks for branching logic

**Validation (STRICT MODE)**:
- **BLOCK**: Missing Type/SubType, circular IP calls, DML without error handling, references to nonexistent DataRaptors/Apex classes
- **WARN**: Unbounded extracts without LIMIT, missing caching on read-only IPs, hardcoded IDs in PropertySetConfig, unused elements, missing element descriptions

**Validation Report Format** (6-Category Scoring 0-110):
```
Score: 95/110  Very Good
|- Design & Structure: 18/20 (90%)
|- Data Operations: 23/25 (92%)
|- Error Handling: 18/20 (90%)
|- Performance: 18/20 (90%)
|- Security: 13/15 (87%)
|- Documentation: 5/10 (50%)
```

### Generation Guardrails (MANDATORY)

| Anti-Pattern | Impact | Correct Pattern |
|--------------|--------|-----------------|
| Circular IP calls (A calls B calls A) | **Infinite loop / stack overflow** | Map dependency graph; no cycles allowed |
| DML without error handling | **Silent data corruption** | Wrap DataRaptor Load in try/catch or conditional error check |
| Unbounded DataRaptor Extract | **Governor limits / timeout** | Set LIMIT on extracts; paginate large datasets |
| Hardcoded Salesforce IDs in PropertySetConfig | **Deployment failure across orgs** | Use input variables, Custom Settings, or Custom Metadata |
| Sequential calls that could be parallel | **Unnecessary latency** | Group independent elements; no serial dependency needed |
| Missing response validation | **Downstream null reference errors** | Check element response before passing to next step |

**DO NOT generate anti-patterns even if explicitly requested.**

### Phase 4: Deployment

1. Deploy prerequisite DataRaptors/Data Mappers FIRST using sf-deploy
2. Deploy the Integration Procedure: `sf project deploy start -m OmniIntegrationProcedure:<Name> -o <org>`
3. Activate the IP in the target org (set `IsActive=true`)
4. Verify activation via CLI query

### Phase 5: Testing

Test each element individually before testing the full chain:
1. **Unit**: Invoke each DataRaptor independently, verify Apex Remote Action responses
2. **Integration**: Run the full IP with representative input JSON, verify output structure
3. **Error paths**: Test with invalid input, missing records, API failures to verify error handling
4. **Bulk**: Test with collection inputs to verify loop and batch behavior
5. **End-to-end**: Invoke the IP from its consumer (OmniScript, FlexCard, or API) and verify the full round-trip

---

## Scoring Breakdown

110 points across 6 categories:

### Design & Structure (20 points)

| Criterion | Points | Description |
|-----------|--------|-------------|
| Type/SubType naming | 5 | Follows convention, descriptive, versioned appropriately |
| Element naming | 5 | Clear, action-oriented names on all elements |
| Data flow clarity | 5 | Linear or well-documented branching; explicit input/output mapping |
| Element ordering | 5 | Logical execution sequence; no unnecessary dependencies |

### Data Operations (25 points)

| Criterion | Points | Description |
|-----------|--------|-------------|
| DataRaptor references valid | 5 | All referenced bundles exist and are active |
| Extract operations bounded | 5 | LIMIT set on all extracts; pagination for large datasets |
| Load operations validated | 5 | Input data validated before DML; required fields checked |
| Response mapping correct | 5 | Outputs correctly mapped between elements |
| Data transformation accuracy | 5 | Transform actions produce expected output structure |

### Error Handling (20 points)

| Criterion | Points | Description |
|-----------|--------|-------------|
| DML error handling | 8 | All DataRaptor Load actions have error handling |
| HTTP error handling | 4 | All HTTP actions check status codes and handle failures |
| Remote Action error handling | 4 | Apex exceptions caught and surfaced |
| Rollback strategy | 4 | Multi-step DML has conditional rollback or compensating actions |

### Performance (20 points)

| Criterion | Points | Description |
|-----------|--------|-------------|
| No unbounded queries | 5 | All extracts have reasonable LIMIT values |
| Caching applied | 5 | Read-only procedures use platform cache where appropriate |
| Parallel execution | 5 | Independent elements not serialized unnecessarily |
| No redundant calls | 5 | Same data not fetched multiple times across elements |

### Security (15 points)

| Criterion | Points | Description |
|-----------|--------|-------------|
| No hardcoded IDs | 5 | IDs passed as input variables or from metadata |
| No hardcoded credentials | 5 | API keys/tokens use Named Credentials or Custom Settings |
| Input validation | 5 | User-supplied input sanitized before use in queries or DML |

### Documentation (10 points)

| Criterion | Points | Description |
|-----------|--------|-------------|
| Procedure description | 3 | Clear description of purpose and business context |
| Element descriptions | 4 | Each element has a description explaining its role |
| Input/output documentation | 3 | Expected input JSON and output JSON structure documented |

---

## CLI Commands

```bash
# Query active Integration Procedures
sf data query -q "SELECT Id,Name,Type,SubType,IsActive FROM OmniProcess WHERE IsActive=true AND IsIntegrationProcedure=true" -o <org>

# Query all Integration Procedures (including inactive)
sf data query -q "SELECT Id,Name,Type,SubType,IsActive,LastModifiedDate FROM OmniProcess WHERE IsIntegrationProcedure=true ORDER BY LastModifiedDate DESC" -o <org>

# Retrieve an Integration Procedure
sf project retrieve start -m OmniIntegrationProcedure:<Name> -o <org>

# Deploy an Integration Procedure
sf project deploy start -m OmniIntegrationProcedure:<Name> -o <org>

# Deploy with dry-run validation first
sf project deploy start -m OmniIntegrationProcedure:<Name> -o <org> --dry-run
```

**Core Namespace Note**: The `IsIntegrationProcedure=true` filter is REQUIRED (or equivalently `OmniProcessType='Integration Procedure'`). OmniScript and Integration Procedure records share the `OmniProcess` sObject. Without this filter, queries return both types and produce misleading results.

---

## Cross-Skill Integration

| From Skill | To sf-industry-commoncore-integration-procedure | When |
|------------|----------------------------|------|
| sf-industry-commoncore-omnistudio-analyze | -> sf-industry-commoncore-integration-procedure | "Analyze dependencies before building IP" |
| sf-industry-commoncore-datamapper | -> sf-industry-commoncore-integration-procedure | "DataRaptor/Data Mapper is ready, wire it into IP" |
| sf-apex | -> sf-industry-commoncore-integration-procedure | "Apex Remote Action class deployed, configure in IP" |

| From sf-industry-commoncore-integration-procedure | To Skill | When |
|-------------------------------|----------|------|
| sf-industry-commoncore-integration-procedure | -> sf-deploy | "Deploy IP to target org" |
| sf-industry-commoncore-integration-procedure | -> sf-industry-commoncore-omniscript | "IP is active, build OmniScript that calls it" |
| sf-industry-commoncore-integration-procedure | -> sf-industry-commoncore-flexcard | "IP is active, build FlexCard data source" |
| sf-industry-commoncore-integration-procedure | -> sf-industry-commoncore-omnistudio-analyze | "Verify IP dependency graph before deployment" |

---

## Edge Cases

| Scenario | Solution |
|----------|----------|
| IP calls itself (direct recursion) | Block at design time; circular dependency check is mandatory |
| IP calls IP that calls original (indirect recursion) | Map full call graph; sf-industry-commoncore-omnistudio-analyze detects cycles |
| DataRaptor not yet deployed | Deploy DataRaptors first; IP deployment will fail on missing references |
| External API timeout | Set timeout values on HTTP Action elements; implement retry logic or graceful degradation |
| Large collection input to Loop Block | Set batch size; test with realistic data volumes to avoid CPU timeout |
| Type/SubType collision with existing IP | Query existing IPs before creating; SubType versioning avoids collisions |
| Mixed namespace (Vlocity vs Core) | Confirm org namespace; element property names differ between packages |

**Debug**: IP not executing -> check IsActive flag + Type/SubType match | Elements skipped -> verify conditional block logic + input data shape | Timeout -> check DataRaptor query scope + HTTP timeout settings | Deployment failure -> verify all referenced components deployed and active

---

## Notes

**Dependencies** (optional): sf-deploy, sf-industry-commoncore-datamapper, sf-industry-commoncore-omnistudio-analyze | **API**: 66.0 | **Mode**: Strict (warnings block) | **Scoring**: Block deployment if score < 67 | See `references/best-practices.md` and `references/element-types.md` for detailed guidance.

**Creating IPs programmatically**: Use REST API (`sf api request rest --method POST --body @file.json`). Required fields: `Name`, `Type`, `SubType`, `Language`, `VersionNumber`, `IsIntegrationProcedure=true`. Then create `OmniProcessElement` child records for each action step (also via REST API for JSON PropertySetConfig). Activate by setting `IsActive=true` after all elements are created.

---

## License

MIT License.
Copyright (c) 2026 David Ryan (weytani)
