<!-- Parent: sf-flow/SKILL.md -->
# Transform vs Loop: A Decision Guide

When processing collections in Salesforce Flow, choosing between **Transform** and **Loop** elements can significantly impact both performance and maintainability. This guide provides clear decision criteria and best practices.

---

## Quick Decision Matrix

```
┌─────────────────────────────────────────────────────────────────────────┐
│ TRANSFORM vs LOOP DECISION MATRIX                                       │
├───────────────────────────────┬─────────────────────────────────────────┤
│ USE TRANSFORM                 │ USE LOOP                                │
├───────────────────────────────┼─────────────────────────────────────────┤
│ Mapping one collection to     │ IF/ELSE logic per record                │
│   another                     │ Different records need different paths  │
│ Bulk field assignments        │ Counters, flags, multi-step calcs       │
│ Simple formula calculations   │ Business rules vary per record          │
│ Preparing records for DML     │ Need to track state across iterations   │
│ Fewer elements, cleaner flows │ Complex conditional transformations     │
└───────────────────────────────┴─────────────────────────────────────────┘
```

**Simple Rule to Remember:**
- **Shaping data** → Use **Transform** (30-50% faster)
- **Making decisions per record** → Use **Loop**

---

## When Transform is the Right Choice

Transform is ideal when you need to:

### 1. Map One Collection to Another
Converting a collection of one record type to another (e.g., Contacts → Opportunity Contact Roles).

```
✅ GOOD: Get Contacts → Transform → Create Opportunity Contact Roles
❌ BAD:  Get Contacts → Loop → Assignment → Create Records (per iteration)
```

### 2. Bulk Field Assignments
Assigning the same field values across all records in a collection.

```
Example: Set Status = "Processed" for all records
Transform handles this in a single server-side operation.
```

### 3. Simple Calculations Using Formulas
Transform supports formulas for generating dynamic values during mapping.

```
Example: Calculate FullName from FirstName + ' ' + LastName
```

### 4. Prepare Records for Create/Update Operations
Building a collection of records to insert or update.

```
Example: Map Account fields to new Case records before bulk insert
```

### 5. Reduce Flow Elements
Transform consolidates what would be Loop + Assignment into a single element, making flows cleaner and easier to maintain.

---

## When You Still Need a Loop

Loop is required when:

### 1. IF/ELSE Logic Per Record
Different records need different processing paths.

```
Example:
- If Amount > 10000 → High priority
- If Amount > 5000 → Medium priority
- Else → Low priority
```

### 2. Counters, Flags, or Multi-Step Calculations
You need to maintain state across iterations.

```
Example: Count how many records meet certain criteria
         Track running totals
         Build comma-separated lists
```

### 3. Business Rules Vary Per Record
Each record may follow a different logic path based on its values.

```
Example: Route leads to different queues based on State + Industry
```

### 4. Complex Conditional Transformations
When the transformation logic itself is conditional and complex.

```
Example: If record has parent → use parent's values
         If orphan → use defaults
         If flagged → skip entirely
```

---

## Performance Comparison

| Metric | Transform | Loop + Assignment |
|--------|-----------|-------------------|
| **Processing Model** | Server-side bulk | Client-side iteration |
| **Speed** | 30-50% faster | Baseline |
| **CPU Time** | Lower | Higher |
| **DML Statements** | No change | No change |
| **Flow Elements** | 1 element | 2+ elements |
| **Maintainability** | Simpler | More complex |

### Why Transform is Faster

Transform processes the entire collection as a single server-side operation, while Loop iterates through each record individually. For large collections (100+ records), this difference becomes significant.

---

## Visual Comparison: Before and After

### BAD Pattern: Loop for Simple Mapping

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ❌ ANTI-PATTERN: Using Loop for Simple Field Mapping                   │
└─────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │ Get Records      │  Query Contacts
    │ (All Contacts)   │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ Loop             │  Iterate through each Contact
    │ (Contact Loop)   │◄──────────────────────────────┐
    └────────┬─────────┘                               │
             │ For Each                                │
             ▼                                         │
    ┌──────────────────┐                               │
    │ Assignment       │  Map Contact fields to        │
    │ (Map Fields)     │  OpportunityContactRole       │
    └────────┬─────────┘                               │
             │                                         │
             ▼                                         │
    ┌──────────────────┐                               │
    │ Add to Collection│  Build output collection      │
    └────────┬─────────┘                               │
             │ After Last ─────────────────────────────┘
             ▼
    ┌──────────────────┐
    │ Create Records   │  Insert all OCRs
    └──────────────────┘

    Problem: 4 elements, client-side iteration, slower
```

### GOOD Pattern: Transform for Simple Mapping

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ✅ BEST PRACTICE: Using Transform for Field Mapping                    │
└─────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │ Get Records      │  Query Contacts
    │ (All Contacts)   │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ Transform        │  Map Contact → OpportunityContactRole
    │ (Map to OCR)     │  (Server-side bulk operation)
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ Create Records   │  Insert all OCRs
    └──────────────────┘

    Benefits: 3 elements, server-side processing, 30-50% faster
```

---

## Transform XML Structure Reference

> **Important:** Create Transform elements in Flow Builder UI, then deploy. The XML structure is complex and error-prone to hand-write.

### Basic Structure

```xml
<transforms>
    <name>Transform_Contacts_To_OCR</name>
    <label>Transform Contacts to Opportunity Contact Roles</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <connector>
        <targetReference>Create_OCR_Records</targetReference>
    </connector>
    <!-- Input: collection of source records -->
    <inputVariable>col_Contacts</inputVariable>
    <!-- Output: collection of target records -->
    <outputVariable>col_OpportunityContactRoles</outputVariable>
    <!-- Field mappings with optional formulas -->
    <transformValueActions>
        <transformValueActionType>Map</transformValueActionType>
        <inputReference>col_Contacts.ContactId</inputReference>
        <outputReference>col_OpportunityContactRoles.ContactId</outputReference>
    </transformValueActions>
    <transformValueActions>
        <transformValueActionType>Map</transformValueActionType>
        <inputReference>var_OpportunityId</inputReference>
        <outputReference>col_OpportunityContactRoles.OpportunityId</outputReference>
    </transformValueActions>
    <transformValueActions>
        <transformValueActionType>Formula</transformValueActionType>
        <formula>"Primary"</formula>
        <outputReference>col_OpportunityContactRoles.Role</outputReference>
    </transformValueActions>
</transforms>
```

### Key Elements

| Element | Purpose |
|---------|---------|
| `inputVariable` | Source collection to transform |
| `outputVariable` | Target collection (output) |
| `transformValueActions` | Individual field mappings |
| `transformValueActionType` | `Map` (direct copy) or `Formula` (calculated) |
| `inputReference` | Source field path |
| `outputReference` | Target field path |
| `formula` | Formula expression (when type is Formula) |

---

## Testing Transform Elements

### 1. Flow Builder Debug Mode

```
Step-by-Step:
1. Open your flow in Flow Builder
2. Click the "Debug" button in the toolbar
3. Configure debug inputs:
   - Provide a sample collection (or create test records)
   - Set any required input variables
4. Run the debug
5. Inspect the Transform element output:
   - Verify field mappings are correct
   - Check formula calculations
   - Confirm collection size matches input
```

### 2. Apex Test Class Approach

```apex
@isTest
private class TransformFlowTest {

    @isTest
    static void testTransformMapsFieldsCorrectly() {
        // Setup: Create source records
        List<Contact> contacts = new List<Contact>();
        for (Integer i = 0; i < 200; i++) {
            contacts.add(new Contact(
                FirstName = 'Test' + i,
                LastName = 'Contact' + i,
                Email = 'test' + i + '@example.com'
            ));
        }
        insert contacts;

        // Create parent Opportunity
        Opportunity opp = new Opportunity(
            Name = 'Test Opp',
            StageName = 'Prospecting',
            CloseDate = Date.today().addDays(30)
        );
        insert opp;

        // Execute: Run the Transform flow
        Test.startTest();
        Map<String, Object> inputs = new Map<String, Object>{
            'inp_Contacts' => contacts,
            'inp_OpportunityId' => opp.Id
        };
        Flow.Interview.Transform_Contact_To_OCR flow =
            new Flow.Interview.Transform_Contact_To_OCR(inputs);
        flow.start();
        Test.stopTest();

        // Verify: Check transformed records were created
        List<OpportunityContactRole> ocrs = [
            SELECT Id, ContactId, OpportunityId, Role
            FROM OpportunityContactRole
            WHERE OpportunityId = :opp.Id
        ];

        System.assertEquals(200, ocrs.size(), 'All contacts should be mapped');
        for (OpportunityContactRole ocr : ocrs) {
            System.assertNotEquals(null, ocr.ContactId, 'ContactId should be mapped');
            System.assertEquals(opp.Id, ocr.OpportunityId, 'OpportunityId should be set');
        }
    }

    @isTest
    static void testTransformPerformance() {
        // Setup: Create 250 records (exceeds batch boundary)
        List<Contact> contacts = new List<Contact>();
        for (Integer i = 0; i < 250; i++) {
            contacts.add(new Contact(
                FirstName = 'Perf' + i,
                LastName = 'Test' + i
            ));
        }
        insert contacts;

        Opportunity opp = new Opportunity(
            Name = 'Perf Test',
            StageName = 'Prospecting',
            CloseDate = Date.today().addDays(30)
        );
        insert opp;

        // Execute and measure
        Test.startTest();
        Integer cpuBefore = Limits.getCpuTime();

        Map<String, Object> inputs = new Map<String, Object>{
            'inp_Contacts' => contacts,
            'inp_OpportunityId' => opp.Id
        };
        Flow.Interview.Transform_Contact_To_OCR flow =
            new Flow.Interview.Transform_Contact_To_OCR(inputs);
        flow.start();

        Integer cpuAfter = Limits.getCpuTime();
        Test.stopTest();

        // Assert: Transform should be efficient
        Integer cpuUsed = cpuAfter - cpuBefore;
        System.assert(cpuUsed < 5000,
            'Transform should use minimal CPU. Used: ' + cpuUsed + 'ms');
    }
}
```

### 3. CLI Performance Comparison

```bash
# Enable debug logging
sf apex tail log --color

# Run Transform flow via anonymous Apex
sf apex run -f scripts/run-transform-flow.apex

# Run equivalent Loop flow for comparison
sf apex run -f scripts/run-loop-flow.apex

# Compare CPU_TIME in debug logs
# Transform should show ~30-50% lower CPU_TIME
```

### Sample Anonymous Apex (`scripts/run-transform-flow.apex`)

```apex
// Query source records
List<Contact> contacts = [SELECT Id, FirstName, LastName, Email FROM Contact LIMIT 200];

// Get target Opportunity
Opportunity opp = [SELECT Id FROM Opportunity LIMIT 1];

// Run Transform flow
Map<String, Object> inputs = new Map<String, Object>{
    'inp_Contacts' => contacts,
    'inp_OpportunityId' => opp.Id
};

Flow.Interview flow = Flow.Interview.createInterview('Transform_Contact_To_OCR', inputs);
flow.start();

System.debug('Transform completed. CPU Time: ' + Limits.getCpuTime() + 'ms');
```

---

## Migration Checklist: Loop to Transform

If you have existing flows using Loop for simple field mapping, consider migrating:

- [ ] Identify Loop elements that only do field assignment (no decisions)
- [ ] Verify no counters, flags, or state tracking is needed
- [ ] Create equivalent Transform element in Flow Builder UI
- [ ] Test with same data set
- [ ] Compare debug output for correctness
- [ ] Compare CPU time for performance gain
- [ ] Replace Loop + Assignment with single Transform
- [ ] Validate and deploy

---

## Common Mistakes to Avoid

### 1. Using Transform for Conditional Logic

```
❌ WRONG: Trying to add IF/ELSE inside Transform
   Transform doesn't support per-record branching.

✅ RIGHT: Use Loop + Decision for conditional processing.
```

### 2. Ignoring the UI Recommendation

```
❌ WRONG: Hand-writing Transform XML
   The XML structure is complex with strict ordering requirements.

✅ RIGHT: Always create Transform in Flow Builder, then deploy.
```

### 3. Over-Optimizing Simple Flows

```
❌ WRONG: Converting every Loop to Transform
   Some flows process very small collections where optimization doesn't matter.

✅ RIGHT: Focus on loops processing 50+ records regularly.
```

---

## Related Documentation

- [Loop Pattern Template](../assets/elements/loop-pattern.xml) - When Loop is the right choice
- [Transform Pattern Template](../assets/elements/transform-pattern.xml) - Reference XML structure
- [Flow Best Practices](./flow-best-practices.md) - General optimization guidelines
- [Governance Checklist](./governance-checklist.md) - Pre-deployment validation

---

## Attribution

This guide was inspired by content shared by:
- **Jalumchi Akpoke** - Transform vs Loop decision pattern visualization
- **Shubham Bhardwaj** - Original YouTube video on Transform efficiency

See [CREDITS.md](../CREDITS.md) for full attribution.
