<!-- Parent: sf-metadata/SKILL.md -->
# Field Types Example: Complete Reference

This example demonstrates all common field types with real-world usage.

---

## Text Fields

### Standard Text
```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Product_SKU__c</fullName>
    <label>Product SKU</label>
    <type>Text</type>
    <length>50</length>
    <required>true</required>
    <unique>true</unique>
    <externalId>true</externalId>
    <caseSensitive>false</caseSensitive>
    <description>Unique product identifier for inventory</description>
    <inlineHelpText>Enter the unique SKU (e.g., SKU-12345)</inlineHelpText>
</CustomField>
```

### Long Text Area
```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Internal_Notes__c</fullName>
    <label>Internal Notes</label>
    <type>LongTextArea</type>
    <length>32000</length>
    <visibleLines>6</visibleLines>
    <description>Internal team notes (not visible to customers)</description>
    <inlineHelpText>Add any internal notes or comments</inlineHelpText>
</CustomField>
```

### Rich Text Area
```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Product_Description__c</fullName>
    <label>Product Description</label>
    <type>Html</type>
    <length>32000</length>
    <visibleLines>10</visibleLines>
    <description>Rich text product description for marketing</description>
    <inlineHelpText>Format description with bold, lists, and images</inlineHelpText>
</CustomField>
```

---

## Numeric Fields

### Integer (Whole Number)
```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Quantity__c</fullName>
    <label>Quantity</label>
    <type>Number</type>
    <precision>18</precision>
    <scale>0</scale>
    <required>true</required>
    <defaultValue>1</defaultValue>
    <description>Number of units ordered</description>
    <inlineHelpText>Enter quantity (whole numbers only)</inlineHelpText>
</CustomField>
```

### Decimal
```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Weight_Kg__c</fullName>
    <label>Weight (kg)</label>
    <type>Number</type>
    <precision>10</precision>
    <scale>3</scale>
    <required>false</required>
    <description>Product weight in kilograms</description>
    <inlineHelpText>Enter weight with up to 3 decimal places</inlineHelpText>
</CustomField>
```

### Currency
```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Unit_Price__c</fullName>
    <label>Unit Price</label>
    <type>Currency</type>
    <precision>18</precision>
    <scale>2</scale>
    <required>true</required>
    <defaultValue>0</defaultValue>
    <description>Price per unit</description>
    <inlineHelpText>Enter the price per unit</inlineHelpText>
</CustomField>
```

### Percent
```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Discount_Percent__c</fullName>
    <label>Discount %</label>
    <type>Percent</type>
    <precision>5</precision>
    <scale>2</scale>
    <required>false</required>
    <defaultValue>0</defaultValue>
    <description>Discount percentage applied</description>
    <inlineHelpText>Enter discount as percentage (e.g., 10 for 10%)</inlineHelpText>
</CustomField>
```

---

## Date/Time Fields

### Date
```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Contract_Start_Date__c</fullName>
    <label>Contract Start Date</label>
    <type>Date</type>
    <required>true</required>
    <defaultValue>TODAY()</defaultValue>
    <description>Date the contract becomes effective</description>
    <inlineHelpText>When does this contract take effect?</inlineHelpText>
</CustomField>
```

### DateTime
```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Last_Contact_DateTime__c</fullName>
    <label>Last Contact Date/Time</label>
    <type>DateTime</type>
    <required>false</required>
    <description>Last time we contacted this customer</description>
    <inlineHelpText>Date and time of most recent contact</inlineHelpText>
</CustomField>
```

---

## Boolean Field

### Checkbox
```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Is_VIP_Customer__c</fullName>
    <label>VIP Customer</label>
    <type>Checkbox</type>
    <defaultValue>false</defaultValue>
    <description>Indicates if customer has VIP status</description>
    <inlineHelpText>Check if this is a VIP customer</inlineHelpText>
</CustomField>
```

---

## Picklist Fields

### Single-Select Picklist
```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Priority__c</fullName>
    <label>Priority</label>
    <type>Picklist</type>
    <required>true</required>
    <description>Task priority level</description>
    <inlineHelpText>Select the priority level</inlineHelpText>
    <valueSet>
        <restricted>true</restricted>
        <valueSetDefinition>
            <sorted>false</sorted>
            <value>
                <fullName>Low</fullName>
                <default>false</default>
                <label>Low</label>
            </value>
            <value>
                <fullName>Medium</fullName>
                <default>true</default>
                <label>Medium</label>
            </value>
            <value>
                <fullName>High</fullName>
                <default>false</default>
                <label>High</label>
            </value>
            <value>
                <fullName>Critical</fullName>
                <default>false</default>
                <label>Critical</label>
            </value>
        </valueSetDefinition>
    </valueSet>
</CustomField>
```

### Multi-Select Picklist
```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Product_Categories__c</fullName>
    <label>Product Categories</label>
    <type>MultiselectPicklist</type>
    <visibleLines>4</visibleLines>
    <required>false</required>
    <description>Categories this product belongs to</description>
    <inlineHelpText>Select all applicable categories</inlineHelpText>
    <valueSet>
        <restricted>true</restricted>
        <valueSetDefinition>
            <sorted>true</sorted>
            <value>
                <fullName>Electronics</fullName>
                <label>Electronics</label>
            </value>
            <value>
                <fullName>Clothing</fullName>
                <label>Clothing</label>
            </value>
            <value>
                <fullName>Home_Garden</fullName>
                <label>Home &amp; Garden</label>
            </value>
            <value>
                <fullName>Sports</fullName>
                <label>Sports</label>
            </value>
        </valueSetDefinition>
    </valueSet>
</CustomField>
```

---

## Relationship Fields

### Lookup
```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Primary_Contact__c</fullName>
    <label>Primary Contact</label>
    <type>Lookup</type>
    <referenceTo>Contact</referenceTo>
    <relationshipLabel>Primary For</relationshipLabel>
    <relationshipName>Primary_For</relationshipName>
    <required>false</required>
    <deleteConstraint>SetNull</deleteConstraint>
    <description>Main contact person for this account</description>
    <inlineHelpText>Select the primary contact</inlineHelpText>
    <lookupFilter>
        <active>true</active>
        <filterItems>
            <field>Contact.AccountId</field>
            <operation>equals</operation>
            <valueField>$Source.AccountId</valueField>
        </filterItems>
        <isOptional>false</isOptional>
    </lookupFilter>
</CustomField>
```

### Master-Detail
```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Order__c</fullName>
    <label>Order</label>
    <type>MasterDetail</type>
    <referenceTo>Order__c</referenceTo>
    <relationshipLabel>Line Items</relationshipLabel>
    <relationshipName>Line_Items</relationshipName>
    <relationshipOrder>0</relationshipOrder>
    <reparentableMasterDetail>false</reparentableMasterDetail>
    <writeRequiresMasterRead>false</writeRequiresMasterRead>
    <description>Parent order for this line item</description>
    <inlineHelpText>The order this line item belongs to</inlineHelpText>
</CustomField>
```

---

## Special Fields

### Email
```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Support_Email__c</fullName>
    <label>Support Email</label>
    <type>Email</type>
    <required>false</required>
    <unique>false</unique>
    <description>Customer support contact email</description>
    <inlineHelpText>Email address for support inquiries</inlineHelpText>
</CustomField>
```

### Phone
```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Mobile_Phone__c</fullName>
    <label>Mobile Phone</label>
    <type>Phone</type>
    <required>false</required>
    <description>Mobile phone number</description>
    <inlineHelpText>Enter mobile number including country code</inlineHelpText>
</CustomField>
```

### URL
```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>LinkedIn_Profile__c</fullName>
    <label>LinkedIn Profile</label>
    <type>Url</type>
    <required>false</required>
    <description>LinkedIn profile URL</description>
    <inlineHelpText>Enter full LinkedIn URL (https://linkedin.com/in/...)</inlineHelpText>
</CustomField>
```

---

## Formula Fields

### Text Formula
```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Full_Address__c</fullName>
    <label>Full Address</label>
    <type>Text</type>
    <formula>Street__c &amp; BR() &amp;
City__c &amp; ", " &amp; State__c &amp; " " &amp; Postal_Code__c &amp; BR() &amp;
Country__c</formula>
    <description>Formatted complete address</description>
</CustomField>
```

### Number Formula (Calculated)
```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Line_Total__c</fullName>
    <label>Line Total</label>
    <type>Currency</type>
    <precision>18</precision>
    <scale>2</scale>
    <formula>Quantity__c * Unit_Price__c * (1 - BLANKVALUE(Discount_Percent__c, 0) / 100)</formula>
    <formulaTreatBlanksAs>BlankAsZero</formulaTreatBlanksAs>
    <description>Calculated line item total with discount</description>
</CustomField>
```

### Checkbox Formula
```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Is_Overdue__c</fullName>
    <label>Is Overdue</label>
    <type>Checkbox</type>
    <formula>AND(
    NOT(ISPICKVAL(Status__c, 'Paid')),
    NOT(ISPICKVAL(Status__c, 'Cancelled')),
    Due_Date__c < TODAY()
)</formula>
    <description>True if invoice is past due date and not paid</description>
</CustomField>
```

---

## Roll-Up Summary

```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Total_Line_Items__c</fullName>
    <label>Total Line Items</label>
    <type>Summary</type>
    <summarizedField>Order_Line_Item__c.Line_Total__c</summarizedField>
    <summaryForeignKey>Order_Line_Item__c.Order__c</summaryForeignKey>
    <summaryOperation>sum</summaryOperation>
    <description>Sum of all line item totals</description>
</CustomField>
```

### Roll-Up with Filter
```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Completed_Tasks_Count__c</fullName>
    <label>Completed Tasks</label>
    <type>Summary</type>
    <summaryForeignKey>Project_Task__c.Project__c</summaryForeignKey>
    <summaryOperation>count</summaryOperation>
    <summaryFilterItems>
        <field>Project_Task__c.Status__c</field>
        <operation>equals</operation>
        <value>Completed</value>
    </summaryFilterItems>
    <description>Count of completed tasks on this project</description>
</CustomField>
```

---

## Summary

| Field Type | Use Case | Key Settings |
|------------|----------|--------------|
| Text | Short strings | `length` (1-255) |
| LongTextArea | Multi-line text | `length`, `visibleLines` |
| Number | Quantities, rates | `precision`, `scale` |
| Currency | Money | `precision`, `scale` |
| Date | Calendar dates | - |
| DateTime | Timestamps | - |
| Checkbox | True/False | `defaultValue` (required) |
| Picklist | Single choice | `valueSet` |
| MultiselectPicklist | Multiple choices | `valueSet`, `visibleLines` |
| Lookup | Optional relationship | `referenceTo`, `deleteConstraint` |
| MasterDetail | Required relationship | `referenceTo`, `relationshipOrder` |
| Formula | Calculated | `formula`, return type |
| Summary | Aggregation | `summaryOperation`, `summarizedField` |
