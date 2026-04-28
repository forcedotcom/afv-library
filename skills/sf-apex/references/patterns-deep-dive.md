<!-- Parent: sf-apex/SKILL.md -->
# Apex Patterns Deep Dive

Comprehensive guide to advanced Apex patterns including Trigger Actions Framework, Flow Integration, and architectural patterns.

---

## Table of Contents

1. [Trigger Actions Framework (TAF)](#trigger-actions-framework-taf)
2. [Flow Integration (@InvocableMethod)](#flow-integration-invocablemethod)
3. [Async Patterns](#async-patterns)
4. [Service Layer Patterns](#service-layer-patterns)

---

## Trigger Actions Framework (TAF)

### ⚠️ CRITICAL PREREQUISITES

**Before using TAF patterns, the target org MUST have:**

1. **Trigger Actions Framework Package Installed**
   - GitHub: https://github.com/mitchspano/apex-trigger-actions-framework
   - Install via: `sf package install --package 04tKZ000000gUEFYA2 --target-org [alias] --wait 10`
   - Or use unlocked package from repository

2. **Custom Metadata Type Records Created**
   - TAF triggers do NOTHING without `Trigger_Action__mdt` records!
   - Each trigger action class needs a corresponding CMT record

**If TAF is NOT installed, use the Standard Trigger Pattern instead.**

---

### TAF Pattern (Requires Package)

All triggers MUST use the Trigger Actions Framework pattern when the package is installed:

**Trigger** (one per object):
```apex
trigger AccountTrigger on Account (
    before insert, after insert,
    before update, after update,
    before delete, after delete, after undelete
) {
    new MetadataTriggerHandler().run();
}
```

**Single-Context Action Class** (one interface):
```apex
public class TA_Account_SetDefaults implements TriggerAction.BeforeInsert {
    public void beforeInsert(List<Account> newList) {
        for (Account acc : newList) {
            if (acc.Industry == null) {
                acc.Industry = 'Other';
            }
        }
    }
}
```

**Multi-Context Action Class** (multiple interfaces):
```apex
public class TA_Lead_CalculateScore implements TriggerAction.BeforeInsert, TriggerAction.BeforeUpdate {

    // Called on new record creation
    public void beforeInsert(List<Lead> newList) {
        calculateScores(newList);
    }

    // Called on record updates
    public void beforeUpdate(List<Lead> newList, List<Lead> oldList) {
        // Only recalculate if scoring fields changed
        List<Lead> leadsToScore = new List<Lead>();
        Map<Id, Lead> oldMap = new Map<Id, Lead>(oldList);

        for (Lead newLead : newList) {
            Lead oldLead = oldMap.get(newLead.Id);
            if (scoringFieldsChanged(newLead, oldLead)) {
                leadsToScore.add(newLead);
            }
        }

        if (!leadsToScore.isEmpty()) {
            calculateScores(leadsToScore);
        }
    }

    private void calculateScores(List<Lead> leads) {
        // Scoring logic here
        for (Lead l : leads) {
            Integer score = 0;
            if (l.Industry == 'Technology') score += 10;
            if (l.NumberOfEmployees != null && l.NumberOfEmployees > 100) score += 20;
            l.Score__c = score;
        }
    }

    private Boolean scoringFieldsChanged(Lead newLead, Lead oldLead) {
        return newLead.Industry != oldLead.Industry ||
               newLead.NumberOfEmployees != oldLead.NumberOfEmployees;
    }
}
```

---

### ⚠️ REQUIRED: Custom Metadata Type Records

**TAF triggers will NOT execute without `Trigger_Action__mdt` records!**

For each trigger action class, create a Custom Metadata record:

| Field | Value | Description |
|-------|-------|-------------|
| Label | TA Lead Calculate Score | Human-readable name |
| Trigger_Action_Name__c | TA_Lead_CalculateScore | Apex class name |
| Object__c | Lead | sObject API name |
| Context__c | Before Insert | Trigger context |
| Order__c | 1 | Execution order (lower = first) |
| Active__c | true | Enable/disable without deploy |

**Example Custom Metadata XML** (`Trigger_Action.TA_Lead_CalculateScore_BI.md-meta.xml`):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>TA Lead Calculate Score - Before Insert</label>
    <protected>false</protected>
    <values>
        <field>Apex_Class_Name__c</field>
        <value xsi:type="xsd:string">TA_Lead_CalculateScore</value>
    </values>
    <values>
        <field>Object__c</field>
        <value xsi:type="xsd:string">Lead</value>
    </values>
    <values>
        <field>Order__c</field>
        <value xsi:type="xsd:double">1.0</value>
    </values>
    <values>
        <field>Bypass_Execution__c</field>
        <value xsi:type="xsd:boolean">false</value>
    </values>
</CustomMetadata>
```

**NOTE**: Create separate CMT records for each context (Before Insert, Before Update, etc.)

**Deploy Custom Metadata:**
```bash
sf project deploy start --metadata CustomMetadata:Trigger_Action.TA_Lead_CalculateScore_BI --target-org myorg
```

---

<a id="standard-trigger-pattern"></a>

### Standard Trigger Pattern (No Package Required)

**Use this when TAF package is NOT installed in the target org:**

```apex
trigger LeadTrigger on Lead (before insert, before update) {

    LeadScoringService scoringService = new LeadScoringService();

    if (Trigger.isBefore) {
        if (Trigger.isInsert) {
            scoringService.calculateScores(Trigger.new);
        }
        else if (Trigger.isUpdate) {
            scoringService.recalculateIfChanged(Trigger.new, Trigger.oldMap);
        }
    }
}
```

**Service Class:**
```apex
public with sharing class LeadScoringService {

    public void calculateScores(List<Lead> leads) {
        for (Lead l : leads) {
            Integer score = 0;
            if (l.Industry == 'Technology') score += 10;
            if (l.NumberOfEmployees != null && l.NumberOfEmployees > 100) score += 20;
            l.Score__c = score;
        }
    }

    public void recalculateIfChanged(List<Lead> newLeads, Map<Id, Lead> oldMap) {
        List<Lead> leadsToScore = new List<Lead>();

        for (Lead newLead : newLeads) {
            Lead oldLead = oldMap.get(newLead.Id);
            if (scoringFieldsChanged(newLead, oldLead)) {
                leadsToScore.add(newLead);
            }
        }

        if (!leadsToScore.isEmpty()) {
            calculateScores(leadsToScore);
        }
    }

    private Boolean scoringFieldsChanged(Lead newLead, Lead oldLead) {
        return newLead.Industry != oldLead.Industry ||
               newLead.NumberOfEmployees != oldLead.NumberOfEmployees;
    }
}
```

**Pros**: No external dependencies, works in any org
**Cons**: Less maintainable for complex triggers, no declarative control

---

### TAF vs Standard Pattern Comparison

| Feature | TAF Pattern | Standard Pattern |
|---------|-------------|------------------|
| **Package Required** | Yes | No |
| **Complexity** | Lower (single-purpose classes) | Higher (monolithic trigger) |
| **Maintainability** | High (separate files) | Medium (one trigger file) |
| **Declarative Control** | Yes (CMT records) | No |
| **Order Control** | Yes (Order__c field) | Manual in code |
| **Bypass Mechanism** | Built-in (Active__c) | Manual Custom Setting |
| **Testing** | Easy (test action classes) | Medium (test trigger + service) |

**Recommendation**: Use TAF when available, fall back to Standard Pattern when TAF is not installed.

---

## Flow Integration (@InvocableMethod)

Apex classes can be called from Flow using `@InvocableMethod`. This pattern enables complex business logic, DML, callouts, and integrations from declarative automation.

### Quick Reference

| Annotation | Purpose |
|------------|---------|
| `@InvocableMethod` | Makes method callable from Flow |
| `@InvocableVariable` | Exposes properties in Request/Response wrappers |

### Template

Use `assets/invocable-method.cls` for the complete pattern with Request/Response wrappers.

### Basic Example

```apex
public with sharing class RecordProcessor {

    @InvocableMethod(label='Process Record' category='Custom')
    public static List<Response> execute(List<Request> requests) {
        List<Response> responses = new List<Response>();

        for (Request req : requests) {
            Response res = new Response();
            res.isSuccess = true;
            res.processedId = req.recordId;
            responses.add(res);
        }

        return responses;
    }

    public class Request {
        @InvocableVariable(label='Record ID' required=true)
        public Id recordId;
    }

    public class Response {
        @InvocableVariable(label='Is Success')
        public Boolean isSuccess;

        @InvocableVariable(label='Processed ID')
        public Id processedId;
    }
}
```

### Advanced Example with Error Handling

```apex
public with sharing class AccountValidator {

    @InvocableMethod(
        label='Validate Account Data'
        description='Validates account data and returns validation results'
        category='Account Management'
    )
    public static List<ValidationResponse> validateAccounts(List<ValidationRequest> requests) {
        List<ValidationResponse> responses = new List<ValidationResponse>();

        // Collect all Account IDs for bulk query
        Set<Id> accountIds = new Set<Id>();
        for (ValidationRequest req : requests) {
            accountIds.add(req.accountId);
        }

        // Bulk query
        Map<Id, Account> accountMap = new Map<Id, Account>(
            [SELECT Id, Name, Industry, AnnualRevenue, Phone
             FROM Account
             WHERE Id IN :accountIds
             WITH USER_MODE]
        );

        // Process each request
        for (ValidationRequest req : requests) {
            ValidationResponse res = new ValidationResponse();

            Account acc = accountMap.get(req.accountId);
            if (acc == null) {
                res.isValid = false;
                res.errorMessage = 'Account not found';
                responses.add(res);
                continue;
            }

            // Validation logic
            List<String> errors = new List<String>();

            if (String.isBlank(acc.Name)) {
                errors.add('Name is required');
            }
            if (String.isBlank(acc.Industry)) {
                errors.add('Industry is required');
            }
            if (acc.AnnualRevenue == null || acc.AnnualRevenue <= 0) {
                errors.add('Annual Revenue must be greater than 0');
            }

            res.isValid = errors.isEmpty();
            res.errorMessage = errors.isEmpty() ? null : String.join(errors, '; ');
            res.validatedAccountId = acc.Id;

            responses.add(res);
        }

        return responses;
    }

    public class ValidationRequest {
        @InvocableVariable(label='Account ID' description='ID of account to validate' required=true)
        public Id accountId;
    }

    public class ValidationResponse {
        @InvocableVariable(label='Is Valid' description='Whether account passed validation')
        public Boolean isValid;

        @InvocableVariable(label='Error Message' description='Validation error details')
        public String errorMessage;

        @InvocableVariable(label='Validated Account ID')
        public Id validatedAccountId;
    }
}
```

### Best Practices

1. **Always use Request/Response wrappers** - Never use primitive types directly
2. **Bulkify** - Process `List<Request>` even if Flow passes single record
3. **Use USER_MODE** - Respect user permissions in SOQL
4. **Error handling** - Return structured errors in Response, don't throw exceptions
5. **Label & Category** - Make methods discoverable in Flow Builder
6. **Description** - Add descriptions to variables for clarity

### Common Patterns

**Pattern 1: DML Operations**
```apex
@InvocableMethod(label='Create Related Contacts')
public static List<Response> createContacts(List<Request> requests) {
    List<Contact> contactsToInsert = new List<Contact>();

    for (Request req : requests) {
        Contact con = new Contact(
            AccountId = req.accountId,
            LastName = req.lastName,
            Email = req.email
        );
        contactsToInsert.add(con);
    }

    insert contactsToInsert;

    // Return results
    List<Response> responses = new List<Response>();
    for (Contact con : contactsToInsert) {
        Response res = new Response();
        res.contactId = con.Id;
        responses.add(res);
    }
    return responses;
}
```

**Pattern 2: External Callouts**
```apex
@InvocableMethod(label='Send to External System')
public static List<Response> sendData(List<Request> requests) {
    // Note: Callouts in Flow require @future or Queueable
    // This is a sync example - for async, enqueue from here

    List<Response> responses = new List<Response>();
    for (Request req : requests) {
        HttpRequest request = new HttpRequest();
        request.setEndpoint('callout:MyNamedCredential/api');
        request.setMethod('POST');
        request.setBody(JSON.serialize(req));

        Http http = new Http();
        HttpResponse response = http.send(request);

        Response res = new Response();
        res.statusCode = response.getStatusCode();
        res.success = response.getStatusCode() == 200;
        responses.add(res);
    }
    return responses;
}
```

**See Also**:
- [references/flow-integration.md](../references/flow-integration.md) - Complete @InvocableMethod guide
- [references/triangle-pattern.md](../references/triangle-pattern.md) - Flow-LWC-Apex triangle (Apex perspective)

---

## Async Patterns

### Decision Matrix

| Scenario | Use | Key Advantage | Daily Limit |
|----------|-----|---------------|-------------|
| Default async processing | **Queueable** (preferred) | Job ID, chaining, non-primitive types, delays, dedup | 250K or 200× licenses |
| Process millions of records | Batch Apex | Chunked, off-peak, max 5 concurrent threads | Same pool |
| Modern batch alternative | **CursorStep** (`Database.Cursor`) | 2000-record chunks, higher throughput | N/A |
| Scheduled/recurring job | **Scheduled Flow** (preferred) or Schedulable | Flow = deployable metadata; Apex = 100 job limit | — |
| Post-job cleanup | Queueable Finalizer (`System.Finalizer`) | Runs regardless of success/failure | — |
| Long-running Lightning callouts | `Continuation` | 3 per txn, 3 parallel | — |
| Legacy fire-and-forget | `@future` (legacy) | Simpler syntax only | Same pool |

> ⚠️ **Batch Apex max 5 simultaneous threads.** Additional batch jobs queue. Plan accordingly for time-sensitive processing.

> **Scheduled Flow preferred over Apex Schedulable** for most scheduling needs. Schedulable has a hard limit of 100 jobs. Use Schedulable only when chaining to Batch Apex or needing complex Apex-only logic.

> **For delays > 10 minutes** (Queueable max), use `System.scheduleBatch()` to schedule a Batch job at a specific time.

### Queueable Pattern (Preferred)

```apex
public class AccountProcessor implements Queueable {

    private List<Id> accountIds;

    public AccountProcessor(List<Id> accountIds) {
        this.accountIds = accountIds;
    }

    public void execute(QueueableContext context) {
        List<Account> accounts = [SELECT Id, Name, Industry FROM Account WHERE Id IN :accountIds];

        for (Account acc : accounts) {
            acc.Description = 'Processed on ' + System.now();
        }

        update accounts;

        // Chain another job if needed
        if (!Test.isRunningTest() && accountIds.size() > 200) {
            // Process next batch
            List<Id> nextBatch = getNextBatch();
            if (!nextBatch.isEmpty()) {
                System.enqueueJob(new AccountProcessor(nextBatch));
            }
        }
    }

    private List<Id> getNextBatch() {
        // Logic to get next batch
        return new List<Id>();
    }
}

// Usage:
System.enqueueJob(new AccountProcessor(accountIds));
```

### Queueable: Configurable Delay

Delay execution up to 10 minutes using `AsyncOptions`:

```apex
AccountProcessor job = new AccountProcessor(accountIds);
AsyncOptions options = new AsyncOptions();
options.setMinimumQueueableDelayInMinutes(10); // Max 10 min
System.enqueueJob(job, options);
```

### Queueable: Deduplication Signatures

Prevent duplicate jobs from being enqueued by assigning a dedup signature:

```apex
AccountProcessor job = new AccountProcessor(accountIds);
AsyncOptions options = new AsyncOptions();
options.setDuplicateSignature(QueueableDuplicateSignature.Builder()
    .addId(accountIds[0])
    .addString('AccountProcessor')
    .build());
System.enqueueJob(job, options);
// If another job with the same signature is already queued, this is silently ignored
```

### Queueable with Finalizer (System.Finalizer)

`System.Finalizer` acts as a blanket error handler — it executes regardless of whether the Queueable job succeeds or fails. Use it for logging, notifications, retry logic, and cleanup.

```apex
public class DataSyncQueueable implements Queueable {

    public void execute(QueueableContext context) {
        // Attach finalizer for cleanup
        System.attachFinalizer(new DataSyncFinalizer(context.getJobId()));

        // Main logic
        try {
            // Process data
            Http http = new Http();
            HttpRequest req = new HttpRequest();
            req.setEndpoint('callout:ExternalSystem/sync');
            req.setMethod('POST');

            HttpResponse res = http.send(req);

            if (res.getStatusCode() != 200) {
                throw new CalloutException('Sync failed: ' + res.getBody());
            }
        } catch (Exception e) {
            // Log error
            System.debug(LoggingLevel.ERROR, 'Sync failed: ' + e.getMessage());
            throw e; // Finalizer will still run
        }
    }
}

public class DataSyncFinalizer implements Finalizer {

    private Id jobId;

    public DataSyncFinalizer(Id jobId) {
        this.jobId = jobId;
    }

    public void execute(FinalizerContext context) {
        // This ALWAYS runs, even if job fails

        // Log status
        insert new Sync_Log__c(
            Job_Id__c = String.valueOf(jobId),
            Status__c = context.getResult() == ParentJobResult.SUCCESS ? 'Success' : 'Failed',
            Error__c = context.getException()?.getMessage()
        );
    }
}
```

### Batch Apex Pattern

```apex
public class AccountBatchProcessor implements Database.Batchable<SObject> {

    // Start: Define query
    public Database.QueryLocator start(Database.BatchableContext context) {
        return Database.getQueryLocator([
            SELECT Id, Name, Industry, AnnualRevenue
            FROM Account
            WHERE Industry = 'Technology'
        ]);
    }

    // Execute: Process each batch (default 200 records)
    public void execute(Database.BatchableContext context, List<Account> scope) {
        for (Account acc : scope) {
            acc.Description = 'Processed by batch on ' + System.now();
        }

        update scope;
    }

    // Finish: Post-processing
    public void finish(Database.BatchableContext context) {
        // Send email, log results, chain another batch
        AsyncApexJob job = [
            SELECT Id, Status, NumberOfErrors, JobItemsProcessed, TotalJobItems
            FROM AsyncApexJob
            WHERE Id = :context.getJobId()
        ];

        System.debug('Batch completed: ' + job.TotalJobItems + ' items processed');
    }
}

// Usage:
Database.executeBatch(new AccountBatchProcessor(), 200); // Batch size
```

### CursorStep Pattern (Database.Cursor)

Modern alternative to Batch Apex with higher throughput and 2000-record chunks:

```apex
public class AccountCursorStep implements Database.CursorStep {

    public Database.Cursor start() {
        return Database.getCursor(
            'SELECT Id, Name, Industry FROM Account WHERE Industry = \'Technology\''
        );
    }

    public void execute(Database.CursorStepContext context, List<SObject> scope) {
        List<Account> accounts = (List<Account>) scope;
        for (Account acc : accounts) {
            acc.Description = 'Processed via CursorStep on ' + System.now();
        }
        update accounts;
    }

    public void finish(Database.CursorStepContext context) {
        System.debug('CursorStep completed');
    }
}

// Usage:
Database.executeCursorStep(new AccountCursorStep());
```

> **CursorStep vs Batch**: CursorStep processes 2000 records per chunk (vs 200 default for Batch), doesn't count against the 5 simultaneous batch job limit, and has higher throughput. Use for new development when Batch Apex limits are a concern.

### @future Pattern (Legacy — Prefer Queueable)

> ⚠️ **Legacy pattern.** Prefer Queueable for new development. `@future` cannot return job IDs, cannot chain, cannot pass non-primitive types, and cannot use configurable delays or dedup signatures.

```apex
public class CalloutService {

    @future(callout=true)
    public static void sendDataToExternalSystem(Set<Id> recordIds) {
        // Cannot pass complex objects, only primitives
        List<Account> accounts = [SELECT Id, Name FROM Account WHERE Id IN :recordIds];

        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:MyNamedCredential/api');
        req.setMethod('POST');
        req.setBody(JSON.serialize(accounts));

        Http http = new Http();
        HttpResponse res = http.send(req);
        System.debug('Response: ' + res.getBody());
    }
}
```

---

## Service Layer Patterns

### Service Class Structure

```apex
public with sharing class AccountService {

    // Public interface methods
    public static List<Account> createAccounts(List<AccountRequest> requests) {
        validateRequests(requests);

        List<Account> accounts = buildAccounts(requests);
        insert accounts;

        // Post-processing
        handlePostCreation(accounts);

        return accounts;
    }

    // Private helper methods
    private static void validateRequests(List<AccountRequest> requests) {
        for (AccountRequest req : requests) {
            if (String.isBlank(req.name)) {
                throw new IllegalArgumentException('Account name is required');
            }
        }
    }

    private static List<Account> buildAccounts(List<AccountRequest> requests) {
        List<Account> accounts = new List<Account>();
        for (AccountRequest req : requests) {
            accounts.add(new Account(
                Name = req.name,
                Industry = req.industry
            ));
        }
        return accounts;
    }

    private static void handlePostCreation(List<Account> accounts) {
        // Create related records, send notifications, etc.
    }

    // Inner class for structured requests
    public class AccountRequest {
        public String name;
        public String industry;
    }
}
```

### Selector Pattern (Data Access Layer)

```apex
public inherited sharing class AccountSelector {

    public static List<Account> selectById(Set<Id> accountIds) {
        return [
            SELECT Id, Name, Industry, AnnualRevenue, Type
            FROM Account
            WHERE Id IN :accountIds
            WITH USER_MODE
        ];
    }

    public static List<Account> selectByIndustry(String industry) {
        return [
            SELECT Id, Name, Industry, AnnualRevenue
            FROM Account
            WHERE Industry = :industry
            WITH USER_MODE
            LIMIT 200
        ];
    }

    public static Map<Id, Account> selectByIdWithContacts(Set<Id> accountIds) {
        return new Map<Id, Account>([
            SELECT Id, Name,
                   (SELECT Id, Name, Email FROM Contacts)
            FROM Account
            WHERE Id IN :accountIds
            WITH USER_MODE
        ]);
    }
}
```

**Benefits**:
- Centralized SOQL queries
- Reusable across multiple classes
- Easier to test (mock Selector)
- Consistent field selection

---

## Reference

**Full Documentation**: See `references/` folder for comprehensive guides:
- `trigger-actions-framework.md` - TAF setup and advanced patterns
- `design-patterns.md` - 12 Apex design patterns
- `flow-integration.md` - Complete @InvocableMethod guide
- `triangle-pattern.md` - Flow-LWC-Apex integration

**Back to Main**: [SKILL.md](../SKILL.md)
