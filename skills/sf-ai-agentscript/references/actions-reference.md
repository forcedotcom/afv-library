<!-- Parent: sf-ai-agentscript/SKILL.md -->
# Actions Reference

> Migrated from the former `sf-ai-agentforce-legacy/references/actions-reference.md` on 2026-02-07.
> For context-aware descriptions, instruction references, and input binding patterns, see [action-patterns.md](action-patterns.md).
> For prompt template actions (`generatePromptResponse://`), see [action-prompt-templates.md](action-prompt-templates.md).

Complete guide to Agent Actions in Agentforce: Flow, Apex, API actions,
escalation routing, and GenAiFunction metadata.

---

## Action Properties Reference

All actions in Agent Script support these properties:

### Action Definition Properties

| Property | Type | Required | Description | TDD |
|----------|------|----------|-------------|-----|
| `target` | String | Yes | Executable target (see Action Target Types below) | v1.3.0 |
| `description` | String | Yes | Explains behavior for LLM decision-making | v1.3.0 |
| `label` | String | No | Display name in UI (valid on action definitions, topics, and I/O fields) | v2.2.0 |
| `inputs` | Object | No | Input parameters and requirements | v1.3.0 |
| `outputs` | Object | No | Return parameters | v1.3.0 |
| `available_when` | Expression | No | Conditional availability for the LLM | v1.3.0 |
| `require_user_confirmation` | Boolean | No | Ask user to confirm before execution (compiles; runtime no-op per Issue 6) | v2.2.0 |
| `include_in_progress_indicator` | Boolean | No | Show progress indicator during execution | v2.2.0 |
| `progress_indicator_message` | String | No | Custom message shown during execution (e.g., "Processing your request...") | v2.2.0 |

> **Note**: `label`, `require_user_confirmation`, `include_in_progress_indicator`, and `progress_indicator_message` are valid on action definitions with `target:` but NOT on `@utils.transition` utility actions (see Val_Action_Properties vs Val_Action_Meta_Props).

### Input Properties

| Property | Type | Description | TDD |
|----------|------|-------------|-----|
| `description` | String | Explains the input parameter to LLM | v1.3.0 |
| `label` | String | Display name in UI | v2.2.0 |
| `is_required` | Boolean | Marks input as mandatory for the LLM | v2.2.0 |
| `is_user_input` | Boolean | LLM extracts value from conversation context | v2.2.0 |
| `complex_data_type_name` | String | Lightning data type mapping | v2.1.0 |

### Output Properties

| Property | Type | Description | TDD |
|----------|------|-------------|-----|
| `description` | String | Explains the output parameter | v1.3.0 |
| `label` | String | Display name in UI | v2.2.0 |
| `filter_from_agent` | Boolean | `True` = hide from user display (GA standard name) | v1.3.0 |
| `is_displayable` | Boolean | `False` = hide from user (compile-valid alias for `filter_from_agent`). Prefer this on prompt outputs when the planner still needs the value | v2.2.0 |
| `is_used_by_planner` | Boolean | `True` = LLM can reason about this value for routing decisions | v2.2.0 |
| `developer_name` | String | Overrides the parameter's developer name | — |
| `complex_data_type_name` | String | Lightning data type mapping | v2.1.0 |

> **`filter_from_agent` vs `is_displayable`**: Both control the same behavior. `filter_from_agent: True` is the GA standard name (used in official documentation). `is_displayable: False` is a compile-valid alias that achieves the same result.

> ⚠️ **Prompt-template exception**: On `prompt://` / `generatePromptResponse://` targets, prefer `is_displayable: False` + `is_used_by_planner: True` when the planner should synthesize the reply. `is_displayable: True` is a blank-response trap for prompt outputs.

> ⚠️ **`filter_from_agent` and `is_used_by_planner` are mutually exclusive**: Do NOT use both on the same output field. The combination causes `InvalidFormatError` which invalidates the entire action definition, triggering cascading `ACTION_NOT_IN_SCOPE` errors on every reference to that action. Use `filter_from_agent: True` alone to hide outputs from the customer. See [known-issues.md](known-issues.md#issue-40-filter-planner-conflict) Issue 40.

### Output Access Follows the Output Schema

Do not assume `@outputs.X` is always a scalar.

```agentscript
# Scalar output
set @variables.status = @outputs.status

# Structured/wrapper output
set @variables.raw_result = @outputs.output
set @variables.result_text = @outputs.output.value   # only if the schema exposes 'value'
```

**Guidance:**
- Direct assignment is safe for scalar outputs (`string`, `number`, `boolean`).
- If an action returns `object` or another structured type, inspect the output schema before comparing or assigning it.
- `.value` is a common wrapper field, but not a universal rule.
- When a deterministic branch depends on the result, flatten the Flow/Apex output so the agent receives an explicit scalar.

### Example with All Properties

```agentscript
actions:
   process_payment:
      description: "Processes payment for the order"
      require_user_confirmation: True    # Ask user before executing
      include_in_progress_indicator: True
      inputs:
         amount: number
            description: "Payment amount"
         card_token: string
            description: "Tokenized card number"
      outputs:
         transaction_id: string
            description: "Transaction reference"
         card_last_four: string
            description: "Last 4 digits of card"
            filter_from_agent: True     # Hide from direct customer display
      target: "flow://Process_Payment"
      available_when: @variables.cart_total > 0
```

---

## Action Target Types (Complete Reference)

AgentScript supports **22+ action target types**. Use the correct protocol for your integration:

| Short Name | Long Name | Description | Use Case |
|------------|-----------|-------------|----------|
| `flow` | `flow` | Salesforce Flow | Most common — Autolaunched Flows |
| `apex` | `apex` | Apex Class | Custom business logic |
| `prompt` | `generatePromptResponse` | Prompt Template | AI-generated responses |
| `standardInvocableAction` | `standardInvocableAction` | Built-in Salesforce actions | Send email, create task, etc. |
| `externalService` | `externalService` | External API via OpenAPI schema | External system calls |
| `quickAction` | `quickAction` | Object-specific quick actions | Log call, create related record |
| `api` | `api` | REST API calls | Direct API invocation |
| `apexRest` | `apexRest` | Custom REST endpoints | Custom @RestResource classes |
| `serviceCatalog` | `createCatalogItemRequest` | Service Catalog | Service catalog requests |
| `integrationProcedureAction` | `executeIntegrationProcedure` | OmniStudio Integration | Industry Cloud procedures |
| `expressionSet` | `runExpressionSet` | Expression calculations | Decision matrix, calculations |
| `cdpMlPrediction` | `cdpMlPrediction` | CDP ML predictions | Data Cloud predictions |
| `externalConnector` | `externalConnector` | External system connector | Pre-built connectors |
| `slack` | `slack` | Slack integration | Slack messaging |
| `namedQuery` | `namedQuery` | Predefined queries | Saved SOQL queries |
| `auraEnabled` | `auraEnabled` | Lightning component methods | @AuraEnabled Apex methods |
| `mcpTool` | `mcpTool` | Model Context Protocol | MCP tool integrations |
| `retriever` | `retriever` | Knowledge retrieval | RAG/knowledge base queries |

**Target Format**: `<type>://<DeveloperName>` (e.g., `flow://Get_Account_Info`, `standardInvocableAction://sendEmail`)

> 💡 `prompt://` is the official shorthand for `generatePromptResponse://`. Both forms resolve to the same target.

**Common Examples:**
```agentscript
# Flow action (most common)
target: "flow://Get_Customer_Orders"

# Apex action
target: "apex://CustomerServiceController"

# Prompt template
target: "generatePromptResponse://Email_Draft_Template"

# Standard invocable action (built-in Salesforce)
target: "standardInvocableAction://sendEmail"

# External service (API call)
target: "externalService://Stripe_Payment_API"
```

**Tip**: Before creating a custom Flow, check if a `standardInvocableAction://` already exists for your use case.

### Pre-Publish Target Validation

Before `sf agent publish`, verify action targets exist and are active:

| Target Protocol | Validation Query |
|-----------------|-----------------|
| `flow://X` | `SELECT ApiName FROM FlowDefinitionView WHERE ApiName = 'X' AND IsActive = true` |
| `apex://X` | `SELECT Name FROM ApexClass WHERE Name = 'X'` |
| `retriever://X` | `SELECT DeveloperName FROM DataCloudRetriever WHERE DeveloperName = 'X'` |
| `externalService://X` | `SELECT DeveloperName FROM ExternalServiceRegistration WHERE DeveloperName = 'X'` |
| `generatePromptResponse://X` | `SELECT DeveloperName FROM PromptTemplate WHERE DeveloperName = 'X' AND Status IN ('Active', 'Published')` |

Run these via: `sf data query -q "QUERY" -o ORG --json`

> **Prompt template note**: the queryable object name may still appear as `PromptTemplate`, while the current source metadata type is `GenAiPromptTemplate`.

### Direct Action Invocation (Debugging)

Test action targets outside the agent context via REST API:
- Flow: `POST /services/data/v66.0/actions/custom/flow/{FlowApiName}`
- Apex: `POST /services/data/v66.0/actions/custom/apex/{ClassName}`

Useful for isolating whether failures are in the action target or the agent framework.

---

## Action Invocation Methods

| Method | Syntax | Behavior | AiAuthoringBundle | GenAiPlannerBundle |
|--------|--------|----------|-------------------|-------------------|
| **Actions Block** | `actions:` in `reasoning:` | LLM chooses which to execute | ✅ Works | ✅ Works |
| **Deterministic** | `run @actions.name` | Always executes when code path is reached **if `name` resolves to a topic-level target-backed action definition** | ⚠️ Partial (see below) | ✅ Works |

### Deployment Method Capabilities

**`run` keyword IS supported in `reasoning.actions:` post-action blocks and `instructions: ->` blocks (Validated Jan 2026)**

```agentscript
# ✅ WORKS — run in reasoning.actions post-action block
create: @actions.create_order
   with customer_id = @variables.customer_id
   run @actions.send_confirmation     # ✅ Chains after create_order
   set @variables.order_id = @outputs.id

# ✅ WORKS — run in instructions: -> block
reasoning:
   instructions: ->
      run @actions.load_customer
         with id = @variables.customer_id
         set @variables.name = @outputs.name

# ❌ DOES NOT WORK — run in before_reasoning (no LLM context)
before_reasoning:
   run @actions.log_turn    # ❌ May not execute as expected
```

> **Note**: The Dec 2025 finding that `run` was "NOT supported" has been superseded. As of Jan 2026, `run` works in post-action chains and procedural instruction blocks **when it targets a topic-level action definition with `target:`**. It does NOT work reliably in `before_reasoning:`. Do **not** use `run` for utilities / delegations (`@utils.setVariables`, `@utils.transition`, `@topic.X`) even if they are written under an `actions:` block — those are not deterministic `run` targets.

**`{!@actions.name}` interpolation in instructions (Updated Feb 2026)**

The `{!@actions.action_name}` syntax embeds a reference to the full action definition into reasoning instructions. This gives the LLM richer context about available actions.

```agentscript
# ✅ WORKS — reference action in instructions for guided selection
reasoning:
   instructions: ->
      | To look up an order, use {!@actions.get_order}.
      | To check shipping status, use {!@actions.track_shipment}.
```

> **Note**: The Dec 2025 finding that this was broken has been superseded. See [action-patterns.md](action-patterns.md#2-instruction-action-references) for detailed usage patterns and examples.

### Correct Approach: Use `reasoning.actions` Block

The LLM automatically selects appropriate actions from those defined in the `reasoning.actions` block:

```agentscript
topic order_management:
   description: "Handles order inquiries"

   actions:
      get_order:
         description: "Retrieves order information"
         inputs:
            order_id: string
               description: "The order ID"
         outputs:
            status: string
               description: "Order status"
         target: "flow://Get_Order_Details"

   reasoning:
      instructions: ->
         | Help the customer with their order.
         | When they ask about an order, look it up.
      actions:
         # LLM automatically selects this when appropriate
         lookup: @actions.get_order
            with order_id=...
            set @variables.order_status = @outputs.status
```

---

## Action Type 1: Flow Actions

### When to Use

- Standard Salesforce data operations (CRUD)
- Business logic that can be expressed in Flow
- Screen flows for guided user experiences
- Approval processes

### Implementation

```yaml
actions:
  create_case:
    description: "Creates a new support case for the customer"
    inputs:
      subject:
        type: string
        description: "Case subject line"
      description:
        type: string
        description: "Detailed case description"
      priority:
        type: string
        description: "Case priority (Low, Medium, High, Urgent)"
    outputs:
      caseNumber:
        type: string
        description: "Created case number"
      caseId:
        type: string
        description: "Case record ID"
    target: "flow://Create_Support_Case"
```

### Flow Requirements

For an action to work with agents, the Flow must:

1. **Be Autolaunched** — `processType: AutoLaunchedFlow`
2. **Have Input Variables** — Marked as `isInput: true`
3. **Have Output Variables** — Marked as `isOutput: true`
4. **Be Active** — `status: Active`

**Flow Variable Example:**
```xml
<variables>
    <name>subject</name>
    <dataType>String</dataType>
    <isCollection>false</isCollection>
    <isInput>true</isInput>
    <isOutput>false</isOutput>
</variables>
```

### Best Practices

| Practice | Description |
|----------|-------------|
| Descriptive names | Use clear Flow API names that describe the action |
| Error handling | Include fault paths in your Flow |
| Bulkification | Design Flows to handle multiple records |
| Governor limits | Avoid SOQL/DML in loops |

---

## Action Type 2: Apex Actions

### When to Use

- Complex calculations or algorithms
- Custom integrations requiring Apex
- Operations not possible in Flow
- Bulk data processing
- When you need full control over execution

### Two Deployment Paths (CRITICAL DISTINCTION)

| Deployment Method | How Apex Actions Work | GenAiFunction Required? |
|-------------------|----------------------|------------------------|
| **AiAuthoringBundle** (.agent file) | `apex://ClassName` target in topic actions block | **NO** |
| **Agent Builder UI** (GenAiPlannerBundle) | GenAiFunction metadata wraps the Apex class | **YES** |

> ⚠️ **The official [agent-script-recipes](https://github.com/trailheadapps/agent-script-recipes) repo uses `apex://ClassName` directly with ZERO GenAiFunction metadata.** GenAiFunction is only needed when configuring agents through the Agent Builder UI or deploying via GenAiPlannerBundle.

### Path A: AiAuthoringBundle (Agent Script — RECOMMENDED)

#### Step 1: Create Apex Class with @InvocableMethod

```apex
public with sharing class CalculateDiscountAction {

    public class DiscountRequest {
        @InvocableVariable(label='Order Amount' required=true)
        public Decimal orderAmount;

        @InvocableVariable(label='Customer Tier' required=true)
        public String customerTier;
    }

    public class DiscountResult {
        @InvocableVariable(label='Discount Percentage')
        public Decimal discountPercentage;

        @InvocableVariable(label='Final Amount')
        public Decimal finalAmount;
    }

    @InvocableMethod(
        label='Calculate Discount'
        description='Calculates discount based on order amount and customer tier'
    )
    public static List<DiscountResult> calculateDiscount(List<DiscountRequest> requests) {
        List<DiscountResult> results = new List<DiscountResult>();
        for (DiscountRequest req : requests) {
            DiscountResult result = new DiscountResult();
            result.discountPercentage = getTierDiscount(req.customerTier);
            result.finalAmount = req.orderAmount * (1 - result.discountPercentage / 100);
            results.add(result);
        }
        return results;
    }

    private static Decimal getTierDiscount(String tier) {
        Map<String, Decimal> tierDiscounts = new Map<String, Decimal>{
            'Bronze' => 5, 'Silver' => 10, 'Gold' => 15, 'Platinum' => 20
        };
        return tierDiscounts.containsKey(tier) ? tierDiscounts.get(tier) : 0;
    }
}
```

#### Step 2: Reference DIRECTLY in Agent Script via `apex://`

```yaml
topic discount_calculator:
   description: "Calculates discount for customer order"

   # Level 1: Action DEFINITION with target
   actions:
      calculate_discount:
         description: "Calculates discount based on order amount and customer tier"
         inputs:
            orderAmount: number
               description: "The total order amount before discount"
            customerTier: string
               description: "Customer membership tier"
         outputs:
            discountPercentage: number
               description: "Applied discount percentage"
            finalAmount: number
               description: "Final order amount after discount"
         target: "apex://CalculateDiscountAction"   # Direct Apex — NO GenAiFunction needed!

   reasoning:
      instructions: |
         Help the customer calculate their discount.
      # Level 2: Action INVOCATION referencing the Level 1 definition
      actions:
         calc: @actions.calculate_discount
            with orderAmount=...
            with customerTier=@variables.tier
            set @variables.final_amount = @outputs.finalAmount
```

> ✅ **No GenAiFunction, no GenAiPlugin, no metadata deployment beyond the Apex class itself.** The `apex://ClassName` target auto-discovers the `@InvocableMethod` on the class.

#### I/O Name Matching Rules (TDD Validated v2.1.0)

Action `inputs:` and `outputs:` names in Agent Script must **exactly match** the `@InvocableVariable` field names in the Apex class:

| Agent Script I/O Name | Apex @InvocableVariable Field | Result |
|------------------------|-------------------------------|--------|
| `orderAmount` | `public Decimal orderAmount` | ✅ Publishes |
| `order_amount` | `public Decimal orderAmount` | ❌ `invalid input 'order_amount'` |
| `wrong_name` | `public String outputText` | ❌ `invalid output 'wrong_name'` |
| *(subset of outputs)* | *(declares fewer than all)* | ✅ Publishes (partial is valid) |

> **Partial Output Pattern**: You can declare a **subset** of the target's outputs in your action definition — you don't need to map every output parameter. This is useful when you only need one field from a multi-output action.

#### Bare @InvocableMethod Pattern (NOT Compatible)

> ⚠️ **TDD Finding (v2.1.0)**: Apex classes using bare `List<String>` parameters (no `@InvocableVariable` wrapper classes) are **incompatible** with Agent Script actions. The framework cannot discover bindable parameter names without `@InvocableVariable` annotations.

```apex
// ❌ INCOMPATIBLE with Agent Script — bare parameters, no wrappers
public class BareAction {
    @InvocableMethod(label='Bare Action')
    public static List<String> execute(List<String> inputs) {
        return inputs;
    }
}

// ✅ COMPATIBLE — wrapper classes with @InvocableVariable
public class WrappedAction {
    public class Request {
        @InvocableVariable(label='Input Text' required=true)
        public String inputText;  // ← This field name becomes the I/O name
    }
    public class Response {
        @InvocableVariable(label='Output Text')
        public String outputText;  // ← This field name becomes the I/O name
    }
    @InvocableMethod(label='Wrapped Action')
    public static List<Response> execute(List<Request> requests) { ... }
}
```

**Rule**: Always use `@InvocableVariable` wrapper classes when your Apex action will be called from Agent Script.

> ⚠️ **Namespace Warning (Unresolved)**: In namespaced packages, `apex://ClassName` may fail at publish time with "invocable action does not exist," even when the Apex class is confirmed deployed via SOQL. It is unclear whether namespace prefix syntax is required (e.g., `apex://ns__ClassName`). If you encounter this in a namespaced org, try: (1) `apex://ns__ClassName` format, (2) wrapping the Apex in a Flow and using `flow://` instead. See [known-issues.md](known-issues.md#issue-2-sf-agent-publish-fails-with-namespace-prefix-on-apex-targets) for tracking.

### Path B: Agent Builder UI (GenAiPlannerBundle — Legacy)

If you're NOT using Agent Script and are building agents through the Agent Builder UI, you need GenAiFunction metadata to wrap the Apex class. See the `assets/metadata/genai-function-apex.xml` template for the XML format.

> **Note**: GenAiFunction XML (API v66.0) only supports these elements: `masterLabel`, `description`, `invocationTarget`, `invocationTargetType`, `isConfirmationRequired`. Input/output schemas are defined via `input/schema.json` and `output/schema.json` bundle files, NOT inline XML elements.

---

## Action Type 3: API Actions (External System Integration)

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  API ACTION ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────┤
│  Agent Script                                                │
│       │                                                      │
│       ▼                                                      │
│  flow://HTTP_Callout_Flow                                    │
│       │                                                      │
│       ▼                                                      │
│  HTTP Callout Action (in Flow)                               │
│       │                                                      │
│       ▼                                                      │
│  Named Credential (Authentication)                           │
│       │                                                      │
│       ▼                                                      │
│  External API                                                │
└─────────────────────────────────────────────────────────────┘
```

### Implementation Steps

1. **Create Named Credential** (via sf-integration skill)
2. **Create HTTP Callout Flow** wrapping the external call
3. **Reference Flow in Agent Script** with `flow://` target

### Security Considerations

| Consideration | Implementation |
|---------------|----------------|
| Authentication | Always use Named Credentials (never hardcode secrets) |
| Permissions | Use Permission Sets to grant Named Principal access |
| Error handling | Implement fault paths in Flow |
| Logging | Log callout details for debugging |
| Timeouts | Set appropriate timeout values |

---

## Connection Block (Escalation Routing)

The `connection` block enables escalation to human agents via Omni-Channel. Use `connection messaging:` (singular). The plural `connections:` wrapper is invalid — see [known-issues.md](known-issues.md#issue-16).

### Basic Syntax

```agentscript
# Messaging channel (most common)
connection messaging:
   outbound_route_type: "OmniChannelFlow"
   outbound_route_name: "Support_Queue_Flow"
   escalation_message: "Transferring you to a human agent..."
   adaptive_response_allowed: True
```

### Multiple Channels

> ⚠️ The plural `connections:` wrapper block is **invalid** (see known-issues.md Issue 16). Use separate `connection <channel>:` blocks:

```agentscript
# Each channel gets its own top-level connection block
connection messaging:
   escalation_message: "Transferring to messaging agent..."
   outbound_route_type: "OmniChannelFlow"
   outbound_route_name: "flow://Agent_Support_Flow"
   adaptive_response_allowed: True
```

### Connection Block Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `outbound_route_type` | String | Yes | **`"OmniChannelFlow"` is the only TDD-validated value.** SKILL.md mentions `"Queue"` and `"Skill"` but the `connections:` block itself is not GA (see known-issues.md Issue 16). |
| `outbound_route_name` | String | Yes | API name of Omni-Channel Flow (must exist in org) |
| `escalation_message` | String | Yes | Message shown to user during transfer |
| `adaptive_response_allowed` | Boolean | No | Allow agent to adapt responses during escalation (default: False) |

### Supported Channels

| Channel | Description | Use Case |
|---------|-------------|----------|
| `messaging` | Chat/messaging channels | Enhanced Chat, Web Chat, In-App |
| `telephony` | Voice/phone channels | Service Cloud Voice, phone support |

**CRITICAL**: Values like `"queue"`, `"skill"`, `"agent"` for `outbound_route_type` cause validation errors!

### Escalation Action

```agentscript
# AiAuthoringBundle - basic escalation
actions:
   transfer_to_human: @utils.escalate
      description: "Transfer to human agent"

# GenAiPlannerBundle - with reason parameter
actions:
   transfer_to_human: @utils.escalate with reason="Customer requested"
```

### Prerequisites for Escalation

1. Omni-Channel configured in Salesforce
2. Omni-Channel Flow created and deployed
3. Connection block in agent script
4. Messaging channel active (Enhanced Chat, etc.)

---

## GenAiFunction Metadata Summary (Agent Builder UI / GenAiPlannerBundle ONLY)

> ⚠️ **NOT needed for AiAuthoringBundle (Agent Script)**. If you're writing `.agent` files, use `target: "apex://ClassName"` or `target: "flow://FlowName"` directly. See Action Type 2 above.

`GenAiFunction` wraps Apex, Flows, or Prompts as Agent Actions **for the Agent Builder UI path**.

```xml
<!-- Minimal valid GenAiFunction XML (API v66.0) -->
<GenAiFunction xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>What this action does</description>
    <invocationTarget>FlowOrApexName</invocationTarget>
    <invocationTargetType>flow|apex|prompt</invocationTargetType>
    <isConfirmationRequired>false</isConfirmationRequired>
    <masterLabel>Display Name</masterLabel>
</GenAiFunction>
```

**Input/Output Schemas**: Use `input/schema.json` and `output/schema.json` files in the GenAiFunction bundle directory. Do NOT use inline XML elements like `<genAiFunctionInputs>`, `<genAiFunctionOutputs>`, `<genAiFunctionParameters>`, or `<capability>` — these are NOT valid in the Metadata API XML schema (API v66.0).

### Prompt Builder Template Types

| Current metadata value | Typical use case |
|------|----------|
| `einstein_gpt__flex` | General purpose, maximum flexibility |
| `einstein_gpt__salesEmail` | Sales-oriented generated content |
| `einstein_gpt__fieldCompletion` | Suggest field values |
| `einstein_gpt__recordSummary` | Summarize record data |

### Template Variable Types

| Variable Type | Description |
|---------------|-------------|
| `freeText` | User-provided text input |
| `recordField` | Bound to specific record field |
| `relatedList` | Data from related records |
| `resource` | Static resource content |

---

## Cross-Skill Integration

### Orchestration Order for API Actions

When building agents with external API integrations, follow this order:

```
┌─────────────────────────────────────────────────────────────┐
│  INTEGRATION + AGENTFORCE ORCHESTRATION ORDER                │
├─────────────────────────────────────────────────────────────┤
│  1. sf-connected-apps  → Connected App (if OAuth needed)     │
│  2. sf-integration     → Named Credential + External Service │
│  3. sf-apex            → @InvocableMethod (if custom logic)  │
│  4. sf-flow            → Flow wrapper (HTTP Callout / Apex)  │
│  5. sf-deploy          → Deploy all metadata to org          │
│  6. sf-ai-agentscript  → Agent with flow:// target           │
│  7. sf-deploy          → Publish (sf agent publish            │
│                           authoring-bundle)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `Tool target 'X' is not an action definition` | Action not defined in topic `actions:` block, or target doesn't exist in org | Define action with `target:` in topic-level `actions:` block; ensure Apex class/Flow is deployed |
| `invalid input 'X'` or `invalid output 'X'` | I/O name doesn't match `@InvocableVariable` field name in Apex | Use exact field names from the Apex wrapper class (case-sensitive) |
| `Internal Error` with inputs-only action | Action has `inputs:` but no `outputs:` block | Add `outputs:` block — the server-side compiler requires it (see known-issues.md Issue 15) |
| `Internal Error` with bare @InvocableMethod | Apex uses `List<String>` without `@InvocableVariable` wrappers | Refactor Apex to use wrapper classes with `@InvocableVariable` annotations |
| `apex://` target not found | Apex class not deployed or missing `@InvocableMethod` | Deploy class first, ensure it has `@InvocableMethod` annotation |
| Flow action fails | Flow not active or not Autolaunched | Activate the Flow; ensure it's Autolaunched (not Screen) |
| API action timeout | External system slow | Increase timeout, add retry logic |
| Permission denied | Missing Named Principal access | Grant Permission Set |
| Action not appearing in Agent Builder UI | GenAiFunction not deployed (UI path only) | Deploy GenAiFunction metadata (only needed for Agent Builder UI, not Agent Script) |

### Debugging Tips

1. **Check deployment status:** `sf project deploy report`
2. **Verify GenAiFunction deployment:** `sf org list metadata -m GenAiFunction`
3. **Test Flow independently:** Use Flow debugger in Setup with sample inputs
4. **Check agent logs:** Agent Builder → Logs

---

## Related Documentation

- [action-patterns.md](action-patterns.md) — Context-aware descriptions, instruction references, binding strategies
- [action-prompt-templates.md](action-prompt-templates.md) — Prompt template invocation (`generatePromptResponse://`)
- [fsm-architecture.md](fsm-architecture.md) — FSM design and node patterns
