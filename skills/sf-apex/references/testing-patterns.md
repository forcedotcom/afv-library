<!-- Parent: sf-apex/SKILL.md -->
# Apex Testing Patterns

Comprehensive guide to Apex testing including exception types, test patterns, mocking, and achieving 90%+ code coverage.

---

## Table of Contents

1. [Testing Fundamentals](#testing-fundamentals)
2. [Common Exception Types](#common-exception-types)
3. [Test Patterns](#test-patterns)
4. [Test Data Factory](#test-data-factory)
5. [Mocking and Stubs](#mocking-and-stubs)
6. [Bulk Testing](#bulk-testing)
7. [Code Coverage Strategies](#code-coverage-strategies)

---

## Testing Fundamentals

### Test Class Structure

```apex
@IsTest
private class AccountServiceTest {

    @TestSetup
    static void setup() {
        // Runs ONCE before all test methods
        // Create shared test data
        TestDataFactory.createAccounts(10);
    }

    @IsTest
    static void testPositiveCase() {
        // Arrange: Set up test data
        Account acc = new Account(Name = 'Test', Industry = 'Technology');

        // Act: Execute code under test
        Test.startTest();
        insert acc;
        Test.stopTest();

        // Assert: Verify results
        Account inserted = [SELECT Id, Industry FROM Account WHERE Id = :acc.Id];
        Assert.areEqual('Technology', inserted.Industry, 'Industry should be set');
    }

    @IsTest
    static void testNegativeCase() {
        // Test error conditions
        try {
            insert new Account(); // Missing required Name
            Assert.fail('Expected DmlException was not thrown');
        } catch (DmlException e) {
            Assert.isTrue(e.getMessage().contains('REQUIRED_FIELD_MISSING'));
        }
    }

    @IsTest
    static void testBulkCase() {
        // Test with 251+ records
        List<Account> accounts = new List<Account>();
        for (Integer i = 0; i < 251; i++) {
            accounts.add(new Account(Name = 'Bulk ' + i));
        }

        Test.startTest();
        insert accounts;
        Test.stopTest();

        Assert.areEqual(251, [SELECT COUNT() FROM Account WHERE Name LIKE 'Bulk%']);
    }
}
```

---

### @TestSetup vs Test Methods

| Feature | @TestSetup | Test Methods |
|---------|------------|--------------|
| **Runs** | Once before all tests | Once per test |
| **Data Isolation** | Shared across tests (read-only view) | Isolated per test |
| **Performance** | Faster (reuses data) | Slower (recreates each time) |
| **When to Use** | Common baseline data | Test-specific scenarios |

**Example**:
```apex
@TestSetup
static void setup() {
    // Common data for all tests
    insert new Account(Name = 'Shared Account');
}

@IsTest
static void test1() {
    // Can query the Shared Account
    Account acc = [SELECT Id FROM Account WHERE Name = 'Shared Account'];
    acc.Industry = 'Tech';
    update acc;  // Only visible in this test
}

@IsTest
static void test2() {
    // Shared Account still has Industry = null (data rollback between tests)
    Account acc = [SELECT Id, Industry FROM Account WHERE Name = 'Shared Account'];
    Assert.isNull(acc.Industry);
}
```

---

### Test.startTest() and Test.stopTest()

**Purpose**: Reset governor limits and execute async code.

```apex
@IsTest
static void testAsyncOperation() {
    Account acc = new Account(Name = 'Test');
    insert acc;

    // Limits reset here
    Test.startTest();

    // Enqueue async job
    System.enqueueJob(new AccountProcessor(acc.Id));

    // Async job executes synchronously here
    Test.stopTest();

    // Verify async results
    Account updated = [SELECT Id, Description FROM Account WHERE Id = :acc.Id];
    Assert.isNotNull(updated.Description);
}
```

**Key Points**:
- Governor limits reset at `Test.startTest()`
- Async code (@future, Queueable, Batch) executes at `Test.stopTest()`
- Only one `startTest/stopTest` block per test method

---

## Common Exception Types

When writing test classes, use these specific exception types to validate error handling.

### Exception Type Reference

| Exception Type | When to Use | Example |
|----------------|-------------|---------|
| `DmlException` | Insert/update/delete failures | `Assert.isTrue(e.getMessage().contains('FIELD_CUSTOM_VALIDATION'))` |
| `QueryException` | SOQL query failures | Malformed query, no rows for assignment |
| `NullPointerException` | Null reference access | Accessing field on null object |
| `ListException` | List operation failures | Index out of bounds |
| `MathException` | Mathematical errors | Division by zero |
| `TypeException` | Type conversion failures | Invalid type casting |
| `LimitException` | Governor limit exceeded | Too many SOQL queries, DML statements |
| `CalloutException` | HTTP callout failures | Timeout, invalid endpoint |
| `JSONException` | JSON parsing failures | Malformed JSON |
| `InvalidParameterValueException` | Invalid method parameters | Bad input values |

---

### Testing DmlException

```apex
@IsTest
static void testRequiredFieldMissing() {
    try {
        insert new Account(); // Missing Name
        Assert.fail('Expected DmlException was not thrown');
    } catch (DmlException e) {
        Assert.isTrue(
            e.getMessage().contains('REQUIRED_FIELD_MISSING'),
            'Expected REQUIRED_FIELD_MISSING but got: ' + e.getMessage()
        );
    }
}

@IsTest
static void testDuplicateValue() {
    Account acc1 = new Account(Name = 'Test', Unique_Field__c = 'ABC123');
    insert acc1;

    try {
        Account acc2 = new Account(Name = 'Test2', Unique_Field__c = 'ABC123');
        insert acc2; // Violates unique constraint
        Assert.fail('Expected DmlException');
    } catch (DmlException e) {
        Assert.isTrue(e.getMessage().contains('DUPLICATE_VALUE'));
    }
}

@IsTest
static void testCustomValidationRule() {
    Account acc = new Account(Name = 'Test', AnnualRevenue = -100);

    try {
        insert acc; // Validation rule: Revenue must be > 0
        Assert.fail('Expected DmlException');
    } catch (DmlException e) {
        Assert.isTrue(e.getMessage().contains('FIELD_CUSTOM_VALIDATION_EXCEPTION'));
    }
}
```

---

### Testing QueryException

```apex
@IsTest
static void testNoRowsForAssignment() {
    try {
        // Query expects exactly 1 row but finds 0
        Account acc = [SELECT Id FROM Account WHERE Name = 'Nonexistent'];
        Assert.fail('Expected QueryException');
    } catch (QueryException e) {
        Assert.isTrue(e.getMessage().contains('List has no rows for assignment'));
    }
}

@IsTest
static void testTooManyRows() {
    TestDataFactory.createAccounts(5); // All with same Name

    try {
        // Query expects 1 row but finds 5
        Account acc = [SELECT Id FROM Account WHERE Name LIKE 'Test%'];
        Assert.fail('Expected QueryException');
    } catch (QueryException e) {
        Assert.isTrue(e.getMessage().contains('List has more than 1 row'));
    }
}
```

---

### Testing NullPointerException

```apex
@IsTest
static void testNullReferenceAccess() {
    Account acc = null;

    try {
        String name = acc.Name; // NullPointerException
        Assert.fail('Expected NullPointerException');
    } catch (NullPointerException e) {
        Assert.isNotNull(e.getMessage());
    }
}

@IsTest
static void testSafeNavigationOperator() {
    Account acc = null;

    // No exception - returns null
    String name = acc?.Name;
    Assert.isNull(name, 'Safe navigation should return null');
}
```

---

### Testing LimitException

```apex
@IsTest
static void testSoqlLimitExceeded() {
    // Artificially trigger SOQL limit (for demonstration - don't do this in real code!)
    try {
        for (Integer i = 0; i < 101; i++) {
            List<Account> accounts = [SELECT Id FROM Account LIMIT 1];
        }
        Assert.fail('Expected LimitException');
    } catch (System.LimitException e) {
        Assert.isTrue(e.getMessage().contains('Too many SOQL queries'));
    }
}
```

**Note**: In real tests, you should NEVER hit limits - tests should validate limit-safe code.

---

### Testing CalloutException

```apex
@IsTest
static void testCalloutTimeout() {
    // Set mock callout
    Test.setMock(HttpCalloutMock.class, new TimeoutMock());

    Test.startTest();
    try {
        CalloutService.sendData('test');
        Assert.fail('Expected CalloutException');
    } catch (CalloutException e) {
        Assert.isTrue(e.getMessage().contains('Read timed out'));
    }
    Test.stopTest();
}

// Mock class
private class TimeoutMock implements HttpCalloutMock {
    public HttpResponse respond(HttpRequest req) {
        throw new CalloutException('Read timed out');
    }
}
```

---

## Test Patterns

### Pattern 1: Positive, Negative, Bulk (PNB)

**Every feature needs 3 tests:**

```apex
// 1. POSITIVE: Happy path
@IsTest
static void testCreateAccountSuccess() {
    Account acc = new Account(Name = 'Test', Industry = 'Tech');

    Test.startTest();
    insert acc;
    Test.stopTest();

    Account inserted = [SELECT Id, Industry FROM Account WHERE Id = :acc.Id];
    Assert.areEqual('Tech', inserted.Industry);
}

// 2. NEGATIVE: Error handling
@IsTest
static void testCreateAccountMissingName() {
    try {
        insert new Account();
        Assert.fail('Expected exception');
    } catch (DmlException e) {
        Assert.isTrue(e.getMessage().contains('REQUIRED_FIELD_MISSING'));
    }
}

// 3. BULK: 251+ records
@IsTest
static void testCreateAccountsBulk() {
    List<Account> accounts = new List<Account>();
    for (Integer i = 0; i < 251; i++) {
        accounts.add(new Account(Name = 'Bulk ' + i));
    }

    Test.startTest();
    insert accounts;
    Test.stopTest();

    Assert.areEqual(251, [SELECT COUNT() FROM Account]);
}
```

---

### Pattern 2: System.runAs() for Permission Testing

```apex
@IsTest
static void testUserCannotAccessRestrictedField() {
    // Create user without field permission
    User restrictedUser = TestDataFactory.createStandardUser();

    Account acc = new Account(Name = 'Test', Restricted_Field__c = 'Secret');
    insert acc;

    System.runAs(restrictedUser) {
        try {
            List<Account> accounts = [
                SELECT Id, Restricted_Field__c
                FROM Account
                WHERE Id = :acc.Id
                WITH USER_MODE
            ];
            Assert.fail('Expected QueryException due to FLS');
        } catch (QueryException e) {
            Assert.isTrue(e.getMessage().contains('Insufficient privileges'));
        }
    }
}
```

---

### Pattern 3: Database Methods for Partial Success

```apex
@IsTest
static void testPartialInsertSuccess() {
    List<Account> accounts = new List<Account>{
        new Account(Name = 'Valid Account'),
        new Account(), // Invalid - missing Name
        new Account(Name = 'Another Valid')
    };

    Test.startTest();
    Database.SaveResult[] results = Database.insert(accounts, false); // allOrNone = false
    Test.stopTest();

    // Verify results
    Integer successCount = 0;
    Integer failureCount = 0;

    for (Database.SaveResult result : results) {
        if (result.isSuccess()) {
            successCount++;
        } else {
            failureCount++;
            for (Database.Error err : result.getErrors()) {
                Assert.areEqual(StatusCode.REQUIRED_FIELD_MISSING, err.getStatusCode());
            }
        }
    }

    Assert.areEqual(2, successCount, 'Two accounts should succeed');
    Assert.areEqual(1, failureCount, 'One account should fail');
}
```

---

### Pattern 4: Testing Async Code

**Testing @future:**
```apex
@IsTest
static void testFutureMethod() {
    Account acc = new Account(Name = 'Test');
    insert acc;

    Test.startTest();
    AccountService.updateAsync(acc.Id); // @future method
    Test.stopTest(); // Future executes here

    Account updated = [SELECT Id, Description FROM Account WHERE Id = :acc.Id];
    Assert.areEqual('Updated by future', updated.Description);
}
```

**Testing Queueable:**
```apex
@IsTest
static void testQueueable() {
    Account acc = new Account(Name = 'Test');
    insert acc;

    Test.startTest();
    System.enqueueJob(new AccountProcessor(acc.Id));
    Test.stopTest(); // Queueable executes here

    Account updated = [SELECT Id, Description FROM Account WHERE Id = :acc.Id];
    Assert.areEqual('Processed', updated.Description);
}
```

**Testing Batch:**
```apex
@IsTest
static void testBatch() {
    TestDataFactory.createAccounts(200);

    Test.startTest();
    Database.executeBatch(new AccountBatchProcessor(), 100);
    Test.stopTest(); // Batch executes here

    Integer processed = [SELECT COUNT() FROM Account WHERE Description = 'Processed'];
    Assert.areEqual(200, processed);
}
```

**Testing Schedulable:**
```apex
@IsTest
static void testSchedulable() {
    String cronExp = '0 0 0 * * ?'; // Daily at midnight

    Test.startTest();
    String jobId = System.schedule('Test Job', cronExp, new AccountScheduler());
    Test.stopTest();

    // Verify job was scheduled
    CronTrigger ct = [SELECT Id, CronExpression FROM CronTrigger WHERE Id = :jobId];
    Assert.areEqual(cronExp, ct.CronExpression);
}
```

---

## Test Data Factory

### Basic Factory Pattern

```apex
@IsTest
public class TestDataFactory {

    public static List<Account> createAccounts(Integer count) {
        return createAccounts(count, true);
    }

    public static List<Account> createAccounts(Integer count, Boolean doInsert) {
        List<Account> accounts = new List<Account>();

        for (Integer i = 0; i < count; i++) {
            accounts.add(new Account(
                Name = 'Test Account ' + i,
                Industry = 'Technology',
                AnnualRevenue = 1000000
            ));
        }

        if (doInsert) {
            insert accounts;
        }

        return accounts;
    }

    public static List<Contact> createContacts(Integer count, Id accountId) {
        return createContacts(count, accountId, true);
    }

    public static List<Contact> createContacts(Integer count, Id accountId, Boolean doInsert) {
        List<Contact> contacts = new List<Contact>();

        for (Integer i = 0; i < count; i++) {
            contacts.add(new Contact(
                FirstName = 'Test',
                LastName = 'Contact ' + i,
                AccountId = accountId,
                Email = 'test' + i + '@example.com'
            ));
        }

        if (doInsert) {
            insert contacts;
        }

        return contacts;
    }

    public static User createStandardUser() {
        Profile standardProfile = [SELECT Id FROM Profile WHERE Name = 'Standard User' LIMIT 1];

        User u = new User(
            FirstName = 'Test',
            LastName = 'User',
            Email = 'testuser@example.com',
            Username = 'testuser' + System.currentTimeMillis() + '@example.com',
            Alias = 'tuser',
            TimeZoneSidKey = 'America/Los_Angeles',
            LocaleSidKey = 'en_US',
            EmailEncodingKey = 'UTF-8',
            LanguageLocaleKey = 'en_US',
            ProfileId = standardProfile.Id
        );

        insert u;
        return u;
    }
}
```

**Usage:**
```apex
@TestSetup
static void setup() {
    // Create 251 accounts
    TestDataFactory.createAccounts(251);

    // Create account with 10 contacts
    Account acc = TestDataFactory.createAccounts(1)[0];
    TestDataFactory.createContacts(10, acc.Id);
}
```

---

### Advanced Factory with Builder Pattern

```apex
@IsTest
public class AccountBuilder {

    private Account record;

    public AccountBuilder() {
        record = new Account(
            Name = 'Default Account',
            Industry = 'Technology'
        );
    }

    public AccountBuilder withName(String name) {
        record.Name = name;
        return this;
    }

    public AccountBuilder withIndustry(String industry) {
        record.Industry = industry;
        return this;
    }

    public AccountBuilder withRevenue(Decimal revenue) {
        record.AnnualRevenue = revenue;
        return this;
    }

    public Account build() {
        return record;
    }

    public Account buildAndInsert() {
        insert record;
        return record;
    }
}
```

**Usage:**
```apex
@IsTest
static void testWithBuilder() {
    Account acc = new AccountBuilder()
        .withName('Custom Account')
        .withIndustry('Finance')
        .withRevenue(5000000)
        .buildAndInsert();

    Assert.areEqual('Finance', acc.Industry);
}
```

---

## Mocking and Stubs

### HTTP Callout Mocking

```apex
@IsTest
public class ExternalServiceMock implements HttpCalloutMock {

    public HttpResponse respond(HttpRequest req) {
        // Verify request
        Assert.areEqual('POST', req.getMethod());
        Assert.areEqual('https://api.example.com/accounts', req.getEndpoint());

        // Create mock response
        HttpResponse res = new HttpResponse();
        res.setHeader('Content-Type', 'application/json');
        res.setBody('{"status": "success", "id": "12345"}');
        res.setStatusCode(200);

        return res;
    }
}
```

**Test:**
```apex
@IsTest
static void testExternalCallout() {
    Test.setMock(HttpCalloutMock.class, new ExternalServiceMock());

    Test.startTest();
    String result = CalloutService.sendData('test data');
    Test.stopTest();

    Assert.areEqual('12345', result);
}
```

---

### Multi-Request Callout Mock

```apex
@IsTest
public class MultiCalloutMock implements HttpCalloutMock {

    public HttpResponse respond(HttpRequest req) {
        HttpResponse res = new HttpResponse();
        res.setHeader('Content-Type', 'application/json');

        // Different responses based on endpoint
        if (req.getEndpoint().endsWith('/accounts')) {
            res.setBody('{"accounts": [{"id": "1"}]}');
            res.setStatusCode(200);
        } else if (req.getEndpoint().endsWith('/contacts')) {
            res.setBody('{"contacts": [{"id": "2"}]}');
            res.setStatusCode(200);
        } else {
            res.setStatusCode(404);
        }

        return res;
    }
}
```

---

### Stub API (Test Doubles)

```apex
@IsTest
public class AccountSelectorStub implements IAccountSelector {

    private List<Account> stubbedAccounts;

    public AccountSelectorStub(List<Account> accounts) {
        this.stubbedAccounts = accounts;
    }

    public List<Account> selectById(Set<Id> accountIds) {
        // Return stubbed data instead of querying
        return stubbedAccounts;
    }
}
```

**Test with stub:**
```apex
@IsTest
static void testWithStub() {
    // Create stub data (no DML needed!)
    List<Account> stubbedAccounts = new List<Account>{
        new Account(Id = TestUtility.getFakeId(Account.SObjectType), Name = 'Stub Account')
    };

    IAccountSelector selector = new AccountSelectorStub(stubbedAccounts);

    // Inject stub into service
    AccountService service = new AccountService(selector);

    Test.startTest();
    List<Account> results = service.getAccounts();
    Test.stopTest();

    Assert.areEqual(1, results.size());
    Assert.areEqual('Stub Account', results[0].Name);
}
```

---

## Bulk Testing

### The 251 Record Test

```apex
@IsTest
static void testBulkTriggerExecution() {
    List<Account> accounts = new List<Account>();

    for (Integer i = 0; i < 251; i++) {
        accounts.add(new Account(
            Name = 'Bulk Test ' + i,
            Industry = 'Technology'
        ));
    }

    Test.startTest();

    insert accounts;

    Test.stopTest();

    // Verify trigger logic executed for all 251
    List<Account> inserted = [SELECT Id, Description FROM Account WHERE Name LIKE 'Bulk Test%'];
    Assert.areEqual(251, inserted.size());

    for (Account acc : inserted) {
        Assert.isNotNull(acc.Description, 'Description should be set by trigger');
    }
}
```

---

### Testing Governor Limits

```apex
@IsTest
static void testDoesNotHitSoqlLimit() {
    TestDataFactory.createAccounts(251);

    Integer queriesBefore = Limits.getQueries();

    Test.startTest();
    AccountService.processAllAccounts();
    Test.stopTest();

    Integer queriesAfter = Limits.getQueries();
    Integer queriesUsed = queriesAfter - queriesBefore;

    Assert.isTrue(queriesUsed <= 5, 'Should use no more than 5 SOQL queries, used: ' + queriesUsed);
}
```

---

## Code Coverage Strategies

### Achieving 90%+ Coverage

**1. Test all branches (if/else):**
```apex
// Code
public static String getStatus(Account acc) {
    if (acc.AnnualRevenue > 1000000) {
        return 'Enterprise';
    } else {
        return 'SMB';
    }
}

// Test BOTH branches
@IsTest
static void testEnterpriseStatus() {
    Account acc = new Account(Name = 'Test', AnnualRevenue = 2000000);
    Assert.areEqual('Enterprise', AccountService.getStatus(acc));
}

@IsTest
static void testSmbStatus() {
    Account acc = new Account(Name = 'Test', AnnualRevenue = 500000);
    Assert.areEqual('SMB', AccountService.getStatus(acc));
}
```

**2. Test all catch blocks:**
```apex
// Code
try {
    insert accounts;
} catch (DmlException e) {
    // Handle DML error
    logError(e);
}

// Test
@IsTest
static void testCatchBlock() {
    List<Account> invalid = new List<Account>{ new Account() }; // Missing Name

    try {
        insert invalid;
    } catch (DmlException e) {
        // Catch block is now covered
    }
}
```

**3. Test all methods:**
```apex
// Every public/global method needs at least one test
@IsTest
static void testEveryMethod() {
    AccountService.method1();
    AccountService.method2();
    AccountService.method3();
    // etc.
}
```

---

### Identifying Uncovered Code

**Developer Console:**
1. Open class
2. Click Tests → New Run
3. Select test class
4. View coverage % and red highlights

**VS Code:**
1. Run tests: `Ctrl+Shift+P` → "SFDX: Run Apex Tests"
2. View coverage in Problems panel

**CLI:**
```bash
sf apex run test --code-coverage --result-format human --test-level RunLocalTests
```

---

## Reference

**Full Documentation**: See `references/` folder for comprehensive guides:
- `testing-guide.md` - Complete testing reference
- `best-practices.md` - Test best practices
- `code-review-checklist.md` - Testing scoring criteria

**Back to Main**: [SKILL.md](../SKILL.md)
