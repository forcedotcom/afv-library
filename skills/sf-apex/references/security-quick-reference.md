<!-- Parent: sf-apex/SKILL.md -->
# Apex Security Guide

## Sharing Modes

### with sharing (Default)

Use for most classes. Enforces record-level security (OWD, sharing rules).

```apex
public with sharing class AccountService {
    public List<Account> getAccounts() {
        // Only returns records user has access to
        return [SELECT Id, Name FROM Account];
    }
}
```

### inherited sharing

Use for utility/helper classes. Inherits sharing mode from caller.

```apex
public inherited sharing class QueryHelper {
    public static List<SObject> query(String soql) {
        // Sharing determined by calling class
        return Database.query(soql);
    }
}
```

### without sharing

Use sparingly. Only for specific system operations that require full access.

```apex
public without sharing class SystemService {
    // DOCUMENT WHY this needs without sharing
    public static void updateSystemRecords(List<Record__c> records) {
        // Updates regardless of sharing rules
        update records;
    }
}
```

**Rule**: Keep `without sharing` classes small and isolated. Never expose directly to users.

---

## CRUD/FLS Enforcement

### USER_MODE (Recommended)

```apex
// SOQL with USER_MODE - enforces CRUD and FLS
List<Account> accounts = [
    SELECT Id, Name, AnnualRevenue
    FROM Account
    WITH USER_MODE
];

// Database methods with AccessLevel
Database.insert(records, AccessLevel.USER_MODE);
Database.update(records, AccessLevel.USER_MODE);
Database.delete(records, AccessLevel.USER_MODE);

// Database.query with USER_MODE
String query = 'SELECT Id FROM Account WHERE Name = :name';
List<Account> accounts = Database.query(query, AccessLevel.USER_MODE);
```

### Security.stripInaccessible()

Remove inaccessible fields before DML or returning to user:

```apex
// Strip inaccessible fields before insert
List<Account> accounts = getAccountsFromExternalSource();
SObjectAccessDecision decision = Security.stripInaccessible(
    AccessType.CREATABLE,
    accounts
);
insert decision.getRecords();

// Strip before returning to user
List<Account> accounts = [SELECT Id, Name, Secret_Field__c FROM Account];
SObjectAccessDecision decision = Security.stripInaccessible(
    AccessType.READABLE,
    accounts
);
return decision.getRecords();  // Secret_Field__c removed if not accessible

// Check which fields were removed
Set<String> removedFields = decision.getRemovedFields().get('Account');
```

### Manual Checks (Legacy)

```apex
// Object-level
if (!Schema.sObjectType.Account.isCreateable()) {
    throw new SecurityException('No create access to Account');
}

// Field-level
if (!Schema.sObjectType.Account.fields.Name.isUpdateable()) {
    throw new SecurityException('No update access to Account.Name');
}
```

---

## SOQL Injection Prevention

### Use Bind Variables (Preferred)

```apex
// SAFE: Bind variable
String name = userInput;
List<Account> accounts = [SELECT Id FROM Account WHERE Name = :name];

// SAFE: Dynamic query with bind
String query = 'SELECT Id FROM Account WHERE Name = :name';
List<Account> accounts = Database.query(query);
```

### Escape User Input (If Dynamic)

```apex
// If you must build dynamic SOQL
String safeName = String.escapeSingleQuotes(userInput);
String query = 'SELECT Id FROM Account WHERE Name = \'' + safeName + '\'';
```

### Never Do This

```apex
// VULNERABLE: Direct concatenation
String query = 'SELECT Id FROM Account WHERE Name = \'' + userInput + '\'';
// Attacker input: ' OR Name != '
// Results in: SELECT Id FROM Account WHERE Name = '' OR Name != ''
```

---

## Named Credentials

### Never Hardcode Credentials

```apex
// BAD: Hardcoded credentials
Http http = new Http();
HttpRequest req = new HttpRequest();
req.setEndpoint('https://api.example.com');
req.setHeader('Authorization', 'Bearer sk_live_abc123');  // EXPOSED!

// GOOD: Named Credential
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:MyNamedCredential/api/resource');
// Authorization handled automatically
```

### Setting Up Named Credentials

1. Setup → Named Credentials
2. Configure authentication (OAuth, Password, etc.)
3. Reference in code: `callout:CredentialName/path`

---

## Custom Settings for Bypass Flags

Enable admins to disable automation without code changes:

```apex
public class TriggerConfig {
    private static Trigger_Settings__c settings;

    public static Boolean isDisabled(String triggerName) {
        if (settings == null) {
            settings = Trigger_Settings__c.getInstance();
        }

        return settings?.Disable_All_Triggers__c == true ||
               (Boolean)settings.get('Disable_' + triggerName + '__c') == true;
    }
}

// Usage in trigger action
if (TriggerConfig.isDisabled('Account')) {
    return;
}
```

---

## Secure Apex for LWC/Aura

### AuraHandledException

```apex
@AuraEnabled
public static Account getAccount(Id accountId) {
    try {
        // Use USER_MODE for security
        return [SELECT Id, Name FROM Account WHERE Id = :accountId WITH USER_MODE];
    } catch (QueryException e) {
        throw new AuraHandledException('Account not found');
    } catch (Exception e) {
        // Log for debugging
        System.debug(LoggingLevel.ERROR, e.getMessage());
        // Return user-friendly message
        throw new AuraHandledException('An error occurred. Please contact support.');
    }
}
```

### Cacheable Methods

```apex
@AuraEnabled(cacheable=true)
public static List<Account> getAccounts() {
    // Cacheable methods cannot have DML
    // Must be idempotent
    return [SELECT Id, Name FROM Account WITH USER_MODE LIMIT 100];
}
```

---

## Permission Checks

### Custom Permissions

```apex
public static Boolean hasCustomPermission(String permissionName) {
    return FeatureManagement.checkPermission(permissionName);
}

// Usage
if (!hasCustomPermission('Access_Sensitive_Data')) {
    throw new SecurityException('Insufficient permissions');
}
```

### Profile/Permission Set Checks

```apex
// Check if user has specific permission
public static Boolean canModifyAllData() {
    return [
        SELECT PermissionsModifyAllData
        FROM Profile
        WHERE Id = :UserInfo.getProfileId()
    ].PermissionsModifyAllData;
}
```

---

## Security Review Checklist

| Check | Status |
|-------|--------|
| Uses `with sharing` by default | ☐ |
| `without sharing` justified and documented | ☐ |
| SOQL uses USER_MODE or manual CRUD/FLS checks | ☐ |
| No SOQL injection vulnerabilities | ☐ |
| No hardcoded credentials | ☐ |
| Sensitive data not exposed in debug logs | ☐ |
| AuraEnabled methods have proper error handling | ☐ |
| Custom permissions used for sensitive operations | ☐ |
