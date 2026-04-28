---
name: sf-industry-commoncore-callable-apex
description: >
  Salesforce Industries Common Core (OmniStudio/Vlocity) Apex callable generation and review with
  120-point scoring.
  TRIGGER when: user creates or reviews System.Callable classes, migrates
  `VlocityOpenInterface` / `VlocityOpenInterface2`, or builds Industries callable extensions used by
  OmniStudio, Integration Procedures, or DataRaptors.
  DO NOT TRIGGER when: generic Apex classes/triggers (use sf-apex), building Integration Procedures
  (use sf-industry-commoncore-integration-procedure), authoring OmniScripts (use sf-industry-commoncore-omniscript),
  configuring Data Mappers (use sf-industry-commoncore-datamapper), or analyzing namespace/dependency
  issues (use sf-industry-commoncore-omnistudio-analyze).
license: MIT
metadata:
  version: "1.0.0"
  author: "Shreyas Dhond"
  scoring: "120 points across 7 categories"
---

# sf-industry-commoncore-callable-apex: Callable Apex for Salesforce Industries Common Core

Specialist for Salesforce Industries Common Core callable Apex implementations. Produce secure,
deterministic, and configurable Apex that cleanly integrates with OmniStudio and Industries
extension points.

## Core Responsibilities

1. **Callable Generation**: Build `System.Callable` classes with safe action dispatch
2. **Callable Review**: Audit existing callable implementations for correctness and risks
3. **Validation & Scoring**: Evaluate against the 120-point rubric
4. **Industries Fit**: Ensure compatibility with OmniStudio/Industries extension points

---

## Workflow (4-Phase Pattern)

### Phase 1: Requirements Gathering

Ask for:
- Entry point (OmniScript, Integration Procedure, DataRaptor, or other Industries hook)
- Action names (strings passed into `call`)
- Input/output contract (required keys, types, and response shape)
- Data access needs (objects/fields, CRUD/FLS rules)
- Side effects (DML, callouts, async requirements)

Then:
1. Scan for existing callable classes: `Glob: **/*Callable*.cls`
2. Identify shared utilities or base classes used for Industries extensions
3. Create a task list

---

### Phase 2: Design & Contract Definition

**Define the callable contract**:
- Action list (explicit, versioned strings)
- Input schema (required keys + types)
- Output schema (consistent response envelope)

**Recommended response envelope**:
```
{
  "success": true|false,
  "data": {...},
  "errors": [ { "code": "...", "message": "..." } ]
}
```

**Action dispatch rules**:
- Use `switch on action`
- Default case throws a typed exception
- No dynamic method invocation or reflection

**VlocityOpenInterface / VlocityOpenInterface2 contract mapping**:

When designing for legacy Open Interface extensions (or dual Callable + Open Interface support), map the signature:

```
invokeMethod(String methodName, Map<String, Object> inputMap, Map<String, Object> outputMap, Map<String, Object> options)
```

| Parameter | Role | Callable equivalent |
|-----------|------|---------------------|
| `methodName` | Action selector (same semantics as `action`) | `action` in `call(action, args)` |
| `inputMap` | Primary input data (required keys, types) | `args.get('inputMap')` |
| `outputMap` | Mutable map where results are written (out-by-reference) | Return value; Callable returns envelope instead |
| `options` | Additional context (parent DataRaptor/OmniScript context, invocation metadata) | `args.get('options')` |

Design rules for Open Interface contracts:
- Treat `inputMap` and `options` as the combined input schema
- Define what keys must be written to `outputMap` per action (success and error cases)
- Preserve `methodName` strings so they align with Callable `action` strings
- Document whether `options` is required, optional, or unused for each action

---

### Phase 3: Implementation Pattern

**Vanilla System.Callable** (flat args, no Open Interface coupling):

```apex
public with sharing class Industries_OrderCallable implements System.Callable {
    public Object call(String action, Map<String, Object> args) {
        switch on action {
            when 'createOrder' {
                return createOrder(args != null ? args : new Map<String, Object>());
            }
            when else {
                throw new IndustriesCallableException('Unsupported action: ' + action);
            }
        }
    }

    private Map<String, Object> createOrder(Map<String, Object> args) {
        // Validate input (e.g. args.get('orderId')), run business logic, return response envelope
        return new Map<String, Object>{ 'success' => true };
    }
}
```

Use the vanilla pattern when callers pass flat args and no VlocityOpenInterface integration is required.

**Callable skeleton** (same inputs as VlocityOpenInterface):

Use `inputMap` and `options` keys in `args` when integrating with Open Interface or when callers pass that structure:

```apex
public with sharing class Industries_OrderCallable implements System.Callable {
    public Object call(String action, Map<String, Object> args) {
        Map<String, Object> inputMap = (args != null && args.containsKey('inputMap'))
            ? (Map<String, Object>) args.get('inputMap') : (args != null ? args : new Map<String, Object>());
        Map<String, Object> options  = (args != null && args.containsKey('options'))
            ? (Map<String, Object>) args.get('options')  : new Map<String, Object>();
        if (inputMap == null) { inputMap = new Map<String, Object>(); }
        if (options  == null) { options  = new Map<String, Object>(); }

        switch on action {
            when 'createOrder' {
                return createOrder(inputMap, options);
            }
            when else {
                throw new IndustriesCallableException('Unsupported action: ' + action);
            }
        }
    }

    private Map<String, Object> createOrder(Map<String, Object> inputMap, Map<String, Object> options) {
        // Validate input, run business logic, return response envelope
        return new Map<String, Object>{ 'success' => true };
    }
}
```

**Input format**: Callers pass `args` as `{ 'inputMap' => Map<String, Object>, 'options' => Map<String, Object> }`. For backward compatibility with flat callers, if `args` lacks `'inputMap'`, treat `args` itself as `inputMap` and use an empty map for `options`.

**Implementation rules**:
1. Keep `call()` thin; delegate to private methods or service classes
2. Validate and coerce input types early (null-safe)
3. Enforce CRUD/FLS and sharing (`with sharing`, `Security.stripInaccessible()`)
4. Bulkify when args include record collections
5. Use `WITH USER_MODE` for SOQL when appropriate

**VlocityOpenInterface / VlocityOpenInterface2 implementation**:

When implementing `omnistudio.VlocityOpenInterface` or `omnistudio.VlocityOpenInterface2`, use the signature:

```apex
global Boolean invokeMethod(String methodName, Map<String, Object> inputMap,
                           Map<String, Object> outputMap, Map<String, Object> options)
```

Open Interface skeleton:

```apex
global with sharing class Industries_OrderOpenInterface implements omnistudio.VlocityOpenInterface2 {
    global Boolean invokeMethod(String methodName, Map<String, Object> inputMap,
                                Map<String, Object> outputMap, Map<String, Object> options) {
        switch on methodName {
            when 'createOrder' {
                Map<String, Object> result = createOrder(inputMap, options);
                outputMap.putAll(result);
                return true;
            }
            when else {
                outputMap.put('success', false);
                outputMap.put('errors', new List<Map<String, Object>>{
                    new Map<String, Object>{ 'code' => 'UNSUPPORTED_ACTION', 'message' => 'Unsupported action: ' + methodName }
                });
                return false;
            }
        }
    }

    private Map<String, Object> createOrder(Map<String, Object> inputMap, Map<String, Object> options) {
        // Validate input, run business logic, return response envelope
        return new Map<String, Object>{ 'success' => true, 'data' => new Map<String, Object>() };
    }
}
```

Open Interface implementation rules:
- Write results into `outputMap` via `putAll()` or individual `put()` calls; do not return the envelope from `invokeMethod`
- Return `true` for success, `false` for unsupported or failed actions
- Use the same internal private methods as the Callable (same `inputMap` and `options` parameters); only the entry point differs
- Populate `outputMap` with the same envelope shape (`success`, `data`, `errors`) for consistency

Both Callable and Open Interface accept the same inputs (`inputMap`, `options`) and delegate to identical private method signatures for shared logic.

---

### Phase 4: Testing & Validation

Minimum tests:
- **Positive**: Supported action executes successfully
- **Negative**: Unsupported action throws expected exception
- **Contract**: Missing/invalid inputs return error envelope
- **Bulk**: Handles list inputs without hitting limits

**Example test class**:
```apex
@IsTest
private class Industries_OrderCallableTest {
    @IsTest
    static void testCreateOrder() {
        System.Callable svc = new Industries_OrderCallable();
        Map<String, Object> args = new Map<String, Object>{
            'inputMap' => new Map<String, Object>{ 'orderId' => '001000000000001' },
            'options'  => new Map<String, Object>()
        };
        Map<String, Object> result =
            (Map<String, Object>) svc.call('createOrder', args);
        Assert.isTrue((Boolean) result.get('success'));
    }

    @IsTest
    static void testUnsupportedAction() {
        try {
            System.Callable svc = new Industries_OrderCallable();
            svc.call('unknownAction', new Map<String, Object>());
            Assert.fail('Expected IndustriesCallableException');
        } catch (IndustriesCallableException e) {
            Assert.isTrue(e.getMessage().contains('Unsupported action'));
        }
    }
}
```

---

## Migration: VlocityOpenInterface to System.Callable

When modernizing Industries extensions, move `VlocityOpenInterface` or
`VlocityOpenInterface2` implementations to `System.Callable` and keep the
action contract stable. Use the Salesforce guidance as the source of truth.
[Salesforce Help](https://help.salesforce.com/s/articleView?id=ind.v_dev_t_callable_implementations_651821.htm&type=5)

**Guidance**:
- Preserve action names (`methodName`) as `action` strings in `call()`
- Pass `inputMap` and `options` as keys in `args`: `{ 'inputMap' => inputMap, 'options' => options }`
- Return a consistent response envelope instead of mutating `outMap`
- Keep `call()` thin; delegate to the same internal methods with `(inputMap, options)` signature
- Add tests for each action and unsupported action

**Example migration (pattern)**:
```apex
// BEFORE: VlocityOpenInterface2
global class OrderOpenInterface implements omnistudio.VlocityOpenInterface2 {
    global Boolean invokeMethod(String methodName, Map<String, Object> input,
                                Map<String, Object> output,
                                Map<String, Object> options) {
        if (methodName == 'createOrder') {
            output.putAll(createOrder(input, options));
            return true;
        }
        return false;
    }
}

// AFTER: System.Callable (same inputs: inputMap, options)
public with sharing class OrderCallable implements System.Callable {
    public Object call(String action, Map<String, Object> args) {
        Map<String, Object> inputMap = args != null ? (Map<String, Object>) args.get('inputMap') : new Map<String, Object>();
        Map<String, Object> options  = args != null ? (Map<String, Object>) args.get('options')   : new Map<String, Object>();
        if (inputMap == null) { inputMap = new Map<String, Object>(); }
        if (options  == null) { options  = new Map<String, Object>(); }

        switch on action {
            when 'createOrder' {
                return createOrder(inputMap, options);
            }
            when else {
                throw new IndustriesCallableException('Unsupported action: ' + action);
            }
        }
    }
}
```

---

## Best Practices (120-Point Scoring)

| Category | Points | Key Rules |
|----------|--------|-----------|
| **Contract & Dispatch** | 20 | Explicit action list; `switch on`; versioned action strings |
| **Input Validation** | 20 | Required keys validated; types coerced safely; null guards |
| **Security** | 20 | `with sharing`; CRUD/FLS checks; `Security.stripInaccessible()` |
| **Error Handling** | 15 | Typed exceptions; consistent error envelope; no empty catch |
| **Bulkification & Limits** | 20 | No SOQL/DML in loops; supports list inputs |
| **Testing** | 15 | Positive/negative/contract/bulk tests |
| **Documentation** | 10 | ApexDoc for class and action methods |

**Thresholds**: ✅ 90+ (Ready) | ⚠️ 70-89 (Review) | ❌ <70 (Block)

---

## ⛔ Guardrails (Mandatory)

Stop and ask the user if any of these would be introduced:
- Dynamic method execution based on user input (no reflection)
- SOQL/DML inside loops
- `without sharing` on callable classes
- Silent failures (empty catch, swallowed exceptions)
- Inconsistent response shapes across actions

---

## Common Anti-Patterns

- `call()` contains business logic instead of delegating
- Action names are unversioned or not documented
- Input maps assumed to have keys without checks
- Mixed response types (sometimes Map, sometimes String)
- No tests for unsupported actions

---

## Cross-Skill Integration

| Skill | When to Use | Example |
|-------|-------------|---------|
| sf-apex | General Apex work beyond callable implementations | "Create trigger for Account" |
| sf-metadata | Verify object/field availability before coding | "Describe Product2" |
| sf-deploy | Validate/deploy callable classes | "Deploy to sandbox" |

---

## Reference Skill

Use the core Apex standards, testing patterns, and guardrails in:
- [skills/sf-apex/SKILL.md](../sf-apex/SKILL.md)

---

## Bundled Examples

- [examples/Test_QuoteByProductCallable/](examples/Test_QuoteByProductCallable/) — read-only query example with `WITH USER_MODE`
- [examples/Test_VlocityOpenInterfaceConversion/](examples/Test_VlocityOpenInterfaceConversion/) — migration from legacy `VlocityOpenInterface`
- [examples/Test_VlocityOpenInterface2Conversion/](examples/Test_VlocityOpenInterface2Conversion/) — migration from `VlocityOpenInterface2`

## Notes

- Prefer deterministic, side-effect-aware callable actions
- Keep action contracts stable; introduce new actions for breaking changes
- Avoid long-running work in synchronous callables; use async when needed

---
