<!-- Parent: sf-metadata/SKILL.md -->
# Custom Object Example: Invoice

This example demonstrates creating a complete custom object with fields, validation rules, and record types.

## Scenario

Create an Invoice object for tracking customer invoices with:
- Auto-numbered invoice number
- Customer (Account) relationship
- Line items (child object)
- Status tracking
- Validation rules

---

## Step 1: Create Custom Object

**File:** `force-app/main/default/objects/Invoice__c/Invoice__c.object-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Invoice</label>
    <pluralLabel>Invoices</pluralLabel>
    <description>Tracks customer invoices and payment status</description>

    <nameField>
        <label>Invoice Number</label>
        <type>AutoNumber</type>
        <displayFormat>INV-{0000000}</displayFormat>
        <trackHistory>false</trackHistory>
    </nameField>

    <deploymentStatus>Deployed</deploymentStatus>
    <sharingModel>Private</sharingModel>

    <enableHistory>true</enableHistory>
    <enableActivities>true</enableActivities>
    <enableReports>true</enableReports>
    <enableSearch>true</enableSearch>
    <enableFeeds>false</enableFeeds>
    <enableBulkApi>true</enableBulkApi>
    <enableSharing>true</enableSharing>
    <enableStreamingApi>true</enableStreamingApi>

    <searchLayouts>
        <customTabListAdditionalFields>Name</customTabListAdditionalFields>
        <customTabListAdditionalFields>Account__c</customTabListAdditionalFields>
        <customTabListAdditionalFields>Total_Amount__c</customTabListAdditionalFields>
        <customTabListAdditionalFields>Status__c</customTabListAdditionalFields>
        <lookupDialogsAdditionalFields>Name</lookupDialogsAdditionalFields>
        <lookupDialogsAdditionalFields>Account__c</lookupDialogsAdditionalFields>
        <searchResultsAdditionalFields>Name</searchResultsAdditionalFields>
        <searchResultsAdditionalFields>Account__c</searchResultsAdditionalFields>
        <searchResultsAdditionalFields>Status__c</searchResultsAdditionalFields>
    </searchLayouts>

    <compactLayoutAssignment>SYSTEM</compactLayoutAssignment>
</CustomObject>
```

---

## Step 2: Create Custom Fields

### Account Lookup
**File:** `force-app/main/default/objects/Invoice__c/fields/Account__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Account__c</fullName>
    <label>Account</label>
    <type>Lookup</type>
    <referenceTo>Account</referenceTo>
    <relationshipLabel>Invoices</relationshipLabel>
    <relationshipName>Invoices</relationshipName>
    <required>true</required>
    <deleteConstraint>Restrict</deleteConstraint>
    <description>The customer account for this invoice</description>
    <inlineHelpText>Select the customer account</inlineHelpText>
    <trackHistory>true</trackHistory>
    <trackTrending>false</trackTrending>
</CustomField>
```

### Status Picklist
**File:** `force-app/main/default/objects/Invoice__c/fields/Status__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Status__c</fullName>
    <label>Status</label>
    <type>Picklist</type>
    <required>true</required>
    <description>Current status of the invoice</description>
    <inlineHelpText>Select the invoice status</inlineHelpText>
    <trackHistory>true</trackHistory>
    <trackTrending>false</trackTrending>
    <valueSet>
        <restricted>true</restricted>
        <valueSetDefinition>
            <sorted>false</sorted>
            <value>
                <fullName>Draft</fullName>
                <default>true</default>
                <label>Draft</label>
            </value>
            <value>
                <fullName>Sent</fullName>
                <default>false</default>
                <label>Sent</label>
            </value>
            <value>
                <fullName>Paid</fullName>
                <default>false</default>
                <label>Paid</label>
            </value>
            <value>
                <fullName>Overdue</fullName>
                <default>false</default>
                <label>Overdue</label>
            </value>
            <value>
                <fullName>Cancelled</fullName>
                <default>false</default>
                <label>Cancelled</label>
            </value>
        </valueSetDefinition>
    </valueSet>
</CustomField>
```

### Invoice Date
**File:** `force-app/main/default/objects/Invoice__c/fields/Invoice_Date__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Invoice_Date__c</fullName>
    <label>Invoice Date</label>
    <type>Date</type>
    <required>true</required>
    <defaultValue>TODAY()</defaultValue>
    <description>Date the invoice was issued</description>
    <inlineHelpText>Date the invoice was created</inlineHelpText>
    <trackHistory>true</trackHistory>
    <trackTrending>false</trackTrending>
</CustomField>
```

### Due Date
**File:** `force-app/main/default/objects/Invoice__c/fields/Due_Date__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Due_Date__c</fullName>
    <label>Due Date</label>
    <type>Date</type>
    <required>true</required>
    <defaultValue>TODAY() + 30</defaultValue>
    <description>Payment due date</description>
    <inlineHelpText>Date payment is due (default: 30 days from today)</inlineHelpText>
    <trackHistory>true</trackHistory>
    <trackTrending>false</trackTrending>
</CustomField>
```

### Total Amount
**File:** `force-app/main/default/objects/Invoice__c/fields/Total_Amount__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Total_Amount__c</fullName>
    <label>Total Amount</label>
    <type>Currency</type>
    <precision>18</precision>
    <scale>2</scale>
    <required>false</required>
    <defaultValue>0</defaultValue>
    <description>Total invoice amount (calculated from line items)</description>
    <inlineHelpText>Total amount including all line items</inlineHelpText>
    <trackHistory>true</trackHistory>
    <trackTrending>false</trackTrending>
</CustomField>
```

### Payment Date
**File:** `force-app/main/default/objects/Invoice__c/fields/Payment_Date__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Payment_Date__c</fullName>
    <label>Payment Date</label>
    <type>Date</type>
    <required>false</required>
    <description>Date payment was received</description>
    <inlineHelpText>Leave blank until payment is received</inlineHelpText>
    <trackHistory>true</trackHistory>
    <trackTrending>false</trackTrending>
</CustomField>
```

### Days Overdue (Formula)
**File:** `force-app/main/default/objects/Invoice__c/fields/Days_Overdue__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Days_Overdue__c</fullName>
    <label>Days Overdue</label>
    <type>Number</type>
    <precision>18</precision>
    <scale>0</scale>
    <formula>IF(
    AND(
        ISBLANK(Payment_Date__c),
        Due_Date__c < TODAY(),
        NOT(ISPICKVAL(Status__c, 'Cancelled'))
    ),
    TODAY() - Due_Date__c,
    0
)</formula>
    <formulaTreatBlanksAs>BlankAsZero</formulaTreatBlanksAs>
    <description>Number of days past due date</description>
    <inlineHelpText>Calculated days overdue (0 if paid or not yet due)</inlineHelpText>
    <trackHistory>false</trackHistory>
    <trackTrending>false</trackTrending>
</CustomField>
```

---

## Step 3: Create Validation Rules

### Require Payment Date When Paid
**File:** `force-app/main/default/objects/Invoice__c/validationRules/Require_Payment_Date_When_Paid.validationRule-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ValidationRule xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Require_Payment_Date_When_Paid</fullName>
    <active>true</active>
    <description>Ensures Payment Date is filled when Status is set to Paid</description>
    <errorConditionFormula>AND(
    NOT($Permission.Bypass_Validation__c),
    ISPICKVAL(Status__c, 'Paid'),
    ISBLANK(Payment_Date__c)
)</errorConditionFormula>
    <errorDisplayField>Payment_Date__c</errorDisplayField>
    <errorMessage>Payment Date is required when marking an invoice as Paid.</errorMessage>
</ValidationRule>
```

### Due Date After Invoice Date
**File:** `force-app/main/default/objects/Invoice__c/validationRules/Due_Date_After_Invoice_Date.validationRule-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ValidationRule xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Due_Date_After_Invoice_Date</fullName>
    <active>true</active>
    <description>Ensures Due Date is on or after Invoice Date</description>
    <errorConditionFormula>AND(
    NOT($Permission.Bypass_Validation__c),
    Due_Date__c < Invoice_Date__c
)</errorConditionFormula>
    <errorDisplayField>Due_Date__c</errorDisplayField>
    <errorMessage>Due Date must be on or after the Invoice Date.</errorMessage>
</ValidationRule>
```

---

## Step 4: Create Record Type (Optional)

**File:** `force-app/main/default/objects/Invoice__c/recordTypes/Standard_Invoice.recordType-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<RecordType xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Standard_Invoice</fullName>
    <active>true</active>
    <label>Standard Invoice</label>
    <description>Standard invoice for regular billing</description>
</RecordType>
```

---

## Directory Structure

```
force-app/main/default/objects/Invoice__c/
├── Invoice__c.object-meta.xml
├── fields/
│   ├── Account__c.field-meta.xml
│   ├── Status__c.field-meta.xml
│   ├── Invoice_Date__c.field-meta.xml
│   ├── Due_Date__c.field-meta.xml
│   ├── Total_Amount__c.field-meta.xml
│   ├── Payment_Date__c.field-meta.xml
│   └── Days_Overdue__c.field-meta.xml
├── validationRules/
│   ├── Require_Payment_Date_When_Paid.validationRule-meta.xml
│   └── Due_Date_After_Invoice_Date.validationRule-meta.xml
└── recordTypes/
    └── Standard_Invoice.recordType-meta.xml
```

---

## Deployment

```bash
# Validate
sf project deploy start \
  --source-dir force-app/main/default/objects/Invoice__c \
  --target-org myorg \
  --dry-run

# Deploy
sf project deploy start \
  --source-dir force-app/main/default/objects/Invoice__c \
  --target-org myorg
```

---

## Next Steps

1. Create Permission Set for Invoice access
2. Create Page Layout
3. Create related Line Item object (Master-Detail)
4. Build Flows for automation
5. Create Reports and Dashboards
