---
name: integrate-b2b-commerce-open-code
description: Integrate Salesforce B2B Commerce open source components from GitHub into B2B Commerce stores. Use when users mention "integrate open code components", "open source B2B commerce", "replace OOTB components", "forcedotcom/b2b-commerce-open-source-components", or want to add/replace commerce components with open source versions. Handles component integration, dependency resolution, and OOTB component replacement.
license: Apache-2.0
compatibility: Requires Salesforce CLI (sf), Git, B2B Commerce license, Experience Builder access, and internet connectivity
allowed-tools: Bash Read Write
metadata:
  author: afv-library
  version: "1.0"
---

## When to Use This Skill

Use this skill when you need to:
- Integrate all open source B2B Commerce components into a store
- Replace all OOTB (out-of-the-box) components with open code equivalents
- Replace specific OOTB components with open code versions
- Add open source components to a new or existing B2B Commerce store
- Copy components with automatic dependency resolution

## Overview

This skill enables integration of open source B2B Commerce components from the official Salesforce repository (https://github.com/forcedotcom/b2b-commerce-open-source-components) into existing or new B2B Commerce stores.

**Three main scenarios:**
1. **Integrate** - Add all open code components to a store (components become available in Experience Builder)
2. **Replace All** - Replace all OOTB components with open code equivalents in site metadata
3. **Replace Specific** - Replace individual OOTB components with open code equivalents

## References

Before executing any workflow, **MUST** load the relevant reference docs:

- [ootb-to-opencode-mapping.md](docs/ootb-to-opencode-mapping.md) - OOTB-to-open-code naming rules and mapping table. Load when replacing components (Use Cases 2 & 3).
- [dependency-resolution.md](docs/dependency-resolution.md) - Dependency scanning algorithm (HTML/JS/labels) and recursive resolution. Load when copying specific components (Use Case 3).
- [component-replacement-workflow.md](docs/component-replacement-workflow.md) - How to scan site metadata, find OOTB components, and replace definitions. Load when replacing components (Use Cases 2 & 3).

---

## Startup Flow

When this skill is triggered, perform these checks automatically before presenting options to the user.

### Check 1: Open Source Repository

Verify the repo is cloned at `.tmp/b2b-commerce-open-source-components`:

1. If directory exists and contains `force-app/main/default/sfdc_cms__lwc` and `sfdc_cms__label`: reuse it
2. If directory does not exist: clone silently — `git clone https://github.com/forcedotcom/b2b-commerce-open-source-components .tmp/b2b-commerce-open-source-components`
3. If directory exists but structure is invalid: remove and re-clone
4. If clone fails: inform user and abort

### Check 2: Store and Site Metadata

Verify a store is selected and site metadata is available locally:

1. Check if `force-app/main/default/digitalExperiences/site/` contains any store directories
2. **If store metadata exists:** use it. If multiple stores found, ask user to select one.
3. **If no store metadata found:** delegate to the **creating-b2b-commerce-store** skill (`skills/creating-b2b-commerce-store/SKILL.md`) to create/select a store and retrieve metadata.

**Required state** after both checks (used by all subsequent tasks):
- **Store name** — the selected `fullName` value (e.g., `My_B2B_Store1`)
- **Site metadata path** — `force-app/main/default/digitalExperiences/site/<store-name>/`
- **Repo path** — `.tmp/b2b-commerce-open-source-components/`

### Present Options

Once all checks pass, present the user with:

> "Open code repository is ready and store metadata is available for **{store-name}**. What would you like to do?"
>
> 1. **Only Integrate** — Copy all open code components to your store (available in Experience Builder)
> 2. **Replace All** — Replace all OOTB components with open code equivalents
> 3. **Replace Specific** — Replace individual OOTB components with open code versions

Proceed to the corresponding use case workflow based on user selection.

---

## Core Tasks

### Task 1: Copy All Open Code Resources

Copy all components and labels from cloned repo to site directory:

- **Source:** `.tmp/b2b-commerce-open-source-components/force-app/main/default/sfdc_cms__lwc/*` and `sfdc_cms__label/*`
- **Destination:** `force-app/main/default/digitalExperiences/site/<store-name>/sfdc_cms__lwc/` and `sfdc_cms__label/`

Warn before overwriting existing files. Report count of components and labels copied.

### Task 2: Copy Specific Component with Dependencies

Copy a single component and recursively resolve all its dependencies.

> **MUST** read [dependency-resolution.md](docs/dependency-resolution.md) before executing this task.

1. Verify component exists in cloned repo
2. Scan for HTML, JavaScript, and label dependencies
3. Copy component + all dependencies + label sets
4. Report full dependency tree

### Task 3: Extract All OOTB Components from Site Metadata

Scan `content.json` files in `sfdc_cms__themeLayout/*` and `sfdc_cms__view/*` to find all OOTB component definitions.

> **MUST** read [component-replacement-workflow.md](docs/component-replacement-workflow.md) before executing this task.

Filter: keep any `"definition"` value that starts with `commerce` (e.g., `commerce_builder:*`, `commerce_cart:*`, `commerce:*`, `commerce_my_account:*`). Return deduplicated list.

### Task 4: Find Specific OOTB Component

Check if a specific OOTB component is used in the site. If not found, display all used components and offer alternatives.

> **MUST** read [component-replacement-workflow.md](docs/component-replacement-workflow.md) before executing this task.

### Task 5: Replace OOTB Component with Open Code Equivalent

Map an OOTB component name to its open code equivalent and update all `content.json` references.

> **MUST** read [ootb-to-opencode-mapping.md](docs/ootb-to-opencode-mapping.md) before executing this task.

Verify the open code component exists in the cloned repo before replacing. Only modify the `"definition"` value in JSON files.

---

## Use Case Workflows

All workflows begin after the Startup Flow completes and the user selects an option.

### Option 1: Only Integrate

**Task Sequence:** Task 1

**Output:**
```
✅ Integration Complete!

Next Steps:
1. Deploy: sf project deploy start -d force-app/main/default/digitalExperiences/site/<store-name>
2. Open Experience Builder and use new components from the palette
3. Publish your site when ready
```

### Option 2: Replace All OOTB Components

**Task Sequence:** Task 1 → Task 3 → For each component: Task 5

> **MUST** load: [ootb-to-opencode-mapping.md](docs/ootb-to-opencode-mapping.md), [component-replacement-workflow.md](docs/component-replacement-workflow.md)

**Output:**
```
✅ Replacement Complete!

Summary:
- Total OOTB components found: X
- Successfully replaced: Y
- Could not map: Z (list them)

Modified files: [list content.json files]

Next Steps:
1. Review: git diff force-app/main/default/digitalExperiences/site/<store-name>
2. Deploy: sf project deploy start -d force-app/main/default/digitalExperiences/site/<store-name>
3. Test the store thoroughly in Experience Builder
```

### Option 3: Replace Specific Components

> **MUST** load: [ootb-to-opencode-mapping.md](docs/ootb-to-opencode-mapping.md), [component-replacement-workflow.md](docs/component-replacement-workflow.md), [dependency-resolution.md](docs/dependency-resolution.md)

Ask user: "Would you like to enter a component name or select from a list of OOTB components currently in your site?"

**If user chooses "Enter component name(s)":**
- Accept one or more component names (comma-separated)
- For each component: Run Task 4 to verify it exists in site metadata
- For each verified component: Task 5 → Task 2

**If user chooses "Select from list":**
1. Run Task 3 to extract all OOTB components from site metadata
2. Display the list with multi-select (user can pick one or more):
   ```
   OOTB components found in your site:
   [ ] commerce_builder:cartBadge
   [ ] commerce_builder:cartContents
   [ ] commerce_builder:searchInput
   [ ] commerce:searchInput
   [ ] commerce_cart:items
   ...
   Select the components to replace (comma-separated numbers or 'all'):
   ```
3. For each selected component: Task 5 → Task 2

**Output:**
```
✅ Component Replacement Complete!

Replaced:
- commerce_builder:cartBadge → site:cartBadge
- commerce_builder:searchInput → site:searchInput

Copied components + dependencies:
- cartBadge, cartBadgeUi, productAddToCartUtils
- searchInput

Modified: [list content.json files]

Next Steps:
1. Deploy: sf project deploy start -d force-app/main/default/digitalExperiences/site/<store-name>
2. Test the components in Experience Builder
```

---

## Example Interaction

**User:** "I want to integrate open code components"

**Agent:** _(runs Startup Flow silently)_
- ✓ Open source repo already cloned
- ✓ Found store metadata for My_B2B_Store1

**Agent:**
> "Open code repository is ready and store metadata is available for **My_B2B_Store1**. What would you like to do?"
> 1. **Only Integrate** — Copy all open code components to your store
> 2. **Replace All** — Replace all OOTB components with open code equivalents
> 3. **Replace Specific** — Replace individual OOTB components

**User:** "2"

**Agent:** Executes Option 2 with progress updates:
- ✓ Copied 45 components and 38 label sets
- ✓ Found 12 OOTB components in site
- ✓ Replaced 10 components successfully
- ⚠ Could not map: commerce_custom:specialComponent, commerce_custom:anotherOne

**Agent:** Provides completion summary with next steps

---

## Error Handling

| Error | Message | Action |
|-------|---------|--------|
| Store not found | "Store '{name}' not found in org." | List stores again |
| Component not in repo | "Component '{name}' not found in open source repo." | List available components |
| Component not in site | "Component '{name}' is not currently used in this site." | Show used components |
| No OOTB components | "No OOTB commerce components found. Site may already use open code." | Offer to integrate instead |
| Git clone failed | "Failed to clone repository. Check internet connection." | Retry or abort |
| File copy failed | "Failed to copy files. Check file permissions." | Show error details |
| No mapping found | "No direct mapping found for '{component}'." | Ask user to select manually |

---

## Verification Checklist

- [ ] Startup Flow completed: repo cloned, store metadata available
- [ ] User selected an option (Integrate / Replace All / Replace Specific)
- [ ] Components and labels copied to correct destination paths
- [ ] Dependencies resolved recursively (if copying specific component)
- [ ] OOTB components identified and mapped correctly (if replacing)
- [ ] `content.json` files updated — only `definition` value changed, JSON structure preserved
- [ ] No JSON syntax errors introduced
- [ ] Deployment command provided and user informed about testing

---

## Anti-Patterns

**DO NOT:** copy without checking for existing files, modify open source component code, replace without verifying existence in site metadata, skip dependency resolution, deploy without user confirmation, modify `content.json` structure beyond the `definition` value, add components to wrong site directory.

**DO:** warn before overwriting, verify paths before operations, inform user of next steps, provide clear error messages, track and report all changes, preserve JSON structure, resolve dependencies recursively, verify mappings exist before replacement.
