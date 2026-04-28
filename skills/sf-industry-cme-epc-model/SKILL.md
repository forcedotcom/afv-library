---
name: sf-industry-cme-epc-model
description: >
  Salesforce Industries CME EPC product-modeling skill for Product2-based catalog
  creation. Use when creating EPC products, configuring product attributes,
  building offer bundles with Product Child Items, or reviewing EPC DataPack JSON
  metadata for product catalog changes.
  TRIGGER when: user creates or updates Product2 EPC records, AttributeAssignment
  payloads, AttributeMetadata/AttributeDefaultValues, Offer bundles, or
  ProductChildItem relationships.
  DO NOT TRIGGER when: designing OmniScripts/FlexCards/Integration Procedures
  (use sf-industry-commoncore-* skills), implementing Apex business logic
  (use sf-apex), or troubleshooting deployment pipelines (use sf-deploy).
license: MIT
metadata:
  version: "1.0.0"
  author: "Shreyas Dhond (ShreyasD)"
  scoring: "120 points across 6 categories"
---

# sf-industry-cme-epc-model: CME EPC Product and Offer Modeling

Expert Salesforce Industries CME EPC modeler for creating Product2-based catalog entries, assigning configurable attributes, and building offer bundles through Product Child Item relationships.

This skill is optimized for DataPack-style metadata authoring. Use the canonical template set in `assets/`:

- `assets/product2-offer-template.json`
- `assets/attribute-assignment-template.json`
- `assets/product-child-item-template.json`
- `assets/pricebook-entries-template.json`
- `assets/price-list-entries-template.json`
- `assets/object-field-attributes-template.json`
- `assets/orchestration-scenarios-template.json`
- `assets/decomposition-relationships-template.json`
- `assets/compiled-attribute-overrides-template.json`
- `assets/override-definitions-template.json`
- `assets/parent-keys-template.json`

Additional packaged examples are available under `assets/examples/` with one folder per bundle/simple-offer sample.
The root `assets/` folder contains the canonical baseline template set for bundle authoring.

---

## Quick Reference

- **Primary object**: `Product2` (EPC product and offer records)
- **Attribute data**: `%vlocity_namespace%__AttributeMetadata__c`, `%vlocity_namespace%__AttributeDefaultValues__c`, and `%vlocity_namespace%__AttributeAssignment__c`
- **Offer bundle composition**: `%vlocity_namespace%__ProductChildItem__c`
- **Offer marker**: `%vlocity_namespace%__SpecificationType__c = "Offer"` and `%vlocity_namespace%__SpecificationSubType__c = "Bundle"`
- **Companion bundle artifacts**: pricebook entries, price list entries, object field attributes, orchestration scenarios, decomposition relationships, compiled attribute overrides, override definitions, and parent keys

**Scoring**: 120 points across 6 categories.  
**Thresholds**: `>= 95` Deploy-ready | `70-94` Needs review | `< 70` Block and fix.

---

## Asset Template Set

Use the root `assets/` templates when creating a bundle payload:

- `product2-offer-template.json`
- `attribute-assignment-template.json`
- `product-child-item-template.json`
- `pricebook-entries-template.json`
- `price-list-entries-template.json`
- `object-field-attributes-template.json`
- `orchestration-scenarios-template.json`
- `decomposition-relationships-template.json`
- `compiled-attribute-overrides-template.json`
- `override-definitions-template.json`
- `parent-keys-template.json`

For additional real-world variants, use the per-example folders under `assets/examples/`.

---

## Core Responsibilities

1. **Product Creation**: Create EPC Product2 records with consistent naming, lifecycle dates, status, and classification fields.
2. **Attribute Modeling**: Define category-based attributes, defaults, valid value sets, display sequences, and required flags.
3. **Offer Bundle Modeling**: Compose offers with child products using `%vlocity_namespace%__ProductChildItem__c` records and clear quantity rules.
4. **Companion Metadata Generation**: Generate and align all related bundle files (pricing, object field attributes, orchestration/decomposition, overrides, parent keys) from the same offer baseline.
5. **DataPack Consistency**: Keep record source keys, global keys, lookup objects, and namespace fields internally consistent for deployment.

---

## Invocation Rules (Mandatory)

Route to this skill whenever the prompt intent matches either of these:

1. **Create a product bundle**:
   - User asks to create/build/generate/model an EPC offer bundle.
   - User asks for Product2 offer setup with Product Child Items.
   - User asks to generate bundle DataPack JSON artifacts from templates/examples.

2. **Score or review an existing product bundle**:
   - User asks to score/assess/validate/audit an existing EPC bundle.
   - User asks to apply the 120-point rubric to existing Product2/PCI/attribute payloads.
   - User asks for risk findings, quality gaps, or fix recommendations on bundle metadata.

**Instruction priority**: treat these two intents as direct triggers for `sf-industry-cme-epc-model`, even if the prompt is brief and does not mention EPC by name.

---

## Workflow (Create/Review)

### Phase 1: Identify Catalog Intent

Ask for:

- Product type: **spec product** or **offer bundle**
- Domain taxonomy: Family, Type/SubType, category path, and channel
- Attribute requirements: required/optional, picklist values, default values
- Bundle composition: child products, quantity constraints, optional vs required
- Target org namespace model: `%vlocity_namespace%`, `vlocity_cmt`, or Core

### Phase 1A: Clarifying Questions for Complete Bundle (Mandatory)

Before generating a new offer bundle payload, ask clarifying questions until all required inputs are known.

Required clarification checklist:

1. **Offer identity**
   - What is the offer name and `ProductCode`?
   - Is this net-new or an update to an existing Product2 offer?
2. **Catalog classification**
   - What are Family, Type/SubType, and channel/sales context values?
   - Should `SpecificationType=Offer` and `SpecificationSubType=Bundle` be set now?
3. **Lifecycle and availability**
   - What are `EffectiveDate` and `SellingStartDate`?
   - Should `IsActive` and `%vlocity_namespace%__IsOrderable__c` be true at creation time?
4. **Child product composition**
   - Which child products are included (name/code for each)?
   - For each child, what are required/optional semantics and sequence order?
5. **Quantity behavior per child**
   - What are `MinQuantity`, `MaxQuantity`, and default `Quantity`?
   - Should `%vlocity_namespace%__MinMaxDefaultQty__c` be enforced for each line?
6. **Attribute model**
   - Which attributes are required vs optional?
   - What are valid values, defaults, display types, and display sequences?
7. **Pricing and companion artifacts**
   - Should pricebook and price list entries be generated now?
   - Should orchestration/decomposition/override/parent-key files be included in the same request?
8. **Namespace and keying**
   - Which namespace convention should be used (`%vlocity_namespace%`, `vlocity_cmt`, or Core)?
   - Are there existing global keys/source keys to preserve?

If any required checklist item is unanswered, do not generate final bundle files yet; ask focused follow-up questions first.

### Phase 2: Build Product2 Backbone

For every new EPC record, define:

- `Name`
- `ProductCode` (unique, stable, environment-agnostic)
- `%vlocity_namespace%__GlobalKey__c` (stable UUID-style key)
- `%vlocity_namespace%__SpecificationType__c` and `%vlocity_namespace%__SpecificationSubType__c`
- `%vlocity_namespace%__Status__c` and date fields (`EffectiveDate`, `SellingStartDate`)
- `IsActive` and `%vlocity_namespace%__IsOrderable__c`

Use `assets/product2-offer-template.json` as baseline structure.

### Phase 3: Add Attributes

When attributes are required:

1. Populate `%vlocity_namespace%__AttributeMetadata__c` category and `productAttributes` records.
2. Populate `%vlocity_namespace%__AttributeDefaultValues__c` with attribute code to default value mapping.
3. Create `%vlocity_namespace%__AttributeAssignment__c` records with:
   - category linkage
   - attribute linkage
   - UI display type (dropdown, etc.)
   - valid values and default marker

Use `assets/attribute-assignment-template.json` as the assignment baseline.

### Phase 4: Build Offer Bundles

For offers:

1. Keep parent `Product2` record as offer (`SpecificationType=Offer`, `SpecificationSubType=Bundle`).
2. Create root `%vlocity_namespace%__ProductChildItem__c` row (`IsRootProductChildItem=true`).
3. Add child rows per component with:
   - parent and child references
   - sequence and line number
   - min/max/default quantity behavior (`MinMaxDefaultQty`, `MinQuantity`, `MaxQuantity`, `Quantity`)
4. Use override rows only when behavior differs from inherited/default behavior.

Use `assets/product-child-item-template.json` for child relationship structure.

For complete bundle payloads, also align and include:

- `assets/pricebook-entries-template.json`
- `assets/price-list-entries-template.json`
- `assets/object-field-attributes-template.json`
- `assets/orchestration-scenarios-template.json`
- `assets/decomposition-relationships-template.json`
- `assets/compiled-attribute-overrides-template.json`
- `assets/override-definitions-template.json`
- `assets/parent-keys-template.json`

### Phase 4B: Generate Companion Metadata Files

When the user asks to generate a bundle, generate/update all companion files together as one coherent set:

1. `pricebook-entries-template.json` and `price-list-entries-template.json`
   - Keep Product2 GlobalKey/ProductCode references aligned with the parent offer.
2. `object-field-attributes-template.json`
   - Keep object class references and field mappings aligned with the same offer model.
3. `orchestration-scenarios-template.json` and `decomposition-relationships-template.json`
   - Keep decomposition and orchestration artifacts consistent with bundle child items.
4. `compiled-attribute-overrides-template.json` and `override-definitions-template.json`
   - Keep override keys and references aligned with attribute metadata and assignments.
5. `parent-keys-template.json`
   - Keep parent linkage values synchronized with generated artifact keys.

**Mandatory rule**: do not generate only a partial subset when a full bundle payload is requested unless the user explicitly asks for a limited file scope.

### Phase 5: Validate and Handoff

Provide a completion block:

```text
EPC Model Complete: <Name>
Type: <Spec Product|Offer Bundle>
ProductCode: <code>
Attributes: <count>
Bundle Children: <count>
Companion Metadata Files: <count generated>
Validation Score: <score>/120
Risks: <none|list>
```

---

## Generation Guardrails (Mandatory)

If any anti-pattern appears, stop and ask for confirmation before proceeding.

| Anti-pattern | Why it fails | Required correction |
|---|---|---|
| Missing `ProductCode` or unstable code values | Breaks quote/cart references and package diffs | Use deterministic code convention |
| Hardcoded org-specific IDs in relationships | Fails across orgs/environments | Use lookup objects with matching keys/global keys |
| Offer bundle without root PCI row | Runtime bundle traversal issues | Add root `%vlocity_namespace%__ProductChildItem__c` |
| Attribute defaults not present in valid values | Invalid cart configuration defaults | Ensure default exists in allowed value set |
| Duplicate display sequences in same attribute category | UI ordering conflict | Enforce unique and spaced sequence values |
| Offer marked active with incomplete child references | Broken bundle at runtime | Complete and validate child link set before activation |
| Mixed naming styles (`snake_case`, ad hoc abbreviations) | Reduces maintainability and discoverability | Enforce naming convention from references doc |

---

## Scoring Model (120 Points)

### 1) Catalog Identity and Naming (20)
- Product name clarity and uniqueness
- `ProductCode` convention quality
- Type/SubType/Family coherence
- Stable keying (`GlobalKey`, source key integrity)

### 2) EPC Product Structure (20)
- Required Product2 + EPC fields present
- Lifecycle dates and status alignment
- Orderable/active flags are coherent
- Record type and classification consistency

### 3) Attribute Modeling (25)
- Category and attribute grouping quality
- Valid values + default alignment
- Required/read-only/filterable semantics
- Display sequence and UX consistency

### 4) Offer Bundle Composition (25)
- Root PCI presence and correctness
- Child references and sequencing integrity
- Quantity constraints correctness
- Optional/required semantics reflected in min/max/defaults

### 5) DataPack Integrity (15)
- Namespace placeholder correctness
- Lookup object key integrity
- No environment-specific brittle fields

### 6) Documentation and Handoff (15)
- Clear explanation of modeled intent
- Testing checklist included
- Risks and assumptions explicitly called out

---

## CLI and Validation Commands

```bash
# Query candidate EPC products
sf data query -q "SELECT Id,Name,ProductCode,Family,IsActive FROM Product2 ORDER BY LastModifiedDate DESC" -o <org>

# Query Product Child Items for an offer
sf data query -q "SELECT Id,Name,%vlocity_namespace%__ParentProductName__c,%vlocity_namespace%__ChildProductName__c,%vlocity_namespace%__MinMaxDefaultQty__c FROM %vlocity_namespace%__ProductChildItem__c WHERE %vlocity_namespace%__ParentProductName__c='<Offer Name>'" -o <org>

# Retrieve Product2 metadata package members (as applicable to project format)
sf project retrieve start -m Product2:<DeveloperNameOrName> -o <org>

# Validate deployment in dry-run mode
sf project deploy start -x manifest/package.xml --dry-run -o <org>
```

---

## Sample Skill Invocation Commands

Use these examples to invoke this skill from your agent/CLI workflow:

```bash
# Create a new EPC offer bundle with full companion metadata
cursor-agent "Create a Product2 offer bundle named Business Internet Plus with ProductCode BIZ-INT-PLUS-01, 3 child products, and generate all companion DataPack JSON files from the assets templates."

# Add configurable attributes to an existing EPC Product2 record
cursor-agent "Update Product2 Business Internet Essential with attribute metadata/defaults/assignments for Bandwidth, ContractTerm, and StaticIPCount, including valid values and defaults."

# Build ProductChildItem relationships for an offer
cursor-agent "Create root and child %vlocity_namespace%__ProductChildItem__c records for offer Business Internet Essential VPL with min/max/default quantity rules."

# Review an existing DataPack for EPC modeling quality
cursor-agent "Review the Product2 bundle JSON files under skills/sf-industry-cme-epc-model/examples/business-internet-plus-bundle/, score against the 120-point rubric, and return risks plus required fixes."

# Convert a spec product into a bundle-ready offer payload
cursor-agent "Transform Product2 Dedicated Fiber 1G from spec product to offer bundle (SpecificationType=Offer, SpecificationSubType=Bundle) and generate aligned PCI + pricing artifacts."
```

If your environment uses a different command wrapper, keep the quoted instruction text and replace `cursor-agent` with your local agent command.

---

## Cross-Skill Integration

| From Skill | To `sf-industry-cme-epc-model` | When |
|---|---|---|
| sf-industry-commoncore-omnistudio-analyze | -> sf-industry-cme-epc-model | Need current dependency and namespace inventory first |
| sf-metadata | -> sf-industry-cme-epc-model | Need object or field readiness before EPC modeling |
| sf-soql | -> sf-industry-cme-epc-model | Need existing catalog query analysis |

| From `sf-industry-cme-epc-model` | To Skill | When |
|---|---|---|
| sf-industry-cme-epc-model | -> sf-industry-commoncore-omniscript | Configure guided selling UX using the modeled catalog |
| sf-industry-cme-epc-model | -> sf-industry-commoncore-integration-procedure | Build server-side orchestration over product and pricing payloads |
| sf-industry-cme-epc-model | -> sf-deploy | Deploy validated catalog metadata |

---

## External References

- EPC overview: [Salesforce Help - Enterprise Product Catalog](https://help.salesforce.com/s/articleView?id=ind.comms_enterprise_product_catalog__epc_.htm&type=5)
- EPC naming conventions: [Salesforce Help - EPC Naming Conventions](https://help.salesforce.com/s/articleView?id=ind.comms_epc_name_conventions.htm&type=5)
- EPC product catalog data model: [Salesforce Help - Product Catalog ERD](https://help.salesforce.com/s/articleView?id=ind.v_data_models_t_product_catalog_erd_666964.htm&type=5)

Additional local references:

- [references/epc-field-guide.md](references/epc-field-guide.md)
- [references/naming-conventions.md](references/naming-conventions.md)

---

## Notes

- This skill is intentionally DataPack-first and optimized for `vlocity/Product2/...` artifact authoring.
- Keep `%vlocity_namespace%` placeholders intact in templates to preserve portability.
- Prefer creating reusable spec products first, then assemble offers via child relationships.

---

## License

MIT License.
