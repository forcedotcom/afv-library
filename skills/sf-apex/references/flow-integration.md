<!-- Parent: sf-apex/SKILL.md -->
# Apex Flow Integration Guide

This guide covers creating Apex classes callable from Salesforce Flows using `@InvocableMethod` and `@InvocableVariable`.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FLOW → APEX INTEGRATION                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────┐     actionCalls      ┌─────────────────────┐     │
│   │    Flow     │ ─────────────────────▶ │  @InvocableMethod   │     │
│   │   Action    │                       │  Apex Class          │     │
│   └─────────────┘ ◀───────────────────── └─────────────────────┘     │
│                      Response                                        │
│                                                                      │
│   Input Variables ────▶ Request Wrapper ────▶ Business Logic        │
│   Output Variables ◀──── Response Wrapper ◀──── Return Values       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quick Reference

| Annotation | Purpose | Required |
|------------|---------|----------|
| `@InvocableMethod` | Marks method as Flow-callable | Yes |
| `@InvocableVariable` | Marks property as Flow parameter | Yes (for wrappers) |

---

## @InvocableMethod Decorator

### Syntax

```apex
@InvocableMethod(
    label='Display Name in Flow'
    description='Explanation shown in Flow Builder'
    category='Category for grouping'
    callout=true  // If method makes HTTP callouts
)
public static List<Response> execute(List<Request> requests) {
    // Implementation
}
```

### Parameters

| Parameter | Description | Required |
|-----------|-------------|----------|
| `label` | Display name in Flow Builder action list | Yes |
| `description` | Help text shown when configuring action | No |
| `category` | Groups actions in Flow Builder | No |
| `callout` | Set `true` if method makes HTTP callouts | No (default: false) |
| `configurationEditor` | Custom LWC for configuration UI | No |

### Method Signature Rules

```apex
// ✅ CORRECT: Static, List input, List output
public static List<Response> execute(List<Request> requests)

// ❌ WRONG: Non-static method
public List<Response> execute(List<Request> requests)

// ❌ WRONG: Single object (not List)
public static Response execute(Request request)

// ✅ CORRECT: Simple types also allowed
public static List<String> execute(List<Id> recordIds)
```

---

## @InvocableVariable Decorator

### Syntax

```apex
public class Request {
    @InvocableVariable(
        label='Record ID'
        description='The ID of the record to process'
        required=true
    )
    public Id recordId;
}
```

### Parameters

| Parameter | Description | Required |
|-----------|-------------|----------|
| `label` | Display name in Flow mapping UI | Yes |
| `description` | Help text for the variable | No |
| `required` | Whether Flow must provide a value | No (default: false) |

### Supported Data Types

| Type | Flow Equivalent | Notes |
|------|-----------------|-------|
| `Boolean` | Boolean | |
| `Date` | Date | |
| `DateTime` | DateTime | |
| `Decimal` | Number | |
| `Double` | Number | |
| `Integer` | Number | |
| `Long` | Number | |
| `String` | Text | |
| `Time` | Time | |
| `Id` | Text (Record ID) | Stores as 18-char ID |
| `SObject` | Record | Any standard/custom object |
| `List<T>` | Collection | Collection of any above type |

---

## Request/Response Pattern

The recommended pattern uses wrapper classes for clean data exchange:

```apex
public class AccountProcessorInvocable {

    @InvocableMethod(label='Process Account' category='Account')
    public static List<Response> execute(List<Request> requests) {
        List<Response> responses = new List<Response>();

        for (Request req : requests) {
            Response res = new Response();
            try {
                // Process the request
                res = processRequest(req);
            } catch (Exception e) {
                res.isSuccess = false;
                res.errorMessage = e.getMessage();
            }
            responses.add(res);
        }

        return responses;
    }

    private static Response processRequest(Request req) {
        // Business logic here
        Response res = new Response();
        res.isSuccess = true;
        res.outputMessage = 'Processed successfully';
        return res;
    }

    // ═══════════════════════════════════════════════════════════════
    // REQUEST WRAPPER
    // ═══════════════════════════════════════════════════════════════
    public class Request {
        @InvocableVariable(label='Account ID' required=true)
        public Id accountId;

        @InvocableVariable(label='Operation Type')
        public String operation;
    }

    // ═══════════════════════════════════════════════════════════════
    // RESPONSE WRAPPER
    // ═══════════════════════════════════════════════════════════════
    public class Response {
        @InvocableVariable(label='Is Success')
        public Boolean isSuccess;

        @InvocableVariable(label='Error Message')
        public String errorMessage;

        @InvocableVariable(label='Output Message')
        public String outputMessage;

        @InvocableVariable(label='Result Record ID')
        public Id outputRecordId;
    }
}
```

---

## Bulkification Best Practices

Flows can invoke your method with multiple records. Always bulkify:

```apex
@InvocableMethod(label='Update Accounts' category='Account')
public static List<Response> execute(List<Request> requests) {
    List<Response> responses = new List<Response>();

    // ─────────────────────────────────────────────────────────────
    // STEP 1: Collect all IDs first (avoid SOQL in loop)
    // ─────────────────────────────────────────────────────────────
    Set<Id> accountIds = new Set<Id>();
    for (Request req : requests) {
        if (req.accountId != null) {
            accountIds.add(req.accountId);
        }
    }

    // ─────────────────────────────────────────────────────────────
    // STEP 2: Single bulk query with USER_MODE
    // ─────────────────────────────────────────────────────────────
    Map<Id, Account> accountsById = new Map<Id, Account>(
        [SELECT Id, Name, Industry, AnnualRevenue
         FROM Account
         WHERE Id IN :accountIds
         WITH USER_MODE]
    );

    // ─────────────────────────────────────────────────────────────
    // STEP 3: Collect DML records
    // ─────────────────────────────────────────────────────────────
    List<Account> accountsToUpdate = new List<Account>();

    for (Request req : requests) {
        Response res = new Response();
        Account acc = accountsById.get(req.accountId);

        if (acc == null) {
            res.isSuccess = false;
            res.errorMessage = 'Account not found: ' + req.accountId;
        } else {
            // Process and collect for bulk DML
            acc.Description = 'Processed via Flow';
            accountsToUpdate.add(acc);
            res.isSuccess = true;
            res.outputRecordId = acc.Id;
        }

        responses.add(res);
    }

    // ─────────────────────────────────────────────────────────────
    // STEP 4: Single bulk DML operation
    // ─────────────────────────────────────────────────────────────
    if (!accountsToUpdate.isEmpty()) {
        update accountsToUpdate;
    }

    return responses;
}
```

---

## Error Handling

### Return Errors to Flow (Recommended)

```apex
public class Response {
    @InvocableVariable(label='Is Success')
    public Boolean isSuccess;

    @InvocableVariable(label='Error Message')
    public String errorMessage;

    @InvocableVariable(label='Error Type')
    public String errorType;
}

// In your method:
try {
    // Business logic
    res.isSuccess = true;
} catch (DmlException e) {
    res.isSuccess = false;
    res.errorMessage = e.getDmlMessage(0);
    res.errorType = 'DmlException';
} catch (Exception e) {
    res.isSuccess = false;
    res.errorMessage = e.getMessage();
    res.errorType = e.getTypeName();
}
```

### Throw Exception (Flow Fault Path)

```apex
// Throwing an exception triggers the Flow's Fault path
@InvocableMethod(label='Process Account')
public static List<Response> execute(List<Request> requests) {
    if (requests.isEmpty()) {
        throw new InvocableException('No requests provided');
    }
    // ...
}

public class InvocableException extends Exception {}
```

**Flow Fault Connector:**
```xml
<actionCalls>
    <name>Call_Apex</name>
    <faultConnector>
        <targetReference>Handle_Error</targetReference>
    </faultConnector>
    <!-- ... -->
</actionCalls>
```

---

## Working with Collections

### Accept Collection Input

```apex
public class Request {
    @InvocableVariable(label='Account IDs' required=true)
    public List<Id> accountIds;  // Flow passes a collection
}
```

### Return Collection Output

```apex
public class Response {
    @InvocableVariable(label='Processed Accounts')
    public List<Account> accounts;  // Flow receives a collection
}
```

### Collection Iteration in Flow

When your invocable returns a List inside the Response, Flow can:
1. Use it directly in data tables
2. Loop over it with a Loop element
3. Pass it to another invocable action

---

## Security Considerations

### FLS/CRUD Enforcement

```apex
// Use USER_MODE for automatic FLS/CRUD checks
Map<Id, Account> accounts = new Map<Id, Account>(
    [SELECT Id, Name FROM Account WHERE Id IN :ids WITH USER_MODE]
);

// Or use Security.stripInaccessible for DML
SObjectAccessDecision decision = Security.stripInaccessible(
    AccessType.CREATABLE,
    accounts
);
insert decision.getRecords();
```

### with sharing

```apex
// Always use 'with sharing' unless there's a specific reason not to
public with sharing class AccountInvocable {
    // Respects org-wide defaults and sharing rules
}
```

---

## Testing Invocable Methods

```apex
@IsTest
private class AccountInvocableTest {

    @IsTest
    static void testSuccessScenario() {
        // Setup test data
        Account testAccount = new Account(Name = 'Test Account');
        insert testAccount;

        // Create request
        AccountInvocable.Request req = new AccountInvocable.Request();
        req.accountId = testAccount.Id;
        req.operation = 'process';

        // Execute
        Test.startTest();
        List<AccountInvocable.Response> responses =
            AccountInvocable.execute(new List<AccountInvocable.Request>{ req });
        Test.stopTest();

        // Verify
        System.assertEquals(1, responses.size(), 'Should return one response');
        System.assertEquals(true, responses[0].isSuccess, 'Should succeed');
        System.assertNotEquals(null, responses[0].outputRecordId, 'Should return record ID');
    }

    @IsTest
    static void testBulkExecution() {
        // Test with multiple records to verify bulkification
        List<Account> accounts = new List<Account>();
        for (Integer i = 0; i < 200; i++) {
            accounts.add(new Account(Name = 'Test ' + i));
        }
        insert accounts;

        List<AccountInvocable.Request> requests = new List<AccountInvocable.Request>();
        for (Account acc : accounts) {
            AccountInvocable.Request req = new AccountInvocable.Request();
            req.accountId = acc.Id;
            requests.add(req);
        }

        Test.startTest();
        List<AccountInvocable.Response> responses = AccountInvocable.execute(requests);
        Test.stopTest();

        System.assertEquals(200, responses.size(), 'Should handle bulk records');
        for (AccountInvocable.Response res : responses) {
            System.assertEquals(true, res.isSuccess, 'All should succeed');
        }
    }

    @IsTest
    static void testErrorHandling() {
        // Test with invalid ID
        AccountInvocable.Request req = new AccountInvocable.Request();
        req.accountId = '001000000000000AAA';  // Non-existent ID

        Test.startTest();
        List<AccountInvocable.Response> responses =
            AccountInvocable.execute(new List<AccountInvocable.Request>{ req });
        Test.stopTest();

        System.assertEquals(false, responses[0].isSuccess, 'Should fail for invalid ID');
        System.assertNotEquals(null, responses[0].errorMessage, 'Should have error message');
    }
}
```

---

## Flow XML Reference

When your Invocable is deployed, Flows call it like this:

```xml
<actionCalls>
    <name>Process_Account</name>
    <label>Process Account</label>
    <actionName>AccountProcessorInvocable</actionName>
    <actionType>apex</actionType>
    <connector>
        <targetReference>Next_Element</targetReference>
    </connector>
    <faultConnector>
        <targetReference>Error_Handler</targetReference>
    </faultConnector>

    <!-- Map Flow variable to Apex Request property -->
    <inputParameters>
        <name>accountId</name>
        <value>
            <elementReference>recordId</elementReference>
        </value>
    </inputParameters>

    <!-- Map Apex Response property to Flow variable -->
    <outputParameters>
        <assignToReference>isSuccess</assignToReference>
        <name>isSuccess</name>
    </outputParameters>
    <outputParameters>
        <assignToReference>errorMessage</assignToReference>
        <name>errorMessage</name>
    </outputParameters>
</actionCalls>
```

---

## Cross-Skill Integration

| Integration | See Also |
|-------------|----------|
| Flow → LWC → Apex | [triangle-pattern.md](triangle-pattern.md) |
| Apex → LWC | via @AuraEnabled controller pattern |
| Agentforce Actions | sf-ai-agentscript skill (similar pattern for agent actions) |

---

## Template

Use the template at `assets/invocable-method.cls` as a starting point.
