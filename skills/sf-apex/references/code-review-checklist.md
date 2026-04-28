<!-- Parent: sf-apex/SKILL.md -->
# Apex Code Review Checklist

## Critical Issues (Must Fix)

### Bulkification

| Check | Status |
|-------|--------|
| No SOQL queries inside loops | ☐ |
| No DML statements inside loops | ☐ |
| Uses collections (List, Set, Map) properly | ☐ |
| Handles 200+ records per trigger batch | ☐ |
| Test class includes bulk test (251+ records) | ☐ |

**Anti-Pattern:**
```apex
// BAD
for (Account acc : accounts) {
    Contact c = [SELECT Id FROM Contact WHERE AccountId = :acc.Id];
    update c;
}
```

**Fix:**
```apex
// GOOD
Set<Id> accountIds = new Map<Id, Account>(accounts).keySet();
List<Contact> contacts = [SELECT Id, AccountId FROM Contact WHERE AccountId IN :accountIds];
update contacts;
```

---

### Security

| Check | Status |
|-------|--------|
| Uses `WITH USER_MODE` for SOQL | ☐ |
| Uses bind variables (no SOQL injection) | ☐ |
| Uses `with sharing` by default | ☐ |
| `without sharing` justified and documented | ☐ |
| No hardcoded credentials | ☐ |
| No hardcoded Record IDs | ☐ |
| Named Credentials used for callouts | ☐ |

**Anti-Pattern:**
```apex
// BAD
String query = 'SELECT Id FROM Account WHERE Name = \'' + userInput + '\'';
```

**Fix:**
```apex
// GOOD
String query = 'SELECT Id FROM Account WHERE Name = :userInput';
List<Account> accounts = Database.query(query);
```

---

### Testing

| Check | Status |
|-------|--------|
| Test class exists | ☐ |
| Coverage > 75% (90%+ recommended) | ☐ |
| Uses Assert class (not System.assert) | ☐ |
| Assert in every test method | ☐ |
| Tests positive scenario | ☐ |
| Tests negative scenario (error handling) | ☐ |
| Tests bulk scenario (251+ records) | ☐ |
| Uses `Test.startTest()`/`Test.stopTest()` for async | ☐ |
| Uses `seeAllData=false` | ☐ |
| Uses Test Data Factory pattern | ☐ |

**Anti-Pattern:**
```apex
// BAD: No assertion
@isTest
static void testMethod() {
    Account acc = new Account(Name = 'Test');
    insert acc;
    // No assert!
}
```

**Fix:**
```apex
// GOOD
@isTest
static void testAccountInsert() {
    Account acc = new Account(Name = 'Test');

    Test.startTest();
    insert acc;
    Test.stopTest();

    Account result = [SELECT Name FROM Account WHERE Id = :acc.Id];
    Assert.areEqual('Test', result.Name, 'Name should match');
}
```

---

## Important Issues (Should Fix)

### Architecture

| Check | Status |
|-------|--------|
| One trigger per object | ☐ |
| Uses Trigger Actions Framework (or similar) | ☐ |
| Logic-less triggers (delegates to handler) | ☐ |
| Service layer for business logic | ☐ |
| Selector pattern for queries | ☐ |
| Single responsibility per class | ☐ |

**Anti-Pattern:**
```apex
// BAD: Logic in trigger
trigger AccountTrigger on Account (before insert) {
    for (Account acc : Trigger.new) {
        if (acc.Industry == null) {
            acc.Industry = 'Other';
        }
        // 100 more lines of logic...
    }
}
```

**Fix:**
```apex
// GOOD: Delegate to framework
trigger AccountTrigger on Account (before insert, after insert, ...) {
    new MetadataTriggerHandler().run();
}
```

---

### Error Handling

| Check | Status |
|-------|--------|
| Catches specific exceptions before generic | ☐ |
| No empty catch blocks | ☐ |
| Errors logged appropriately | ☐ |
| Uses `AuraHandledException` for LWC | ☐ |
| Custom exceptions for business logic | ☐ |

**Anti-Pattern:**
```apex
// BAD
try {
    insert accounts;
} catch (Exception e) {
    // Silent failure
}
```

**Fix:**
```apex
// GOOD
try {
    insert accounts;
} catch (DmlException e) {
    for (Integer i = 0; i < e.getNumDml(); i++) {
        System.debug(LoggingLevel.ERROR, 'DML Error: ' + e.getDmlMessage(i));
    }
    throw new AccountServiceException('Failed to insert accounts: ' + e.getMessage());
}
```

---

### Naming

| Check | Status |
|-------|--------|
| Class names are PascalCase | ☐ |
| Method names are camelCase verbs | ☐ |
| Variable names are descriptive | ☐ |
| No abbreviations (tks, rec, acc) | ☐ |
| Constants are UPPER_SNAKE_CASE | ☐ |
| Collections indicate type (accountsById) | ☐ |

---

### Performance

| Check | Status |
|-------|--------|
| Uses `Limits` class to monitor | ☐ |
| Caches expensive operations | ☐ |
| Heavy processing in async | ☐ |
| SOQL filters on indexed fields | ☐ |
| Variables go out of scope (heap) | ☐ |
| No class-level large collections | ☐ |

---

## Minor Issues (Nice to Fix)

### Clean Code

| Check | Status |
|-------|--------|
| No double negatives (`!= false`) | ☐ |
| Boolean conditions extracted to variables | ☐ |
| Methods do one thing | ☐ |
| No side effects in methods | ☐ |
| Consistent formatting | ☐ |
| ApexDoc comments on public methods | ☐ |

---

### Common Anti-Patterns Quick Reference

| Anti-Pattern | Fix |
|--------------|-----|
| SOQL in loop | Query before loop, use Map |
| DML in loop | Collect in loop, DML after |
| `without sharing` everywhere | `with sharing` default |
| Multiple triggers per object | One trigger + TAF |
| SOQL without WHERE/LIMIT | Always filter |
| `isEmpty()` before DML | Remove (empty = 0 DMLs) |
| Generic Exception only | Catch specific first |
| Hard-coded IDs | Query dynamically |
| No Test Data Factory | Create factory class |
| `System.debug` everywhere | Use Custom Metadata toggle |
| No trigger bypass | Boolean Custom Setting |
| Exactly 75% coverage | Aim for 90%+ |
| No assertions in tests | Assert in every test |
| Public Read/Write OWD | Private + sharing rules |

---

## Review Process

1. **Static Analysis**: Run PMD, check code coverage
2. **Bulkification**: Verify no SOQL/DML in loops
3. **Security**: Check sharing, CRUD/FLS, injection
4. **Testing**: Review test coverage and quality
5. **Architecture**: Verify patterns and separation
6. **Naming**: Check conventions
7. **Performance**: Review limits awareness
8. **Documentation**: Verify ApexDoc comments

---

## Scoring

| Category | Weight |
|----------|--------|
| Critical (Bulkification, Security, Testing) | 75 points |
| Important (Architecture, Error Handling, Naming) | 55 points |
| Minor (Clean Code, Performance, Docs) | 20 points |
| **Total** | **150 points** |

**Pass Threshold**: 90+ points (no critical issues)
