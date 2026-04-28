<!-- Parent: sf-flow/SKILL.md -->
# Salesforce Flow XML Metadata Gotchas

Critical XML metadata constraints and known issues when deploying flows via Metadata API.

## storeOutputAutomatically Data Leak Risk (v2.0.0)

**⚠️ SECURITY WARNING**: When `storeOutputAutomatically="true"` in recordLookups, **ALL fields** are retrieved and stored.

### Risks

1. **Data Leak**: Sensitive fields (SSN, salary, etc.) may be exposed unintentionally
2. **Performance**: Large objects with many fields impact query performance
3. **Screen Flow Exposure**: In screen flows, external users could access all data

### Recommended Pattern

**Always specify only the fields you need:**

```xml
<recordLookups>
    <name>Get_Account</name>
    <!-- Specify exact fields needed -->
    <queriedFields>Id</queriedFields>
    <queriedFields>Name</queriedFields>
    <queriedFields>Industry</queriedFields>
    <!-- Store in explicit variable -->
    <outputReference>rec_Account</outputReference>
</recordLookups>
```

**Avoid:**
```xml
<recordLookups>
    <name>Get_Account</name>
    <!-- Retrieves ALL fields - security risk! -->
    <storeOutputAutomatically>true</storeOutputAutomatically>
</recordLookups>
```

---

## Relationship Fields Not Supported in recordLookups (CRITICAL)

**⚠️ DEPLOYMENT BLOCKER**: Flow's Get Records (recordLookups) CANNOT query parent relationship fields.

### What Doesn't Work

```xml
<!-- ❌ THIS WILL FAIL DEPLOYMENT -->
<recordLookups>
    <name>Get_User</name>
    <object>User</object>
    <queriedFields>Id</queriedFields>
    <queriedFields>Name</queriedFields>
    <queriedFields>Manager.Name</queriedFields>  <!-- FAILS! -->
</recordLookups>
```

**Error**: `field integrity exception: unknown (The field "Manager.Name" for the object "User" doesn't exist.)`

### Why It Fails

- Flow's recordLookups only supports direct fields on the queried object
- Parent relationship traversal (dot notation like `Parent.Field`) is NOT supported
- This is different from SOQL in Apex which supports relationship queries

### Fields That WON'T Work

| Object | Invalid Field | Error |
|--------|---------------|-------|
| User | `Manager.Name` | Manager.Name doesn't exist |
| Contact | `Account.Name` | Account.Name doesn't exist |
| Case | `Account.Owner.Email` | Account.Owner.Email doesn't exist |
| Opportunity | `Account.Industry` | Account.Industry doesn't exist |

### Correct Solution: Two-Step Query

```xml
<!-- Step 1: Get the child record with lookup ID -->
<recordLookups>
    <name>Get_User</name>
    <object>User</object>
    <queriedFields>Id</queriedFields>
    <queriedFields>Name</queriedFields>
    <queriedFields>ManagerId</queriedFields>  <!-- ✅ Get the ID only -->
    <outputReference>rec_User</outputReference>
</recordLookups>

<!-- Step 2: Query parent record using the lookup ID -->
<recordLookups>
    <name>Get_Manager</name>
    <object>User</object>
    <filters>
        <field>Id</field>
        <operator>EqualTo</operator>
        <value>
            <elementReference>rec_User.ManagerId</elementReference>
        </value>
    </filters>
    <queriedFields>Id</queriedFields>
    <queriedFields>Name</queriedFields>
    <outputReference>rec_Manager</outputReference>
</recordLookups>
```

### Flow Routing

Ensure your flow checks for null before using the parent record:
```xml
<decisions>
    <name>Check_Manager_Exists</name>
    <rules>
        <conditions>
            <leftValueReference>rec_Manager</leftValueReference>
            <operator>IsNull</operator>
            <rightValue><booleanValue>false</booleanValue></rightValue>
        </conditions>
    </rules>
</decisions>
```

---

## $Record vs $Record__c Confusion (Record-Triggered Flows)

**⚠️ COMMON MISTAKE**: Confusing Flow's `$Record` with Process Builder's `$Record__c`.

### What's the Difference?

| Variable | Context | Usage |
|----------|---------|-------|
| `$Record` | Flow (Record-Triggered) | Single record that triggered the flow |
| `$Record__c` | Process Builder | Collection of records in trigger batch |

### The Mistake

Trying to create a loop over `$Record__c` in a Flow:

```xml
<!-- ❌ THIS DOES NOT EXIST IN FLOWS -->
<loops>
    <collectionReference>$Record__c</collectionReference>  <!-- INVALID! -->
</loops>
```

### Why This Happens

- Process Builder used `$Record__c` to represent the batch of triggering records
- Developers migrating from Process Builder assume Flows work the same way
- In Flows, `$Record` is always a **single record**, not a collection
- The platform handles bulk batching automatically

### Correct Approach in Record-Triggered Flows

**Use `$Record` directly without loops:**

```xml
<!-- ✅ CORRECT: Direct access to triggered record -->
<decisions>
    <conditions>
        <leftValueReference>$Record.StageName</leftValueReference>
        <operator>EqualTo</operator>
        <rightValue><stringValue>Closed Won</stringValue></rightValue>
    </conditions>
</decisions>

<!-- ✅ Build task using $Record fields -->
<assignments>
    <assignmentItems>
        <assignToReference>rec_Task.WhatId</assignToReference>
        <value><elementReference>$Record.Id</elementReference></value>
    </assignmentItems>
</assignments>
```

### When You DO Need Loops

Only when processing **related records**, not the triggered record:

```xml
<!-- ✅ CORRECT: Loop over RELATED records -->
<recordLookups>
    <filters>
        <field>AccountId</field>
        <value><elementReference>$Record.AccountId</elementReference></value>
    </filters>
    <outputReference>col_RelatedContacts</outputReference>
</recordLookups>

<loops>
    <collectionReference>col_RelatedContacts</collectionReference>  <!-- ✅ Valid -->
</loops>
```

---

## recordLookups Conflicts

**NEVER use both** `<storeOutputAutomatically>` AND `<outputReference>` together.

**Choose ONE approach:**
```xml
<!-- Option 1: Auto-store (creates variable automatically) - NOT RECOMMENDED -->
<storeOutputAutomatically>true</storeOutputAutomatically>

<!-- Option 2: Explicit variable - RECOMMENDED -->
<outputReference>rec_AccountRecord</outputReference>
```

## Element Ordering in recordLookups

Elements must follow this order:
1. `<name>` 2. `<label>` 3. `<locationX>` 4. `<locationY>` 5. `<assignNullValuesIfNoRecordsFound>` 6. `<connector>` 7. `<filterLogic>` 8. `<filters>` 9. `<getFirstRecordOnly>` 10. `<object>` 11. `<outputReference>` OR `<storeOutputAutomatically>` 12. `<queriedFields>`

## Transform Element

**Recommendation**: Create Transform elements in Flow Builder UI, then deploy - do NOT hand-write.

Issues with hand-written Transform:
- Complex nested XML structure with strict ordering
- `inputReference` placement varies by context
- Multiple conflicting rules in Metadata API

## Subflow Elements: What Works and What Doesn't

Record-triggered flows **CAN** call subflows via XML deployment (confirmed API 66.0, Spring '26).

### Working `<subflows>` Example

```xml
<subflows>
    <name>Call_Validation_Subflow</name>
    <label>Call Validation Subflow</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <connector>
        <targetReference>Next_Element</targetReference>
    </connector>
    <flowName>Validation_Subflow</flowName>
    <inputAssignments>
        <name>recordId</name>
        <value>
            <elementReference>$Record.Id</elementReference>
        </value>
    </inputAssignments>
    <outputAssignments>
        <assignToReference>validationResult</assignToReference>
        <name>isValid</name>
    </outputAssignments>
</subflows>
```

### `<faultConnector>` Is NOT Valid on `<subflows>`

Adding a `<faultConnector>` to a `<subflows>` element causes a deployment error:

**Error**: `The "faultConnector" field should not be set for "subflows" elements.`

**Valid `<faultConnector>` targets** (elements that DO support fault paths):
- `<actionCalls>` — Apex invocable actions, external services
- `<recordCreates>` — DML create operations
- `<recordUpdates>` — DML update operations
- `<recordDeletes>` — DML delete operations

### Correct Pattern: Handle Faults Inside the Subflow

Instead of adding a fault connector on the `<subflows>` element, handle faults **within** the subflow itself and surface errors via output variables:

1. Inside the subflow: wrap DML/action calls with fault connectors
2. On fault: set an output variable (e.g., `errorMessage`) with the error details
3. In the parent flow: check the output variable after the subflow call and branch accordingly

## Fault Connectors Cannot Self-Reference (CRITICAL)

**⚠️ DEPLOYMENT BLOCKER**: An element CANNOT have a fault connector pointing to itself.

### What Doesn't Work

```xml
<!-- ❌ THIS WILL FAIL DEPLOYMENT -->
<recordUpdates>
    <name>Update_Account</name>
    <label>Update Account</label>
    <connector>
        <targetReference>Next_Element</targetReference>
    </connector>
    <faultConnector>
        <targetReference>Update_Account</targetReference>  <!-- FAILS! Self-reference -->
    </faultConnector>
    <!-- ... -->
</recordUpdates>
```

**Error**: `The element "Update_Account" cannot be connected to itself.`

### Why This Matters

- Self-referencing fault connectors would create infinite loops on failure
- Salesforce validates this during deployment and blocks it
- This applies to ALL connector types (faultConnector, connector, nextValueConnector, etc.)

### Correct Fault Handling Patterns

**Option 1: Route to dedicated error handler:**
```xml
<recordUpdates>
    <name>Update_Account</name>
    <faultConnector>
        <targetReference>Handle_Update_Error</targetReference>  <!-- ✅ Different element -->
    </faultConnector>
</recordUpdates>

<assignments>
    <name>Handle_Update_Error</name>
    <!-- Log error, set flag, etc. -->
</assignments>
```

**Option 2: Route to error logging assignment:**
```xml
<recordUpdates>
    <name>Update_Account</name>
    <faultConnector>
        <targetReference>Log_Error_And_Continue</targetReference>  <!-- ✅ -->
    </faultConnector>
</recordUpdates>
```

**Option 3: Omit fault connector (flow will terminate on error):**
```xml
<recordUpdates>
    <name>Update_Account</name>
    <connector>
        <targetReference>Next_Element</targetReference>
    </connector>
    <!-- No faultConnector - flow terminates on failure -->
</recordUpdates>
```

### Best Practice

- Always route fault connectors to a dedicated error handling element
- Use an assignment to capture `{!$Flow.FaultMessage}` before logging
- Consider whether the flow should continue or terminate on failure

---

## Root-Level Element Ordering (CRITICAL)

Salesforce Metadata API requires **strict alphabetical ordering** at root level.

### Complete Element Type List (Alphabetical Order)

All elements of the same type MUST be grouped together. You CANNOT have elements of one type scattered across the file.

```
1.  <apiVersion>
2.  <assignments>         ← ALL assignments together
3.  <constants>
4.  <decisions>           ← ALL decisions together
5.  <description>
6.  <environments>
7.  <formulas>
8.  <interviewLabel>
9.  <label>
10. <loops>               ← ALL loops together
11. <processMetadataValues>
12. <processType>
13. <recordCreates>       ← ALL recordCreates together
14. <recordDeletes>       ← ALL recordDeletes together
15. <recordLookups>       ← ALL recordLookups together
16. <recordUpdates>       ← ALL recordUpdates together
17. <runInMode>
18. <screens>             ← ALL screens together
19. <start>
20. <status>
21. <subflows>            ← ALL subflows together
22. <textTemplates>
23. <variables>           ← ALL variables together
24. <waits>
```

### The Grouping Rule (CRITICAL)

**Wrong** - Assignment after loops section:
```xml
<assignments>
    <name>Set_Initial_Values</name>
    <!-- ... -->
</assignments>
<loops>
    <name>Loop_Contacts</name>
    <!-- ... -->
</loops>
<assignments>  <!-- ❌ FAILS: Can't have assignments after loops! -->
    <name>Increment_Counter</name>
    <!-- ... -->
</assignments>
```

**Error**: `Element assignments is duplicated at this location in type Flow`

**Correct** - All assignments together:
```xml
<assignments>  <!-- ✅ All assignments grouped -->
    <name>Increment_Counter</name>
    <!-- ... -->
</assignments>
<assignments>
    <name>Set_Initial_Values</name>
    <!-- ... -->
</assignments>
<loops>
    <name>Loop_Contacts</name>
    <!-- ... -->
</loops>
```

### Why This Happens

When generating flows programmatically or manually editing XML:
- Easy to add a new element near related logic
- Salesforce requires ALL elements of same type to appear consecutively
- The "duplicate" error is misleading - it means elements aren't grouped

**Note**: API 60.0+ does NOT use `<bulkSupport>` - bulk processing is automatic.

## Common Deployment Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Element X is duplicated" | Elements not alphabetically ordered | Reorder elements |
| "Element bulkSupport invalid" | Using deprecated element (API 60.0+) | Remove `<bulkSupport>` |
| "Error parsing file" | Malformed XML | Validate XML syntax |
| "field 'X.Y' doesn't exist" | Relationship field in queriedFields | Use two-step query pattern |
| "$Record__Prior can only be used..." | Using $Record__Prior with Create trigger | Change to Update or CreateAndUpdate |
| "You can't use the Flows action type..." | Subflow in AutoLaunchedFlow | Use inline logic instead |
| "nothing is connected to the Start element" | Empty flow with no elements | Add at least one assignment connected to start |

---

## Start Element Must Have Connector (For Agentforce Flow Actions)

**⚠️ DEPLOYMENT BLOCKER**: Flows used as Agent Script actions MUST have at least one element connected to the Start element.

### What Doesn't Work

```xml
<!-- ❌ THIS WILL FAIL DEPLOYMENT -->
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <label>My Agent Flow</label>
    <processType>AutoLaunchedFlow</processType>
    <status>Active</status>

    <variables>
        <name>inp_SearchQuery</name>
        <dataType>String</dataType>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
    </variables>

    <start>
        <locationX>50</locationX>
        <locationY>50</locationY>
        <!-- No connector! -->
    </start>
</Flow>
```

**Error**: `field integrity exception: unknown (The flow can't run because nothing is connected to the Start element.)`

### Why This Happens

- Minimal flows with only inputs/outputs and no logic still need at least one element
- Salesforce validates that the flow has something to execute
- This is especially common when creating stub/mock flows for testing

### Correct Pattern: Add Assignment Element

Even for simple pass-through flows, add at least one assignment:

```xml
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <label>My Agent Flow</label>
    <processType>AutoLaunchedFlow</processType>
    <status>Active</status>

    <variables>
        <name>inp_SearchQuery</name>
        <dataType>String</dataType>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>out_Result</name>
        <dataType>String</dataType>
        <isInput>false</isInput>
        <isOutput>true</isOutput>
    </variables>

    <!-- ✅ Start connected to assignment -->
    <start>
        <locationX>50</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Set_Result</targetReference>
        </connector>
    </start>

    <!-- ✅ At least one element required -->
    <assignments>
        <name>Set_Result</name>
        <label>Set Result</label>
        <locationX>176</locationX>
        <locationY>158</locationY>
        <assignmentItems>
            <assignToReference>out_Result</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Success</stringValue>
            </value>
        </assignmentItems>
    </assignments>
</Flow>
```

### When Creating Agentforce Flow Actions

1. **Define inputs** matching Agent Script action `inputs:`
2. **Define outputs** matching Agent Script action `outputs:`
3. **Add at least one assignment** to set output values
4. **Connect start to assignment** via `<connector>`
5. **Set status to Active** for agent to invoke

---

## Summary: Lessons Learned

### Fault Connector Self-Reference
- **Problem**: Fault connector pointing to the same element
- **Error**: "The element cannot be connected to itself"
- **Solution**: Route fault connectors to a dedicated error handler element

### XML Element Grouping
- **Problem**: Elements of same type scattered across the file
- **Error**: "Element X is duplicated at this location"
- **Solution**: Group ALL elements of same type together, in alphabetical order by type

### Relationship Fields
- **Problem**: Querying `Parent.Field` in Get Records
- **Solution**: Two separate queries - child first, then parent by ID

### Record-Triggered Flow Architecture
- **Problem**: Creating loops over triggered records
- **Solution**: Use `$Record` directly - platform handles batching

### Deployment
- **Problem**: Using direct CLI commands
- **Solution**: Always use sf-deploy skill

### $Record Context
- **Problem**: Confusing Flow's `$Record` with Process Builder's `$Record__c`
- **Solution**: `$Record` is single record, use without loops

### Standard Objects for Testing
- **Problem**: Custom objects may not exist in target org
- **Solution**: When testing flow generation/deployment, prefer standard objects (Account, Contact, Opportunity, Task) for guaranteed deployability

### RTF + Subflow Deployment Order (Validated 2026-03-05)
- **Problem**: Parent RTF references a child subflow that doesn't exist or isn't active
- **Info Warning**: "The referenced flow X has no active version" (deploys succeed but flow fails at runtime)
- **Solution**: Deploy and activate child subflow FIRST, then deploy and activate parent RTF
- **Activation Order**: Child Active -> Parent Active (reverse for deactivation: Parent Draft -> Child Draft)
- **Proof**: Case Escalation pattern — RTF on Case (after-save, Priority=High AND Status=New) calls Sub_EscalateCase to create Task. Passed positive, negative, and bulk (5x) tests on AgentforceTesting org, API 66.0
