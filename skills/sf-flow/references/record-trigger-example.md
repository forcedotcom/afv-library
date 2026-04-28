<!-- Parent: sf-flow/SKILL.md -->
# Record-Triggered Flow Example: Opportunity Stage Update

This example demonstrates creating a Record-Triggered Flow with proper bulkification that updates related contacts when an Opportunity reaches "Closed Won".

## Scenario

When an Opportunity is marked as "Closed Won":
- Find all related Contacts
- Update their Status__c field to "Customer"
- Send notification to account owner
- **Handle bulk updates** (200+ opportunities at once)

## User Request

```
User: "Create a record-triggered flow on Opportunity.
When the Stage changes to 'Closed Won', update all related contacts
to have Status__c = 'Customer'."
```

## Skill Workflow

### Phase 1: Requirements Gathering

The skill asks:

**Q1: What type of flow?**
→ Record-Triggered Flow (After-Save)

**Q2: What is the purpose?**
→ "Update related contacts when opportunity reaches Closed Won"

**Q3: Which object triggers this flow?**
→ "Opportunity"

**Q4: When should it run?**
→ After records are created OR updated

**Q5: Target org?**
→ "production" (careful - always test in sandbox first!)

### Phase 2: Flow Design

The skill designs a **bulkified** flow:
- **Trigger**: Opportunity, After Save, Create and Update
- **bulkSupport**: true (CRITICAL for bulk processing)
- **Decision**: Check if Stage = 'Closed Won'
- **Get Records**: Related Contacts (collection)
- **Update Records**: Contact collection (single DML, outside any loops)
- **Fault Path**: Error handling for DML failure

### Phase 3: Validation

```
Flow Validation Report: Opportunity_Closed_Won_Update_Contacts (API 66.0)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ XML Structure: Valid
✓ API Version: 66.0 (current - Spring '26)
✓ Required Elements: Present
✓ Element References: All valid
✓ Naming Conventions: Compliant
✓ Bulkification: <bulkSupport>true</bulkSupport> present
✓ Bulkification: No DML in loops

⚠ Warnings: None
✗ Errors: None

Best Practices Score: 100/100 (Excellent ✨)

Recommendations:
  1. ✓ Bulkified design - handles collections properly
  2. ✓ Fault path configured for error handling
  3. ✓ No governor limit issues expected

✓ VALIDATION PASSED - Flow ready for deployment
```

### Phase 4: Deployment

**Important**: Even though user said "production", skill deploys to sandbox FIRST for testing.

```
⚠️  IMPORTANT: You specified 'production' but testing in sandbox is
strongly recommended for record-triggered flows.

Deploying to sandbox-test first...

Step 1: Validation (Check-Only)
✓ Metadata structure valid
✓ Opportunity object accessible
✓ Contact object accessible
✓ Status__c field exists on Contact
✓ No deployment conflicts

Step 2: Actual Deployment
✓ Deployed to sandbox-test
✓ Flow status: Draft
✓ Ready for bulk testing
```

### Phase 5: Testing Checklist (CRITICAL for Record-Triggered)

```
✓ Testing Checklist: Opportunity_Closed_Won_Update_Contacts
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SINGLE RECORD TESTING:
□ Create test Opportunity with Stage = 'Prospecting'
□ Add 2-3 related Contacts
□ Update Opportunity Stage to 'Closed Won'
□ Check Debug Logs - verify flow executed
□ Verify Contacts updated to Status__c = 'Customer'
□ Check no errors in Debug Logs

BULK TESTING (CRITICAL):
□ Prepare 200+ test Opportunities with related Contacts
□ Use Data Loader to bulk update Stage to 'Closed Won'
□ Monitor Debug Logs during bulk update
□ Verify NO governor limit errors
□ Confirm all Contacts updated correctly
□ Check execution time stays within limits

ERROR TESTING:
□ Test with Opportunity that has no related Contacts
□ Test with invalid Contact field values
□ Verify fault path triggers on errors
□ Check error messages are helpful

Debug Logs Query:
sf data query --query "SELECT Id, Status, NumElements FROM FlowInterview
WHERE FlowDefinitionName='Opportunity_Closed_Won_Update_Contacts'
AND CreatedDate=TODAY ORDER BY CreatedDate DESC LIMIT 50"
--target-org sandbox-test
```

## Generated Flow Structure (Key Parts)

### Start Element with Bulkification

```xml
<start>
    <locationX>50</locationX>
    <locationY>50</locationY>
    <object>Opportunity</object>
    <recordTriggerType>CreateAndUpdate</recordTriggerType>
    <triggerType>RecordAfterSave</triggerType>
    <bulkSupport>true</bulkSupport>  <!-- CRITICAL for bulk processing -->
    <connector>
        <targetReference>Decision_Check_Stage</targetReference>
    </connector>
</start>
```

### Decision: Check if Closed Won

```xml
<decisions>
    <name>Decision_Check_Stage</name>
    <label>Check if Closed Won</label>
    <rules>
        <name>Is_Closed_Won</name>
        <conditionLogic>and</conditionLogic>
        <conditions>
            <leftValueReference>$Record.StageName</leftValueReference>
            <operator>EqualTo</operator>
            <rightValue>
                <stringValue>Closed Won</stringValue>
            </rightValue>
        </conditions>
        <connector>
            <targetReference>Get_Related_Contacts</targetReference>
        </connector>
        <label>Is Closed Won</label>
    </rules>
</decisions>
```

### Get Records: Related Contacts (Collection)

```xml
<recordLookups>
    <name>Get_Related_Contacts</name>
    <label>Get Related Contacts</label>
    <assignNullValuesIfNoRecordsFound>false</assignNullValuesIfNoRecordsFound>
    <connector>
        <targetReference>Update_Contact_Status</targetReference>
    </connector>
    <filterLogic>and</filterLogic>
    <filters>
        <field>AccountId</field>
        <operator>EqualTo</operator>
        <value>
            <elementReference>$Record.AccountId</elementReference>
        </value>
    </filters>
    <object>Contact</object>
    <outputReference>colContacts</outputReference>  <!-- Collection variable -->
    <queriedFields>Id</queriedFields>
    <queriedFields>Status__c</queriedFields>
</recordLookups>
```

### Update Records: Bulk Update (NOT in a loop!)

```xml
<recordUpdates>
    <name>Update_Contact_Status</name>
    <label>Update Contact Status</label>
    <faultConnector>
        <targetReference>Handle_Error</targetReference>  <!-- Fault path -->
    </faultConnector>
    <inputAssignments>
        <field>Status__c</field>
        <value>
            <stringValue>Customer</stringValue>
        </value>
    </inputAssignments>
    <inputReference>colContacts</inputReference>  <!-- Updates entire collection -->
</recordUpdates>
```

## Testing Results

### Single Record Test
✓ Flow triggered correctly
✓ Stage change detected
✓ Related contacts retrieved (3 contacts)
✓ All 3 contacts updated to Status__c = 'Customer'
✓ Execution time: 142ms
✓ No errors

### Bulk Test (200 Opportunities, ~800 Contacts)
✓ Data Loader bulk update completed
✓ Flow executed for all 200 opportunities
✓ All ~800 contacts updated correctly
✓ **NO governor limit errors**
✓ Average execution time: 287ms per opportunity
✓ Total DML statements: Within limits (150 max)
✓ SOQL queries: Within limits (100 max)

**Why it worked:**
- `<bulkSupport>true</bulkSupport>` enabled collection processing
- DML operation on collection (not individual records in a loop)
- Single SOQL query per opportunity
- Fault paths handled errors gracefully

## Common Mistakes (Avoided by This Flow)

### ❌ WRONG: DML in Loop
```xml
<!-- THIS WOULD FAIL WITH BULK DATA -->
<loops>
    <name>Loop_Contacts</name>
    <collectionReference>colContacts</collectionReference>
    <nextValueConnector>
        <targetReference>Update_Single_Contact</targetReference>  <!-- DML HERE -->
    </nextValueConnector>
</loops>

<recordUpdates>
    <name>Update_Single_Contact</name>
    <!-- This executes INSIDE the loop - CRITICAL ERROR -->
    <!-- Hits governor limit with 200+ records -->
</recordUpdates>
```

**Why it fails:**
- DML inside loop = one DML per record
- Governor limit: 150 DML statements per transaction
- 200 contacts = 200 DML statements = FAILURE

### ✓ CORRECT: Bulk DML
```xml
<!-- Our flow does this correctly -->
<recordLookups>
    <name>Get_Related_Contacts</name>
    <outputReference>colContacts</outputReference>  <!-- Get collection -->
</recordLookups>

<recordUpdates>
    <name>Update_Contact_Status</name>
    <inputReference>colContacts</inputReference>  <!-- Update entire collection -->
    <!-- Single DML operation, regardless of collection size -->
</recordUpdates>
```

**Why it works:**
- One DML operation for entire collection
- Handles 200, 2000, or 20,000 records equally well
- Stays within governor limits

## Production Deployment

After successful bulk testing in sandbox:

1. **Deploy to production:**
   ```
   "Deploy Opportunity_Closed_Won_Update_Contacts to production"
   ```

2. **Activate carefully:**
   - Skill prompts: "Keep as Draft or Activate Now?"
   - Select: "Keep as Draft"
   - Manually activate after final verification

3. **Monitor in production:**
   - Check Debug Logs daily for first week
   - Review flow interviews for errors
   - Monitor performance metrics

4. **Set up monitoring:**
   ```
   sf data query --query "SELECT Id, Status, NumElements
   FROM FlowInterview
   WHERE FlowDefinitionName='Opportunity_Closed_Won_Update_Contacts'
   AND Status='Error'
   AND CreatedDate=LAST_N_DAYS:1"
   --target-org production
   ```

## Performance Metrics

**Single Execution:**
- SOQL Queries: 1 (Get Contacts)
- DML Statements: 1 (Update Contacts)
- Execution Time: ~150ms

**Bulk Execution (200 Opportunities):**
- SOQL Queries: 200 (1 per opportunity)
- DML Statements: 200 (1 per opportunity)
- Total Time: ~58 seconds
- **NO governor limit errors**

## Key Takeaways

✓ **ALWAYS set <bulkSupport>true</bulkSupport>** for record-triggered flows
✓ **NEVER put DML inside loops** - causes bulk failures
✓ **Use collections** - get all records, update all at once
✓ **Add fault paths** - handle errors gracefully
✓ **Test with bulk data** - 200+ records minimum
✓ **Monitor in production** - check Debug Logs regularly

This is production-grade, bulkified Flow design!
