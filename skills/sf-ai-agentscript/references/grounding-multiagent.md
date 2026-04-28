<!-- Parent: sf-ai-agentscript/SKILL.md -->
# Data Grounding & Multi-Agent Guide

> High-stakes enterprise agents cannot rely on training data. They must be **grounded in real-time business data** and coordinate with **specialized agents** for complex tasks.

---

## Two Pillars

| Pillar | Icon | Description |
|--------|------|-------------|
| 🔽 **Retriever Actions** | Filter | Dynamic filtering ensures agents only see relevant data |
| 🔀 **Multi-Agent SOMA** | Branch | Primary agents delegate to expert agents |

---

## Context Placement Rules

- **Instructions**: behavior, tone, guardrails, tool-choice guidance.
- **Knowledge / retrieval**: facts, policy text, mutable rules, product specifics.
- **Filters**: what the agent can see or use; stronger than instructions for scope control.
- **Variables**: facts or state that must survive turn history or feed later actions.

### Retrieval Storage Heuristic

- Do not put long policy text in instructions.
- Retrieve facts just in time.
- Store retrieval output in variables only when it must persist across turns or feed deterministic follow-up.
- Prefer Flow-wrapped filtering over prose like “only use region X policy.”

## Retriever Actions

### Connecting Agents to Data Cloud

Retriever Actions connect your agent to Data Cloud Search Indexes, enabling context-aware knowledge retrieval.

**Capabilities:**
- ✅ Search Index wraps unstructured data (PDFs, docs, web pages)
- ✅ Chunking parses text, tables, and images into searchable segments
- ✅ Returns relevant chunks based on semantic similarity
- ✅ Integrated with Data Cloud for current data

### Basic Retriever Action

```yaml
actions:
  fetch_refund_policy:
    description: "Retrieve refund policy from knowledge base"
    target: "retriever://RefundSOP_Retriever"
    inputs:
      query: string
    outputs:
      chunks: list[object]
      relevance_scores: list[number]
```

### Retrieval Pipeline

```
┌────────────┐    ┌────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐
│ User Query │ → │ Dynamic Filter │ → │ Data Cloud Index│ → │ Relevant Chunks │ → │ LLM Response │
└────────────┘    └────────────────┘    └─────────────────┘    └─────────────────┘    └──────────────┘
```

---

### Filtered Retrieval with Flows

> Agent Script cannot filter retrieval results inline. When you need filtered knowledge retrieval, wrap the retriever in a Flow.

**Problem**: Direct `retriever://` targets don't support inline filtering.

**Solution**: Use `flow://` to wrap the retriever with filter logic.

```yaml
# WRONG - No filtering capability
actions:
  fetch_policy:
    target: "retriever://RefundSOP_Index"  # Can't filter!

# CORRECT - Flow handles filtering
actions:
  fetch_regional_policy:
    description: "Fetch policy filtered by customer region"
    inputs:
      query: string
      customer_country: string
        description: "Country code for regional filtering"
    outputs:
      chunks: list[object]
      policy_region: string
    target: "flow://GetRegionalRefundPolicy"  # Flow filters internally
```

> ⚠️ **Security Note**: Filtering in a Flow prevents accidental cross-region data exposure. The Flow enforces the filter - the LLM cannot bypass it.

---

### Safe Expressions

Agent Script uses a safe subset of Python for expressions:

**Allowed Operations:**
| Category | Operators |
|----------|-----------|
| **Comparison** | `==`, `!=` (not-equal), `>`, `<`, `>=`, `<=` |
| **Logical** | `and`, `or`, `not` |
| **String** | `contains`, `startswith`, `endswith` |

> ⚠️ **Guardrail note**: These string operators may compile, but they are not the most reliable way to enforce control-flow-critical validation or intent routing. For anything that must deterministically gate behavior — such as URL validation, cancellation detection, or revision handling — prefer a Flow/Apex/classifier action that returns an explicit boolean or enum.

**Security Constraints:**
- ❌ No `import` statements
- ❌ No file access
- ❌ No arbitrary code execution

```python
# Valid safe expressions:
@variables.risk_score > 80
@variables.country == "Germany"
@variables.is_vip and @variables.order_total > 100
not @variables.verified

# INVALID (security risk):
import os     # NOT ALLOWED
eval(...)     # NOT ALLOWED
open(...)     # NOT ALLOWED
```

---

## The 6 Action Target Protocols

Every action uses a `target:` field to specify where to send the request.

| Protocol | Use When | Example |
|----------|----------|---------|
| `flow://` | Data operations, business logic | `target: "flow://GetOrderStatus"` |
| `apex://` | Custom calculations, validation | `target: "apex://RefundCalculator"` |
| `generatePromptResponse://` | Grounded LLM responses | `target: "generatePromptResponse://Summary"` |
| `retriever://` | RAG knowledge search | `target: "retriever://Policy_Index"` |
| `externalService://` | Third-party APIs | `target: "externalService://AddressAPI"` |
| `standardInvocableAction://` | Built-in SF actions | `target: "standardInvocableAction://email"` |

---

### Protocol 1: Salesforce Flow (`flow://`)

**Use Case**: Data operations, business logic, filtered retrieval

```yaml
actions:
  get_order_status:
    description: "Retrieves order details by order number"
    inputs:
      order_number: string
        description: "The order ID to look up"
    outputs:
      status: string
      tracking_number: string
    target: "flow://GetOrderStatus"
```

---

### Protocol 2: Apex Class (`apex://`)

**Use Case**: Custom calculations, complex validation

```yaml
actions:
  calculate_refund:
    description: "Calculate refund amount based on policy rules"
    inputs:
      order_id: string
      refund_reason: string
    outputs:
      refund_amount: currency
      requires_approval: boolean
    target: "apex://RefundCalculatorService"
```

---

### Protocol 3: Prompt Template (`generatePromptResponse://`)

**Use Case**: Grounded LLM responses, summarization

```yaml
actions:
  summarize_case:
    description: "Generate a summary of the customer case"
    inputs:
      "Input:caseId": id
        description: "The Case record ID"
    outputs:
      promptResponse: string
    target: "generatePromptResponse://Generate_Case_Summary"
```

> ⚠️ Note: Input keys use quoted strings with colon notation (`"Input:caseId"`)

---

### Protocol 4: Data Cloud Retriever (`retriever://`)

**Use Case**: Knowledge base search, FAQ lookup

```yaml
actions:
  search_knowledge:
    description: "Search the knowledge base for relevant info"
    inputs:
      query: string
    outputs:
      chunks: list[object]
      relevance_scores: list[number]
    target: "retriever://RefundPolicy_Retriever"
```

---

### Protocol 5: External Service (`externalService://`)

**Use Case**: Third-party APIs via Named Credentials

```yaml
actions:
  verify_address:
    description: "Validate shipping address via external API"
    inputs:
      street: string
      city: string
      postal_code: string
    outputs:
      is_valid: boolean
      normalized_address: object
    target: "externalService://AddressValidation"
```

---

### Protocol 6: Standard Invocable (`standardInvocableAction://`)

**Use Case**: Built-in Salesforce actions (email, tasks, Chatter)

```yaml
actions:
  send_email:
    description: "Send confirmation email to customer"
    inputs:
      recipient_email: string
      template_id: id
    outputs:
      success: boolean
    target: "standardInvocableAction://emailSimple"
```

---

### Protocol Selection Guide

| If you need... | Use this protocol |
|----------------|-------------------|
| Complex data queries, record updates | `flow://` |
| Custom calculations, validation | `apex://` |
| LLM-generated summaries | `generatePromptResponse://` |
| Knowledge search, RAG | `retriever://` |
| External REST APIs | `externalService://` |
| Standard SF actions | `standardInvocableAction://` |

### Conditional Knowledge Retrieval Pattern

Use `available when` to route to different knowledge bases based on user context:

```yaml
topic knowledge_router:
   description: "Route to appropriate knowledge base"
   reasoning:
      instructions: ->
         | Let me find the right information for you.
      actions:
         search_premium_kb: @actions.search_premium_knowledge
            description: "Search premium support articles"
            available when @variables.customer_tier == "premium"
            with query = ...
         search_standard_kb: @actions.search_standard_knowledge
            description: "Search standard support articles"
            available when @variables.customer_tier != "premium"
            with query = ...
```

> **Why this matters**: Different customer tiers may need access to different knowledge bases with different SLA guidance, pricing, or support procedures. The `available when` guard ensures the LLM can only search the appropriate knowledge base.

---

## Same Org Multi-Agent (SOMA)

When a primary agent encounters specialized needs, it can coordinate with expert agents.

### Two Coordination Patterns

| Pattern | Description | Return Behavior |
|---------|-------------|-----------------|
| 🔀 **Delegation** | Farm out, then return | ✅ Control returns to original agent |
| ➡️ **Handoff** | Transfer permanently | ❌ No return - original agent exits |

---

### Pattern 1: Delegation

**Flow:**
```
┌─────────┐    DELEGATE    ┌────────────┐    RETURN    ┌─────────┐
│ Primary │ ─────────────▶ │ Specialist │ ───────────▶ │ Primary │
└─────────┘                └────────────┘              └─────────┘
```

**Use Cases:**
- Tax questions → Compliance Agent
- Technical issues → Support Specialist
- Order changes → Fulfillment Agent

**Implementation:**
```yaml
# Delegation uses topic reference (NOT @utils.transition)
# Parent orchestrates — child returns control
reasoning:
  actions:
    ask_compliance: @topic.compliance
      description: "Consult compliance specialist on tax questions"
      # ✅ Returns to this topic after specialist finishes

    ask_refund_help: @topic.refund_specialist
      description: "Consult refund specialist for calculations"
      # ✅ Control returns to continue conversation
```

---

### Pattern 2: Handoff

**Flow:**
```
┌─────────┐    HANDOFF    ┌────────┐    NO RETURN
│ Primary │ ────────────▶ │ Target │ ────────────▶ ✗
└─────────┘               └────────┘
```

**Use Cases:**
- Escalation to human agent
- Domain boundary (Sales → Support)
- Fraud detection requiring specialized handling

**Implementation:**
```yaml
# Permanent handoff - conversation leaves this agent
reasoning:
  actions:
    escalate_to_human: @utils.escalate
      description: "Transfer to live support"
      # Conversation ends for this agent
```

---

### Delegation vs Handoff Decision

| Use This | When You Need |
|----------|---------------|
| `@topic.X` (in reasoning.actions) | Temporary delegation — control returns |
| `@utils.transition to @topic.X` | Permanent handoff — no return |
| `@utils.escalate` | Permanent handoff to human |
| `@agent.X` (Connections) | Permanent handoff to another agent |

> **KEY INSIGHT**: The difference is whether the original agent continues after the specialist finishes.

### SOMA Limitations (Community-Confirmed)

| Limitation | Description | Workaround |
|-----------|-------------|------------|
| Single action per supervision call | Delegated topic can only execute ONE action before returning | Break complex operations into separate delegation calls |
| `related_agent` nodes may fail | SOMA configuration with related agent references can cause "Node does not have corresponding topic" errors | Use `@topic.X` delegation within same agent instead |
| No cross-agent variable sharing | Delegated agents cannot read/write parent agent's variables | Pass data through action inputs/outputs |

---

## Variable Configuration for Grounding

### Linked Variables for Session Context

```yaml
variables:
  # WRONG - mutable allows modification
  CustomerCountry: mutable string = ""

  # CORRECT - linked preserves session data
  CustomerCountry: linked string
    source: @session.Country
```

**Why This Matters:**
- `mutable string = ""` starts empty - filter won't work
- `linked string` pulls from session - filter gets real value

---

### Debug Exercise: Wrong Policy Applied

**Symptom**: German customer received US refund policy

**Root Cause Trace:**

| Step | Wrong Implementation | Correct Implementation |
|------|---------------------|------------------------|
| 1. Session Start | `CustomerCountry: ""` | `CustomerCountry: "Germany"` |
| 2. Filter | `Region == ""` | `Region == "Germany"` |
| 3. Knowledge Fetch | US_Refund_Policy | EU_Refund_Policy_GDPR |
| 4. Refund | $10 credit | Full refund (€45.99) |

**Fix**: Change `mutable string = ""` to `linked string` with `source: @session.Country`

---

## Best Practices

### 1. Always Filter Regional Data
Never return unfiltered results for region-specific policies.

### 2. Use Flows for Complex Filtering
Agent Script can't filter inline - wrap retrievers in Flows.

### 3. Validate Session Variables
Ensure linked variables have sources - empty values cause wrong retrievals.

### 4. Choose Delegation vs Handoff Carefully
- `@topic.X` (delegation) — returns control to parent topic
- `@utils.transition to @topic.X` (handoff) — permanent, no return

### 5. Use `available when` for Sensitive Protocols
Guard external service calls with verification checks.

```yaml
actions:
  call_payment_api: @actions.charge_card
    target: "externalService://PaymentGateway"
    available when @variables.customer_verified == True
```
