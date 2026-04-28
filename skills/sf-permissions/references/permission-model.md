<!-- Parent: sf-permissions/SKILL.md -->
# Salesforce Permission Model

A guide to understanding how permissions work in Salesforce.

## Overview

Salesforce uses a layered permission model:

```
┌─────────────────────────────────────────────────────┐
│                      USER                           │
├─────────────────────────────────────────────────────┤
│                    PROFILE                          │
│  (Base permissions - one per user)                  │
├─────────────────────────────────────────────────────┤
│           PERMISSION SET GROUPS                     │
│  (Collections of Permission Sets)                   │
├─────────────────────────────────────────────────────┤
│              PERMISSION SETS                        │
│  (Additive permissions)                             │
└─────────────────────────────────────────────────────┘
```

## Key Concepts

### Profiles

- **One profile per user** (mandatory)
- Defines base-level access
- Can restrict or grant permissions
- Legacy approach - Salesforce recommends minimal profiles + Permission Sets

### Permission Sets (PS)

- **Additive only** - can grant access, cannot revoke
- Multiple PS can be assigned to a user
- Can include:
  - Object CRUD permissions
  - Field-Level Security (FLS)
  - Apex Class access
  - Visualforce Page access
  - Flow access
  - Custom Permissions
  - Tab visibility
  - System permissions

### Permission Set Groups (PSG)

- **Container for multiple Permission Sets**
- Assign one PSG instead of many individual PS
- Simplifies user provisioning
- Status can be "Active" or "Outdated"

## Permission Types

### Object Permissions

| Permission | Description |
|------------|-------------|
| Create | Insert new records |
| Read | View records |
| Edit | Update existing records |
| Delete | Remove records |
| View All | Read all records regardless of sharing |
| Modify All | Full access regardless of sharing |

### Field-Level Security (FLS)

| Permission | Description |
|------------|-------------|
| Read | View field value |
| Edit | Modify field value |

Note: Edit includes Read access.

### Setup Entity Access

Access to programmatic components:

| Entity Type | Examples |
|-------------|----------|
| ApexClass | Controller classes, utility classes |
| ApexPage | Visualforce pages |
| Flow | Screen flows, autolaunched flows |
| CustomPermission | Feature flags, custom access controls |

### System Permissions

Organization-wide permissions like:

- ViewSetup
- ModifyAllData
- ViewAllData
- ManageUsers
- ApiEnabled
- RunReports
- ExportReport

## Common Permission Patterns

### Sales User Pattern

```
Permission Set Group: Sales_Cloud_User
├── Account_Access (PS)
│   └── Account: CRUD
├── Opportunity_Access (PS)
│   └── Opportunity: CRUD
└── Report_Runner (PS)
    └── System: RunReports, ExportReport
```

### API Integration Pattern

```
Permission Set: Integration_User
├── System: ApiEnabled
├── Objects: Read on required objects
└── Custom Permission: API_Access_Enabled
```

### Admin Lite Pattern

```
Permission Set: Admin_Lite
├── System: ViewSetup (NOT ModifyAllData)
├── System: ManageUsers
└── Custom Permission: Can_Manage_Users
```

## Best Practices

### 1. Minimum Necessary Access

Grant only the permissions users actually need.

### 2. Use Permission Set Groups

Group related PS into PSGs for easier management:
- `Sales_Cloud_User` (PSG) instead of 5 individual PS
- `Service_Cloud_User` (PSG) for case management

### 3. Audit Regularly

Use sf-permissions to:
- Find PS with overly broad access (ModifyAllData)
- Identify unused PS
- Document permission structures

### 4. Naming Conventions

```
Permission Set:     [Department]_[Capability]_PS
Permission Set Group: [Department]_[Role]_PSG

Examples:
  - Sales_Account_Edit_PS
  - Sales_Manager_PSG
  - HR_Employee_Data_Access_PS
```

### 5. Document Custom Permissions

Custom Permissions should have clear names:
- `Can_Approve_Expenses`
- `View_Salary_Data`
- `Export_Customer_Data`

## Related Salesforce Documentation

- [Permission Sets](https://help.salesforce.com/s/articleView?id=sf.perm_sets_overview.htm)
- [Permission Set Groups](https://help.salesforce.com/s/articleView?id=sf.perm_set_groups.htm)
- [Field-Level Security](https://help.salesforce.com/s/articleView?id=sf.users_fields_fls.htm)
