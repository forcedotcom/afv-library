<!-- Parent: sf-metadata/SKILL.md -->

# Field Type Guide, Relationships & CLI Reference

## Field Type Selection Guide

| Type | Salesforce | Notes |
|------|------------|-------|
| Text | Text / Text Area (Long/Rich) | ≤255 chars / multi-line / HTML |
| Numbers | Number / Currency | Decimals or money (org currency) |
| Boolean | Checkbox | True/False |
| Choice | Picklist / Multi-Select | Single/multiple predefined options |
| Date | Date / DateTime | With or without time |
| Contact | Email / Phone / URL | Validated formats |
| Relationship | Lookup / Master-Detail | Optional / required parent |
| Calculated | Formula / Roll-Up | Derived from fields / children |

## Relationship Decision Matrix

| Scenario | Use | Reason |
|----------|-----|--------|
| Parent optional | Lookup | Child can exist without parent |
| Parent required | Master-Detail | Cascade delete, roll-up summaries |
| Many-to-Many | Junction Object | Two Master-Detail relationships |
| Self-referential | Hierarchical Lookup | Same object (e.g., Account hierarchy) |
| Cross-object formula | Master-Detail or Formula | Access parent fields |

## Common Validation Rule Patterns

| Pattern | Formula | Use |
|---------|---------|-----|
| Conditional Required | `AND(ISPICKVAL(Status,'Closed'), ISBLANK(Close_Date__c))` | Field required when condition met |
| Email Regex | `NOT(REGEX(Email__c, "^[a-zA-Z0-9._-]+@..."))` | Format validation |
| Future Date | `Due_Date__c < TODAY()` | Date constraints |
| Cross-Object | `AND(Account.Type != 'Customer', Amount__c > 100000)` | Related field checks |

---

## sf CLI Quick Reference

### Object & Field Queries

```bash
# Describe standard or custom object
sf sobject describe --sobject Account --target-org [alias] --json

# List all custom objects
sf org list metadata --metadata-type CustomObject --target-org [alias] --json

# List all custom fields on an object
sf org list metadata --metadata-type CustomField --folder Account --target-org [alias] --json
```

### Metadata Operations

```bash
# List all metadata types available
sf org list metadata-types --target-org [alias] --json

# Retrieve specific metadata
sf project retrieve start --metadata CustomObject:Account --target-org [alias]

# Generate package.xml from source
sf project generate manifest --source-dir force-app --name package.xml
```

### Interactive Generation

```bash
# Generate custom object interactively
sf schema generate sobject --label "My Object"

# Generate custom field interactively
sf schema generate field --label "My Field" --object Account
```
