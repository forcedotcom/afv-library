<!-- Parent: sf-apex/SKILL.md -->
# Apex Naming Conventions

## Classes

### Format: PascalCase

| Type | Convention | Example |
|------|------------|---------|
| Standard class | `[Domain]Service` | `AccountService` |
| Controller | `[Page]Controller` | `AccountPageController` |
| Extension | `[Page]ControllerExt` | `AccountControllerExt` |
| Trigger Action | `TA_[Object]_[Action]` | `TA_Account_SetDefaults` |
| Batch | `[Domain]_Batch` | `AccountCleanup_Batch` |
| Queueable | `[Domain]_Queueable` | `AccountSync_Queueable` |
| Schedulable | `[Domain]_Schedule` | `DailyReport_Schedule` |
| Selector | `[Object]Selector` | `AccountSelector` |
| Domain | `[Object]Domain` | `AccountDomain` |
| Test class | `[ClassName]Test` | `AccountServiceTest` |
| Test factory | `TestDataFactory` | `TestDataFactory` |
| Exception | `[Domain]Exception` | `InsufficientFundsException` |
| Interface | `I[Name]` or descriptive | `IPaymentProcessor` |

### Examples

```apex
public class AccountService { }
public class TA_Account_ValidateAddress implements TriggerAction.BeforeInsert { }
public class AccountCleanup_Batch implements Database.Batchable<SObject> { }
public class AccountSync_Queueable implements Queueable { }
public class AccountSelector { }
```

---

## Methods

### Format: camelCase, Start with Verb

| Purpose | Convention | Example |
|---------|------------|---------|
| Get data | `get[Noun]` | `getAccounts()` |
| Set data | `set[Noun]` | `setAccountStatus()` |
| Check condition | `is[Adjective]` / `has[Noun]` | `isActive()`, `hasPermission()` |
| Action | `[verb][Noun]` | `processOrders()`, `validateData()` |
| Calculate | `calculate[Noun]` | `calculateTotal()` |
| Create | `create[Noun]` | `createAccount()` |
| Update | `update[Noun]` | `updateStatus()` |
| Delete | `delete[Noun]` | `deleteRecords()` |

### Special Verbs

- Use `obtain` instead of `get` for expensive operations
- Use `specify` instead of `set` for configuration
- Reserve `get`/`set` for actual property getters/setters

```apex
// Good
public Account getAccount(Id accountId) { }
public void processRecords(List<Record__c> records) { }
public Boolean isEligible(Account acc) { }
public Decimal calculateTotalRevenue(List<Opportunity> opps) { }

// Better for expensive operations
public Account obtainAccountWithRelated(Id accountId) { }

// Boolean methods read as assertions
public Boolean hasActiveSubscription() { }
public Boolean canModifyRecord() { }
```

---

## Variables

### Format: camelCase, Descriptive

| Type | Convention | Example |
|------|------------|---------|
| Local variable | descriptive noun | `account`, `totalAmount` |
| Loop iterator | single letter (temp) | `i`, `j`, `k` |
| Boolean | `is[Adjective]` / `has[Noun]` | `isValid`, `hasError` |
| Collection | plural noun | `accounts`, `contactList` |
| Map | `[value]By[key]` | `accountsById`, `contactsByEmail` |
| Set | `[noun]Set` or `[noun]Ids` | `accountIds`, `processedIdSet` |

### Anti-Patterns to Avoid

```apex
// BAD: Abbreviations
String acct;      // What is this?
List<Task> tks;   // Unclear
SObject rec;      // Too generic

// GOOD: Descriptive names
String accountName;
List<Task> openTasks;
Account parentAccount;
```

### Collection Naming

```apex
// Lists - plural noun
List<Account> accounts;
List<Contact> relatedContacts;

// Sets - noun + Ids or noun + Set
Set<Id> accountIds;
Set<String> processedEmailSet;

// Maps - value + By + key description
Map<Id, Account> accountsById;
Map<String, List<Contact>> contactsByEmail;
Map<Id, Map<String, Decimal>> metricsByAccountByType;
```

---

## Constants

### Format: UPPER_SNAKE_CASE

```apex
public class Constants {
    public static final String STATUS_ACTIVE = 'Active';
    public static final String STATUS_INACTIVE = 'Inactive';
    public static final Integer MAX_RETRY_COUNT = 3;
    public static final Decimal TAX_RATE = 0.08;
}
```

---

## Custom Objects & Fields

### Format: Title_Case_With_Underscores

```apex
// Objects
Account_Score__c
Order_Line_Item__c

// Fields
Account_Status__c
Total_Revenue__c
Is_Primary__c

// Reference in code (use API names)
account.Account_Status__c = 'Active';
```

---

## Triggers

### Format: [ObjectName]Trigger

```apex
trigger AccountTrigger on Account (...) { }
trigger ContactTrigger on Contact (...) { }
trigger OpportunityTrigger on Opportunity (...) { }
```

---

## Test Classes

### Format: [TestedClassName]Test

```apex
// For AccountService.cls
@isTest
private class AccountServiceTest { }

// For TA_Account_SetDefaults.cls
@isTest
private class TA_Account_SetDefaultsTest { }
```

### Test Methods

```apex
// Format: test[Scenario]
@isTest
static void testPositiveScenario() { }

@isTest
static void testBulkInsert() { }

@isTest
static void testInvalidInput() { }

@isTest
static void testAsStandardUser() { }
```

---

## Quick Reference

| Element | Convention | Example |
|---------|------------|---------|
| Class | PascalCase | `AccountService` |
| Interface | I + PascalCase | `IPaymentProcessor` |
| Method | camelCase verb | `processRecords()` |
| Variable | camelCase noun | `accountList` |
| Constant | UPPER_SNAKE | `MAX_RETRIES` |
| Parameter | camelCase | `accountId` |
| Boolean | is/has prefix | `isActive` |
| Map | valueByKey | `accountsById` |
| Set | nounIds/nounSet | `accountIds` |
| List | plural noun | `accounts` |
| Trigger | ObjectTrigger | `AccountTrigger` |
| Trigger Action | TA_Object_Action | `TA_Account_Validate` |
| Batch | Domain_Batch | `Cleanup_Batch` |
| Test | ClassTest | `AccountServiceTest` |
