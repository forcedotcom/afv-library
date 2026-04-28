<!-- Parent: sf-flow/SKILL.md -->
# Flow + LWC Integration Guide

This guide covers embedding custom Lightning Web Components in Flow Screens.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                   FLOW SCREEN + LWC ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                      FLOW (Screen)                           │   │
│   │  ┌──────────────────────────────────────────────────────┐   │   │
│   │  │                  screens element                      │   │   │
│   │  │    ┌──────────────────────────────────────────────┐  │   │   │
│   │  │    │           fields > componentInstance         │  │   │   │
│   │  │    │                                              │  │   │   │
│   │  │    │   extensionName="c:myComponent"              │  │   │   │
│   │  │    │                                              │  │   │   │
│   │  │    │   inputParameters ────────────▶ @api (in)    │  │   │   │
│   │  │    │   outputParameters ◀────────── @api (out)    │  │   │   │
│   │  │    │                                              │  │   │   │
│   │  │    └──────────────────────────────────────────────┘  │   │   │
│   │  └──────────────────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quick Reference

| Flow Element | LWC Requirement | Purpose |
|--------------|-----------------|---------|
| `extensionName` | `target="lightning__FlowScreen"` | Identify LWC component |
| `inputParameters` | `@api` with `role="inputOnly"` | Flow → LWC data |
| `outputParameters` | `@api` with `role="outputOnly"` | LWC → Flow data |
| N/A | `FlowAttributeChangeEvent` | LWC updates outputs |
| N/A | `FlowNavigationFinishEvent` | LWC controls navigation |

---

## Flow XML Structure

### Basic Screen with LWC

```xml
<screens>
    <name>My_LWC_Screen</name>
    <label>Custom Component Screen</label>
    <locationX>176</locationX>
    <locationY>158</locationY>
    <connector>
        <targetReference>Next_Element</targetReference>
    </connector>
    <showFooter>true</showFooter>
    <showHeader>true</showHeader>

    <fields>
        <name>myLwcField</name>
        <!-- Component reference: namespace:componentName -->
        <extensionName>c:myFlowComponent</extensionName>
        <fieldType>ComponentInstance</fieldType>

        <!-- Flow → LWC (inputs) -->
        <inputParameters>
            <name>recordId</name>
            <value>
                <elementReference>var_RecordId</elementReference>
            </value>
        </inputParameters>

        <!-- LWC → Flow (outputs) -->
        <outputParameters>
            <assignToReference>var_SelectedId</assignToReference>
            <name>selectedRecordId</name>
        </outputParameters>
    </fields>
</screens>
```

---

## Input Parameters

Pass data from Flow variables to LWC `@api` properties.

### Value Types

```xml
<!-- String literal -->
<inputParameters>
    <name>mode</name>
    <value>
        <stringValue>edit</stringValue>
    </value>
</inputParameters>

<!-- Boolean literal -->
<inputParameters>
    <name>showDetails</name>
    <value>
        <booleanValue>true</booleanValue>
    </value>
</inputParameters>

<!-- Number literal -->
<inputParameters>
    <name>maxRecords</name>
    <value>
        <numberValue>10</numberValue>
    </value>
</inputParameters>

<!-- Flow variable reference -->
<inputParameters>
    <name>recordId</name>
    <value>
        <elementReference>var_CurrentRecordId</elementReference>
    </value>
</inputParameters>

<!-- Record variable (SObject) -->
<inputParameters>
    <name>account</name>
    <value>
        <elementReference>get_Account</elementReference>
    </value>
</inputParameters>

<!-- Collection variable -->
<inputParameters>
    <name>selectedIds</name>
    <value>
        <elementReference>col_SelectedRecordIds</elementReference>
    </value>
</inputParameters>
```

### LWC Property Declaration

```javascript
// LWC must declare matching @api properties
@api recordId;      // Maps to inputParameter name="recordId"
@api mode;          // Maps to inputParameter name="mode"
@api showDetails;   // Maps to inputParameter name="showDetails"
@api maxRecords;    // Maps to inputParameter name="maxRecords"
```

---

## Output Parameters

Receive data from LWC `@api` properties into Flow variables.

### Flow XML

```xml
<!-- Simple value output -->
<outputParameters>
    <assignToReference>var_SelectedRecordId</assignToReference>
    <name>selectedRecordId</name>
</outputParameters>

<!-- Boolean output -->
<outputParameters>
    <assignToReference>var_IsComplete</assignToReference>
    <name>isComplete</name>
</outputParameters>

<!-- Collection output -->
<outputParameters>
    <assignToReference>col_SelectedIds</assignToReference>
    <name>selectedIds</name>
</outputParameters>
```

### LWC Dispatching Updates

**CRITICAL**: LWC must dispatch `FlowAttributeChangeEvent` for outputs to update.

```javascript
import { FlowAttributeChangeEvent } from 'lightning/flowSupport';

@api selectedRecordId;

handleSelection(event) {
    this.selectedRecordId = event.detail.id;

    // REQUIRED: Notify Flow of the change
    this.dispatchEvent(new FlowAttributeChangeEvent(
        'selectedRecordId',    // Property name (must match meta.xml)
        this.selectedRecordId  // New value
    ));
}
```

---

## Variable Types Mapping

| Flow Type | LWC Type | XML Declaration |
|-----------|----------|-----------------|
| `String` | `String` | `<dataType>String</dataType>` |
| `Number` | `Number` | `<dataType>Number</dataType>` |
| `Currency` | `Number` | `<dataType>Currency</dataType>` |
| `Boolean` | `Boolean` | `<dataType>Boolean</dataType>` |
| `Date` | `String` | `<dataType>Date</dataType>` |
| `DateTime` | `String` | `<dataType>DateTime</dataType>` |
| `Record` | `Object` | `<objectType>Account</objectType>` |
| `Collection` | `Array` | `<isCollection>true</isCollection>` |

### Variable Declaration Examples

```xml
<!-- String variable -->
<variables>
    <name>var_SelectedId</name>
    <dataType>String</dataType>
    <isCollection>false</isCollection>
    <isInput>false</isInput>
    <isOutput>false</isOutput>
</variables>

<!-- Boolean variable with default -->
<variables>
    <name>var_IsComplete</name>
    <dataType>Boolean</dataType>
    <isCollection>false</isCollection>
    <isInput>false</isInput>
    <isOutput>false</isOutput>
    <value>
        <booleanValue>false</booleanValue>
    </value>
</variables>

<!-- Collection of strings -->
<variables>
    <name>col_SelectedIds</name>
    <dataType>String</dataType>
    <isCollection>true</isCollection>
    <isInput>false</isInput>
    <isOutput>false</isOutput>
</variables>

<!-- Record variable -->
<variables>
    <name>var_Account</name>
    <dataType>SObject</dataType>
    <isCollection>false</isCollection>
    <isInput>false</isInput>
    <isOutput>false</isOutput>
    <objectType>Account</objectType>
</variables>
```

---

## Validation Patterns

### Check LWC Output Before Proceeding

```xml
<screens>
    <name>LWC_Screen</name>
    <!-- ... -->
    <connector>
        <targetReference>Validate_Output</targetReference>
    </connector>
</screens>

<decisions>
    <name>Validate_Output</name>
    <label>Validate LWC Output</label>
    <defaultConnector>
        <targetReference>Show_Error</targetReference>
    </defaultConnector>
    <defaultConnectorLabel>Invalid</defaultConnectorLabel>
    <rules>
        <name>Is_Valid</name>
        <conditionLogic>and</conditionLogic>
        <conditions>
            <leftValueReference>var_SelectedId</leftValueReference>
            <operator>IsNull</operator>
            <rightValue>
                <booleanValue>false</booleanValue>
            </rightValue>
        </conditions>
        <connector>
            <targetReference>Continue_Flow</targetReference>
        </connector>
        <label>Valid Selection</label>
    </rules>
</decisions>
```

### LWC-Side Validation

```javascript
@api validate() {
    // Flow calls this when user clicks Next
    if (!this.selectedRecordId) {
        return {
            isValid: false,
            errorMessage: 'Please select a record before continuing.'
        };
    }
    return { isValid: true };
}
```

---

## Screen Configuration

### Navigation Options

```xml
<screens>
    <name>My_Screen</name>
    <allowBack>true</allowBack>      <!-- Show Back button -->
    <allowFinish>true</allowFinish>  <!-- Allow Finish (last screen) -->
    <allowPause>true</allowPause>    <!-- Show Pause button -->
    <showFooter>true</showFooter>    <!-- Show button bar -->
    <showHeader>true</showHeader>    <!-- Show screen label -->
</screens>
```

### Hiding Standard Navigation

When LWC handles its own navigation:

```xml
<screens>
    <name>Custom_Nav_Screen</name>
    <showFooter>false</showFooter>  <!-- LWC provides buttons -->
    <!-- ... -->
</screens>
```

LWC then uses:
```javascript
import { FlowNavigationFinishEvent } from 'lightning/flowSupport';

handleNext() {
    this.dispatchEvent(new FlowNavigationFinishEvent('NEXT'));
}
```

---

## Multiple LWCs in One Screen

```xml
<screens>
    <name>Multi_LWC_Screen</name>
    <label>Multiple Components</label>

    <!-- First LWC -->
    <fields>
        <name>headerComponent</name>
        <extensionName>c:flowHeader</extensionName>
        <fieldType>ComponentInstance</fieldType>
        <inputParameters>
            <name>title</name>
            <value><stringValue>Select Options</stringValue></value>
        </inputParameters>
    </fields>

    <!-- Standard Flow field between LWCs -->
    <fields>
        <name>instructions</name>
        <fieldText>&lt;p&gt;Choose from the options below&lt;/p&gt;</fieldText>
        <fieldType>DisplayText</fieldType>
    </fields>

    <!-- Second LWC -->
    <fields>
        <name>selectorComponent</name>
        <extensionName>c:recordSelector</extensionName>
        <fieldType>ComponentInstance</fieldType>
        <outputParameters>
            <assignToReference>var_SelectedId</assignToReference>
            <name>selectedId</name>
        </outputParameters>
    </fields>
</screens>
```

---

## Error Handling

### Capture LWC Error Output

```xml
<fields>
    <outputParameters>
        <assignToReference>var_ErrorMessage</assignToReference>
        <name>errorMessage</name>
    </outputParameters>
</fields>

<!-- Check for errors after screen -->
<decisions>
    <name>Check_Errors</name>
    <rules>
        <name>Has_Error</name>
        <conditions>
            <leftValueReference>var_ErrorMessage</leftValueReference>
            <operator>IsNull</operator>
            <rightValue>
                <booleanValue>false</booleanValue>
            </rightValue>
        </conditions>
        <connector>
            <targetReference>Error_Handler</targetReference>
        </connector>
    </rules>
</decisions>
```

### LWC Dispatching Errors

```javascript
handleError(error) {
    this.errorMessage = this.reduceErrors(error);
    this.dispatchEvent(new FlowAttributeChangeEvent(
        'errorMessage',
        this.errorMessage
    ));
}
```

---

## Context Variables

Pass Flow context to LWC using record context:

```xml
<!-- In Flow: Map $Record context -->
<inputParameters>
    <name>recordId</name>
    <value>
        <elementReference>$Record.Id</elementReference>
    </value>
</inputParameters>
<inputParameters>
    <name>objectApiName</name>
    <value>
        <elementReference>$Record.Object</elementReference>
    </value>
</inputParameters>
```

---

## Templates

| Template | Use Case |
|----------|----------|
| `assets/screen-flow-with-lwc.xml` | Complete LWC screen integration |
| `assets/apex-action-template.xml` | Calling Apex from Flow |

---

## Cross-Skill Integration

| Integration | See Also |
|-------------|----------|
| LWC Component Setup | [sf-lwc/references/flow-integration-guide.md](../../sf-lwc/references/flow-integration-guide.md) |
| Full Triangle Architecture | [triangle-pattern.md](triangle-pattern.md) |
| LWC FlowAttributeChangeEvent | [sf-lwc/assets/flow-screen-component/](../../sf-lwc/assets/flow-screen-component/) |

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| LWC not appearing in Flow Builder | Missing `isExposed` or target | Add `isExposed=true` and `target="lightning__FlowScreen"` |
| Properties not showing in builder | Missing `targetConfigs` | Add `targetConfig` with property definitions |
| Outputs not updating | Missing FlowAttributeChangeEvent | Dispatch event when value changes |
| Type mismatch error | Wrong dataType | Match Flow variable type to LWC property type |
| LWC not receiving inputs | Property name mismatch | Ensure `name` matches `@api` property exactly |
| Navigation not working | Wrong event type | Use `FlowNavigationFinishEvent` with action string |
