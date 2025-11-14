---
name: Apex Development Guardrails
description: Enforce best practices for Apex architecture, performance, security, and testing.
tags: apex, rules, guardrails, testing, security
---

## General Requirements
- Write Invocable Apex that can be called from flows when possible
- Use enums over string constants whenever possible. Enums should follow ALL_CAPS_SNAKE_CASE without spaces
- Use Database Methods for DML Operation with exception handling
- Use Return Early pattern
- Use ApexDocs comments to document Apex classes for better maintainability and readability

## Apex Triggers Requirements
- Follow the One Trigger Per Object pattern
- Implement a trigger handler class to separate trigger logic from the trigger itself
- Use trigger context variables (Trigger.new, Trigger.old, etc.) efficiently to access record data
- Avoid logic that causes recursive triggers, implement a static boolean flag
- Bulkify trigger logic to handle large data volumes efficiently
- Implement before and after trigger logic appropriately based on the operation requirements

## Governor Limits Compliance Requirements
- Always write bulkified code - never perform SOQL/DML operations inside loops
- Use collections for bulk processing
- Implement proper exception handling with try-catch blocks
- Limit SOQL queries to 100 per transaction
- Limit DML statements to 150 per transaction
- Use `Database.Stateful` interface only when necessary for batch jobs

## SOQL Optimization Requirements
- Use selective queries with proper WHERE clauses
- Do not use `SELECT *` - it is not supported in SOQL
- Use indexed fields in WHERE clauses when possible
- Implement SOQL best practices: LIMIT clauses, proper ordering
- Use `WITH SECURITY_ENFORCED` for user context queries where appropriate
- When querying Custom Metadata Types (objects ending with `__mdt`), DO NOT use SOQL queries. Instead, use the built-in Custom Metadata Type methods like '.getAll().values()'

## Naming Conventions & Code Organization Requirements
- Class names: PascalCase with descriptive names (e.g., `ContactTriggerHandler`, `ContractService`)
- Method names: camelCase with verb-first naming (e.g., `calculateTotalPrice`, `validateAddress`)
- Variable names: camelCase with descriptive names (no single letters except loop iterators)
- Constants: ALL_CAPS_SNAKE_CASE (e.g., `MAX_RETRY_ATTEMPTS`, `DEFAULT_TIMEOUT`)
- Test classes: Append `Test` suffix (e.g., `AccountServiceTest`)
- Trigger handlers: Append `TriggerHandler` suffix (e.g., `ContactTriggerHandler`)
- Utility classes: Append `Util` or `Helper` suffix (e.g., `DateTimeUtil`, `ValidationHelper`)
- Prefix test methods with `test` or use `@IsTest` annotation
- Group related classes in packages/folders when possible
- Keep classes focused on single responsibility (SRP)
- Limit class size to 500 lines of code maximum

## Security & Access Control Requirements
- Run database operations in user mode rather than in the default system mode.
  - List<Account> acc = [SELECT Id FROM Account WITH USER_MODE];
  - Database.insert(accts, AccessLevel.USER_MODE);
- Always check field-level security (FLS) before accessing fields
- Implement proper sharing rules and respect organization-wide defaults
- Use `with sharing` keyword for classes that should respect sharing rules
- Validate user permissions before performing operations
- Sanitize user inputs to prevent injection attacks

## Prohibited Practices
- No hardcoded IDs or URLs
- No SOQL/DML operations in loops
- No System.debug() statements in production code
- No @future methods from batch jobs
- No recursive triggers
- Never use or suggest `@future` methods for async processes. Use queueables and always suggest implementing `System.Finalizer` methods

## Required Patterns
- Use Builder pattern for complex object construction
- Implement Factory pattern for object creation
- Use Dependency Injection for testability
- Follow MVC pattern in Lightning components
- Use Command pattern for complex business operations

## Unit Testing Requirements
- Maintain minimum 75% code coverage
- Write meaningful test assertions, not just coverage
- Use `Test.startTest()` and `Test.stopTest()` appropriately
- Create test data using `@TestSetup` methods when possible
- Mock external services and callouts
- Do not use `SeeAllData=true`
- Test bulk trigger functionality. 

## Test Data Management Requirements
- Use `Test.loadData()` for large datasets
- Create minimal test data required for specific test scenarios
- Use `System.runAs()` to test different user contexts
- Implement proper test isolation - no dependencies between tests