<!-- Parent: sf-flow/SKILL.md -->
# Flow Quick Reference

A comprehensive cheat sheet for Salesforce Flow development. Use this guide for quick decisions on flow types, elements, and variables.

---

## Flow Type Selection Decision Tree

```
┌─────────────────────────────────────────────────────────────────────────┐
│ WHICH FLOW TYPE SHOULD I USE?                                           │
└─────────────────────────────────────────────────────────────────────────┘

Need to gather user input?
├─ YES ──────────────────────────────────────────► SCREEN FLOW
│                                                   └─ Foreground execution
│                                                   └─ Users see and interact
│
└─ NO ─► Need multi-step, multi-user workflow?
         ├─ YES ─────────────────────────────────► FLOW ORCHESTRATION
         │                                          └─ Multi-stage approvals
         │                                          └─ Sequential user tasks
         │
         └─ NO ─► Record created, updated, or deleted?
                  ├─ YES ────────────────────────► RECORD-TRIGGERED FLOW
                  │    │
                  │    ├─ Modify same record? ──► Before-Save Trigger
                  │    │    └─ No DML required
                  │    │    └─ Field updates, validation
                  │    │
                  │    └─ Modify related records? ► After-Save Trigger
                  │         └─ DML on other objects
                  │         └─ Callouts, emails
                  │
                  └─ NO ─► Run on a schedule?
                           ├─ YES ──────────────► SCHEDULE-TRIGGERED FLOW
                           │                       └─ Runs once/daily/weekly
                           │                       └─ Batch processing
                           │
                           └─ NO ─► Platform Event received?
                                    ├─ YES ─────► PLATFORM EVENT-TRIGGERED
                                    │              └─ Event-driven automation
                                    │              └─ Async processing
                                    │
                                    └─ NO ──────► AUTOLAUNCHED FLOW
                                                   └─ Called from Apex/REST
                                                   └─ Called from other flows
                                                   └─ Agent actions
```

---

## Flow Type Quick Reference

| Flow Type | Trigger | Use Case | Execution |
|-----------|---------|----------|-----------|
| **Screen Flow** | User clicks button/link | Forms, wizards, guided processes | Foreground |
| **Record-Triggered (Before)** | Record DML (before commit) | Same-record validation, field defaults | Background |
| **Record-Triggered (After)** | Record DML (after commit) | Related records, callouts, emails | Background |
| **Schedule-Triggered** | Time-based (cron) | Batch updates, cleanup, notifications | Background |
| **Platform Event-Triggered** | Platform Event published | Event-driven processing, async work | Background |
| **Autolaunched** | Code/Flow invocation | Subflows, Apex-called, REST API | Background |
| **Flow Orchestration** | Multi-step workflow | Approvals, multi-user processes | Background |

---

## Flow Elements Reference

### Logic Elements (Flow Control)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ LOGIC ELEMENTS                                                          │
├──────────────────┬──────────────────────────────────────────────────────┤
│ Assignment       │ Set variable values; update data as flow progresses │
│                  │ Example: var_Total = var_Subtotal * 1.08             │
├──────────────────┼──────────────────────────────────────────────────────┤
│ Decision         │ IF/THEN/ELSE routing; branch flow paths             │
│                  │ Example: If Amount > 10000 → High Priority path     │
├──────────────────┼──────────────────────────────────────────────────────┤
│ Loop             │ Iterate through collections; per-record processing  │
│                  │ Example: For each Contact in collection...          │
│                  │ USE WHEN: Per-record decisions, counters, flags     │
├──────────────────┼──────────────────────────────────────────────────────┤
│ Collection Sort  │ Organize collection by specified field              │
│                  │ Example: Sort Accounts by AnnualRevenue DESC        │
├──────────────────┼──────────────────────────────────────────────────────┤
│ Collection Filter│ Create filtered subset without new SOQL query       │
│                  │ Example: Filter Opps where Amount > 5000            │
│                  │ TIP: Use after Get Records to reduce governor use   │
├──────────────────┼──────────────────────────────────────────────────────┤
│ Transform        │ Map fields and transform collections (bulk)         │
│                  │ Example: Map Contact fields → Lead fields           │
│                  │ USE WHEN: Data mapping, bulk assignments            │
│                  │ 30-50% faster than Loop for field mapping           │
├──────────────────┼──────────────────────────────────────────────────────┤
│ Custom Error     │ Display error message and stop flow execution       │
│                  │ Example: "Amount must be greater than zero"         │
└──────────────────┴──────────────────────────────────────────────────────┘
```

### Data Elements (CRUD Operations)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ DATA ELEMENTS                                                           │
├──────────────────┬──────────────────────────────────────────────────────┤
│ Get Records      │ Query database (SOQL equivalent)                    │
│                  │ TIP: Use filters! Unfiltered = governor limit risk  │
│                  │ TIP: Can't traverse parent fields (use 2-step)      │
├──────────────────┼──────────────────────────────────────────────────────┤
│ Create Records   │ Insert new records; supports collections            │
│                  │ Example: Create Case from Opportunity data          │
├──────────────────┼──────────────────────────────────────────────────────┤
│ Update Records   │ Modify existing records                             │
│                  │ In Before-Save: No DML needed for trigger record    │
│                  │ In After-Save: Use for related records              │
├──────────────────┼──────────────────────────────────────────────────────┤
│ Delete Records   │ Remove records from database                        │
│                  │ Example: Delete old cases older than 2 years        │
├──────────────────┼──────────────────────────────────────────────────────┤
│ Roll Back Records│ Undo pending changes in current transaction         │
│                  │ Use in fault paths for multi-step DML rollback      │
└──────────────────┴──────────────────────────────────────────────────────┘
```

### Interaction Elements (UI & External)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ INTERACTION ELEMENTS                                                    │
├──────────────────┬──────────────────────────────────────────────────────┤
│ Screen           │ UI canvas with standard/custom components           │
│                  │ Supports: Text, Input, Picklist, Checkbox, LWC      │
│                  │ TIP: Use Stage resource for multi-screen progress   │
├──────────────────┼──────────────────────────────────────────────────────┤
│ Action           │ Call external processes                             │
│                  │ Built-in: Send Email, Submit for Approval           │
│                  │ Custom: Apex @InvocableMethod                       │
├──────────────────┼──────────────────────────────────────────────────────┤
│ Subflow          │ Call another flow with input/output variables       │
│                  │ Use for: Reusable logic, modular architecture       │
│                  │ See: references/subflow-library.md for pre-built subflows │
├──────────────────┼──────────────────────────────────────────────────────┤
│ Wait             │ Pause flow execution until condition met            │
│                  │ Types: Duration, Date, Platform Event               │
│                  │ See: references/wait-patterns.md for XML patterns         │
└──────────────────┴──────────────────────────────────────────────────────┘
```

---

## Variable Types Reference

```
┌─────────────────────────────────────────────────────────────────────────┐
│ FLOW RESOURCE TYPES                                                     │
├────────────────────┬────────────────────────────────────────────────────┤
│ Type               │ Description & Use Case                            │
├────────────────────┼────────────────────────────────────────────────────┤
│ Variable           │ Mutable container for data that changes           │
│                    │ Types: Text, Number, Date, DateTime, Boolean,     │
│                    │        Currency, Record, Collection               │
│                    │ Naming: var_AccountName, col_Contacts, rec_Lead   │
├────────────────────┼────────────────────────────────────────────────────┤
│ Constant           │ Immutable value (set once, never changes)         │
│                    │ Use: Fixed rates, status codes, thresholds        │
│                    │ Example: con_TaxRate = 0.08                        │
├────────────────────┼────────────────────────────────────────────────────┤
│ Formula            │ Calculated result from variables/constants        │
│                    │ Example: frm_Total = var_Subtotal * (1 + con_Tax) │
├────────────────────┼────────────────────────────────────────────────────┤
│ Text Template      │ Dynamic text with variable interpolation          │
│                    │ Use: Email bodies, notifications, messages        │
│                    │ Example: "Hello {!var_FirstName}, order ready"    │
├────────────────────┼────────────────────────────────────────────────────┤
│ Choice             │ Single picklist/radio option (label + value)      │
│                    │ Use: Screen flow input controls                   │
│                    │ Example: { Label: "High", Value: "1" }            │
├────────────────────┼────────────────────────────────────────────────────┤
│ Collection Choice  │ Options populated from existing Collection        │
│ Set                │ Use: Dynamic dropdown from variable data          │
├────────────────────┼────────────────────────────────────────────────────┤
│ Record Choice Set  │ Options from SOQL query built into resource       │
│                    │ Use: Query-based selection (e.g., Account list)   │
├────────────────────┼────────────────────────────────────────────────────┤
│ Picklist Choice    │ Uses standard object picklist field values        │
│ Set                │ Use: Industry, Stage, Status dropdowns            │
├────────────────────┼────────────────────────────────────────────────────┤
│ Stage              │ Progress tracking across multiple screens         │
│                    │ Use: Multi-screen wizards with visual progress    │
│                    │ Example: Identity → Configuration → Payment       │
└────────────────────┴────────────────────────────────────────────────────┘
```

### Variable Naming Conventions

| Prefix | Type | Example |
|--------|------|---------|
| `var_` | Single variable | `var_AccountName` |
| `col_` | Collection | `col_Contacts` |
| `rec_` | Record variable | `rec_CurrentLead` |
| `inp_` | Input variable | `inp_RecordId` |
| `out_` | Output variable | `out_ResultMessage` |
| `con_` | Constant | `con_MaxRetries` |
| `frm_` | Formula | `frm_DiscountedPrice` |

---

## Governor Limit Optimization Patterns

### Pattern 1: Collection Filter vs Get Records in Loop

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ❌ ANTI-PATTERN: Get Records Inside Loop                               │
└─────────────────────────────────────────────────────────────────────────┘

    Loop (Accounts)
    └── Get Records (Contacts WHERE AccountId = current Account)
        └── ⚠️ SOQL limit: 100 queries per transaction!

┌─────────────────────────────────────────────────────────────────────────┐
│ ✅ BEST PRACTICE: Query Once + Collection Filter                       │
└─────────────────────────────────────────────────────────────────────────┘

    Get Records (All Contacts for Account IDs in collection)
    └── 1 SOQL query total
    Loop (Accounts)
    └── Collection Filter (Contacts WHERE AccountId = current)
        └── In-memory filtering, no SOQL!
```

### Pattern 2: Entry Criteria for Record-Triggered Flows

```
Always use Entry Criteria to limit when flows run:

┌─────────────────────────────────────────────────────────────────────────┐
│ Entry Criteria Examples                                                 │
├─────────────────────────────────────────────────────────────────────────┤
│ Run only when Status changes:                                          │
│   ISNEW() || ISCHANGED({!$Record.Status})                             │
├─────────────────────────────────────────────────────────────────────────┤
│ Run only for specific record types:                                    │
│   {!$Record.RecordType.DeveloperName} = 'Enterprise'                  │
├─────────────────────────────────────────────────────────────────────────┤
│ Skip during data loads (bypass pattern):                               │
│   {!$Setup.Flow_Bypass__c.Bypass_All__c} = FALSE                      │
└─────────────────────────────────────────────────────────────────────────┘
```

### Pattern 3: Transform vs Loop Decision

```
┌─────────────────────────────────────────────────────────────────────────┐
│ When to Use Transform vs Loop                                          │
├───────────────────────────────┬─────────────────────────────────────────┤
│ USE TRANSFORM (30-50% faster) │ USE LOOP                                │
├───────────────────────────────┼─────────────────────────────────────────┤
│ Data mapping/shaping          │ Per-record IF/ELSE decisions            │
│ Bulk field assignments        │ Counters, flags, state tracking         │
│ Simple formula calculations   │ Varying business rules per record       │
│ Record type conversion        │ Complex conditional transformations     │
└───────────────────────────────┴─────────────────────────────────────────┘

See: references/transform-vs-loop-guide.md for detailed decision criteria
```

---

## Before-Save vs After-Save Triggers

```
┌─────────────────────────────────────────────────────────────────────────┐
│ BEFORE-SAVE TRIGGER                                                     │
├─────────────────────────────────────────────────────────────────────────┤
│ When: Before record is committed to database                           │
│ Can modify: Trigger record only ($Record)                              │
│ DML needed: NO (changes auto-saved with record)                        │
│ Use for:                                                               │
│   • Field defaulting and auto-population                               │
│   • Validation and Custom Errors                                       │
│   • Same-record field calculations                                     │
│   • Preventing record creation (throw error)                           │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ AFTER-SAVE TRIGGER                                                      │
├─────────────────────────────────────────────────────────────────────────┤
│ When: After record is committed (has ID)                               │
│ Can modify: Related/child records, external systems                    │
│ DML needed: YES (explicit Create/Update/Delete required)               │
│ Use for:                                                               │
│   • Creating child records                                             │
│   • Updating parent/related records                                    │
│   • Sending emails, notifications                                      │
│   • HTTP callouts to external systems                                  │
│   ⚠️ CAUTION: Updating same object can cause infinite loop!           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Common Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| DML in Loop | Governor limit failure | Collect records, single DML after loop |
| SOQL in Loop | Query limit exceeded | Query all data upfront, filter in memory |
| No fault paths | Silent failures | Add fault connector to all DML elements |
| No entry criteria | Runs on every update | Use ISCHANGED() or field conditions |
| After-Save same object | Infinite recursion | Add recursion check or use Before-Save |
| Hardcoded IDs | Fails in different orgs | Use Custom Metadata or Custom Labels |
| Unfiltered Get Records | Too many records | Always add filter conditions |
| Loop for field mapping | Slower processing | Use Transform element instead |

---

## Quick Reference: Element Connectors

| Element | Connector Types |
|---------|-----------------|
| Decision | One per outcome + Default |
| Loop | `nextValueConnector` (each item) + `noMoreValuesConnector` (after last) |
| Get Records | `connector` (records found) + `faultConnector` (error) |
| Create/Update/Delete | `connector` (success) + `faultConnector` (error) |
| Screen | `connector` (next) |
| Wait | `waitEvents` with `connector` per condition |

---

## Testing Checklist Quick Reference

```
□ Path Coverage
  □ All Decision outcomes tested
  □ Loop with 0, 1, many records
  □ Fault paths triggered

□ Bulk Testing (Record-Triggered)
  □ 1 record
  □ 10 records
  □ 50 records
  □ 200+ records (governor limit boundary)

□ User Context
  □ Standard User profile
  □ Admin profile
  □ FLS restrictions applied

□ Edge Cases
  □ Null/empty values
  □ Maximum field lengths
  □ Special characters
```

---

## Related Documentation

| Topic | Document |
|-------|----------|
| Transform vs Loop | [transform-vs-loop-guide.md](./transform-vs-loop-guide.md) |
| Best Practices | [flow-best-practices.md](./flow-best-practices.md) |
| Testing Guide | [testing-guide.md](./testing-guide.md) |
| Governance | [governance-checklist.md](./governance-checklist.md) |
| Subflow Library | [subflow-library.md](./subflow-library.md) |
| Wait Patterns | [wait-patterns.md](./wait-patterns.md) |
| LWC Integration | [lwc-integration-guide.md](./lwc-integration-guide.md) |

---

## Attribution

Content adapted from:
- **Salesforce Ben** - [Flow Cheat Sheet](https://www.salesforceben.com/salesforce-flow-cheat-sheet-examples-infographic/)
- **Official Salesforce Documentation** - Flow Builder Guide

See [CREDITS.md](../CREDITS.md) for full attribution.
