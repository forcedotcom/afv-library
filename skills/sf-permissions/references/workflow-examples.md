<!-- Parent: sf-permissions/SKILL.md -->

# Common Workflows & Examples

## Workflow 0: Start with stable identifiers

```
User: "Help me investigate permissions without relying on org-specific IDs"

1. Start with stable identifiers:
   - PermissionSet.Name
   - PermissionSetGroup.DeveloperName
   - Assignee.Username
   - object / field API names
2. Run first-pass discovery with those names
3. If a child query requires `ParentId` or `SetupEntityId`, resolve that ID from the prior result
4. Avoid starting with copied record IDs unless the user explicitly wants an exact lookup
```

## Workflow 1: Audit "Who can delete Accounts?"

```
User: "Who has delete access to the Account object?"

1. Run permission detector for object API name `Account` with delete access
2. For each PS found, trace PSG membership by `PermissionSet.Name` / `PermissionSetGroup.DeveloperName`
3. Only resolve IDs if a deeper child query needs `ParentId`
4. Display results in table format
```

## Workflow 2: Troubleshoot User Access

```
User: "Why can't John edit Opportunities?"

1. Run user analyzer for john@company.com
2. Check if any PS/PSG grants `Opportunity` edit using the object API name first
3. If a child permission query needs `ParentId`, resolve it from the matching PS result
4. If no grant exists, suggest which PS/PSG to assign and check for conflicting profile restrictions
```

## Workflow 3: Document Permission Set

```
User: "Export the Sales_Manager PS for documentation"

1. Run exporter for Sales_Manager
2. Generate CSV with all permissions
3. Optionally generate Mermaid diagram showing PSG membership
```

## Example 1: Full Org Audit

```
User: "Give me a complete picture of permissions in my org"

Claude:
1. Runs hierarchy viewer to show all PS/PSG using names and developer names as the primary identifiers
2. Identifies PSGs with "Outdated" status
3. Counts users per PS
4. Generates Mermaid diagram for documentation
```

## Example 2: Security Review

```
User: "Find all PS that grant ModifyAllData"

Claude:
1. Queries PermissionSet for PermissionsModifyAllData = true
2. Lists PS names and assigned user counts
3. Flags any non-admin PS with this powerful permission
```

## Example 3: Permission Set Creation

```
User: "Create a PS for contractors with read-only Account access"

Claude:
1. Uses permission_generator.py to create XML
2. Sets Account object to Read-only (no Create/Edit/Delete)
3. Outputs .permissionset-meta.xml file
```
