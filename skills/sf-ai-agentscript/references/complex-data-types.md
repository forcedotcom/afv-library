<!-- Parent: sf-ai-agentscript/SKILL.md -->

# `complex_data_type_name` Mapping Table

> **"#1 source of compile errors"** - Use this table when defining action inputs/outputs in Agentforce Assets.

| Data Type | `complex_data_type_name` Value | Notes |
|-----------|-------------------------------|-------|
| `string` | *(none needed)* | Primitive type |
| `number` | *(none needed)* | Primitive type — **variables only**† |
| `boolean` | *(none needed)* | Primitive type |
| `object` (SObject) | `lightning__recordInfoType` | Use for Account, Contact, etc. |
| `list[string]` | `lightning__textType` | Collection of text values |
| `list[object]` (JSON text) | `lightning__textType` | Serialized as JSON text |
| `list[object]` (SObject collection) | `lightning__recordInfoType` | **USE THIS for Flow SObject outputs** |
| Apex Inner Class | `@apexClassType/NamespacedClass__InnerClass` | Namespace required |
| Custom LWC Type | `lightning__c__CustomTypeName` | Custom component types |
| Currency field | `lightning__currencyType` | For monetary values |
| `datetime` | `lightning__dateTimeStringType` | DateTime values (TDD v2.1.0) |
| `integer` | `lightning__integerType` | Integer numbers (action I/O only) |
| `double` / `number` | `lightning__doubleType` | Decimal/floating-point numbers (action I/O only) |
| `object` (structured) | `lightning__objectType` | Complex data structures (action I/O only) |
| `list` (generic) | `lightning__listType` | Arrays/lists (action I/O only) |

> **† WARNING: #1 Publish Error Source** — Bare `number` works in `variables:` declarations
> but **FAILS at publish** in action `inputs:`/`outputs:`. For action I/O, you MUST use:
> - Integer values → `lightning__integerType`
> - Decimal values → `lightning__doubleType`

> **Naming variance**: Upstream documentation uses `lightning__dateTimeType` while our TDD-validated testing confirms `lightning__dateTimeStringType`. Both may be valid depending on API version — use `lightning__dateTimeStringType` as the tested default.

## Agent Script → Lightning Type Mapping (TDD Validated v2.1.0)

> Use this when troubleshooting type errors between Agent Script action I/O and Apex/Flow targets.

| Agent Script Type | Lightning Type | Apex Type | Notes |
|-------------------|---------------|-----------|-------|
| `string` | `lightning__textType` | `String` | No `complex_data_type_name` needed |
| `number` | `lightning__numberType` | `Decimal` / `Double` | No `complex_data_type_name` needed |
| `boolean` | `lightning__booleanType` | `Boolean` | No `complex_data_type_name` needed |
| `datetime` | `lightning__dateTimeStringType` | `DateTime` | **Actions only** — not valid for variables |
| `date` | `lightning__dateType` | `Date` | Valid for both variables and actions |
| `currency` | `lightning__currencyType` | `Decimal` | Annotated with currency type |

## Flow Type -> Agent Script Mapping (Production-Validated)

> When defining action I/O for `flow://` targets, use this table to map Flow variable types to Agent Script declarations.

| Flow Type | Agent Script Type | `complex_data_type_name` | Notes |
|-----------|------------------|--------------------------|-------|
| `String` | `string` | *(none needed)* | Or `lightning__textType` (optional) |
| `Date` | `object` | `lightning__dateType` | Must use `object`, not `date` |
| `DateTime` | `object` | `lightning__dateTimeStringType` | NOT `lightning__dateTimeType` |
| `Boolean` | `boolean` | *(none needed)* | Primitive type |
| `SObject` collection | `list[object]` | `lightning__recordInfoType` | NOT `lightning__objectType` |

> **Common Mistake**: Using `lightning__textType` for SObject collection outputs. The publisher accepts it but the LLM receives serialized JSON text instead of structured records, breaking field access patterns.

**Pro Tip**: Don't manually edit `complex_data_type_name` - use the UI dropdown in **Agentforce Assets > Action Definition**, then export/import the action definition.
