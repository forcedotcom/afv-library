<!-- Parent: sf-flow/SKILL.md -->
# Reusable Subflow Library

## Overview

The Subflow Library provides pre-built, production-ready subflows that accelerate flow development and enforce best practices. Instead of recreating common patterns, use these standardized components to build flows faster while maintaining consistency.

**Benefits:**
- ⚡ **Faster Development**: Pre-built patterns save 30-50% development time
- 🔒 **Built-in Error Handling**: Fault paths and logging included
- ✅ **Best Practices**: Bulkified, tested, and validated
- 🔄 **Reusable**: One subflow, many parent flows
- 📊 **Maintainable**: Update once, improve everywhere

---

## Available Subflows

### 1. Sub_LogError
**Purpose**: Structured error logging for fault paths
**File**: `assets/subflows/subflow-error-logger.xml`

**When to Use**:
- In fault paths of DML operations
- When you need to capture and track flow failures
- For production observability and debugging

**Input Variables**:
- `varFlowName` (String): Name of the calling flow
- `varRecordId` (String): ID of the record being processed
- `varErrorMessage` (String): Error message (typically `$Flow.FaultMessage`)

**Output Variables**: None

**Example**:
```xml
<subflows>
    <name>Log_Update_Error</name>
    <flowName>Sub_LogError</flowName>
    <inputAssignments>
        <name>varFlowName</name>
        <value>
            <stringValue>RTF_Account_UpdateIndustry</stringValue>
        </value>
    </inputAssignments>
    <inputAssignments>
        <name>varRecordId</name>
        <value>
            <elementReference>$Record.Id</elementReference>
        </value>
    </inputAssignments>
    <inputAssignments>
        <name>varErrorMessage</name>
        <value>
            <elementReference>$Flow.FaultMessage</elementReference>
        </value>
    </inputAssignments>
</subflows>
```

**Prerequisites**:
Create Flow_Error_Log__c custom object with fields:
- `Flow_Name__c` (Text, 255)
- `Record_Id__c` (Text, 18)
- `Error_Message__c` (Long Text Area, 32,768)

**Related**: [Error Logging Example](../references/error-logging-example.md)

---

### 2. Sub_SendEmailAlert
**Purpose**: Standard email notifications
**File**: `assets/subflows/subflow-email-alert.xml`

**When to Use**:
- Send notifications when certain conditions are met
- Alert users about flow completion or errors
- Standardize email formatting across flows

**Input Variables**:
- `varEmailAddresses` (String): Comma-separated email addresses
- `varEmailSubject` (String): Email subject line
- `varEmailBody` (String): Email body content

**Output Variables**: None

**Example**:
```xml
<subflows>
    <name>Notify_Manager</name>
    <flowName>Sub_SendEmailAlert</flowName>
    <inputAssignments>
        <name>varEmailAddresses</name>
        <value>
            <elementReference>$Record.Manager.Email</elementReference>
        </value>
    </inputAssignments>
    <inputAssignments>
        <name>varEmailSubject</name>
        <value>
            <stringValue>High-Value Opportunity Created</stringValue>
        </value>
    </inputAssignments>
    <inputAssignments>
        <name>varEmailBody</name>
        <value>
            <stringValue>A new opportunity worth {!$Record.Amount} has been created.</stringValue>
        </value>
    </inputAssignments>
</subflows>
```

**Best Practices**:
- Use formula fields or text templates to build dynamic email bodies
- Consider using email templates instead for complex HTML emails
- Validate email addresses before passing to subflow

---

### 3. Sub_ValidateRecord
**Purpose**: Common validation patterns
**File**: `assets/subflows/subflow-record-validator.xml`

**When to Use**:
- Validate required fields before DML operations
- Check business rules before proceeding
- Return validation status to parent flow

**Input Variables**:
- `varFieldValue` (String): Field value to validate

**Output Variables**:
- `varIsValid` (Boolean): `true` if validation passed, `false` otherwise
- `varValidationMessage` (String): Validation result message

**Example**:
```xml
<subflows>
    <name>Validate_Industry</name>
    <flowName>Sub_ValidateRecord</flowName>
    <inputAssignments>
        <name>varFieldValue</name>
        <value>
            <elementReference>$Record.Industry</elementReference>
        </value>
    </inputAssignments>
    <storeOutputAutomatically>true</storeOutputAutomatically>
</subflows>

<!-- Decision based on validation result -->
<decisions>
    <name>Check_Validation</name>
    <rules>
        <name>Valid</name>
        <conditions>
            <leftValueReference>Validate_Industry.varIsValid</leftValueReference>
            <operator>EqualTo</operator>
            <rightValue>
                <booleanValue>true</booleanValue>
            </rightValue>
        </conditions>
        <connector>
            <targetReference>Proceed_With_Update</targetReference>
        </connector>
    </rules>
    <defaultConnector>
        <targetReference>Show_Error_Screen</targetReference>
    </defaultConnector>
</decisions>
```

**Extension**:
Customize the validation logic in the subflow for your specific needs:
- Add more complex rules (regex, format checks)
- Validate multiple fields
- Check against external systems

---

### 4. Sub_UpdateRelatedRecords
**Purpose**: Bulk update pattern with error handling
**File**: `assets/subflows/subflow-bulk-updater.xml`

**When to Use**:
- Update collections of related records
- Maintain bulkification best practices
- Centralize common update logic

**Input Variables**:
- `colRecordsToUpdate` (SObject Collection): Collection of records to update
- `varNewValue` (String): New value to assign (customize for your field type)

**Output Variables**: None

**Example**:
```xml
<!-- First, collect records in a loop -->
<loops>
    <name>Loop_Through_Contacts</name>
    <collectionReference>Get_Related_Contacts</collectionReference>
    <iterationOrder>Asc</iterationOrder>
    <nextValueConnector>
        <targetReference>Add_To_Collection</targetReference>
    </nextValueConnector>
    <noMoreValuesConnector>
        <targetReference>Call_Bulk_Updater</targetReference>
    </noMoreValuesConnector>
</loops>

<assignments>
    <name>Add_To_Collection</name>
    <assignmentItems>
        <assignToReference>colContactsToUpdate</assignToReference>
        <operator>Add</operator>
        <value>
            <elementReference>Loop_Through_Contacts</elementReference>
        </value>
    </assignmentItems>
    <connector>
        <targetReference>Loop_Through_Contacts</targetReference>
    </connector>
</assignments>

<!-- Then, call subflow OUTSIDE the loop -->
<subflows>
    <name>Call_Bulk_Updater</name>
    <flowName>Sub_UpdateRelatedRecords</flowName>
    <inputAssignments>
        <name>colRecordsToUpdate</name>
        <value>
            <elementReference>colContactsToUpdate</elementReference>
        </value>
    </inputAssignments>
    <inputAssignments>
        <name>varNewValue</name>
        <value>
            <elementReference>$Record.Industry</elementReference>
        </value>
    </inputAssignments>
</subflows>
```

**Key Pattern**:
✅ **Correct**: Loop → Add to Collection → (Outside Loop) → Call Subflow with Collection
❌ **Incorrect**: Loop → Call Subflow → (DML in loop!)

---

### 5. Sub_QueryRecordsWithRetry
**Purpose**: Query with built-in error handling
**File**: `assets/subflows/subflow-query-with-retry.xml`

**When to Use**:
- Query related records with fault handling
- Standardize query patterns
- Log query failures for troubleshooting

**Input Variables**:
- `varAccountId` (String): Filter criteria (customize for your query)

**Output Variables**:
- Automatically stores query results (use `storeOutputAutomatically="true"`)

**Example**:
```xml
<subflows>
    <name>Get_Related_Contacts</name>
    <flowName>Sub_QueryRecordsWithRetry</flowName>
    <inputAssignments>
        <name>varAccountId</name>
        <value>
            <elementReference>$Record.Id</elementReference>
        </value>
    </inputAssignments>
    <storeOutputAutomatically>true</storeOutputAutomatically>
</subflows>

<!-- Access query results -->
<decisions>
    <name>Check_Results</name>
    <rules>
        <name>Contacts_Found</name>
        <conditions>
            <leftValueReference>Get_Related_Contacts</leftValueReference>
            <operator>IsNull</operator>
            <rightValue>
                <booleanValue>false</booleanValue>
            </rightValue>
        </conditions>
        <connector>
            <targetReference>Process_Contacts</targetReference>
        </connector>
    </rules>
    <defaultConnector>
        <targetReference>No_Contacts_Path</targetReference>
    </defaultConnector>
</decisions>
```

**Customization**:
Modify the query filters in the template for your specific object and criteria.

---

## Deployment Guide

### Step 1: Deploy Subflows to Your Org

```bash
# Deploy all subflows at once
sf project deploy start \
  --source-dir assets/subflows/ \
  --target-org myorg

# Or deploy individually
sf project deploy start \
  --source-dir assets/subflows/subflow-error-logger.xml \
  --target-org myorg
```

### Step 2: Activate Subflows

1. Navigate to **Setup → Flows**
2. Find each subflow (Sub_LogError, Sub_SendEmailAlert, etc.)
3. Click **Activate**

**⚠️ Important**: Deploy Sub_LogError first if other subflows use it for error handling.

### Step 3: Create Required Custom Objects

For **Sub_LogError**, create the Flow_Error_Log__c object:

```bash
# Using Salesforce CLI
sf data create record \
  --sobject CustomObject \
  --values "FullName=Flow_Error_Log__c Label='Flow Error Log' PluralLabel='Flow Error Logs'"
```

Or manually in Setup → Object Manager → Create → Custom Object.

---

## Usage Patterns

### Pattern 1: Orchestrated Error Handling

Use Sub_LogError consistently across all flows:

```
Parent Flow
├── DML Operation 1 → [Fault] → Sub_LogError
├── DML Operation 2 → [Fault] → Sub_LogError
└── Subflow Call → [Fault] → Sub_LogError
```

### Pattern 2: Modular Notifications

Centralize all email logic in Sub_SendEmailAlert:

```
Record-Triggered Flow
├── Decision: High Value?
│   ├── Yes → Sub_SendEmailAlert(Manager)
│   └── No → End
└── Decision: Overdue?
    ├── Yes → Sub_SendEmailAlert(Owner)
    └── No → End
```

### Pattern 3: Validation Pipeline

Chain validation subflows before DML:

```
Screen Flow
├── Sub_ValidateRecord(Required Fields)
│   └── Invalid? → Show Error
├── Sub_ValidateRecord(Business Rules)
│   └── Invalid? → Show Error
└── All Valid → Create Record
```

---

## Best Practices

### ✅ DO:

1. **Deploy Once, Reference Everywhere**: Activate subflows in your org, then reference them in multiple parent flows
2. **Use Naming Conventions**: Start subflow names with `Sub_` for easy identification
3. **Add Fault Paths**: Connect all DML operations in subflows to error handlers
4. **Document Inputs/Outputs**: Use clear variable names (varFieldName, colRecordCollection)
5. **Version Control**: Track subflow changes and test before updating active versions

### ❌ DON'T:

1. **Don't Copy-Paste Subflows**: Reference the deployed subflow instead of duplicating logic
2. **Don't Skip Error Handling**: All subflows should handle their own errors gracefully
3. **Don't Hardcode Values**: Use input variables for flexibility
4. **Don't Create DML in Loops**: Use Sub_UpdateRelatedRecords pattern for bulk operations
5. **Don't Forget Testing**: Test subflows independently before using in parent flows

---

## Testing Your Subflows

### Unit Testing Individual Subflows

1. Create a test flow that calls the subflow
2. Pass various input combinations (valid, invalid, null)
3. Verify output variables and behavior
4. Check error logs if using Sub_LogError

```bash
# Example: Test Sub_LogError
sf data query \
  --query "SELECT Flow_Name__c, Error_Message__c FROM Flow_Error_Log__c ORDER BY CreatedDate DESC LIMIT 5" \
  --target-org myorg
```

### Integration Testing in Parent Flows

1. Use subflows in record-triggered flows
2. Test with bulk data (200+ records)
3. Verify subflow doesn't cause governor limit errors
4. Check execution time in debug logs

---

## Customization Guide

### Extending Subflows

All subflows are templates—customize for your needs:

1. **Clone the subflow**: Create a copy (e.g., `Sub_LogError_WithEmail`)
2. **Add custom logic**: Extend functionality while keeping core pattern
3. **Maintain naming convention**: Keep `Sub_` prefix for discoverability

### Example: Enhanced Error Logger

Extend Sub_LogError to send Platform Events:

```xml
<!-- Add to subflow after Create_Error_Log -->
<recordCreates>
    <name>Publish_Error_Event</name>
    <object>Flow_Error__e</object>
    <inputAssignments>
        <field>Flow_Name__c</field>
        <value>
            <elementReference>varFlowName</elementReference>
        </value>
    </inputAssignments>
    <!-- Real-time error monitoring -->
</recordCreates>
```

---

## Performance Considerations

### Governor Limits

- **Subflow Depth**: Maximum 50 levels of nested subflows (avoid deep nesting)
- **DML Statements**: Each subflow DML counts toward 150 limit
- **SOQL Queries**: Each subflow query counts toward 100 limit

### Optimization Tips

1. **Batch Operations**: Use Sub_UpdateRelatedRecords for bulk updates
2. **Minimize Subflow Calls**: Call once with collections vs. multiple times with single records
3. **Cache Results**: Store subflow outputs in variables to avoid repeated calls

---

## Troubleshooting

### "Subflow not found" Error
- ✅ Verify subflow is activated in target org
- ✅ Check API name matches exactly (`Sub_LogError`, not `Sub_Log_Error`)
- ✅ Deploy subflow before deploying parent flow

### "Input variable not found" Error
- ✅ Verify variable names match subflow definition
- ✅ Check variable data types (String vs. SObject Collection)
- ✅ Ensure required inputs are provided

### Performance Issues
- ✅ Check debug logs for subflow execution time
- ✅ Avoid calling subflows inside loops
- ✅ Use bulk operations with collections

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-11-30 | Initial library: 5 subflows (LogError, EmailAlert, Validator, BulkUpdater, QueryWithRetry) |

---

## Related Documentation

- [Error Logging Example](../references/error-logging-example.md) - Detailed Sub_LogError usage
- [Orchestration Guide](orchestration-guide.md) - Parent-child flow patterns
- [Flow Best Practices](flow-best-practices.md) - Flow guidelines and security

---

## Support

For issues or questions:
1. Check subflow XML for correct variable names and types
2. Test subflow independently before using in parent flow
3. Review error logs in Flow_Error_Log__c (if using Sub_LogError)
4. Check debug logs for detailed execution information

**Happy flow building! 🚀**
