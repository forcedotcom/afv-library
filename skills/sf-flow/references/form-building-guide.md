<!-- Parent: sf-flow/SKILL.md | Cross-ref: sf-lwc/SKILL.md -->
# Form Building Guide

> **Source**: Salesforce Architect Decision Guide — Build Forms
> **Related**: [flow-best-practices.md](./flow-best-practices.md) | [integration-patterns.md](./integration-patterns.md)

---

## Overview

Salesforce offers 5 primary tools for building forms. The right choice depends on complexity, user type, testing requirements, and deployment model.

---

## 5-Tool Comparison Matrix

| Tool | Complexity | Best For | Testing | Deployment | Admin-Buildable |
|------|-----------|----------|---------|------------|-----------------|
| **Dynamic Forms** | Low | Single-record field visibility/layout | Manual only | Change Sets, Metadata API | Yes |
| **Screen Flow** | Low-Medium | Guided wizards, multi-step processes | Flow testing (CLI) | Metadata API, Change Sets | Yes |
| **OmniStudio** | Medium-High | Industry Cloud, complex multi-step | OmniStudio testing tools | IDX Workbench (special) | Partially |
| **Screen Flow + LWC** | Medium-High | Custom UI within Flow orchestration | Flow testing + Jest | Metadata API | No (developer needed) |
| **LWC** | High | Full custom UI, complex interactions | **Jest unit tests** (only option with automated testing) | Metadata API | No (developer only) |

---

## Form Selection Decision Tree

```
Is the form a simple record edit (show/hide fields based on conditions)?
  └── YES → Dynamic Forms
  └── NO → Does the form need multi-step guided input?
        └── YES → Is Industry Cloud (Health, Financial, etc.) installed?
        │     └── YES → OmniStudio (if already licensed)
        │     └── NO → Does it need custom UI components?
        │           └── YES → Screen Flow + LWC (hybrid)
        │           └── NO → Screen Flow
        └── NO → Does it need complex client-side interactions?
              └── YES → LWC (full custom)
              └── NO → Screen Flow (simplest declarative option)
```

### Quick Decision Table

| Need | Recommended Tool |
|------|-----------------|
| Simple record layout with conditional visibility | **Dynamic Forms** |
| Guided wizard with standard components | **Screen Flow** |
| Multi-step form with custom input controls | **Screen Flow + LWC** |
| Complex real-time interactions, client-side validation | **LWC** |
| Industry Cloud multi-step orchestration | **OmniStudio** |

---

## Dynamic Forms

Dynamic Forms replace page layouts with component-level control on Lightning record pages.

### Capabilities

- **Conditional visibility**: Show/hide fields based on field values, user permissions, device
- **Field sections**: Group fields with collapsible sections
- **No code**: Pure configuration in Lightning App Builder

### Limitations

- Single record context only — no multi-record forms
- No multi-step flows or guided processes
- Limited to record page context (no standalone forms)
- Not all standard objects supported (varies by release)

---

## Reactive Screen Flows

Screen Flows gained reactive capabilities that enable richer form experiences.

### Screen Actions (Reactive Screens)

Screen Actions allow components within a screen to communicate, enabling on-screen reactivity without advancing to the next screen.

**Use cases**:
- Dependent picklists across custom components
- Real-time validation feedback
- Dynamic section visibility based on input
- Auto-populating fields from a lookup selection

### Transaction Boundary Warning

> **Each screen element breaks the transaction boundary.** DML committed before a screen element cannot be rolled back after the screen. For multi-step forms with rollback needs, use the **Roll Back Records** element.

```
Screen 1: Collect input
  └── Create Records (Account) ← DML COMMITS HERE
Screen 2: Collect related info
  └── Create Records (Contact)
Screen 3: Confirmation
  ⚠️ If user navigates away at Screen 3, Account is already created but Contact may not be
```

### Best Practice for Multi-Step Data Entry

1. Collect ALL input across screens first (store in variables)
2. Perform ALL DML after the final screen
3. Use Fault Paths for rollback on failure

---

## Screen Flow + LWC Hybrid

Embed custom LWC components within Screen Flow for the best of both worlds.

### Architecture

```
Screen Flow (orchestration)
  ├── Screen 1: Standard flow components + Custom LWC
  │     └── LWC: @api inputs ← Flow variables
  │     └── LWC: FlowAttributeChangeEvent → Flow variable updates
  ├── Screen 2: More components
  └── Screen 3: Confirmation
        └── FlowNavigationFinishEvent → complete flow
```

### When to Use

- Need custom UI (charts, maps, complex tables) within a guided process
- Admin controls the flow path; developer builds the components
- Need reactive behavior that standard flow components can't provide

### Limitations

- LWC must be exposed to `lightning__FlowScreen` target
- Communication between LWC and Flow uses `FlowAttributeChangeEvent` (one-way push to Flow)
- Cannot use Flow variables directly in LWC — must pass via `@api` properties

---

## LWC (Full Custom Forms)

### Testing Advantage

> **LWC is the only form-building option with Jest unit testing.** For forms requiring automated test coverage, regression testing, or CI/CD validation, LWC provides the most robust testing story.

```javascript
// Jest test for a form component
describe('c-account-form', () => {
    it('validates required fields before submission', () => {
        const element = createElement('c-account-form', { is: AccountForm });
        document.body.appendChild(element);

        const submitBtn = element.shadowRoot.querySelector('lightning-button');
        submitBtn.click();

        return Promise.resolve().then(() => {
            const errorMsg = element.shadowRoot.querySelector('.error-message');
            expect(errorMsg).not.toBeNull();
        });
    });
});
```

### Complexity Spectrum

```
Dynamic Forms < Screen Flow < Screen Flow + LWC < OmniStudio < Full LWC
  (simplest)                                                    (most flexible)
```

Choose the simplest tool that meets requirements. Don't default to LWC when Screen Flow suffices.

---

## Security Considerations

### Experience Cloud (Community) Forms

> **Screen Flows on Experience Cloud run in system context by default.** This means they bypass sharing rules and FLS. Explicitly enforce security:

- Add **entry conditions** that check the running user's access
- Use `{!$Permission.Custom_Permission}` to gate access
- Query with `WITH USER_MODE` in any Apex Invocable Actions called from the flow
- Test as a community user, not an admin

### OmniStudio Security Warning

OmniStudio forms render client-side, meaning:
- Form structure and field metadata are visible in browser DevTools
- Client-side validation can be bypassed
- Always validate server-side (Before Save Flow or Apex trigger) for data integrity

### Input Sanitization

Rich Text inputs in flows can contain malicious HTML/JavaScript:

- Use **Before Save Flows** or Apex triggers to strip unsafe HTML tags
- The `String.stripHtmlTags()` Apex method removes all HTML
- For selective sanitization, use a custom sanitizer that allows safe tags

---

## OmniStudio Considerations

### When to Use

- Organization is on Industry Cloud (Health Cloud, Financial Services Cloud, etc.)
- Complex, multi-step data entry with branching logic
- Need pre-built industry-specific components (e.g., care plans, financial applications)

### Deployment Caveat

> **OmniStudio components are NOT deployable via standard Metadata API.** Use **IDX Workbench** for deployment. OmniStudio components are also **not packageable** in standard managed/unmanaged packages.

This impacts:
- CI/CD pipelines (need IDX Workbench CLI integration)
- Scratch org development (manual import/export)
- ISV distribution (cannot include in AppExchange packages)

---

## Validation Limitations by Tool

| Tool | Built-in Validation | Custom Validation | Server-Side Enforcement |
|------|-------------------|-------------------|------------------------|
| Dynamic Forms | Validation Rules on object | Limited | Yes (standard validation) |
| Screen Flow | Required fields, regex on some components | Decision elements for custom logic | Before Save Flow / Trigger |
| OmniStudio | Client-side validation rules | OmniScript validation | Must add server-side separately |
| LWC | `required`, `pattern`, `min/max` attributes | Full JavaScript validation | Apex controller / Before Save |

> **No form tool provides complete server-side validation out of the box.** Always pair client-side form validation with server-side enforcement (Validation Rules, Before Save Flows, or Apex triggers).

---

## Summary

1. **Start simple**: Dynamic Forms for single-record layouts, Screen Flow for guided processes
2. **Add complexity only when needed**: LWC components in Flow, or full LWC for rich interactions
3. **Always validate server-side**: Client-side validation is a UX convenience, not a security measure
4. **Consider testing**: If automated test coverage is required, LWC (Jest) is the strongest option
5. **Watch transaction boundaries**: Screens break transactions in Screen Flows — plan DML placement carefully
