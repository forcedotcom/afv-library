<!-- Parent: sf-metadata/SKILL.md -->
# Salesforce Metadata Naming Conventions

## Overview

Consistent naming conventions improve maintainability, discoverability, and team collaboration. Follow these standards for all Salesforce metadata.

---

## Custom Objects

### Format
```
[BusinessEntity]__c
```

### Rules
- Use PascalCase
- Singular form (not plural)
- Max 40 characters (API name)
- No abbreviations
- Descriptive and business-meaningful

### Examples
✅ Good:
- `Invoice__c`
- `Product_Catalog__c`
- `Service_Request__c`
- `Customer_Feedback__c`

❌ Avoid:
- `Invoices__c` (plural)
- `Inv__c` (abbreviated)
- `SvcReq__c` (abbreviated)
- `object1__c` (meaningless)

---

## Custom Fields

### Format
```
[Descriptive_Name]__c
```

### Rules
- Use PascalCase with underscores
- Indicate purpose, not data type
- Max 40 characters (API name)
- Use standard suffixes for relationships

### Standard Suffixes
| Suffix | Use Case |
|--------|----------|
| `_Date` | Date fields (e.g., `Due_Date__c`) |
| `_Amount` | Currency/Number (e.g., `Total_Amount__c`) |
| `_Count` | Counts (e.g., `Line_Item_Count__c`) |
| `_Percent` | Percentages (e.g., `Discount_Percent__c`) |
| `_Flag` | Boolean indicators (e.g., `Is_Active_Flag__c`) |
| `_Code` | Codes/identifiers (e.g., `Region_Code__c`) |

### Relationship Fields
```
[RelatedObject]__c     // Lookup/Master-Detail field
[RelatedObject]__r     // Relationship name (auto-generated)
```

### Examples
✅ Good:
- `Account_Manager__c` (Lookup to User)
- `Total_Contract_Value__c` (Currency)
- `Expected_Close_Date__c` (Date)
- `Is_Primary_Contact__c` (Checkbox)

❌ Avoid:
- `Amt__c` (abbreviated)
- `Field1__c` (meaningless)
- `TCV__c` (acronym without context)
- `contactLookup__c` (inconsistent casing)

---

## Profiles

### Format
```
[Role/Function] [Level]
```

### Examples
- `Sales Representative`
- `Sales Manager`
- `Marketing User`
- `System Administrator`
- `Integration User`

### Notes
- Standard profiles cannot be renamed
- Create custom profiles for specific needs
- Use Permission Sets for granular access

---

## Permission Sets

### Format
```
[Feature/Capability]_[AccessLevel]
```

### Patterns
| Pattern | Use Case |
|---------|----------|
| `[Object]_Full_Access` | Complete CRUD on object |
| `[Object]_Read_Only` | Read-only access |
| `[Feature]_Manager` | Feature management |
| `[Integration]_API` | Integration access |

### Examples
✅ Good:
- `Invoice_Full_Access`
- `Customer_Portal_User`
- `ERP_Integration_API`
- `Report_Builder_Access`
- `Deal_Approval_Manager`

❌ Avoid:
- `PS1` (meaningless)
- `John_Smith_Access` (user-specific)
- `Temp_Access` (ambiguous)

---

## Validation Rules

### Format
```
[Object]_[Action]_[Condition]
```

### Rules
- Start with object name for organization
- Use verb describing what it prevents/requires
- End with condition being validated

### Examples
✅ Good:
- `Opportunity_Require_Close_Date_When_Closed`
- `Account_Prevent_Type_Change_After_Active`
- `Contact_Require_Email_Or_Phone`
- `Invoice_Amount_Must_Be_Positive`

❌ Avoid:
- `VR001` (meaningless)
- `Check1` (undescriptive)
- `Validation` (too generic)

---

## Record Types

### Format
```
[Category/Type]_[SubCategory]
```

### Examples
✅ Good:
- `Business_Account`
- `Person_Account`
- `New_Business_Opportunity`
- `Renewal_Opportunity`
- `Support_Case`
- `Billing_Inquiry`

❌ Avoid:
- `RT1` (meaningless)
- `Type1` (undescriptive)

---

## Page Layouts

### Format
```
[Object]-[RecordType] Layout
```

### Examples
- `Account-Business Account Layout`
- `Account-Person Account Layout`
- `Opportunity-New Business Layout`
- `Case-Support Case Layout`

---

## Quick Reference Table

| Metadata Type | Pattern | Example |
|---------------|---------|---------|
| Custom Object | `BusinessEntity__c` | `Invoice__c` |
| Custom Field | `Descriptive_Name__c` | `Total_Amount__c` |
| Lookup Field | `RelatedObject__c` | `Primary_Contact__c` |
| Permission Set | `Feature_AccessLevel` | `Invoice_Manager` |
| Validation Rule | `Object_Action_Condition` | `Opp_Require_Amount` |
| Record Type | `Category_SubCategory` | `Business_Account` |
| Page Layout | `Object-RecordType Layout` | `Account-Business Layout` |

---

## Anti-Patterns to Avoid

### Abbreviations
| Instead of | Use |
|------------|-----|
| `Acct__c` | `Account__c` |
| `Opp__c` | `Opportunity__c` |
| `Cont__c` | `Contact__c` |
| `Amt__c` | `Amount__c` |
| `Qty__c` | `Quantity__c` |

### Meaningless Names
| Instead of | Use |
|------------|-----|
| `Field1__c` | `Customer_Status__c` |
| `Custom__c` | `Priority_Level__c` |
| `Temp__c` | `Processing_Date__c` |

### Inconsistent Casing
| Instead of | Use |
|------------|-----|
| `totalamount__c` | `Total_Amount__c` |
| `TOTAL_AMOUNT__c` | `Total_Amount__c` |
| `TotalAmount__c` | `Total_Amount__c` |

---

## Checklist

Before creating metadata, verify:
- [ ] Name is PascalCase with underscores
- [ ] Name describes business purpose
- [ ] No abbreviations used
- [ ] Follows standard suffix patterns
- [ ] Unique within the object/type
- [ ] Max length constraints met
- [ ] Consistent with existing patterns
