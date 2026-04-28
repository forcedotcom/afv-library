<!-- Parent: sf-apex/SKILL.md -->
# Code Smells & Refactoring Guide

> 💡 *Principles inspired by "Clean Apex Code" by Pablo Gonzalez.
> [Purchase the book](https://link.springer.com/book/10.1007/979-8-8688-1411-2) for complete coverage.*

## Overview

Code smells are patterns that indicate potential problems in code structure. This guide helps identify common smells in Apex and provides refactoring strategies.

---

## 1. Long Methods

### The Smell

Methods exceeding 20-30 lines, doing too much, hard to test in isolation.

### Signs

- Method name is vague (`processData`, `handleStuff`)
- Multiple levels of nesting
- Many local variables
- Comments separating "sections" of work

### Before

```apex
public void processOpportunity(Opportunity opp) {
    // Validate opportunity
    if (opp == null) {
        throw new IllegalArgumentException('Opportunity cannot be null');
    }
    if (opp.AccountId == null) {
        throw new IllegalArgumentException('Account is required');
    }
    if (opp.Amount == null || opp.Amount <= 0) {
        throw new IllegalArgumentException('Valid amount required');
    }

    // Calculate discount
    Account acc = [SELECT Type, AnnualRevenue FROM Account WHERE Id = :opp.AccountId];
    Decimal discountRate = 0;
    if (acc.Type == 'Enterprise') {
        if (acc.AnnualRevenue > 1000000) {
            discountRate = 0.20;
        } else {
            discountRate = 0.15;
        }
    } else if (acc.Type == 'Partner') {
        discountRate = 0.10;
    }
    opp.Discount__c = opp.Amount * discountRate;

    // Assign to team
    if (opp.Amount > 100000) {
        opp.OwnerId = getEnterpriseTeamQueue();
    } else if (opp.Amount > 25000) {
        opp.OwnerId = getMidMarketQueue();
    }

    // Send notifications
    if (discountRate > 0.15) {
        sendApprovalRequest(opp);
    }
    if (opp.Amount > 500000) {
        notifyExecutiveTeam(opp);
    }

    update opp;
}
```

### After

```apex
public void processOpportunity(Opportunity opp) {
    validateOpportunity(opp);

    Account account = getAccountForOpportunity(opp);
    applyDiscount(opp, account);
    assignToAppropriateTeam(opp);
    sendRequiredNotifications(opp);

    update opp;
}

private void validateOpportunity(Opportunity opp) {
    if (opp == null) {
        throw new IllegalArgumentException('Opportunity cannot be null');
    }
    if (opp.AccountId == null) {
        throw new IllegalArgumentException('Account is required');
    }
    if (opp.Amount == null || opp.Amount <= 0) {
        throw new IllegalArgumentException('Valid amount required');
    }
}

private Account getAccountForOpportunity(Opportunity opp) {
    return [SELECT Type, AnnualRevenue FROM Account WHERE Id = :opp.AccountId];
}

private void applyDiscount(Opportunity opp, Account account) {
    Decimal discountRate = DiscountRules.calculateRate(account);
    opp.Discount__c = opp.Amount * discountRate;
}

private void assignToAppropriateTeam(Opportunity opp) {
    opp.OwnerId = TeamAssignment.getQueueForAmount(opp.Amount);
}

private void sendRequiredNotifications(Opportunity opp) {
    NotificationService.sendIfRequired(opp);
}
```

### When to Extract

Extract a method when:
- The code block can be understood independently
- It doesn't require knowledge of the caller's implementation
- It serves a purpose beyond the immediate use case
- You find yourself writing a comment to explain what a section does

---

## 2. Mixed Abstraction Levels

### The Smell

A method mixing high-level orchestration with low-level implementation details.

### Signs

- Business logic alongside HTTP request building
- Validation mixed with string manipulation
- SOQL queries interspersed with notification logic

### Before

```apex
public void processNewCustomer(Account account) {
    // HIGH-LEVEL: Validation
    validateAccount(account);

    // LOW-LEVEL: String manipulation
    String sanitizedPhone = account.Phone.replaceAll('[^0-9]', '');
    if (sanitizedPhone.length() == 10) {
        sanitizedPhone = '1' + sanitizedPhone;
    }
    account.Phone = '+' + sanitizedPhone;

    // HIGH-LEVEL: Save
    insert account;

    // LOW-LEVEL: HTTP details
    HttpRequest req = new HttpRequest();
    req.setEndpoint('https://api.crm.com/customers');
    req.setMethod('POST');
    req.setHeader('Content-Type', 'application/json');
    req.setBody(JSON.serialize(account));
    Http http = new Http();
    HttpResponse res = http.send(req);

    // HIGH-LEVEL: Notification
    sendWelcomeEmail(account);
}
```

### After

```apex
public void processNewCustomer(Account account) {
    validateAccount(account);
    normalizePhoneNumber(account);
    insert account;
    syncToExternalCRM(account);
    sendWelcomeEmail(account);
}

private void normalizePhoneNumber(Account account) {
    if (String.isBlank(account.Phone)) return;

    String digitsOnly = account.Phone.replaceAll('[^0-9]', '');
    if (digitsOnly.length() == 10) {
        digitsOnly = '1' + digitsOnly;
    }
    account.Phone = '+' + digitsOnly;
}

private void syncToExternalCRM(Account account) {
    ExternalCRMService.syncCustomer(account);
}
```

### Principle

Each method should operate at **one level of abstraction**. High-level methods orchestrate; low-level methods implement.

---

## 3. Boolean Parameter Proliferation

### The Smell

Methods with multiple boolean parameters that control behavior.

### Signs

- Method calls like `process(acc, true, false, true)`
- Hard to remember which boolean does what
- Many if/else branches based on parameters

### Before

```apex
public void createCase(
    String subject,
    String description,
    Id accountId,
    Boolean sendEmail,
    Boolean highPriority,
    Boolean assignToQueue,
    String origin
) {
    Case c = new Case(Subject = subject, Description = description);
    if (highPriority) {
        c.Priority = 'High';
    }
    if (assignToQueue) {
        c.OwnerId = getDefaultQueue();
    }
    // ... more conditionals
}

// Caller - which boolean is which?
createCase('Issue', 'Desc', accId, true, false, true, 'Web');
```

### After: Options Object Pattern

```apex
public class CaseOptions {
    public Boolean sendEmail = false;
    public Boolean highPriority = false;
    public Boolean assignToQueue = true;
    public String origin = 'Web';

    public CaseOptions withEmail() {
        this.sendEmail = true;
        return this;
    }

    public CaseOptions withHighPriority() {
        this.highPriority = true;
        return this;
    }

    public CaseOptions withOrigin(String origin) {
        this.origin = origin;
        return this;
    }
}

public Case createCase(String subject, String description, Id accountId, CaseOptions options) {
    Case c = new Case(
        Subject = subject,
        Description = description,
        AccountId = accountId,
        Priority = options.highPriority ? 'High' : 'Medium',
        Origin = options.origin
    );

    if (options.assignToQueue) {
        c.OwnerId = getDefaultQueue();
    }

    insert c;

    if (options.sendEmail) {
        sendCaseConfirmation(c);
    }

    return c;
}

// Clear, self-documenting caller
Case newCase = createCase(
    'Login Issue',
    'Cannot access account',
    accountId,
    new CaseOptions()
        .withEmail()
        .withHighPriority()
        .withOrigin('Phone')
);
```

---

## 4. Magic Numbers and Strings

### The Smell

Hardcoded values scattered throughout code without explanation.

### Signs

- Numbers like `5`, `100`, `1000000` without context
- String literals like `'Enterprise'`, `'Active'`
- Same value repeated in multiple places

### Before

```apex
if (account.AnnualRevenue > 1000000) {
    if (retryCount < 5) {
        if (account.Type == 'Enterprise') {
            // process
        }
    }
}

// Elsewhere in code
if (customer.Revenue__c > 1000000) { }  // Same threshold, different field
```

### After

```apex
public class AccountConstants {
    public static final Decimal HIGH_VALUE_THRESHOLD = 1000000;
    public static final Integer MAX_RETRY_ATTEMPTS = 5;
    public static final String TYPE_ENTERPRISE = 'Enterprise';
    public static final String TYPE_PARTNER = 'Partner';
    public static final String STATUS_ACTIVE = 'Active';
}

// Usage
if (account.AnnualRevenue > AccountConstants.HIGH_VALUE_THRESHOLD) {
    if (retryCount < AccountConstants.MAX_RETRY_ATTEMPTS) {
        if (account.Type == AccountConstants.TYPE_ENTERPRISE) {
            // process
        }
    }
}
```

### Benefits

- Single source of truth
- Self-documenting code
- Easy to change values globally
- Prevents typos in string literals

---

## 5. Complex Conditionals

### The Smell

Long, nested boolean expressions that are hard to understand.

### Signs

- Multiple `&&` and `||` in one expression
- Negations of negations
- Conditions spanning multiple lines without names

### Before

```apex
if (account.Type == 'Enterprise' &&
    account.AnnualRevenue > 1000000 &&
    account.NumberOfEmployees > 500 &&
    (account.Industry == 'Technology' || account.Industry == 'Finance') &&
    account.BillingCountry == 'United States' &&
    account.Rating == 'Hot') {
    // 50 lines of logic
}
```

### Step 1: Named Boolean Variables

_Improves readability by naming each condition, but the logic still sits inline — the reader must parse it even if they don't care about the details._

```apex
Boolean isEnterpriseCustomer = account.Type == 'Enterprise';
Boolean isHighValue = account.AnnualRevenue > 1000000;
Boolean isLargeCompany = account.NumberOfEmployees > 500;
Boolean isTargetIndustry = account.Industry == 'Technology' ||
                           account.Industry == 'Finance';
Boolean isDomestic = account.BillingCountry == 'United States';
Boolean isHotLead = account.Rating == 'Hot';

Boolean isStrategicAccount = isEnterpriseCustomer &&
                              isHighValue &&
                              isLargeCompany &&
                              isTargetIndustry &&
                              isDomestic &&
                              isHotLead;

if (isStrategicAccount) {
    processStrategicAccount(account);
}
```

### Step 2: Extract Method (Recommended)

_Move the decision behind a single descriptive method name. Callers see **what** is being checked; only maintainers who open the method see **how**._

```apex
// In the same class — no new file needed
private Boolean isStrategicAccount(Account account) {
    Boolean isEnterpriseCustomer = account.Type == 'Enterprise';
    Boolean isHighValue = account.AnnualRevenue > 1000000;
    Boolean isLargeCompany = account.NumberOfEmployees > 500;
    Boolean isTargetIndustry = account.Industry == 'Technology' ||
                               account.Industry == 'Finance';
    Boolean isDomestic = account.BillingCountry == 'United States';
    Boolean isHotLead = account.Rating == 'Hot';

    return isEnterpriseCustomer && isHighValue && isLargeCompany &&
           isTargetIndustry && isDomestic && isHotLead;
}

// Clean call site — one line, self-documenting
if (isStrategicAccount(account)) {
    processStrategicAccount(account);
}
```

### Step 3: Domain Rules Class

_Best for rules reused across triggers, batch jobs, and flows._

```apex
// Reusable business rules
public class AccountRules {
    public static Boolean isStrategicAccount(Account account) {
        return isEnterpriseCustomer(account) &&
               isHighValue(account) &&
               isInTargetMarket(account);
    }

    public static Boolean isEnterpriseCustomer(Account account) {
        return account.Type == 'Enterprise' &&
               account.NumberOfEmployees > 500;
    }

    public static Boolean isHighValue(Account account) {
        return account.AnnualRevenue != null &&
               account.AnnualRevenue > 1000000;
    }

    public static Boolean isInTargetMarket(Account account) {
        Set<String> targetIndustries = new Set<String>{'Technology', 'Finance'};
        return targetIndustries.contains(account.Industry) &&
               account.BillingCountry == 'United States';
    }
}

// Clean usage
if (AccountRules.isStrategicAccount(account)) {
    processStrategicAccount(account);
}
```

---

## 6. Duplicate Code

### The Smell

Same or similar code repeated in multiple places.

### Signs

- Copy-paste patterns
- Same SOQL query in multiple methods
- Similar validation logic across classes

### Before

```apex
// In AccountService
public void processAccount(Id accountId) {
    Account acc = [
        SELECT Id, Name, Type, Industry, AnnualRevenue, OwnerId
        FROM Account
        WHERE Id = :accountId
    ];
    // process
}

// In ReportingService
public void generateReport(Id accountId) {
    Account acc = [
        SELECT Id, Name, Type, Industry, AnnualRevenue, OwnerId
        FROM Account
        WHERE Id = :accountId
    ];
    // generate
}

// In IntegrationService
public void syncAccount(Id accountId) {
    Account acc = [
        SELECT Id, Name, Type, Industry, AnnualRevenue, OwnerId
        FROM Account
        WHERE Id = :accountId
    ];
    // sync
}
```

### After: Selector Pattern

```apex
public class AccountSelector {
    private static final Set<String> STANDARD_FIELDS = new Set<String>{
        'Id', 'Name', 'Type', 'Industry', 'AnnualRevenue', 'OwnerId'
    };

    public Account selectById(Id accountId) {
        List<Account> accounts = selectByIds(new Set<Id>{accountId});
        return accounts.isEmpty() ? null : accounts[0];
    }

    public List<Account> selectByIds(Set<Id> accountIds) {
        if (accountIds == null || accountIds.isEmpty()) {
            return new List<Account>();
        }
        return [
            SELECT Id, Name, Type, Industry, AnnualRevenue, OwnerId
            FROM Account
            WHERE Id IN :accountIds
        ];
    }
}

// All services use the selector
AccountSelector selector = new AccountSelector();
Account acc = selector.selectById(accountId);
```

---

## 7. Deep Nesting

### The Smell

Code with many levels of indentation, often from nested if statements.

### Signs

- 4+ levels of nesting
- Business logic hidden deep in conditionals
- Hard to follow execution flow

### Solution: Guard Clauses

See [Best Practices: Guard Clauses](best-practices.md#10-guard-clauses--fail-fast) for detailed refactoring patterns.

---

## 8. God Class

### The Smell

A class that knows too much or does too much.

### Signs

- Hundreds or thousands of lines
- Many unrelated methods
- Class name is vague (`Utility`, `Helper`, `Manager`)
- Changes to any feature require modifying this class

### Solution

Split by responsibility:
- Extract domain classes for business rules
- Create selectors for data access
- Separate services for different business operations
- Use interfaces for dependency injection

See [Design Patterns: Domain Class Pattern](design-patterns.md#domain-class-pattern) for implementation guidance.

---

## Refactoring Decision Guide

| Smell | Quick Fix | Proper Fix |
|-------|-----------|------------|
| Long method | Extract method | Separate concerns into classes |
| Mixed abstraction | Extract low-level to methods | Create abstraction layers |
| Boolean parameters | Options object | Strategy pattern |
| Magic numbers | Named constants | Configuration class |
| Complex conditionals | Named booleans | Domain class |
| Duplicate code | Extract method | Selector/Service pattern |
| Deep nesting | Guard clauses | Command pattern |
| God class | Split methods | Proper architecture |

---

## When NOT to Refactor

- **Working code under deadline**: Don't refactor what you don't have time to test
- **No tests exist**: Write tests first, then refactor
- **Code is being deprecated**: Don't polish what's being removed
- **Premature abstraction**: Wait until you have 3 concrete examples before abstracting

---

## Testing After Refactoring

Every refactoring should be validated:

1. **Run existing tests** - They should still pass
2. **Check code coverage** - Coverage shouldn't drop
3. **Verify behavior** - Same inputs produce same outputs
4. **Performance check** - No significant degradation

If tests fail after refactoring that shouldn't change behavior, you've introduced a bug, not just refactored.
