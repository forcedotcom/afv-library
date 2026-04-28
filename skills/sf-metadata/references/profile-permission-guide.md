<!-- Parent: sf-metadata/SKILL.md -->
# Profiles vs Permission Sets Guide

## Overview

Salesforce provides two primary mechanisms for controlling user access: Profiles and Permission Sets. Understanding when to use each is critical for maintainable security architecture.

---

## Quick Comparison

| Aspect | Profile | Permission Set |
|--------|---------|----------------|
| Assignment | One per user (required) | Multiple per user |
| Access model | Defines base access | Adds to profile |
| Modification | All-or-nothing | Granular additions |
| Standard items | Yes (System Admin, etc.) | No standard sets |
| Best for | Base access, login settings | Feature-based access |

---

## When to Use Profiles

### Use Profiles For:

1. **Login Settings**
   - Login hours
   - Login IP ranges
   - Password policies

2. **Default Settings**
   - Default record types
   - Default page layouts
   - Default applications

3. **Base Object Access**
   - Minimum required object permissions
   - Tab visibility defaults

4. **License-Based Access**
   - Different profiles for different licenses
   - Platform vs Full Salesforce users

### Profile Best Practices

```
✅ Create minimal profiles (least privilege)
✅ Use descriptive names (Sales_User, Service_User)
✅ Document what each profile provides
✅ Review profiles quarterly

❌ Don't create user-specific profiles
❌ Don't manage feature access in profiles
❌ Don't clone System Administrator
```

---

## When to Use Permission Sets

### Use Permission Sets For:

1. **Feature Access**
   - Invoice approval
   - Report building
   - API access

2. **Object/Field Access**
   - Read access to sensitive objects
   - Edit access to specific fields

3. **Temporary Access**
   - Project-based access
   - Training access

4. **Integration Users**
   - API permissions
   - System access

### Permission Set Best Practices

```
✅ Create feature-focused sets
✅ Use consistent naming conventions
✅ Combine into Permission Set Groups
✅ Document purpose and audience

❌ Don't duplicate profile permissions
❌ Don't create user-specific sets
❌ Don't include login settings
```

---

## Architecture Patterns

### Pattern 1: Minimal Profile + Permission Sets (Recommended)

```
Profile: Base_User
├── Read access to common objects
├── Default applications
└── Login settings

Permission Sets (assigned as needed):
├── Invoice_Creator
├── Invoice_Approver
├── Report_Builder
├── API_Access
└── Admin_Tools
```

**Benefits:**
- Flexible
- Easy to audit
- Scalable

---

### Pattern 2: Role-Based Permission Set Groups

```
Permission Set Groups:
├── Sales_Representative
│   ├── Account_Full_Access
│   ├── Contact_Full_Access
│   ├── Opportunity_Full_Access
│   └── Reports_Basic
│
├── Sales_Manager
│   ├── Sales_Representative (inherit)
│   ├── Team_Reports
│   └── Approval_Authority
│
└── Sales_Operations
    ├── Sales_Representative (inherit)
    ├── Data_Import
    └── Admin_Reports
```

**Benefits:**
- Role-aligned
- Inheritance via groups
- Single assignment point

---

### Pattern 3: Functional Decomposition

```
Base Layer (Profile):
└── Standard_User_Profile

Feature Layer (Permission Sets):
├── CRM_Features
├── Marketing_Features
├── Service_Features
└── Commerce_Features

Object Layer (Permission Sets):
├── Custom_Invoice_Access
├── Custom_Product_Access
└── Integration_Object_Access

Admin Layer (Permission Sets):
├── User_Management
├── Data_Management
└── System_Configuration
```

---

## Permission Set Groups

### What Are They?
Permission Set Groups bundle multiple Permission Sets into a single assignable unit.

### Structure
```xml
<PermissionSetGroup>
    <label>Sales Team Access</label>
    <permissionSets>
        <permissionSet>Account_Full_Access</permissionSet>
        <permissionSet>Contact_Full_Access</permissionSet>
        <permissionSet>Opportunity_Full_Access</permissionSet>
    </permissionSets>
</PermissionSetGroup>
```

### Benefits
- Single assignment = multiple permissions
- Easier onboarding
- Consistent access across role
- Simpler audit trail

### Muting Permission Sets
Temporarily remove specific permissions from a group:
```xml
<MutingPermissionSet>
    <label>Remove_Delete_Access</label>
    <objectPermissions>
        <allowDelete>false</allowDelete>
        <object>Account</object>
    </objectPermissions>
</MutingPermissionSet>
```

---

## Migration Strategy

### Moving from Profiles to Permission Sets

1. **Audit Current State**
   ```
   - List all profiles and their permissions
   - Identify unique permission combinations
   - Map profiles to user roles
   ```

2. **Design Permission Sets**
   ```
   - Group permissions by feature/function
   - Create atomic permission sets
   - Plan permission set groups
   ```

3. **Create Minimal Profiles**
   ```
   - Clone existing profiles
   - Remove feature-specific permissions
   - Keep only base access + settings
   ```

4. **Create Permission Sets**
   ```
   - Build feature-based sets
   - Test with pilot users
   - Document each set's purpose
   ```

5. **Migrate Users**
   ```
   - Assign new minimal profile
   - Assign relevant permission sets
   - Verify access is equivalent
   ```

6. **Deprecate Old Profiles**
   ```
   - Remove users from old profiles
   - Archive (don't delete) old profiles
   - Monitor for issues
   ```

---

## Common Scenarios

### Scenario 1: New Feature Rollout

**Situation:** Rolling out new invoice approval feature

**Solution:**
```
Create: Invoice_Approval_Permission_Set
├── Object: Invoice__c (Read, Edit)
├── Field: Approval_Status__c (Edit)
├── Field: Approver_Comments__c (Edit)
└── Apex: Invoice_Approval_Controller (Execute)

Assign to: Users who approve invoices
```

---

### Scenario 2: Temporary Contractor Access

**Situation:** Contractors need limited access for 3 months

**Solution:**
```
Profile: Contractor_Base (minimal)
Permission Set: Project_XYZ_Access (time-limited)

Process:
1. Assign Contractor_Base profile
2. Assign Project_XYZ_Access permission set
3. Set calendar reminder for removal
4. Remove permission set at project end
```

---

### Scenario 3: Integration User

**Situation:** External system needs API access

**Solution:**
```
Profile: Integration_User (minimal, API-only)
Permission Sets:
├── API_Enabled (system permission)
├── ERP_Objects_Access (specific objects)
└── ERP_Fields_Access (specific fields)

No: UI access, reports, dashboards
Yes: API, specific objects/fields only
```

---

## Anti-Patterns to Avoid

### 1. Profile Proliferation
```
❌ John_Smith_Profile
❌ Marketing_Temp_Profile
❌ Sales_With_Reports_Profile

✅ Standard profiles + targeted permission sets
```

### 2. Cloning System Administrator
```
❌ Clone System Admin for power users
❌ Modify cloned admin for "limited admin"

✅ Build from minimal profile + specific sets
```

### 3. Permission Set Sprawl
```
❌ One permission set per user request
❌ Overlapping permission sets
❌ Undocumented permission sets

✅ Feature-aligned, documented sets
✅ Regular audit and consolidation
```

### 4. Mixing Concerns
```
❌ Profile with feature permissions
❌ Permission set with login settings

✅ Profiles: settings + base access
✅ Permission sets: feature access only
```

---

## Audit Checklist

### Profiles
- [ ] Each profile has clear purpose
- [ ] No user-specific profiles
- [ ] Minimal permissions (least privilege)
- [ ] Login settings appropriate
- [ ] Documented and reviewed

### Permission Sets
- [ ] Named by feature/function
- [ ] No overlapping permissions
- [ ] Documented purpose
- [ ] Grouped logically
- [ ] Assignment tracked

### Permission Set Groups
- [ ] Role-aligned groupings
- [ ] No redundant inclusions
- [ ] Muting sets used appropriately
- [ ] Easy to understand structure

---

## Quick Reference

### Profile Contains
- User license
- Login hours/IP ranges
- Password policies
- Default record types
- Default page layouts
- Default applications
- Base object permissions
- Tab visibility

### Permission Set Contains
- Object permissions (additive)
- Field permissions (additive)
- Apex class access
- Visualforce page access
- Custom permissions
- Connected app access
- External data source access

### Permission Set Group Contains
- Multiple permission sets
- Muting permission sets (optional)
- Calculated permissions (union)
