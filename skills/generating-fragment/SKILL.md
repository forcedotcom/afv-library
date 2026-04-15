---
name: generating-fragment
description: "Use this skill when users need to create or edit Salesforce Fragments (reusable UI pieces) or mosaic renditions for CLTs. Trigger when users mention fragments, mosaics, mosaic renditions, 
  widgets, UEM blocks, reusable UI templates, structured rendering across Slack/Mobile/LEX, or block-based layouts. Also trigger when creating CLTs with mosaic/widget/fragment renditions. Always use this 
  skill for any fragment or mosaic work."
---

## When to Use This Skill

Use this skill when you need to:
- Create reusable UI fragments for Salesforce experiences
- Generate Fragment metadata following UEM structure
- Build fragments for Slack, Mobile, LEX, and other Salesforce experiences
- Troubleshoot deployment errors related to Fragments

## Specification

# Fragment Generation Guide

## 📋 Overview
Mosaics aka fragments aka widgets are reusable pieces of UI similar to templates, with placeholders for actual data values. The purpose of this file is to assist developers in creating mosaic renditions for CLTs.

## 🎯 Purpose
Fragments render data in a structured and unified way across various Salesforce experiences like Slack, Mobile, LEX etc.

## Schema Grounding
Fragment generation is **always schema-grounded** using a CLT's schema. The schema describes the data shape the fragment should render. Extract property names, types, required vs optional, and nesting from the schema; then follow the full **Workflow** below, using this extracted structure to guide every step. Do not add or remove properties relative to the schema.

## ⚙️ Composition
A fragment is a UEM (Unified Experience Model) tree of blocks and regions. The fragment you return must follow the Typescript interfaces below:

```ts
interface BlockType {
   type: 'block'
   definition: string  // {namespace}/{blockName}
   attributes?: Record<string, any>
   children?: (BlockType | RegionType)[]
}

interface RegionType {
   type: 'region'
   name: string
   children: BlockType[]
}
```

---

## 🔧 Available Metadata Actions

### When to Use Each Action

#### discoverUiComponents

**Purpose:** Discover the palette of available blocks that can be used in fragment composition.

**Use for:** Finding available blocks before building your fragment structure.

**Input Parameters:**
- `actionName` (**required***): "discoverUiComponents"
- `metadataType` (**required**): "FRAGMENT"
- `parameters` (**required**): JSON object with the below fields
    - `pageType` (**required**): "FRAGMENT"
    - `pageContext` (optional): JSON object - not required for FRAGMENT type
    - `searchQuery` (optional): String to filter components by name or description

**Returns:** List of components with:
- `definition`: Fully qualified name (e.g., "namespace/definiton")
- `description`: Component description
- `label`: Human-readable label
- `attributes`: Optional attribute metadata

#### getUiComponentSchemas

**Purpose:** Get detailed JSON schemas for component configuration, including property types, required vs optional fields, and validation rules.

**Use for:** You know which components you want but need to understand their attributes before adding them to your fragment.

**Input Parameters:**
- `actionName` (**required***): "getUiComponentSchemas"
- `metadataType` (**required**): "FRAGMENT"
- `parameters` (**required**): JSON object with the below fields
    - `pageType` (**required**): "FRAGMENT"
    - `componentDefinitions` (**required**): List of fully qualified names (e.g., ["namespace/definition"])
        - **CRITICAL**: NEVER include "tile/mosaic" in this list. "tile/mosaic" is a container component used in renderer.json structure but should NOT be passed to getUiComponentSchemas
    - `pageContext` (optional): JSON object - not required for FRAGMENT type
    - `includeKnowledge` (optional): Boolean, defaults to true - includes additional component-specific guidance

**Returns:**
- `componentSchemas`: List of results (supports partial failures)
- **Success entries**: Contains JSON schema with property definitions, types, constraints
- **Failure entries**: Contains error message explaining why schema couldn't be retrieved
- `$defs`: Schema definitions and references (if schema transformation applied)

**Key Feature:** Supports partial failures - if some components can't be found, you still get schemas for the successful ones.

---

## Attribute binding using placeholder syntax

- **Where to use:** When block attributes must display or pass through runtime data from the grounding schema, use the **Placeholder Syntax** below so that the runtime binds values into the fragment. Check each block's schema (from `getUiComponentSchemas`) for the correct attribute name (e.g. `value`, `text`, `label`).
- **Placeholder Syntax:** Use `{!$attrs.<attrName>}` as the placeholder for each attribute that should receive data.
  `<attrName>` **must** match the property name from the grounding schema so that the runtime can resolve its value.
  Example: for a schema property `title`, set the block attribute to `{!$attrs.title}`.
- **List / iterative data:** Only the children (list items) hold bound values; the parent list block does not. For each item inside a list (e.g. `tile/listItem`), use `{!$attrs.<listAttrName>.item}` so the runtime binds the current item. `<listAttrName>` MUST match the schema property name of the list. Example: for `icons`, use `"{!$attrs.icons.item}"` on the list item.

---

## 💡Workflow

1. **Schema Parsing**
- Parse the schema and extract: property names, types, required vs optional, and nested structure. Use this as the **fragment spec**.

2. **Discover Available Blocks** (**REQUIRED** - do NOT skip)
- Use **discoverUiComponents metadata action** above to explore what blocks are available.
- Use property types from the **fragment spec** to inform `searchQuery` (e.g. text → "text", number → "number").

3. **Select Components**
- Choose blocks that can represent each property in the **fragment spec** from the results of step 2.

4. **Get Component Schemas** (**REQUIRED** - do NOT skip)
- Use **getUiComponentSchemas metadata action** above with the selected component definitions and review attribute metadata.

5. **Build Fragment**
- Construct the UEM tree. Map each property in the **fragment spec** to block attributes and preserve order of the **fragment spec**.
- For attributes that must show or pass runtime data, use the placeholder syntax (see **Attribute binding (placeholders)** above).
- Use the attribute names from the schemas retrieved in step 4.

6. **Write output to CLT Bundle**
- Always write to `lightningTypes/<TypeName>/lightningDesktopGenAi/renderer.json` (or the correct target subfolder for the product surface, e.g. `experienceBuilder/`, `lightningMobileGenAi/`, `enhancedWebChat/` when applicable).
  Check **required root override pattern** below -
  `renderer.componentOverrides["$"] = { "type": "mosaic", "definition": "tile/mosaic", "children": [ ... ] — array of UEM nodes produced by the fragment workflow (e.g. "tile/card", per getUiComponentSchemas) }`

---

## ⚠️ Important Notes

- **fragment spec** includes both required and optional attributes - review carefully to ensure valid configuration.
- When using **`execute_metadata_action`** tool, always supply **`parameters`** with the required fields above; missing `parameters` or required keys causes hard failures, not partial results.
- Block definitions always follow the `{namespace}/{blockName}` convention.
- Use the same definition format returned by `discoverUiComponents` when calling `getUiComponentSchemas`
- Placeholder syntax for non-list properties is `{!$attrs.<attrName>}` and for list properties is `{!$attrs.<listAttrName>.item}`.