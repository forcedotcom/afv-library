<!-- Parent: sf-flow/SKILL.md -->
# Salesforce Flow Testing Guide

> **Version**: 2.0.0
> **Last Updated**: December 2025
> **Purpose**: Comprehensive testing strategies for all Salesforce Flow types

This guide provides structured testing approaches to ensure your flows work correctly under all conditions.

---

## Table of Contents

1. [Test Path Coverage](#1-test-path-coverage)
2. [Graduated Bulk Testing](#2-graduated-bulk-testing)
3. [Edge Case Checklist](#3-edge-case-checklist)
4. [User Context Testing](#4-user-context-testing)
5. [Flow Type-Specific Testing](#5-flow-type-specific-testing)
6. [Deployment Testing Sequence](#6-deployment-testing-sequence)
7. [Regression Testing](#7-regression-testing)
8. [Governor Limits Testing](#8-governor-limits-testing)
9. [Post-Deployment Verification](#9-post-deployment-verification)

---

## 1. Test Path Coverage

Before testing, map every possible route through your flow.

### Identify All Paths

Document these for every flow:
- **Decision element outcomes** (all branches, including default)
- **Loop iterations** (0 items, 1 item, many items)
- **Fault paths** (every DML element's error path)
- **Conditional screens** (all visibility combinations)

### Test Matrix Template

Create a test matrix for each flow:

| Test Case ID | Path Description | Input Data | Expected Output | Actual Result | Pass/Fail |
|--------------|------------------|------------|-----------------|---------------|-----------|
| TC-001 | Happy path - all valid | Valid Account data | Record created | | |
| TC-002 | Null input - missing required | AccountId = null | Error message shown | | |
| TC-003 | Empty collection | 0 records from query | Loop skips, no DML | | |
| TC-004 | Fault path - DML fails | Invalid record data | Error logged, user notified | | |
| TC-005 | Decision branch A | Type = 'Customer' | Customer logic runs | | |
| TC-006 | Decision branch B | Type = 'Partner' | Partner logic runs | | |

### Positive vs Negative Testing

**Positive Testing**: Valid inputs → Expected successful outcomes
- Correct data formats
- Required fields populated
- Valid record IDs

**Negative Testing**: Invalid inputs → Graceful failure/error handling
- Missing required values
- Invalid formats
- Non-existent record IDs
- Null values where not expected

---

## 2. Graduated Bulk Testing

Test in this progression to isolate issues:

| Stage | Record Count | Purpose | What to Check |
|-------|--------------|---------|---------------|
| 1 | Single (1) | Logic correctness | Flow completes, correct output |
| 2 | Small batch (10-20) | Basic bulkification | No obvious errors |
| 3 | Medium batch (50-100) | Performance baseline | Execution time acceptable |
| 4 | Large batch (200+) | Governor limit validation | No limit exceeded errors |
| 5 | Stress test (10,000+) | Edge case (optional) | System stability |

### Why 200+ Records?

- Record-triggered flows fire in **batches of 200**
- Testing at this level ensures your flow survives real-world triggers
- Data Loader operations commonly process 200 records per batch

### How to Bulk Test

**Via Data Loader**:
1. Create CSV with test data (200+ rows)
2. Load via Data Loader or Workbench
3. Monitor Debug Logs during execution

**Via Apex**:
```apex
@isTest
static void testBulkTrigger() {
    List<Account> accounts = new List<Account>();
    for (Integer i = 0; i < 200; i++) {
        accounts.add(new Account(Name = 'Test ' + i));
    }

    Test.startTest();
    insert accounts;  // Triggers record-triggered flow
    Test.stopTest();

    // Assert expected outcomes
    System.assertEquals(200, [SELECT COUNT() FROM Account WHERE Name LIKE 'Test%']);
}
```

**Via Flow Simulator**:
```bash
python3 validators/flow_simulator.py \
  force-app/main/default/flows/[FlowName].flow-meta.xml \
  --test-records 200
```

---

## 3. Edge Case Checklist

Always test these scenarios:

| Edge Case | Test Scenario | What to Verify |
|-----------|---------------|----------------|
| **Null values** | Required field is null | Error handling activates, no crash |
| **Empty collections** | Get Records returns 0 | Loop skips gracefully, no null errors |
| **Max field lengths** | 255-char text, max picklist | No truncation errors |
| **Special characters** | `<>&"'` in text fields | No XML/formula breaks |
| **Unicode/Emoji** | International characters, emojis | Proper encoding maintained |
| **Date boundaries** | Year 2000, 2038, leap years | Date calculations work correctly |
| **Negative numbers** | -1, MIN_INT values | Math operations handle correctly |
| **Large numbers** | MAX_INT, currency limits | No overflow errors |
| **Blank strings** | Empty string vs null | Handled differently if expected |
| **Whitespace** | Leading/trailing spaces | Trimmed or preserved as designed |

### Creating Edge Case Test Data

```apex
// Edge case test data
Account edgeCaseAccount = new Account(
    Name = 'Test <Special> & "Characters"',           // Special chars
    Description = String.valueOf(Crypto.getRandomLong()),  // Max length test
    AnnualRevenue = -100                               // Negative number
);
```

---

## 4. User Context Testing

Test with multiple user profiles to verify security.

### Minimum Test Profiles

| Profile | Purpose | What to Verify |
|---------|---------|----------------|
| **System Administrator** | Full access baseline | All features work |
| **Standard User** | Limited permissions | FLS/CRUD enforced |
| **Custom Profile** | Business-specific restrictions | Custom permissions work |
| **Community User** (if applicable) | External access | Portal restrictions apply |

### What to Verify

- **Field-Level Security (FLS)**: Restricted fields not visible
- **Record sharing rules**: Access limited to owned/shared records
- **Custom permissions**: `$Permission` global variable works
- **System mode vs User mode**: Behaves as designed

### Testing with Different Users

**CLI Approach**:
```bash
# Authenticate as different user (sf org login user does not exist)
sf org login web --alias standard-user-org
# Note: To test as different users, authenticate separate orgs or use sf org login jwt with per-user credentials

# Run tests/verify behavior
```

**Apex Test Approach**:
```apex
@isTest
static void testAsStandardUser() {
    User standardUser = [SELECT Id FROM User WHERE Profile.Name = 'Standard User' LIMIT 1];

    System.runAs(standardUser) {
        // Test flow behavior as this user
        // Verify FLS/CRUD restrictions
    }
}
```

### User Mode Flow Testing

For flows running in User Mode, verify:
- Users cannot access records they don't have permission to
- Field-level security is enforced
- Sharing rules are respected

### System Mode Flow Testing

For flows running in System Mode:
- Document justification for bypassing security
- Verify flow doesn't expose sensitive data inappropriately
- Test that security-sensitive operations are logged

---

<a id="5-flow-type-specific-testing"></a>

## 5. Flow Type-Specific Testing

### Screen Flows

**Launch Methods**:
- Setup → Flows → Run
- Direct URL: `https://[org].lightning.force.com/flow/[FlowApiName]`
- Embedded in Lightning page

**Test Checklist**:
- [ ] All navigation paths (Next/Previous/Finish)
- [ ] Input validation on each screen
- [ ] Conditional field visibility
- [ ] Multiple user profiles
- [ ] Error messages display correctly
- [ ] Progress indicator updates (if multi-step)
- [ ] Back button behavior (data preserved or re-queried)

### Record-Triggered Flows

**CRITICAL**: Always bulk test with 200+ records.

**Test Checklist**:
- [ ] Create single test record - verify trigger fires
- [ ] Bulk test via Data Loader (200+ records)
- [ ] Entry conditions work correctly
- [ ] Before-save vs After-save timing correct
- [ ] `$Record` and `$Record__Prior` values correct
- [ ] Re-entry prevention working (if applicable)

**Query Recent Executions**:
```bash
sf data query --query "SELECT Id, Status, CreatedDate FROM FlowInterview WHERE FlowDeveloperName='[FlowName]' ORDER BY CreatedDate DESC LIMIT 10" --target-org [org]
```

### Autolaunched Flows

**Test via Apex**:
```apex
Map<String, Object> inputs = new Map<String, Object>{
    'inputRecordId' => testRecord.Id,
    'inputAmount' => 1000
};

Flow.Interview.My_Autolaunched_Flow flow = new Flow.Interview.My_Autolaunched_Flow(inputs);
flow.start();

// Get output variables
String result = (String) flow.getVariableValue('outputResult');
System.assertEquals('Success', result);
```

**Test Checklist**:
- [ ] Input variable mapping correct
- [ ] Output variable values correct
- [ ] Edge cases: nulls, empty collections, max values
- [ ] Bulkification test (200+ records)
- [ ] Governor limits not exceeded

### Scheduled Flows

**Test Checklist**:
- [ ] Verify schedule configuration in Setup → Scheduled Jobs
- [ ] Manual "Run" test first (before enabling schedule)
- [ ] Monitor Debug Logs during execution
- [ ] Batch processing works correctly
- [ ] Verify record selection criteria
- [ ] Test with empty result set (no records match)
- [ ] Cleanup/completion logic works

**Verify Schedule**:
```bash
sf data query --query "SELECT Id, CronJobDetail.Name, State, NextFireTime FROM CronTrigger WHERE CronJobDetail.Name LIKE '%[FlowName]%'" --target-org [org]
```

### Platform Event-Triggered Flows

**Publish Test Event**:
```apex
// Publish event
My_Event__e event = new My_Event__e(
    Record_Id__c = testRecord.Id,
    Action__c = 'CREATE'
);
Database.SaveResult sr = EventBus.publish(event);
System.assert(sr.isSuccess());
```

**Test Checklist**:
- [ ] Flow triggers on event publication
- [ ] Event data accessible via `$Record`
- [ ] High-volume scenarios work (multiple events)
- [ ] Order of processing correct
- [ ] Error handling works for failed events

---

## 6. Deployment Testing Sequence

Follow this 5-step deployment validation:

| Step | Action | Tool/Method | Success Criteria |
|------|--------|-------------|------------------|
| 1 | Validate XML structure | Flow validator scripts | No errors |
| 2 | Deploy with checkOnly=true | `sf project deploy start --dry-run` | Deployment succeeds |
| 3 | Verify package.xml | Manual review | API version matches flow |
| 4 | Test with minimal data | 1-5 records in sandbox | Basic functionality works |
| 5 | Test with bulk data | 200+ records in sandbox | Governor limits OK |

### Dry-Run Deployment

```bash
# Validate without deploying
sf project deploy start --source-dir force-app --dry-run --target-org sandbox

# Check deployment status
sf project deploy report --target-org sandbox
```

### Package.xml Verification

Ensure API version matches:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>My_Flow</members>
        <name>Flow</name>
    </types>
    <version>66.0</version>  <!-- Must match flow's apiVersion -->
</Package>
```

---

## 7. Regression Testing

### Document Test Cases

Maintain a test case document for each flow:

| Field | Description |
|-------|-------------|
| Test Case ID | Unique identifier (TC-001) |
| Description | What this test verifies |
| Pre-conditions | Required setup before test |
| Steps | Numbered steps to execute |
| Expected Result | What should happen |
| Last Tested | Date and version |

### After Every Change

Re-run **ALL** test cases, not just changed paths:
- Logic changes can have cascading effects
- Decision criteria changes affect multiple branches
- Variable changes impact downstream elements

### Integration Testing

Test interactions with:
- **Other flows** on the same object (trigger order)
- **Process Builders** (legacy - if still active)
- **Apex triggers** (execution order matters)
- **Validation rules** (may block flow DML)
- **Workflow rules** (legacy - field updates)
- **External integrations** (API calls, platform events)

### Automated Regression Testing

Consider creating Apex test classes that:
- Invoke flows programmatically
- Assert expected outcomes
- Run as part of CI/CD pipeline

```apex
@isTest
static void testFlowRegressionSuite() {
    // Setup test data
    Account testAccount = new Account(Name = 'Test');
    insert testAccount;

    // Invoke flow
    Map<String, Object> inputs = new Map<String, Object>{
        'recordId' => testAccount.Id
    };
    Flow.Interview.My_Flow flow = new Flow.Interview.My_Flow(inputs);
    flow.start();

    // Assert expected outcomes
    testAccount = [SELECT Status__c FROM Account WHERE Id = :testAccount.Id];
    System.assertEquals('Processed', testAccount.Status__c);
}
```

---

## 8. Governor Limits Testing

### Limit Thresholds

| Limit | Value | Warning Threshold |
|-------|-------|-------------------|
| SOQL Queries | 100 | 80 |
| DML Statements | 150 | 120 |
| Records Retrieved | 50,000 | 40,000 |
| DML Rows | 10,000 | 8,000 |
| CPU Time | 10,000 ms | 8,000 ms |
| Heap Size | 6 MB | 5 MB |

### Monitoring During Tests

**Debug Log Analysis**:
1. Enable debug logs for running user
2. Execute flow
3. Review logs for `LIMIT_USAGE_FOR_NS`

**Key Log Entries**:
```
LIMIT_USAGE_FOR_NS|namespace||SOQL queries|15/100
LIMIT_USAGE_FOR_NS|namespace||DML statements|5/150
LIMIT_USAGE_FOR_NS|namespace||CPU time|1234/10000
```

### Governor Limit Prevention

If approaching limits:
- **SOQL**: Consolidate queries, add filters
- **DML**: Batch operations, reduce elements
- **CPU**: Simplify formulas, reduce loops
- **Heap**: Process in smaller batches

---

<a id="9-post-deployment-verification"></a>

## 9. Post-Deployment Verification

### Immediate Checks (Within 1 Hour)

1. **Check Flow Status**: Setup → Process Automation → Flows
   - Verify flow is Active (if intended)
   - Verify correct version is active

2. **Review Debug Logs**: Developer Console → Debug Logs
   - Check for unexpected errors
   - Verify expected execution paths

3. **Monitor Flow Interviews**: Setup → Process Automation → Paused Flow Interviews
   - No unexpected paused interviews

4. **Check Errors**: Setup → Process Automation → Flow Errors
   - No new errors from the deployed flow

### Short-Term Monitoring (First 24-48 Hours)

- Monitor for user-reported issues
- Check batch job completions (scheduled flows)
- Review error email notifications
- Verify integrations still working

### Query Flow Errors

```bash
sf data query --query "SELECT Id, ElementApiName, ErrorMessage, FlowVersionId, InterviewGuid FROM FlowInterviewLogEntry WHERE CreatedDate = TODAY ORDER BY CreatedDate DESC LIMIT 20" --target-org [org]
```

---

## Quick Reference Commands

```bash
# Deploy and test
sf project deploy start --source-dir force-app --target-org sandbox

# Query flow interviews
sf data query --query "SELECT Id, Status FROM FlowInterview WHERE FlowDeveloperName='MyFlow' LIMIT 10" --target-org sandbox

# Check scheduled jobs
sf data query --query "SELECT Id, CronJobDetail.Name, State, NextFireTime FROM CronTrigger" --target-org sandbox

# Authenticate as different user (sf org login user does not exist)
sf org login web --alias test-user-org
# Note: To test as different users, authenticate separate orgs or use sf org login jwt
```

---

## Flow Test CLI Commands

### Run Flow Tests

> `sf flow run test` is a first-class CLI command for running Flow tests (available in sf CLI v2.122.6+).

```bash
# Run all Flow tests
sf flow run test -o TARGET_ORG --json

# Run with code coverage
sf flow run test -o TARGET_ORG --code-coverage --json

# Run specific test classes
sf flow run test --class-names MyFlowTest -o TARGET_ORG --json

# Synchronous execution (waits for completion)
sf flow run test -o TARGET_ORG --synchronous --json
```

### Combined Apex + Flow Test Runner

> `sf logic run test` runs both Apex and Flow tests in a single command — useful for comprehensive CI/CD test suites.

```bash
# Run combined Apex + Flow tests
sf logic run test -o TARGET_ORG --json

# Check results
sf logic get test --test-run-id <id> -o TARGET_ORG --json
```

---

## Related Documentation

- [Flow Best Practices](./flow-best-practices.md) - Design patterns and standards
- [Testing Checklist](./testing-checklist.md) - Quick reference checklist
- [Governance Checklist](./governance-checklist.md) - Security and compliance
