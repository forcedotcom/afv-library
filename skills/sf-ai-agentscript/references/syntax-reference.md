<!-- Parent: sf-ai-agentscript/SKILL.md -->
# Agent Script Syntax Reference

> Complete syntax guide for the Agent Script DSL. Your entire agent in one `.agent` file.

---

## Design Principles

| Principle | Description |
|-----------|-------------|
| **Declarative Over Imperative** | Describe WHAT the agent should do, not HOW step-by-step |
| **Human-Readable by Design** | Syntax resembles structured English - non-engineers can read it |
| **Single File Portability** | Entire agent definition in one `.agent` file - copy/paste ready |
| **Version Control Friendly** | Plain text works with Git - diff, review, rollback |

---

## Block Structure

### Recommended Top-Level Block Convention

Use the following order as this skill's preferred convention:

```
config → variables → system → connection → knowledge → language → start_agent → topic
```

| Block | Required | Purpose |
|-------|----------|---------|
| `config:` | ✅ Yes | Agent metadata and identification |
| `variables:` | Optional | State management (mutable/linked) |
| `system:` | ✅ Yes | Global messages and instructions |
| `connection:` | Optional | Escalation routing (`connection messaging:` — singular, NOT `connections:`) |
| `knowledge:` | Optional | Knowledge base configuration |
| `language:` | Optional | Supported languages |
| `start_agent:` | ✅ Yes | Entry point (exactly one) |
| `topic:` | ✅ Yes | Conversation topics (one or more) |

> ✅ **Evidence note**: Official Salesforce docs and examples present top-level blocks in varying sequences, and local validation evidence indicates both config-first and system-first orderings compile. Use one convention consistently, but do not treat top-level block order alone as a correctness rule.

### Block Internal Ordering

Within `start_agent` and `topic` blocks, sub-blocks follow this order:

```
description → system → actions → reasoning → after_reasoning
```

Within a `reasoning` block:

```
instructions → actions
```

---

## Block Definitions

### 1. system: Block (Required)

```yaml
system:
  messages:
    welcome: "Hello! How can I help?"
    error: "Sorry, something went wrong."
  instructions: "You are a helpful assistant."
```

| Field | Purpose |
|-------|---------|
| `messages.welcome` | Initial greeting message |
| `messages.error` | Fallback error message |
| `instructions` | Global system prompt for the agent |

> **Message syntax note**: Quoted strings are fine for **static** `welcome` / `error` messages. If a welcome or error message includes variable interpolation such as `{!@variables.user_preferred_name}`, author that message in template/block form with `|` so the value is rendered in the system message. For first-turn personalization, prefer linked or session-backed variables.

**❌ Wrong — quoted interpolation can render literally**
```yaml
system:
  messages:
    welcome: "Hi {!@variables.user_preferred_name}!"
    error: "Sorry, something went wrong."
  instructions: "You are a helpful assistant."
```

**✅ Correct — use block form for dynamic system messages**
```yaml
system:
  messages:
    welcome: |
      Hi {!@variables.user_preferred_name}! How can I help today?
    error: "Sorry, something went wrong."
  instructions: "You are a helpful assistant."
```

---

### 2. config: Block (Required)

```yaml
config:
  developer_name: "refund_agent"
  description: "Handles refund requests"
  agent_type: "AgentforceServiceAgent"
  default_agent_user: "admin@yourorg.com"
```

| Field | Required | Purpose |
|-------|----------|---------|
| `developer_name` | ✅ Yes | Internal identifier (must match folder name, case-sensitive) |
| `description` | ✅ Yes | Agent's goals and purpose |
| `agent_type` | ✅ Yes | `AgentforceServiceAgent` or `AgentforceEmployeeAgent` |
| `default_agent_user` | ⚠️ **REQUIRED** | Must be valid Einstein Agent User |
| `agent_label` | Optional | Display name for the agent in UI (defaults to `developer_name` if omitted) |
| `agent_description` | Optional / compatibility | Alternative config key accepted by local tooling; public docs/examples in this skill prefer `description` |
| `company` | Optional | Company context for the agent |
| `role` | Optional | Role/persona description for the agent |
| `agent_version` | Optional / system-managed | Agent version metadata |
| `enable_enhanced_event_logs` | Optional | Enables enhanced conversation logging (`True` / `False`) |
| `user_locale` | Optional | User locale setting |

> ⚠️ **Critical**: `default_agent_user` must exist in the org with the "Einstein Agent User" profile. Query: `SELECT Username FROM User WHERE Profile.Name = 'Einstein Agent User' AND IsActive = true`

> ⚠️ **Official-docs caution**: `company`, `role`, `agent_version`, `enable_enhanced_event_logs`, and `user_locale` are documented by Salesforce. This skill now records them for completeness, but local field behavior has not been revalidated to the same depth as the core fields above.

---

### 3. variables: Block (Optional)

```yaml
variables:
  # Mutable: State we track and modify
  failed_attempts: mutable number = 0
  customer_verified: mutable boolean = False
    label: "Customer Verified"
  order_ids: mutable list[string] = []
  order_notes: mutable string = ""
    description: |
      Notes collected during the order process.
      May contain multiple lines of customer input.

  # Linked: Read-only from external sources
  session_id: linked string
    source: @session.sessionID
    description: "Current session identifier"
  customer_id: linked string
    source: @context.customerId
    description: "Customer ID from context"
```

> 💡 Variables support a `label:` property for UI display names and multiline `description: |` using pipe syntax.

> 💡 Variables also support a `visibility:` property with values `"Internal"` (default — hidden from end user, used by planner only) or `"External"` (visible to end user in the chat interface). Example: `visibility: "External"`

#### Variable Types

| Type | Description | Example |
|------|-------------|---------|
| `string` | Text values | `name: mutable string = ""` |
| `number` | Numeric values | `count: mutable number = 0` |
| `boolean` | True/false flags | `verified: mutable boolean = False` |
| `object` | Structured data | `data: mutable object = {}` |
| `date` | Calendar dates | `created: mutable date` |
| `id` | Unique identifiers | `record_id: mutable id` |
| `list[T]` | Arrays of type T | `items: mutable list[string] = []` |

**Action-Only Types** (valid for action I/O, NOT for mutable/linked variables):

| Type | Description |
|------|-------------|
| `datetime` | Date and time (action I/O only) |
| `time` | Time of day (action I/O only) |
| `integer` | Whole numbers (action I/O only) |
| `long` | Large whole numbers (action I/O only) |
| `timestamp` | Date and time (action I/O only) |
| `currency` | Money values (action I/O only) |

> ⚠️ **Undocumented variable types**: `timestamp` and `currency` compile as variable types but are absent from official GA documentation. Prefer `date` for date/time variables and `number` for currency values. These types are reliable for action I/O.

> ⚠️ **`date` type fails in action I/O**: Using `date` as an action input or output type compiles but causes a runtime error (`'Date'`). Use `object` with `complex_data_type_name: "lightning__dateType"` instead. The `date` type works correctly for mutable/linked variables — the issue is only in action I/O. See [known-issues.md](known-issues.md#issue-28) Issue 28.

#### Variable Modifiers

| Modifier | Behavior | Use Case |
|----------|----------|----------|
| `mutable` | Read/write - can be changed during conversation | Counters, flags, accumulated state |
| `linked` | Read-only - populated from external source | Session IDs, user profiles, context data |

> ⚠️ **Booleans are capitalized**: Use `True`/`False`, not `true`/`false`

---

### 4. language: Block (Optional)

```yaml
language:
  default: "en_US"
  supported: ["en_US", "es_ES", "fr_FR"]
```

---

### 5. knowledge: Block (Optional)

```yaml
knowledge:
  knowledge_base: "My_Knowledge_Base"
  citations_enabled: False
```

| Field | Required | Purpose |
|-------|----------|---------|
| `knowledge_base` | ✅ Yes (if block present) | Name of the knowledge base to attach to the agent |
| `citations_enabled` | Optional | `True`/`False` — controls whether knowledge citations are included in responses (default: `True` if omitted). Set to `False` if citations are not needed or if using NGA agents where citations do not render (Issue 32). |

> 💡 Knowledge bases are configured in the Salesforce org and referenced by name. The knowledge block enables RAG (Retrieval Augmented Generation) capabilities for the agent.

> ⚠️ **Required even without Data Library**: If your agent references knowledge in any topic but you don't have a Data Library configured, you still need a `knowledge:` block with `citations_enabled: False` to prevent compilation errors.

---

### 6. connection: Block (Optional)

```yaml
# Minimal form (no routing):
connection messaging:
   adaptive_response_allowed: True

# Full form with escalation routing:
connection messaging:
   outbound_route_type: "OmniChannelFlow"
   outbound_route_name: "flow://Route_from_Agent"
   escalation_message: "Connecting you with a specialist."
   adaptive_response_allowed: False
```

> ⚠️ Use `connection messaging:` (singular, NOT `connections:`). The plural `connections:` wrapper is invalid — see [known-issues.md](known-issues.md#issue-16) Issue 16.

#### Supported Channels

| Channel | Purpose |
|---------|---------|
| `messaging` | Chat/messaging channels (Enhanced Chat, Web Chat, In-App) |
| `voice` | Voice/phone channels (Service Cloud Voice) |
| `web` | Web-based channels |

---

### 7. topic: Block (Required - one or more)

```yaml
topic main:
  description: "Main conversation handler"
  reasoning:
    instructions: |
      Help the user with their request.
    actions:
      do_something: @actions.my_action
        description: "Action description"
```

| Field | Purpose |
|-------|---------|
| `description` | Helps LLM understand topic purpose |
| `reasoning.instructions` | Instructions for this topic |
| `reasoning.actions` | Available actions in this topic |

#### Topic-Level System Overrides

Topics can override the agent-level `system:` instructions with their own `system:` block:

```yaml
topic specialized_support:
   description: "Handles technical support"
   system:
      instructions: "You are a technical support specialist. Be precise and methodical."
   reasoning:
      instructions: |
         Help with technical issues.
```

> The topic-level `system:` replaces (not appends to) the agent-level system instructions for that topic's reasoning context.

---

### 8. start_agent: Block (Required - exactly one)

```yaml
start_agent entry:
  description: "Entry point for conversations"
  reasoning:
    instructions: |
      Greet the user and route appropriately.
    actions:
      go_main: @utils.transition to @topic.main
        description: "Navigate to main topic"
```

> 💡 The name can be anything - "main", "entry", "topic_selector" - just be consistent.

---

## Instruction Syntax

### Pipe vs Arrow Syntax

| Syntax | Use When | Example |
|--------|----------|---------|
| `instructions: \|` | Simple multi-line text (no expressions) | `instructions: \| Help the user.` |
| `instructions: ->` | Complex logic with conditionals/actions | `instructions: -> if @variables.x:` |

### Arrow Syntax (`->`) Patterns

```yaml
reasoning:
  instructions: ->
    # Conditional (resolves BEFORE LLM)
    if @variables.customer_verified == True:
      | Welcome back, verified customer!
    else:
      | Please verify your identity first.

    # Inline action execution
    run @actions.load_customer
      with customer_id = @variables.customer_id
      set @variables.customer_data = @outputs.data

    # Variable injection in text
    | Customer name: {!@variables.customer_name}

    # Deterministic transition
    if @variables.failed_attempts >= 3:
      transition to @topic.escalation
```

### Instruction Syntax Elements

| Element | Syntax | Purpose |
|---------|--------|---------|
| Literal text | `\| text` | Text that becomes part of LLM prompt |
| Conditional | `if @variables.x:` | Resolves before LLM sees instructions |
| Else clause | `else:` | Alternative path |
| Inline action | `run @actions.x` | Execute action during resolution |
| Set variable | `set @var = @outputs.y` | Capture action output |
| Template injection | Curly-bang syntax: {!@variables.x} | Insert variable value into text |
| Deterministic transition | `transition to @topic.x` | Change topic without LLM |

> ⚠️ **`else if` is NOT supported**: Agent Script does not have an `else if` keyword. Nested `if` inside `else:` is also invalid. Use compound conditions (`if A and B:`) or flatten to sequential `if` statements.

### Multiline String Continuation

Long literal text can span multiple lines using indented continuation:

```yaml
instructions: |
  | This is a long instruction that
    continues on the next line without a pipe.
```

The continued line is indented further than the `|` line and does NOT start with a new `|`.

### Deterministic Resolution vs LLM-Driven Tool Use

`instructions: ->` mixes two very different execution modes. Treat them separately when authoring.

| Pattern | Who executes it | When it runs | Supports `...` | Best use |
|---------|------------------|--------------|----------------|----------|
| `run @actions.X` inside `instructions: ->` | Deterministic resolver | Before the LLM sees the final prompt | **No** | Preload data, normalize state, perform fixed control flow |
| `reasoning.actions` tool invocation | LLM / planner | After instructions resolve | **Yes** | Slot filling, user-driven tool calls, flexible next-step selection |
| `@utils.setVariables` from `reasoning.actions` | LLM / planner | After instructions resolve | **Yes** | Capture user-provided values into variables for later deterministic use |

**Rule of thumb:** if a line begins with `run` inside `instructions: ->`, every `with` value must already exist as a literal, a variable, or a prior action output. Do not expect the resolver to slot-fill `...` in that phase.

**❌ Wrong — deterministic `run` cannot slot-fill**
```yaml
reasoning:
  instructions: ->
    run @actions.send_verification_code
      with email = ...
```

**✅ Correct — let the LLM capture first, then use the saved variable**
```yaml
variables:
  member_email: mutable string = ""

topic collect_email:
  reasoning:
    instructions: ->
      if @variables.member_email == "":
        | Ask the user for their email address, then call {!@actions.save_email}.
      else:
        transition to @topic.send_code
    actions:
      save_email: @utils.setVariables
        description: "Save the user's email address"
        with member_email = ...

topic send_code:
  reasoning:
    instructions: ->
      run @actions.send_verification_code
        with email = @variables.member_email
```

---

## Action Configuration

### Action Declaration

```yaml
actions:
  action_name: @actions.my_action
    description: "What this action does"
    with input_param = @variables.some_value
    set @variables.result = @outputs.output_field
    available when @variables.is_authorized == True
```

### Action `source` Attribute

Actions imported from the Agentforce Asset Library require a `source:` attribute that matches the asset library's API name:

```yaml
actions:
   search_knowledge:
      description: "Search the knowledge base"
      source: "My_Knowledge_Asset"   # Must match asset library API name exactly
      inputs:
         query: string
      outputs:
         answer: string
      target: "retriever://My_Knowledge_Base"
```

> ⚠️ If `source:` does not match the asset library API name exactly (case-sensitive), the action will fail at publish time with a reference resolution error.

### Action Metadata Properties

Action definitions with `target:` support the following metadata properties. These are NOT valid on `@utils.transition` utility actions.

**Action-Level:**

| Property | Type | Context | Notes |
|----------|------|---------|-------|
| `label` | String | Action def, topic, I/O | Display name in UI |
| `description` | String | Action def, I/O | LLM decision-making context |
| `require_user_confirmation` | Boolean | Action def | Compiles; runtime no-op (Issue 6) |
| `include_in_progress_indicator` | Boolean | Action def | Shows spinner during execution |
| `progress_indicator_message` | String | Action def | Custom spinner text |

**Input-Level:**

| Property | Type | Notes |
|----------|------|-------|
| `is_required` | Boolean | Marks input as mandatory — ⚠️ NOT enforced by planner (Issue 26) |
| `is_user_input` | Boolean | LLM extracts from conversation |
| `label` | String | Display name |
| `description` | String | LLM context |
| `complex_data_type_name` | String | Lightning type mapping |
| `lightning:isPII` | Boolean | Marks field as PII for platform data handling and masking |

**Output-Level:**

| Property | Type | Notes |
|----------|------|-------|
| `filter_from_agent` | Boolean | `True` = hide from user display (GA standard name) |
| `is_displayable` | Boolean | `False` = hide from user (compile-valid alias for `filter_from_agent`). ⚠️ Setting `True` on prompt template outputs causes blank response (Issue 34) |
| `is_used_by_planner` | Boolean | `True` = LLM can reason about value |
| `developer_name` | String | Overrides the parameter's developer name |
| `label` | String | Display name |
| `description` | String | LLM context |
| `complex_data_type_name` | String | Lightning type mapping |
| `lightning:isPII` | Boolean | Marks field as PII for platform data handling and masking |

---

### Two-Level Action System

Agent Script uses a two-level system for actions. Understanding this distinction is critical:

```
Level 1: ACTION DEFINITION (in topic's `actions:` block)
   → Has `target:`, `inputs:`, `outputs:`, `description:`
   → Specifies WHAT to call (e.g., "flow://GetOrderStatus")

Level 2: ACTION INVOCATION (in `reasoning.actions:` block)
   → References Level 1 via `@actions.name`
   → Specifies HOW to call it (`with`, `set` clauses)
   → Does NOT use `inputs:`/`outputs:` (use `with`/`set` instead)
```

**Complete Example:**
```yaml
topic order_lookup:
   description: "Look up order details"

   # Level 1: DEFINE the action (with target + I/O schemas)
   actions:
      get_order:
         description: "Retrieves order information by ID"
         inputs:
            order_id: string
               description: "Customer's order number"
         outputs:
            status: string
               description: "Current order status"
         target: "flow://Get_Order_Details"

   reasoning:
      instructions: |
         Help the customer check their order status.
      # Level 2: INVOKE the action (with/set, NOT inputs/outputs)
      actions:
         lookup: @actions.get_order
            with order_id = ...
            set @variables.order_status = @outputs.status
```

> ⚠️ **I/O schemas are REQUIRED for publish**: Action definitions with only `description:` and `target:` (no `inputs:`/`outputs:`) will PASS LSP and CLI validation but FAIL server-side compilation with "Internal Error." Always include complete I/O schemas in Level 1 definitions.

---

### Lifecycle Hooks: `before_reasoning:` and `after_reasoning:`

Lifecycle hooks enable deterministic pre/post-processing around LLM reasoning. They are FREE (no credit cost).

```yaml
topic main:
   description: "Topic with lifecycle hooks"

   # BEFORE: Runs deterministically BEFORE LLM sees instructions
   before_reasoning:
      # Content goes DIRECTLY here (NO instructions: wrapper!)
      set @variables.turn_count = @variables.turn_count + 1
      if @variables.needs_redirect == True:
         transition to @topic.redirect

   # LLM reasoning phase
   reasoning:
      instructions: ->
         | Turn {!@variables.turn_count}: How can I help?

   # AFTER: Runs deterministically AFTER LLM finishes reasoning
   after_reasoning:
      # Content goes DIRECTLY here (NO instructions: wrapper!)
      set @variables.interaction_logged = True
```

**Key Rules:**
- Content goes **directly** under the block (NO `instructions:` wrapper)
- Reliable primitives: `set`, `if`/`else`, `transition to`
- `run` behavior: lifecycle-hook syntax is valid, but `run @actions.X` inside `before_reasoning:` / `after_reasoning:` is not portable enough to treat as universally reliable. It has worked in some target-backed cases, but behavior is inconsistent across bundle types and org states. Safest guidance: keep lifecycle hooks focused on `set`, `if`/`else`, and `transition to`, and use `run` primarily in `reasoning.actions:` post-action chains or `instructions: ->` blocks.
- `transition to` works in `after_reasoning:` blocks
- If a topic transitions mid-execution, the original topic's `after_reasoning:` does NOT run
- Both hooks are FREE (no credit cost) — use for data prep, logging, cleanup

> 💡 Official GA docs show `after_reasoning:->` (arrow syntax). Our TDD validated the direct-content form. Both forms may work — we recommend the tested direct-content form.

---

### Action Target Protocols

**Core Targets (Validated)**

| Protocol | Use When | Status |
|----------|----------|--------|
| `flow://` | Data operations, business logic | ✅ Validated |
| `apex://` | Custom calculations, validation | ✅ Validated |
| `prompt://` / `generatePromptResponse://` | Grounded LLM responses | ✅ Validated |
| `api://` | REST API callouts | ✅ Validated |
| `retriever://` | RAG knowledge search | ✅ Validated |
| `externalService://` | Third-party APIs via Named Credential | ✅ Validated |
| `standardInvocableAction://` | Built-in SF actions | ✅ Validated |

**Additional Targets (From agent-script-recipes)**

| Protocol | Use When | Status |
|----------|----------|--------|
| `datacloudDataGraphAction://` | Data Cloud graph queries | ⚠️ Untested |
| `datacloudSegmentAction://` | Data Cloud segment operations | ⚠️ Untested |
| `triggerByKnowledgeSource://` | Knowledge-triggered actions | ⚠️ Untested |
| `contextGrounding://` | Context grounding operations | ⚠️ Untested |
| `predictiveAI://` | Einstein predictions | ⚠️ Untested |
| `runAction://` | Sub-action execution | ⚠️ Untested |
| `external://` | External services | ⚠️ Untested |
| `copilotAction://` | Copilot actions | ⚠️ Untested |
| `@topic.X` | Topic delegation (supervision) | ✅ Validated |

> **Note**: Untested targets are documented in the official AGENT_SCRIPT.md rules. They may require specific licenses, org configurations, or future API versions.

> 💡 `prompt://` is the official shorthand for `generatePromptResponse://`. Both forms resolve to the same target. Example: `target: "prompt://Email_Draft_Template"`

### Utility Actions

| Action | Purpose | Example |
|--------|---------|---------|
| `@utils.transition to @topic.x` | LLM-chosen topic navigation | `go_main: @utils.transition to @topic.main` |
| `@utils.escalate` | Hand off to human agent | `escalate: @utils.escalate` |
| `@utils.setVariables` | Set multiple variables | `set_vars: @utils.setVariables` |

---

## Resource References

| Syntax | Purpose | Example |
|--------|---------|---------|
| `@variables.x` | Reference a variable | `@variables.customer_id` |
| `@actions.x` | Reference an action | `@actions.process_refund` |
| `@topic.x` | Reference a topic | `@topic.escalation` |
| `@outputs.x` | Reference action output | `@outputs.status` |
| `@session.x` | Reference session data | `@session.sessionID` |
| `@context.x` | Reference context data (**Employee Agents on LEX only** — NOT available for Service Agents; see Issue 39) | `@context.userProfile` |
| `@inputs.x` | Reference procedure input | `@inputs.account_number` ⚠️ Procedure context only — see Common Pitfalls |
| `@system_variables.user_input` | Most recent user utterance | `@system_variables.user_input` |
| `@knowledge.citations_url` | Knowledge citation URL config | `@knowledge.citations_url` |
| `@knowledge.rag_feature_config_id` | RAG feature configuration ID | `@knowledge.rag_feature_config_id` |
| `@knowledge.citations_enabled` | Whether citations are active | `@knowledge.citations_enabled` |

> 💡 `@system_variables` is a separate namespace from `@variables`. The `user_input` system variable contains the customer's most recent utterance.

> ⚠️ Treat `@system_variables.user_input` as raw text, not a durable deterministic intent signal. Direct guards like `if @system_variables.user_input contains "never mind":` are brittle for control-flow-critical routing. Prefer a Flow, Apex, or classifier action that normalizes the utterance into a boolean or enum variable first.

#### Common Linked Variable Sources

Linked variables commonly reference these external source patterns:

| Source Pattern | Description | Example |
|----------------|-------------|---------|
| `@session.sessionID` | Current session identifier | Standard session context |
| `@context.customerId` | Customer ID from context | **Employee Agents on LEX pages only** — NOT available for Service Agents (Issue 39) |
| `@MessagingSession.{field}` | Messaging session fields (Service Agents) | `@MessagingSession.MessagingEndUserId` |
| `@MessagingEndUser.{field}` | Messaging end user fields (Service Agents) | `@MessagingEndUser.Name`, `@MessagingEndUser.ContactId` |

> ⚠️ **Agent Type Determines Source Availability**: `@context.*` sources resolve LEX page-level context — they only work for **Employee Agents** embedded on Lightning record pages. **Service Agents** (NGA / ExternalCopilot) must use `@MessagingSession.*` or `@MessagingEndUser.*` for channel context. Using `@context.*` in a Service Agent compiles but produces "Unsupported data type" at runtime. See [known-issues.md](known-issues.md#issue-39) Issue 39.

```yaml
# Common Messaging channel linked variables
variables:
   session_key: linked string
      source: @MessagingSession.MessagingSessionKey
      description: "Unique messaging session key"
   end_user_name: linked string
      source: @MessagingEndUser.Name
      description: "End user display name from messaging channel"
   contact_id: linked string
      source: @MessagingEndUser.ContactId
      description: "Contact record ID linked to messaging end user"
```

> 💡 `@MessagingSession` and `@MessagingEndUser` sources are available when the agent is deployed on a Messaging channel (Enhanced Chat, In-App, Web Chat). They are NOT available in Agent Builder Preview or `sf agent preview`.

### Output Access Depends on the Declared Schema

Do **not** assume `@outputs.X` is always a plain scalar. The correct access pattern depends on the action's declared output shape.

```yaml
# Scalar output → direct assignment is fine
set @variables.order_status = @outputs.status

# Structured output → keep it as an object, or access a concrete field
set @variables.raw_result = @outputs.output
set @variables.result_text = @outputs.output.value      # if the output schema exposes 'value'
```

**Guidance:**
- If the output is declared as `string`, `number`, or `boolean`, direct assignment is fine.
- If the output is declared as `object` or another structured type, inspect the schema before branching on it.
- Some actions wrap their primary scalar under a field such as `.value`; others expose named properties directly.
- When a deterministic branch depends on the result, the safest design is to flatten the target output in Flow/Apex so Agent Script receives an explicit scalar like `is_after_hours: boolean` instead of a wrapper object.

---

## Whitespace Rules

### Indentation

| ✅ CORRECT | ❌ INCORRECT |
|------------|-------------|
| 2-space consistent | Mixed tabs and spaces |
| 3-space consistent | Inconsistent spacing |
| Tabs consistent | Tab in one block, spaces in another |

> **CRITICAL**: Never mix tabs and spaces in the same file. This causes compilation errors.

### Boolean Values

| ✅ CORRECT | ❌ INCORRECT |
|------------|-------------|
| `True` | `true` |
| `False` | `false` |

---

## Complete Example

```yaml
system:
  messages:
    welcome: "Welcome to Pronto Support!"
    error: "Sorry, something went wrong. Let me connect you with a human."
  instructions: "You are a helpful customer service agent for Pronto Delivery."

config:
  developer_name: "pronto_refund_agent"
  description: "Handles customer refund requests with churn risk assessment"
  agent_type: "AgentforceServiceAgent"
  default_agent_user: "agent_user@myorg.com"

variables:
  # Mutable state
  customer_verified: mutable boolean = False
  failed_attempts: mutable number = 0
  churn_risk_score: mutable number = 0
  refund_status: mutable string = ""

  # Linked from session
  customer_id: linked string
    source: @session.customerId
    description: "Customer ID from messaging session"

topic identity_verification:
  description: "Verify customer identity before refund processing"
  reasoning:
    instructions: ->
      if @variables.failed_attempts >= 3:
        | Too many failed attempts. Escalating to human agent.
        transition to @topic.escalation

      if @variables.customer_verified == True:
        | Identity verified. Proceeding to refund assessment.
        transition to @topic.refund_processor

      | Please verify your identity by providing your email address.
    actions:
      verify: @actions.verify_customer
        description: "Verify customer by email"
        set @variables.customer_verified = @outputs.verified

topic refund_processor:
  description: "Process refund based on churn risk assessment"
  reasoning:
    instructions: ->
      # Post-action check (triggers on loop after refund)
      if @variables.refund_status == "Approved":
        run @actions.create_crm_case
          with customer_id = @variables.customer_id
        transition to @topic.success

      # Pre-LLM: Load churn data
      run @actions.get_churn_score
        with customer_id = @variables.customer_id
        set @variables.churn_risk_score = @outputs.score

      # Dynamic instructions based on score
      | Customer churn risk: {!@variables.churn_risk_score}%

      if @variables.churn_risk_score >= 80:
        | HIGH RISK - Offer full cash refund to retain customer.
      else:
        | LOW RISK - Offer $10 store credit as goodwill.
    actions:
      process_refund: @actions.process_refund
        description: "Issue the refund"
        available when @variables.customer_verified == True
        set @variables.refund_status = @outputs.status

topic escalation:
  description: "Escalate to human agent"
  reasoning:
    instructions: |
      Apologize for the inconvenience and transfer to a human agent.
    actions:
      handoff: @utils.escalate
        description: "Transfer to live support"

topic success:
  description: "Successful refund confirmation"
  reasoning:
    instructions: |
      Thank the customer and confirm their refund has been processed.

start_agent topic_selector:
  description: "Entry point - route to identity verification"
  reasoning:
    instructions: |
      Greet the customer and begin identity verification.
    actions:
      start: @utils.transition to @topic.identity_verification
        description: "Begin refund process"
```

---

## Expression Operators

### Comparison Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `==` | Equal to | `if @variables.status == "active":` |
| `!=` | Not equal to | `if @variables.status != "closed":` |
| `<` | Less than | `if @variables.count < 10:` |
| `<=` | Less than or equal | `if @variables.count <= 5:` |
| `>` | Greater than | `if @variables.risk > 80:` |
| `>=` | Greater than or equal | `if @variables.attempts >= 3:` |
| `is` | Identity check | `if @variables.data is None:` |
| `is not` | Negated identity check | `if @variables.data is not None:` |

> **Note**: Use `!=` for not-equal comparisons. The `<>` operator does NOT compile.

### Logical Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `and` | Logical AND | `if @variables.verified == True and @variables.active == True:` |
| `or` | Logical OR | `if @variables.status == "open" or @variables.status == "pending":` |
| `not` | Logical NOT | `if not @variables.blocked:` |

### Arithmetic Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `+` | Addition | `set @variables.count = @variables.count + 1` |
| `-` | Subtraction | `set @variables.remaining = @variables.total - @variables.used` |

> ⚠️ **NOT supported**: `*` (multiplication), `/` (division), `%` (modulo). For complex arithmetic, use a Flow or Apex action.

### Access Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `.` | Property access | `@outputs.result.status` |
| `[]` | Index access | `@variables.items[0]` |

### Conditional Expression (Ternary-like)

```yaml
| Status: {!@variables.status if @variables.status else "pending"}
```

### Expression Limitations (Sandboxed Python AST Subset)

Agent Script expressions use a sandboxed subset of Python. Not all Python operations are available.

**Supported:**

| Category | Operations |
|----------|-----------|
| Arithmetic | `+`, `-` |
| Comparison | `==`, `!=`, `<`, `<=`, `>`, `>=`, `is`, `is not` |
| Logical | `and`, `or`, `not` |
| Ternary | `x if condition else y` |
| Built-in functions | `len()`, `max()`, `min()` |
| Attribute access | `@outputs.result.field` |
| Index access | `@variables.items[0]` |
| String methods | `contains`, `startswith`, `endswith` |

> ⚠️ **Portability warning**: `contains` / `startswith` / `endswith` may compile, but they are not the safest choice for control-flow-critical validation or intent routing. Use them only as light heuristics. For URL validation, cancellation detection, or anything that must deterministically gate behavior, prefer a Flow/Apex/classifier action that returns a normalized boolean or enum.

**NOT Supported:**

| Operation | Workaround |
|-----------|-----------|
| Multiplication (`*`) | Use Flow/Apex action |
| Division (`/`) | Use Flow/Apex action |
| Modulo (`%`) | Use Flow/Apex action |
| String concatenation (`+` on strings) | Use `{!var1}{!var2}` template injection |
| List slicing (`items[1:3]`) | Use Flow to extract sublist |
| List comprehensions (`[x for x in ...]`) | Use Flow/Apex for list transformation |
| Lambda expressions | Use Flow/Apex action |
| `for`/`while` loops | Use topic loop pattern (re-entry) |
| `import` statements | Not available (security sandbox) |
| Empty list literal in expressions (`== []`, `= []`) | Use `len(@variables.list) == 0` for empty check; use temp empty var for reset (Issue 33) |

### Apex Complex Type Notation

When action inputs or outputs reference Apex inner classes, use the `@apexClassType` notation:

```
@apexClassType/c__OuterClass$InnerClass
```

| Component | Description | Example |
|-----------|-------------|---------|
| `@apexClassType/` | Required prefix | — |
| `c__` | Default namespace (or your package namespace) | `c__`, `myns__` |
| `OuterClass` | The containing Apex class | `OrderService` |
| `$` | Inner class separator | — |
| `InnerClass` | The inner class name | `LineItem` |

**Example:**
```yaml
actions:
   process_order:
      inputs:
         line_items: list[object]
            complex_data_type_name: "@apexClassType/c__OrderService$LineItem"
      target: "apex://OrderService"
```

> **Note**: This notation is used in the `complex_data_type_name` field of action input/output definitions in Agentforce Assets, not in the `.agent` file directly.

---

## Current Limitations and Practical Workarounds

| Limitation | What happens | Practical workaround |
|------------|--------------|----------------------|
| `set @variables.list = []` in runtime logic | Parse error (`[` not allowed in expression position) | Define a dedicated empty list variable and assign from it |
| Nested object mutation such as `set @variables.profile.name = ...` | Mutation is not portable / may fail silently or parse incorrectly | Flatten state into scalar variables or shape structured data upstream in Flow/Apex |
| Direct variable capture with `set @variables.x = ...` | No user input is captured | Expose `@utils.setVariables` (or another LLM-invoked action) and let the planner fill `...` |
| Exact quoted field names in special cases | Raw `.agent` may be valid, but some visual editors can rewrite the field name during round-trip save/reformat | Treat the raw `.agent` file in source control as the source of truth and diff after builder edits |

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Mixed tabs/spaces | `SyntaxError: cannot mix` | Use consistent indentation |
| Invalid boolean | Type mismatch | Use `True`/`False` (capitalized) |
| Spaces in variable names | Parse error | Use `snake_case` |
| Mutable + linked | Conflicting modifiers | Choose one modifier |
| Missing `source:` for linked | Variable empty | Add `source: @session.X` |
| Missing `default_agent_user` | Internal error on deploy | Add valid Einstein Agent User |
| `@inputs` in `set` directive | Unknown deploy error | Use `@utils.setVariables` to capture inputs separately, then reference via `@variables` |
| `set @variables.X = ...` | Variable never fills from user input | Capture the value through an LLM-invoked action such as `@utils.setVariables`, then read `@variables.X` later |
| Bare action name (no prefix) | Action not found / ignored | Always use `@actions.action_name` in `run`, templates, and instruction text |
| `run @actions.X with param = ...` | Deterministic inline `run` never slot-fills the parameter | Capture the value first with an LLM-invoked action, then run deterministically using the saved variable |
| `run @actions.X` for utility / delegation / unresolved action | `ACTION_NOT_IN_SCOPE`, action not found, or available-actions list excludes the name | `run @actions.X` resolves only to topic-level `actions:` that declare `target:`. Use direct `set` / `transition to` for deterministic utility behavior, or let `reasoning.actions:` invoke the utility. |
| `set @variables.object.field = ...` or `set @variables.object["field"] = ...` | Nested object updates fail or behave inconsistently | Use flattened scalar variables, or update the structure in Flow/Apex and return a fresh object |
| Null check vs empty string | Wrong comparison for null | Use `is None` for null checks, `== ""` for empty strings — they are different |
| `is_required` not enforced | Planner invokes action without required inputs | Use `available when @variables.X is not None` guard instead. `is_required` is a hint, not a gate. See Issue 26 |
| Raw `@system_variables.user_input contains/startswith/endswith` routing | Cancellation/revision intent checks behave inconsistently | Use a Flow/Apex/classifier action to normalize the utterance into a boolean or enum, then branch on `@variables.X`. See Issue 42 |
| `contains` / `startswith` / `endswith` as critical validation gates | URL or string guards compile but behave unevenly across authoring/runtime contexts | Prefer an upstream validation action that returns an explicit scalar like `is_valid_url: boolean`. |
| `date` type in action I/O | Runtime error `'Date'` | Use `object` + `complex_data_type_name: "lightning__dateType"` in action I/O. `date` works fine for variables. See Issue 28 |
| `== []` or `set = []` in expressions | Parse error (`[` not allowed) | Use `len(@variables.list) == 0` for empty check; use temp empty var for reset. See Issue 33 |
| `is_displayable: True` on prompt outputs | Agent returns blank/empty response | Set `is_displayable: False` and let the reasoner synthesize the output. If the output should influence the response or routing, also set `is_used_by_planner: True`. See Issue 34 |
| Structured output assigned directly to scalar variable | Comparisons fail or wrapper/object text leaks into state | Inspect the output schema and access a concrete property such as `.value` only when that field actually exists, or flatten the output in Flow/Apex first. |
| Line breaks in topic `description:` | Script breaks with syntax error | Keep `description:` on a single line — no line breaks. See Issue 35 |
| Variable name matches system context | "Field is already mapped to a Context Variable" | Avoid names like `Locale`, `Channel`, `Status`, `Origin` — use prefixed names like `customer_locale`. See Issue 36 |
| `filter_from_agent` + `is_used_by_planner` on output | `InvalidFormatError` + cascading `ACTION_NOT_IN_SCOPE` | These are mutually exclusive. Use only `filter_from_agent: True`; remove `is_used_by_planner`. See [Issue 40](known-issues.md#issue-40-filter-planner-conflict). |
| Lifecycle arithmetic on mutable number without null guard | Silent crash: `None + 1` → "unexpected error" | Add `if @variables.X is None: set @variables.X = 0` before arithmetic in `before_reasoning` / `after_reasoning`. See Issue 41 |

### `@inputs` in `set` — Deploy-Breaking Anti-Pattern

```yaml
# ❌ WRONG — @inputs in set causes unknown error at deploy time
verify: @actions.verify_customer
   with account_number=...
   set @variables.account_number = @inputs.account_number

# ✅ CORRECT — use @utils.setVariables to capture input separately
collect_input: @utils.setVariables
   with account_number=...
verify: @actions.verify_customer
   with account_number=@variables.account_number
   set @variables.customer_name = @outputs.customer_name
```

### Direct Variable Capture — Use `@utils.setVariables`, not `set ... = ...`

```yaml
# ❌ WRONG — direct slot-fill in deterministic instructions does not work
reasoning:
   instructions: ->
      set @variables.member_email = ...
      run @actions.send_verification_code
         with email = @variables.member_email

# ✅ CORRECT — let the LLM capture the value through a tool
reasoning:
   instructions: ->
      if @variables.member_email == "":
         | Ask the user for their email address, then call {!@actions.save_email}.
   actions:
      save_email: @utils.setVariables
         description: "Save the user's email address"
         with member_email = ...
```

Once the variable is set, later deterministic logic can safely reference `@variables.member_email`.

### Bare Action Names — Always Use `@actions.` Prefix

```yaml
# ❌ WRONG — bare names in run, templates, and instructions
run set_user_name
| Use add_to_cart to add items.

# ✅ CORRECT — always prefix with @actions.
run @actions.set_user_name
| Use {!@actions.add_to_cart} to add items.
```

### `is None` vs `== ""` — Different Checks

```yaml
# ❌ WRONG — checks for empty string, not null
if @variables.data == "":
   | Data is missing.

# ✅ CORRECT — checks for null/undefined
if @variables.data is None:
   | Data has not been set.

# ✅ CORRECT — checks for empty string
if @variables.data == "":
   | Data is set but empty.
```

> Use `is None` when a variable may not have been set at all. Use `== ""` when checking for an explicitly empty string value.

### `run @actions.X` Only Works for Topic-Level Target-Backed Actions

`run @actions.X` resolves only against topic-level `actions:` definitions that declare a real `target:`. It does **not** work for reasoning-level utilities, and it is also the wrong tool for topic-level utilities / delegations that do not have `target:`.

```yaml
# ❌ WRONG — set_user_name is a reasoning-level utility, not a target-backed action
run @actions.set_user_name   # ACTION_NOT_IN_SCOPE / action not found

reasoning:
   actions:
      set_user_name: @utils.setVariables
         with user_name=...
```

```yaml
# ❌ WRONG — go_help is topic-level, but it is still a utility transition (no target:)
actions:
   go_help: @utils.transition to @topic.help

reasoning:
   instructions: ->
      run @actions.go_help   # not a valid deterministic run target
```

```yaml
# ✅ CORRECT — use direct deterministic primitives for non-target utility behavior
reasoning:
   instructions: ->
      set @variables.user_name = "Pat"
      transition to @topic.help
```

```yaml
# ✅ CORRECT — use run only for a topic-level target-backed action definition
actions:
   load_customer:
      target: "flow://Load_Customer"
      inputs:
         customer_id: string
      outputs:
         customer_name: string

reasoning:
   instructions: ->
      run @actions.load_customer
         with customer_id = @variables.customer_id
         set @variables.customer_name = @outputs.customer_name
```

**Rule of thumb:** if you want deterministic execution, `run` is correct **only** when the referenced action is a topic-level definition with `target:`. Otherwise use direct `set` / `transition to`, or let `reasoning.actions:` expose the utility for LLM-driven invocation.

---

## Upcoming: Naming Changes (Forward-Looking)

> **Roadmap signal**: Salesforce is moving toward renaming core Agent Script concepts. Both old and new names will be supported during a transition period, with the old names deprecated later.

| Current Name | New Name | Notes |
|-------------|----------|-------|
| `topic` | `subagent` | Reflects the delegation/supervision model |
| `action` | `tool` | Aligns with industry-standard LLM terminology |

**No action required now** — current `topic:` and `actions:` syntax continues to work. This is informational for forward planning.
