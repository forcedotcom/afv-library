<!-- Parent: sf-apex/SKILL.md -->
# Apex Bulkification Guide

Comprehensive guide to writing bulk-safe Apex code, understanding governor limits, and optimizing collection handling.

---

## Table of Contents

1. [Governor Limits Overview](#governor-limits-overview)
2. [The Golden Rules](#the-golden-rules)
3. [Common Bulkification Patterns](#common-bulkification-patterns)
4. [Collection Handling Best Practices](#collection-handling-best-practices)
5. [Monitoring and Debugging](#monitoring-and-debugging)
6. [Bulk Testing](#bulk-testing)

---

## Governor Limits Overview

Salesforce enforces per-transaction limits to ensure multi-tenant platform stability.

### Critical Limits (Synchronous Context)

| Resource | Limit | Notes |
|----------|-------|-------|
| **SOQL Queries** | 100 | Includes parent-child queries |
| **SOQL Query Rows** | 50,000 | Total rows retrieved |
| **DML Statements** | 150 | insert, update, delete, undelete operations |
| **DML Rows** | 10,000 | Total records per transaction |
| **CPU Time** | 10,000ms | Actual CPU time (not wall clock) |
| **Heap Size** | 6 MB | Memory used by variables |
| **Callouts** | 100 | HTTP requests |
| **Callout Time** | 120 seconds | Total time for all callouts |

### Asynchronous Limits (Future, Batch, Queueable)

| Resource | Limit | Notes |
|----------|-------|-------|
| **SOQL Queries** | 200 | Double synchronous |
| **SOQL Query Rows** | 50,000 | Same as sync |
| **DML Statements** | 150 | Same as sync |
| **DML Rows** | 10,000 | Same as sync |
| **CPU Time** | 60,000ms | 6x synchronous |
| **Heap Size** | 12 MB | 2x synchronous |

**Key Insight**: Async has more SOQL queries and CPU time, but DML limits are the same.

---

## The Golden Rules

### Rule 1: Never Query Inside a Loop

**❌ BAD - Hits SOQL limit at 100 accounts:**
```apex
for (Account acc : accounts) {
    List<Contact> contacts = [SELECT Id FROM Contact WHERE AccountId = :acc.Id];
    // Process contacts
}
```

**✅ GOOD - Single query handles unlimited accounts:**
```apex
// Step 1: Collect all Account IDs
Set<Id> accountIds = new Set<Id>();
for (Account acc : accounts) {
    accountIds.add(acc.Id);
}

// Step 2: Query ONCE
Map<Id, List<Contact>> contactsByAccountId = new Map<Id, List<Contact>>();
for (Contact con : [SELECT Id, AccountId FROM Contact WHERE AccountId IN :accountIds]) {
    if (!contactsByAccountId.containsKey(con.AccountId)) {
        contactsByAccountId.put(con.AccountId, new List<Contact>());
    }
    contactsByAccountId.get(con.AccountId).add(con);
}

// Step 3: Loop and process
for (Account acc : accounts) {
    List<Contact> contacts = contactsByAccountId.get(acc.Id);
    if (contacts != null) {
        // Process contacts
    }
}
```

**Pattern**: Collect IDs → Query with `IN` clause → Build Map → Loop.

---

### Rule 2: Never DML Inside a Loop

**❌ BAD - Hits DML limit at 150 accounts:**
```apex
for (Account acc : accounts) {
    acc.Industry = 'Technology';
    update acc;  // DML inside loop!
}
```

**✅ GOOD - Single DML handles 10,000 accounts:**
```apex
for (Account acc : accounts) {
    acc.Industry = 'Technology';
}
update accounts;  // DML after loop
```

**Pattern**: Modify in loop → DML after loop.

---

### Rule 3: Use Collections Efficiently

**❌ BAD - Multiple queries for related data:**
```apex
for (Account acc : accounts) {
    List<Contact> contacts = [SELECT Id FROM Contact WHERE AccountId = :acc.Id];
    List<Opportunity> opps = [SELECT Id FROM Opportunity WHERE AccountId = :acc.Id];
}
```

**✅ GOOD - Single query with subqueries:**
```apex
Map<Id, Account> accountsWithRelated = new Map<Id, Account>([
    SELECT Id, Name,
           (SELECT Id FROM Contacts),
           (SELECT Id FROM Opportunities)
    FROM Account
    WHERE Id IN :accountIds
]);

for (Account acc : accountsWithRelated.values()) {
    List<Contact> contacts = acc.Contacts;
    List<Opportunity> opps = acc.Opportunities;
}
```

**Pattern**: Use relationship queries to fetch related records in one SOQL.

---

## Common Bulkification Patterns

### Pattern 1: Map-Based Lookup

**Use Case**: Need to lookup related records for each item in a loop.

```apex
public static void updateAccountIndustry(List<Contact> contacts) {
    // Step 1: Collect Account IDs
    Set<Id> accountIds = new Set<Id>();
    for (Contact con : contacts) {
        if (con.AccountId != null) {
            accountIds.add(con.AccountId);
        }
    }

    // Step 2: Query Accounts into Map
    Map<Id, Account> accountMap = new Map<Id, Account>([
        SELECT Id, Industry
        FROM Account
        WHERE Id IN :accountIds
    ]);

    // Step 3: Loop and lookup
    for (Contact con : contacts) {
        Account acc = accountMap.get(con.AccountId);
        if (acc != null) {
            con.Description = 'Account Industry: ' + acc.Industry;
        }
    }

    update contacts;
}
```

**Key**: `Map<Id, SObject>` constructor automatically creates map from query results.

---

### Pattern 2: Grouping Related Records

**Use Case**: Process child records grouped by parent.

```apex
public static void processContactsByAccount(List<Contact> contacts) {
    // Group contacts by AccountId
    Map<Id, List<Contact>> contactsByAccount = new Map<Id, List<Contact>>();

    for (Contact con : contacts) {
        if (!contactsByAccount.containsKey(con.AccountId)) {
            contactsByAccount.put(con.AccountId, new List<Contact>());
        }
        contactsByAccount.get(con.AccountId).add(con);
    }

    // Process each group
    for (Id accountId : contactsByAccount.keySet()) {
        List<Contact> accountContacts = contactsByAccount.get(accountId);
        System.debug('Account ' + accountId + ' has ' + accountContacts.size() + ' contacts');
        // Process accountContacts
    }
}
```

**Alternative using Null Coalescing (API 59+):**
```apex
for (Contact con : contacts) {
    List<Contact> existing = contactsByAccount.get(con.AccountId);
    if (existing == null) {
        existing = new List<Contact>();
        contactsByAccount.put(con.AccountId, existing);
    }
    existing.add(con);
}
```

---

### Pattern 3: Aggregate Queries for Rollups

**Use Case**: Calculate rollup values (count, sum, avg) on related records.

```apex
public static void updateAccountContactCounts(Set<Id> accountIds) {
    // Query aggregate data
    Map<Id, Integer> contactCountsByAccount = new Map<Id, Integer>();

    for (AggregateResult ar : [
        SELECT AccountId, COUNT(Id) contactCount
        FROM Contact
        WHERE AccountId IN :accountIds
        GROUP BY AccountId
    ]) {
        Id accountId = (Id) ar.get('AccountId');
        Integer count = (Integer) ar.get('contactCount');
        contactCountsByAccount.put(accountId, count);
    }

    // Update accounts
    List<Account> accountsToUpdate = new List<Account>();
    for (Id accountId : accountIds) {
        Integer count = contactCountsByAccount.get(accountId) ?? 0;
        accountsToUpdate.add(new Account(
            Id = accountId,
            Number_of_Contacts__c = count
        ));
    }

    update accountsToUpdate;
}
```

**Why use aggregates**: More efficient than querying all records and counting in Apex.

---

### Pattern 4: Bulk Upsert with External ID

**Use Case**: Upserting records from external system.

```apex
public static void syncAccountsFromExternal(List<ExternalAccount> externalAccounts) {
    List<Account> accountsToUpsert = new List<Account>();

    for (ExternalAccount ext : externalAccounts) {
        accountsToUpsert.add(new Account(
            External_ID__c = ext.externalId,  // External ID field
            Name = ext.name,
            Industry = ext.industry
        ));
    }

    // Upsert by External ID field
    Database.upsert(accountsToUpsert, Account.External_ID__c, false);
}
```

**Key**: `Database.upsert()` with External ID field automatically matches and updates existing records.

---

### Pattern 5: Conditional DML (Only Update Changed Records)

**Use Case**: Avoid unnecessary DML on unchanged records.

```apex
public static void updateAccountsIfChanged(List<Account> accounts, Map<Id, Account> oldMap) {
    List<Account> accountsToUpdate = new List<Account>();

    for (Account newAcc : accounts) {
        Account oldAcc = oldMap.get(newAcc.Id);

        // Only update if specific fields changed
        if (newAcc.Industry != oldAcc.Industry || newAcc.Rating != oldAcc.Rating) {
            accountsToUpdate.add(newAcc);
        }
    }

    if (!accountsToUpdate.isEmpty()) {
        update accountsToUpdate;
    }
}
```

**Benefit**: Reduces DML statements and CPU time.

---

## Collection Handling Best Practices

### Use the Right Collection Type

| Collection | When to Use | Key Features |
|------------|-------------|--------------|
| **List<T>** | Ordered data, duplicates allowed | Index access, iteration |
| **Set<T>** | Unique values, fast lookups | No duplicates, O(1) contains() |
| **Map<K,V>** | Key-value pairs, fast lookups | O(1) get(), unique keys |

**Example: Deduplication**
```apex
// ❌ BAD - O(n²) complexity
List<Id> uniqueIds = new List<Id>();
for (Id accountId : allAccountIds) {
    if (!uniqueIds.contains(accountId)) {  // Linear search!
        uniqueIds.add(accountId);
    }
}

// ✅ GOOD - O(n) complexity
Set<Id> uniqueIdsSet = new Set<Id>(allAccountIds);  // Automatic deduplication
```

---

### List Operations

**Creating Lists:**
```apex
// Empty list
List<Account> accounts = new List<Account>();

// From SOQL
List<Account> accounts = [SELECT Id FROM Account];

// From Set
Set<Id> idSet = new Set<Id>{acc1.Id, acc2.Id};
List<Id> idList = new List<Id>(idSet);
```

**Adding Elements:**
```apex
accounts.add(newAccount);           // Add single
accounts.addAll(moreAccounts);      // Add list
```

**Checking Before DML (NOT NEEDED):**
```apex
// ❌ UNNECESSARY - Salesforce handles empty lists
if (!accounts.isEmpty()) {
    update accounts;
}

// ✅ SIMPLER - Just do it
update accounts;  // No-op if empty, saves CPU cycles checking
```

---

### Set Operations

**Union, Intersection, Difference:**
```apex
Set<Id> set1 = new Set<Id>{id1, id2, id3};
Set<Id> set2 = new Set<Id>{id2, id3, id4};

// Union (all unique values)
Set<Id> union = set1.clone();
union.addAll(set2);  // {id1, id2, id3, id4}

// Intersection (common values)
Set<Id> intersection = set1.clone();
intersection.retainAll(set2);  // {id2, id3}

// Difference (in set1 but not set2)
Set<Id> difference = set1.clone();
difference.removeAll(set2);  // {id1}
```

**Checking Membership:**
```apex
if (accountIds.contains(acc.Id)) {
    // Fast O(1) lookup
}
```

**⚠️ API 62.0 Breaking Change:**
Cannot modify Set while iterating - throws `System.FinalException`.

```apex
// ❌ FAILS in API 62.0+
Set<Id> ids = new Set<Id>{id1, id2, id3};
for (Id currentId : ids) {
    ids.add(newId);  // FinalException!
}

// ✅ GOOD - Collect changes, apply after loop
Set<Id> ids = new Set<Id>{id1, id2, id3};
Set<Id> toAdd = new Set<Id>();

for (Id currentId : ids) {
    toAdd.add(newId);
}

ids.addAll(toAdd);
```

---

### Map Operations

**Creating Maps:**
```apex
// Empty map
Map<Id, Account> accountMap = new Map<Id, Account>();

// From List (uses SObject Id as key)
Map<Id, Account> accountMap = new Map<Id, Account>([SELECT Id, Name FROM Account]);

// Manual insertion
Map<String, Integer> scoreMap = new Map<String, Integer>();
scoreMap.put('Alice', 95);
scoreMap.put('Bob', 87);
```

**Safe Access with Null Coalescing:**
```apex
// Old way
Integer score = scoreMap.get('Charlie');
if (score == null) {
    score = 0;
}

// Modern way (API 59+)
Integer score = scoreMap.get('Charlie') ?? 0;
```

**Iterating Maps:**
```apex
// Iterate keys
for (Id accountId : accountMap.keySet()) {
    Account acc = accountMap.get(accountId);
}

// Iterate values
for (Account acc : accountMap.values()) {
    System.debug(acc.Name);
}

// Iterate entries (best for both key + value)
for (Id accountId : accountMap.keySet()) {
    Account acc = accountMap.get(accountId);
    System.debug('Account ' + accountId + ': ' + acc.Name);
}
```

---

## Monitoring and Debugging

### Using Limits Class

**Check current consumption:**
```apex
System.debug('SOQL Queries: ' + Limits.getQueries() + '/' + Limits.getLimitQueries());
System.debug('DML Statements: ' + Limits.getDmlStatements() + '/' + Limits.getLimitDmlStatements());
System.debug('CPU Time: ' + Limits.getCpuTime() + '/' + Limits.getLimitCpuTime());
System.debug('Heap Size: ' + Limits.getHeapSize() + '/' + Limits.getLimitHeapSize());
```

**Strategic placement:**
```apex
public static void expensiveOperation() {
    System.debug('=== BEFORE OPERATION ===');
    logLimits();

    // Expensive code
    List<Account> accounts = [SELECT Id FROM Account];

    System.debug('=== AFTER OPERATION ===');
    logLimits();
}

private static void logLimits() {
    System.debug('SOQL: ' + Limits.getQueries() + '/' + Limits.getLimitQueries());
    System.debug('DML: ' + Limits.getDmlStatements() + '/' + Limits.getLimitDmlStatements());
}
```

---

### Debug Logs Best Practices

**Use log levels strategically:**
```apex
System.debug(LoggingLevel.ERROR, 'Critical failure: ' + errorMsg);
System.debug(LoggingLevel.WARN, 'Warning: potential issue');
System.debug(LoggingLevel.INFO, 'Processing ' + accounts.size() + ' accounts');
System.debug(LoggingLevel.DEBUG, 'Variable value: ' + variable);
System.debug(LoggingLevel.FINE, 'Detailed trace info');
```

**Filter in Setup → Debug Logs:**
- Apex Code: DEBUG
- Database: INFO
- Workflow: INFO
- Validation: INFO

**Avoid excessive debug statements** - they consume heap and CPU.

---

### Query Plan Analysis

**Check query selectivity:**
```apex
// Use EXPLAIN in Developer Console or Workbench
// Or query plan API (requires REST call)
```

**Indicators of bad queries:**
- TableScan (full table scan)
- Cardinality mismatch (estimated vs actual rows)
- Missing indexes on WHERE clause fields

**See Also**: [Live SOQL Query Plan Analyzer](../../../shared/code_analyzer/live_query_plan.py) for automated analysis.

---

## Bulk Testing

### The 251 Record Rule

**Why 251?** Trigger bulkification often breaks between 200-250 records due to chunk processing.

**Test Class Pattern:**
```apex
@IsTest
private class AccountTriggerTest {

    @TestSetup
    static void setup() {
        // Use Test Data Factory to create 251 records
        TestDataFactory.createAccounts(251);
    }

    @IsTest
    static void testBulkInsert() {
        Test.startTest();

        List<Account> accounts = new List<Account>();
        for (Integer i = 0; i < 251; i++) {
            accounts.add(new Account(Name = 'Bulk Test ' + i, Industry = 'Technology'));
        }

        insert accounts;

        Test.stopTest();

        // Verify all 251 were processed correctly
        List<Account> inserted = [SELECT Id, Industry FROM Account WHERE Name LIKE 'Bulk Test%'];
        Assert.areEqual(251, inserted.size(), 'All 251 accounts should be inserted');

        for (Account acc : inserted) {
            Assert.areEqual('Technology', acc.Industry, 'Industry should be set for all records');
        }
    }

    @IsTest
    static void testBulkUpdate() {
        Test.startTest();

        List<Account> accounts = [SELECT Id, Industry FROM Account];
        for (Account acc : accounts) {
            acc.Industry = 'Finance';
        }

        update accounts;

        Test.stopTest();

        // Verify
        List<Account> updated = [SELECT Id, Industry FROM Account];
        Assert.areEqual(251, updated.size());

        for (Account acc : updated) {
            Assert.areEqual('Finance', acc.Industry);
        }
    }
}
```

---

### Test Data Factory Pattern

**Centralized test data creation:**
```apex
@IsTest
public class TestDataFactory {

    public static List<Account> createAccounts(Integer count) {
        List<Account> accounts = new List<Account>();

        for (Integer i = 0; i < count; i++) {
            accounts.add(new Account(
                Name = 'Test Account ' + i,
                Industry = 'Technology',
                AnnualRevenue = 1000000
            ));
        }

        insert accounts;
        return accounts;
    }

    public static List<Contact> createContacts(Integer count, Id accountId) {
        List<Contact> contacts = new List<Contact>();

        for (Integer i = 0; i < count; i++) {
            contacts.add(new Contact(
                LastName = 'Test Contact ' + i,
                AccountId = accountId,
                Email = 'test' + i + '@example.com'
            ));
        }

        insert contacts;
        return contacts;
    }

    // Add more factory methods as needed
}
```

**Benefits**:
- Centralized data creation
- Consistent test data
- Easy to create 251+ records
- Reduces code duplication

---

### Performance Testing

**Measure CPU time and SOQL:**
```apex
@IsTest
static void testPerformance() {
    TestDataFactory.createAccounts(251);

    Integer startQueries = Limits.getQueries();
    Integer startCpu = Limits.getCpuTime();

    Test.startTest();

    // Your code here
    AccountService.processAccounts([SELECT Id FROM Account]);

    Test.stopTest();

    Integer queriesUsed = Limits.getQueries() - startQueries;
    Integer cpuUsed = Limits.getCpuTime() - startCpu;

    System.debug('Queries used: ' + queriesUsed);
    System.debug('CPU time: ' + cpuUsed + 'ms');

    // Assert performance thresholds
    Assert.isTrue(queriesUsed <= 5, 'Should use no more than 5 SOQL queries');
    Assert.isTrue(cpuUsed <= 2000, 'Should complete in under 2 seconds CPU time');
}
```

---

## Advanced Optimization Techniques

### Lazy Loading Pattern

**Defer expensive operations until needed:**
```apex
public class AccountProcessor {

    private Map<Id, List<Contact>> contactsCache;

    public List<Contact> getContactsForAccount(Id accountId) {
        // Lazy load - only query when first accessed
        if (contactsCache == null) {
            loadAllContacts();
        }

        return contactsCache.get(accountId) ?? new List<Contact>();
    }

    private void loadAllContacts() {
        contactsCache = new Map<Id, List<Contact>>();

        for (Contact con : [SELECT Id, AccountId FROM Contact WHERE AccountId IN :accountIds]) {
            if (!contactsCache.containsKey(con.AccountId)) {
                contactsCache.put(con.AccountId, new List<Contact>());
            }
            contactsCache.get(con.AccountId).add(con);
        }
    }
}
```

---

### Platform Cache for Expensive Queries

**Cache frequently accessed data:**
```apex
public class CachedMetadataService {

    private static final String CACHE_PARTITION = 'local.MetadataCache';

    public static List<Config__c> getConfigurations() {
        // Try cache first
        List<Config__c> cached = (List<Config__c>) Cache.Org.get(CACHE_PARTITION + '.configs');

        if (cached != null) {
            return cached;
        }

        // Cache miss - query and store
        List<Config__c> configs = [SELECT Id, Name, Value__c FROM Config__c];
        Cache.Org.put(CACHE_PARTITION + '.configs', configs, 3600); // 1 hour TTL

        return configs;
    }
}
```

---

## Reference

**Full Documentation**: See `references/` folder for comprehensive guides:
- `best-practices.md` - Bulkification patterns
- `testing-guide.md` - Test Data Factory and bulk testing
- `code-review-checklist.md` - Bulkification scoring criteria

**Back to Main**: [SKILL.md](../SKILL.md)
