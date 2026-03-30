# Component Dependency Resolution

Algorithm for identifying and copying all dependencies when integrating a specific open code component.

## Overview

Open code components can depend on other components and labels. When copying a single component, all dependencies must be resolved recursively to ensure the component works correctly.

## Dependency Types

### 1. HTML Dependencies — `<site-*>` tags

Components reference other components via custom element tags in HTML templates.

```html
<!-- Example -->
<site-cart-badge-ui></site-cart-badge-ui>
```

**Pattern:** Extract component name from `<site-{component-name}>` where `component-name` is in kebab-case. Convert to camelCase for the directory name.

**Conversion:** `cart-badge-ui` → `cartBadgeUi`

### 2. JavaScript Dependencies — `import ... from 'site/*'`

Components import modules from other site components.

```javascript
import { handleAddToCartSuccessWithToast } from 'site/productAddToCartUtils';
```

**Pattern:** Extract the module name after `site/`. The module name maps directly to the component directory name.

### 3. Label Dependencies — `@salesforce/label/site.*`

Components import custom labels scoped to a component.

```javascript
import maximumCount from '@salesforce/label/site.cartBadge.maximumCount';
```

**Pattern:** Extract the component name between `site.` and the next `.` — this identifies which label set to copy from `sfdc_cms__label/`.

## Resolution Algorithm

1. **Scan** all files in the target component directory (`.html`, `.js`) for the three dependency patterns above
2. **Collect** a deduplicated set of dependent component names and label set names
3. **For each dependency:**
   - Copy the component from: `sfdc_cms__lwc/<dependency-name>/`
   - Copy labels from: `sfdc_cms__label/<dependency-name>/` (if the directory exists)
4. **Recurse** — scan each newly copied dependency for its own dependencies
5. **Track** all visited components to avoid circular dependency loops
6. **Report** the full dependency tree when complete

## Source and Destination Paths

**Source (cloned repo):**
- Components: `.tmp/b2b-commerce-open-source-components/force-app/main/default/sfdc_cms__lwc/<name>/`
- Labels: `.tmp/b2b-commerce-open-source-components/force-app/main/default/sfdc_cms__label/<name>/`

**Destination (local project):**
- Components: `force-app/main/default/digitalExperiences/site/<store-name>/sfdc_cms__lwc/<name>/`
- Labels: `force-app/main/default/digitalExperiences/site/<store-name>/sfdc_cms__label/<name>/`
