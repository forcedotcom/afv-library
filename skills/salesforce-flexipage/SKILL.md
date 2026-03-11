---
name: salesforce-flexipage
description: Use this skill when users need to create, generate, modify, or validate Salesforce Lightning pages (FlexiPages). Trigger when users mention RecordPage, AppPage, HomePage, Lightning pages, page layouts, adding components to pages, or page customization. Also use when users say things like "create a Lightning page", "add a component to a page", "customize the record page", "generate a FlexiPage", or when they're working with FlexiPage XML files and need help with components, regions, or deployment errors. Always use this skill for any FlexiPage-related work, even if they just mention "page" in the context of Salesforce.
---

## When to Use This Skill

Use this skill when you need to:
- Create Lightning page layouts (RecordPage, AppPage, HomePage)
- Generate FlexiPage metadata XML
- Add components to existing FlexiPages
- Troubleshoot FlexiPage deployment errors
- Configure field sections, highlights panels, and related lists
- Work with FlexiPage regions, facets, and component properties

## Specification

# FlexiPage Metadata Specification

## Overview
Lightning page layouts for RecordPage, AppPage, and HomePage. Dynamic, component-based design supporting desktop, phone, and tablet.

---

## Generation Philosophy

**Deploy Incrementally, Iterate Quickly**

FlexiPages are complex. Deploy in small increments for fast feedback:
1. **Start simple**: Deploy with minimal components (e.g., just header region)
2. **Add incrementally**: Add one region or component at a time
3. **Deploy often**: Each addition = immediate validation
4. **Use errors to learn**: Deployment errors are faster than guessing

**Benefits:**
- Isolated errors (one component at a time)
- Faster debugging (know exactly what broke)
- Build confidence (each success validates approach)
- User feedback (see progress, adjust direction)

**Anti-pattern:** Creating entire complex page at once → hard-to-debug error cascade

---

## Critical Rules (Read First)

### 1. Property Value Encoding (MOST COMMON ERROR)

**ANY property value containing HTML/XML tags MUST be manually encoded in your XML.**

Common properties with HTML:
- Component labels with formatting: `<b>Important</b>`
- Rich text descriptions
- Help text with links: `<a href="...">Link</a>`

**Encoding rules you must apply:**
```
< → &lt;
> → &gt;
& → &amp;
" → &quot;
' → &apos;
```

**Wrong XML (will fail deployment):**
```xml
<componentInstanceProperties>
  <name>label</name>
  <value><b>Important:</b> Read this</value>
</componentInstanceProperties>
```

**Correct XML (manually encoded):**
```xml
<componentInstanceProperties>
  <name>label</name>
  <value>&lt;b&gt;Important:&lt;/b&gt; Read this</value>
</componentInstanceProperties>
```

**Process:**
1. When writing component properties, scan for `<`, `>`, `&`, `"`, or `'` characters
2. **BEFORE writing XML**, manually replace each with its entity
3. Write the encoded value directly into the XML
4. **VERIFY**: Search your generated XML for `<value>` tags - check they don't contain raw HTML tags

**Self-check:** If you see `<value><b>` or `<value><a` in your XML, you forgot to encode!

**Helper skill available (if you cannot encode manually):**
```
encode_property_value("<b>Text</b>")
```
Returns `encoded` field - copy that exact string into your XML `<value>` tag.

### 2. Field References

**ALWAYS:** `Record.{FieldApiName}`  
**NEVER:** `{ObjectName}.{FieldApiName}`

**Correct:**
```xml
<fieldItem>Record.Name</fieldItem>
```

**Incorrect:**
```xml
<fieldItem>Account.Name</fieldItem>
```

### 3. Region vs Facet Types

- Template regions (header, main, sidebar) → `<type>Region</type>`
- Component facets (internal slots) → `<type>Facet</type>`

### 4. fieldInstance Structure

Every fieldInstance requires:
- Own `<itemInstances>` wrapper
- `fieldInstanceProperties` with `uiBehavior`
- `Record.{Field}` format

---

## Generation Workflow

### Step 1: Get Metadata Information
```
get_metadata_resource("flexiPage-knowledge")
```
Returns: This knowledge content, metadata skills, resource URIs (knowledge://, schema://, example://), and schema content

### Step 2: Examine Existing FlexiPages
**CRITICAL:** Study working FlexiPages BEFORE creating spec. Real examples show actual XML patterns.

**Priority 1: Org-Retrieved FlexiPages (Best Source)**

Check `<sfdx-project-dir>/main/default/flexipages/` for existing FlexiPages:
- Use standard file tools: `list_dir`, `read_file`
- These are org-specific, production-tested pages
- Show real component usage, not theoretical patterns
- **Most valuable reference** - use as primary template

**Priority 2: Static Examples (Fallback)**

If no org FlexiPages exist, use static examples via URIs from Step 1:
```
get_metadata_resource("example://FlexiPage/0")
```
Index 0 is the App Page example
Index 1 is the Home Page example
Index 2 is the Record Page example

**What to learn:**
- Complete XML structure (regions, Facets, components)
- Remember that regions need to be adjusted to match the page template
- fieldInstance structure (itemInstances, fieldInstanceProperties)
- Facet definition and reference patterns
- Component property formats
- Valid starting point for new pages

**Use as structural reference when generating XML.**

### Step 3: Get Templates
```
get_page_templates("RecordPage")
```
Returns: Available templates and their required regions

### Step 4: Create Specification File

**Purpose:** Plan what the user wants to achieve (business requirements), NOT just inventory existing components.

**File:** `.flexipage_<PageName>_spec.md` (delete after deployment)

```markdown
# FlexiPage: [Page Name]

## Goal
[1-2 sentences: what should this page accomplish for users?]

## Page Info
- Type: RecordPage|AppPage|HomePage
- Object: [if RecordPage]
- Template: [chosen from step 2]

## Functionality Required

### [Region Name]
1. **[Functionality Description]**
   - Purpose: [what user needs to do]
   - Solution: [existing component URI] OR [Custom component to build]
   - Config needed: [properties, fields, etc.]

2. **[Another Functionality]**
   - Purpose: [user need]
   - Solution: [component or "TODO: Build CustomComponent__c"]
   - Config needed: [details]

## Custom Components Needed
- [ ] [ComponentName] - [what it does, why existing components insufficient]

## Fields to Display
- [Field] - [why user needs to see this]

## Relationships/Data
- [ ] Verify [relationship] exists for [component]

## Open Questions
- [Anything uncertain that needs clarification]
```

**Key principle:** Spec describes DESIRED functionality, not technical inventory. Include custom components that don't exist yet.

### Step 5: Discover Components
```
get_org_component_palette(target: "lightning__RecordPage")
```
Use to find components that match functionality in spec. Not all functionality may have existing components.

### Step 6: Get Component Details
```
get_org_component_metadata([uris], includeAiInfo: true, includeSource: false)
```
For components identified in step 5.

**When debugging property errors:** Fetch source code to understand component internals:
```
get_org_component_metadata([uri], includeSource: true)
```
Source code shows:
- Actual property names and types
- Required vs. optional properties
- Property value formats
- Decorators and annotations

Use when: AI descriptions are unclear or property errors occur during deployment.

### Step 7: Get Component Knowledge (When Available)
Check metadata skills from Step 1. Call for complex components:
```
get_component_knowledge("fieldSection")
```

**Components with knowledge:** `fieldSection`, `dynamicHighlights`, `dynamicRelatedList`

### Step 8: Update Spec with Solutions
Mark which functionality uses existing components vs. needs custom development.

### Step 9: Get User Approval
Present spec. Confirm approach before generating XML.

### Step 10: Generate XML
Follow approved spec. **Use example file from Step 2 as structural reference.**

**Incremental approach:**
1. Start with minimal version (e.g., header + one main component)
2. Deploy and validate
3. Add next component or region
4. Deploy again
5. Repeat until complete

Key patterns from examples:
- Template regions (`type="Region"`) vs. component facets (`type="Facet"`)
- Facet structure and references
- fieldInstance with fieldInstanceProperties
- Region and component nesting
- Property value formats

---

## Using Examples Effectively

### Example Priority

1. **Org FlexiPages** (in `force-app/main/default/flexipages/`) - **Best source**
    - Production-tested, org-specific
    - Access via `list_dir`, `read_file`
2. **Static examples** (from metadata information response) - Fallback only

### When to Reference Examples

1. **Before creating spec** (Step 2): Understand existing patterns
2. **Before generating XML** (Step 10): Copy structural patterns
3. **When debugging errors**: Compare your XML to working examples

### What Examples Show

**Facet Patterns:**
- How Facets are defined with `type="Facet"`
- How components reference Facets in properties
- Field Facets vs. component Facets

**Field Structure:**
- `fieldInstance` always in own `itemInstances`
- `fieldInstanceProperties` with `uiBehavior` required
- `Record.{Field}` format (never object name)

**Component Configuration:**
- Property formats (`componentInstanceProperties`)
- ValueLists for arrays
- Facet references in properties

**Region Structure:**
- Required regions for templates
- Component placement in regions
- Nesting patterns

### How to Use Examples

1. **Check org first**: `list_dir force-app/main/default/flexipages/`, then `read_file` similar page types
2. **If no org pages**: Use static examples for your page type
3. **Identify similar components** to what you need
4. **Copy XML structure patterns**, not exact content
5. **Adapt** to your specific fields/components
6. **Maintain** the same nesting and property structure

**Workflow:**
- Need dynamicHighlights? → Find org RecordPage with header region, or use static example
- Need fields in main? → Find org page with fieldSection, or use static example
- Need related list? → Find org page with similar component, or use static example

---

## Critical XML Rules

### Parent flexipage
**DO NOT** define a parent flexipage: do not include \`<parentFlexiPage>\` tags

### Field References
**ALWAYS:** `Record.{FieldApiName}`  
**NEVER:** `{ObjectName}.{FieldApiName}`

**Correct:**
```xml
<fieldItem>Record.Name</fieldItem>
```

**Incorrect:**
```xml
<fieldItem>Account.Name</fieldItem>
```

### fieldInstance Requirements
**Every fieldInstance MUST have:**
1. Its own `<itemInstances>` wrapper (no grouping)
2. `fieldInstanceProperties` with `uiBehavior`
3. `Record.{Field}` format

```xml
<flexiPageRegions>
    <itemInstances>
        <fieldInstance>
      <fieldInstanceProperties>
        <name>uiBehavior</name>
        <value>none</value> <!-- none|readonly|required -->
      </fieldInstanceProperties>
            <fieldItem>Record.Name</fieldItem>
            <identifier>RecordNameField</identifier>
        </fieldInstance>
    </itemInstances>
  <name>Facet-uuid</name>
    <type>Facet</type>
</flexiPageRegions>
```

### Region vs. Facet Types
**CRITICAL DISTINCTION:**

**Template Regions** (header, main, sidebar, etc.):
- Use `<type>Region</type>`
- Defined by page template
- **ONLY** use regions defined in the page template
- **DO NOT** define a \`<mode>\` for regions
- Top-level containers for components

```xml
<flexiPageRegions>
  <itemInstances>
    <componentInstance>
      <componentName>record_flexipage:dynamicHighlights</componentName>
      <identifier>highlights</identifier>
    </componentInstance>
  </itemInstances>
  <name>header</name>
  <type>Region</type> <!-- Template regions are Region -->
</flexiPageRegions>
```

**Component Facets** (component slots like column body, fieldSection columns):
- Use `<type>Facet</type>`
- Internal component properties
- Referenced by component properties

```xml
<flexiPageRegions>
    <itemInstances>
        <fieldInstance>
      <fieldInstanceProperties>
        <name>uiBehavior</name>
        <value>none</value>
      </fieldInstanceProperties>
            <fieldItem>Record.Name</fieldItem>
            <identifier>RecordNameField</identifier>
        </fieldInstance>
    </itemInstances>
  <name>Facet-uuid</name>
  <type>Facet</type> <!-- Component facets are Facet -->
</flexiPageRegions>
```

### Facet Rules
- Each Facet referenced exactly once by a component property
- No unused Facets
- Unique names (use UUIDs for Facets)

---

## Component-Specific Guidance

### fieldSection
**Retrieve knowledge before use.** Complex three-level nesting required.

### dynamicHighlights
**Retrieve knowledge before use.** Two approaches:
- Compact Layout (no config) - if object has compact layout
- Explicit Fields (Facets) - for new objects without compact layouts

**Must be in header region.**

### dynamicRelatedList
**Retrieve knowledge before use.**
- Use relationship name (NOT field name)
- Format: `parentFieldApiName: {Object}.Id`

---

## Common Deployment Errors

### "Invalid field reference"
Wrong: `Delivery__c.Order_Number__c`  
Fix: `Record.Order_Number__c`

### "Element fieldInstance is duplicated"
Cause: Multiple fieldInstances in one itemInstances  
Fix: Separate itemInstances for each

### "Missing fieldInstanceProperties"
Cause: No uiBehavior  
Fix: Add fieldInstanceProperties block with uiBehavior

### "Invalid component property" / "Unknown property"
Cause: Wrong property name or format  
**Debug strategy:** Fetch component source code:
```
get_org_component_metadata([uri], includeSource: true)
```
Source code reveals exact property names, types, and required values.

### "Unused Facet"
Cause: Facet defined but not referenced  
Fix: Reference in component property or remove

### "Invalid Region/Facet type"
**Cause:** Using wrong type for context

**Fix:**
- Template regions (header, main, sidebar) → `<type>Region</type>`
- Component facets (column body, fieldSection columns) → `<type>Facet</type>`

Common mistake: Using `<type>Facet</type>` for header/main/sidebar regions

### Region specifies mode that parent region doesn't support
**Cause:** Using a mode that is not enabled for the parent region
**Fix:** Remove the mode from the region

### "XML parsing error" / "Malformed XML" / "Unexpected element"
**Cause:** Unencoded HTML/XML tags in property values

**Fix:** See "Critical Rules" section at top of this spec for encoding requirements. You must manually encode `<`, `>`, `&`, `"`, `'` characters in property values before writing XML.

### Cannot create a new component with the namespace
**Cause:** invalid flexipage name or file name
**Fix:** Do not include \`__c\` suffix in page names and *.flexipage-meta.xml file names

---

## Template Region Requirements

Templates specify which regions are required. Get from `get_page_templates`.

Common patterns:
- Three-column: header, main, sidebar
- Two-column: main, sidebar
- Single: main

**All required regions must have at least one component.**

---

## Deprecated Components

**DO NOT USE:**
- `force:detailPanel` → use `flexipage:fieldSection`
- `force:highlightsPanel` → use `record_flexipage:dynamicHighlights`

---

## Required Metadata

```xml
<FlexiPage xmlns="http://soap.sforce.com/2006/04/metadata">
  <flexiPageRegions>...</flexiPageRegions>
  <masterLabel>Page Label</masterLabel>
  <template><name>template_name</name></template>
  <type>RecordPage|AppPage|HomePage</type>
  <sobjectType>Object__c</sobjectType> <!-- RecordPage only -->
</FlexiPage>
```

## Naming Conventions
- NO `__c` suffix in page names and *.flexipage-meta.xml file names: "Volunteer_Record_Page.flexipage-meta.xml" not "Volunteer__c_Record_Page.flexipage-meta.xml"
- Unique component identifiers
- Exact field API names from Salesforce

## Validation Before Deployment
- [ ] **Using incremental deployment** (start minimal, add iteratively)
- [ ] **Reviewed org FlexiPages** (force-app/main/default/flexipages/) or static examples for structural reference
- [ ] All fields: `Record.{Field}` format
- [ ] Every fieldInstance has fieldInstanceProperties
- [ ] Each fieldInstance in own itemInstances
- [ ] **Template regions (header, main, sidebar): `type="Region"`**
- [ ] **Component facets: `type="Facet"`**
- [ ] **Property values with HTML/XML tags are XML-encoded**
- [ ] Component knowledge followed (if available)
- [ ] Template regions populated
- [ ] No `<mode>` tags in regions
- [ ] No deprecated components
