<!-- Parent: sf-flow/SKILL.md -->
# Orchestration Pattern: Parent-Child

## Overview

The **Parent-Child pattern** is an orchestration approach where a parent flow coordinates multiple child subflows, each handling a specific responsibility. This creates modular, maintainable automation that's easier to test, debug, and enhance.

## When to Use This Pattern

✅ **Use Parent-Child when:**
- Complex automation has multiple distinct steps
- Different teams own different parts of the logic
- You need to reuse steps across multiple parent flows
- Testing and debugging large flows is difficult
- Changes to one step shouldn't require retesting everything

❌ **Don't use when:**
- Automation is simple with 1-2 steps
- All logic is tightly coupled
- Performance is critical (minimal subflow overhead acceptable)

## Real-World Example: Account Industry Change

### Business Requirement

When an Account's Industry changes:
1. Update all related Contacts with the new Industry
2. Update all related Opportunities with Industry-specific Stage
3. Send notification to Account Owner
4. Log the change for audit purposes

### ❌ Monolithic Approach (Anti-Pattern)

One large flow with everything inline:

```
RTF_Account_IndustryChange
├── Get Related Contacts (150+ records)
├── Loop Through Contacts
│   └── Update Each Contact (DML in loop! ❌)
├── Get Related Opportunities
├── Decision: Industry = "Technology"?
│   ├── Yes → Update Stage to "Discovery"
│   └── No → Update Stage to "Qualification"
├── Loop Through Opportunities
│   └── Update Each Opportunity (DML in loop! ❌)
├── Send Email to Owner
└── Create Audit Log

Problems:
- 400+ lines of XML
- DML in loops causes bulk failures
- Can't reuse Contact update logic elsewhere
- Testing requires full end-to-end scenario
- Debugging is painful
```

### ✅ Parent-Child Approach (Best Practice)

Break into coordinated flows:

```
Parent: RTF_Account_IndustryChange_Orchestrator
├── Child: Sub_UpdateContactIndustry (reusable)
├── Child: Sub_UpdateOpportunityStages (reusable)
├── Child: Sub_SendEmailAlert (from library)
└── Child: Sub_CreateAuditLog (reusable)

Benefits:
- Each child is 50-100 lines
- Each child can be tested independently
- Children can be reused in other flows
- Clear separation of concerns
- Easy to add/remove steps
```

## Implementation

### Parent Flow: RTF_Account_IndustryChange_Orchestrator

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <description>Parent orchestrator that coordinates industry change automation. Calls child subflows for each responsibility.</description>
    <label>RTF_Account_IndustryChange_Orchestrator</label>
    <processMetadataValues>
        <name>BuilderType</name>
        <value>
            <stringValue>LightningFlowBuilder</stringValue>
        </value>
    </processMetadataValues>
    <processType>AutoLaunchedFlow</processType>
    <start>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Update_Contacts</targetReference>
        </connector>
        <object>Account</object>
        <recordTriggerType>Update</recordTriggerType>
        <triggerType>RecordAfterSave</triggerType>
    </start>
    <status>Draft</status>

    <!-- Step 1: Update Related Contacts -->
    <subflows>
        <name>Update_Contacts</name>
        <label>Update Related Contacts</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Update_Opportunities</targetReference>
        </connector>
        <flowName>Sub_UpdateContactIndustry</flowName>
        <inputAssignments>
            <name>varAccountId</name>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>varNewIndustry</name>
            <value>
                <elementReference>$Record.Industry</elementReference>
            </value>
        </inputAssignments>
    </subflows>

    <!-- Step 2: Update Related Opportunities -->
    <subflows>
        <name>Update_Opportunities</name>
        <label>Update Related Opportunities</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Notify_Owner</targetReference>
        </connector>
        <flowName>Sub_UpdateOpportunityStages</flowName>
        <inputAssignments>
            <name>varAccountId</name>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>varIndustry</name>
            <value>
                <elementReference>$Record.Industry</elementReference>
            </value>
        </inputAssignments>
    </subflows>

    <!-- Step 3: Send Notification -->
    <subflows>
        <name>Notify_Owner</name>
        <label>Notify Account Owner</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Create_Audit_Log</targetReference>
        </connector>
        <flowName>Sub_SendEmailAlert</flowName>
        <inputAssignments>
            <name>varEmailAddresses</name>
            <value>
                <elementReference>$Record.Owner.Email</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>varEmailSubject</name>
            <value>
                <stringValue>Account Industry Updated</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>varEmailBody</name>
            <value>
                <stringValue>Account {!$Record.Name} industry changed to {!$Record.Industry}. Related records have been updated.</stringValue>
            </value>
        </inputAssignments>
    </subflows>

    <!-- Step 4: Audit Logging -->
    <subflows>
        <name>Create_Audit_Log</name>
        <label>Create Audit Log</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <flowName>Sub_CreateAuditLog</flowName>
        <inputAssignments>
            <name>varObjectName</name>
            <value>
                <stringValue>Account</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>varRecordId</name>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>varFieldChanged</name>
            <value>
                <stringValue>Industry</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>varNewValue</name>
            <value>
                <elementReference>$Record.Industry</elementReference>
            </value>
        </inputAssignments>
    </subflows>
</Flow>
```

### Child Flow 1: Sub_UpdateContactIndustry

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <description>Updates Industry field on all Contacts related to an Account. Bulkified and reusable.</description>
    <label>Sub_UpdateContactIndustry</label>
    <processType>AutoLaunchedFlow</processType>

    <!-- Get Related Contacts -->
    <recordLookups>
        <name>Get_Related_Contacts</name>
        <label>Get Related Contacts</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <assignNullValuesIfNoRecordsFound>false</assignNullValuesIfNoRecordsFound>
        <connector>
            <targetReference>Check_If_Contacts_Found</targetReference>
        </connector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>AccountId</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>varAccountId</elementReference>
            </value>
        </filters>
        <getFirstRecordOnly>false</getFirstRecordOnly>
        <object>Contact</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordLookups>

    <!-- Decision: Were contacts found? -->
    <decisions>
        <name>Check_If_Contacts_Found</name>
        <label>Contacts Found?</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <defaultConnectorLabel>No Contacts</defaultConnectorLabel>
        <rules>
            <name>Contacts_Exist</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>Get_Related_Contacts</leftValueReference>
                <operator>IsNull</operator>
                <rightValue>
                    <booleanValue>false</booleanValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Update_Contacts_Bulk</targetReference>
            </connector>
            <label>Contacts Exist</label>
        </rules>
    </decisions>

    <!-- Bulk Update (NO DML in loops!) -->
    <recordUpdates>
        <name>Update_Contacts_Bulk</name>
        <label>Update Contacts (Bulk)</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <faultConnector>
            <targetReference>Log_Update_Error</targetReference>
        </faultConnector>
        <inputAssignments>
            <field>Industry</field>
            <value>
                <elementReference>varNewIndustry</elementReference>
            </value>
        </inputAssignments>
        <inputReference>Get_Related_Contacts</inputReference>
    </recordUpdates>

    <!-- Error Handler -->
    <subflows>
        <name>Log_Update_Error</name>
        <label>Log Update Error</label>
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
                <stringValue>Sub_UpdateContactIndustry</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>varRecordId</name>
            <value>
                <elementReference>varAccountId</elementReference>
            </value>
        </inputAssignments>
    </subflows>

    <start>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Get_Related_Contacts</targetReference>
        </connector>
    </start>
    <status>Draft</status>

    <!-- Input Variables -->
    <variables>
        <name>varAccountId</name>
        <dataType>String</dataType>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>varNewIndustry</name>
        <dataType>String</dataType>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
    </variables>
</Flow>
```

### Child Flow 2: Sub_UpdateOpportunityStages

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <description>Updates Opportunity Stages based on Industry. Demonstrates conditional logic in child flows.</description>
    <label>Sub_UpdateOpportunityStages</label>
    <processType>AutoLaunchedFlow</processType>

    <!-- Get Related Opportunities -->
    <recordLookups>
        <name>Get_Related_Opportunities</name>
        <label>Get Related Opportunities</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <assignNullValuesIfNoRecordsFound>false</assignNullValuesIfNoRecordsFound>
        <connector>
            <targetReference>Check_If_Opportunities_Found</targetReference>
        </connector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>AccountId</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>varAccountId</elementReference>
            </value>
        </filters>
        <filters>
            <field>IsClosed</field>
            <operator>EqualTo</operator>
            <value>
                <booleanValue>false</booleanValue>
            </value>
        </filters>
        <getFirstRecordOnly>false</getFirstRecordOnly>
        <object>Opportunity</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordLookups>

    <!-- Decision: Were opportunities found? -->
    <decisions>
        <name>Check_If_Opportunities_Found</name>
        <label>Opportunities Found?</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <defaultConnectorLabel>No Opportunities</defaultConnectorLabel>
        <rules>
            <name>Opportunities_Exist</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>Get_Related_Opportunities</leftValueReference>
                <operator>IsNull</operator>
                <rightValue>
                    <booleanValue>false</booleanValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Determine_Stage_By_Industry</targetReference>
            </connector>
            <label>Opportunities Exist</label>
        </rules>
    </decisions>

    <!-- Decision: Which stage based on Industry? -->
    <decisions>
        <name>Determine_Stage_By_Industry</name>
        <label>Determine Stage By Industry</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <defaultConnector>
            <targetReference>Set_Default_Stage</targetReference>
        </defaultConnector>
        <defaultConnectorLabel>Other Industries</defaultConnectorLabel>
        <rules>
            <name>Technology_Industry</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>varIndustry</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>Technology</stringValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Set_Technology_Stage</targetReference>
            </connector>
            <label>Technology</label>
        </rules>
        <rules>
            <name>Healthcare_Industry</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>varIndustry</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>Healthcare</stringValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Set_Healthcare_Stage</targetReference>
            </connector>
            <label>Healthcare</label>
        </rules>
    </decisions>

    <!-- Assignment: Technology Stage -->
    <assignments>
        <name>Set_Technology_Stage</name>
        <label>Set Technology Stage</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <assignmentItems>
            <assignToReference>varNewStage</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Discovery</stringValue>
            </value>
        </assignmentItems>
        <connector>
            <targetReference>Update_Opportunity_Stages</targetReference>
        </connector>
    </assignments>

    <!-- Assignment: Healthcare Stage -->
    <assignments>
        <name>Set_Healthcare_Stage</name>
        <label>Set Healthcare Stage</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <assignmentItems>
            <assignToReference>varNewStage</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Needs Analysis</stringValue>
            </value>
        </assignmentItems>
        <connector>
            <targetReference>Update_Opportunity_Stages</targetReference>
        </connector>
    </assignments>

    <!-- Assignment: Default Stage -->
    <assignments>
        <name>Set_Default_Stage</name>
        <label>Set Default Stage</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <assignmentItems>
            <assignToReference>varNewStage</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Qualification</stringValue>
            </value>
        </assignmentItems>
        <connector>
            <targetReference>Update_Opportunity_Stages</targetReference>
        </connector>
    </assignments>

    <!-- Bulk Update Opportunities -->
    <recordUpdates>
        <name>Update_Opportunity_Stages</name>
        <label>Update Opportunity Stages</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <faultConnector>
            <targetReference>Log_Update_Error</targetReference>
        </faultConnector>
        <inputAssignments>
            <field>StageName</field>
            <value>
                <elementReference>varNewStage</elementReference>
            </value>
        </inputAssignments>
        <inputReference>Get_Related_Opportunities</inputReference>
    </recordUpdates>

    <!-- Error Handler -->
    <subflows>
        <name>Log_Update_Error</name>
        <label>Log Update Error</label>
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
                <stringValue>Sub_UpdateOpportunityStages</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>varRecordId</name>
            <value>
                <elementReference>varAccountId</elementReference>
            </value>
        </inputAssignments>
    </subflows>

    <start>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Get_Related_Opportunities</targetReference>
        </connector>
    </start>
    <status>Draft</status>

    <!-- Variables -->
    <variables>
        <name>varAccountId</name>
        <dataType>String</dataType>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>varIndustry</name>
        <dataType>String</dataType>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>varNewStage</name>
        <dataType>String</dataType>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
    </variables>
</Flow>
```

## Benefits of This Pattern

### 1. **Modularity**
Each child flow has one clear responsibility:
- Sub_UpdateContactIndustry: Only handles Contact updates
- Sub_UpdateOpportunityStages: Only handles Opportunity logic
- Sub_SendEmailAlert: Only handles notifications

### 2. **Reusability**
Child flows can be called from multiple parents:
```
RTF_Account_IndustryChange → Sub_UpdateContactIndustry
RTF_Account_Merge → Sub_UpdateContactIndustry
Auto_BulkIndustryUpdate → Sub_UpdateContactIndustry
```

### 3. **Testability**
Test each child independently:
- Unit test: Sub_UpdateContactIndustry with 200 Contacts
- Unit test: Sub_UpdateOpportunityStages with various Industries
- Integration test: Parent flow with full scenario

### 4. **Maintainability**
Update logic in one place:
- Need to change Contact update logic? Edit Sub_UpdateContactIndustry
- All parent flows automatically get the update
- No need to find/replace across multiple flows

### 5. **Debugging**
Clear error isolation:
- Error in Contact update? Check Sub_UpdateContactIndustry logs
- Parent flow shows which step failed
- Error logs show exact subflow name

## Performance Considerations

### Governor Limits
- **Subflow Depth**: Max 50 levels (parent → child → grandchild...)
- **DML Statements**: Each child's DML counts toward 150 limit
- **SOQL Queries**: Each child's query counts toward 100 limit

### Best Practices
✅ Keep parent flow lightweight (orchestration only)
✅ Put complex logic in children
✅ Use bulkified operations in each child
✅ Monitor total DML/SOQL across all children

## Testing Strategy

### 1. Unit Test Each Child
```bash
# Test Sub_UpdateContactIndustry
Create 200 test Contacts → Manually invoke flow → Verify all updated
```

### 2. Integration Test Parent
```bash
# Test full orchestration
Update Account Industry → Verify all children executed → Check audit logs
```

### 3. Bulk Test
```bash
# Test with 200+ Accounts
Data Loader update 200 Accounts → Verify no governor limit errors
```

## When to Add More Children

Add a new child subflow when:
- New requirement emerges (e.g., "Also update Cases")
- Existing child gets too complex (>200 lines)
- You need to reuse logic elsewhere

```xml
<!-- Adding a new step is easy -->
<subflows>
    <name>Update_Cases</name>
    <label>Update Related Cases</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <connector>
        <targetReference>Notify_Owner</targetReference>
    </connector>
    <flowName>Sub_UpdateCaseIndustry</flowName>
    <inputAssignments>
        <name>varAccountId</name>
        <value>
            <elementReference>$Record.Id</elementReference>
        </value>
    </inputAssignments>
    <inputAssignments>
        <name>varIndustry</name>
        <value>
            <elementReference>$Record.Industry</elementReference>
        </value>
    </inputAssignments>
</subflows>
```

## Related Patterns

- [Sequential Orchestration](orchestration-sequential.md) - Chain flows A → B → C
- [Conditional Orchestration](orchestration-conditional.md) - Parent decides which children to call
- [Subflow Library](../references/subflow-library.md) - Reusable subflow templates

## Summary

**Parent-Child orchestration** transforms complex automations from monolithic nightmares into modular, maintainable architectures. Each child flow is focused, testable, and reusable—making your entire automation ecosystem more robust.

**Key Takeaway**: If your flow has more than 3 distinct responsibilities, consider breaking it into a parent orchestrator with child subflows. Your future self (and your team) will thank you! 🚀
