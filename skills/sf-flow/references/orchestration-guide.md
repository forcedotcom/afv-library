<!-- Parent: sf-flow/SKILL.md -->
# Flow Orchestration Guide

## Introduction

**Flow orchestration** is the practice of coordinating multiple flows to work together as a cohesive system. Instead of building large, monolithic flows, orchestration breaks complex automation into smaller, focused components that communicate through well-defined interfaces.

## Why Orchestrate?

### The Monolithic Flow Problem

```
❌ Single 800-Line Flow:
RTF_Account_Update_Everything
├── Update 5 related objects (500 lines)
├── Send 3 different notifications (100 lines)
├── Complex validation logic (150 lines)
└── Audit logging (50 lines)

Problems:
- Impossible to test individual pieces
- Changes require full regression testing
- Multiple teams can't work in parallel
- Debugging is a nightmare
- Can't reuse any logic elsewhere
```

### The Orchestrated Approach

```
✅ Parent + Children (200 lines total):
RTF_Account_Update_Orchestrator (50 lines)
├── Sub_UpdateRelatedObjects (50 lines) ← Reusable!
├── Sub_SendNotifications (40 lines) ← Reusable!
├── Sub_ValidateChanges (30 lines) ← Reusable!
└── Sub_AuditLog (30 lines) ← Reusable!

Benefits:
- Test each component independently
- Change one without affecting others
- Multiple teams own their components
- Debug specific component easily
- Reuse components across flows
```

## Three Core Orchestration Patterns

### 1. Parent-Child Pattern

**Use when**: Complex task has multiple independent responsibilities

**Structure**: Parent coordinates, children execute

```
Parent (Orchestrator)
├── Child A (does one thing)
├── Child B (does another thing)
└── Child C (does a third thing)
```

**Example**: Account industry change
- Parent: RTF_Account_IndustryChange_Orchestrator
- Child 1: Update Contacts
- Child 2: Update Opportunities
- Child 3: Send Notifications

**[Full Example →](../references/orchestration-parent-child.md)**

---

### 2. Sequential Pattern

**Use when**: Each step depends on the previous step's output

**Structure**: Linear pipeline with data flowing through stages

```
Step 1 → Output → Step 2 → Output → Step 3 → Output → Step 4
```

**Example**: Order processing
- Step 1: Validate Order → (isValid, validationMessage)
- Step 2: Calculate Tax → (taxAmount, totalAmount)
- Step 3: Process Payment → (paymentId, status)
- Step 4: Reserve Inventory → (reservationId)

**[Full Example →](../references/orchestration-sequential.md)**

---

### 3. Conditional Pattern

**Use when**: Different scenarios require completely different logic

**Structure**: Router that directs to specialized handlers

```
Parent (Router)
    ├── [Condition A] → Handler A
    ├── [Condition B] → Handler B
    ├── [Condition C] → Handler C
    └── [Default] → Handler D
```

**Example**: Case triage
- Critical → Escalate immediately
- High + Technical → Create Jira ticket
- High + Billing → Check payment status
- Standard → Auto-assign

**[Full Example →](../references/orchestration-conditional.md)**

---

## Choosing the Right Pattern

### Decision Tree

```
Does each step depend on the previous step's output?
    ├── YES → Use Sequential Pattern
    │         (Order: Validate → Calculate → Charge → Fulfill)
    │
    └── NO → Are the steps completely independent?
            ├── YES → Use Parent-Child Pattern
            │         (Account: Update Contacts + Update Opps + Notify)
            │
            └── NO → Do different scenarios need different logic?
                    └── YES → Use Conditional Pattern
                              (Case: Route by priority and type)
```

### Pattern Comparison

| Aspect | Parent-Child | Sequential | Conditional |
|--------|-------------|-----------|------------|
| **Execution** | All children run (parallel possible) | Steps run in order | One path runs |
| **Dependencies** | Children independent | Each step needs previous output | Paths independent |
| **Use Case** | Multi-responsibility task | Multi-stage pipeline | Scenario-based routing |
| **Performance** | Fast (parallel possible) | Slower (sequential) | Fast (only one path) |
| **Complexity** | Medium | Low | Medium |
| **Testability** | Excellent (test each child) | Good (test each stage) | Excellent (test each path) |

## Best Practices

### 1. Design Principles

#### Single Responsibility
Each flow should do ONE thing well:
```xml
✅ GOOD:
Sub_UpdateContactIndustry → Only updates Contact Industry field

❌ BAD:
Sub_UpdateEverything → Updates Contacts, Opportunities, Cases, sends emails...
```

#### Clear Interfaces
Define explicit inputs and outputs:
```xml
<!-- Good: Clear contract -->
<variables>
    <name>varAccountId</name>
    <dataType>String</dataType>
    <isInput>true</isInput>
    <isOutput>false</isOutput>
</variables>
<variables>
    <name>varSuccessCount</name>
    <dataType>Number</dataType>
    <isInput>false</isInput>
    <isOutput>true</isOutput>
</variables>
```

#### Fail Fast
Check prerequisites early, fail immediately if not met:
```xml
<decisions>
    <name>Check_Prerequisites</name>
    <defaultConnector>
        <targetReference>Log_Error_And_Exit</targetReference>
    </defaultConnector>
    <rules>
        <name>Prerequisites_Met</name>
        <!-- Only proceed if everything is ready -->
        <connector>
            <targetReference>Begin_Processing</targetReference>
        </connector>
    </rules>
</decisions>
```

---

### 2. Naming Conventions

Use consistent prefixes to identify orchestration roles:

| Prefix | Purpose | Example |
|--------|---------|---------|
| `RTF_` | Record-Triggered orchestrator | RTF_Account_UpdateOrchestrator |
| `Auto_` | Autolaunched orchestrator | Auto_OrderProcessingPipeline |
| `Sub_` | Reusable child/subflow | Sub_UpdateContactIndustry |
| `Screen_` | Screen flow (UI) | Screen_OrderEntry |

**Pattern**: `{Type}_{Object}_{Purpose}{Role}`

Examples:
- `RTF_Account_IndustryChange_Orchestrator` (parent)
- `Sub_UpdateContactIndustry` (child)
- `Auto_ValidateOrder` (sequential step)

---

### 3. Error Handling Strategy

#### Each Child Handles Its Own Errors

```xml
<!-- In child flow -->
<recordUpdates>
    <name>Update_Records</name>
    <faultConnector>
        <targetReference>Log_Update_Error</targetReference>
    </faultConnector>
    <!-- ... -->
</recordUpdates>

<subflows>
    <name>Log_Update_Error</name>
    <flowName>Sub_LogError</flowName>
    <inputAssignments>
        <name>varFlowName</name>
        <value>
            <stringValue>Sub_UpdateContactIndustry</stringValue>
        </value>
    </inputAssignments>
    <inputAssignments>
        <name>varRecordId</name>
        <value>
            <elementReference>varAccountId</elementReference>
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

#### Parent Monitors Overall Success

```xml
<!-- In parent flow -->
<decisions>
    <name>Check_Child_Success</name>
    <rules>
        <name>Child_Failed</name>
        <conditions>
            <leftValueReference>Update_Contacts.varSuccess</leftValueReference>
            <operator>EqualTo</operator>
            <rightValue>
                <booleanValue>false</booleanValue>
            </rightValue>
        </conditions>
        <connector>
            <targetReference>Handle_Partial_Failure</targetReference>
        </connector>
    </rules>
    <defaultConnector>
        <targetReference>Continue_To_Next_Step</targetReference>
    </defaultConnector>
</decisions>
```

---

### 4. Performance Optimization

#### Minimize Subflow Calls in Loops

```xml
❌ BAD: Calling subflow 200 times
<loops>
    <name>Loop_Through_Records</name>
    <collectionReference>Get_Records</collectionReference>
    <nextValueConnector>
        <targetReference>Call_Subflow_For_Each</targetReference><!-- BAD! -->
    </nextValueConnector>
</loops>

✅ GOOD: Collect, then call subflow once
<loops>
    <name>Loop_Through_Records</name>
    <collectionReference>Get_Records</collectionReference>
    <nextValueConnector>
        <targetReference>Add_To_Collection</targetReference>
    </nextValueConnector>
    <noMoreValuesConnector>
        <targetReference>Call_Subflow_Once_With_Collection</targetReference><!-- GOOD! -->
    </noMoreValuesConnector>
</loops>
```

#### Avoid Deep Nesting

```
✅ GOOD (3 levels):
Parent → Child → Grandchild

⚠️ WARNING (5+ levels):
Parent → Child → Grandchild → Great-grandchild → Great-great-grandchild

Limit: Maximum 50 levels (governor limit)
Recommended: Maximum 3-4 levels
```

#### Use Bulkified Operations

Each child should handle collections, not single records:

```xml
<!-- Child accepts collection -->
<variables>
    <name>colRecordsToProcess</name>
    <dataType>SObject</dataType>
    <isCollection>true</isCollection>
    <isInput>true</isInput>
</variables>

<!-- Bulk DML operation -->
<recordUpdates>
    <name>Update_All_Records</name>
    <inputReference>colRecordsToProcess</inputReference>
    <!-- Processes entire collection in one DML -->
</recordUpdates>
```

---

## Implementation Patterns

### Pattern 1: Fire-and-Forget

Parent doesn't wait for children or check results:

```xml
<subflows>
    <name>Send_Notification</name>
    <flowName>Sub_SendEmailAlert</flowName>
    <!-- No output checking, just fire it -->
    <connector>
        <targetReference>Next_Step</targetReference>
    </connector>
</subflows>
```

**Use when**: Child failure doesn't affect parent success (e.g., non-critical notifications)

---

### Pattern 2: Check-and-Continue

Parent checks child result, then decides:

```xml
<subflows>
    <name>Validate_Data</name>
    <flowName>Sub_ValidateRecord</flowName>
    <storeOutputAutomatically>true</storeOutputAutomatically>
    <connector>
        <targetReference>Check_Validation_Result</targetReference>
    </connector>
</subflows>

<decisions>
    <name>Check_Validation_Result</name>
    <rules>
        <name>Valid</name>
        <conditions>
            <leftValueReference>Validate_Data.varIsValid</leftValueReference>
            <operator>EqualTo</operator>
            <rightValue>
                <booleanValue>true</booleanValue>
            </rightValue>
        </conditions>
        <connector>
            <targetReference>Continue_Processing</targetReference>
        </connector>
    </rules>
    <defaultConnector>
        <targetReference>Handle_Invalid_Data</targetReference>
    </defaultConnector>
</decisions>
```

**Use when**: Child result determines next step

---

### Pattern 3: Collect-and-Report

Parent runs all children, collects results, reports summary:

```xml
<!-- Run all children -->
<subflows>
    <name>Update_Contacts</name>
    <flowName>Sub_UpdateContacts</flowName>
    <storeOutputAutomatically>true</storeOutputAutomatically>
    <connector>
        <targetReference>Update_Opportunities</targetReference>
    </connector>
</subflows>

<subflows>
    <name>Update_Opportunities</name>
    <flowName>Sub_UpdateOpportunities</flowName>
    <storeOutputAutomatically>true</storeOutputAutomatically>
    <connector>
        <targetReference>Generate_Summary</targetReference>
    </connector>
</subflows>

<!-- Collect results -->
<assignments>
    <name>Generate_Summary</name>
    <assignmentItems>
        <assignToReference>varTotalRecordsUpdated</assignToReference>
        <operator>Add</operator>
        <value>
            <elementReference>Update_Contacts.varRecordCount</elementReference>
        </value>
    </assignmentItems>
    <assignmentItems>
        <assignToReference>varTotalRecordsUpdated</assignToReference>
        <operator>Add</operator>
        <value>
            <elementReference>Update_Opportunities.varRecordCount</elementReference>
        </value>
    </assignmentItems>
</assignments>
```

**Use when**: Parent needs to aggregate results from all children

---

## Testing Strategy

### Unit Testing Children

Test each child flow independently:

```bash
# Test Sub_UpdateContactIndustry
1. Create 200 test Contacts linked to test Account
2. Invoke Sub_UpdateContactIndustry via flow debug
3. Verify all 200 Contacts updated
4. Check no governor limit errors
5. Verify error logging if fault injected
```

### Integration Testing Parents

Test orchestration flow end-to-end:

```bash
# Test RTF_Account_IndustryChange_Orchestrator
1. Create test Account with related Contacts, Opportunities
2. Update Account.Industry field
3. Verify all children executed
4. Check all related records updated
5. Verify notifications sent
6. Check audit logs created
```

### Bulk Testing

Test with production-like volumes:

```bash
# Bulk test orchestrated flows
1. Use Data Loader to update 200 Accounts
2. Monitor execution in Setup → Apex Jobs
3. Check Flow_Error_Log__c for any failures
4. Verify no governor limit errors
5. Check debug logs for performance bottlenecks
```

---

## Common Anti-Patterns

### ❌ Anti-Pattern 1: God Flow

One flow that does everything:

```
RTF_Account_DoEverything
├── 500 lines of Contact updates
├── 400 lines of Opportunity updates
├── 300 lines of Case updates
├── 200 lines of notification logic
└── 100 lines of audit logging

Total: 1500 lines of unmaintainable spaghetti
```

**Fix**: Break into orchestrator + specialized children

---

### ❌ Anti-Pattern 2: Circular Dependencies

```
Flow A calls Flow B
Flow B calls Flow C
Flow C calls Flow A  ← INFINITE LOOP!
```

**Fix**: Design clear flow hierarchy with no cycles

---

### ❌ Anti-Pattern 3: Chatty Orchestration

```
Parent → Child A (1 record)
Parent → Child A (1 record)
Parent → Child A (1 record)
... 200 times

Total: 200 subflow calls!
```

**Fix**: Collect records, call child once with collection

---

### ❌ Anti-Pattern 4: Shared State

```
Flow A sets global variable
Flow B reads global variable
Flow C modifies global variable

Result: Unpredictable behavior based on execution order
```

**Fix**: Pass data explicitly via input/output variables

---

## Troubleshooting

### "Subflow not found" Error

```
✅ Fix:
1. Verify child flow is activated
2. Check API name matches exactly (case-sensitive)
3. Ensure child flow is deployed to target org
```

### "Too many subflow levels" Error

```
✅ Fix:
1. Reduce nesting depth (max 50, recommend 3-4)
2. Flatten hierarchy by combining some children
3. Consider different orchestration pattern
```

### Performance Issues

```
✅ Fix:
1. Profile flow execution in debug logs
2. Check for DML/SOQL in loops
3. Reduce number of subflow calls
4. Use Transform element instead of loops
5. Batch operations where possible
```

### Difficult Debugging

```
✅ Fix:
1. Add descriptive element names
2. Use Sub_LogError in all fault paths
3. Add debug assignments to trace execution
4. Test children independently first
5. Use flow interview records to trace execution
```

---

## Governor Limits

Orchestrated flows share governor limits across all components:

| Limit | Value | Orchestration Impact |
|-------|-------|---------------------|
| SOQL Queries | 100 | Each child's queries count toward total |
| DML Statements | 150 | Each child's DML counts toward total |
| DML Rows | 10,000 | Shared across all children |
| CPU Time | 10,000ms | Sum of all flow execution time |
| Subflow Depth | 50 | Parent → Child → Grandchild... |

**Tip**: Use `limits` method in debug logs to monitor consumption

---

## Version Control

### Organize by Pattern

```
force-app/main/default/flows/
├── orchestrators/
│   ├── RTF_Account_IndustryChange_Orchestrator.flow-meta.xml
│   └── Auto_OrderProcessingPipeline.flow-meta.xml
├── subflows/
│   ├── Sub_UpdateContactIndustry.flow-meta.xml
│   ├── Sub_UpdateOpportunityStages.flow-meta.xml
│   └── Sub_SendEmailAlert.flow-meta.xml
└── standalone/
    └── Screen_SimpleForm.flow-meta.xml
```

### Dependency Documentation

Create README documenting dependencies:

```markdown
# Flow Dependencies

## RTF_Account_IndustryChange_Orchestrator
- Calls: Sub_UpdateContactIndustry
- Calls: Sub_UpdateOpportunityStages
- Calls: Sub_SendEmailAlert

## Sub_UpdateContactIndustry
- No dependencies

## Sub_UpdateOpportunityStages
- Calls: Sub_LogError (error handling)
```

---

## Migration Strategy

### From Monolith to Orchestration

#### Step 1: Identify Responsibilities
Break down existing monolithic flow into distinct responsibilities

#### Step 2: Extract Children
Create child subflows for each responsibility

#### Step 3: Create Orchestrator
Build parent flow that calls children

#### Step 4: Test Side-by-Side
Run old and new flows in parallel (different trigger conditions)

#### Step 5: Cutover
Deactivate old flow, activate new orchestrated flows

#### Step 6: Monitor
Watch error logs and performance metrics

---

## Success Metrics

### Indicators of Good Orchestration

✅ **Modularity**: Average flow length < 200 lines
✅ **Reusability**: 40%+ of children used by multiple parents
✅ **Testability**: Can test each component independently
✅ **Maintainability**: Changes isolated to specific children
✅ **Performance**: No governor limit warnings
✅ **Observability**: Clear error logs showing which component failed

---

## Related Documentation

- [Parent-Child Pattern Example](../references/orchestration-parent-child.md)
- [Sequential Pattern Example](../references/orchestration-sequential.md)
- [Conditional Pattern Example](../references/orchestration-conditional.md)
- [Subflow Library](subflow-library.md)
- [Error Logging Best Practices](../references/error-logging-example.md)

---

## Summary

Flow orchestration transforms complex automations from unmaintainable monoliths into modular, testable systems. By applying the three core patterns—Parent-Child, Sequential, and Conditional—you can build robust, scalable automation that's easy to understand, test, and enhance.

**Key Principles**:
1. **Single Responsibility**: Each flow does one thing well
2. **Clear Interfaces**: Explicit inputs and outputs
3. **Error Handling**: Every component handles its own failures
4. **Testability**: Independent testing of each component
5. **Reusability**: Components used across multiple flows

Start small: Identify one complex flow in your org and break it into an orchestrated architecture. The benefits become immediately apparent! 🚀
