<!-- Parent: sf-metadata/SKILL.md -->

# Permission Set Auto-Generation

When creating custom objects or fields, default to generating or updating a Permission Set unless the user explicitly opts out.

## Core rule

**Object CRUD does not make custom fields visible.**
New metadata work should normally include both:
- `<objectPermissions>` for the object
- `<fieldPermissions>` for eligible custom fields

## Default workflow

1. **Collect field information** from the metadata being created or changed
2. **Build or update a Permission Set by default** for the affected object
3. **Include eligible custom fields** with the correct read/edit behavior
4. **Exclude only fields that Salesforce treats as system-managed or always-available in Permission Set metadata**
5. **Write the Permission Set** to `force-app/main/default/permissionsets/[ObjectName]_Access.permissionset-meta.xml`
6. **Tell the user what was included and excluded**

## Eligible field guidance

| Field type / category | Include in Permission Set? | Guidance |
|---|---|---|
| Optional custom fields | YES | `readable=true`, `editable=true` |
| Formula fields | YES | `readable=true`, `editable=false` |
| Roll-up summary fields | YES | `readable=true`, `editable=false` |
| Universally required custom fields | Usually NO | Salesforce commonly treats these as always-available / excluded in modern metadata retrievals |
| Master-Detail relationship fields | Usually NO | Commonly treated as parent-controlled / excluded in Permission Set metadata |
| Name / system-managed fields | NO | Do not generate explicit field permissions |

## Generated output expectations

A generated Permission Set should:
- include object permissions for the target object
- include field permissions for eligible custom fields
- use read-only field permissions for calculated fields
- clearly document any excluded fields and why they were skipped

## Example generated Permission Set

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Auto-generated: Grants access to Customer_Feedback__c and eligible custom fields</description>
    <hasActivationRequired>false</hasActivationRequired>
    <label>Customer Feedback Access</label>

    <objectPermissions>
        <allowCreate>true</allowCreate>
        <allowDelete>true</allowDelete>
        <allowEdit>true</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>Customer_Feedback__c</object>
        <viewAllRecords>true</viewAllRecords>
    </objectPermissions>

    <fieldPermissions>
        <editable>true</editable>
        <field>Customer_Feedback__c.Optional_Field__c</field>
        <readable>true</readable>
    </fieldPermissions>

    <fieldPermissions>
        <editable>false</editable>
        <field>Customer_Feedback__c.Score_Band__c</field>
        <readable>true</readable>
    </fieldPermissions>
</PermissionSet>
```

## Opt-out guidance

If the user explicitly says they do **not** want a Permission Set generated, still call out the exact FLS follow-up they must handle manually.

## Implementation note

The generator script under `hooks/scripts/generate_permission_set.py` should be treated as the default automation path for this workflow.
