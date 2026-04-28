<!-- Parent: sf-flow/SKILL.md -->
# Error Logging Pattern Example

## Overview

This example demonstrates how to use the **Sub_LogError** reusable subflow to implement structured error logging in your flows. Structured error logging provides visibility into flow failures and accelerates debugging in production environments.

## Prerequisites

1. **Deploy the Sub_LogError subflow** from `assets/subflows/subflow-error-logger.xml`
2. **Create the Flow_Error_Log__c custom object** with these fields:
   - `Flow_Name__c` (Text, 255)
   - `Record_Id__c` (Text, 18)
   - `Error_Message__c` (Long Text Area, 32,768)

## Use Case

You have a Record-Triggered Flow on Account that updates related Contacts. If the Contact update fails, you want to log the error with context for troubleshooting.

## Implementation Pattern

###  1. Main Flow with Fault Path

```xml
<recordUpdates>
    <name>Update_Related_Contacts</name>
    <label>Update Related Contacts</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <!-- Fault connector to error handler -->
    <faultConnector>
        <targetReference>Call_Error_Logger</targetReference>
    </faultConnector>
    <filters>
        <field>AccountId</field>
        <operator>EqualTo</operator>
        <value>
            <elementReference>$Record.Id</elementReference>
        </value>
    </filters>
    <inputAssignments>
        <field>Industry</field>
        <value>
            <elementReference>$Record.Industry</elementReference>
        </value>
    </inputAssignments>
    <object>Contact</object>
</recordUpdates>
```

### 2. Call Sub_LogError Subflow

```xml
<subflows>
    <name>Call_Error_Logger</name>
    <label>Call Error Logger</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <flowName>Sub_LogError</flowName>
    <inputAssignments>
        <name>varFlowName</name>
        <value>
            <stringValue>RTF_Account_UpdateContacts</stringValue>
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

## Benefits

### ✅ Structured Data Capture
- **Flow Name**: Identifies which flow failed
- **Record ID**: Links error to specific record for investigation
- **Error Message**: Captures the system fault message
- **Timestamp**: Auto-captured by Flow_Error_Log__c created date

### ✅ Centralized Error Tracking
Query all flow errors in one place:
```sql
SELECT Flow_Name__c, Record_Id__c, Error_Message__c, CreatedDate
FROM Flow_Error_Log__c
WHERE CreatedDate = TODAY
ORDER BY CreatedDate DESC
```

### ✅ Debugging Efficiency
1. User reports: "Account update failed"
2. Query Flow_Error_Log__c for that Account ID
3. See exact error message and flow name
4. Debug with full context—no need to enable debug logs first

### ✅ Production Monitoring
Create a dashboard showing:
- Error count by flow name
- Error trends over time
- Most common error messages

## Advanced Patterns

### Pattern 1: Add Alert Email

Extend Sub_LogError to send email alerts for critical errors:

```xml
<actionCalls>
    <name>Send_Error_Alert</name>
    <label>Send Error Alert</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <actionName>emailSimple</actionName>
    <actionType>emailSimple</actionType>
    <inputParameters>
        <name>emailAddresses</name>
        <value>
            <stringValue>admin@company.com</stringValue>
        </value>
    </inputParameters>
    <inputParameters>
        <name>emailSubject</name>
        <value>
            <stringValue>Flow Error: {!varFlowName}</stringValue>
        </value>
    </inputParameters>
    <inputParameters>
        <name>emailBody</name>
        <value>
            <stringValue>Error occurred in flow: {!varFlowName}
Record ID: {!varRecordId}
Error Message: {!varErrorMessage}</stringValue>
        </value>
    </inputParameters>
</actionCalls>
```

### Pattern 2: Integration with Platform Events

For real-time error monitoring, publish a Platform Event instead of creating a record:

```xml
<recordCreates>
    <name>Publish_Error_Event</name>
    <object>Flow_Error__e</object>
    <inputAssignments>
        <field>Flow_Name__c</field>
        <value>
            <elementReference>varFlowName</elementReference>
        </value>
    </inputAssignments>
    <!-- ... other fields ... -->
</recordCreates>
```

## Testing Your Error Logger

### 1. Deploy Sub_LogError
```bash
sf project deploy start --source-dir assets/subflows/ --target-org myorg
```

### 2. Create Test Flow with Intentional Error
Create a flow that attempts to update a field that doesn't exist, then check Flow_Error_Log__c.

### 3. Verify Error Capture
```bash
sf data query --query "SELECT Flow_Name__c, Error_Message__c FROM Flow_Error_Log__c ORDER BY CreatedDate DESC LIMIT 1" --target-org myorg
```

## Best Practices

✅ **DO**:
- Use Sub_LogError in all fault paths
- Pass meaningful flow names (use naming conventions like RTF_, Auto_, etc.)
- Include record ID whenever available for context
- Review error logs regularly to identify patterns

❌ **DON'T**:
- Skip fault paths on DML operations
- Hardcode error messages (use $Flow.FaultMessage)
- Ignore error logs—they're your production monitoring

## Related Documentation

- [Subflow Library](../references/subflow-library.md) - All reusable subflows
- [Orchestration Patterns](../references/orchestration-guide.md) - Parent-child flow architecture
- [Flow Best Practices](../references/flow-best-practices.md) - Running mode and permissions

## Questions?

For issues or questions:
1. Check the troubleshooting section in README.md
2. Review the skill.md for detailed workflow
3. Test with the Sub_LogError template first before customizing
