<!-- Parent: sf-metadata/SKILL.md -->
# Field-Level Security (FLS) Best Practices

## Overview

Field-Level Security (FLS) controls which users can view and edit specific fields on records. Proper FLS configuration is essential for data security and compliance.

---

## Understanding FLS

### Two Levels of Field Access
1. **Readable**: User can see the field value
2. **Editable**: User can modify the field value (implies readable)

### FLS vs Object Permissions
```
User Access = Object Permissions + Field-Level Security + Record Access

Object Permissions: Can user access the object at all?
FLS: Can user see/edit specific fields?
Record Access: Can user access specific records?
```

### Where FLS is Configured
- Profiles (base access)
- Permission Sets (additive access)
- Permission Set Groups (combined sets)

---

## Best Practices

### 1. Use Permission Sets Over Profiles

**Why:**
- Profiles are monolithic and hard to maintain
- Permission Sets are additive and composable
- Easier to manage feature-based access

**Pattern:**
```
Profile: Base access (read-only on most fields)
Permission Set: Feature-specific edit access
```

**Example:**
```xml
<!-- Permission Set for Invoice Editors -->
<PermissionSet>
    <label>Invoice Editor</label>
    <fieldPermissions>
        <editable>true</editable>
        <field>Invoice__c.Amount__c</field>
        <readable>true</readable>
    </fieldPermissions>
    <fieldPermissions>
        <editable>true</editable>
        <field>Invoice__c.Status__c</field>
        <readable>true</readable>
    </fieldPermissions>
</PermissionSet>
```

---

### 2. Principle of Least Privilege

**Rule:** Grant minimum access needed for the job function

**Steps:**
1. Start with no access
2. Add read access where needed
3. Add edit access only where required
4. Review periodically

**Anti-Pattern:**
```xml
<!-- DON'T: Grant edit on everything -->
<fieldPermissions>
    <editable>true</editable>
    <field>Account.AnnualRevenue</field>
    <readable>true</readable>
</fieldPermissions>
```

**Better:**
```xml
<!-- DO: Grant read-only unless edit is required -->
<fieldPermissions>
    <editable>false</editable>
    <field>Account.AnnualRevenue</field>
    <readable>true</readable>
</fieldPermissions>
```

---

### 3. Protect Sensitive Fields

#### Identify Sensitive Fields
| Category | Examples |
|----------|----------|
| PII | SSN, Date of Birth, Driver's License |
| Financial | Bank Account, Credit Card, Salary |
| Health | Medical conditions, Insurance |
| Security | Password, Token, API Key |
| Business | Trade secrets, Pricing formulas |

#### Protection Strategies

1. **Restrict to Specific Permission Sets**
```xml
<PermissionSet>
    <label>PII_Access</label>
    <description>Access to sensitive PII fields</description>
    <fieldPermissions>
        <editable>false</editable>
        <field>Contact.SSN__c</field>
        <readable>true</readable>
    </fieldPermissions>
</PermissionSet>
```

2. **Use Shield Platform Encryption**
- Encrypts data at rest
- Searchable with deterministic encryption
- Requires Shield license

3. **Use Classic Encryption (Encrypted Text Field)**
- Masks display (shows last 4 characters)
- Limited functionality
- No additional license needed

---

### 4. FLS in Apex Code

#### Always Check FLS in Apex

**With SOQL:**
```apex
// Good: Respects FLS
List<Account> accounts = [
    SELECT Name, Industry
    FROM Account
    WITH USER_MODE
];

// Alternative: Security.stripInaccessible
List<Account> accounts = [SELECT Name, Industry, Revenue FROM Account];
SObjectAccessDecision decision = Security.stripInaccessible(
    AccessType.READABLE,
    accounts
);
List<Account> safeAccounts = decision.getRecords();
```

**With DML:**
```apex
// Good: Respects FLS
Database.insert(accounts, AccessLevel.USER_MODE);

// Alternative: Check before DML
if (Schema.sObjectType.Account.fields.Industry.isUpdateable()) {
    account.Industry = 'Technology';
}
```

---

### 5. Organize Permission Sets by Function

**Pattern:**
```
[Object]_[AccessLevel]
[Feature]_[Role]
[Integration]_Access
```

**Example Structure:**
```
Permission Sets/
├── Account_Read_Only.permissionset-meta.xml
├── Account_Full_Access.permissionset-meta.xml
├── Invoice_Approver.permissionset-meta.xml
├── Invoice_Creator.permissionset-meta.xml
├── ERP_Integration_Access.permissionset-meta.xml
└── Reports_Power_User.permissionset-meta.xml
```

---

### 6. Use Permission Set Groups

**Why:**
- Combine related permission sets
- Easier role-based assignment
- Single assignment per user role

**Example:**
```
Permission Set Group: Sales_Representative
├── Account_Full_Access
├── Contact_Full_Access
├── Opportunity_Full_Access
├── Quote_Creator
└── Reports_Basic
```

---

### 7. Handle Formula Fields Correctly

**Important:** Formula fields inherit FLS from referenced fields

```
Formula: Account.Owner.Manager.Name

User needs READ access to:
- Account.OwnerId
- User.ManagerId
- User.Name (on Manager)
```

**Best Practice:** Test formulas with different user profiles

---

### 8. Document FLS Decisions

**For each sensitive field, document:**
- Why it exists
- Who should have access
- Which permission sets grant access
- Review date

**Example:**
```xml
<CustomField>
    <fullName>SSN__c</fullName>
    <description>
        Social Security Number - SENSITIVE
        Access: HR_PII_Access permission set only
        Review: Quarterly by Security team
    </description>
</CustomField>
```

---

## Common Mistakes

### 1. Relying on Page Layout for Security
```
❌ "Users can't see it because it's not on the layout"
✅ FLS controls true visibility; layouts are UX only
```

### 2. Granting Edit Without Business Need
```
❌ "Give them edit just in case they need it"
✅ Start read-only, add edit when requested
```

### 3. Not Checking FLS in Apex
```
❌ Assuming controller/trigger runs as system
✅ Always use WITH USER_MODE or Security.stripInaccessible
```

### 4. Over-Using System Administrator
```
❌ "Just use System Admin profile"
✅ Create specific permission sets for each function
```

### 5. Not Testing FLS Changes
```
❌ Deploy FLS changes without testing
✅ Test with actual user profiles before deploy
```

---

## FLS Audit Checklist

### For Each Object

- [ ] All fields reviewed for sensitivity
- [ ] Sensitive fields have restricted access
- [ ] Permission Sets exist for each access pattern
- [ ] No unnecessary edit permissions
- [ ] Formula fields tested with limited users
- [ ] Integration users have minimal required access

### For Apex Code

- [ ] All SOQL uses WITH USER_MODE or stripInaccessible
- [ ] All DML uses USER_MODE or checks isUpdateable()
- [ ] Tests verify FLS enforcement
- [ ] No hardcoded field access bypass

### For Deployment

- [ ] FLS changes reviewed by security team
- [ ] Changes tested with representative users
- [ ] Rollback plan exists
- [ ] Documentation updated

---

## Quick Reference

### SOQL FLS Modes
| Mode | Behavior |
|------|----------|
| `WITH USER_MODE` | Enforces FLS and sharing |
| `WITH SYSTEM_MODE` | Bypasses FLS (use carefully) |
| Default (no mode) | Depends on context |

### Schema Methods
| Method | Purpose |
|--------|---------|
| `isAccessible()` | Can user read field? |
| `isUpdateable()` | Can user edit field? |
| `isCreateable()` | Can user set on create? |

### Security.stripInaccessible
| AccessType | Strips Fields Not... |
|------------|----------------------|
| `READABLE` | Readable by user |
| `CREATABLE` | Creatable by user |
| `UPDATABLE` | Updatable by user |
| `UPSERTABLE` | Creatable or updatable |
