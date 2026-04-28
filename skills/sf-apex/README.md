# sf-apex

Generates and reviews Salesforce Apex code with 2025 best practices and 150-point scoring. Build production-ready, secure, and maintainable Apex.

## Features

- **Code Generation**: Create Apex classes, triggers (TAF), tests, batch jobs, queueables from requirements
- **Code Review**: Analyze existing Apex for best practices violations with actionable fixes
- **150-Point Scoring**: Automated validation across 8 categories
- **Template Library**: Pre-built patterns for common class types
- **LSP Integration**: Real-time syntax validation via Apex Language Server

## Installation

```bash
# Install as part of sf-skills
npx skills add Jaganpro/sf-skills

# Or install just this skill
npx skills add Jaganpro/sf-skills --skill sf-apex
```

## Quick Start

### 1. Invoke the skill

```
Skill: sf-apex
Request: "Create an AccountService class with CRUD methods"
```

### 2. Answer requirements questions

The skill will ask about:
- Class type (Service, Selector, Trigger, Batch, etc.)
- Primary purpose
- Target object(s)
- Test requirements

### 3. Review generated code

The skill generates:
- Main class with ApexDoc comments
- Corresponding test class with 90%+ coverage patterns
- Proper naming following conventions

## Scoring System (150 Points)

| Category | Points | Focus |
|----------|--------|-------|
| Bulkification | 25 | No SOQL/DML in loops, collection patterns |
| Security | 25 | CRUD/FLS checks, no injection, SOQL injection prevention |
| Testing | 25 | Test coverage, assertions, negative tests |
| Architecture | 20 | SOLID principles, separation of concerns |
| Error Handling | 15 | Try-catch, custom exceptions, logging |
| Naming | 15 | Consistent naming, ApexDoc comments |
| Performance | 15 | Async patterns, efficient queries |
| Code Quality | 10 | Clean code, no hardcoding |

**Thresholds**: 90+ | 80-89 | 70-79 | Block: <60

## Templates

| Template | Use Case |
|----------|----------|
| `trigger.trigger` | Trigger with TAF pattern |
| `trigger-action.cls` | Trigger Actions Framework handler |
| `service.cls` | Business logic service class |
| `selector.cls` | SOQL selector pattern |
| `batch.cls` | Batch Apex job |
| `queueable.cls` | Queueable async job |
| `test-class.cls` | Test class with data factory |

## Cross-Skill Integration

| Related Skill | When to Use |
|---------------|-------------|
| sf-flow | Create Flow to call @InvocableMethod |
| sf-lwc | Create LWC to call @AuraEnabled controllers |
| sf-testing | Run tests and analyze coverage |
| sf-deploy | Deploy Apex to org |

## Documentation

- [Naming Conventions](references/naming-conventions.md)
- [Best Practices](references/best-practices.md)
- [Testing Guide](references/testing-guide.md)
- [Flow Integration](references/flow-integration.md)
- [Design Patterns](references/design-patterns.md)

## Requirements

- sf CLI v2
- Target Salesforce org
- Java 11+ (for Apex LSP validation)

## License

MIT License. See LICENSE file.
Copyright (c) 2024-2025 Jag Valaiyapathy
