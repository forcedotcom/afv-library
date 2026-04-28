<!-- Parent: sf-apex/SKILL.md -->
# Apex Best Practices Reference

## 1. Bulkification

### The Problem
Apex triggers can process up to 200 records at once. Code that works for single records often fails at scale.

### Anti-Pattern
```apex
// BAD: SOQL in loop - will hit 100 query limit
for (Account acc : Trigger.new) {
    Contact c = [SELECT Id FROM Contact WHERE AccountId = :acc.Id LIMIT 1];
}
```

### Best Practice
```apex
// GOOD: Query once, use Map for lookup
Set<Id> accountIds = new Map<Id, Account>(Trigger.new).keySet();
Map<Id, Contact> contactsByAccountId = new Map<Id, Contact>();
for (Contact c : [SELECT Id, AccountId FROM Contact WHERE AccountId IN :accountIds]) {
    contactsByAccountId.put(c.AccountId, c);
}

for (Account acc : Trigger.new) {
    Contact c = contactsByAccountId.get(acc.Id);
}
```

### DML Bulkification
```apex
// BAD: DML in loop
for (Account acc : accounts) {
    acc.Status__c = 'Active';
    update acc;
}

// GOOD: Collect and update once
List<Account> toUpdate = new List<Account>();
for (Account acc : accounts) {
    acc.Status__c = 'Active';
    toUpdate.add(acc);
}
update toUpdate;
```

### Test with Bulk Data
```apex
@isTest
static void testBulkOperation() {
    List<Account> accounts = new List<Account>();
    for (Integer i = 0; i < 251; i++) {  // 251 to span two trigger batches
        accounts.add(new Account(Name = 'Test ' + i));
    }

    Test.startTest();
    insert accounts;
    Test.stopTest();

    Assert.areEqual(251, [SELECT COUNT() FROM Account]);
}
```

---

## 2. Collections Best Practices

### Use Map Constructor for ID Extraction
```apex
// BAD: Loop to get IDs
Set<Id> accountIds = new Set<Id>();
for (Account acc : accounts) {
    accountIds.add(acc.Id);
}

// GOOD: Map constructor
Set<Id> accountIds = new Map<Id, Account>(accounts).keySet();
```

### Use Maps for Lookups
```apex
// Build lookup map
Map<Id, Account> accountsById = new Map<Id, Account>(accounts);

// O(1) lookup instead of O(n) loop
Account acc = accountsById.get(someId);
```

### Collection Naming Convention
```apex
List<Account> accounts;              // Plural noun
Set<Id> accountIds;                  // Type suffix
Map<Id, Account> accountsById;       // Key description
Map<String, List<Contact>> contactsByEmail;  // Nested collection
```

---

## 3. SOQL Best Practices

### Always Use Selective Queries
```apex
// GOOD: Filter on indexed fields
[SELECT Id FROM Account WHERE Id = :recordId]
[SELECT Id FROM Account WHERE Name = :name]
[SELECT Id FROM Account WHERE CreatedDate > :startDate]
[SELECT Id FROM Contact WHERE Email = :email]  // If External ID

// BAD: Non-selective patterns
[SELECT Id FROM Account WHERE Custom_Field__c != null]  // != null
[SELECT Id FROM Account WHERE Name LIKE '%test%']       // Leading wildcard
[SELECT Id FROM Account WHERE CALENDAR_YEAR(CreatedDate) = 2025]  // Function
```

### Use Bind Variables (Prevent SOQL Injection)
```apex
// BAD: String concatenation (SOQL injection risk)
String query = 'SELECT Id FROM Account WHERE Name = \'' + userInput + '\'';

// GOOD: Bind variable
String query = 'SELECT Id FROM Account WHERE Name = :userInput';
List<Account> accounts = Database.query(query);
```

### Use USER_MODE for Security
```apex
// Enforces CRUD/FLS automatically
List<Account> accounts = [SELECT Id, Name FROM Account WITH USER_MODE];

// For Database methods
Database.query(query, AccessLevel.USER_MODE);
Database.insert(records, AccessLevel.USER_MODE);
```

### SOQL For Loops for Large Data
```apex
// Memory efficient - processes 200 records at a time
for (Account acc : [SELECT Id, Name FROM Account]) {
    // Process each account
}

// Or batch processing
for (List<Account> batch : [SELECT Id, Name FROM Account]) {
    // Process batch of 200
}
```

---

## 4. Governor Limits Awareness

### Key Limits
| Limit | Synchronous | Asynchronous |
|-------|-------------|--------------|
| SOQL Queries | 100 | 200 |
| DML Statements | 150 | 150 |
| CPU Time | 10,000 ms | 60,000 ms |
| Heap Size | 6 MB | 12 MB |
| Callouts | 100 | 100 |

### Monitor Limits
```apex
System.debug('SOQL: ' + Limits.getQueries() + '/' + Limits.getLimitQueries());
System.debug('DML: ' + Limits.getDmlStatements() + '/' + Limits.getLimitDmlStatements());
System.debug('CPU: ' + Limits.getCpuTime() + '/' + Limits.getLimitCpuTime());
System.debug('Heap: ' + Limits.getHeapSize() + '/' + Limits.getLimitHeapSize());
```

### Heap Optimization
```apex
// BAD: Class-level variable holds large data
public class BadExample {
    private List<Account> allAccounts;  // Stays in memory
}

// GOOD: Let variables go out of scope
public class GoodExample {
    public void process() {
        List<Account> accounts = [SELECT Id FROM Account];
        // Process...
    }  // accounts released here
}
```

---

## 5. Null Safety

### Null Coalescing Operator (??)
```apex
// Old way
String value = input != null ? input : 'default';

// New way (API 60+)
String value = input ?? 'default';

// Chaining
String value = firstChoice ?? secondChoice ?? 'default';
```

### Safe Navigation Operator (?.)
```apex
// Old way
String accountName = null;
if (contact != null && contact.Account != null) {
    accountName = contact.Account.Name;
}

// New way
String accountName = contact?.Account?.Name;

// With null coalescing
String accountName = contact?.Account?.Name ?? 'Unknown';
```

### Null-Safe Collection Access
```apex
// Check before accessing
if (myMap != null && myMap.containsKey(key)) {
    return myMap.get(key);
}

// Or use getOrDefault pattern
public static Object getOrDefault(Map<Id, Object> m, Id key, Object defaultVal) {
    return m?.containsKey(key) == true ? m.get(key) : defaultVal;
}
```

---

## 6. Error Handling

### Catch Specific Exceptions
```apex
try {
    insert accounts;
} catch (DmlException e) {
    // Handle DML-specific errors
    for (Integer i = 0; i < e.getNumDml(); i++) {
        System.debug('Field: ' + e.getDmlFieldNames(i));
        System.debug('Message: ' + e.getDmlMessage(i));
    }
} catch (QueryException e) {
    // Handle query errors
} catch (Exception e) {
    // Generic fallback - log and rethrow
    System.debug(LoggingLevel.ERROR, e.getMessage());
    throw e;
}
```

### Custom Exceptions
```apex
public class InsufficientInventoryException extends Exception {}

public void processOrder(Order ord) {
    if (ord.Quantity__c > availableStock) {
        throw new InsufficientInventoryException(
            'Requested: ' + ord.Quantity__c + ', Available: ' + availableStock
        );
    }
}
```

### AuraHandledException for LWC
```apex
@AuraEnabled
public static void processRecord(Id recordId) {
    try {
        // Business logic
    } catch (Exception e) {
        throw new AuraHandledException(e.getMessage());
    }
}
```

---

## 7. Async Apex Selection

### @future
```apex
// Simple, fire-and-forget
@future(callout=true)
public static void makeCallout(Set<Id> recordIds) {
    // Cannot return value, cannot chain
}
```

### Queueable
```apex
// Complex logic, can chain, can pass complex types
public class ProcessRecordsQueueable implements Queueable {
    private List<Account> accounts;

    public ProcessRecordsQueueable(List<Account> accounts) {
        this.accounts = accounts;
    }

    public void execute(QueueableContext context) {
        // Process accounts

        // Chain next job if needed
        if (moreWork) {
            System.enqueueJob(new ProcessRecordsQueueable(nextBatch));
        }
    }
}
```

### Batch Apex
```apex
// Large data volumes (millions of records)
public class ProcessAccountsBatch implements Database.Batchable<SObject> {
    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator('SELECT Id FROM Account');
    }

    public void execute(Database.BatchableContext bc, List<Account> scope) {
        // Process batch (default 200 records)
    }

    public void finish(Database.BatchableContext bc) {
        // Cleanup, notifications, chain next batch
    }
}
```

---

## 8. Platform Cache

### When to Use
- Frequently accessed, rarely changed data
- Expensive calculations
- Cross-transaction data sharing

### Implementation
```apex
// Check cache first
Account acc = (Account)Cache.Org.get('local.AccountCache.' + accountId);
if (acc == null) {
    acc = [SELECT Id, Name FROM Account WHERE Id = :accountId];
    Cache.Org.put('local.AccountCache.' + accountId, acc, 3600);  // 1 hour TTL
}
return acc;
```

### Always Handle Cache Misses
```apex
// Cache can be evicted at any time
Object cachedValue = Cache.Org.get(key);
if (cachedValue == null) {
    // Rebuild from source
}
```

---

## 9. Static Variables for Transaction Caching

### Prevent Duplicate Queries
```apex
public class AccountService {
    private static Map<Id, Account> accountCache;

    public static Account getAccount(Id accountId) {
        if (accountCache == null) {
            accountCache = new Map<Id, Account>();
        }

        if (!accountCache.containsKey(accountId)) {
            accountCache.put(accountId, [SELECT Id, Name FROM Account WHERE Id = :accountId]);
        }

        return accountCache.get(accountId);
    }
}
```

### Recursion Prevention
```apex
public class TriggerHelper {
    private static Set<Id> processedIds = new Set<Id>();

    public static Boolean hasProcessed(Id recordId) {
        if (processedIds.contains(recordId)) {
            return true;
        }
        processedIds.add(recordId);
        return false;
    }
}
```

---

<a id="10-guard-clauses--fail-fast"></a>

## 10. Guard Clauses & Fail-Fast

> 💡 *Principles inspired by "Clean Apex Code" by Pablo Gonzalez.
> [Purchase the book](https://link.springer.com/book/10.1007/979-8-8688-1411-2) for complete coverage.*

### The Problem

Deeply nested validation leads to hard-to-read code where business logic is buried.

### Anti-Pattern
```apex
// BAD: Deep nesting obscures business logic
public void processAccountUpdate(Account oldAccount, Account newAccount) {
    if (newAccount != null) {
        if (oldAccount != null) {
            if (newAccount.Id != null) {
                if (hasFieldChanged(oldAccount, newAccount)) {
                    if (UserInfo.getUserType() == 'Standard') {
                        // Actual business logic buried 5 levels deep
                        performSync(newAccount);
                        sendNotification(newAccount);
                    }
                }
            }
        }
    }
}
```

### Best Practice: Guard Clauses
```apex
// GOOD: Guard clauses at the top, exit early
public void processAccountUpdate(Account oldAccount, Account newAccount) {
    // Guard clauses - validate preconditions and exit fast
    if (newAccount == null) return;
    if (oldAccount == null) return;
    if (newAccount.Id == null) return;
    if (!hasFieldChanged(oldAccount, newAccount)) return;
    if (UserInfo.getUserType() != 'Standard') return;

    // Main logic is now at the top level, clearly visible
    performSync(newAccount);
    sendNotification(newAccount);
}
```

### Parameter Validation with Exceptions

For public APIs, throw exceptions for invalid input:

```apex
public Database.LeadConvertResult convertLead(Id leadId, Id accountId) {
    // Guard clauses with exceptions for public API
    if (leadId == null) {
        throw new IllegalArgumentException('Lead ID cannot be null');
    }

    if (leadId.getSObjectType() != Lead.SObjectType) {
        throw new IllegalArgumentException('Expected Lead ID, received: ' + leadId.getSObjectType());
    }

    Lead leadRecord = queryLead(leadId);

    if (leadRecord == null) {
        throw new IllegalArgumentException('Lead not found: ' + leadId);
    }

    if (leadRecord.IsConverted) {
        throw new IllegalArgumentException('Lead is already converted: ' + leadId);
    }

    // Main conversion logic
    return performConversion(leadRecord, accountId);
}
```

### When to Use Each Pattern

| Scenario | Pattern | Example |
|----------|---------|---------|
| Private/internal methods | `return` early | `if (list == null) return;` |
| Public API | `throw Exception` | `throw new IllegalArgumentException(...)` |
| Trigger handlers | `return` for skip | `if (records.isEmpty()) return;` |
| Validation service | `addError()` | `record.addError('...')` |

---

## 11. Comment Best Practices

> 💡 *Principles inspired by "Clean Apex Code" by Pablo Gonzalez.
> [Purchase the book](https://link.springer.com/book/10.1007/979-8-8688-1411-2) for complete coverage.*

### Core Principle

Comments should explain **"why"**, not **"what"**. The code itself should communicate the "what".

### When Comments Add Value

```apex
// GOOD: Explains business decision
// Salesforce processes triggers in batches of 200. We use 201 to ensure
// our code handles batch boundaries correctly during testing.
private static final Integer BULK_TEST_SIZE = 201;

// GOOD: Documents platform limitation
// Safe navigation (?.) doesn't work in formulas - must use IF(ISBLANK())
// See Known Issue W-12345678

// GOOD: References external documentation
// Algorithm based on RFC 7519 (JSON Web Token specification)
// See: https://tools.ietf.org/html/rfc7519#section-4.1

// GOOD: Explains non-obvious optimization
// SOQL query in a loop replaced with map-based lookup — O(1) per record.
Account acc = accountsByExternalId.get(record.ExternalId__c);
```

### Comment Anti-Patterns

```apex
// BAD: Restates what code clearly shows
Integer count = 0;  // Initialize count to zero

// BAD: Version history belongs in Git
// Modified by John on 2024-01-15 to add validation
// Modified by Jane on 2024-02-20 to fix bug

// BAD: Commented-out code (delete it!)
// if (account.Type == 'Partner') {
//     processPartner(account);
// }

// BAD: TODO without owner or ticket
// TODO: fix this later

// GOOD: TODO with context
// TODO(JIRA-1234): Refactor to use Platform Events after Spring '26 release
```

### Self-Documenting Code

Instead of comments, make code self-explanatory:

```apex
// BAD: Needs comment to explain
if (acc.AnnualRevenue > 1000000 && acc.Type == 'Enterprise' && acc.Industry == 'Technology') {
    // Process strategic tech accounts
}

// GOOD: Code explains itself
Boolean isStrategicTechAccount =
    acc.AnnualRevenue > 1000000 &&
    acc.Type == 'Enterprise' &&
    acc.Industry == 'Technology';

if (isStrategicTechAccount) {
    processStrategicAccount(acc);
}
```
