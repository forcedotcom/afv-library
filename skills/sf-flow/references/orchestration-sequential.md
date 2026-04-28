<!-- Parent: sf-flow/SKILL.md -->
# Orchestration Pattern: Sequential

## Overview

The **Sequential pattern** chains multiple flows together where each flow's output becomes the next flow's input. This creates a pipeline of transformations, with each step building on the previous one.

## When to Use This Pattern

✅ **Use Sequential when:**
- Each step depends on the previous step's output
- You need a multi-stage validation/approval process
- Data flows through a transformation pipeline
- Steps must execute in a specific order
- Each stage can be developed and tested independently

❌ **Don't use when:**
- Steps are independent and can run in parallel
- Order doesn't matter
- You need conditional branching (use Conditional pattern instead)

## Real-World Example: Order Processing Pipeline

### Business Requirement

Process customer orders through multiple stages:
1. **Validate Order**: Check inventory, pricing, customer credit
2. **Calculate Tax**: Determine tax based on shipping address and products
3. **Process Payment**: Charge payment method
4. **Reserve Inventory**: Allocate products from warehouse
5. **Generate Invoice**: Create invoice record and send to customer

Each step depends on the previous step's success. If any step fails, the pipeline stops.

## Architecture

```
Screen Flow: Order_Entry
    ↓ (User submits order)
Auto Flow: Auto_ValidateOrder
    ↓ (Outputs: varIsValid, varValidationMessage)
Auto Flow: Auto_CalculateTax
    ↓ (Outputs: varTaxAmount, varTotalAmount)
Auto Flow: Auto_ProcessPayment
    ↓ (Outputs: varPaymentId, varPaymentStatus)
Auto Flow: Auto_ReserveInventory
    ↓ (Outputs: varReservationId)
Auto Flow: Auto_GenerateInvoice
    ↓ (Outputs: varInvoiceId)
Screen Flow: Order_Confirmation (displays final results)
```

## Implementation

### Flow 1: Screen_OrderEntry

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <description>Entry point for order processing. Collects order details and initiates sequential pipeline.</description>
    <label>Screen_OrderEntry</label>
    <processType>Flow</processType>

    <!-- Screen: Collect Order Information -->
    <screens>
        <name>Order_Details_Screen</name>
        <label>Enter Order Details</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <allowBack>true</allowBack>
        <allowFinish>true</allowFinish>
        <allowPause>false</allowPause>
        <connector>
            <targetReference>Validate_Order</targetReference>
        </connector>
        <fields>
            <name>ProductId</name>
            <dataType>String</dataType>
            <fieldText>Product</fieldText>
            <fieldType>InputField</fieldType>
            <isRequired>true</isRequired>
        </fields>
        <fields>
            <name>Quantity</name>
            <dataType>Number</dataType>
            <fieldText>Quantity</fieldText>
            <fieldType>InputField</fieldType>
            <isRequired>true</isRequired>
            <scale>0</scale>
        </fields>
        <fields>
            <name>ShippingAddress</name>
            <dataType>String</dataType>
            <fieldText>Shipping Address</fieldText>
            <fieldType>LargeTextArea</fieldType>
            <isRequired>true</isRequired>
        </fields>
        <showFooter>true</showFooter>
        <showHeader>true</showHeader>
    </screens>

    <!-- Step 1: Validate Order -->
    <subflows>
        <name>Validate_Order</name>
        <label>Validate Order</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Check_Validation_Result</targetReference>
        </connector>
        <flowName>Auto_ValidateOrder</flowName>
        <inputAssignments>
            <name>varProductId</name>
            <value>
                <elementReference>ProductId</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>varQuantity</name>
            <value>
                <elementReference>Quantity</elementReference>
            </value>
        </inputAssignments>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </subflows>

    <!-- Decision: Did validation pass? -->
    <decisions>
        <name>Check_Validation_Result</name>
        <label>Validation Passed?</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <defaultConnector>
            <targetReference>Show_Validation_Error</targetReference>
        </defaultConnector>
        <defaultConnectorLabel>Failed</defaultConnectorLabel>
        <rules>
            <name>Validation_Passed</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>Validate_Order.varIsValid</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <booleanValue>true</booleanValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Calculate_Tax</targetReference>
            </connector>
            <label>Passed</label>
        </rules>
    </decisions>

    <!-- Step 2: Calculate Tax (only if validation passed) -->
    <subflows>
        <name>Calculate_Tax</name>
        <label>Calculate Tax</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Process_Payment</targetReference>
        </connector>
        <flowName>Auto_CalculateTax</flowName>
        <inputAssignments>
            <name>varProductId</name>
            <value>
                <elementReference>ProductId</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>varQuantity</name>
            <value>
                <elementReference>Quantity</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>varShippingAddress</name>
            <value>
                <elementReference>ShippingAddress</elementReference>
            </value>
        </inputAssignments>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </subflows>

    <!-- Step 3: Process Payment (uses tax calculation output) -->
    <subflows>
        <name>Process_Payment</name>
        <label>Process Payment</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Check_Payment_Result</targetReference>
        </connector>
        <flowName>Auto_ProcessPayment</flowName>
        <inputAssignments>
            <name>varTotalAmount</name>
            <value>
                <elementReference>Calculate_Tax.varTotalAmount</elementReference>
            </value>
        </inputAssignments>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </subflows>

    <!-- Decision: Did payment succeed? -->
    <decisions>
        <name>Check_Payment_Result</name>
        <label>Payment Successful?</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <defaultConnector>
            <targetReference>Show_Payment_Error</targetReference>
        </defaultConnector>
        <defaultConnectorLabel>Failed</defaultConnectorLabel>
        <rules>
            <name>Payment_Successful</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>Process_Payment.varPaymentStatus</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>Success</stringValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Reserve_Inventory</targetReference>
            </connector>
            <label>Success</label>
        </rules>
    </decisions>

    <!-- Step 4: Reserve Inventory (only after successful payment) -->
    <subflows>
        <name>Reserve_Inventory</name>
        <label>Reserve Inventory</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Generate_Invoice</targetReference>
        </connector>
        <flowName>Auto_ReserveInventory</flowName>
        <inputAssignments>
            <name>varProductId</name>
            <value>
                <elementReference>ProductId</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>varQuantity</name>
            <value>
                <elementReference>Quantity</elementReference>
            </value>
        </inputAssignments>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </subflows>

    <!-- Step 5: Generate Invoice (final step) -->
    <subflows>
        <name>Generate_Invoice</name>
        <label>Generate Invoice</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Show_Confirmation</targetReference>
        </connector>
        <flowName>Auto_GenerateInvoice</flowName>
        <inputAssignments>
            <name>varProductId</name>
            <value>
                <elementReference>ProductId</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>varQuantity</name>
            <value>
                <elementReference>Quantity</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>varTaxAmount</name>
            <value>
                <elementReference>Calculate_Tax.varTaxAmount</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>varTotalAmount</name>
            <value>
                <elementReference>Calculate_Tax.varTotalAmount</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <name>varPaymentId</name>
            <value>
                <elementReference>Process_Payment.varPaymentId</elementReference>
            </value>
        </inputAssignments>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </subflows>

    <!-- Success Screen -->
    <screens>
        <name>Show_Confirmation</name>
        <label>Order Confirmation</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <allowBack>false</allowBack>
        <allowFinish>true</allowFinish>
        <allowPause>false</allowPause>
        <fields>
            <name>ConfirmationMessage</name>
            <fieldText>Order Successful! Invoice #{!Generate_Invoice.varInvoiceNumber} has been created.</fieldText>
            <fieldType>DisplayText</fieldType>
        </fields>
        <showFooter>true</showFooter>
        <showHeader>true</showHeader>
    </screens>

    <!-- Error Screens -->
    <screens>
        <name>Show_Validation_Error</name>
        <label>Validation Error</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <allowBack>true</allowBack>
        <allowFinish>true</allowFinish>
        <allowPause>false</allowPause>
        <fields>
            <name>ValidationErrorMessage</name>
            <fieldText>Order validation failed: {!Validate_Order.varValidationMessage}</fieldText>
            <fieldType>DisplayText</fieldType>
        </fields>
        <showFooter>true</showFooter>
        <showHeader>true</showHeader>
    </screens>

    <screens>
        <name>Show_Payment_Error</name>
        <label>Payment Error</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <allowBack>false</allowBack>
        <allowFinish>true</allowFinish>
        <allowPause>false</allowPause>
        <fields>
            <name>PaymentErrorMessage</name>
            <fieldText>Payment failed. Your order has not been processed.</fieldText>
            <fieldType>DisplayText</fieldType>
        </fields>
        <showFooter>true</showFooter>
        <showHeader>true</showHeader>
    </screens>

    <start>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Order_Details_Screen</targetReference>
        </connector>
    </start>
    <status>Draft</status>
</Flow>
```

### Flow 2: Auto_ValidateOrder

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <description>First step in sequential pipeline. Validates order details and returns validation status.</description>
    <label>Auto_ValidateOrder</label>
    <processType>AutoLaunchedFlow</processType>

    <!-- Query Product for Availability Check -->
    <recordLookups>
        <name>Get_Product_Details</name>
        <label>Get Product Details</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <assignNullValuesIfNoRecordsFound>false</assignNullValuesIfNoRecordsFound>
        <connector>
            <targetReference>Check_Product_Found</targetReference>
        </connector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>varProductId</elementReference>
            </value>
        </filters>
        <getFirstRecordOnly>true</getFirstRecordOnly>
        <object>Product2</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordLookups>

    <!-- Validation Logic -->
    <decisions>
        <name>Check_Product_Found</name>
        <label>Product Exists?</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <defaultConnector>
            <targetReference>Set_Invalid_Product</targetReference>
        </defaultConnector>
        <defaultConnectorLabel>Not Found</defaultConnectorLabel>
        <rules>
            <name>Product_Exists</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>Get_Product_Details</leftValueReference>
                <operator>IsNull</operator>
                <rightValue>
                    <booleanValue>false</booleanValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Check_Quantity</targetReference>
            </connector>
            <label>Exists</label>
        </rules>
    </decisions>

    <decisions>
        <name>Check_Quantity</name>
        <label>Quantity Valid?</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <defaultConnector>
            <targetReference>Set_Invalid_Quantity</targetReference>
        </defaultConnector>
        <defaultConnectorLabel>Invalid</defaultConnectorLabel>
        <rules>
            <name>Quantity_Valid</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>varQuantity</leftValueReference>
                <operator>GreaterThan</operator>
                <rightValue>
                    <numberValue>0.0</numberValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Set_Valid</targetReference>
            </connector>
            <label>Valid</label>
        </rules>
    </decisions>

    <!-- Set Validation Results -->
    <assignments>
        <name>Set_Valid</name>
        <label>Set Valid</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <assignmentItems>
            <assignToReference>varIsValid</assignToReference>
            <operator>Assign</operator>
            <value>
                <booleanValue>true</booleanValue>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>varValidationMessage</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Validation passed</stringValue>
            </value>
        </assignmentItems>
    </assignments>

    <assignments>
        <name>Set_Invalid_Product</name>
        <label>Set Invalid Product</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <assignmentItems>
            <assignToReference>varIsValid</assignToReference>
            <operator>Assign</operator>
            <value>
                <booleanValue>false</booleanValue>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>varValidationMessage</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Product not found</stringValue>
            </value>
        </assignmentItems>
    </assignments>

    <assignments>
        <name>Set_Invalid_Quantity</name>
        <label>Set Invalid Quantity</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <assignmentItems>
            <assignToReference>varIsValid</assignToReference>
            <operator>Assign</operator>
            <value>
                <booleanValue>false</booleanValue>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>varValidationMessage</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Quantity must be greater than 0</stringValue>
            </value>
        </assignmentItems>
    </assignments>

    <start>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Get_Product_Details</targetReference>
        </connector>
    </start>
    <status>Draft</status>

    <!-- Input Variables -->
    <variables>
        <name>varProductId</name>
        <dataType>String</dataType>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>varQuantity</name>
        <dataType>Number</dataType>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
        <scale>0</scale>
    </variables>

    <!-- Output Variables -->
    <variables>
        <name>varIsValid</name>
        <dataType>Boolean</dataType>
        <isInput>false</isInput>
        <isOutput>true</isOutput>
        <value>
            <booleanValue>false</booleanValue>
        </value>
    </variables>
    <variables>
        <name>varValidationMessage</name>
        <dataType>String</dataType>
        <isInput>false</isInput>
        <isOutput>true</isOutput>
    </variables>
</Flow>
```

## Key Characteristics

### 1. **Linear Flow**
Each step executes only after the previous step completes:
```
Step 1 → Output → Step 2 → Output → Step 3 → Output → Step 4
```

### 2. **Data Propagation**
Outputs from earlier steps are passed as inputs to later steps:
```
Calculate_Tax.varTotalAmount → Process_Payment.varTotalAmount
Process_Payment.varPaymentId → Generate_Invoice.varPaymentId
```

### 3. **Fail-Fast Behavior**
If any step fails, the pipeline stops:
```
Validation Failed → Show Error → End (no further processing)
Payment Failed → Show Error → End (inventory not reserved)
```

### 4. **Clear Exit Points**
Each validation point can terminate the flow early, preventing unnecessary work.

## Benefits of Sequential Pattern

### ✅ Staged Processing
- Break complex workflows into digestible stages
- Each stage has clear inputs and outputs
- Easy to understand flow of data

### ✅ Error Isolation
- Know exactly which stage failed
- Can retry individual stages
- Log shows precise failure point

### ✅ Flexibility
- Add new stages easily
- Remove stages without affecting others
- Reorder stages if dependencies allow

### ✅ Testing
- Test each stage independently
- Mock outputs for downstream testing
- Verify data transformation at each step

## Common Use Cases

1. **Order Processing**: Validate → Calculate → Charge → Fulfill → Invoice
2. **Approval Workflows**: Submit → Manager Approval → Director Approval → Execute
3. **Data Transformation**: Extract → Transform → Validate → Load
4. **Document Generation**: Gather Data → Apply Template → Generate PDF → Send
5. **Multi-Step Validation**: Check A → Check B → Check C → Approve

## Best Practices

### ✅ DO:

1. **Define Clear Contracts**: Each flow should have well-defined inputs and outputs
2. **Use Output Variables**: Pass data between stages via output variables
3. **Validate at Each Stage**: Check prerequisites before expensive operations
4. **Log Stage Completion**: Track which stages completed successfully
5. **Design for Rollback**: Consider how to undo if later stages fail

### ❌ DON'T:

1. **Create Circular Dependencies**: A → B → C → A (infinite loop!)
2. **Skip Error Handling**: Every stage should have fault paths
3. **Make Steps Too Large**: Each stage should do ONE thing well
4. **Ignore Performance**: Sequential = slower than parallel (by design)
5. **Hardcode Values**: Use variables to pass data between stages

## Performance Considerations

### Sequential = Longer Execution Time

```
Parallel (3 seconds total):
Step A (1s) ───┐
Step B (1s) ───┼──→ Complete
Step C (1s) ───┘

Sequential (3 seconds total):
Step A (1s) → Step B (1s) → Step C (1s) → Complete
```

**Trade-off**: Sequential is slower but provides:
- Better error handling
- Clear data flow
- Easier debugging
- Predictable execution order

## Error Handling in Pipelines

### Strategy 1: Fail Fast
Stop on first error (shown in example above)

### Strategy 2: Collect and Report
Continue through all steps, collect all errors, report at end:

```xml
<!-- Track errors but don't stop -->
<assignments>
    <name>Add_To_Error_List</name>
    <assignmentItems>
        <assignToReference>colErrors</assignToReference>
        <operator>Add</operator>
        <value>
            <elementReference>$Flow.FaultMessage</elementReference>
        </value>
    </assignmentItems>
    <connector>
        <targetReference>Next_Step</targetReference>
    </connector>
</assignments>
```

### Strategy 3: Retry Logic
Attempt failed step again before failing:

```xml
<decisions>
    <name>Check_Retry_Count</name>
    <rules>
        <name>Can_Retry</name>
        <conditions>
            <leftValueReference>varRetryCount</leftValueReference>
            <operator>LessThan</operator>
            <rightValue>
                <numberValue>3.0</numberValue>
            </rightValue>
        </conditions>
        <connector>
            <targetReference>Increment_Retry</targetReference>
        </connector>
    </rules>
    <defaultConnector>
        <targetReference>Report_Failure</targetReference>
    </defaultConnector>
</decisions>
```

## Related Patterns

- [Parent-Child Orchestration](orchestration-parent-child.md) - Coordinate parallel operations
- [Conditional Orchestration](orchestration-conditional.md) - Branch based on conditions
- [Subflow Library](../references/subflow-library.md) - Reusable building blocks

## Summary

**Sequential orchestration** creates clear, predictable workflows where each step builds on the previous one. While slower than parallel execution, the benefits of clear data flow, error isolation, and maintainability make it ideal for multi-stage processes with dependencies.

**Key Takeaway**: If your workflow is "Step A must complete before Step B can start," use sequential orchestration. Each stage becomes a tested, reusable component in your automation pipeline. 🔗
