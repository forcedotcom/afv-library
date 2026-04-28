<!-- Parent: sf-apex/SKILL.md -->
# Apex Anti-Patterns

Comprehensive catalog of common Apex anti-patterns, code smells, and how to fix them.

---

## Table of Contents

1. [Critical Anti-Patterns](#critical-anti-patterns)
2. [Code Review Red Flags](#code-review-red-flags)
3. [Performance Anti-Patterns](#performance-anti-patterns)
4. [Security Anti-Patterns](#security-anti-patterns)
5. [Testing Anti-Patterns](#testing-anti-patterns)
6. [Code Smell Catalog](#code-smell-catalog)

---

<a id="critical-anti-patterns"></a>

## Critical Anti-Patterns

These patterns will cause immediate failures or security vulnerabilities. **NEVER allow these in production code.**

### 1. SOQL in Loop

**Problem**: Hits 100 SOQL query limit.

**❌ BAD:**
```apex
for (Account acc : accounts) {
    List<Contact> contacts = [SELECT Id FROM Contact WHERE AccountId = :acc.Id];
    // Process contacts
}
// Fails after 100 accounts
```

**✅ GOOD:**
```apex
Set<Id> accountIds = new Set<Id>();
for (Account acc : accounts) {
    accountIds.add(acc.Id);
}

Map<Id, List<Contact>> contactsByAccountId = new Map<Id, List<Contact>>();
for (Contact con : [SELECT Id, AccountId FROM Contact WHERE AccountId IN :accountIds]) {
    if (!contactsByAccountId.containsKey(con.AccountId)) {
        contactsByAccountId.put(con.AccountId, new List<Contact>());
    }
    contactsByAccountId.get(con.AccountId).add(con);
}

for (Account acc : accounts) {
    List<Contact> contacts = contactsByAccountId.get(acc.Id) ?? new List<Contact>();
    // Process contacts
}
```

**Detection**: Search for `[SELECT` inside `for` loops.

---

### 2. DML in Loop

**Problem**: Hits 150 DML statement limit.

**❌ BAD:**
```apex
for (Account acc : accounts) {
    acc.Industry = 'Technology';
    update acc;  // DML in loop!
}
// Fails after 150 accounts
```

**✅ GOOD:**
```apex
for (Account acc : accounts) {
    acc.Industry = 'Technology';
}
update accounts;  // Single DML after loop
```

**Detection**: Search for `insert`, `update`, `delete`, `upsert` inside `for` loops.

---

### 3. Missing Sharing Keyword

**Problem**: Bypasses record-level security by default.

**❌ BAD:**
```apex
public class AccountService {
    // Implicitly "without sharing" - security risk!
}
```

**✅ GOOD:**
```apex
public with sharing class AccountService {
    // Respects sharing rules
}
```

**Detection**: Classes without `with sharing`, `without sharing`, or `inherited sharing`.

---

### 4. Hardcoded Record IDs

**Problem**: IDs differ between orgs, causing deployment failures.

**❌ BAD:**
```apex
Id recordTypeId = '012000000000000AAA';  // Hardcoded ID!
```

**✅ GOOD:**
```apex
// Option 1: Query at runtime
Id recordTypeId = Schema.SObjectType.Account.getRecordTypeInfosByDeveloperName()
    .get('Enterprise').getRecordTypeId();

// Option 2: Custom Metadata
Account_Config__mdt config = Account_Config__mdt.getInstance('Default');
Id recordTypeId = config.Record_Type_Id__c;
```

**Detection**: 15 or 18-character ID literals in code.

---

### 5. Empty Catch Blocks

**Problem**: Silently swallows errors, making debugging impossible.

**❌ BAD:**
```apex
try {
    insert accounts;
} catch (DmlException e) {
    // Silent failure - no logging!
}
```

**✅ GOOD:**
```apex
try {
    insert accounts;
} catch (DmlException e) {
    System.debug(LoggingLevel.ERROR, 'Failed to insert accounts: ' + e.getMessage());
    throw e;  // Or handle gracefully with user feedback
}
```

**Detection**: `catch` blocks with no statements or only comments.

---

### 6. SOQL Injection

**Problem**: User input concatenated into SOQL allows malicious queries.

**❌ BAD:**
```apex
String query = 'SELECT Id FROM Account WHERE Name = \'' + userInput + '\'';
List<Account> accounts = Database.query(query);
// userInput = "test' OR '1'='1" returns ALL accounts!
```

**✅ GOOD:**
```apex
// Use bind variables
List<Account> accounts = [SELECT Id FROM Account WHERE Name = :userInput];
```

**Detection**: String concatenation in SOQL with variables.

---

### 7. Test Without Assertions

**Problem**: False positive tests that pass even when code fails.

**❌ BAD:**
```apex
@IsTest
static void testAccountCreation() {
    Account acc = new Account(Name = 'Test');
    insert acc;
    // No assertions - test passes even if logic is broken!
}
```

**✅ GOOD:**
```apex
@IsTest
static void testAccountCreation() {
    Account acc = new Account(Name = 'Test', Industry = 'Tech');
    insert acc;

    Account inserted = [SELECT Id, Industry FROM Account WHERE Id = :acc.Id];
    Assert.areEqual('Tech', inserted.Industry, 'Industry should be set');
}
```

**Detection**: `@IsTest` methods with no `Assert.*` calls.

---

## Code Review Red Flags

These patterns indicate poor code quality and should be refactored.

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| **SOQL without WHERE or LIMIT** | Returns all records, slow | Always add `WHERE` clause or `LIMIT` |
| **Multiple triggers on object** | Unpredictable execution order | Single trigger + Trigger Actions Framework |
| **Generic `Exception` only** | Masks specific errors | Catch specific exceptions first |
| **No trigger bypass flag** | Can't disable for data loads | Add Custom Setting bypass |
| **`System.debug()` everywhere** | Performance impact, clutters logs | Use logging framework with levels |
| **Unnecessary `isEmpty()` before DML** | Wastes CPU | Remove - DML handles empty lists |
| **`!= false` comparisons** | Confusing double negative | Use `== true` or just the boolean |
| **No Test Data Factory** | Duplicated test data setup | Centralize in factory class |
| **God Class** | Single class does everything | Split into Service/Selector/Domain |
| **Magic Numbers** | Hardcoded values like `if (score > 75)` | Use named constants |

---

### SOQL Without WHERE or LIMIT

**❌ BAD:**
```apex
List<Account> accounts = [SELECT Id FROM Account];
// Returns ALL accounts - could be millions!
```

**✅ GOOD:**
```apex
// Option 1: Filter
List<Account> accounts = [SELECT Id FROM Account WHERE Industry = 'Technology'];

// Option 2: Limit
List<Account> accounts = [SELECT Id FROM Account ORDER BY CreatedDate DESC LIMIT 200];

// Option 3: Both
List<Account> accounts = [SELECT Id FROM Account WHERE CreatedDate = THIS_YEAR LIMIT 1000];
```

---

### Multiple Triggers on Same Object

**❌ BAD:**
```apex
// AccountTrigger1.trigger
trigger AccountTrigger1 on Account (before insert) {
    // Some logic
}

// AccountTrigger2.trigger
trigger AccountTrigger2 on Account (before insert) {
    // More logic - which runs first?
}
```

**✅ GOOD:**
```apex
// Single trigger + TAF
trigger AccountTrigger on Account (before insert, after insert, before update, after update) {
    new MetadataTriggerHandler().run();
}

// Separate action classes
public class TA_Account_SetDefaults implements TriggerAction.BeforeInsert { }
public class TA_Account_Validate implements TriggerAction.BeforeInsert { }
```

---

### Generic Exception Only

**❌ BAD:**
```apex
try {
    insert accounts;
} catch (Exception e) {
    // Catches EVERYTHING - too broad
}
```

**✅ GOOD:**
```apex
try {
    insert accounts;
} catch (DmlException e) {
    // Handle DML errors specifically
    System.debug('DML failed: ' + e.getDmlMessage(0));
} catch (Exception e) {
    // Catch unexpected errors
    System.debug('Unexpected error: ' + e.getMessage());
    throw e;
}
```

---

### Unnecessary isEmpty() Before DML

**❌ BAD:**
```apex
if (!accounts.isEmpty()) {
    update accounts;
}
// Wastes CPU checking - DML already handles empty lists
```

**✅ GOOD:**
```apex
update accounts;  // No-op if empty, no error thrown
```

---

### Double Negative Comparisons

**❌ BAD:**
```apex
if (acc.IsActive__c != false) {
    // Confusing logic
}
```

**✅ GOOD:**
```apex
if (acc.IsActive__c == true) {
    // Clear intent
}

// Or even better
if (acc.IsActive__c) {
    // Most concise
}
```

---

<a id="performance-anti-patterns"></a>

## Performance Anti-Patterns

### 1. Nested Loops with SOQL

**❌ BAD:**
```apex
for (Account acc : accounts) {
    for (Contact con : [SELECT Id FROM Contact WHERE AccountId = :acc.Id]) {
        // Nested SOQL - quadratic complexity!
    }
}
```

**✅ GOOD:**
```apex
Map<Id, Account> accountsWithContacts = new Map<Id, Account>([
    SELECT Id, (SELECT Id FROM Contacts)
    FROM Account
    WHERE Id IN :accountIds
]);

for (Account acc : accountsWithContacts.values()) {
    for (Contact con : acc.Contacts) {
        // No SOQL in loop
    }
}
```

---

### 2. Querying in Constructor

**❌ BAD:**
```apex
public class AccountService {
    private List<Account> accounts;

    public AccountService() {
        accounts = [SELECT Id FROM Account];  // Runs on EVERY instantiation
    }
}
```

**✅ GOOD:**
```apex
public class AccountService {
    private List<Account> accounts;

    public AccountService(List<Account> accounts) {
        this.accounts = accounts;  // Inject dependencies
    }

    // Or lazy load only when needed
    private List<Account> getAccounts() {
        if (accounts == null) {
            accounts = [SELECT Id FROM Account LIMIT 200];
        }
        return accounts;
    }
}
```

---

### 3. Excessive CPU Time

**❌ BAD:**
```apex
for (Account acc : accounts) {
    for (Integer i = 0; i < 10000; i++) {
        String hash = EncodingUtil.convertToHex(Crypto.generateDigest('SHA256', Blob.valueOf(acc.Name + i)));
        // Expensive crypto in nested loop
    }
}
```

**✅ GOOD:**
```apex
// Move expensive operations outside loops
String baseHash = EncodingUtil.convertToHex(Crypto.generateDigest('SHA256', Blob.valueOf('base')));

for (Account acc : accounts) {
    acc.Hash__c = baseHash;  // Reuse computed value
}
```

---

### 4. Inefficient Collections

**❌ BAD:**
```apex
List<Id> uniqueIds = new List<Id>();
for (Id accountId : allIds) {
    if (!uniqueIds.contains(accountId)) {  // O(n) lookup in List
        uniqueIds.add(accountId);
    }
}
```

**✅ GOOD:**
```apex
Set<Id> uniqueIds = new Set<Id>(allIds);  // O(1) deduplication
```

---

<a id="security-anti-patterns"></a>

## Security Anti-Patterns

### 1. without sharing Everywhere

**❌ BAD:**
```apex
public without sharing class AccountController {
    @AuraEnabled
    public static List<Account> getAccounts() {
        // Bypasses sharing - user sees ALL accounts!
        return [SELECT Id FROM Account];
    }
}
```

**✅ GOOD:**
```apex
public with sharing class AccountController {
    @AuraEnabled
    public static List<Account> getAccounts() {
        // Respects sharing rules
        return [SELECT Id FROM Account WITH USER_MODE];
    }
}
```

---

### 2. No CRUD/FLS Checks

**❌ BAD:**
```apex
public static void updateAccounts(List<Account> accounts) {
    update accounts;  // No permission check!
}
```

**✅ GOOD:**
```apex
public static void updateAccounts(List<Account> accounts) {
    if (!Schema.sObjectType.Account.isUpdateable()) {
        throw new SecurityException('User cannot update Accounts');
    }

    // Or use WITH USER_MODE in queries
    update accounts;
}
```

---

### 3. Hardcoded Credentials

**❌ BAD:**
```apex
String apiKey = 'sk_live_abc123xyz';  // NEVER hardcode secrets!
```

**✅ GOOD:**
```apex
// Use Named Credentials
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:MyNamedCredential/api');  // Auth handled by platform
```

---

<a id="testing-anti-patterns"></a>

## Testing Anti-Patterns

### 1. @SeeAllData=true

**❌ BAD:**
```apex
@IsTest(SeeAllData=true)
private class AccountServiceTest {
    // Depends on org data - brittle, slow
}
```

**✅ GOOD:**
```apex
@IsTest
private class AccountServiceTest {
    @TestSetup
    static void setup() {
        TestDataFactory.createAccounts(10);  // Isolated test data
    }
}
```

---

### 2. No Bulk Testing

**❌ BAD:**
```apex
@IsTest
static void testAccountCreation() {
    Account acc = new Account(Name = 'Test');
    insert acc;
    // Only tests 1 record - misses bulkification bugs
}
```

**✅ GOOD:**
```apex
@IsTest
static void testBulkAccountCreation() {
    List<Account> accounts = new List<Account>();
    for (Integer i = 0; i < 251; i++) {
        accounts.add(new Account(Name = 'Bulk Test ' + i));
    }

    insert accounts;
    Assert.areEqual(251, [SELECT COUNT() FROM Account]);
}
```

---

### 3. Testing Implementation, Not Behavior

**❌ BAD:**
```apex
@IsTest
static void testGetAccountsCallsQuery() {
    // Tests internal implementation
    Assert.areEqual(1, Limits.getQueries(), 'Should call SOQL once');
}
```

**✅ GOOD:**
```apex
@IsTest
static void testGetAccountsReturnsCorrectRecords() {
    TestDataFactory.createAccounts(5);

    List<Account> results = AccountService.getAccounts();

    Assert.areEqual(5, results.size(), 'Should return all accounts');
}
```

---

## Code Smell Catalog

Based on "Clean Apex Code" by Pablo Gonzalez and clean code principles.

### Long Method

**Smell**: Method exceeds 30 lines.

**❌ BAD:**
```apex
public static void processAccount(Account acc) {
    // 100 lines of mixed logic
    if (acc.Industry == 'Tech') {
        // Validation logic
        if (acc.AnnualRevenue == null) { ... }
        // Calculation logic
        Decimal score = ...;
        // DML logic
        update acc;
        // Notification logic
        EmailService.send(...);
    }
}
```

**✅ GOOD:**
```apex
public static void processAccount(Account acc) {
    validateAccount(acc);
    calculateScore(acc);
    saveAccount(acc);
    notifyOwner(acc);
}

private static void validateAccount(Account acc) { ... }
private static void calculateScore(Account acc) { ... }
private static void saveAccount(Account acc) { ... }
private static void notifyOwner(Account acc) { ... }
```

**Refactoring**: Extract Method - split into smaller methods with single responsibilities.

---

### Large Class (God Class)

**Smell**: Class exceeds 500 lines or has 20+ methods.

**❌ BAD:**
```apex
public class AccountService {
    // 50 methods mixing concerns:
    public static void createAccount() { }
    public static void updateAccount() { }
    public static void validateAccount() { }
    public static void calculateScore() { }
    public static void sendEmail() { }
    public static void generateReport() { }
    // ... 44 more methods
}
```

**✅ GOOD:**
```apex
// Split by responsibility
public class AccountService { }         // Business logic
public class AccountValidator { }       // Validation
public class AccountScoreCalculator { } // Scoring
public class AccountEmailService { }    // Notifications
public class AccountReportGenerator { } // Reporting
```

**Refactoring**: Extract Class - split into multiple classes by concern.

---

### Magic Numbers

**Smell**: Unexplained numeric literals.

**❌ BAD:**
```apex
if (acc.Score__c > 75) {
    acc.Rating = 'Hot';
}
```

**✅ GOOD:**
```apex
private static final Integer HOT_LEAD_THRESHOLD = 75;

if (acc.Score__c > HOT_LEAD_THRESHOLD) {
    acc.Rating = 'Hot';
}
```

---

### Long Parameter List

**Smell**: Method has 5+ parameters.

**❌ BAD:**
```apex
public static void createAccount(
    String name,
    String industry,
    Decimal revenue,
    String phone,
    String email,
    String website,
    Id ownerId
) { }
```

**✅ GOOD:**
```apex
public class AccountRequest {
    public String name;
    public String industry;
    public Decimal revenue;
    public String phone;
    public String email;
    public String website;
    public Id ownerId;
}

public static void createAccount(AccountRequest request) { }
```

---

### Feature Envy

**Smell**: Method uses more methods/fields from another class than its own.

**❌ BAD:**
```apex
public class OrderService {
    public static Decimal calculateDiscount(Order__c order) {
        Account acc = [SELECT Id, Tier__c FROM Account WHERE Id = :order.Account__c];
        if (acc.Tier__c == 'Gold') {
            return order.Amount__c * 0.2;
        } else if (acc.Tier__c == 'Silver') {
            return order.Amount__c * 0.1;
        }
        return 0;
    }
}
```

**✅ GOOD:**
```apex
public class Account extends SObject {
    public Decimal getDiscountRate() {
        if (this.Tier__c == 'Gold') return 0.2;
        if (this.Tier__c == 'Silver') return 0.1;
        return 0;
    }
}

public class OrderService {
    public static Decimal calculateDiscount(Order__c order) {
        Account acc = [SELECT Id, Tier__c FROM Account WHERE Id = :order.Account__c];
        return order.Amount__c * acc.getDiscountRate();
    }
}
```

**Refactoring**: Move Method - move logic to the class it uses most.

---

### Primitive Obsession

**Smell**: Using primitives instead of small objects to represent concepts.

**❌ BAD:**
```apex
public static void sendEmail(String address, String subject, String body) {
    // Validates email format inline
    if (!address.contains('@')) throw new InvalidEmailException();
}
```

**✅ GOOD:**
```apex
public class EmailAddress {
    private String value;

    public EmailAddress(String address) {
        if (!address.contains('@')) {
            throw new InvalidEmailException('Invalid email format');
        }
        this.value = address;
    }

    public String getValue() {
        return value;
    }
}

public static void sendEmail(EmailAddress address, String subject, String body) {
    // Email is already validated
}
```

---

## Detection Tools

**How to find anti-patterns:**

| Tool | What It Finds |
|------|---------------|
| **Salesforce Code Analyzer** | SOQL/DML in loops, security issues |
| **PMD (via VS Code)** | Code quality, complexity, unused code |
| **Developer Console** | Test coverage, debug logs |
| **Grep/Search** | Hardcoded IDs, empty catches, magic numbers |

**VS Code Command:**
```bash
sf code-analyzer run --workspace force-app/main/default/classes --view table
```

**Example output:**
```
Severity  File                    Line  Rule                     Message
────────────────────────────────────────────────────────────────────────────
3         AccountService.cls      45    ApexSOQLInjection        SOQL injection risk
2         AccountTrigger.trigger  12    ApexCRUDViolation        Missing FLS check
1         ContactController.cls   28    ApexUnitTestClassShouldHaveAsserts  No assertions
```

---

## Refactoring Checklist

When reviewing code, check for:

**Bulkification:**
- [ ] No SOQL in loops
- [ ] No DML in loops
- [ ] Collections used efficiently (Maps for lookups)
- [ ] Tested with 251+ records

**Security:**
- [ ] All classes have sharing keyword
- [ ] SOQL uses `WITH USER_MODE` or `Security.stripInaccessible()`
- [ ] No hardcoded credentials
- [ ] No SOQL injection vulnerabilities

**Clean Code:**
- [ ] Methods under 30 lines
- [ ] Classes under 500 lines
- [ ] No magic numbers (use constants)
- [ ] Meaningful variable/method names

**Testing:**
- [ ] All methods covered by tests
- [ ] Tests have assertions
- [ ] Bulk tests exist (251+ records)
- [ ] No `@SeeAllData=true`

**Error Handling:**
- [ ] No empty catch blocks
- [ ] Specific exceptions before generic
- [ ] Errors logged with context

---

## Reference

**Full Documentation**: See `references/` folder for comprehensive guides:
- `code-smells-guide.md` - Complete code smell catalog
- `best-practices.md` - Correct patterns
- `code-review-checklist.md` - 150-point scoring

**Back to Main**: [SKILL.md](../SKILL.md)
