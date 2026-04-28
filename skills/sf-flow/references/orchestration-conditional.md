<!-- Parent: sf-flow/SKILL.md -->
# Orchestration Pattern: Conditional

## Overview

The **Conditional pattern** uses a parent flow to evaluate conditions and dynamically decide which child subflows to execute. Think of it as a smart router that directs automation down different paths based on business rules.

## When to Use This Pattern

✅ **Use Conditional when:**
- Different scenarios require completely different logic
- You want to avoid complex branching in a single flow
- Child flows can be developed by different teams
- Business rules determine which automation to run
- You need to add new scenarios without modifying existing logic

❌ **Don't use when:**
- All steps must execute regardless of conditions
- Logic is simple (use inline decisions instead)
- Conditions are trivial (no need for separate subflows)

## Real-World Example: Case Triage and Routing

### Business Requirement

When a Case is created, route it to the appropriate team and apply appropriate automation based on priority and type:

- **Priority = Critical** → Escalate immediately, page on-call engineer, create Slack alert
- **Priority = High + Type = Technical** → Assign to senior support, create Jira ticket
- **Priority = High + Type = Billing** → Assign to billing team, check payment status
- **Priority = Medium/Low** → Standard assignment, send email notification

Each scenario has completely different logic, so we route to specialized subflows.

## Architecture

```
Parent: RTF_Case_TriageRouter (Decision Hub)
    ↓
    ├── [Critical] → Sub_EscalateCriticalCase
    │                 ├── Page on-call engineer
    │                 ├── Create Slack alert
    │                 └── Assign to escalation queue
    │
    ├── [High + Technical] → Sub_HandleTechnicalCase
    │                          ├── Assign to senior support
    │                          ├── Create Jira ticket
    │                          └── Set SLA timer
    │
    ├── [High + Billing] → Sub_HandleBillingCase
    │                        ├── Check payment status
    │                        ├── Assign to billing team
    │                        └── Generate payment report
    │
    └── [Medium/Low] → Sub_HandleStandardCase
                        ├── Auto-assign by round-robin
                        └── Send email notification
```

## Implementation

### Parent Flow: RTF_Case_TriageRouter

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <description>Conditional orchestrator that routes Cases to appropriate subflows based on priority and type.</description>
    <label>RTF_Case_TriageRouter</label>
    <processMetadataValues>
        <name>BuilderType</name>
        <value>
            <stringValue>LightningFlowBuilder</stringValue>
        </value>
    </processMetadataValues>
    <processType>AutoLaunchedFlow</processType>

    <!-- Routing Decision -->
    <decisions>
        <name>Route_By_Priority_And_Type</name>
        <label>Route By Priority And Type</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <defaultConnector>
            <targetReference>Handle_Standard_Case</targetReference>
        </defaultConnector>
        <defaultConnectorLabel>Standard (Medium/Low)</defaultConnectorLabel>

        <!-- Rule 1: Critical Priority -->
        <rules>
            <name>Critical_Priority</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>$Record.Priority</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>Critical</stringValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Escalate_Critical_Case</targetReference>
            </connector>
            <label>Critical</label>
        </rules>

        <!-- Rule 2: High Priority + Technical -->
        <rules>
            <name>High_Priority_Technical</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>$Record.Priority</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>High</stringValue>
                </rightValue>
            </conditions>
            <conditions>
                <leftValueReference>$Record.Type</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>Technical</stringValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Handle_Technical_Case</targetReference>
            </connector>
            <label>High + Technical</label>
        </rules>

        <!-- Rule 3: High Priority + Billing -->
        <rules>
            <name>High_Priority_Billing</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>$Record.Priority</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>High</stringValue>
                </rightValue>
            </conditions>
            <conditions>
                <leftValueReference>$Record.Type</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>Billing</stringValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Handle_Billing_Case</targetReference>
            </connector>
            <label>High + Billing</label>
        </rules>
    </decisions>

    <!-- Subflow 1: Critical Case Escalation -->
    <subflows>
        <name>Escalate_Critical_Case</name>
        <label>Escalate Critical Case</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <flowName>Sub_EscalateCriticalCase</flowName>
        <inputAssignments>
            <name>varCaseId</name>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>varCaseNumber</name>
            <value>
                <elementReference>$Record.CaseNumber</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>varSubject</name>
            <value>
                <elementReference>$Record.Subject</elementReference>
            </value>
        </inputAssignments>
    </subflows>

    <!-- Subflow 2: Technical Case Handling -->
    <subflows>
        <name>Handle_Technical_Case</name>
        <label>Handle Technical Case</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <flowName>Sub_HandleTechnicalCase</flowName>
        <inputAssignments>
            <name>varCaseId</name>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>varCaseNumber</name>
            <value>
                <elementReference>$Record.CaseNumber</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>varDescription</name>
            <value>
                <elementReference>$Record.Description</elementReference>
            </value>
        </inputAssignments>
    </subflows>

    <!-- Subflow 3: Billing Case Handling -->
    <subflows>
        <name>Handle_Billing_Case</name>
        <label>Handle Billing Case</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <flowName>Sub_HandleBillingCase</flowName>
        <inputAssignments>
            <name>varCaseId</name>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>varAccountId</name>
            <value>
                <elementReference>$Record.AccountId</elementReference>
            </value>
        </inputAssignments>
    </subflows>

    <!-- Subflow 4: Standard Case Handling -->
    <subflows>
        <name>Handle_Standard_Case</name>
        <label>Handle Standard Case</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <flowName>Sub_HandleStandardCase</flowName>
        <inputAssignments>
            <name>varCaseId</name>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputAssignments>
    </subflows>

    <start>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Route_By_Priority_And_Type</targetReference>
        </connector>
        <object>Case</object>
        <recordTriggerType>Create</recordTriggerType>
        <triggerType>RecordAfterSave</triggerType>
    </start>
    <status>Draft</status>
</Flow>
```

### Child Flow 1: Sub_EscalateCriticalCase

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <description>Handles critical case escalation with immediate notifications and special routing.</description>
    <label>Sub_EscalateCriticalCase</label>
    <processType>AutoLaunchedFlow</processType>

    <!-- Step 1: Page On-Call Engineer -->
    <actionCalls>
        <name>Page_On_Call_Engineer</name>
        <label>Page On-Call Engineer</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <actionName>PagerDuty_Trigger_Alert</actionName>
        <actionType>apex</actionType>
        <connector>
            <targetReference>Create_Slack_Alert</targetReference>
        </connector>
        <inputParameters>
            <name>caseId</name>
            <value>
                <elementReference>varCaseId</elementReference>
            </value>
        </inputParameters>
        <inputParameters>
            <name>urgency</name>
            <value>
                <stringValue>high</stringValue>
            </value>
        </inputParameters>
    </actionCalls>

    <!-- Step 2: Create Slack Alert -->
    <actionCalls>
        <name>Create_Slack_Alert</name>
        <label>Create Slack Alert</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <actionName>Slack_Post_Message</actionName>
        <actionType>apex</actionType>
        <connector>
            <targetReference>Assign_To_Escalation_Queue</targetReference>
        </connector>
        <inputParameters>
            <name>channel</name>
            <value>
                <stringValue>#critical-alerts</stringValue>
            </value>
        </inputParameters>
        <inputParameters>
            <name>message</name>
            <value>
                <stringValue>🚨 CRITICAL CASE: {!varCaseNumber} - {!varSubject}</stringValue>
            </value>
        </inputParameters>
    </actionCalls>

    <!-- Step 3: Assign to Escalation Queue -->
    <recordUpdates>
        <name>Assign_To_Escalation_Queue</name>
        <label>Assign To Escalation Queue</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <faultConnector>
            <targetReference>Log_Assignment_Error</targetReference>
        </faultConnector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>varCaseId</elementReference>
            </value>
        </filters>
        <inputAssignments>
            <field>OwnerId</field>
            <value>
                <stringValue>00G5e000001XYZ1</stringValue><!-- Escalation Queue ID -->
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Status</field>
            <value>
                <stringValue>Escalated</stringValue>
            </value>
        </inputAssignments>
        <object>Case</object>
    </recordUpdates>

    <!-- Error Handler -->
    <subflows>
        <name>Log_Assignment_Error</name>
        <label>Log Assignment Error</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <flowName>Sub_LogError</flowName>
        <inputAssignments>
            <name>varErrorMessage</name>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>varFlowName</name>
            <value>
                <stringValue>Sub_EscalateCriticalCase</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>varRecordId</name>
            <value>
                <elementReference>varCaseId</elementReference>
            </value>
        </inputAssignments>
    </subflows>

    <start>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Page_On_Call_Engineer</targetReference>
        </connector>
    </start>
    <status>Draft</status>

    <!-- Input Variables -->
    <variables>
        <name>varCaseId</name>
        <dataType>String</dataType>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>varCaseNumber</name>
        <dataType>String</dataType>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>varSubject</name>
        <dataType>String</dataType>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
    </variables>
</Flow>
```

### Child Flow 2: Sub_HandleTechnicalCase

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <description>Handles high-priority technical cases with Jira integration and senior support assignment.</description>
    <label>Sub_HandleTechnicalCase</label>
    <processType>AutoLaunchedFlow</processType>

    <!-- Step 1: Create Jira Ticket -->
    <actionCalls>
        <name>Create_Jira_Ticket</name>
        <label>Create Jira Ticket</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <actionName>Jira_Create_Issue</actionName>
        <actionType>apex</actionType>
        <connector>
            <targetReference>Get_Senior_Support_Agent</targetReference>
        </connector>
        <inputParameters>
            <name>summary</name>
            <value>
                <stringValue>SF Case {!varCaseNumber}</stringValue>
            </value>
        </inputParameters>
        <inputParameters>
            <name>description</name>
            <value>
                <elementReference>varDescription</elementReference>
            </value>
        </inputParameters>
        <inputParameters>
            <name>priority</name>
            <value>
                <stringValue>High</stringValue>
            </value>
        </inputParameters>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </actionCalls>

    <!-- Step 2: Get Available Senior Support Agent -->
    <recordLookups>
        <name>Get_Senior_Support_Agent</name>
        <label>Get Senior Support Agent</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <assignNullValuesIfNoRecordsFound>false</assignNullValuesIfNoRecordsFound>
        <connector>
            <targetReference>Assign_To_Senior_Support</targetReference>
        </connector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>IsActive</field>
            <operator>EqualTo</operator>
            <value>
                <booleanValue>true</booleanValue>
            </value>
        </filters>
        <filters>
            <field>UserRole.Name</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Senior Support Engineer</stringValue>
            </value>
        </filters>
        <getFirstRecordOnly>true</getFirstRecordOnly>
        <object>User</object>
        <sortField>NumberOfCasesAssigned__c</sortField>
        <sortOrder>Asc</sortOrder>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordLookups>

    <!-- Step 3: Assign Case -->
    <recordUpdates>
        <name>Assign_To_Senior_Support</name>
        <label>Assign To Senior Support</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>varCaseId</elementReference>
            </value>
        </filters>
        <inputAssignments>
            <field>OwnerId</field>
            <value>
                <elementReference>Get_Senior_Support_Agent.Id</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Status</field>
            <value>
                <stringValue>In Progress</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Jira_Ticket_Id__c</field>
            <value>
                <elementReference>Create_Jira_Ticket.ticketId</elementReference>
            </value>
        </inputAssignments>
        <object>Case</object>
    </recordUpdates>

    <start>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Create_Jira_Ticket</targetReference>
        </connector>
    </start>
    <status>Draft</status>

    <!-- Input Variables -->
    <variables>
        <name>varCaseId</name>
        <dataType>String</dataType>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>varCaseNumber</name>
        <dataType>String</dataType>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>varDescription</name>
        <dataType>String</dataType>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
    </variables>
</Flow>
```

## Key Characteristics

### 1. **Single Decision Point**
All routing logic centralized in one decision element in the parent flow

### 2. **Mutually Exclusive Paths**
Only ONE child subflow executes per scenario:
```
If Critical → Sub_EscalateCriticalCase ONLY
If High+Tech → Sub_HandleTechnicalCase ONLY
If High+Billing → Sub_HandleBillingCase ONLY
Else → Sub_HandleStandardCase ONLY
```

### 3. **Specialized Children**
Each child flow is optimized for its specific scenario with unique logic

### 4. **Easy to Extend**
Add new scenarios by adding new rules and new child subflows:
```xml
<!-- Adding VIP customer handling -->
<rules>
    <name>VIP_Customer</name>
    <conditions>
        <leftValueReference>$Record.Account.Type</leftValueReference>
        <operator>EqualTo</operator>
        <rightValue>
            <stringValue>VIP</stringValue>
        </rightValue>
    </conditions>
    <connector>
        <targetReference>Handle_VIP_Case</targetReference>
    </connector>
    <label>VIP Customer</label>
</rules>
```

## Benefits of Conditional Pattern

### ✅ Separation of Concerns
- Routing logic in parent
- Business logic in children
- No mixing of concerns

### ✅ Team Collaboration
- Critical escalation team owns Sub_EscalateCriticalCase
- Technical support team owns Sub_HandleTechnicalCase
- Billing team owns Sub_HandleBillingCase
- Teams work independently

### ✅ Simplified Testing
- Test routing logic separately from business logic
- Mock child subflows for parent testing
- Test each child independently with representative data

### ✅ Performance Optimization
- Only execute logic needed for the scenario
- Avoid unnecessary queries and DML
- Faster execution than "check everything" approach

### ✅ Maintainability
- Add new scenarios without touching existing children
- Modify specific scenario logic without affecting others
- Clear separation makes debugging easier

## Common Use Cases

1. **Case Routing**: Route by priority, type, product, geography
2. **Lead Assignment**: Route by score, source, industry, region
3. **Approval Routing**: Route by amount, requestor, department
4. **Order Fulfillment**: Route by product type, shipping method, warehouse
5. **Error Handling**: Route by error type, severity, system

## Best Practices

### ✅ DO:

1. **Order Rules Carefully**: Most specific conditions first, default last
2. **Document Decision Logic**: Clear labels and descriptions
3. **Use Meaningful Names**: Sub_Handle{Scenario}Case, not Sub_Flow1
4. **Keep Parent Lightweight**: Only routing logic, no business logic
5. **Make Children Self-Contained**: Each child has everything it needs

### ❌ DON'T:

1. **Duplicate Logic Across Children**: Extract common logic to shared subflows
2. **Make Conditions Too Complex**: If routing is complex, simplify business rules
3. **Forget the Default Path**: Always have a fallback scenario
4. **Mix Routing and Business Logic**: Keep parent as pure router
5. **Create Too Many Paths**: >10 paths suggests need for different pattern

## Advanced Pattern: Dynamic Routing

For scenarios where routing rules are stored as metadata:

```xml
<!-- Query routing rules from custom metadata -->
<recordLookups>
    <name>Get_Routing_Rules</name>
    <label>Get Routing Rules</label>
    <object>Case_Routing_Rule__mdt</object>
    <filters>
        <field>IsActive__c</field>
        <operator>EqualTo</operator>
        <value>
            <booleanValue>true</booleanValue>
        </value>
    </filters>
    <sortField>Priority__c</sortField>
    <sortOrder>Asc</sortOrder>
    <storeOutputAutomatically>true</storeOutputAutomatically>
</recordLookups>

<!-- Loop through rules and evaluate -->
<loops>
    <name>Evaluate_Routing_Rules</name>
    <collectionReference>Get_Routing_Rules</collectionReference>
    <iterationOrder>Asc</iterationOrder>
    <!-- Evaluate each rule until match found -->
</loops>
```

## Performance Considerations

### Governor Limits
- **DML Statements**: Only the executed child's DML counts (not all children)
- **SOQL Queries**: Only the executed child's queries count
- **Execution Time**: Faster than sequential (no unnecessary steps)

### Optimization Tips
1. Order decision rules by frequency (most common first)
2. Use indexed fields in routing conditions
3. Keep routing decision fast (<100ms)
4. Profile which paths execute most often

## Error Handling

Each child should handle its own errors:

```xml
<!-- In each child flow -->
<recordUpdates>
    <name>Some_Operation</name>
    <faultConnector>
        <targetReference>Log_Child_Error</targetReference>
    </faultConnector>
    <!-- ... -->
</recordUpdates>

<subflows>
    <name>Log_Child_Error</name>
    <flowName>Sub_LogError</flowName>
    <inputAssignments>
        <name>varFlowName</name>
        <value>
            <stringValue>Sub_HandleTechnicalCase</stringValue>
        </value>
    </inputAssignments>
    <!-- ... -->
</subflows>
```

## Related Patterns

- [Parent-Child Orchestration](orchestration-parent-child.md) - Execute all children
- [Sequential Orchestration](orchestration-sequential.md) - Chain flows in order
- [Subflow Library](../references/subflow-library.md) - Reusable components

## Summary

**Conditional orchestration** enables smart routing where a parent flow evaluates business rules and directs execution to specialized child subflows. This pattern creates maintainable, testable automation where teams can own their scenarios independently.

**Key Takeaway**: If your flow has complex branching with statements like "If critical, do X, Y, Z; if high-priority technical, do A, B, C," use conditional orchestration. Each scenario becomes a focused, testable subflow. 🎯
