<!-- Parent: sf-flow/SKILL.md -->
# Flow-LWC-Apex Triangle: Flow Perspective

The **Triangle Architecture** is a foundational Salesforce pattern where Flow, LWC, and Apex work together. This guide focuses on the **Flow role** as the orchestrator.

---

## Architecture Overview

```
                         ┌─────────────────────────────────────┐
                         │              FLOW              ◀── YOU ARE HERE
                         │         (Orchestrator)              │
                         │                                     │
                         │  • Process Logic                    │
                         │  • User Experience                  │
                         │  • Variable Management              │
                         └───────────────┬─────────────────────┘
                                         │
              ┌──────────────────────────┼──────────────────────────┐
              │                          │                          │
              │ screens                  │ actionCalls              │
              │ <componentInstance>      │ actionType="apex"        │
              │                          │                          │
              ▼                          ▼                          ▲
┌─────────────────────────┐    ┌─────────────────────────┐         │
│          LWC            │    │         APEX            │         │
│     (UI Component)      │───▶│   (Business Logic)      │─────────┘
│                         │    │                         │
│ • Rich UI/UX            │    │ • @InvocableMethod      │
│ • User Interaction      │    │ • @AuraEnabled          │
│ • FlowAttribute         │    │ • Complex Logic         │
│   ChangeEvent           │    │ • DML Operations        │
│ • FlowNavigation        │    │ • Integration           │
│   FinishEvent           │    │                         │
└─────────────────────────┘    └─────────────────────────┘
```

---

## Flow's Role in the Triangle

| Communication Path | Flow XML Element | Direction |
|-------------------|------------------|-----------|
| Flow → LWC | `inputParameters` in `<screens>` | Push data to component |
| LWC → Flow | `outputParameters` in `<screens>` | Receive from component |
| Flow → Apex | `actionCalls` with `actionType="apex"` | Call Invocable |
| Apex → Flow | `outputParameters` in `<actionCalls>` | Receive results |

---

## Pattern 1: Flow Embedding LWC Screen Component

**Use Case**: Custom UI component for user selection within a guided Flow.

```
┌─────────┐     inputParameters     ┌─────────┐
│  FLOW   │ ─────────────────────▶  │   LWC   │
│ Screen  │                         │Component│
│         │ ◀─────────────────────  │         │
│         │    outputParameters     │         │
└─────────┘                         └─────────┘
```

### Flow XML

```xml
<screens>
    <name>Select_Record_Screen</name>
    <label>Select Record</label>
    <locationX>264</locationX>
    <locationY>398</locationY>
    <allowBack>true</allowBack>
    <allowFinish>true</allowFinish>
    <allowPause>false</allowPause>
    <connector>
        <targetReference>Process_Selection</targetReference>
    </connector>
    <fields>
        <name>recordSelectorComponent</name>
        <extensionName>c:recordSelector</extensionName>
        <fieldType>ComponentInstance</fieldType>
        <inputParameters>
            <name>recordId</name>
            <value>
                <elementReference>var_ParentRecordId</elementReference>
            </value>
        </inputParameters>
        <outputParameters>
            <assignToReference>var_SelectedRecordId</assignToReference>
            <name>selectedRecordId</name>
        </outputParameters>
    </fields>
</screens>
```

### Variable Definitions

```xml
<variables>
    <name>var_ParentRecordId</name>
    <dataType>String</dataType>
    <isCollection>false</isCollection>
    <isInput>true</isInput>
    <isOutput>false</isOutput>
</variables>
<variables>
    <name>var_SelectedRecordId</name>
    <dataType>String</dataType>
    <isCollection>false</isCollection>
    <isInput>false</isInput>
    <isOutput>true</isOutput>
</variables>
```

---

## Pattern 2: Flow Calling Apex Invocable

**Use Case**: Complex business logic, DML, or external integrations.

```
┌─────────┐   actionCalls    ┌─────────┐
│  FLOW   │ ───────────────▶ │  APEX   │
│         │   inputParams    │@Invocable│
│         │ ◀─────────────── │ Method   │
│         │   outputParams   │          │
└─────────┘                  └─────────┘
```

### Flow XML

```xml
<actionCalls>
    <name>Process_Records</name>
    <label>Process Records</label>
    <locationX>440</locationX>
    <locationY>518</locationY>
    <actionName>RecordProcessor</actionName>
    <actionType>apex</actionType>
    <connector>
        <targetReference>Show_Success</targetReference>
    </connector>
    <faultConnector>
        <targetReference>Handle_Error</targetReference>
    </faultConnector>
    <inputParameters>
        <name>recordId</name>
        <value>
            <elementReference>var_RecordId</elementReference>
        </value>
    </inputParameters>
    <inputParameters>
        <name>processType</name>
        <value>
            <stringValue>FULL</stringValue>
        </value>
    </inputParameters>
    <outputParameters>
        <assignToReference>var_IsSuccess</assignToReference>
        <name>isSuccess</name>
    </outputParameters>
    <outputParameters>
        <assignToReference>var_ProcessedId</assignToReference>
        <name>processedId</name>
    </outputParameters>
    <outputParameters>
        <assignToReference>var_ErrorMessage</assignToReference>
        <name>errorMessage</name>
    </outputParameters>
    <storeOutputAutomatically>false</storeOutputAutomatically>
</actionCalls>
```

### Fault Handling

```xml
<screens>
    <name>Handle_Error</name>
    <label>Error</label>
    <locationX>660</locationX>
    <locationY>638</locationY>
    <fields>
        <name>ErrorDisplay</name>
        <fieldText>&lt;p&gt;&lt;strong&gt;An error occurred:&lt;/strong&gt;&lt;/p&gt;&lt;p&gt;{!$Flow.FaultMessage}&lt;/p&gt;</fieldText>
        <fieldType>DisplayText</fieldType>
    </fields>
</screens>
```

---

## Pattern 3: Full Triangle Flow

**Use Case**: Complete solution combining LWC screens and Apex actions.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <label>Quote Builder Flow</label>
    <processType>Flow</processType>
    <status>Active</status>
    <interviewLabel>Quote Builder {!$Flow.CurrentDateTime}</interviewLabel>

    <!-- Start -->
    <start>
        <locationX>50</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Select_Products_Screen</targetReference>
        </connector>
    </start>

    <!-- LWC Screen: Product Selection -->
    <screens>
        <name>Select_Products_Screen</name>
        <label>Select Products</label>
        <connector>
            <targetReference>Calculate_Pricing_Apex</targetReference>
        </connector>
        <fields>
            <name>productSelectorLWC</name>
            <extensionName>c:productSelector</extensionName>
            <fieldType>ComponentInstance</fieldType>
            <inputParameters>
                <name>accountId</name>
                <value><elementReference>var_AccountId</elementReference></value>
            </inputParameters>
            <outputParameters>
                <assignToReference>var_SelectedProductIds</assignToReference>
                <name>selectedProducts</name>
            </outputParameters>
        </fields>
    </screens>

    <!-- Apex Action: Calculate Pricing -->
    <actionCalls>
        <name>Calculate_Pricing_Apex</name>
        <actionName>PricingCalculator</actionName>
        <actionType>apex</actionType>
        <connector>
            <targetReference>Review_Quote_Screen</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Pricing_Error_Screen</targetReference>
        </faultConnector>
        <inputParameters>
            <name>productIds</name>
            <value><elementReference>var_SelectedProductIds</elementReference></value>
        </inputParameters>
        <inputParameters>
            <name>accountId</name>
            <value><elementReference>var_AccountId</elementReference></value>
        </inputParameters>
        <outputParameters>
            <assignToReference>var_QuoteLineItems</assignToReference>
            <name>lineItems</name>
        </outputParameters>
        <outputParameters>
            <assignToReference>var_TotalPrice</assignToReference>
            <name>totalPrice</name>
        </outputParameters>
    </actionCalls>

    <!-- LWC Screen: Review Quote -->
    <screens>
        <name>Review_Quote_Screen</name>
        <label>Review Quote</label>
        <connector>
            <targetReference>Create_Quote_Record</targetReference>
        </connector>
        <fields>
            <name>quoteReviewLWC</name>
            <extensionName>c:quoteReview</extensionName>
            <fieldType>ComponentInstance</fieldType>
            <inputParameters>
                <name>lineItems</name>
                <value><elementReference>var_QuoteLineItems</elementReference></value>
            </inputParameters>
            <inputParameters>
                <name>totalPrice</name>
                <value><elementReference>var_TotalPrice</elementReference></value>
            </inputParameters>
            <outputParameters>
                <assignToReference>var_ApprovedForSubmit</assignToReference>
                <name>isApproved</name>
            </outputParameters>
        </fields>
    </screens>

    <!-- Variables -->
    <variables>
        <name>var_AccountId</name>
        <dataType>String</dataType>
        <isInput>true</isInput>
    </variables>
    <variables>
        <name>var_SelectedProductIds</name>
        <dataType>String</dataType>
        <isCollection>true</isCollection>
    </variables>
    <variables>
        <name>var_QuoteLineItems</name>
        <dataType>Apex</dataType>
        <apexClass>QuoteLineItemWrapper</apexClass>
        <isCollection>true</isCollection>
    </variables>
    <variables>
        <name>var_TotalPrice</name>
        <dataType>Currency</dataType>
    </variables>
</Flow>
```

---

## Testing Flow with Apex

```apex
@isTest
private class QuoteBuilderFlowTest {
    @isTest
    static void testFlowWithApexIntegration() {
        // Setup test data
        Account acc = new Account(Name = 'Test Account');
        insert acc;

        Product2 prod = new Product2(Name = 'Test Product', IsActive = true);
        insert prod;

        // Flow inputs
        Map<String, Object> inputs = new Map<String, Object>{
            'var_AccountId' => acc.Id
        };

        Test.startTest();
        // Create and run Flow interview
        Flow.Interview flow = Flow.Interview.createInterview(
            'Quote_Builder_Flow',
            inputs
        );
        flow.start();
        Test.stopTest();

        // Verify Flow outputs
        Object totalPrice = flow.getVariableValue('var_TotalPrice');
        System.assertNotEquals(null, totalPrice, 'Total price should be calculated');
    }
}
```

---

## Deployment Order

When deploying integrated triangle solutions:

```
1. APEX CLASSES
   └── @InvocableMethod classes
   └── @AuraEnabled controllers

2. LWC COMPONENTS
   └── meta.xml with targets
   └── JavaScript with Flow imports

3. FLOWS                ← Deploy LAST
   └── Reference deployed Apex classes
   └── Reference deployed LWC components
```

---

## Decision Matrix: When to Use Each Approach

| Scenario | Primary | Supporting | Why |
|----------|---------|------------|-----|
| Simple record selection | LWC | - | Rich UI, immediate feedback |
| Complex multi-step process | **Flow** | Apex, LWC | Orchestration strength |
| Bulk data processing | Apex | - | Governor limit handling |
| Custom UI in guided process | **Flow** | LWC | Best of both |
| External API integration | Apex | Flow wrapper | Authentication, callouts |
| Admin-maintainable logic | **Flow** | Apex for complex ops | Low-code primary |
| User-facing wizard | **Flow** + LWC | Apex | Complete solution |

---

## Common Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| No faultConnector on Apex actions | Unhandled exceptions crash Flow | Always add fault path |
| Hardcoded IDs in Flow | Environment-specific failures | Use Custom Metadata or variables |
| Missing outputParameters | Apex results not available | Map all needed outputs |
| LWC without outputParameters | Component outputs ignored | Add outputParameters mapping |
| Skipping validation before Apex | Invalid data causes errors | Add decision elements |

---

## Related Documentation

| Topic | Location |
|-------|----------|
| Apex action template | `sf-flow/assets/apex-action-template.xml` |
| Screen Flow with LWC | `sf-flow/assets/screen-flow-with-lwc.xml` |
| LWC integration guide | `sf-flow/references/lwc-integration-guide.md` |
| Apex triangle perspective | `sf-apex/references/triangle-pattern.md` |
| LWC triangle perspective | `sf-lwc/references/triangle-pattern.md` |
