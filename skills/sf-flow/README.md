# sf-flow

Creates and validates Salesforce Flows with 110-point scoring and Spring '26 best practices. Build production-ready, performant, and secure flows.

## Features

- **Flow Generation**: Create record-triggered, screen, autolaunched, and scheduled flows
- **110-Point Scoring**: Automated validation across 6 categories
- **Template Library**: Pre-built patterns for common flow types
- **Bulk Safety**: Automatic checks for 251+ record handling
- **Element Library**: Complete Wait, Loop, Get Records, Transform patterns
- **Transform vs Loop Guide**: Decision pattern for choosing Transform (data mapping) vs Loop (per-record decisions)
- **Flow Quick Reference**: Comprehensive cheat sheet with flow type selection trees and element reference

## Installation

```bash
# Install as part of sf-skills
npx skills add Jaganpro/sf-skills

# Or install just this skill
npx skills add Jaganpro/sf-skills --skill sf-flow
```

## Quick Start

### 1. Invoke the skill

```
Skill: sf-flow
Request: "Create a before-save flow to auto-populate Account fields"
```

### 2. Answer requirements questions

The skill will ask about:
- Flow type (Record-Triggered, Screen, Autolaunched, etc.)
- Trigger object and timing (Before/After Save)
- Entry conditions
- Actions needed

### 3. Review generated flow

The skill generates:
- Complete Flow XML metadata
- Proper element naming with alphabetical ordering
- Entry conditions and fault connectors

## Scoring System (110 Points)

| Category | Points | Focus |
|----------|--------|-------|
| Bulkification | 25 | No DML/queries in loops, collection variables |
| Entry Criteria | 20 | Selective, indexed fields |
| Naming | 20 | Consistent element names, descriptions |
| Fault Handling | 20 | Fault paths on all DML/queries |
| Performance | 15 | Minimal elements, efficient paths |
| Documentation | 10 | Element descriptions, flow description |

**Minimum Score**: 88 (80%) for deployment

## Key Insights

| Rule | Details |
|------|---------|
| Before vs After Save | Before: same-record updates (no DML). After: related records, callouts |
| Test with 251 records | Batch boundary at 200. Test bulk behavior |
| $Record context | Single record, not a collection. Platform handles batching |
| Transform vs Loop | Transform: data mapping (30-50% faster). Loop: per-record decisions |
| Deploy as Draft | Always deploy flows as Draft first, then activate |

## Templates

| Template | Use Case |
|----------|----------|
| `before-save-template.xml` | Field auto-population |
| `after-save-template.xml` | Related record updates |
| `screen-flow-template.xml` | User interaction flows |
| `autolaunched-template.xml` | Background automation |
| `scheduled-template.xml` | Time-based automation |
| `wait-template.xml` | Wait element patterns |

## Cross-Skill Integration

| Related Skill | When to Use |
|---------------|-------------|
| sf-apex | Create @InvocableMethod for complex logic |
| sf-lwc | Create screen components for custom UI |
| sf-metadata | Deploy custom objects BEFORE flows |
| sf-deploy | Deploy flows to org |

## Orchestration Order

```
sf-metadata → sf-flow → sf-deploy → sf-data
```

Always deploy custom objects/fields BEFORE flows that reference them.

## Documentation

- [Transform vs Loop Guide](references/transform-vs-loop-guide.md) - When to use each element
- [Flow Quick Reference](references/flow-quick-reference.md) - Comprehensive cheat sheet
- [Flow Best Practices](references/flow-best-practices.md) - Performance and design patterns
- [LWC Integration](references/lwc-integration-guide.md) - Screen components
- [Wait Patterns](references/wait-patterns.md) - Delay and scheduling
- [Testing Guide](references/testing-guide.md) - Validation strategies

## Requirements

- sf CLI v2
- Target Salesforce org
- API Version 66.0+ (Spring '26)

## License

MIT License. See LICENSE file.
Copyright (c) 2024-2025 Jag Valaiyapathy
