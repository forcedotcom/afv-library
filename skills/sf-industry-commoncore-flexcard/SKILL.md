---
name: sf-industry-commoncore-flexcard
description: >
  OmniStudio FlexCard creation and validation with 130-point scoring. Use when
  building at-a-glance UI cards, configuring data source bindings to Integration
  Procedures, or reviewing existing FlexCard definitions for accessibility and
  performance.
  TRIGGER when: user creates FlexCards, configures data sources, designs card
  layouts, or asks about OmniUiCard metadata.
  DO NOT TRIGGER when: building OmniScripts (use sf-industry-commoncore-omniscript), creating Integration
  Procedures (use sf-industry-commoncore-integration-procedure), or analyzing dependencies
  (use sf-industry-commoncore-omnistudio-analyze).
license: MIT
metadata:
  version: "1.0.0"
  author: "David Ryan (weytani)"
  scoring: "130 points across 7 categories"
---

# sf-industry-commoncore-flexcard: OmniStudio FlexCard Creation and Validation

Expert OmniStudio engineer specializing in FlexCard UI components for Salesforce Industries. Generate production-ready FlexCard definitions that display at-a-glance information with declarative data binding, Integration Procedure data sources, conditional rendering, and proper SLDS styling. All FlexCards are validated against a **130-point scoring rubric** across 7 categories.

## Core Responsibilities

1. **FlexCard Authoring**: Design and build FlexCard definitions with proper layout, states, and field mappings
2. **Data Source Binding**: Configure Integration Procedure data sources with correct field mapping and error handling
3. **Test Generation**: Validate cards against multiple data states (populated, empty, error, multi-record)
4. **Documentation**: Produce deployment-ready documentation with data source lineage and action mappings

## Document Map

| Need | Document | Description |
|------|----------|-------------|
| **Best practices** | [references/best-practices.md](references/best-practices.md) | Layout patterns, SLDS, accessibility, performance |
| **Data binding** | [references/data-binding-guide.md](references/data-binding-guide.md) | IP sources, field mapping, conditional rendering |

---

## CRITICAL: Orchestration Order

FlexCards sit at the presentation layer of the OmniStudio stack. Ensure upstream components exist before building a FlexCard that depends on them.

```
sf-industry-commoncore-omnistudio-analyze → sf-industry-commoncore-datamapper → sf-industry-commoncore-integration-procedure → sf-industry-commoncore-omniscript → sf-industry-commoncore-flexcard (you are here)
```

FlexCards consume data from Integration Procedures and can launch OmniScripts. Build the data layer first, then the presentation layer.

---

## Key Insights

| Insight | Detail |
|---------|--------|
| **Configuration fields** | `OmniUiCard` uses `DataSourceConfig` for data source bindings and `PropertySetConfig` for card layout, states, and actions. There is NO `Definition` field on `OmniUiCard` in Core namespace. |
| **Data source binding** | Data sources bind to Integration Procedures for live data; the IP must be active and deployed before the FlexCard can retrieve data |
| **Child card embedding** | FlexCards can embed other FlexCards as child cards, enabling composite layouts with shared or independent data sources |
| **OmniScript launching** | FlexCards can launch OmniScripts via action buttons, passing context data from the card's data source into the OmniScript's input |
| **Designer virtual object** | The FlexCard Designer uses `OmniFlexCardView` as a virtual list object (`/lightning/o/OmniFlexCardView/home`), separate from the `OmniUiCard` sObject where card records are stored. Cards created via API may not appear in "Recently Viewed" until opened in the Designer. |

---

## Workflow (5-Phase Pattern)

### Phase 1: Requirements Gathering

Before building, clarify these with the stakeholder:

| Question | Why It Matters |
|----------|---------------|
| What is the card's purpose? | Determines layout type and data density |
| Which data sources are needed? | Identifies required Integration Procedures |
| What object context does it run in? | Determines record-level vs. list-level display |
| What actions should the card expose? | Drives button/link configuration and OmniScript integration |
| What layout best fits the use case? | Single card, list, tabbed, or flyout |
| Are there conditional display rules? | Fields or sections that appear/hide based on data values |

### Phase 2: Design & Layout

#### Card Layout Options

| Layout Type | Use Case | Description |
|-------------|----------|-------------|
| **Single Card** | Record summary | One card displaying fields from a single record |
| **Card List** | Related records | Repeating cards bound to an array data source |
| **Tabbed Card** | Multi-context | Multiple states displayed as tabs within one card |
| **Flyout Card** | Detail on demand | Expandable detail panel triggered from a summary card |

#### Data Source Configuration

Each FlexCard data source connects to an Integration Procedure (or other source type) and maps response fields to display elements.

```
FlexCard → Data Source (type: IntegrationProcedure)
         → IP Name + Input Mapping
         → Response Field Mapping → Card Elements
```

- Map IP response fields to card display elements using `{datasource.fieldName}` merge syntax
- Configure input parameters to pass record context (e.g., `{recordId}`) to the IP
- Set data source order when multiple sources feed the same card

#### Action Button Design

| Action Type | Purpose | Configuration |
|-------------|---------|---------------|
| **Launch OmniScript** | Start a guided process | OmniScript Type + SubType, pass context params |
| **Navigate** | Go to record or URL | Record ID or URL template with merge fields |
| **Custom Action** | Platform event, LWC, etc. | Custom action handler with payload mapping |

#### Conditional Visibility

- Show/hide fields based on data values using visibility conditions
- Show/hide entire card states based on data source results
- Display empty-state messaging when data source returns no records

### Phase 3: Generation & Validation

1. Generate the FlexCard definition JSON
2. Validate all data source references resolve to active Integration Procedures
3. Run the 130-point scoring rubric (see Scoring section below)
4. Verify merge field syntax matches IP response structure
5. Check accessibility attributes on all interactive elements

### Phase 4: Deployment

1. Ensure all upstream Integration Procedures are deployed and active
2. Deploy the FlexCard metadata (`OmniUiCard`)
3. Activate the FlexCard in the target org
4. Embed the FlexCard in the target Lightning page, OmniScript, or parent FlexCard

### Phase 5: Testing

Test each FlexCard against multiple data scenarios:

| Scenario | What to Verify |
|----------|---------------|
| **Populated data** | All fields render correctly, merge fields resolve |
| **Empty data** | Empty-state message displays, no broken merge fields |
| **Error state** | Graceful handling when IP returns an error or times out |
| **Multi-record** | Card list renders correct number of items, pagination works |
| **Action buttons** | OmniScript launches with correct pre-populated data |
| **Conditional fields** | Visibility rules toggle correctly based on data values |
| **Mobile** | Card layout adapts to smaller viewport widths |

---

## Generation Guardrails

Avoid these patterns when generating FlexCard definitions:

| Anti-Pattern | Why It's Wrong | Correct Approach |
|--------------|---------------|-----------------|
| Referencing non-existent IP data sources | Card fails to load data at runtime | Verify IP exists and is active before binding |
| Hardcoded colors in styles | Breaks SLDS theming and dark mode | Use SLDS design tokens and CSS custom properties |
| Missing accessibility attributes | Fails WCAG compliance | Add `aria-label`, `role`, and keyboard handlers |
| Excessive nested child cards | Performance degrades with deep nesting | Limit to 2 levels of nesting; flatten where possible |
| Ignoring empty states | Broken UI when data source returns no records | Configure explicit empty-state messaging |
| Hardcoded record IDs | Card breaks across environments | Use merge fields and context-driven parameters |

---

## Scoring Rubric (130 Points)

All FlexCards are validated against 7 categories. **Thresholds**: ✅ 90+ (Deploy) | ⚠️ 67-89 (Review) | ❌ <67 (Block - fix required)

| Category | Points | Criteria |
|----------|--------|----------|
| **Design & Layout** | 25 | Appropriate layout type, logical field grouping, responsive design, consistent spacing, clear visual hierarchy |
| **Data Binding** | 20 | Correct IP references, proper merge field syntax, input parameter mapping, multi-source coordination |
| **Actions & Navigation** | 20 | Action buttons configured correctly, OmniScript launch params mapped, navigation targets valid, action labels descriptive |
| **Styling** | 20 | SLDS tokens used (no hardcoded colors), consistent typography, proper use of card/tile patterns, dark mode compatible |
| **Accessibility** | 15 | `aria-label` on interactive elements, keyboard navigable actions, sufficient color contrast, screen reader friendly field labels |
| **Testing** | 15 | Verified with populated data, empty state, error state, multi-record scenario, and mobile viewport |
| **Performance** | 15 | Data source calls minimized, child card nesting limited (max 2 levels), no redundant IP calls, lazy loading for non-visible states |

### Scoring Breakdown Detail

#### Design & Layout (25 points)

| Criterion | Points | Description |
|-----------|--------|-------------|
| Layout type matches use case | 5 | Single, list, tabbed, or flyout chosen appropriately |
| Field grouping is logical | 5 | Related fields are visually grouped together |
| Responsive behavior | 5 | Card adapts to different viewport widths |
| Consistent spacing | 5 | Margins and padding follow SLDS spacing scale |
| Visual hierarchy | 5 | Primary information is prominent, secondary is de-emphasized |

#### Data Binding (20 points)

| Criterion | Points | Description |
|-----------|--------|-------------|
| IP references are valid | 5 | All referenced IPs exist and are active |
| Merge field syntax correct | 5 | `{datasource.field}` paths resolve to actual IP response fields |
| Input parameters mapped | 5 | Record context passed correctly to IP inputs |
| Multi-source coordination | 5 | Multiple data sources load in correct order without conflicts |

#### Actions & Navigation (20 points)

| Criterion | Points | Description |
|-----------|--------|-------------|
| Action buttons functional | 5 | All buttons trigger their configured actions |
| OmniScript params mapped | 5 | Context data flows correctly into launched OmniScripts |
| Navigation targets valid | 5 | Record and URL navigation resolves correctly |
| Labels are descriptive | 5 | Action labels clearly communicate what the action does |

#### Styling (20 points)

| Criterion | Points | Description |
|-----------|--------|-------------|
| SLDS tokens used | 5 | Colors, fonts, spacing via design tokens |
| Consistent typography | 5 | Text sizes follow SLDS type scale |
| Card pattern compliance | 5 | Uses standard SLDS card or tile patterns |
| Dark mode compatible | 5 | No hardcoded colors; works with SLDS dark theme |

#### Accessibility (15 points)

| Criterion | Points | Description |
|-----------|--------|-------------|
| ARIA labels on interactive elements | 5 | Buttons, links, and inputs have accessible names |
| Keyboard navigable | 5 | All actions reachable via Tab, activated via Enter/Space |
| Color contrast sufficient | 5 | Meets WCAG 2.1 AA contrast ratio (4.5:1 for text) |

#### Testing (15 points)

| Criterion | Points | Description |
|-----------|--------|-------------|
| Populated data verified | 3 | Card renders correctly with full data |
| Empty state verified | 3 | Empty-state message displays properly |
| Error state verified | 3 | Graceful handling of IP errors |
| Multi-record verified | 3 | Card list renders correct items |
| Mobile viewport verified | 3 | Layout adapts to small screens |

#### Performance (15 points)

| Criterion | Points | Description |
|-----------|--------|-------------|
| Data source calls minimized | 5 | No redundant or duplicate IP invocations |
| Child card nesting limited | 5 | Maximum 2 levels of nested child cards |
| Lazy loading for hidden states | 5 | Non-visible tabs/flyouts load on demand |

---

## CLI Commands

```bash
# Query active FlexCards in the org
sf data query -q "SELECT Id,Name,DataSourceConfig,PropertySetConfig,IsActive FROM OmniUiCard WHERE IsActive=true" -o <org>

# Retrieve a specific FlexCard by name
sf project retrieve start -m OmniUiCard:<Name> -o <org>

# Deploy a FlexCard to the target org
sf project deploy start -m OmniUiCard:<Name> -o <org>

# Retrieve all FlexCards
sf project retrieve start -m OmniUiCard -o <org>

# Deploy all OmniStudio metadata (FlexCards + dependencies)
sf project deploy start -m OmniUiCard -m OmniIntegrationProcedure -m OmniScript -o <org>
```

---

## Data Source Binding

### FlexCard Data Source Configuration

The `DataSourceConfig` field on `OmniUiCard` contains the data source bindings as JSON. The `PropertySetConfig` field contains the card layout, states, and field definitions.

> **IMPORTANT**: There is NO `Definition` field on `OmniUiCard` in Core namespace. Use `DataSourceConfig` for data sources and `PropertySetConfig` for layout.

```json
{
  "dataSource": {
    "type": "IntegrationProcedures",
    "value": {
      "ipMethod": "Type_SubType",
      "vlocityAsync": false,
      "inputMap": {
        "recordId": "{recordId}"
      },
      "resultVar": ""
    },
    "orderBy": {
      "name": "",
      "isReverse": ""
    },
    "contextVariables": []
  }
}
```

### Data Source Types

| Type | `dataSource.type` | When to Use |
|------|-------------------|-------------|
| **Integration Procedure** | `IntegrationProcedures` (plural, capital P) | Primary pattern; calls an IP for live data |
| **SOQL** | `SOQL` | Direct query (use sparingly; prefer IP for abstraction) |
| **Apex Remote** | `ApexRemote` | Custom Apex class invocation |
| **REST** | `REST` | External API call via Named Credential |
| **Custom** | `Custom` | Custom data provider (pass JSON body directly) |

### Field Mapping from IP Response

Map IP response fields to card display elements using merge field syntax:

```
IP Response:                    FlexCard Merge Field:
─────────────                   ─────────────────────
{ "Name": "Acme Corp" }   →    {Name}
{ "Account": {            →    {Account.Name}
    "Name": "Acme Corp"
  }
}
{ "records": [             →    {records[0].Name}  (single)
    { "Name": "Acme" }          or iterate with Card List layout
  ]
}
```

### Input Parameter Mapping

Pass context from the hosting page into the IP data source:

| Context Variable | Source | Example |
|-----------------|--------|---------|
| `{recordId}` | Current record page | Pass to IP to query related data |
| `{userId}` | Running user | Filter data by current user |
| `{param.customKey}` | URL parameter or parent card | Pass from parent FlexCard or URL |

---

## Cross-Skill Integration

| Skill | Relationship to sf-industry-commoncore-flexcard |
|-------|---------------------------|
| **sf-industry-commoncore-integration-procedure** | Build the IP data sources that FlexCards consume |
| **sf-industry-commoncore-omniscript** | Build the OmniScripts that FlexCard action buttons launch |
| **sf-industry-commoncore-datamapper** | Build DataRaptors/DataMappers that IPs use under the hood |
| **sf-industry-commoncore-omnistudio-analyze** | Analyze dependency chains across FlexCards, IPs, and OmniScripts |
| **sf-deploy** | Deploy FlexCard metadata along with upstream dependencies |
| **sf-lwc** | Build custom LWC components embedded within FlexCards |

---

## Edge Cases

| Scenario | Handling |
|----------|---------|
| **Empty data** | Configure an explicit empty-state with a user-friendly message; do not show raw "No data" or blank card |
| **Error states** | Display a meaningful error message when the IP data source fails; log the error for debugging |
| **Mobile responsiveness** | Use single-column layout for mobile; avoid horizontal scrolling; test at 320px viewport width |
| **Long text values** | Truncate with ellipsis and provide a flyout or tooltip for full text |
| **Large record sets** | Use card list with pagination; limit initial load to 10-25 records |
| **Null field values** | Use conditional visibility to hide fields with null values rather than showing empty labels |
| **Mixed data freshness** | When multiple data sources have different refresh rates, display a "last updated" indicator |

---

## FlexCard vs LWC Decision Guide

| Factor | FlexCard | LWC |
|--------|----------|-----|
| **Build method** | Declarative (drag-and-drop) | Code (JS, HTML, CSS) |
| **Data binding** | Integration Procedure merge fields | Wire service, Apex, GraphQL |
| **Best for** | At-a-glance information display | Complex interactive UIs |
| **Testing** | Manual + data state verification | Jest unit tests + manual |
| **Customization** | Limited to OmniStudio framework | Full platform flexibility |
| **Reuse** | Embed as child cards | Import as child components |
| **When to choose** | Standard card layouts with IP data | Custom behavior, animations, complex state |

---

## Dependencies

**Required**: Target org with OmniStudio (Industries Cloud) license, `sf` CLI authenticated
**For Data Sources**: Active Integration Procedures deployed to the target org
**For Actions**: Active OmniScripts deployed (if action buttons launch OmniScripts)
**Scoring**: Block deployment if score < 67

**Creating FlexCards programmatically**: Use REST API (`sf api request rest --method POST --body @file.json`). Required fields: `Name`, `VersionNumber`, `OmniUiCardType` (e.g., `Child`). Set `DataSourceConfig` (JSON string) for data source bindings and `PropertySetConfig` (JSON string) for card layout. The `sf data create record --values` flag cannot handle JSON in textarea fields. Activate by updating `IsActive=true` after creation.

---

## External References

- [OmniStudio FlexCards Trailhead](https://trailhead.salesforce.com/content/learn/modules/omnistudio-flexcards) - Official learning module
- [OmniStudio Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/omnistudio_flexcards.htm) - Technical reference
- [Salesforce Industries Documentation](https://help.salesforce.com/s/articleView?id=sf.os_flexcards.htm) - FlexCard configuration guide

---

## License

MIT License.
Copyright (c) 2026 David Ryan (weytani)
