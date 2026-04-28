<!-- Parent: sf-ai-agentscript/SKILL.md -->
# Agent Script Patterns Quick Reference

> Decision trees and cheat sheets for common Agent Script patterns

---

## Tool Selection Preflight

```
What kind of problem is this?
│
├─► Single-turn generation only?
│   └─► PROMPT TEMPLATE / prompt action
│
├─► Fully static deterministic sequence?
│   └─► FLOW / APEX
│
├─► Dynamic user input + branching + must-pass gates?
│   └─► AGENT SCRIPT
│
└─► Mostly flexible conversation with a few hard controls?
    └─► AGENT SCRIPT + deterministic envelope
```

---

## Pattern Selection Decision Tree

### Which Architecture Pattern?

```
What's your agent's purpose?
│
├─► Multi-purpose (sales, support, orders)?
│   └─► HUB AND SPOKE
│       Central router → Specialized topics
│
├─► Sequential workflow (onboarding, checkout)?
│   └─► LINEAR FLOW
│       A → B → C pipeline
│
├─► Tiered support with escalation?
│   └─► ESCALATION CHAIN
│       L1 → L2 → L3 → Human
│
├─► Sensitive operations (payments, PII)?
│   └─► VERIFICATION GATE
│       Security check → Protected topics
│
└─► Multiple protected topics behind shared auth gate?
    └─► STATE GATE (OPEN GATE)
        3-variable bypass with deferred routing
```

---

## Routing Quick Rules

- Use `description:` for routing and `label:` for display.
- If one utterance fits two sibling topics, redesign.
- Keep escalation and handoff topics limited to meta-intents.
- Assume every new turn can trigger re-matching.

### Quick Overlap Check

Ask:
- Would the same utterance reasonably match both topics?
- Are you relying on instructions, not the topic description, to separate them?
- Does one topic use broad umbrella terms like `help`, `support`, `account`, or `billing` that absorb adjacent intents?

---

## Node Type Decision Tree

```
What should this topic do?
│
├─► Route based on intent?
│   └─► 🔵 ROUTING (Topic Selector)
│
├─► Security/identity check?
│   └─► 🔵 VERIFICATION
│
├─► Fetch external data?
│   └─► 🟡 DATA-LOOKUP
│
├─► Apply business rules?
│   └─► 🟢 PROCESSING
│
└─► Transfer to human?
    └─► 🔴 HANDOFF
```

---

## Variable Type Decision Tree

```
What kind of data is this?
│
├─► State that changes during conversation?
│   │   (counters, flags, accumulated data)
│   └─► MUTABLE
│       `failed_attempts: mutable number = 0`
│
└─► Data from external source?
    │   (session, context, CRM)
    └─► LINKED
        `customer_id: linked string`
        `   source: @session.customerId`
```

---

## Action Target Protocol Decision Tree

```
Where should this action go?
│
├─► Data queries, record updates?
│   └─► flow://
│
├─► Custom calculations, validation?
│   └─► apex://
│
├─► LLM-generated summaries?
│   └─► generatePromptResponse://
│
├─► Knowledge search, RAG?
│   └─► retriever://
│
├─► External REST APIs?
│   └─► externalService://
│
└─► Built-in SF actions (email, tasks)?
    └─► standardInvocableAction://
```

---

## Deterministic vs Subjective Decision Tree

```
Should this be code-enforced or LLM-flexible?
│
├─► Security/safety requirement?
│   └─► DETERMINISTIC (code)
│
├─► Financial threshold?
│   └─► DETERMINISTIC (code)
│
├─► Counter/state management?
│   └─► DETERMINISTIC (code)
│
├─► Conversational/greeting?
│   └─► SUBJECTIVE (LLM)
│
├─► Context understanding needed?
│   └─► SUBJECTIVE (LLM)
│
└─► Natural language generation?
    └─► SUBJECTIVE (LLM)
```

---

## Control Placement Cheat Sheet

| Need | Best home |
|---|---|
| Tone, behavior, conversational guidance | Instructions |
| Facts, policy text, mutable rules | Retrieval / knowledge |
| Visibility, scope, access control | Filters, `available when`, guarded transitions |
| Mandatory order, must-run logic | Agent Script transitions, `run`, or Flow / Apex |
| Long-lived context across turns | Variables |

---

## SOMA Pattern Decision Tree

```
Does the conversation return to original agent?
│
├─► Yes, specialist handles sub-task
│   └─► DELEGATION
│       `@topic.specialist` (in reasoning.actions)
│
└─► No, permanent transfer
    ├─► To another topic?
    │   └─► HANDOFF  `@utils.transition to @topic.X`
    │
    ├─► To human?
    │   └─► `@utils.escalate`
    │
    └─► To another agent?
        └─► `@agent.X` (Connections)
```

---

## Transition Type Cheat Sheet

| Syntax | Type | Control |
|--------|------|---------|
| `@utils.transition to @topic.X` | LLM-chosen | LLM decides when to use |
| `transition to @topic.X` | Deterministic | Always executes when reached |
| `@utils.escalate` | Permanent handoff | Human takeover |

---

## Instruction Resolution Order

```
instructions: ->
   # 1. POST-ACTION CHECKS (at TOP - triggers on loop)
   if @variables.action_completed == True:
      run @actions.follow_up_action
      transition to @topic.next_step

   # 2. PRE-LLM DATA LOADING
   run @actions.load_required_data
      set @variables.data = @outputs.result

   # 3. DYNAMIC INSTRUCTIONS FOR LLM
   | Here is the context: {!@variables.data}

   if @variables.condition:
      | Do this thing.
   else:
      | Do that thing.
```

**Why this order?**
1. Post-action at TOP → triggers immediately on loop
2. Data loading next → LLM needs current data
3. Instructions last → LLM sees resolved values

---

## Common Patterns Quick Reference

### Security Gate (Early Exit)

```yaml
instructions: ->
   if @variables.failed_attempts >= 3:
      | Account locked due to too many attempts.
      transition to @topic.lockout  # LLM never reasons
```

### Guarded Actions

```yaml
actions:
   process_refund: @actions.process_refund
      description: "Issue refund"
      available when @variables.customer_verified == True
```

### Post-Action Follow-Up

```yaml
instructions: ->
   if @variables.refund_status == "Approved":
      run @actions.create_crm_case
         with customer_id = @variables.customer_id
      transition to @topic.success
```

### Data-Dependent Instructions

```yaml
instructions: ->
   run @actions.get_account_tier
      set @variables.tier = @outputs.tier

   if @variables.tier == "Gold":
      | VIP treatment - offer 20% discount.
   else:
      | Standard customer service.
```

### Open Gate (State Gate)

3-variable state machine that bypasses the LLM topic selector when a gate holds focus and routes users through an auth gate before accessing protected topics.

```yaml
# In topic_selector's before_reasoning — zero-credit bypass:
before_reasoning:
   if @variables.open_gate == "protected_workflow":
      transition to @topic.protected_workflow
   if @variables.open_gate == "authentication_gate":
      transition to @topic.authentication_gate

# In protected topic's before_reasoning — auth redirect:
before_reasoning:
   if @variables.authenticated == False:
      set @variables.next_topic = "protected_workflow"
      set @variables.open_gate = "authentication_gate"
      transition to @topic.authentication_gate
   set @variables.open_gate = "protected_workflow"

# EXIT_PROTOCOL — release gate when user changes intent:
before_reasoning:
   set @variables.open_gate = "null"
   set @variables.next_topic = ""
   transition to @topic.topic_selector
```

> **Template**: [assets/patterns/open-gate-routing.agent](../assets/patterns/open-gate-routing.agent)

---

## Anti-Patterns to Avoid

### ❌ Data Load After LLM Text

```yaml
# WRONG - LLM sees empty values
instructions: ->
   | Customer name: {!@variables.name}  # empty!
   run @actions.load_customer
      set @variables.name = @outputs.name
```

### ❌ Post-Action Check at Bottom

```yaml
# WRONG - Never triggers
instructions: ->
   | Help with refund.
   transition to @topic.main  # Exits first!

   if @variables.refund_done:  # Never reached
      run @actions.log_refund
```

### ❌ Mixing Tabs and Spaces

```yaml
# WRONG - Compilation error
config:
   developer_name: "MyAgent"  # 3 spaces
        agent_label: "Label"  # 8 spaces - FAILS!
```

### ❌ Lowercase Booleans

```yaml
# WRONG - Agent Script uses Python-style
is_verified: mutable boolean = true   # WRONG
is_verified: mutable boolean = True   # CORRECT
```

---

## Syntax Quick Reference

| Pattern | Purpose |
|---------|---------|
| `instructions: ->` | Arrow syntax, enables expressions |
| `instructions: \|` | Pipe syntax, simple multi-line |
| `if @variables.x:` | Conditional (pre-LLM) |
| `run @actions.x` | Execute during resolution |
| `set @var = @outputs.y` | Capture action output |
| Curly-bang: {!@variables.x} | Template injection |
| `available when` | Control action visibility |
| `transition to @topic.x` | Deterministic topic change |
| `@utils.transition to` | LLM-chosen topic change |
| `@utils.escalate` | Human handoff |

---

## The 6 Deterministic Building Blocks

| # | Block | Example |
|---|-------|---------|
| 1 | Conditionals | `if @variables.failed_attempts >= 3:` |
| 2 | Topic Filters | `available when @variables.cart_items > 0` |
| 3 | Variable Checks | `if @variables.churn_risk >= 80:` |
| 4 | Inline Actions | `run @actions.load_customer` |
| 5 | Utility Actions | `@utils.transition`, `@utils.escalate` |
| 6 | Variable Injection | Curly-bang: {!@variables.customer_name} |

---

## Implementation Best Practices

> Migrated from the former `sf-ai-agentforce-legacy/references/patterns-and-practices.md` on 2026-02-07.

### Pattern Details

#### Lifecycle Events Pattern

**File**: `assets/patterns/lifecycle-events.agent`

Execute code automatically before and after every reasoning step.

> **⚠️ Deployment Note**: The `run` keyword works in `reasoning.actions:` post-action blocks and `instructions: ->` blocks. It does NOT work reliably in `before_reasoning:` / `after_reasoning:` lifecycle blocks.

```agentscript
topic conversation:
   before_reasoning:
      set @variables.turn_count = @variables.turn_count + 1
      run @actions.refresh_context                    # ⚠️ GenAiPlannerBundle only
         with user_id=@variables.EndUserId
         set @variables.context = @outputs.fresh_context

   reasoning:
      instructions: ->
         | Turn {!@variables.turn_count}: {!@variables.context}

   after_reasoning:
      run @actions.log_analytics                      # ⚠️ GenAiPlannerBundle only
         with turn=@variables.turn_count
```

| ✅ Good Use Case | ❌ Not Ideal For |
|------------------|------------------|
| Track conversation metrics | One-time setup (use conditional) |
| Refresh context every turn | Heavy processing (adds latency) |
| Log analytics after each response | Actions that might fail often |

#### Action Callbacks Pattern

**File**: `assets/patterns/action-callbacks.agent`

Chain deterministic follow-up actions using the `run` keyword.

> **⚠️ Deployment Note**: The `run` keyword works in `reasoning.actions:` post-action blocks and `instructions: ->` blocks. It does NOT work reliably in `before_reasoning:` / `after_reasoning:` lifecycle blocks.

```agentscript
process_order: @actions.create_order
   with customer_id=@variables.customer_id
   set @variables.order_id = @outputs.order_id
   run @actions.send_confirmation                    # ⚠️ GenAiPlannerBundle only
      with order_id=@variables.order_id
   run @actions.log_activity                         # ⚠️ GenAiPlannerBundle only
      with event="ORDER_CREATED"
```

| ✅ Good Use Case | ❌ Not Ideal For |
|------------------|------------------|
| Audit logging (must happen) | Optional follow-ups (let LLM decide) |
| Send notification after action | Complex branching logic |
| Chain dependent actions | More than 1 level of nesting |

**Critical Rule**: Only 1 level of `run` nesting allowed!

#### Combining Patterns

Patterns can be combined for complex scenarios:

```
┌─────────────────────────────────────────────────────────────┐
│           LIFECYCLE + CALLBACKS + ROUTING                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  topic order_hub:                                            │
│     before_reasoning:                        ◄── Lifecycle   │
│        set @variables.turn_count = ... + 1                   │
│                                                              │
│     reasoning:                                               │
│        actions:                                              │
│           process: @actions.create                           │
│              run @actions.notify           ◄── Callback      │
│              run @actions.log                                │
│                                                              │
│           consult: @utils.transition       ◄── Routing       │
│              to @topic.specialist                            │
│                                                              │
│     after_reasoning:                         ◄── Lifecycle   │
│        run @actions.update_metrics                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

### N-ary Boolean Expressions

AgentScript supports **3 or more conditions** chained with `and`/`or`:

```agentscript
# Three+ conditions with AND
before_reasoning:
   if @variables.is_authenticated and @variables.has_permission and @variables.is_active:
      transition to @topic.authorized

# Three+ conditions with OR
before_reasoning:
   if @variables.is_admin or @variables.is_moderator or @variables.is_owner:
      transition to @topic.elevated_access

# In available when clauses
reasoning:
   actions:
      process_return: @actions.handle_return
         description: "Process customer return request"
         available when @variables.eligible == True and @variables.order_id != None and @variables.tier != "basic"

      premium_action: @actions.premium_feature
         description: "Premium tier feature"
         available when @variables.tier == "premium" or @variables.tier == "enterprise" or @variables.is_trial_premium == True
```

**Key Points:**
- Chain as many conditions as needed with `and` or `or`
- Use `()` grouping for complex expressions: `(a and b) or (c and d)`
- Works in `if` statements and `available when` clauses

---

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Agent name | PascalCase with underscores | `Customer_Service_Agent` |
| Topic name | snake_case | `order_management` |
| Variable name | snake_case | `user_email` |
| Action name | snake_case | `get_account_details` |
| Transition action name | `go_to_` prefix | `go_to_checkout`, `go_to_support` |

> 💡 Official GA docs recommend naming transition actions with a `go_to_` prefix for clarity (e.g., `go_to_checkout: @utils.transition to @topic.checkout`).

---

### Variable Management Best Practices

#### Initialize with Defaults

```agentscript
variables:
    # ✅ RECOMMENDED - Has default value (clearer intent)
    user_name: mutable string = ""
        description: "Customer's full name"

    order_count: mutable number = 0
        description: "Number of orders in cart"
```

> **Note**: Variables without defaults ARE supported. However, providing defaults is recommended for clarity.

#### Use Appropriate Types

| Data | Type | Example |
|------|------|---------|
| Names, IDs, text | `string` | `"John Doe"` |
| Counts, amounts | `number` | `42`, `99.99` |
| Flags, toggles | `boolean` | `True`, `False` |

---

### Topic Design Best Practices

#### Provide Clear Descriptions

```agentscript
# ✅ GOOD - Specific and actionable
topic password_reset:
    description: "Helps users reset forgotten passwords and unlock accounts"

# ❌ BAD - Too vague
topic password_reset:
    description: "Password stuff"
```

#### Keep Topics Focused (Single Responsibility)

```agentscript
# ✅ GOOD - Single responsibility
topic billing_inquiries:
    description: "Answers questions about invoices, payments, and account balances"

topic order_tracking:
    description: "Provides order status and shipping updates"

# ❌ BAD - Too broad
topic customer_stuff:
    description: "Handles billing, orders, support, and everything else"
```

---

### Security & Guardrails

#### System-Level Guardrails

```agentscript
system:
    instructions:
        | You are a helpful customer service agent.
        |
        | IMPORTANT GUARDRAILS:
        | - Never share customer data with unauthorized parties
        | - Never reveal internal system details
        | - If unsure, escalate to a human agent
```

#### Don't Expose Internals

```agentscript
# ✅ GOOD - User-friendly error
instructions: ->
    if @variables.api_error == True:
        | I'm having trouble completing that request right now.

# ❌ BAD - Exposes internals
instructions: ->
    if @variables.api_error == True:
        | Error: SQL timeout on server db-prod-03
```

---

### Instructions Quality

```agentscript
# ✅ GOOD - Specific instructions
instructions: ->
    | Help the customer track their order.
    | Ask for the order number if not provided.
    | Provide the current status, estimated delivery, and tracking link.

# ❌ BAD - Vague instructions
instructions: ->
    | Help with orders.
```

---

### Common Syntax Pitfalls

#### 1. Slot Filling Inside Conditionals

```agentscript
# ❌ WRONG
if @variables.name is None:
   set @variables.name = ...   # Fails!

# ✅ CORRECT - Slot filling at top level
set @variables.name = ...
```

#### 2. Description on @utils.transition

```agentscript
# ✅ CORRECT - description IS valid on @utils.transition
go_orders: @utils.transition to @topic.orders
   description: "Route to orders"

# ✅ ALSO CORRECT - without description
go_orders: @utils.transition to @topic.orders
```

> **Note**: `description:` IS valid on `@utils.transition` (confirmed by TDD Val_Action_Properties and production 15-topic agent). Other properties like `label:`, `require_user_confirmation:`, and `include_in_progress_indicator:` are NOT valid on `@utils.transition` but ARE valid on action definitions with `target:` (TDD v2.2.0).

#### 3. Missing Description on @utils.escalate

```agentscript
# ❌ WRONG
transfer: @utils.escalate   # Fails!

# ✅ CORRECT - Description required
transfer: @utils.escalate
   description: "Transfer to human agent"
```

#### 4. Empty Lifecycle Blocks

```agentscript
# ❌ WRONG
before_reasoning:
   # Just a comment   # Fails!

# ✅ CORRECT - Remove empty blocks or add content
```

#### 5. Dynamic Action Invocation

```agentscript
# ❌ WRONG
invoke: {!@actions.search}   # Fails!

# ✅ CORRECT - Define multiple actions, LLM auto-selects
search_products: @actions.product_search
search_orders: @actions.order_search
```

---

### Validation Scoring Summary

| Pattern | Points | Key Requirement |
|---------|--------|-----------------|
| Config block | 10 | All 4 required fields |
| Linked variables | 10 | EndUserId, RoutableId, ContactId |
| Topic structure | 10 | label, description, reasoning |
| Language block | 5 | default_locale present |
| Lifecycle blocks | 5 | Proper before/after structure |
| Action callbacks | 5 | No nested run |
| Error handling | 5 | Validation patterns |
| Template expressions | 5 | {!@variables.x} syntax |

---

### Slot Filling Reliability Patterns

#### Problem: LLM Fails to Extract Values Correctly

| Symptom | What Happened | Example |
|---------|---------------|---------|
| Empty JSON `{}` sent to action | LLM couldn't find value in conversation | User said "look up my account" without ID |
| Wrong field names | LLM abbreviated or guessed | `_id` instead of `account_id` |
| Wrong value extracted | LLM picked similar value from context | Picked Contact ID instead of Account ID |
| Retry/crash cycles | No recovery path after failure | Agent keeps trying same extraction |

**Root Cause:** The `...` syntax is **probabilistic** — the LLM infers what value to use. For critical inputs (IDs, amounts, required fields), this unreliability causes downstream failures.

#### 5-Pattern Solution for Critical Inputs

**Pattern 1: First-Interaction Collection** — Tell the LLM its PRIMARY GOAL:

```agentscript
reasoning:
   instructions: ->
      | YOUR PRIMARY GOAL: Collect the account ID from the user.
      | Do NOT proceed with any other actions until account_id is captured.
      |
      if @variables.account_id == "":
         | ⚠️ Account ID not yet collected. ASK the user for it.
```

**Pattern 2: Variable Setter Action** — Dedicated action to capture and validate:

```agentscript
actions:
   capture_account_id:
      description: "Captures and validates the Salesforce Account ID from user"
      inputs:
         account_id: string
            description: "The 18-character Salesforce Account ID (starts with 001)"
            is_required: True
      outputs:
         validated_id: string
            description: "The validated account ID (empty if invalid)"
         is_valid: boolean
            description: "Whether the ID is valid"
      target: "flow://Validate_Account_Id"
```

**Pattern 3: Single-Use Guard** — Make setter unavailable after capture:

```agentscript
reasoning:
   actions:
      validate_id: @actions.capture_account_id
         with account_id=...
         set @variables.account_id = @outputs.validated_id
         set @variables.account_id_validated = @outputs.is_valid
         available when @variables.account_id == ""
```

**Pattern 4: Null Guard Downstream Actions** — Block until validated:

```agentscript
reasoning:
   actions:
      do_research: @actions.research_account
         with account_id=@variables.account_id
         available when @variables.account_id_validated == True
```

**Pattern 5: Explicit Action References** — Guide the LLM:

```agentscript
instructions: ->
   | To capture the account ID, use {!@actions.capture_account_id}.
   | This ensures the ID is validated before proceeding.
```

#### When NOT to Use Slot Filling

| Use Slot Filling (`...`) | Use Variable/Fixed Value |
|--------------------------|--------------------------|
| Optional, non-critical inputs | Critical IDs (account, order, case) |
| User preference inputs | Values that must be validated |
| One-time collection | Values used across multiple actions |
| Simple text descriptions | Values with specific formats (dates, IDs) |

**Decision Rule:** If invalid input would cause downstream failure, use deterministic collection.

> ⚠️ **Chained action restriction**: Slot filling (`...`) works for top-level action inputs but NOT for chained action inputs (via `run`). Chained actions run deterministically and cannot use LLM slot-filling.

---

### Pre-Deploy Checklist

Before deploying an agent, verify:

- [ ] All topics have clear descriptions
- [ ] All variables have descriptions and defaults
- [ ] All actions have input/output descriptions
- [ ] System guardrails are defined
- [ ] Error handling is in place for critical operations
- [ ] Navigation back to main menu from all topics
- [ ] Template expressions use correct syntax `{!@variables.name}`
- [ ] Consistent indentation (tabs recommended)

---

<a id="discovery-questions-pre-authoring"></a>

## Discovery Questions (Pre-Authoring)

> Ask these questions before writing any Agent Script to clarify requirements and avoid rework. Sourced from [AGENT_SCRIPT.md](https://github.com/trailheadapps/agent-script-recipes).

### Agent Identity
- What is the agent's primary purpose?
- Who are the end users (customers, employees, partners)?
- What tone and persona should the agent adopt?
- What languages must be supported?

### Topics
- What are the main conversation topics?
- Which topics require security gates (authentication, authorization)?
- What is the expected flow between topics (linear, hub-and-spoke, conditional)?
- Are there topics that should delegate to sub-agents?

### State Management
- What data must persist across the conversation (mutable variables)?
- What external data is needed at start (linked variables from session/context)?
- Are there counters, flags, or accumulators that track progress?
- What default values make sense for each variable?

### Actions
- Which actions require Flow targets vs. Apex targets?
- What are the required inputs and outputs for each action?
- Which actions need `available when` guards?
- Are there actions that must chain deterministically (post-action follow-ups)?

### Reasoning
- Which decisions must be deterministic (code-enforced) vs. LLM-flexible?
- Where should data be loaded (pre-LLM) vs. displayed (LLM instructions)?
- Are there escalation thresholds or retry limits?
- What guardrails must the system instructions enforce?
