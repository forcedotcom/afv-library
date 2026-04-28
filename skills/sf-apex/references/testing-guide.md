<!-- Parent: sf-apex/SKILL.md -->
# Apex Testing Guide

## Testing Fundamentals

### Coverage Requirements
- **Minimum**: 75% for deployment
- **Recommended**: 90%+ for quality
- **Best Practice**: Maintain buffer above 75%

### Test Class Structure

```apex
@isTest
private class AccountServiceTest {

    @TestSetup
    static void setup() {
        // Create test data once, available to all test methods
        TestDataFactory.createAccounts(10);
    }

    @isTest
    static void testPositiveScenario() {
        // Arrange
        Account acc = [SELECT Id FROM Account LIMIT 1];

        // Act
        Test.startTest();
        String result = AccountService.processAccount(acc.Id);
        Test.stopTest();

        // Assert
        Assert.areEqual('Success', result, 'Should return success');
    }

    @isTest
    static void testNegativeScenario() {
        // Test error handling
        Test.startTest();
        try {
            AccountService.processAccount(null);
            Assert.fail('Should have thrown exception');
        } catch (IllegalArgumentException e) {
            Assert.isTrue(e.getMessage().contains('null'), 'Should mention null');
        }
        Test.stopTest();
    }

    @isTest
    static void testBulkScenario() {
        // Test with 251+ records (spans two trigger batches)
        List<Account> accounts = TestDataFactory.createAccounts(251);

        Test.startTest();
        List<String> results = AccountService.processAccounts(accounts);
        Test.stopTest();

        Assert.areEqual(251, results.size(), 'Should process all records');
    }
}
```

---

## Spring '26 Test Annotations

### `@isTest(testFor=ClassName.class)` — Test-to-Source Linking

Explicitly links a test class to the production class it covers. Improves coverage attribution and supports `RunRelevantTests` deployment mode.

```apex
@isTest(testFor=AccountService.class)
private class AccountServiceTest {
    // All test methods here count toward AccountService coverage
}
```

### `@isTest(isCritical=true)` — Always-Run Tests

Marks tests that must always execute, even when using `RunRelevantTests` test level. Use for smoke tests, critical business logic, and integration test entry points.

```apex
@isTest(isCritical=true)
private class PaymentProcessorTest {
    // Runs even in RunRelevantTests mode
}
```

Can combine with `testFor`:
```apex
@isTest(testFor=PaymentProcessor.class, isCritical=true)
private class PaymentProcessorTest { }
```

---

## Assert Class (Winter '23+)

### Preferred Assert Methods

```apex
// Equality
Assert.areEqual(expected, actual, 'Optional message');
Assert.areNotEqual(unexpected, actual);

// Boolean
Assert.isTrue(condition, 'Should be true');
Assert.isFalse(condition, 'Should be false');

// Null
Assert.isNull(value, 'Should be null');
Assert.isNotNull(value, 'Should not be null');

// Instance type
Assert.isInstanceOfType(obj, Account.class, 'Should be Account');

// Explicit failure
Assert.fail('This should not be reached');
```

### Testing Exceptions

```apex
@isTest
static void testExceptionThrown() {
    Test.startTest();
    try {
        MyService.riskyOperation();
        Assert.fail('Expected MyCustomException');
    } catch (MyCustomException e) {
        Assert.isTrue(e.getMessage().contains('expected text'));
    }
    Test.stopTest();
}
```

---

## Test Data Factory Pattern

### Factory Class

```apex
@isTest
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
                BillingCity = 'San Francisco'
            ));
        }
        if (doInsert) {
            insert accounts;
        }
        return accounts;
    }

    public static List<Contact> createContacts(Integer count, Id accountId) {
        List<Contact> contacts = new List<Contact>();
        for (Integer i = 0; i < count; i++) {
            contacts.add(new Contact(
                FirstName = 'Test',
                LastName = 'Contact ' + i,
                Email = 'test' + i + '@example.com',
                AccountId = accountId
            ));
        }
        insert contacts;
        return contacts;
    }

    public static User createUser(String profileName) {
        Profile p = [SELECT Id FROM Profile WHERE Name = :profileName LIMIT 1];
        String uniqueKey = String.valueOf(DateTime.now().getTime());

        User u = new User(
            Alias = 'test' + uniqueKey.right(4),
            Email = 'test' + uniqueKey + '@example.com',
            EmailEncodingKey = 'UTF-8',
            LastName = 'Test',
            LanguageLocaleKey = 'en_US',
            LocaleSidKey = 'en_US',
            ProfileId = p.Id,
            TimeZoneSidKey = 'America/Los_Angeles',
            Username = 'test' + uniqueKey + '@example.com.test'
        );
        insert u;
        return u;
    }
}
```

### Builder Pattern (Complex Objects)

```apex
@isTest
public class AccountBuilder {
    private Account record;

    public AccountBuilder() {
        this.record = new Account(
            Name = 'Default Account',
            Industry = 'Other'
        );
    }

    public AccountBuilder withName(String name) {
        this.record.Name = name;
        return this;
    }

    public AccountBuilder withIndustry(String industry) {
        this.record.Industry = industry;
        return this;
    }

    public AccountBuilder withBillingAddress(String city, String state) {
        this.record.BillingCity = city;
        this.record.BillingState = state;
        return this;
    }

    public Account build() {
        return this.record;
    }

    public Account buildAndInsert() {
        insert this.record;
        return this.record;
    }
}

// Usage
Account acc = new AccountBuilder()
    .withName('Acme Corp')
    .withIndustry('Technology')
    .withBillingAddress('San Francisco', 'CA')
    .buildAndInsert();
```

---

## @TestSetup

### Benefits
- Runs once per test class
- Data available to all test methods
- Rolled back after each test method

```apex
@TestSetup
static void setup() {
    // Create accounts
    List<Account> accounts = TestDataFactory.createAccounts(5);

    // Create contacts for first account
    TestDataFactory.createContacts(10, accounts[0].Id);

    // Create custom settings
    insert new MySettings__c(SetupOwnerId = UserInfo.getOrganizationId());
}
```

### Accessing TestSetup Data

```apex
@isTest
static void testMethod1() {
    // Query the data created in @TestSetup
    List<Account> accounts = [SELECT Id, Name FROM Account];
    Assert.areEqual(5, accounts.size());
}
```

---

## Testing Async Code

### Test.startTest() / Test.stopTest()

```apex
@isTest
static void testQueueable() {
    Account acc = TestDataFactory.createAccounts(1)[0];

    Test.startTest();
    System.enqueueJob(new MyQueueable(acc.Id));
    Test.stopTest();  // Forces async to complete

    // Assert results
    Account updated = [SELECT Status__c FROM Account WHERE Id = :acc.Id];
    Assert.areEqual('Processed', updated.Status__c);
}

@isTest
static void testFuture() {
    Test.startTest();
    MyService.asyncMethod();  // @future method
    Test.stopTest();

    // Assert results after async completes
}

@isTest
static void testBatch() {
    Test.startTest();
    Database.executeBatch(new MyBatch(), 200);
    Test.stopTest();

    // Assert batch results
}
```

---

## Mocking HTTP Callouts

### HttpCalloutMock Implementation

```apex
@isTest
public class MockHttpResponse implements HttpCalloutMock {
    private Integer statusCode;
    private String body;

    public MockHttpResponse(Integer statusCode, String body) {
        this.statusCode = statusCode;
        this.body = body;
    }

    public HTTPResponse respond(HTTPRequest req) {
        HttpResponse res = new HttpResponse();
        res.setStatusCode(this.statusCode);
        res.setBody(this.body);
        return res;
    }
}

// Usage
@isTest
static void testCallout() {
    Test.setMock(HttpCalloutMock.class, new MockHttpResponse(200, '{"success": true}'));

    Test.startTest();
    String result = MyCalloutService.makeCallout();
    Test.stopTest();

    Assert.areEqual('success', result);
}
```

### Multi-Response Mock

```apex
public class MultiMockHttpResponse implements HttpCalloutMock {
    private Map<String, HttpResponse> responses = new Map<String, HttpResponse>();

    public void addResponse(String endpoint, Integer statusCode, String body) {
        HttpResponse res = new HttpResponse();
        res.setStatusCode(statusCode);
        res.setBody(body);
        responses.put(endpoint, res);
    }

    public HTTPResponse respond(HTTPRequest req) {
        String endpoint = req.getEndpoint();
        if (responses.containsKey(endpoint)) {
            return responses.get(endpoint);
        }
        throw new CalloutException('No mock for: ' + endpoint);
    }
}
```

---

## Dependency Injection for Testing

### Factory Pattern

```apex
// Production code
public virtual class Factory {
    private static Factory instance;

    public static Factory getInstance() {
        if (instance == null) {
            instance = new Factory();
        }
        return instance;
    }

    @TestVisible
    private static void setInstance(Factory mockFactory) {
        instance = mockFactory;
    }

    public virtual AccountService getAccountService() {
        return new AccountService();
    }
}

// Test
@isTest
static void testWithMock() {
    Factory.setInstance(new MockFactory());

    Test.startTest();
    // Code uses MockFactory.getAccountService() which returns mock
    Test.stopTest();
}

private class MockFactory extends Factory {
    public override AccountService getAccountService() {
        return new MockAccountService();
    }
}
```

---

## Testing with Different Users

### System.runAs()

```apex
@isTest
static void testAsStandardUser() {
    User standardUser = TestDataFactory.createUser('Standard User');

    System.runAs(standardUser) {
        Test.startTest();
        // Code executes as standardUser
        List<Account> accounts = AccountService.getAccounts();
        Test.stopTest();

        // User only sees records they have access to
        Assert.areEqual(0, accounts.size());
    }
}

@isTest
static void testAsAdmin() {
    User adminUser = TestDataFactory.createUser('System Administrator');

    System.runAs(adminUser) {
        // Test admin-specific functionality
    }
}
```

---

## Testing Private Methods

### @TestVisible Annotation

```apex
public class MyService {
    @TestVisible
    private static String privateMethod(String input) {
        return input.toUpperCase();
    }
}

// Test can now access private method
@isTest
static void testPrivateMethod() {
    String result = MyService.privateMethod('test');
    Assert.areEqual('TEST', result);
}
```

---

## Test Checklist

| Scenario | Required |
|----------|----------|
| Positive test (happy path) | ✓ |
| Negative test (error handling) | ✓ |
| Bulk test (251+ records) | ✓ |
| Single record test | ✓ |
| Null/empty input | ✓ |
| Boundary conditions | ✓ |
| Different user profiles | ✓ |
| Assert statements in every test | ✓ |
| Test.startTest()/stopTest() for async | ✓ |
