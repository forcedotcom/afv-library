<!-- Parent: sf-flow/SKILL.md -->
# Multi-Step DML Rollback Pattern Example

> **Version**: 2.0.0
> **Use Case**: Creating related records with rollback on failure
> **Scenario**: Account → Contact → Opportunity creation with automatic cleanup

---

## Overview

When a flow performs multiple DML operations (Create, Update, Delete), a failure in a later step can leave orphaned records from earlier successful operations. This example demonstrates the **rollback pattern** to maintain data integrity.

### Business Scenario

A screen flow that:
1. Creates an **Account** record
2. Creates a **Primary Contact** for that Account
3. Creates an initial **Opportunity** for the Account

If step 3 fails, we must delete the Contact (step 2) and Account (step 1) to prevent orphaned data.

---

## Flow Architecture

```
┌─────────────────┐
│  Screen_Input   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────────┐
│ Create_Account  │────▶│ Handle_Account_Error │
└────────┬────────┘     └─────────────────────┘
         │ Success
         ▼
┌─────────────────┐     ┌─────────────────────────────┐
│ Create_Contact  │────▶│ Rollback_Account_On_Error   │
└────────┬────────┘     └─────────────────────────────┘
         │ Success
         ▼
┌─────────────────────┐     ┌─────────────────────────────────┐
│ Create_Opportunity  │────▶│ Rollback_Contact_And_Account    │
└────────┬────────────┘     └─────────────────────────────────┘
         │ Success
         ▼
┌─────────────────┐
│ Screen_Success  │
└─────────────────┘
```

---

## Variable Definitions (v2.0.0 Naming)

```xml
<!-- Input Variables -->
<variables>
    <name>inp_AccountName</name>
    <dataType>String</dataType>
    <isInput>true</isInput>
    <isOutput>false</isOutput>
</variables>

<variables>
    <name>inp_ContactFirstName</name>
    <dataType>String</dataType>
    <isInput>true</isInput>
    <isOutput>false</isOutput>
</variables>

<variables>
    <name>inp_ContactLastName</name>
    <dataType>String</dataType>
    <isInput>true</isInput>
    <isOutput>false</isOutput>
</variables>

<!-- Record ID Variables (for rollback) -->
<variables>
    <name>var_CreatedAccountId</name>
    <dataType>String</dataType>
    <isInput>false</isInput>
    <isOutput>false</isOutput>
</variables>

<variables>
    <name>var_CreatedContactId</name>
    <dataType>String</dataType>
    <isInput>false</isInput>
    <isOutput>false</isOutput>
</variables>

<!-- Error Tracking -->
<variables>
    <name>var_ErrorMessage</name>
    <dataType>String</dataType>
    <isInput>false</isInput>
    <isOutput>false</isOutput>
</variables>

<variables>
    <name>var_ErrorStep</name>
    <dataType>String</dataType>
    <isInput>false</isInput>
    <isOutput>false</isOutput>
</variables>

<!-- Output Variables -->
<variables>
    <name>out_Success</name>
    <dataType>Boolean</dataType>
    <isInput>false</isInput>
    <isOutput>true</isOutput>
    <value>
        <booleanValue>false</booleanValue>
    </value>
</variables>

<variables>
    <name>out_ErrorDetails</name>
    <dataType>String</dataType>
    <isInput>false</isInput>
    <isOutput>true</isOutput>
</variables>
```

---

## Step 1: Create Account

```xml
<!-- Create Account Record -->
<recordCreates>
    <name>Create_Account</name>
    <label>Create Account</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <connector>
        <targetReference>Store_Account_Id</targetReference>
    </connector>
    <faultConnector>
        <targetReference>Handle_Account_Error</targetReference>
    </faultConnector>
    <inputAssignments>
        <field>Name</field>
        <value>
            <elementReference>inp_AccountName</elementReference>
        </value>
    </inputAssignments>
    <object>Account</object>
    <storeOutputAutomatically>true</storeOutputAutomatically>
</recordCreates>

<!-- Store Account ID for potential rollback -->
<assignments>
    <name>Store_Account_Id</name>
    <label>Store Account Id</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <assignmentItems>
        <assignToReference>var_CreatedAccountId</assignToReference>
        <operator>Assign</operator>
        <value>
            <elementReference>Create_Account</elementReference>
        </value>
    </assignmentItems>
    <connector>
        <targetReference>Create_Contact</targetReference>
    </connector>
</assignments>

<!-- Handle Account Creation Error -->
<assignments>
    <name>Handle_Account_Error</name>
    <label>Handle Account Error</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <assignmentItems>
        <assignToReference>var_ErrorMessage</assignToReference>
        <operator>Assign</operator>
        <value>
            <elementReference>$Flow.FaultMessage</elementReference>
        </value>
    </assignmentItems>
    <assignmentItems>
        <assignToReference>var_ErrorStep</assignToReference>
        <operator>Assign</operator>
        <value>
            <stringValue>Account Creation</stringValue>
        </value>
    </assignmentItems>
    <connector>
        <targetReference>Set_Error_Output</targetReference>
    </connector>
</assignments>
```

---

## Step 2: Create Contact (with Rollback on Failure)

```xml
<!-- Create Contact Record -->
<recordCreates>
    <name>Create_Contact</name>
    <label>Create Contact</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <connector>
        <targetReference>Store_Contact_Id</targetReference>
    </connector>
    <faultConnector>
        <targetReference>Capture_Contact_Error</targetReference>
    </faultConnector>
    <inputAssignments>
        <field>FirstName</field>
        <value>
            <elementReference>inp_ContactFirstName</elementReference>
        </value>
    </inputAssignments>
    <inputAssignments>
        <field>LastName</field>
        <value>
            <elementReference>inp_ContactLastName</elementReference>
        </value>
    </inputAssignments>
    <inputAssignments>
        <field>AccountId</field>
        <value>
            <elementReference>var_CreatedAccountId</elementReference>
        </value>
    </inputAssignments>
    <object>Contact</object>
    <storeOutputAutomatically>true</storeOutputAutomatically>
</recordCreates>

<!-- Store Contact ID for potential rollback -->
<assignments>
    <name>Store_Contact_Id</name>
    <label>Store Contact Id</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <assignmentItems>
        <assignToReference>var_CreatedContactId</assignToReference>
        <operator>Assign</operator>
        <value>
            <elementReference>Create_Contact</elementReference>
        </value>
    </assignmentItems>
    <connector>
        <targetReference>Create_Opportunity</targetReference>
    </connector>
</assignments>

<!-- Capture error message before rollback -->
<assignments>
    <name>Capture_Contact_Error</name>
    <label>Capture Contact Error</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <assignmentItems>
        <assignToReference>var_ErrorMessage</assignToReference>
        <operator>Assign</operator>
        <value>
            <elementReference>$Flow.FaultMessage</elementReference>
        </value>
    </assignmentItems>
    <assignmentItems>
        <assignToReference>var_ErrorStep</assignToReference>
        <operator>Assign</operator>
        <value>
            <stringValue>Contact Creation</stringValue>
        </value>
    </assignmentItems>
    <connector>
        <targetReference>Rollback_Account</targetReference>
    </connector>
</assignments>

<!-- ROLLBACK: Delete the Account we created -->
<recordDeletes>
    <name>Rollback_Account</name>
    <label>Rollback Account</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <connector>
        <targetReference>Set_Error_Output</targetReference>
    </connector>
    <faultConnector>
        <!-- If rollback fails, still proceed to error output -->
        <targetReference>Set_Error_Output</targetReference>
    </faultConnector>
    <filterLogic>and</filterLogic>
    <filters>
        <field>Id</field>
        <operator>EqualTo</operator>
        <value>
            <elementReference>var_CreatedAccountId</elementReference>
        </value>
    </filters>
    <object>Account</object>
</recordDeletes>
```

---

## Step 3: Create Opportunity (with Full Rollback Chain)

```xml
<!-- Create Opportunity Record -->
<recordCreates>
    <name>Create_Opportunity</name>
    <label>Create Opportunity</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <connector>
        <targetReference>Set_Success_Output</targetReference>
    </connector>
    <faultConnector>
        <targetReference>Capture_Opportunity_Error</targetReference>
    </faultConnector>
    <inputAssignments>
        <field>Name</field>
        <value>
            <stringValue>Initial Opportunity</stringValue>
        </value>
    </inputAssignments>
    <inputAssignments>
        <field>AccountId</field>
        <value>
            <elementReference>var_CreatedAccountId</elementReference>
        </value>
    </inputAssignments>
    <inputAssignments>
        <field>StageName</field>
        <value>
            <stringValue>Prospecting</stringValue>
        </value>
    </inputAssignments>
    <inputAssignments>
        <field>CloseDate</field>
        <value>
            <elementReference>$Flow.CurrentDate</elementReference>
        </value>
    </inputAssignments>
    <object>Opportunity</object>
    <storeOutputAutomatically>true</storeOutputAutomatically>
</recordCreates>

<!-- Capture error before starting rollback chain -->
<assignments>
    <name>Capture_Opportunity_Error</name>
    <label>Capture Opportunity Error</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <assignmentItems>
        <assignToReference>var_ErrorMessage</assignToReference>
        <operator>Assign</operator>
        <value>
            <elementReference>$Flow.FaultMessage</elementReference>
        </value>
    </assignmentItems>
    <assignmentItems>
        <assignToReference>var_ErrorStep</assignToReference>
        <operator>Assign</operator>
        <value>
            <stringValue>Opportunity Creation</stringValue>
        </value>
    </assignmentItems>
    <connector>
        <targetReference>Rollback_Contact</targetReference>
    </connector>
</assignments>

<!-- ROLLBACK CHAIN: Delete Contact first -->
<recordDeletes>
    <name>Rollback_Contact</name>
    <label>Rollback Contact</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <connector>
        <targetReference>Rollback_Account_After_Contact</targetReference>
    </connector>
    <faultConnector>
        <!-- Continue chain even if Contact delete fails -->
        <targetReference>Rollback_Account_After_Contact</targetReference>
    </faultConnector>
    <filterLogic>and</filterLogic>
    <filters>
        <field>Id</field>
        <operator>EqualTo</operator>
        <value>
            <elementReference>var_CreatedContactId</elementReference>
        </value>
    </filters>
    <object>Contact</object>
</recordDeletes>

<!-- ROLLBACK CHAIN: Then delete Account -->
<recordDeletes>
    <name>Rollback_Account_After_Contact</name>
    <label>Rollback Account After Contact</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <connector>
        <targetReference>Set_Error_Output</targetReference>
    </connector>
    <faultConnector>
        <targetReference>Set_Error_Output</targetReference>
    </faultConnector>
    <filterLogic>and</filterLogic>
    <filters>
        <field>Id</field>
        <operator>EqualTo</operator>
        <value>
            <elementReference>var_CreatedAccountId</elementReference>
        </value>
    </filters>
    <object>Account</object>
</recordDeletes>
```

---

## Output Assignments

```xml
<!-- Success Output -->
<assignments>
    <name>Set_Success_Output</name>
    <label>Set Success Output</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <assignmentItems>
        <assignToReference>out_Success</assignToReference>
        <operator>Assign</operator>
        <value>
            <booleanValue>true</booleanValue>
        </value>
    </assignmentItems>
    <connector>
        <targetReference>Screen_Success</targetReference>
    </connector>
</assignments>

<!-- Error Output with Context -->
<assignments>
    <name>Set_Error_Output</name>
    <label>Set Error Output</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <assignmentItems>
        <assignToReference>out_Success</assignToReference>
        <operator>Assign</operator>
        <value>
            <booleanValue>false</booleanValue>
        </value>
    </assignmentItems>
    <assignmentItems>
        <assignToReference>out_ErrorDetails</assignToReference>
        <operator>Assign</operator>
        <value>
            <!-- Concatenate step and error for context -->
            <stringValue>Failed at {!var_ErrorStep}: {!var_ErrorMessage}</stringValue>
        </value>
    </assignmentItems>
    <connector>
        <targetReference>Screen_Error</targetReference>
    </connector>
</assignments>
```

---

## Key Patterns Demonstrated

### 1. Store IDs Immediately After Creation
Always capture the Id of created records in a variable so you can delete them if needed later.

### 2. Rollback in Reverse Order
Delete dependent records first (Contact), then parent records (Account). This respects referential integrity.

### 3. Continue Rollback Chain on Failure
Even if a rollback delete fails, continue to the next delete. Use fault connectors that continue the chain.

### 4. Capture Error Context
Store both the error message (`$Flow.FaultMessage`) and which step failed (`var_ErrorStep`) for debugging.

### 5. Use Output Variables
Expose `out_Success` and `out_ErrorDetails` so calling flows/processes can handle the result.

---

## Alternative: Using the Rollback Subflow

For reusable rollback logic, use the `Sub_RollbackRecords` subflow:

```xml
<!-- Build collection of IDs to delete -->
<assignments>
    <name>Build_Rollback_Collection</name>
    <label>Build Rollback Collection</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <assignmentItems>
        <assignToReference>col_RecordsToRollback</assignToReference>
        <operator>Add</operator>
        <value>
            <elementReference>var_CreatedContactId</elementReference>
        </value>
    </assignmentItems>
    <assignmentItems>
        <assignToReference>col_RecordsToRollback</assignToReference>
        <operator>Add</operator>
        <value>
            <elementReference>var_CreatedAccountId</elementReference>
        </value>
    </assignmentItems>
</assignments>
```

Then call `Sub_RollbackRecords` with the collection. See `assets/subflows/subflow-dml-rollback.xml`.

---

## Testing Checklist

- [ ] Successful creation of all 3 records
- [ ] Account failure → no orphaned records
- [ ] Contact failure → Account deleted, no Contact
- [ ] Opportunity failure → Both Contact and Account deleted
- [ ] Error messages include step context
- [ ] Works with bulk operations (200+ records)

---

## Related Resources

- [Flow Best Practices](../references/flow-best-practices.md) - Three-tier error handling
- [Rollback Subflow Template](../assets/subflows/subflow-dml-rollback.xml) - Reusable rollback
- [Testing Guide](../references/testing-guide.md) - Comprehensive testing strategies
