<!-- Parent: sf-metadata/SKILL.md -->

# Best Practices & Scoring Details (120 Points)

## Category Breakdown

**Structure & Format** (20 points):
- Valid XML syntax (-10 if invalid)
- Correct Salesforce namespace: `http://soap.sforce.com/2006/04/metadata` (-5 if missing)
- API version present and >= 65.0 (-5 if outdated)
- Correct file path and naming structure (-5 if wrong)

**Naming Conventions** (20 points):
- Custom objects/fields end with `__c` (-3 each violation)
- Use PascalCase for API names: `Account_Status__c` not `account_status__c` (-2 each)
- Meaningful labels (no abbreviations like `Acct`, `Sts`) (-2 each)
- Relationship names follow pattern: `[ParentObject]_[ChildObjects]` (-3)

**Data Integrity** (20 points):
- Required fields have sensible defaults or validation (-5)
- Number fields have appropriate precision/scale (-3)
- Picklist values properly defined with labels (-3)
- Relationship delete constraints specified (SetNull, Restrict, Cascade) (-3)
- Formula field syntax valid (-5)
- Roll-up summaries reference correct fields (-3)

**Security & FLS** (20 points):
- Field-Level Security considerations documented (-5 if sensitive field exposed)
- Sensitive field types flagged (SSN patterns, Credit Card patterns) (-10)
- Object sharing model appropriate for data sensitivity (-5)
- Permission Sets preferred over Profile modifications (advisory)

**Documentation** (20 points):
- Description present and meaningful on objects/fields (-5 if missing)
- Help text for user-facing fields (-3 each)
- Clear error messages for validation rules (-3)
- Inline comments in complex formulas (-3)

**Best Practices** (20 points):
- Use Permission Sets over Profiles when possible (-3 if Profile-first)
- Avoid hardcoded Record IDs in formulas (-5 if found)
- Use Global Value Sets for reusable picklists (advisory)
- Master-Detail vs Lookup selection appropriate for use case (-3)
- Record Types have associated Page Layouts (-3)

## Scoring Thresholds

| Rating | Score | Action |
|--------|-------|--------|
| Excellent | 108+ | Production-ready |
| Very Good | 96-107 | Minor improvements |
| Good | 84-95 | Acceptable, needs work |
| Below Standard | 72-83 | Address before deploy |
| Block | <72 | CRITICAL issues |

---

## Field Template Tips

### Number Field: Omit Empty Defaults

Don't include `<defaultValue>` if it's empty or zero — Salesforce ignores it:

```xml
<!-- WRONG: Empty default is ignored, adds noise -->
<CustomField>
    <fullName>Score__c</fullName>
    <type>Number</type>
    <precision>3</precision>
    <scale>0</scale>
    <defaultValue></defaultValue>  <!-- Remove this! -->
</CustomField>

<!-- CORRECT: Omit defaultValue entirely if not needed -->
<CustomField>
    <fullName>Score__c</fullName>
    <type>Number</type>
    <precision>3</precision>
    <scale>0</scale>
</CustomField>

<!-- CORRECT: Include defaultValue only if you need a specific value -->
<CustomField>
    <fullName>Priority__c</fullName>
    <type>Number</type>
    <precision>1</precision>
    <scale>0</scale>
    <defaultValue>3</defaultValue>  <!-- Meaningful default -->
</CustomField>
```

### Standard vs Custom Object Paths

| Object Type | Path Example |
|-------------|--------------|
| Standard (Lead) | `objects/Lead/fields/Lead_Score__c.field-meta.xml` |
| Custom | `objects/MyObject__c/fields/MyField__c.field-meta.xml` |

**Common Mistake**: Using `Lead__c` (with suffix) for standard Lead object.
