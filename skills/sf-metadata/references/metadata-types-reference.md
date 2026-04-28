<!-- Parent: sf-metadata/SKILL.md -->
# Salesforce Metadata Types Reference

## Overview

This guide covers the most common Salesforce metadata types, their file locations, and usage patterns.

---

## Metadata Directory Structure

```
force-app/main/default/
├── objects/
│   ├── Account/
│   │   ├── Account.object-meta.xml          # Object settings (standard)
│   │   ├── fields/
│   │   │   ├── Custom_Field__c.field-meta.xml
│   │   │   └── ...
│   │   ├── validationRules/
│   │   │   └── Rule_Name.validationRule-meta.xml
│   │   ├── recordTypes/
│   │   │   └── Record_Type.recordType-meta.xml
│   │   └── listViews/
│   │       └── All_Accounts.listView-meta.xml
│   └── Custom_Object__c/
│       ├── Custom_Object__c.object-meta.xml  # Full object definition
│       ├── fields/
│       ├── validationRules/
│       └── recordTypes/
├── profiles/
│   └── Profile_Name.profile-meta.xml
├── permissionsets/
│   └── Permission_Set.permissionset-meta.xml
├── layouts/
│   └── Object-Layout_Name.layout-meta.xml
├── classes/
│   ├── ClassName.cls
│   └── ClassName.cls-meta.xml
├── triggers/
│   ├── TriggerName.trigger
│   └── TriggerName.trigger-meta.xml
├── flows/
│   └── Flow_Name.flow-meta.xml
├── lwc/
│   └── componentName/
│       ├── componentName.html
│       ├── componentName.js
│       └── componentName.js-meta.xml
└── aura/
    └── ComponentName/
        ├── ComponentName.cmp
        └── ComponentName.cmp-meta.xml
```

---

## Object Metadata

### Custom Object
**Location:** `objects/[ObjectName__c]/[ObjectName__c].object-meta.xml`

**Contains:**
- Label and plural label
- Name field configuration
- Sharing model
- Feature toggles (history, activities, reports)
- Search layouts

```xml
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Invoice</label>
    <pluralLabel>Invoices</pluralLabel>
    <nameField>
        <label>Invoice Number</label>
        <type>AutoNumber</type>
        <displayFormat>INV-{0000}</displayFormat>
    </nameField>
    <deploymentStatus>Deployed</deploymentStatus>
    <sharingModel>Private</sharingModel>
</CustomObject>
```

### Custom Field
**Location:** `objects/[ObjectName]/fields/[FieldName__c].field-meta.xml`

**Common Types:**
| Type | Element |
|------|---------|
| Text | `<type>Text</type><length>255</length>` |
| Number | `<type>Number</type><precision>18</precision><scale>2</scale>` |
| Currency | `<type>Currency</type>` |
| Date | `<type>Date</type>` |
| Checkbox | `<type>Checkbox</type><defaultValue>false</defaultValue>` |
| Picklist | `<type>Picklist</type><valueSet>...</valueSet>` |
| Lookup | `<type>Lookup</type><referenceTo>Account</referenceTo>` |
| Master-Detail | `<type>MasterDetail</type>` |
| Formula | `<type>Text</type><formula>...</formula>` |
| Roll-Up | `<type>Summary</type>` |

---

## Security Metadata

### Profile
**Location:** `profiles/[ProfileName].profile-meta.xml`

**Contains:**
- Object permissions
- Field permissions
- Tab visibility
- Record type assignments
- Layout assignments
- User permissions

### Permission Set
**Location:** `permissionsets/[PermissionSetName].permissionset-meta.xml`

**Contains:**
- Object permissions
- Field permissions
- Tab settings
- Apex class access
- Visualforce page access
- Custom permissions

### Permission Set Group
**Location:** `permissionsetgroups/[GroupName].permissionsetgroup-meta.xml`

```xml
<PermissionSetGroup xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Sales Team</label>
    <permissionSets>
        <permissionSet>Account_Access</permissionSet>
        <permissionSet>Opportunity_Access</permissionSet>
    </permissionSets>
</PermissionSetGroup>
```

---

## Validation & Business Logic

### Validation Rule
**Location:** `objects/[ObjectName]/validationRules/[RuleName].validationRule-meta.xml`

```xml
<ValidationRule xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Require_Close_Date</fullName>
    <active>true</active>
    <errorConditionFormula>
        AND(
            ISPICKVAL(Status__c, 'Closed'),
            ISBLANK(Close_Date__c)
        )
    </errorConditionFormula>
    <errorDisplayField>Close_Date__c</errorDisplayField>
    <errorMessage>Close Date is required when Status is Closed</errorMessage>
</ValidationRule>
```

### Record Type
**Location:** `objects/[ObjectName]/recordTypes/[RecordTypeName].recordType-meta.xml`

```xml
<RecordType xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Business_Account</fullName>
    <active>true</active>
    <label>Business Account</label>
    <picklistValues>
        <picklist>Type</picklist>
        <values>
            <fullName>Customer</fullName>
            <default>true</default>
        </values>
    </picklistValues>
</RecordType>
```

---

## UI Metadata

### Page Layout
**Location:** `layouts/[ObjectName]-[LayoutName].layout-meta.xml`

**Contains:**
- Section definitions
- Field placements
- Related lists
- Quick actions
- Display options

### Lightning Page (FlexiPage)
**Location:** `flexipages/[PageName].flexipage-meta.xml`

### List View
**Location:** `objects/[ObjectName]/listViews/[ViewName].listView-meta.xml`

```xml
<ListView xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>All_Active_Accounts</fullName>
    <columns>NAME</columns>
    <columns>ACCOUNT_TYPE</columns>
    <columns>PHONE1</columns>
    <filterScope>Everything</filterScope>
    <filters>
        <field>ACCOUNT.ACTIVE__C</field>
        <operation>equals</operation>
        <value>1</value>
    </filters>
    <label>All Active Accounts</label>
</ListView>
```

---

## Automation Metadata

### Flow
**Location:** `flows/[FlowName].flow-meta.xml`

### Apex Class
**Location:** `classes/[ClassName].cls` + `classes/[ClassName].cls-meta.xml`

```xml
<!-- Meta file -->
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

### Apex Trigger
**Location:** `triggers/[TriggerName].trigger` + `triggers/[TriggerName].trigger-meta.xml`

---

## Component Metadata

### Lightning Web Component (LWC)
**Location:** `lwc/[componentName]/`

```
lwc/myComponent/
├── myComponent.html
├── myComponent.js
├── myComponent.css (optional)
└── myComponent.js-meta.xml
```

### Aura Component
**Location:** `aura/[ComponentName]/`

```
aura/MyComponent/
├── MyComponent.cmp
├── MyComponentController.js
├── MyComponentHelper.js
├── MyComponent.css
└── MyComponent.cmp-meta.xml
```

---

## Global Value Sets

### Global Value Set
**Location:** `globalValueSets/[SetName].globalValueSet-meta.xml`

```xml
<GlobalValueSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Industry Values</masterLabel>
    <sorted>false</sorted>
    <customValue>
        <fullName>Technology</fullName>
        <default>false</default>
        <label>Technology</label>
    </customValue>
    <customValue>
        <fullName>Finance</fullName>
        <default>false</default>
        <label>Finance</label>
    </customValue>
</GlobalValueSet>
```

---

## Custom Metadata Types

### Custom Metadata Type Definition
**Location:** `customMetadata/[TypeName].[RecordName].md-meta.xml`

```xml
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>US Config</label>
    <values>
        <field>Country_Code__c</field>
        <value>US</value>
    </values>
    <values>
        <field>Tax_Rate__c</field>
        <value>0.08</value>
    </values>
</CustomMetadata>
```

---

## Quick Reference: File Extensions

| Metadata Type | Extension |
|---------------|-----------|
| Custom Object | `.object-meta.xml` |
| Custom Field | `.field-meta.xml` |
| Profile | `.profile-meta.xml` |
| Permission Set | `.permissionset-meta.xml` |
| Validation Rule | `.validationRule-meta.xml` |
| Record Type | `.recordType-meta.xml` |
| Page Layout | `.layout-meta.xml` |
| Flow | `.flow-meta.xml` |
| Apex Class | `.cls` + `.cls-meta.xml` |
| Apex Trigger | `.trigger` + `.trigger-meta.xml` |
| LWC | `.js-meta.xml` |
| Aura | `.cmp-meta.xml` |

---

## Recent CLI-Supported Metadata Additions

Recent Salesforce CLI / SDR updates added support for several metadata types that were easy to miss in older reference material:

| Current Type | Typical Source Shape | Notes |
|--------------|----------------------|-------|
| `CnfgItemSourceDefinition` | `cnfgItemSourceDefinitions/<Name>.cnfgItemSourceDefinition-meta.xml` | Replaces older `CnfgMgmtCiSourceDef` naming in source workflows |
| `ExtlClntAppOauthSecuritySettings` | `extlClntAppOauthSecuritySettings/<Name>.ecaOauthSecurity-meta.xml` | Companion metadata for External Client Apps |
| `UIBundle` | `uiBundles/<Name>/...` | Replaces older `WebApplication` naming in source workflows |

When working from older examples, prefer the **current** metadata type and suffix names above.

---

## sf CLI Metadata Commands

```bash
# List metadata types
sf org list metadata-types --target-org [alias]

# List specific metadata
sf org list metadata --metadata-type CustomObject --target-org [alias]

# Describe object
sf sobject describe --sobject Account --target-org [alias]

# Retrieve metadata
sf project retrieve start --metadata CustomObject:Account

# Deploy metadata
sf project deploy start --source-dir force-app

# Generate package.xml
sf project generate manifest --source-dir force-app
```
