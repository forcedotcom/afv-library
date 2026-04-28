<!-- Parent: sf-metadata/SKILL.md -->
# Salesforce Field Types Guide

## Overview

Choosing the right field type is critical for data integrity, user experience, and application performance. This guide helps you select the appropriate field type for your requirements.

---

## Field Type Decision Tree

```
What kind of data?
├── Text/String
│   ├── Short (≤255 chars) → Text
│   ├── Long (>255 chars)
│   │   ├── Plain text → Long Text Area
│   │   └── Formatted → Rich Text Area
│   ├── Predefined values
│   │   ├── Single select → Picklist
│   │   └── Multiple select → Multi-Select Picklist
│   ├── Email format → Email
│   ├── Phone format → Phone
│   └── URL format → URL
├── Numeric
│   ├── Whole numbers → Number (scale=0)
│   ├── Decimals → Number (scale>0)
│   ├── Money → Currency
│   └── Percentage → Percent
├── Date/Time
│   ├── Date only → Date
│   └── Date + Time → DateTime
├── True/False → Checkbox
├── Related Record
│   ├── Optional parent → Lookup
│   └── Required parent → Master-Detail
└── Calculated
    ├── From same record → Formula
    └── From child records → Roll-Up Summary
```

---

## Text Fields

### Text (Standard)
**Use When:** Short text values up to 255 characters
**Max Length:** 255 characters
**Features:**
- Can be unique
- Can be external ID
- Searchable
- Can be used in filters

**Examples:** Account codes, serial numbers, short names

```xml
<type>Text</type>
<length>80</length>
```

---

### Long Text Area
**Use When:** Multi-line text over 255 characters
**Max Length:** 131,072 characters
**Limitations:**
- NOT searchable
- NOT filterable
- Cannot be unique
- Cannot be used in roll-ups

**Examples:** Descriptions, notes, comments

```xml
<type>LongTextArea</type>
<length>32000</length>
<visibleLines>5</visibleLines>
```

---

### Rich Text Area
**Use When:** Formatted text with HTML
**Max Length:** 131,072 characters
**Features:**
- Bold, italic, underline
- Lists, links, images
- Same limitations as Long Text Area

**Examples:** Marketing descriptions, detailed instructions

```xml
<type>Html</type>
<length>32000</length>
<visibleLines>10</visibleLines>
```

---

## Picklist Fields

### Picklist (Single-Select)
**Use When:** Predefined single choice
**Max Values:** 1,000 (recommended < 200)
**Features:**
- Filterable
- Reportable
- Can have default value
- Restricted option available

**Best Practices:**
- Use Global Value Sets for reusable values
- Enable restricted picklist for data quality
- Consider dependent picklists for hierarchies

```xml
<type>Picklist</type>
<valueSet>
    <restricted>true</restricted>
    <valueSetDefinition>
        <sorted>false</sorted>
        <value>
            <fullName>Option1</fullName>
            <label>Option 1</label>
            <default>true</default>
        </value>
    </valueSetDefinition>
</valueSet>
```

---

### Multi-Select Picklist
**Use When:** Multiple predefined choices
**Max Values:** 500
**Limitations:**
- Cannot be unique
- Cannot be used in roll-ups
- Stored as semicolon-separated string

**Formula Access:** Use `INCLUDES()` function

```xml
<type>MultiselectPicklist</type>
<visibleLines>4</visibleLines>
```

---

## Numeric Fields

### Number
**Use When:** Numeric values (integers or decimals)
**Max Precision:** 18 digits total
**Max Scale:** 17 decimal places

**Configuration:**
- `precision`: Total digits (1-18)
- `scale`: Decimal places (0-17)

**Examples:**
| Use Case | Precision | Scale |
|----------|-----------|-------|
| Integer | 18 | 0 |
| Two decimals | 18 | 2 |
| Percentage | 5 | 2 |

```xml
<type>Number</type>
<precision>18</precision>
<scale>2</scale>
```

---

### Currency
**Use When:** Monetary values
**Features:**
- Displays with org currency symbol
- Multi-currency support
- Respects locale formatting

**Best Practice:** Use precision=18, scale=2 for standard currency

```xml
<type>Currency</type>
<precision>18</precision>
<scale>2</scale>
```

---

### Percent
**Use When:** Percentage values
**Storage:** Stored as decimal (50 = 50%)
**Display:** Shows with % symbol

```xml
<type>Percent</type>
<precision>5</precision>
<scale>2</scale>
```

---

## Date/Time Fields

### Date
**Use When:** Calendar dates without time
**Format:** YYYY-MM-DD (internal)
**Features:**
- Date picker in UI
- Timezone neutral
- Can use TODAY() in formulas

```xml
<type>Date</type>
```

---

### DateTime
**Use When:** Timestamps with time component
**Format:** ISO 8601 with timezone
**Features:**
- Date and time picker
- Timezone aware
- Can use NOW() in formulas

```xml
<type>DateTime</type>
```

---

## Boolean Fields

### Checkbox
**Use When:** True/False values
**Features:**
- Always has a value (never null)
- Default value required
- Filterable

**Best Practice:** Use clear naming (Is_Active, Has_Permission)

```xml
<type>Checkbox</type>
<defaultValue>false</defaultValue>
```

---

## Relationship Fields

### Lookup
**Use When:** Optional relationship to another record
**Features:**
- Can be empty (null)
- No cascade delete (configurable)
- No roll-up summaries
- Can be reparented

**Delete Constraints:**
| Option | Behavior |
|--------|----------|
| Clear | Sets to null (default) |
| SetNull | Sets to null |
| Restrict | Prevents deletion |

```xml
<type>Lookup</type>
<referenceTo>Account</referenceTo>
<relationshipLabel>Related Records</relationshipLabel>
<relationshipName>Related_Records</relationshipName>
<deleteConstraint>SetNull</deleteConstraint>
```

---

### Master-Detail
**Use When:** Required parent relationship
**Features:**
- Cannot be empty
- Cascade delete
- Supports roll-up summaries
- Child sharing = parent sharing

**Limitations:**
- Max 2 per object
- Cannot convert to Lookup after creation
- Child object must be empty to create

```xml
<type>MasterDetail</type>
<referenceTo>Account</referenceTo>
<relationshipLabel>Line Items</relationshipLabel>
<relationshipName>Line_Items</relationshipName>
<reparentableMasterDetail>false</reparentableMasterDetail>
```

---

## Calculated Fields

### Formula
**Use When:** Derived value from same record
**Return Types:** Text, Number, Currency, Percent, Date, DateTime, Checkbox
**Limits:**
- 5,000 compiled character limit
- Can reference up to 10 relationships

**Examples:**
```
// Text concatenation
FirstName & " " & LastName

// Conditional
IF(Amount > 100000, "Large", "Small")

// Cross-object
Account.Industry
```

```xml
<type>Text</type>  <!-- or Number, Currency, etc. -->
<formula>FirstName__c & " " & LastName__c</formula>
```

---

### Roll-Up Summary
**Use When:** Aggregate child records
**Requires:** Master-Detail relationship
**Operations:** COUNT, SUM, MIN, MAX

**Limitations:**
- Only on Master-Detail parent
- Cannot summarize formula fields
- Cannot summarize Long Text or Multi-Select

```xml
<type>Summary</type>
<summaryOperation>sum</summaryOperation>
<summarizedField>Line_Item__c.Amount__c</summarizedField>
<summaryForeignKey>Line_Item__c.Order__c</summaryForeignKey>
```

---

## Special Fields

### Email
- Max 80 characters
- Format validation
- Click-to-email in Lightning

### Phone
- Max 40 characters
- Click-to-dial support
- No format validation

### URL
- Max 255 characters
- Clickable link
- Opens in new tab

### Geolocation
- Latitude/Longitude
- Distance formulas
- Map integration

### Encrypted Text
- PII protection
- Mask characters
- Limited functionality

---

## Field Type Comparison

| Feature | Text | Long Text | Picklist | Number | Lookup | Formula |
|---------|------|-----------|----------|--------|--------|---------|
| Searchable | ✅ | ❌ | ✅ | ✅ | ✅ | ✅* |
| Filterable | ✅ | ❌ | ✅ | ✅ | ✅ | ✅* |
| Reportable | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Unique | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| External ID | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Roll-up | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Editable | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |

*Formula fields inherit searchability/filterability from return type

---

## Checklist: Choosing a Field Type

1. **Data Nature**
   - [ ] Text, number, date, or boolean?
   - [ ] Predefined values or free-form?
   - [ ] Single value or relationship?

2. **Requirements**
   - [ ] Required or optional?
   - [ ] Unique constraint needed?
   - [ ] External ID for integration?

3. **Usage**
   - [ ] Will it be searched?
   - [ ] Will it be filtered/reported?
   - [ ] Will it be used in formulas?
   - [ ] Will it be used in roll-ups?

4. **Performance**
   - [ ] Expected data volume?
   - [ ] Index needed?
   - [ ] Character limit appropriate?
