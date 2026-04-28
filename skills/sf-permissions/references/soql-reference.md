<!-- Parent: sf-permissions/SKILL.md -->
# Permission SOQL Reference

Quick reference for SOQL queries used in sf-permissions.

## Identifier Strategy (Recommended)

Start investigations with stable metadata names rather than org-specific record IDs.

Prefer:
- `PermissionSet.Name`
- `PermissionSetGroup.DeveloperName`
- `Assignee.Username`
- object / field API names such as `Account` and `Account.AnnualRevenue`
- `CustomPermission.DeveloperName`

Use IDs only when:
- a child object forces `ParentId` or `SetupEntityId`
- you are reusing an ID returned by an earlier read-only query in the same investigation

### Find Users Assigned to a Permission Set by Name

```sql
SELECT Assignee.Name, Assignee.Username, Assignee.IsActive
FROM PermissionSetAssignment
WHERE PermissionSet.Name = 'Sales_Manager'
```

### Find Users Assigned to a Permission Set Group by DeveloperName

```sql
SELECT Assignee.Name, Assignee.Username, Assignee.IsActive
FROM PermissionSetAssignment
WHERE PermissionSetGroup.DeveloperName = 'Sales_Cloud_User'
```

## Permission Set Queries

### List All Permission Sets

```sql
SELECT Id, Name, Label, Description, IsOwnedByProfile, Type
FROM PermissionSet
WHERE IsOwnedByProfile = false
ORDER BY Label
```

### List Permission Set Groups

```sql
SELECT Id, DeveloperName, MasterLabel, Status, Description
FROM PermissionSetGroup
ORDER BY MasterLabel
```

### Get PSG Components (PS in a Group)

```sql
SELECT
    PermissionSetGroupId,
    PermissionSetGroup.DeveloperName,
    PermissionSetId,
    PermissionSet.Name,
    PermissionSet.Label
FROM PermissionSetGroupComponent
```

### Get User's Permission Set Assignments

```sql
SELECT
    AssigneeId,
    Assignee.Username,
    PermissionSetId,
    PermissionSet.Name,
    PermissionSetGroupId,
    PermissionSetGroup.DeveloperName
FROM PermissionSetAssignment
WHERE Assignee.Username = 'john@company.com'
AND PermissionSet.IsOwnedByProfile = false
```

## Object Permission Queries

### Get All Object Permissions for a Permission Set by Name

```sql
SELECT
    SobjectType,
    PermissionsCreate,
    PermissionsRead,
    PermissionsEdit,
    PermissionsDelete,
    PermissionsViewAllRecords,
    PermissionsModifyAllRecords
FROM ObjectPermissions
WHERE Parent.Name = 'Sales_Manager'
ORDER BY SobjectType
```

### Find PS with Specific Object Access

```sql
SELECT
    Parent.Name,
    Parent.Label,
    SobjectType,
    PermissionsDelete
FROM ObjectPermissions
WHERE SobjectType = 'Account'
AND PermissionsDelete = true
```

## Field Permission Queries

### Get Field Permissions for a Permission Set by Name

```sql
SELECT Field, PermissionsRead, PermissionsEdit
FROM FieldPermissions
WHERE Parent.Name = 'Sales_Manager'
ORDER BY Field
```

### Find PS with Specific Field Access

```sql
SELECT
    Parent.Name,
    Parent.Label,
    Field,
    PermissionsRead,
    PermissionsEdit
FROM FieldPermissions
WHERE Field = 'Account.AnnualRevenue'
AND PermissionsEdit = true
```

## Setup Entity Access Queries

### Get All Setup Entity Access for a Permission Set by Name

```sql
SELECT SetupEntityType, SetupEntityId
FROM SetupEntityAccess
WHERE Parent.Name = 'Sales_Manager'
```

### Find PS with Apex Class Access

```sql
SELECT Parent.Name, Parent.Label
FROM SetupEntityAccess
WHERE SetupEntityType = 'ApexClass'
AND SetupEntityId IN (
    SELECT Id FROM ApexClass WHERE Name = 'MyApexClass'
)
```

### Find PS with Custom Permission

```sql
SELECT Parent.Name, Parent.Label
FROM SetupEntityAccess
WHERE SetupEntityType = 'CustomPermission'
AND SetupEntityId IN (
    SELECT Id FROM CustomPermission WHERE DeveloperName = 'Can_Approve'
)
```

### Find PS with Visualforce Page Access

```sql
SELECT Parent.Name, Parent.Label
FROM SetupEntityAccess
WHERE SetupEntityType = 'ApexPage'
AND SetupEntityId IN (
    SELECT Id FROM ApexPage WHERE Name = 'MyVFPage'
)
```

### Find PS with Flow Access

Resolve the active flow version by `DeveloperName` first, then use that returned ID for the child access query.

```sql
SELECT ActiveVersionId
FROM FlowDefinition
WHERE DeveloperName = 'Case_Routing'
```

```sql
SELECT Parent.Name, Parent.Label
FROM SetupEntityAccess
WHERE SetupEntityType = 'Flow'
AND SetupEntityId = '<ActiveVersionId from prior query>'
```

## User Count Queries

### Count Users per Permission Set

```sql
SELECT PermissionSetId, COUNT(AssigneeId) userCount
FROM PermissionSetAssignment
GROUP BY PermissionSetId
```

### Count Users per Permission Set Group

```sql
SELECT PermissionSetGroupId, COUNT(AssigneeId) userCount
FROM PermissionSetAssignment
WHERE PermissionSetGroupId != null
GROUP BY PermissionSetGroupId
```

## System Permission Queries

### Find PS with ModifyAllData

```sql
SELECT Id, Name, Label
FROM PermissionSet
WHERE PermissionsModifyAllData = true
AND IsOwnedByProfile = false
```

### Find PS with ViewSetup

```sql
SELECT Id, Name, Label
FROM PermissionSet
WHERE PermissionsViewSetup = true
AND IsOwnedByProfile = false
```

## Metadata Queries

### List All Custom Permissions

```sql
SELECT Id, DeveloperName, MasterLabel, Description
FROM CustomPermission
ORDER BY MasterLabel
```

### List All Apex Classes

```sql
SELECT Id, Name, NamespacePrefix, IsValid
FROM ApexClass
ORDER BY Name
```

### List All Flows (with Active Version)

```sql
SELECT Id, DeveloperName, MasterLabel, ProcessType, ActiveVersionId
FROM FlowDefinition
WHERE ActiveVersionId != null
ORDER BY MasterLabel
```

## Entity Definition Queries

### List Customizable Objects

```sql
SELECT QualifiedApiName, Label
FROM EntityDefinition
WHERE IsCustomizable = true
ORDER BY Label
```

### Get Fields for an Object

```sql
SELECT QualifiedApiName, Label, DataType
FROM FieldDefinition
WHERE EntityDefinition.QualifiedApiName = 'Account'
ORDER BY Label
```

## Notes

- All permission queries are **read-only** - they don't modify data
- Prefer stable names (`Name`, `DeveloperName`, API names, usernames) for first-pass investigation queries
- `ParentId` in ObjectPermissions/FieldPermissions refers to the Permission Set ID
- `SetupEntityId` is the ID of the Apex Class, VF Page, Flow, or Custom Permission
- When a child query requires an ID, resolve it from a prior read-only query instead of starting with copied IDs
- System permissions are fields on the PermissionSet object (e.g., `PermissionsModifyAllData`)
