<!-- Parent: sf-apex/SKILL.md -->
# Flow-LWC-Apex Triangle: Apex Perspective

The **Triangle Architecture** is a foundational Salesforce pattern where Flow, LWC, and Apex work together. This guide focuses on the **Apex role** in this architecture.

---

## Architecture Overview

```
                         ┌─────────────────────────────────────┐
                         │              FLOW                   │
                         │         (Orchestrator)              │
                         └───────────────┬─────────────────────┘
                                         │
              ┌──────────────────────────┼──────────────────────────┐
              │                          │                          │
              │ screens                  │ actionCalls              │
              │ <componentInstance>      │ actionType="apex"        │
              │                          │                          │
              ▼                          ▼                          ▲
┌─────────────────────────┐    ┌─────────────────────────┐         │
│          LWC            │    │         APEX            │         │
│     (UI Component)      │───▶│   (Business Logic)      │─────────┘
│                         │    │                         │
│ • Rich UI/UX            │    │ • @InvocableMethod  ◀── YOU ARE HERE
│ • User Interaction      │    │ • @AuraEnabled          │
│                         │    │ • Complex Logic         │
│                         │    │ • DML Operations        │
│                         │    │ • Integration           │
└─────────────────────────┘    └─────────────────────────┘
              │                          ▲
              │      @AuraEnabled        │
              │      wire / imperative   │
              └──────────────────────────┘
```

---

## Apex's Role in the Triangle

| Communication Path | Apex Annotation | Direction |
|-------------------|-----------------|-----------|
| Flow → Apex | `@InvocableMethod` | Request/Response |
| Apex → Flow | `@InvocableVariable` | Return values |
| LWC → Apex | `@AuraEnabled` | Async call |
| Apex → LWC | Return value | Response |

---

## Pattern 1: @InvocableMethod for Flow

**Use Case**: Complex business logic, DML, or external integrations called from Flow.

```
┌─────────┐   actionCalls    ┌─────────┐
│  FLOW   │ ───────────────▶ │  APEX   │
│ Auto-   │   List<Request>  │Invocable│
│ mation  │ ◀─────────────── │ Method  │
│         │   List<Response> │         │
└─────────┘                  └─────────┘
```

### Apex Class Pattern

```apex
public with sharing class RecordProcessor {

    @InvocableMethod(label='Process Record' category='Custom')
    public static List<Response> execute(List<Request> requests) {
        List<Response> responses = new List<Response>();

        for (Request req : requests) {
            Response res = new Response();
            try {
                // Business logic here
                res.isSuccess = true;
                res.processedId = req.recordId;
            } catch (Exception e) {
                res.isSuccess = false;
                res.errorMessage = e.getMessage();
            }
            responses.add(res);
        }
        return responses;
    }

    public class Request {
        @InvocableVariable(required=true)
        public Id recordId;
    }

    public class Response {
        @InvocableVariable
        public Boolean isSuccess;
        @InvocableVariable
        public Id processedId;
        @InvocableVariable
        public String errorMessage;
    }
}
```

### Corresponding Flow XML

```xml
<actionCalls>
    <name>Process_Records</name>
    <actionName>RecordProcessor</actionName>
    <actionType>apex</actionType>
    <inputParameters>
        <name>recordId</name>
        <value><elementReference>var_RecordId</elementReference></value>
    </inputParameters>
    <outputParameters>
        <assignToReference>var_IsSuccess</assignToReference>
        <name>isSuccess</name>
    </outputParameters>
    <faultConnector>
        <targetReference>Handle_Error</targetReference>
    </faultConnector>
</actionCalls>
```

---

## Pattern 2: @AuraEnabled for LWC

**Use Case**: LWC needs data or operations beyond Flow context.

```
┌─────────┐     @wire         ┌─────────┐
│   LWC   │ ────────────────▶ │  APEX   │
│         │    imperative     │@Aura    │
│         │ ◀──────────────── │Enabled  │
│         │   Promise/data    │         │
└─────────┘                   └─────────┘
```

### Apex Controller

```apex
public with sharing class RecordController {

    @AuraEnabled(cacheable=true)
    public static List<Record__c> getRecords(Id parentId) {
        return [
            SELECT Id, Name, Status__c
            FROM Record__c
            WHERE Parent__c = :parentId
            WITH USER_MODE
        ];
    }

    @AuraEnabled
    public static Map<String, Object> processRecord(Id recordId) {
        // Process logic (DML operations)
        return new Map<String, Object>{
            'isSuccess' => true,
            'recordId' => recordId
        };
    }
}
```

### Key Differences

| Annotation | Cacheable | Use For |
|------------|-----------|---------|
| `@AuraEnabled(cacheable=true)` | Yes | Read-only queries (SOQL) |
| `@AuraEnabled` | No | DML operations, mutations |

---

## Testing @InvocableMethod

```apex
@isTest
private class RecordProcessorTest {
    @isTest
    static void testProcessRecords() {
        Account acc = new Account(Name = 'Test');
        insert acc;

        RecordProcessor.Request req = new RecordProcessor.Request();
        req.recordId = acc.Id;

        Test.startTest();
        List<RecordProcessor.Response> responses =
            RecordProcessor.execute(new List<RecordProcessor.Request>{ req });
        Test.stopTest();

        System.assertEquals(true, responses[0].isSuccess);
        System.assertEquals(acc.Id, responses[0].processedId);
    }

    @isTest
    static void testBulkProcessing() {
        // Test with 200+ records for bulkification
        List<Account> accounts = new List<Account>();
        for (Integer i = 0; i < 251; i++) {
            accounts.add(new Account(Name = 'Test ' + i));
        }
        insert accounts;

        List<RecordProcessor.Request> requests = new List<RecordProcessor.Request>();
        for (Account acc : accounts) {
            RecordProcessor.Request req = new RecordProcessor.Request();
            req.recordId = acc.Id;
            requests.add(req);
        }

        Test.startTest();
        List<RecordProcessor.Response> responses = RecordProcessor.execute(requests);
        Test.stopTest();

        System.assertEquals(251, responses.size());
    }
}
```

---

## Deployment Order

When deploying integrated triangle solutions:

```
1. APEX CLASSES         ← Deploy FIRST
   └── @InvocableMethod classes
   └── @AuraEnabled controllers

2. LWC COMPONENTS
   └── Depend on Apex controllers

3. FLOWS
   └── Reference deployed Apex classes
   └── Reference deployed LWC components
```

---

## Common Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Non-bulkified Invocable | Fails for multi-record Flows | Use `List<Request>` → `List<Response>` |
| Missing faultConnector handling | Exceptions crash Flow | Return error in Response, add fault path |
| Cacheable method with DML | Runtime error | Remove `cacheable=true` for mutations |
| Mixing concerns | Hard to test | Separate controller (LWC) from service (Flow) classes |

---

## Decision Matrix

| Scenario | Use @InvocableMethod | Use @AuraEnabled |
|----------|---------------------|------------------|
| Called from Flow | ✅ | ❌ |
| Called from LWC | ❌ | ✅ |
| Needs bulkification | ✅ (always bulk) | Optional |
| Read-only query | Either | ✅ (cacheable) |
| DML operations | ✅ | ✅ |
| External callout | ✅ | ✅ |

---

## Related Documentation

| Topic | Location |
|-------|----------|
| @InvocableMethod templates | `sf-apex/assets/invocable-method.cls` |
| Flow integration guide | `sf-apex/references/flow-integration.md` |
| LWC triangle perspective | `sf-lwc/references/triangle-pattern.md` |
| Flow triangle perspective | `sf-flow/references/triangle-pattern.md` |
