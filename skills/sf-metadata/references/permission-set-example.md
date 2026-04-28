<!-- Parent: sf-metadata/SKILL.md -->
# Permission Set Example: Invoice Manager

This example demonstrates creating a comprehensive permission set with object permissions, field-level security, and related access.

---

## Scenario

Create a Permission Set for users who manage invoices:
- Full CRUD on Invoice object
- Edit access to specific fields
- Read access to Account (parent)
- Tab visibility
- Custom permission for approvals

---

## Permission Set Definition

**File:** `force-app/main/default/permissionsets/Invoice_Manager.permissionset-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- Basic Info -->
    <label>Invoice Manager</label>
    <description>Full access to manage invoices including creation, editing, and approval. Assign to users responsible for invoice processing.</description>
    <hasActivationRequired>false</hasActivationRequired>

    <!--
    ═══════════════════════════════════════════════════════════════
    OBJECT PERMISSIONS
    ═══════════════════════════════════════════════════════════════
    -->

    <!-- Invoice Object: Full CRUD -->
    <objectPermissions>
        <allowCreate>true</allowCreate>
        <allowDelete>true</allowDelete>
        <allowEdit>true</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>Invoice__c</object>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>

    <!-- Invoice Line Item: Full CRUD (child object) -->
    <objectPermissions>
        <allowCreate>true</allowCreate>
        <allowDelete>true</allowDelete>
        <allowEdit>true</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>Invoice_Line_Item__c</object>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>

    <!-- Account: Read Only (for invoice lookups) -->
    <objectPermissions>
        <allowCreate>false</allowCreate>
        <allowDelete>false</allowDelete>
        <allowEdit>false</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>Account</object>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>

    <!--
    ═══════════════════════════════════════════════════════════════
    FIELD PERMISSIONS - Invoice__c
    ═══════════════════════════════════════════════════════════════
    -->

    <!-- Account lookup: Read + Edit -->
    <fieldPermissions>
        <editable>true</editable>
        <field>Invoice__c.Account__c</field>
        <readable>true</readable>
    </fieldPermissions>

    <!-- Status: Read + Edit -->
    <fieldPermissions>
        <editable>true</editable>
        <field>Invoice__c.Status__c</field>
        <readable>true</readable>
    </fieldPermissions>

    <!-- Invoice Date: Read + Edit -->
    <fieldPermissions>
        <editable>true</editable>
        <field>Invoice__c.Invoice_Date__c</field>
        <readable>true</readable>
    </fieldPermissions>

    <!-- Due Date: Read + Edit -->
    <fieldPermissions>
        <editable>true</editable>
        <field>Invoice__c.Due_Date__c</field>
        <readable>true</readable>
    </fieldPermissions>

    <!-- Total Amount: Read Only (calculated) -->
    <fieldPermissions>
        <editable>false</editable>
        <field>Invoice__c.Total_Amount__c</field>
        <readable>true</readable>
    </fieldPermissions>

    <!-- Payment Date: Read + Edit -->
    <fieldPermissions>
        <editable>true</editable>
        <field>Invoice__c.Payment_Date__c</field>
        <readable>true</readable>
    </fieldPermissions>

    <!-- Days Overdue: Read Only (formula) -->
    <fieldPermissions>
        <editable>false</editable>
        <field>Invoice__c.Days_Overdue__c</field>
        <readable>true</readable>
    </fieldPermissions>

    <!-- Internal Notes: Read + Edit -->
    <fieldPermissions>
        <editable>true</editable>
        <field>Invoice__c.Internal_Notes__c</field>
        <readable>true</readable>
    </fieldPermissions>

    <!--
    ═══════════════════════════════════════════════════════════════
    FIELD PERMISSIONS - Invoice_Line_Item__c
    ═══════════════════════════════════════════════════════════════
    -->

    <fieldPermissions>
        <editable>true</editable>
        <field>Invoice_Line_Item__c.Product__c</field>
        <readable>true</readable>
    </fieldPermissions>

    <fieldPermissions>
        <editable>true</editable>
        <field>Invoice_Line_Item__c.Quantity__c</field>
        <readable>true</readable>
    </fieldPermissions>

    <fieldPermissions>
        <editable>true</editable>
        <field>Invoice_Line_Item__c.Unit_Price__c</field>
        <readable>true</readable>
    </fieldPermissions>

    <fieldPermissions>
        <editable>false</editable>
        <field>Invoice_Line_Item__c.Line_Total__c</field>
        <readable>true</readable>
    </fieldPermissions>

    <!--
    ═══════════════════════════════════════════════════════════════
    TAB SETTINGS
    ═══════════════════════════════════════════════════════════════
    -->

    <tabSettings>
        <tab>Invoice__c</tab>
        <visibility>Visible</visibility>
    </tabSettings>

    <tabSettings>
        <tab>Invoice_Line_Item__c</tab>
        <visibility>Visible</visibility>
    </tabSettings>

    <!--
    ═══════════════════════════════════════════════════════════════
    RECORD TYPE ACCESS
    ═══════════════════════════════════════════════════════════════
    -->

    <recordTypeVisibilities>
        <recordType>Invoice__c.Standard_Invoice</recordType>
        <visible>true</visible>
    </recordTypeVisibilities>

    <recordTypeVisibilities>
        <recordType>Invoice__c.Credit_Note</recordType>
        <visible>true</visible>
    </recordTypeVisibilities>

    <!--
    ═══════════════════════════════════════════════════════════════
    CUSTOM PERMISSIONS
    ═══════════════════════════════════════════════════════════════
    -->

    <!-- Permission to approve invoices over threshold -->
    <customPermissions>
        <enabled>true</enabled>
        <name>Invoice_Approval</name>
    </customPermissions>

    <!-- Permission to bypass validation rules -->
    <customPermissions>
        <enabled>false</enabled>
        <name>Bypass_Validation</name>
    </customPermissions>

    <!--
    ═══════════════════════════════════════════════════════════════
    APEX CLASS ACCESS
    ═══════════════════════════════════════════════════════════════
    -->

    <classAccesses>
        <apexClass>InvoiceController</apexClass>
        <enabled>true</enabled>
    </classAccesses>

    <classAccesses>
        <apexClass>InvoicePDFGenerator</apexClass>
        <enabled>true</enabled>
    </classAccesses>

    <!--
    ═══════════════════════════════════════════════════════════════
    PAGE ACCESS (Visualforce/LWC)
    ═══════════════════════════════════════════════════════════════
    -->

    <pageAccesses>
        <apexPage>InvoicePDF</apexPage>
        <enabled>true</enabled>
    </pageAccesses>

</PermissionSet>
```

---

## Related Custom Permission

**File:** `force-app/main/default/customPermissions/Invoice_Approval.customPermission-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomPermission xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Invoice Approval</label>
    <description>Allows user to approve invoices over the standard threshold. Check this permission in Apex using FeatureManagement.checkPermission('Invoice_Approval').</description>
    <isLicensed>false</isLicensed>
</CustomPermission>
```

---

## Read-Only Permission Set Variant

**File:** `force-app/main/default/permissionsets/Invoice_Viewer.permissionset-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Invoice Viewer</label>
    <description>Read-only access to invoices. For users who need to view but not modify invoice data.</description>
    <hasActivationRequired>false</hasActivationRequired>

    <!-- Invoice: Read Only -->
    <objectPermissions>
        <allowCreate>false</allowCreate>
        <allowDelete>false</allowDelete>
        <allowEdit>false</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>Invoice__c</object>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>

    <!-- All fields: Read Only -->
    <fieldPermissions>
        <editable>false</editable>
        <field>Invoice__c.Account__c</field>
        <readable>true</readable>
    </fieldPermissions>

    <fieldPermissions>
        <editable>false</editable>
        <field>Invoice__c.Status__c</field>
        <readable>true</readable>
    </fieldPermissions>

    <fieldPermissions>
        <editable>false</editable>
        <field>Invoice__c.Total_Amount__c</field>
        <readable>true</readable>
    </fieldPermissions>

    <!-- Tab: Visible -->
    <tabSettings>
        <tab>Invoice__c</tab>
        <visibility>Visible</visibility>
    </tabSettings>
</PermissionSet>
```

---

## Permission Set Group

**File:** `force-app/main/default/permissionsetgroups/Finance_Team.permissionsetgroup-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSetGroup xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Finance Team</label>
    <description>Combined permissions for Finance team members including invoice management and reporting.</description>
    <permissionSets>
        <permissionSet>Invoice_Manager</permissionSet>
        <permissionSet>Report_Builder</permissionSet>
        <permissionSet>Dashboard_Viewer</permissionSet>
    </permissionSets>
    <status>Enabled</status>
</PermissionSetGroup>
```

---

## Using Custom Permission in Apex

```apex
public class InvoiceService {

    public static void approveInvoice(Invoice__c invoice) {
        // Check custom permission
        if (invoice.Total_Amount__c > 10000 &&
            !FeatureManagement.checkPermission('Invoice_Approval')) {
            throw new InsufficientPermissionException(
                'You do not have permission to approve invoices over $10,000'
            );
        }

        invoice.Status__c = 'Approved';
        update invoice;
    }

    public class InsufficientPermissionException extends Exception {}
}
```

---

## Directory Structure

```
force-app/main/default/
├── permissionsets/
│   ├── Invoice_Manager.permissionset-meta.xml
│   └── Invoice_Viewer.permissionset-meta.xml
├── permissionsetgroups/
│   └── Finance_Team.permissionsetgroup-meta.xml
└── customPermissions/
    └── Invoice_Approval.customPermission-meta.xml
```

---

## Deployment

```bash
# Deploy permission set
sf project deploy start \
  --source-dir force-app/main/default/permissionsets/Invoice_Manager.permissionset-meta.xml \
  --target-org myorg

# Deploy all security metadata
sf project deploy start \
  --source-dir force-app/main/default/permissionsets \
  --source-dir force-app/main/default/permissionsetgroups \
  --source-dir force-app/main/default/customPermissions \
  --target-org myorg
```

---

## Assignment

```bash
# Assign permission set to user
sf org assign permset --name Invoice_Manager --target-org myorg --on-behalf-of user@example.com

# Assign permission set group
sf org assign permset --name Finance_Team --target-org myorg --on-behalf-of user@example.com
```

> Tip: when `sf org assign permset --json` fails, inspect the full JSON payload. Current CLI versions include richer multi-error details for permission-set assignment failures.

---

## Best Practices Summary

1. **Name by function**: `Invoice_Manager`, not `Finance_PS_1`
2. **Document purpose**: Clear description for each permission set
3. **Least privilege**: Only grant what's needed
4. **Group related sets**: Use Permission Set Groups for roles
5. **Use Custom Permissions**: For feature flags in Apex
6. **Separate read/write**: Create viewer variants for read-only users
