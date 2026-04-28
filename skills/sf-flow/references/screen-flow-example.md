<!-- Parent: sf-flow/SKILL.md -->
# Screen Flow Example: Customer Feedback Form

> **Version**: 2.0.0
> **Demonstrates**: UX patterns, progress indicators, navigation controls, error recovery

This example demonstrates creating a Screen Flow that collects customer feedback and creates a custom object record, following v2.0.0 UX best practices.

---

## Scenario

Create an interactive form where users can:
- Select a product from a picklist
- Rate their experience (1-5 stars)
- Provide comments
- Submit feedback to a custom Feedback__c object

## User Request

```
User: "Create a screen flow for customer feedback collection.
It should have a welcome screen, collect product selection,
rating (1-5), and comments, then save to the Feedback__c object."
```

---

## UX Design Patterns (v2.0.0)

### Flow Structure with Navigation

```
┌────────────────────────────────────────────────────────────────┐
│  SCREEN 1: Welcome                                              │
│  ─────────────────────────                                      │
│  "Customer Feedback" (Step 1 of 3)                              │
│                                                                 │
│  Welcome message and instructions                               │
│                                                                 │
│  allowBack: false  │  allowFinish: true  │  Button: [Next]     │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│  SCREEN 2: Feedback Form                                        │
│  ─────────────────────────                                      │
│  "Enter Your Feedback" (Step 2 of 3)                            │
│                                                                 │
│  Product: [Dropdown]                                            │
│  Rating:  ★ ★ ★ ★ ★ (1-5)                                       │
│  Comments: [Text Area]                                          │
│                                                                 │
│  allowBack: true  │  allowFinish: true  │  [Previous] [Next]   │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Create Record  │──fault──▶ Error Screen
                    └────────┬────────┘
                             │ success
                             ▼
┌────────────────────────────────────────────────────────────────┐
│  SCREEN 3: Thank You                                            │
│  ─────────────────────                                          │
│  "Success!" (Step 3 of 3)                                       │
│                                                                 │
│  ✓ Thank you for your feedback!                                 │
│                                                                 │
│  allowBack: false  │  allowFinish: true  │  Button: [Finish]   │
│  (prevents duplicate submissions)                               │
└────────────────────────────────────────────────────────────────┘
```

### Navigation Control Rules Applied

| Screen | allowBack | allowFinish | Reason |
|--------|-----------|-------------|--------|
| Welcome | `false` | `true` | First screen - no previous |
| Feedback Form | `true` | `true` | Allow user to go back |
| Thank You | `false` | `true` | **Record already created** - prevent duplicate |
| Error | `true` | `true` | Let user try again |

---

## Generated Flow Structure (v2.0.0)

### Variables (with v2.0.0 Naming Prefixes)

```xml
<!-- Input/Form Variables -->
<variables>
    <name>var_ProductName</name>
    <dataType>String</dataType>
    <isCollection>false</isCollection>
    <isInput>false</isInput>
    <isOutput>false</isOutput>
</variables>

<variables>
    <name>var_Rating</name>
    <dataType>Number</dataType>
    <isCollection>false</isCollection>
    <isInput>false</isInput>
    <isOutput>false</isOutput>
    <scale>0</scale>
</variables>

<variables>
    <name>var_Comments</name>
    <dataType>String</dataType>
    <isCollection>false</isCollection>
    <isInput>false</isInput>
    <isOutput>false</isOutput>
</variables>

<!-- Error Handling Variable -->
<variables>
    <name>var_ErrorMessage</name>
    <dataType>String</dataType>
    <isCollection>false</isCollection>
    <isInput>false</isInput>
    <isOutput>false</isOutput>
</variables>

<!-- Output Variable for Integration -->
<variables>
    <name>out_FeedbackId</name>
    <dataType>String</dataType>
    <isCollection>false</isCollection>
    <isInput>false</isInput>
    <isOutput>true</isOutput>
</variables>
```

### Screen 1: Welcome (with Progress Indicator)

```xml
<screens>
    <name>Screen_Welcome</name>
    <label>Welcome</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <allowBack>false</allowBack>
    <allowFinish>true</allowFinish>
    <allowPause>false</allowPause>
    <connector>
        <targetReference>Screen_Feedback_Form</targetReference>
    </connector>
    <fields>
        <!-- Progress Indicator Header -->
        <name>Welcome_Header</name>
        <fieldType>DisplayText</fieldType>
        <fieldText>&lt;p&gt;&lt;b style="font-size: 20px;"&gt;Customer Feedback&lt;/b&gt;&lt;/p&gt;&lt;p&gt;&lt;span style="color: rgb(107, 107, 107);"&gt;Step 1 of 3&lt;/span&gt;&lt;/p&gt;</fieldText>
    </fields>
    <fields>
        <!-- Instructions -->
        <name>Welcome_Instructions</name>
        <fieldType>DisplayText</fieldType>
        <fieldText>&lt;p&gt;Thank you for taking the time to share your feedback!&lt;/p&gt;&lt;p&gt;&lt;br&gt;&lt;/p&gt;&lt;p&gt;Your input helps us improve our products and services. This form takes approximately &lt;b&gt;2 minutes&lt;/b&gt; to complete.&lt;/p&gt;&lt;p&gt;&lt;br&gt;&lt;/p&gt;&lt;p&gt;Click &lt;b&gt;Next&lt;/b&gt; to begin.&lt;/p&gt;</fieldText>
    </fields>
    <showFooter>true</showFooter>
    <showHeader>true</showHeader>
</screens>
```

### Screen 2: Feedback Form (with Input Validation)

```xml
<screens>
    <name>Screen_Feedback_Form</name>
    <label>Feedback Form</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <allowBack>true</allowBack>
    <allowFinish>true</allowFinish>
    <allowPause>false</allowPause>
    <connector>
        <targetReference>Create_Feedback_Record</targetReference>
    </connector>
    <fields>
        <!-- Progress Header -->
        <name>Form_Header</name>
        <fieldType>DisplayText</fieldType>
        <fieldText>&lt;p&gt;&lt;b style="font-size: 20px;"&gt;Enter Your Feedback&lt;/b&gt;&lt;/p&gt;&lt;p&gt;&lt;span style="color: rgb(107, 107, 107);"&gt;Step 2 of 3&lt;/span&gt;&lt;/p&gt;</fieldText>
    </fields>
    <fields>
        <!-- Instructions with Required Field Indicator -->
        <name>Form_Instructions</name>
        <fieldType>DisplayText</fieldType>
        <fieldText>&lt;p&gt;Please complete all required fields (&lt;span style="color: rgb(194, 57, 52);"&gt;*&lt;/span&gt;) below.&lt;/p&gt;</fieldText>
    </fields>
    <fields>
        <!-- Product Selection (Required) -->
        <name>Input_Product</name>
        <choiceReferences>choice_Product_A</choiceReferences>
        <choiceReferences>choice_Product_B</choiceReferences>
        <choiceReferences>choice_Product_C</choiceReferences>
        <dataType>String</dataType>
        <fieldText>Which product are you providing feedback for?</fieldText>
        <fieldType>DropdownBox</fieldType>
        <isRequired>true</isRequired>
        <inputsOnNextNavToAssocScrn>UseStoredValues</inputsOnNextNavToAssocScrn>
    </fields>
    <fields>
        <!-- Rating (1-5, Required) -->
        <name>Input_Rating</name>
        <dataType>Number</dataType>
        <fieldText>How would you rate your experience? (1-5)</fieldText>
        <fieldType>InputField</fieldType>
        <helpText>1 = Very Poor, 5 = Excellent</helpText>
        <isRequired>true</isRequired>
        <scale>0</scale>
        <inputsOnNextNavToAssocScrn>UseStoredValues</inputsOnNextNavToAssocScrn>
    </fields>
    <fields>
        <!-- Comments (Optional) -->
        <name>Input_Comments</name>
        <fieldText>Additional Comments (Optional)</fieldText>
        <fieldType>LargeTextArea</fieldType>
        <helpText>Share any additional thoughts, suggestions, or concerns.</helpText>
        <isRequired>false</isRequired>
        <inputsOnNextNavToAssocScrn>UseStoredValues</inputsOnNextNavToAssocScrn>
    </fields>
    <showFooter>true</showFooter>
    <showHeader>true</showHeader>
</screens>
```

### Record Create (with Fault Connector)

```xml
<recordCreates>
    <name>Create_Feedback_Record</name>
    <label>Create Feedback Record</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <connector>
        <targetReference>Screen_Thank_You</targetReference>
    </connector>
    <faultConnector>
        <targetReference>Capture_Error</targetReference>
    </faultConnector>
    <inputAssignments>
        <field>Product__c</field>
        <value>
            <elementReference>Input_Product</elementReference>
        </value>
    </inputAssignments>
    <inputAssignments>
        <field>Rating__c</field>
        <value>
            <elementReference>Input_Rating</elementReference>
        </value>
    </inputAssignments>
    <inputAssignments>
        <field>Comments__c</field>
        <value>
            <elementReference>Input_Comments</elementReference>
        </value>
    </inputAssignments>
    <object>Feedback__c</object>
    <storeOutputAutomatically>true</storeOutputAutomatically>
</recordCreates>
```

### Screen 3: Thank You (Back Button DISABLED)

```xml
<!--
CRITICAL: allowBack="false" on success screen!
The record has already been created. If we allow back navigation,
the user could submit again and create duplicate records.
-->
<screens>
    <name>Screen_Thank_You</name>
    <label>Thank You</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <allowBack>false</allowBack>
    <allowFinish>true</allowFinish>
    <allowPause>false</allowPause>
    <!-- No connector = "Finish" button displayed -->
    <fields>
        <name>ThankYou_Header</name>
        <fieldType>DisplayText</fieldType>
        <fieldText>&lt;p&gt;&lt;b style="font-size: 20px;"&gt;Success!&lt;/b&gt;&lt;/p&gt;&lt;p&gt;&lt;span style="color: rgb(107, 107, 107);"&gt;Step 3 of 3&lt;/span&gt;&lt;/p&gt;</fieldText>
    </fields>
    <fields>
        <name>ThankYou_Message</name>
        <fieldType>DisplayText</fieldType>
        <fieldText>&lt;p&gt;&lt;span style="color: rgb(46, 132, 74); font-size: 24px;"&gt;✓&lt;/span&gt;&lt;/p&gt;&lt;p&gt;&lt;br&gt;&lt;/p&gt;&lt;p&gt;&lt;b&gt;Thank you for your feedback!&lt;/b&gt;&lt;/p&gt;&lt;p&gt;&lt;br&gt;&lt;/p&gt;&lt;p&gt;Your input has been recorded and will help us improve our products and services.&lt;/p&gt;&lt;p&gt;&lt;br&gt;&lt;/p&gt;&lt;p&gt;Click &lt;b&gt;Finish&lt;/b&gt; to close this form.&lt;/p&gt;</fieldText>
    </fields>
    <showFooter>true</showFooter>
    <showHeader>true</showHeader>
</screens>
```

### Error Recovery Screen (Back Button ENABLED)

```xml
<!-- Capture Error Message -->
<assignments>
    <name>Capture_Error</name>
    <label>Capture Error</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <assignmentItems>
        <assignToReference>var_ErrorMessage</assignToReference>
        <operator>Assign</operator>
        <value>
            <elementReference>$Flow.FaultMessage</elementReference>
        </value>
    </assignmentItems>
    <connector>
        <targetReference>Screen_Error</targetReference>
    </connector>
</assignments>

<!--
ERROR SCREEN: allowBack="true"
Let users go back to fix their input and try again.
The record wasn't created, so no duplicate risk.
-->
<screens>
    <name>Screen_Error</name>
    <label>Error</label>
    <locationX>0</locationX>
    <locationY>0</locationY>
    <allowBack>true</allowBack>
    <allowFinish>true</allowFinish>
    <allowPause>false</allowPause>
    <fields>
        <name>Error_Header</name>
        <fieldType>DisplayText</fieldType>
        <fieldText>&lt;p&gt;&lt;span style="color: rgb(194, 57, 52);"&gt;&lt;b style="font-size: 20px;"&gt;Something Went Wrong&lt;/b&gt;&lt;/span&gt;&lt;/p&gt;</fieldText>
    </fields>
    <fields>
        <name>Error_Message</name>
        <fieldType>DisplayText</fieldType>
        <fieldText>&lt;p&gt;We were unable to save your feedback. The error was:&lt;/p&gt;&lt;p&gt;&lt;br&gt;&lt;/p&gt;&lt;p&gt;&lt;i style="color: rgb(194, 57, 52);"&gt;{!var_ErrorMessage}&lt;/i&gt;&lt;/p&gt;&lt;p&gt;&lt;br&gt;&lt;/p&gt;&lt;p&gt;Please click &lt;b&gt;Previous&lt;/b&gt; to review your entries and try again, or click &lt;b&gt;Finish&lt;/b&gt; to exit without saving.&lt;/p&gt;</fieldText>
    </fields>
    <showFooter>true</showFooter>
    <showHeader>true</showHeader>
</screens>
```

---

## UX Best Practices Demonstrated

### 1. Progress Indicators
Every screen shows "Step X of 3" to orient users.

### 2. Clear Instructions
- Welcome screen explains time commitment (2 minutes)
- Form screen explains required fields (*)
- Help text on complex fields

### 3. Input Preservation
`inputsOnNextNavToAssocScrn="UseStoredValues"` preserves user input when navigating back.

### 4. Strategic Back Button Control
| Screen | allowBack | Reason |
|--------|-----------|--------|
| Welcome | false | No previous screen |
| Form | true | Let users go back to re-read instructions |
| Thank You | **false** | **Prevent duplicate submission** |
| Error | true | Let users try again |

### 5. User-Friendly Error Messages
- Technical `$Flow.FaultMessage` displayed in italic
- Clear instruction on recovery options
- Both "Previous" and "Finish" available

### 6. Consistent Visual Hierarchy
- Large, bold headers (20px)
- Subdued progress text (gray)
- Success confirmation with checkmark
- Error text in red

---

## Testing Checklist (v2.0.0)

### Path Coverage
- [ ] Happy path: Welcome → Form → Create → Thank You
- [ ] Error path: Welcome → Form → Error → (Previous) → Form → Success
- [ ] Exit from error: Welcome → Form → Error → Finish

### Navigation Testing
- [ ] Welcome: No "Previous" button visible
- [ ] Form: Both "Previous" and "Next" visible
- [ ] Thank You: No "Previous" button (prevents duplicate)
- [ ] Error: Both "Previous" and "Finish" visible

### Input Validation
- [ ] Empty product → validation message
- [ ] Rating 0 or 6 → validation message (if min/max configured)
- [ ] All required fields empty → validation messages
- [ ] Long comments (32,000+ chars) → handled gracefully

### User Context
- [ ] Works as System Administrator
- [ ] Works as Standard User
- [ ] Works as Community User (if exposed externally)

### Edge Cases
- [ ] Special characters in comments: `<>&"'`
- [ ] Unicode/Emoji in comments
- [ ] Browser back button behavior
- [ ] Session timeout handling

---

## Skill Workflow

### Phase 1: Requirements Gathering

The skill asks:

**Q1: What type of flow?**
→ Screen Flow

**Q2: What is the purpose?**
→ "Collect customer feedback and save to Feedback__c object"

**Q3: Target org?**
→ "sandbox"

### Phase 2: Flow Design

The skill designs:
- **Screen 1**: Welcome message with progress indicator
- **Screen 2**: Feedback form with validation
- **Create Record**: Save to Feedback__c (with fault path)
- **Screen 3**: Thank you confirmation (back disabled)
- **Error Screen**: Recovery option (back enabled)

### Phase 3: Validation

```
Flow Validation Report: Customer_Feedback_Screen_Flow (API 66.0)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Score: 108/110 ⭐⭐⭐⭐⭐ Excellent
├─ Design & Naming: 20/20 (100%) ✓
├─ Logic & Structure: 20/20 (100%) ✓
├─ Architecture: 13/15 (87%)
├─ Performance & Bulk Safety: 20/20 (100%) ✓
├─ Error Handling: 20/20 (100%) ✓
└─ Security: 15/15 (100%) ✓

✓ Variable naming follows v2.0.0 prefixes (var_, out_)
✓ All DML has fault connectors
✓ Progress indicators on all screens
✓ Back button disabled on success screen

✓ VALIDATION PASSED - Flow ready for deployment
```

### Phase 4: Deployment

**Step 1: Check-Only Validation**
```
Deploying flow with --dry-run flag...
✓ Validation successful
✓ No org-specific errors
✓ Ready for actual deployment
```

**Step 2: Actual Deployment**
```
Deploying to sandbox...
✓ Deployment successful
Job ID: 0Af5g00000XXXXX
Flow deployed as Draft
```

### Phase 5: Testing

Follow the testing checklist above, then activate when ready.

---

## Related Resources

- [Screen Flow Template](../assets/screen-flow-template.xml) - Base template with UX guidance
- [Flow Best Practices](../references/flow-best-practices.md) - Comprehensive UX patterns
- [Testing Guide](../references/testing-guide.md) - Testing strategies
- [Testing Checklist](../references/testing-checklist.md) - Quick reference
