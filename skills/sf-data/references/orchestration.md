<!-- Parent: sf-data/SKILL.md -->
# Multi-Skill Orchestration: sf-data Perspective

This document details how sf-data fits into the multi-skill workflow for Salesforce development.

---

## Standard Orchestration Order

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  STANDARD MULTI-SKILL ORCHESTRATION ORDER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. sf-metadata                                                             │
│     └── Create object/field definitions (LOCAL files)                       │
│                                                                             │
│  2. sf-flow                                                                 │
│     └── Create flow definitions (LOCAL files)                               │
│                                                                             │
│  3. sf-deploy                                                               │
│     └── Deploy all metadata (REMOTE)                                        │
│                                                                             │
│  4. sf-data  ◀── YOU ARE HERE (LAST!)                                      │
│     └── Create test data (REMOTE - objects must exist!)                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚠️ Why sf-data Goes LAST

**sf-data operates on REMOTE org data.** Objects/fields must be deployed before sf-data can:
- Insert records
- Query existing data
- Run test factories
- Generate bulk test data

```
ERROR: "SObject type 'Quote__c' is not supported"
CAUSE: Quote__c object was never deployed to the org
FIX:   Run sf-deploy BEFORE sf-data
```

---

## Common Errors from Wrong Order

| Error | Cause | Fix |
|-------|-------|-----|
| `SObject type 'X' not supported` | Object not deployed | Deploy via sf-deploy first |
| `INVALID_FIELD: No such column 'Field__c'` | Field not deployed OR FLS | Deploy field + Permission Set |
| `REQUIRED_FIELD_MISSING` | Validation rule requires field | Include all required fields |
| `FIELD_CUSTOM_VALIDATION_EXCEPTION` | Validation rule triggered | Use valid test data values |

---

## Test Data After Triggers/Flows

When testing triggers or flows, always create test data AFTER deployment:

```
1. sf-apex   → Create trigger handler class
2. sf-flow   → Create record-triggered flow
3. sf-deploy → Deploy trigger + flow + objects
4. sf-data   ◀── CREATE TEST DATA NOW
              └── Triggers and flows will fire!
```

**Why?** Test data insertion triggers flows/triggers. If those aren't deployed, you're not testing realistic behavior.

---

## The 251-Record Pattern

Always test with **251 records** to cross the 200-record batch boundary:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  BATCH BOUNDARY TESTING                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Records 1-200:    First batch                                              │
│  Records 201-251:  Second batch (crosses boundary!)                         │
│                                                                             │
│  Tests: N+1 queries, bulkification, governor limits                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Command:**
```bash
sf apex run --file test-factory.apex --target-org alias
# test-factory.apex creates 251 records
```

---

## Cross-Skill Integration Table

| From Skill | To sf-data | When |
|------------|------------|------|
| sf-apex | → sf-data | "Create 251 Accounts for bulk testing" |
| sf-flow | → sf-data | "Create Opportunities with StageName='Closed Won'" |
| sf-testing | → sf-data | "Generate test records for test class" |

| From sf-data | To Skill | When |
|--------------|----------|------|
| sf-data | → sf-metadata | "Describe Invoice__c" (discover object structure) |
| sf-data | → sf-deploy | "Redeploy field after adding validation rule" |

---

## Prerequisites Check

Before using sf-data, verify:

```bash
# Check org connection
sf org display --target-org alias

# Check objects exist
sf sobject describe --sobject MyObject__c --target-org alias --json

# Check field-level security (if field not visible)
sf data query --query "SELECT Id FROM FieldPermissions WHERE SobjectType='MyObject__c'" --use-tooling-api --target-org alias
```

---

## Factory Pattern Integration

Test Data Factory classes work with sf-data:

```
sf-apex:  Creates TestDataFactory_Account.cls
          ↓
sf-deploy: Deploys factory class
          ↓
sf-data:  Calls factory via Anonymous Apex
          ↓
          251 records created → triggers fire → flows run
```

**Anonymous Apex:**
```apex
List<Account> accounts = TestDataFactory_Account.create(251);
System.debug('Created ' + accounts.size() + ' accounts');
```

---

## Cleanup Sequence

After testing, clean up in reverse order:

```
1. sf-data   → Delete test records
2. sf-deploy → Deactivate flows (if needed)
3. sf-deploy → Remove test metadata (if needed)
```

**Cleanup command:**
```bash
sf apex run --file cleanup.apex --target-org alias
# cleanup.apex: DELETE [SELECT Id FROM Account WHERE Name LIKE 'Test%']
```

---

## Related Documentation

| Topic | Location |
|-------|----------|
| Test data patterns | `sf-data/references/test-data-patterns.md` |
| Cleanup guide | `sf-data/references/cleanup-rollback-guide.md` |
| Factory templates | `sf-data/assets/factories/` |
