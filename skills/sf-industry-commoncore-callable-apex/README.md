# sf-industry-commoncore-callable-apex

Generates and reviews Salesforce Industries Common Core (OmniStudio/Vlocity) Apex callable
implementations. Build secure, deterministic `System.Callable` classes with a 120-point scoring
rubric and migration guidance from legacy `VlocityOpenInterface` implementations.

## Features

- **Callable Generation**: Create `System.Callable` classes with safe action dispatch
- **Callable Review**: Analyze existing callable implementations for risks and fixes
- **120-Point Scoring**: Validation across 7 callable-specific categories
- **VlocityOpenInterface / VlocityOpenInterface2 Support**: Phase 2 contract mapping and Phase 3 implementation patterns for `invokeMethod(String methodName, Map<String, Object> inputMap, Map<String, Object> outputMap, Map<String, Object> options)`
- **Migration Guidance**: Patterns for moving from `VlocityOpenInterface`/`VlocityOpenInterface2` to `System.Callable`
- **Testing Examples**: Test class patterns for actions, errors, and bulk inputs

## Installation

```bash
# Install as part of sf-skills
npx skills add Jaganpro/sf-skills

# Or install just this skill
npx skills add Jaganpro/sf-skills --skill sf-industry-commoncore-callable-apex
```

## Quick Start

### 1. Invoke the skill

```
Skill: sf-industry-commoncore-callable-apex
Request: "Create a callable implementation for Order actions with createOrder and cancelOrder"
```

### 2. Answer requirements questions

The skill will ask about:
- Industries entry point (OmniScript, Integration Procedure, DataRaptor)
- Action names (strings passed into `call`)
- Input/output contract (required keys, response shape)
- Data access needs and security expectations

### 3. Review generated code

The skill generates:
- Callable class with explicit `switch on action`
- Consistent response envelope
- Test class examples for action coverage and error paths

## Bundled Examples

- [examples/Test_QuoteByProductCallable/](examples/Test_QuoteByProductCallable/) — read-only callable example with SOQL and test coverage
- [examples/Test_VlocityOpenInterfaceConversion/](examples/Test_VlocityOpenInterfaceConversion/) — migration pattern from legacy `VlocityOpenInterface`
- [examples/Test_VlocityOpenInterface2Conversion/](examples/Test_VlocityOpenInterface2Conversion/) — migration pattern from `VlocityOpenInterface2`

## Scoring System (120 Points)

| Category | Points | Focus |
|----------|--------|-------|
| Contract & Dispatch | 20 | Explicit actions, `switch on`, versioned strings |
| Input Validation | 20 | Required keys, type coercion, null guards |
| Security | 20 | CRUD/FLS checks, `with sharing`, stripInaccessible |
| Error Handling | 15 | Typed exceptions, consistent errors |
| Bulkification & Limits | 20 | No SOQL/DML in loops, list inputs |
| Testing | 15 | Positive/negative/contract/bulk tests |
| Documentation | 10 | ApexDoc for class and action methods |

**Thresholds**: ✅ 90+ (Ready) | ⚠️ 70-89 (Review) | ❌ <70 (Block)

## Cross-Skill Integration

| Related Skill | When to Use |
|---------------|-------------|
| sf-apex | General Apex work beyond callable implementations |
| sf-metadata | Verify object/field availability before coding |
| sf-testing | Run tests and analyze coverage |
| sf-deploy | Deploy callable classes to an org |

## Documentation

- [Skill Instructions](SKILL.md)
- [Callable Implementations (Salesforce Help)](https://help.salesforce.com/s/articleView?id=ind.v_dev_t_callable_implementations_651821.htm&type=5)

### VlocityOpenInterface / VlocityOpenInterface2

The skill includes design (Phase 2) and implementation (Phase 3) guidance for the Open Interface signature `invokeMethod(String methodName, Map<String, Object> inputMap, Map<String, Object> outputMap, Map<String, Object> options)`. Use this when extending legacy OmniStudio/Vlocity integration points or building dual Callable + Open Interface implementations.

## Requirements

- sf CLI v2
- Target Salesforce org

## License

MIT License. See LICENSE file.
Copyright (c) 2024-2025 Jag Valaiyapathy
