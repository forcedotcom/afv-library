<!-- Parent: sf-ai-agentforce/SKILL.md -->
<!-- TIER: 3 | DETAILED REFERENCE -->
<!-- Read after: SKILL.md -->
<!-- Purpose: LightningTypeBundle for custom agent action UIs (API 64.0+) -->

# Custom Lightning Types for Agentforce

> Build custom UI components for agent action inputs and outputs using LightningTypeBundle

## Overview

**Custom Lightning Types** enable you to define custom data structures with dedicated UI components for Agentforce service agents. When an agent action requires structured input or displays complex output, you can create a custom type with:

- **Schema**: Define the data structure and validation
- **Editor**: Custom UI for input collection
- **Renderer**: Custom UI for displaying output

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CUSTOM LIGHTNING TYPE ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LightningTypeBundle/                                                       │
│  └── MyCustomType/                                                          │
│      ├── schema.json        ← Data structure definition                     │
│      ├── editor.json        ← Input UI configuration                        │
│      ├── renderer.json      ← Output UI configuration                       │
│      └── MyCustomType.lightningTypeBundle-meta.xml                          │
│                                                                             │
│                           ▼                                                 │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                     AGENT CONVERSATION                          │       │
│  ├─────────────────────────────────────────────────────────────────┤       │
│  │  Agent: I need some details to proceed.                         │       │
│  │                                                                  │       │
│  │  ┌──────────────────────────────────────────┐                   │       │
│  │  │ [Custom Input UI - Editor Component]      │                   │       │
│  │  │ ┌───────────────┐ ┌────────────────────┐ │                   │       │
│  │  │ │ Name: [_____] │ │ Type: [Dropdown ▼] │ │                   │       │
│  │  │ └───────────────┘ └────────────────────┘ │                   │       │
│  │  │ [Submit]                                  │                   │       │
│  │  └──────────────────────────────────────────┘                   │       │
│  │                                                                  │       │
│  │  Agent: Here's the result:                                      │       │
│  │                                                                  │       │
│  │  ┌──────────────────────────────────────────┐                   │       │
│  │  │ [Custom Output UI - Renderer Component]   │                   │       │
│  │  │ ┌─────────────────────────────────────┐  │                   │       │
│  │  │ │ Order #12345                         │  │                   │       │
│  │  │ │ Status: ✅ Confirmed                 │  │                   │       │
│  │  │ │ [View Details] [Track Shipment]      │  │                   │       │
│  │  │ └─────────────────────────────────────┘  │                   │       │
│  │  └──────────────────────────────────────────┘                   │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### API Version Requirement

**Minimum API v64.0+ (Fall '25)** for LightningTypeBundle support.

```bash
# Verify org API version
sf org display --target-org [alias] --json | jq '.result.apiVersion'
```

### Enhanced Chat V2 Requirement

Custom Lightning Types require **Enhanced Chat V2** in Service Cloud:

1. Go to **Setup → Chat → Chat Settings**
2. Enable **Enhanced Chat Experience**
3. Select **Version 2 (Enhanced)**

> ⚠️ Without Enhanced Chat V2, custom type UI components will not render.

---

## File Structure

```
force-app/main/default/
└── lightningTypeBundles/
    └── OrderDetails/
        ├── schema.json
        ├── editor.json
        ├── renderer.json
        └── OrderDetails.lightningTypeBundle-meta.xml
```

### Bundle Metadata XML

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningTypeBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Order Details</masterLabel>
    <description>Custom type for order information display</description>
</LightningTypeBundle>
```

---

## Schema Definition (schema.json)

The schema defines your data structure using JSON Schema format:

### Basic Schema

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "OrderDetails",
    "description": "Order information for display in agent conversations",
    "properties": {
        "orderId": {
            "type": "string",
            "title": "Order ID",
            "description": "Unique order identifier"
        },
        "orderStatus": {
            "type": "string",
            "title": "Order Status",
            "enum": ["Pending", "Processing", "Shipped", "Delivered", "Cancelled"],
            "description": "Current order status"
        },
        "orderDate": {
            "type": "string",
            "format": "date",
            "title": "Order Date"
        },
        "totalAmount": {
            "type": "number",
            "title": "Total Amount",
            "minimum": 0
        },
        "items": {
            "type": "array",
            "title": "Order Items",
            "items": {
                "type": "object",
                "properties": {
                    "productName": {
                        "type": "string"
                    },
                    "quantity": {
                        "type": "integer",
                        "minimum": 1
                    },
                    "price": {
                        "type": "number",
                        "minimum": 0
                    }
                },
                "required": ["productName", "quantity", "price"]
            }
        }
    },
    "required": ["orderId", "orderStatus"]
}
```

### Supported JSON Schema Types

| Type | JSON Schema | Notes |
|------|-------------|-------|
| Text | `"type": "string"` | Standard text input |
| Number | `"type": "number"` | Decimal values |
| Integer | `"type": "integer"` | Whole numbers only |
| Boolean | `"type": "boolean"` | True/false checkbox |
| Enum | `"enum": [...]` | Dropdown selection |
| Date | `"format": "date"` | Date picker |
| DateTime | `"format": "date-time"` | Date and time picker |
| Array | `"type": "array"` | List of items |
| Object | `"type": "object"` | Nested structure |

### Validation Keywords

```json
{
    "properties": {
        "email": {
            "type": "string",
            "format": "email",
            "maxLength": 255
        },
        "quantity": {
            "type": "integer",
            "minimum": 1,
            "maximum": 100
        },
        "productCode": {
            "type": "string",
            "pattern": "^PRD-[0-9]{6}$"
        }
    }
}
```

---

## Editor Configuration (editor.json)

The editor defines how input fields are collected from users:

### Basic Editor

```json
{
    "component": "lightning-record-edit-form",
    "attributes": {
        "objectApiName": "Custom_Lightning_Type"
    },
    "fields": [
        {
            "name": "orderId",
            "component": "lightning-input",
            "attributes": {
                "label": "Order ID",
                "placeholder": "Enter order number",
                "required": true
            }
        },
        {
            "name": "orderStatus",
            "component": "lightning-combobox",
            "attributes": {
                "label": "Order Status",
                "options": [
                    { "label": "Pending", "value": "Pending" },
                    { "label": "Processing", "value": "Processing" },
                    { "label": "Shipped", "value": "Shipped" },
                    { "label": "Delivered", "value": "Delivered" },
                    { "label": "Cancelled", "value": "Cancelled" }
                ]
            }
        },
        {
            "name": "orderDate",
            "component": "lightning-input",
            "attributes": {
                "type": "date",
                "label": "Order Date"
            }
        },
        {
            "name": "totalAmount",
            "component": "lightning-input",
            "attributes": {
                "type": "number",
                "label": "Total Amount",
                "formatter": "currency",
                "step": "0.01"
            }
        }
    ],
    "submitButton": {
        "label": "Submit Order Details",
        "variant": "brand"
    }
}
```

### Supported Editor Components

| Component | Use Case | Example |
|-----------|----------|---------|
| `lightning-input` | Text, number, date, email, etc. | `"type": "text"` |
| `lightning-combobox` | Dropdown selection | With `options` array |
| `lightning-checkbox` | Boolean toggle | Single checkbox |
| `lightning-checkbox-group` | Multiple selections | Array of checkboxes |
| `lightning-radio-group` | Single selection from options | Radio buttons |
| `lightning-textarea` | Multi-line text | Long descriptions |
| `lightning-file-upload` | File attachment | Document upload |

### Conditional Fields

```json
{
    "fields": [
        {
            "name": "hasDiscount",
            "component": "lightning-checkbox",
            "attributes": {
                "label": "Apply Discount?"
            }
        },
        {
            "name": "discountCode",
            "component": "lightning-input",
            "attributes": {
                "label": "Discount Code"
            },
            "conditions": {
                "hasDiscount": true
            }
        }
    ]
}
```

---

## Renderer Configuration (renderer.json)

The renderer defines how output is displayed to users:

### Basic Renderer

```json
{
    "component": "lightning-card",
    "attributes": {
        "title": "Order Details",
        "iconName": "standard:orders"
    },
    "body": [
        {
            "component": "lightning-layout",
            "attributes": {
                "multipleRows": true
            },
            "body": [
                {
                    "component": "lightning-layout-item",
                    "attributes": {
                        "size": "6"
                    },
                    "body": [
                        {
                            "component": "lightning-formatted-text",
                            "attributes": {
                                "value": "Order #${orderId}"
                            }
                        }
                    ]
                },
                {
                    "component": "lightning-layout-item",
                    "attributes": {
                        "size": "6"
                    },
                    "body": [
                        {
                            "component": "lightning-badge",
                            "attributes": {
                                "label": "${orderStatus}"
                            }
                        }
                    ]
                }
            ]
        },
        {
            "component": "lightning-formatted-number",
            "attributes": {
                "value": "${totalAmount}",
                "style": "currency",
                "currencyCode": "USD"
            }
        }
    ]
}
```

### Supported Renderer Components

| Component | Use Case |
|-----------|----------|
| `lightning-card` | Container with header |
| `lightning-layout` | Grid layout |
| `lightning-formatted-text` | Display text |
| `lightning-formatted-number` | Currency, percent |
| `lightning-formatted-date-time` | Date display |
| `lightning-badge` | Status indicators |
| `lightning-icon` | Icons |
| `lightning-button` | Actions |
| `lightning-datatable` | Tabular data |
| `lightning-progress-bar` | Progress display |

### List Rendering

For array data:

```json
{
    "component": "lightning-datatable",
    "attributes": {
        "keyField": "productName",
        "data": "${items}",
        "columns": [
            { "label": "Product", "fieldName": "productName" },
            { "label": "Quantity", "fieldName": "quantity", "type": "number" },
            { "label": "Price", "fieldName": "price", "type": "currency" }
        ]
    }
}
```

---

## Complete Example: Customer Address

### 1. schema.json

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "CustomerAddress",
    "properties": {
        "street": {
            "type": "string",
            "title": "Street Address",
            "maxLength": 255
        },
        "city": {
            "type": "string",
            "title": "City"
        },
        "state": {
            "type": "string",
            "title": "State/Province"
        },
        "postalCode": {
            "type": "string",
            "title": "Postal Code",
            "pattern": "^[0-9]{5}(-[0-9]{4})?$"
        },
        "country": {
            "type": "string",
            "title": "Country",
            "enum": ["United States", "Canada", "Mexico", "United Kingdom"]
        },
        "isDefault": {
            "type": "boolean",
            "title": "Default Address",
            "default": false
        }
    },
    "required": ["street", "city", "postalCode", "country"]
}
```

### 2. editor.json

```json
{
    "layout": "vertical",
    "fields": [
        {
            "name": "street",
            "component": "lightning-textarea",
            "attributes": {
                "label": "Street Address",
                "placeholder": "Enter your street address",
                "required": true,
                "maxLength": 255
            }
        },
        {
            "name": "city",
            "component": "lightning-input",
            "attributes": {
                "type": "text",
                "label": "City",
                "required": true
            }
        },
        {
            "name": "state",
            "component": "lightning-input",
            "attributes": {
                "type": "text",
                "label": "State/Province"
            }
        },
        {
            "name": "postalCode",
            "component": "lightning-input",
            "attributes": {
                "type": "text",
                "label": "Postal Code",
                "required": true,
                "pattern": "[0-9]{5}(-[0-9]{4})?"
            }
        },
        {
            "name": "country",
            "component": "lightning-combobox",
            "attributes": {
                "label": "Country",
                "required": true,
                "options": [
                    { "label": "United States", "value": "United States" },
                    { "label": "Canada", "value": "Canada" },
                    { "label": "Mexico", "value": "Mexico" },
                    { "label": "United Kingdom", "value": "United Kingdom" }
                ]
            }
        },
        {
            "name": "isDefault",
            "component": "lightning-checkbox",
            "attributes": {
                "label": "Set as default address"
            }
        }
    ],
    "submitButton": {
        "label": "Save Address",
        "variant": "brand"
    }
}
```

### 3. renderer.json

```json
{
    "component": "lightning-card",
    "attributes": {
        "title": "Shipping Address",
        "iconName": "standard:address"
    },
    "body": [
        {
            "component": "lightning-formatted-address",
            "attributes": {
                "street": "${street}",
                "city": "${city}",
                "province": "${state}",
                "postalCode": "${postalCode}",
                "country": "${country}"
            }
        },
        {
            "component": "lightning-badge",
            "conditions": {
                "isDefault": true
            },
            "attributes": {
                "label": "Default",
                "class": "slds-m-top_small"
            }
        }
    ]
}
```

### 4. CustomerAddress.lightningTypeBundle-meta.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningTypeBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Customer Address</masterLabel>
    <description>Structured address for customer shipping information</description>
</LightningTypeBundle>
```

---

## Using Custom Types in Agent Actions

### In GenAiFunction Metadata

```xml
<GenAiFunction xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Collect Shipping Address</masterLabel>
    <developerName>Collect_Shipping_Address</developerName>
    <description>Collects customer shipping address</description>

    <invocationTarget>Collect_Address_Flow</invocationTarget>
    <invocationTargetType>flow</invocationTargetType>

    <capability>
        Collect the customer's shipping address when they want to update
        their delivery information or place an order.
    </capability>

    <!-- Output uses custom Lightning Type -->
    <genAiFunctionOutputs>
        <developerName>shippingAddress</developerName>
        <description>The customer's shipping address</description>
        <dataType>CustomerAddress</dataType>
        <isRequired>true</isRequired>
    </genAiFunctionOutputs>
</GenAiFunction>
```

### In Agent Script

```agentscript
topic address_management:
    label: "Address Management"
    description: "Manages customer addresses"

    actions:
        Collect_Shipping_Address:
            description: "Collect the customer's shipping address"
            outputs:
                # Reference custom Lightning Type as output
                shippingAddress: CustomerAddress
                    description: "Customer shipping address"
                    is_used_by_planner: True
                    is_displayable: True
            target: "flow://Collect_Address_Flow"

    reasoning:
        instructions: ->
            | When the user wants to update their shipping address,
            | use the Collect_Shipping_Address action.
            | The custom UI will collect the address details.
        actions:
            collect: @actions.Collect_Shipping_Address
```

> **Why `is_displayable: True` is correct in this example**
> This custom Lightning-type output is meant for direct UI rendering, so `is_displayable: True` is intentional here.
>
> Use `is_displayable: False` instead when the value should stay hidden from direct customer display and only drive planner behavior. For prompt-template outputs specifically, the safer default is `is_displayable: False` + `is_used_by_planner: True`.

---

## Best Practices

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CUSTOM LIGHTNING TYPES BEST PRACTICES                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SCHEMA DESIGN                                                              │
│  ─────────────────────────────────────────────────────────────────────────  │
│  ✅ Keep schemas focused on a single concept                                │
│  ✅ Use meaningful property names                                           │
│  ✅ Add validation constraints (min, max, pattern)                          │
│  ✅ Mark required fields explicitly                                         │
│  ❌ Don't nest objects more than 2 levels deep                              │
│  ❌ Don't create overly complex schemas                                     │
│                                                                             │
│  EDITOR UX                                                                  │
│  ─────────────────────────────────────────────────────────────────────────  │
│  ✅ Group related fields together                                           │
│  ✅ Use appropriate input types (date picker for dates)                     │
│  ✅ Provide clear labels and placeholders                                   │
│  ✅ Use conditional fields to reduce complexity                             │
│  ❌ Don't require too many fields at once                                   │
│  ❌ Don't hide critical fields behind conditions                            │
│                                                                             │
│  RENDERER UX                                                                │
│  ─────────────────────────────────────────────────────────────────────────  │
│  ✅ Highlight the most important information                                │
│  ✅ Use visual hierarchy (cards, badges, icons)                             │
│  ✅ Format data appropriately (currency, dates)                             │
│  ✅ Keep displays scannable and concise                                     │
│  ❌ Don't display raw data without formatting                               │
│  ❌ Don't crowd too much information                                        │
│                                                                             │
│  DEPLOYMENT                                                                 │
│  ─────────────────────────────────────────────────────────────────────────  │
│  ✅ Deploy LightningTypeBundle before GenAiFunction                         │
│  ✅ Test with Enhanced Chat V2 enabled                                      │
│  ✅ Validate JSON files before deployment                                   │
│  ❌ Don't reference undefined custom types                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Deployment

### package.xml Entry

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>*</members>
        <name>LightningTypeBundle</name>
    </types>
    <version>64.0</version>
</Package>
```

### Deploy Command

```bash
# Deploy specific type
sf project deploy start -m "LightningTypeBundle:CustomerAddress"

# Deploy all types
sf project deploy start -d force-app/main/default/lightningTypeBundles/

# Deploy with dependencies (type + action)
sf project deploy start -m "LightningTypeBundle:CustomerAddress,GenAiFunction:Collect_Shipping_Address"
```

### Deployment Order

1. **LightningTypeBundle** - Deploy custom types first
2. **GenAiFunction** - Deploy actions that reference the types
3. **AiAuthoringBundle** - Deploy agent that uses the actions

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| UI not rendering | Enhanced Chat V2 not enabled | Enable Enhanced Chat V2 in Setup |
| "Type not found" | Custom type not deployed | Deploy LightningTypeBundle first |
| Schema validation error | Invalid JSON Schema | Validate against JSON Schema draft-07 |
| Editor fields missing | Incorrect field names | Match `name` in editor.json to schema properties |
| Renderer empty | Variable syntax error | Use `${propertyName}` for value interpolation |

---

## Related Documentation

---

## Source

> **Reference**: [How to Use Custom Lightning Types in Agentforce Service Agents](https://salesforcediaries.com/2025/11/23/how-to-use-custom-lightning-types-in-agentforce-service-agents-1/) - Salesforce Diaries
