---
name: sf-metadata
description: >
  Salesforce metadata generation and querying with 120-point scoring.
  TRIGGER when: user creates custom objects, fields, validation rules, or touches
  .object-meta.xml, .field-meta.xml, .profile-meta.xml files.
  DO NOT TRIGGER when: permission set analysis (use sf-permissions), deploying
  metadata (use sf-deploy), or Flow XML (use sf-flow).
license: MIT
metadata:
  version: "1.2.0"
  author: "Jag Valaiyapathy"
  scoring: "120 points across 6 categories"
---

# sf-metadata: Salesforce Metadata Generation and Org Querying

Use this skill when the user needs **metadata definition or org metadata discovery**: custom objects, fields, validation rules, record types, page layouts, permission sets, or schema inspection with `sf` CLI.

## When This Skill Owns the Task

Use `sf-metadata` when the work involves:
- object, field, validation rule, record type, layout, profile, or permission-set metadata
- `.object-meta.xml`, `.field-meta.xml`, `.profile-meta.xml`, and related metadata files
- describing schema before coding or Flow work
- generating metadata XML from requirements

Delegate elsewhere when the user is:
- analyzing permission access rather than defining metadata → [sf-permissions](../sf-permissions/SKILL.md)
- deploying metadata → [sf-deploy](../sf-deploy/SKILL.md)
- editing Flow XML → [sf-flow](../sf-flow/SKILL.md)

---

## Required Context to Gather First

Ask for or infer:
- whether the user wants **generation** or **querying**
- metadata type(s) involved
- target object / field / package directory
- target org alias if querying is required
- whether new custom objects or fields should also include **permission-set / FLS generation**

Unless the user explicitly opts out, assume new custom objects or fields need permission-set follow-up.

---

## Recommended Workflow

### 1. Choose the mode
| Mode | Use when |
|---|---|
| generation | the user wants new or updated metadata XML |
| querying | the user needs object / field / metadata discovery |

### 2. Start from templates or CLI describe data
For generation, use the assets under:
- `assets/objects/`
- `assets/fields/`
- `assets/permission-sets/`
- `assets/profiles/`
- `assets/record-types/`
- `assets/validation-rules/`
- `assets/layouts/`

For querying, prefer `sf` metadata and `sobject describe` commands.

Recent SDR/CLI support worth knowing when reading older examples: `CnfgItemSourceDefinition`, `ExtlClntAppOauthSecuritySettings`, and `UIBundle` are now source-supported under their current names. See [references/metadata-types-reference.md](references/metadata-types-reference.md).

### 3. Validate metadata quality
Check:
- naming conventions
- structural correctness
- field-type fit
- security / FLS implications
- downstream deployment dependencies

### 4. Plan permission impact by default
When new custom fields or objects are created:
- default to generating or updating a Permission Set unless the user opts out
- include `fieldPermissions` for **eligible custom fields**
- note any metadata categories that are excluded because Salesforce treats them as system-managed or always-available
- remember that object CRUD alone does **not** make custom fields visible

### 5. Hand off deployment
Use [sf-deploy](../sf-deploy/SKILL.md) when the user needs the metadata rolled out.

---

## High-Signal Rules

- field-level security is often the hidden blocker after deployment
- **object permissions ≠ field permissions**
- prefer permission sets over profile-centric access patterns
- generate Permission Set follow-up by default for new custom objects and fields
- include `fieldPermissions` for eligible custom fields instead of leaving FLS as a manual afterthought
- avoid hardcoded IDs in formulas or metadata logic
- validation rules should have intentional bypass strategy when operationally necessary
- create metadata before attempting Flow or data tasks that depend on it

---

## Output Format

When finishing, report in this order:
1. **Metadata created or queried**
2. **Files created or updated**
3. **Key schema/security decisions**
4. **Permission / layout follow-ups**
5. **Deploy next step**

Suggested shape:

```text
Metadata task: <generate / query>
Items: <objects, fields, rules, layouts, permsets>
Files: <paths>
Notes: <naming, field types, security, dependencies>
Next step: <deploy, assign permset, or verify in Setup>
```

---

## Cross-Skill Integration

| Need | Delegate to | Reason |
|---|---|---|
| deploy metadata | [sf-deploy](../sf-deploy/SKILL.md) | rollout and validation |
| build Flows on new schema | [sf-flow](../sf-flow/SKILL.md) | declarative automation |
| build Apex on new schema | [sf-apex](../sf-apex/SKILL.md) | code against metadata |
| analyze permission access after creation | [sf-permissions](../sf-permissions/SKILL.md) | access auditing |
| seed data after deploy | [sf-data](../sf-data/SKILL.md) | test data creation |

---

## Reference Map

### Start here
- [references/field-and-cli-reference.md](references/field-and-cli-reference.md)
- [references/metadata-types-reference.md](references/metadata-types-reference.md)
- [references/naming-conventions.md](references/naming-conventions.md)
- [references/orchestration.md](references/orchestration.md)

### Security / scoring / examples
- [references/fls-best-practices.md](references/fls-best-practices.md)
- [references/permset-auto-generation.md](references/permset-auto-generation.md)
- [references/best-practices-scoring.md](references/best-practices-scoring.md)
- [references/field-types-guide.md](references/field-types-guide.md)
- [references/field-types-example.md](references/field-types-example.md)
- [references/custom-object-example.md](references/custom-object-example.md)
- [references/permission-set-example.md](references/permission-set-example.md)
- [references/profile-permission-guide.md](references/profile-permission-guide.md)
- [references/sf-cli-commands.md](references/sf-cli-commands.md)
- [assets/](assets/)

---

## Score Guide

| Score | Meaning |
|---|---|
| 108+ | strong production-ready metadata |
| 96–107 | good metadata with minor review items |
| 84–95 | acceptable but validate carefully |
| < 84 | block deployment until corrected |
