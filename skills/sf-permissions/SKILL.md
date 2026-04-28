---
name: sf-permissions
description: >
  Permission Set analysis, hierarchy viewer, and access auditing.
  TRIGGER when: user asks "who has access to X?", analyzes permission sets/groups,
  or touches .permissionset-meta.xml / .permissionsetgroup-meta.xml files.
  DO NOT TRIGGER when: creating new metadata (use sf-metadata), deploying
  permission sets (use sf-deploy), or Apex sharing logic (use sf-apex).
license: MIT
metadata:
  version: "1.1.0"
  author: "Jag Valaiyapathy"
  inspiration: "PSLab by Oumaima Arbani (github.com/OumArbani/PSLab)"
---

# sf-permissions

Use this skill when the user needs **permission analysis and access auditing**: Permission Set / Permission Set Group hierarchy views, “who has access to X?” investigations, user-permission analysis, or permission-set metadata review.

## When This Skill Owns the Task

Use `sf-permissions` when the work involves:
- permission set / permission set group analysis
- user access investigation
- finding which permission grants object / field / Apex / flow / tab / custom-permission access
- auditing or exporting permission configuration
- reviewing permission metadata impacts

Delegate elsewhere when the user is:
- creating new metadata definitions → [sf-metadata](../sf-metadata/SKILL.md)
- deploying permission sets → [sf-deploy](../sf-deploy/SKILL.md)
- analyzing Apex-managed sharing logic → [sf-apex](../sf-apex/SKILL.md)

---

## Required Context to Gather First

Ask for or infer:
- target org alias
- whether the question is about an object, field, Apex class, flow, tab, custom permission, or specific user
- whether the goal is hierarchy visualization, access detection, export, or metadata generation
- whether the output should be terminal-focused or documentation-friendly

---

## Recommended Workflow

### 1. Classify the request
| Request shape | Default capability |
|---|---|
| “who has access to X?” | permission detector |
| “what does this user have?” | user analyzer |
| “show me the hierarchy” | hierarchy viewer |
| “export this permset” | exporter |
| “generate metadata from analysis” | generator or handoff |

### 2. Connect to the correct org
Verify `sf` auth before running permission analysis.

### 3. Use the narrowest useful query
Prefer focused analysis over broad org-wide scans unless the user explicitly wants a full audit.

When choosing identifiers, prefer stable metadata names first:
- `PermissionSet.Name`
- `PermissionSetGroup.DeveloperName`
- `CustomPermission.DeveloperName`
- object and field API names such as `Account` or `Account.AnnualRevenue`
- `Assignee.Username` / email for user-centric checks

Use Salesforce record IDs only when:
- the underlying object model requires `ParentId` or `SetupEntityId`, or
- you are drilling into records returned by a prior read-only query in the same investigation

### 4. Render findings clearly
Use:
- ASCII tree or table output for terminal work
- Mermaid only when documentation benefit is clear
- concise summaries of which permission source grants access

### 5. Hand off creation or deployment work
Use:
- [sf-metadata](../sf-metadata/SKILL.md) for richer metadata generation
- [sf-deploy](../sf-deploy/SKILL.md) for deployment

---

## High-Signal Rules

- distinguish direct Permission Set grants from grants via Permission Set Groups
- prefer `Name` / `DeveloperName` / API names over org-specific record IDs for first-pass investigation queries
- be explicit about whether access is object-level, field-level, class-level, flow-level, or custom-permission-based
- use Tooling API where required for setup entities and advanced visibility questions
- for agent access questions, verify exact agent-name matching in permission metadata
- when a follow-up child query requires `ParentId` or `SetupEntityId`, resolve the ID from a prior result instead of starting with copied IDs

---

## Output Format

When finishing, report in this order:
1. **What was analyzed**
2. **Org / subject scope**
3. **Which permissions grant access**
4. **Whether access is direct or inherited**
5. **Recommended follow-up**

Suggested shape:

```text
Permission analysis: <hierarchy / detect / user / export>
Scope: <org, user, permission target>
Findings: <permsets / groups / access level>
Source: <direct assignment or via group>
Next step: <export, generate metadata, or deploy changes>
```

---

## Cross-Skill Integration

| Need | Delegate to | Reason |
|---|---|---|
| generate or modify permission metadata | [sf-metadata](../sf-metadata/SKILL.md) | metadata authoring |
| deploy permission changes | [sf-deploy](../sf-deploy/SKILL.md) | rollout |
| identify Apex classes needing grants | [sf-apex](../sf-apex/SKILL.md) | implementation context |
| bulk user assignment analysis | [sf-data](../sf-data/SKILL.md) | larger data operations |

---

## Reference Map

### Start here
- [references/permission-model.md](references/permission-model.md)
- [references/soql-reference.md](references/soql-reference.md)
- [references/workflow-examples.md](references/workflow-examples.md)

### Specialized analysis
- [references/agent-access-guide.md](references/agent-access-guide.md)
- [references/usage-examples.md](references/usage-examples.md)

---

## Score Guide

| Score | Meaning |
|---|---|
| 90+ | strong permission analysis with clear access sourcing |
| 75–89 | useful audit with minor gaps |
| 60–74 | partial visibility only |
| < 60 | insufficient evidence; expand analysis |
