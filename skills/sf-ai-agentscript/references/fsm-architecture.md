<!-- Parent: sf-ai-agentscript/SKILL.md -->
# FSM Architecture Guide

> Design agent behavior as a finite state machine with deterministic nodes and explicit transitions.

---

## Why FSM Architecture?

### The Problem with Prompt-Only Agents

| Anti-Pattern | Description |
|--------------|-------------|
| **ReAct Pattern** | Agents get stuck in reasoning loops without guardrails |
| **Doom-Prompting** | Prompts grow exponentially to handle edge cases |
| **Goal Drift** | Agents forget original intent after several turns |

> **KEY INSIGHT**: "LLMs are non-deterministic by design. Without structured control flow, enterprise agents become unpredictable, expensive, and impossible to debug."

### The FSM Solution

| FSM Concept | Traffic Light Example | Agent Benefit |
|-------------|----------------------|---------------|
| **States** | Red, Green, Yellow | Agent always knows exactly what it's doing |
| **Transitions** | Timer expires | No ambiguity about what happens next |
| **Determinism** | Red → Green (guaranteed) | Auditable, testable, trustworthy |

---

## The Three FSM Pillars

| Pillar | Definition | Agent Benefit |
|--------|------------|---------------|
| **States** | Distinct "modes" the system can be in | Clear context at any moment |
| **Transitions** | Explicit rules for moving between states | Defined paths, no surprises |
| **Determinism** | Same input → same output | Auditable and testable |

---

## The 5 Node Patterns

### Pattern Overview

| Pattern | Color | Purpose |
|---------|-------|---------|
| 🔵 **ROUTING** | Blue | Routes based on intent |
| 🔵 **VERIFICATION** | Light Blue | Security checks |
| 🟡 **DATA-LOOKUP** | Yellow | External data fetch |
| 🟢 **PROCESSING** | Green | Business logic |
| 🔴 **HANDOFF** | Red | Human escalation |

---

### Pattern 1: ROUTING (Topic Selector)

**Purpose**: Routes conversations based on detected intent

```yaml
start_agent topic_selector:
  description: "Route to appropriate topic based on intent"
  reasoning:
    instructions: ->
      | You are the support agent.
        Classify the customer's intent and route:
        - Refund requests go to identity verification
        - General inquiries are handled directly
    actions:
      start_refund: @utils.transition to @topic.identity_verification
        description: "Customer wants a refund"
      handle_inquiry: @utils.transition to @topic.general_support
        description: "General question or inquiry"
```

**When to Use**: Entry point for multi-purpose agents

#### Routing Heuristics

> **Terminology note:** Public Agentforce docs increasingly say **subagent**. In Agent Script and this repo, the routing unit is still a **topic**.

- Use `description:` as the primary routing signal. Use `label:` for display only.
- Topic names should be short and literal; descriptions should capture the exact job to be done.
- If one utterance fits two topics, narrow, merge, or rename them.
- Keep escalation, handoff, and frustration separate from business-domain intents. Broad escalation descriptions absorb real work.
- Expect re-classification on every new turn. Protected actions and gates must still hold after rerouting.

---

### Pattern 2: VERIFICATION (Identity Gate)

**Purpose**: Enforces security checks before proceeding

```yaml
topic identity_verification:
  description: "Verify customer identity before refund"
  reasoning:
    instructions: ->
      if @variables.failed_attempts >= 3:
        | Too many failed attempts. Escalating to human agent.
      if @variables.email_verified == True:
        | Identity verified. Proceed to risk assessment.
      else:
        | Ask customer to verify their email address.
    actions:
      verify_email: @actions.verify_email
        description: "Verify customer email"
        with email = @variables.customer_email
        set @variables.email_verified = @outputs.verified
      proceed: @utils.transition to @topic.risk_assessment
        description: "Continue to risk assessment"
        available when @variables.email_verified == True
      escalate: @utils.escalate
        description: "Transfer to human agent"
        available when @variables.failed_attempts >= 3
```

**When to Use**: Before accessing sensitive data or actions

---

### Pattern 3: DATA-LOOKUP (Risk Assessment)

**Purpose**: Fetches data from external sources

```yaml
topic risk_assessment:
  description: "Fetch customer data and assess churn risk"
  reasoning:
    instructions: ->
      | Fetch customer profile using the action.
        Once loaded, review:
        - Churn Risk: {!@variables.churn_risk_score}%
        - Lifetime Value: {!@variables.lifetime_value}
    actions:
      get_profile: @actions.get_customer_profile
        description: "Load customer data from CRM"
        with customer_id = @variables.customer_id
        set @variables.churn_risk_score = @outputs.churn_risk
        set @variables.lifetime_value = @outputs.ltv
      process_refund: @utils.transition to @topic.refund_processor
        description: "Continue to refund processing"
```

**When to Use**: When decisions require external data

---

### Pattern 4: PROCESSING (Refund Processor)

**Purpose**: Applies business logic based on conditions

```yaml
topic refund_processor:
  description: "Process refund based on churn risk"
  reasoning:
    instructions: ->
      if @variables.churn_risk_score >= 80:
        | HIGH CHURN RISK - Approve full refund.
      if @variables.churn_risk_score < 80:
        | LOW CHURN RISK - Offer partial credit.
    actions:
      approve_full: @actions.process_refund
        available when @variables.churn_risk_score >= 80
        with amount = @variables.order_total
        with type = "full"
      offer_credit: @actions.issue_credit
        available when @variables.churn_risk_score < 80
        with amount = 10
```

**When to Use**: Applying business rules to data

---

### Pattern 5: HANDOFF (Escalation)

**Purpose**: Transfers conversation to human agent

```yaml
topic escalation:
  description: "Escalate to human agent"
  reasoning:
    instructions: ->
      | Customer has failed verification 3 times.
        Escalating to a human agent for assistance.
    actions:
      handoff: @utils.escalate
        description: "Transfer to human agent"
```

**When to Use**: Failed verification, complex issues, customer request

#### Escalation with Availability Check

> **Production-validated issue**: When `@utils.escalate` is invoked but no human agents are available, the conversation re-enters the topic and triggers the escalation logic again — creating an infinite loop. The built-in 3-4 loop guardrail eventually breaks the cycle, but the user experience is poor (repeated "Connecting you..." messages).

**Fix**: Use a latch variable to detect re-entry after a failed escalation, and route to a fallback topic.

```yaml
variables:
   escalation_attempted: mutable boolean = False

topic escalation:
   description: "Escalate to human agent"

   before_reasoning:
      if @variables.escalation_attempted == True:
         # Already attempted — agents unavailable, go to fallback
         transition to @topic.leave_message

      set @variables.escalation_attempted = True

   reasoning:
      instructions: ->
         | I'm connecting you with a support specialist now.
      actions:
         handoff: @utils.escalate
            description: "Transfer to human agent"

topic leave_message:
   description: "Collect contact info when agents are unavailable"
   reasoning:
      instructions: |
         Our team is currently unavailable. Please leave your name
         and a brief description of your issue, and we'll follow up.
```

**Key Points:**
- `@utils.escalate` does NOT return a success/failure status — you cannot check if escalation succeeded
- Use `before_reasoning:` (FREE, deterministic) to detect re-entry before the LLM runs
- Always provide a fallback topic (leave message, callback request, self-service) for graceful degradation
- See [known-issues.md](known-issues.md#issue-31) Issue 31 for full details

---

## Architecture Patterns

### Pattern 1: Hub and Spoke

Central router to specialized topics.

```
       ┌─────────────┐
       │ topic_sel   │
       │   (hub)     │
       └──────┬──────┘
    ┌─────────┼─────────┐
    ▼         ▼         ▼
┌────────┐ ┌────────┐ ┌────────┐
│refunds │ │ orders │ │support │
│(spoke) │ │(spoke) │ │(spoke) │
└────────┘ └────────┘ └────────┘
```

**When to Use**: Multi-purpose agents with distinct request types

---

### Pattern 2: Linear Flow

Sequential A → B → C pipeline.

```
┌───────┐    ┌────────┐    ┌─────────┐    ┌─────────┐
│ entry │ → │ verify │ → │ process │ → │ confirm │
└───────┘    └────────┘    └─────────┘    └─────────┘
```

**When to Use**: Mandatory steps (onboarding, checkout, compliance)

---

### Pattern 3: Escalation Chain

Tiered support with complexity-based routing.

```
┌───────┐    ┌───────┐    ┌──────────┐    ┌─────────┐
│  L1   │ → │  L2   │ → │    L3    │ → │  human  │
│(basic)│    │ (adv) │    │ (expert) │    │  agent  │
└───┬───┘    └───┬───┘    └────┬─────┘    └─────────┘
    ▼            ▼             ▼
[resolved]  [resolved]    [resolved]
```

**When to Use**: Support workflows with complexity levels

---

### Pattern 4: Verification Gate

Security gate before protected topics.

```
              ┌───────────┐
              │   entry   │
              └─────┬─────┘
                    ▼
              ┌───────────┐◄─────────────┐
              │  VERIFY   │              │
              │  (GATE)   │              │
              └─────┬─────┘              │
          ┌─────────┴─────────┐          │
          ▼                   ▼          │
    [verified=True]    [verified=False]──┘
          │
    ┌─────┴─────────────┐
    ▼         ▼         ▼
┌─────────┐┌─────────┐┌──────────┐
│ account ││payments ││ settings │
│(protect)││(protect)││(protected)│
└─────────┘└─────────┘└──────────┘
```

**When to Use**: Sensitive data, payments, PII access

#### Auth Gate Leak Anti-Pattern

> **Production-validated issue**: Escalation topics with broad descriptions absorb auth-gated intents, bypassing the verification gate entirely.

**The Problem**: When an Escalation topic's description includes broad terms like "billing", "payments", or "appointment changes", the topic classifier routes those intents directly to Escalation — skipping the Verification Gate.

**Example**: User says "Make a payment" -> Expected: Verification Gate -> Payments topic. Actual: Escalation topic (because its description mentions "billing inquiries").

**Common leak intents** (confirmed in production):
- "update credit card" -> Escalation (instead of Auth -> Payment Settings)
- "reschedule appointment" -> Escalation (instead of Auth -> Appointments)
- "pay my bill" -> Escalation (instead of Auth -> Payments)
- "when will my package arrive" -> Escalation (instead of Auth -> Shipping)
- "billing issue" -> Escalation (instead of Auth -> Payments)

**Fix**:
1. **Narrow the Escalation description** — Remove business-domain terms. Keep it focused on meta-intents: "Customer explicitly requests a human agent" or "Customer is frustrated and wants to speak to someone"
2. **Guard protected topics with `available when`** — Add `available when @variables.verified == True` to all post-auth actions so even if routing leaks, the actions are invisible
3. **Test for leaks** — For every auth-gated intent, write a test case asserting the expected auth-first routing path

```yaml
# ❌ Broad escalation description — absorbs payment/appointment intents
topic escalation:
   description: "Handles billing inquiries, appointment issues, account problems, and customer frustration"

# ✅ Narrow escalation description — only catches meta-intents
topic escalation:
   description: "Customer explicitly asks to speak with a human agent or expresses frustration"
```

---

### Pattern 5: State Gate (Open Gate)

3-variable state machine that bypasses the LLM topic selector when a gate holds focus, redirects unauthenticated users to an auth gate, and automatically returns them to their original intended topic after authentication.

```
                      ┌─────────────────────┐
                      │   topic_selector    │
                      │   (start_agent)     │
                      │                     │
                      │ before_reasoning:   │
                      │ if open_gate <> null│
                      │   → bypass LLM     │
                      └──────────┬──────────┘
             ┌───────────────────┼───────────────────┐
             ▼                   ▼                   ▼
  ┌──────────────────┐ ┌────────────────┐ ┌─────────────────┐
  │ protected_topic_A│ │protected_top_B│ │ general_inquiry  │
  │ (auth required)  │ │(auth required)│ │ (no auth needed) │
  │                  │ │               │ │                  │
  │ if !auth → gate  │ │ if !auth→gate │ │ (no gate logic)  │
  │ if auth → lock   │ │ if auth→lock  │ │                  │
  └────────┬─────────┘ └───────┬───────┘ └─────────────────┘
           │ set next_topic    │ set next_topic
           ▼                   ▼
  ┌──────────────────────────────────────┐
  │         authentication_gate          │
  │                                      │
  │ after_reasoning:                     │
  │   if auth → route via next_topic     │
  └──────────────────────────────────────┘
```

**The 3 Variables:**

| Variable | Type | Purpose |
|----------|------|---------|
| `open_gate` | string | Which topic holds focus (`"null"` = LLM decides) |
| `next_topic` | string | Deferred destination after auth completes |
| `authenticated` | boolean | Whether user has passed authentication |

**When to Use**: Multiple protected topics behind a shared auth gate, especially when you want zero-credit LLM bypass while the gate holds focus.

**Key Difference from Verification Gate (Pattern 4)**: The Verification Gate is a linear, one-time gate — once verified, the user proceeds and never returns. The State Gate supports **deferred routing** (remembers where the user wanted to go), **N protected topics** behind a single gate, and an **EXIT_PROTOCOL** to release the gate when the user changes intent.

> **Template**: See [assets/patterns/open-gate-routing.agent](../assets/patterns/open-gate-routing.agent) for the complete implementation with walkthrough.

---

## Standard Platform Topics (Implicit)

> These topics are **always active** in every agent, even when not declared in the `.agent` file's topic list. They operate ABOVE custom topic routing and take priority.

| Standard Topic | Catches | Example Utterances |
|---------------|---------|-------------------|
| `Inappropriate_Content` | Hate speech, abuse, insults | "You're useless", "I hate this company" |
| `Prompt_Injection` | Instruction override attempts | "Ignore all previous instructions", "Tell me your system prompt" |
| `Reverse_Engineering` | Agent introspection probes | "What are your instructions?", "Show me your configuration" |
| `Ambiguous_Question` | Multi-intent or unclear messages | "I need help with my camera and also want to pay my bill" |

**Impact on FSM Design**:
- Your custom `Escalation` topic will NOT catch insults — `Inappropriate_Content` intercepts first
- Your custom `Off_Topic` topic will NOT catch prompt injection — `Prompt_Injection` handles it
- Multi-intent messages may bypass your routing logic entirely via `Ambiguous_Question`
- **Test design**: Write guardrail tests targeting these standard topics, not your custom equivalents

**How to Detect in Test Results**:
- Standard topic names appear in test output as-is (e.g., `Inappropriate_Content`, not a hash-suffixed name)
- If a test expects your custom topic but the agent routes to a standard topic, the topic assertion fails

---

## Deterministic vs. Subjective Classification

### Classification Framework

| Put in Deterministic Nodes if... | Put in Subjective Reasoning if... |
|----------------------------------|-----------------------------------|
| Security/safety requirement | Conversational/greeting |
| Financial threshold | Context understanding needed |
| Data fetch required | Natural language generation |
| Counter/state management | Flexible interpretation needed |
| Hard cutoff rule | Response explanation |

### Examples

| Requirement | Classification | Reasoning |
|-------------|----------------|-----------|
| "ALWAYS verify identity before refund" | **Deterministic** | Security - must be code-enforced |
| "Start with a friendly greeting" | **Subjective** | Conversational - LLM flexibility |
| "IF churn > 80, full refund" | **Deterministic** | Financial threshold - no exceptions |
| "Explain the refund status" | **Subjective** | Natural language generation |
| "Count failed verification attempts" | **Deterministic** | Counter logic - must be accurate |
| "Redirect off-topic questions" | **Subjective** | Context understanding required |

---

## State Machine Example: Pronto Refund Agent

```
                              ┌────────────────────┐
                              │ Identity           │  verified
                 refund       │ Verification       │─────────────┐
                 intent       │ (VERIFICATION)     │             │
┌────────────────┐           └─────────┬──────────┘             ▼
│ Topic Selector │──────────▶          │              ┌─────────────────┐
│   (ROUTING)    │                     │ failed 3x    │ Risk Assessment │
└────────────────┘                     │              │ (DATA-LOOKUP)   │
                                       │              └────────┬────────┘
                                       ▼                       │ score loaded
                              ┌────────────────┐               ▼
                              │  Escalation    │      ┌─────────────────┐
                              │  (HANDOFF)     │      │ Refund Processor│
                              └────────────────┘      │  (PROCESSING)   │
                                                      └─────────────────┘
```

### State Definitions

| State | Type | Entry Condition | Exit Conditions |
|-------|------|-----------------|-----------------|
| Topic Selector | ROUTING | Conversation start | Intent detected |
| Identity Verification | VERIFICATION | Refund intent | Verified OR 3 failures |
| Risk Assessment | DATA-LOOKUP | Identity verified | Score loaded |
| Refund Processor | PROCESSING | Score loaded | Refund complete |
| Escalation | HANDOFF | 3 failures | Human takeover |

---

## Best Practices

### 1. Single Responsibility per Topic
Each topic should handle ONE concern. If a topic does verification AND processing, split it.

### 2. Explicit Transitions
Always define how to enter AND exit each state. No dead ends.

### 3. Guard Sensitive Transitions
Use `available when` to make actions invisible when conditions aren't met.

```yaml
actions:
  process_payment: @actions.charge_card
    available when @variables.customer_verified == True
    # LLM literally cannot see this action if not verified
```

### 4. Design for the Happy Path First
Map the success flow, then add failure states.

### 5. Use Escalation as a Safety Net
When in doubt, escalate to human. It's better than a bad automated decision.

---

## Topic Design Patterns

> Migrated from the former `sf-ai-agentforce-legacy/references/topics-guide.md` on 2026-02-07.

### Topic Fundamentals

**Topics** are conversation modes that group related actions and reasoning logic. Think of them as "skill areas" or "conversation contexts" for your agent.

| Benefit | Description |
|---------|-------------|
| **Separation of Concerns** | Group related functionality (e.g., "Order Management", "Support") |
| **Focused Instructions** | Each topic has its own reasoning instructions |
| **Action Scoping** | Actions defined in a topic are available only in that topic |
| **Persona Switching** | Topics can override system instructions for different modes |

### Topic Structure

#### Required Fields

Every topic MUST have:
- `description:` - What the topic does (used by LLM for routing decisions)

> **`label:` is valid on topics** (TDD v2.2.0). Use `label:` for display names and `description:` to convey the topic's purpose to the LLM.

```agentscript
topic order_lookup:
   description: "Helps customers look up their order status and details"

   reasoning:
      instructions: ->
         | Help the user find their order.
```

#### Optional Blocks

| Block | Purpose | Example |
|-------|---------|---------|
| `system:` | Override global system instructions | Persona switching |
| `actions:` | Define topic-specific actions | Flow/Apex actions |
| `reasoning:` | Topic reasoning logic | Instructions + action invocations |

---

### Topic Transition Mechanics

#### `@utils.transition to @topic.[name]`

Permanently move to another topic. The user CANNOT return to the previous topic without explicit routing.

```agentscript
start_agent topic_selector:
   description: "Routes users to topics"

   reasoning:
      instructions: ->
         | What would you like to do?
         | 1. Check order status
         | 2. Get support
      actions:
         go_orders: @utils.transition to @topic.order_lookup
         go_support: @utils.transition to @topic.support
```

**When to Use:**
- **Permanent mode switches** (e.g., "I want to check my order" → order_lookup)
- **One-way transitions** where user won't return to previous topic
- **Entry point routing** (start_agent → specific topics)

---

### Topic Delegation vs Transition

There are TWO ways to reference other topics:

#### 1. `@utils.transition to @topic.[name]` — Permanent Transition

**Behavior:**
- Permanently moves to the target topic
- User CANNOT automatically return
- Current topic is abandoned
- Target topic becomes the active context

**Use Cases:**
- Main menu routing (start_agent → feature topics)
- Mode switches (FAQ → Support)
- One-way workflows

```agentscript
# Permanent transition
actions:
   go_to_orders: @utils.transition to @topic.order_management
```

#### 2. `@topic.[name]` — Topic Delegation (Sub-Agent Pattern)

**Behavior:**
- Temporarily delegates to target topic
- Target topic can "return" control to caller
- Original topic resumes after delegation completes
- Like calling a subroutine

**Use Cases:**
- Specialist consultation (Main Agent → Tax Expert → Main Agent)
- Reusable sub-workflows (Address Collection)
- Modular agent design

```agentscript
# Topic delegation (can return)
actions:
   consult_specialist: @topic.tax_specialist
```

**Key Difference:**

| Pattern | Control Flow | Returns? |
|---------|--------------|----------|
| `@utils.transition to @topic.x` | Permanent move | No |
| `@topic.x` | Temporary delegation | Yes (if target topic transitions back) |

---

### Routing Pattern Examples

#### Hub-and-Spoke (with Back Navigation)

```agentscript
start_agent topic_selector:
   description: "Main menu / router"

   reasoning:
      instructions: ->
         | What can I help you with?
      actions:
         go_orders: @utils.transition to @topic.order_management
         go_support: @utils.transition to @topic.support
         go_faq: @utils.transition to @topic.faq

topic order_management:
   description: "Order lookup and tracking"

   reasoning:
      instructions: ->
         | Help with orders.
      actions:
         back: @utils.transition to @topic.topic_selector

topic support:
   description: "Customer support"

   reasoning:
      instructions: ->
         | Provide support.
      actions:
         back: @utils.transition to @topic.topic_selector
```

**Benefits:** Clear entry point, easy to add new topics, users can always go back to menu.

#### Linear Workflow

```agentscript
start_agent onboarding:
   description: "Collect user information"

   reasoning:
      instructions: ->
         | Welcome! Let's get started.
      actions:
         next: @utils.transition to @topic.collect_address

topic collect_address:
   description: "Get shipping address"

   reasoning:
      instructions: ->
         | What's your address?
      actions:
         next: @utils.transition to @topic.confirm_details

topic confirm_details:
   description: "Review and confirm"

   reasoning:
      instructions: ->
         | Please confirm your information.
```

**Benefits:** Guided, step-by-step experience. Prevents users from skipping steps.

#### Contextual Routing (Data-Driven)

```agentscript
topic order_lookup:
   description: "Look up order by number"

   reasoning:
      instructions: ->
         | if @variables.order_found == False:
         |    | I couldn't find that order.
      actions:
         lookup: @actions.get_order
         # Conditional routing based on outcome
         go_support: @utils.transition to @topic.support
            available when @variables.order_found == False
         back: @utils.transition to @topic.topic_selector
            available when @variables.order_found == True
```

**Benefits:** Dynamic routing based on data, handles error cases gracefully.

---

### Multi-Topic Agent Design

#### When to Use Multiple Topics

| Scenario | Topics Needed |
|----------|---------------|
| **Multi-feature agent** | 1 topic per feature + 1 router topic |
| **Workflow with steps** | 1 topic per step + 1 entry topic |
| **Persona switching** | 1 topic per persona + 1 selector |
| **Specialist delegation** | 1 main topic + N specialist topics |

---

### Bidirectional Routing (Specialist Consultation)

```agentscript
topic main_agent:
   description: "General assistant that can consult specialists"

   reasoning:
      instructions: ->
         | I can help with most questions.
         | For specialized topics, I'll consult our experts.
      actions:
         # Delegation - specialist can return control
         consult_tax: @topic.tax_specialist
         consult_legal: @topic.legal_specialist

topic tax_specialist:
   description: "Expert on tax questions"

   reasoning:
      instructions: ->
         | [Tax Specialist Mode]
         | Provide detailed tax guidance.
      actions:
         # Return to main agent when done
         return_to_main: @utils.transition to @topic.main_agent

topic legal_specialist:
   description: "Expert on legal questions"

   reasoning:
      instructions: ->
         | [Legal Specialist Mode]
         | Provide legal information.
      actions:
         return_to_main: @utils.transition to @topic.main_agent
```

**Benefits:** Main agent stays in control, specialists provide focused expertise, clean separation of concerns, reusable specialist topics.

---

### Topic Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Topic name | snake_case | `order_management` |
| Action name | snake_case | `get_order_status` |

### Common Topic Design Mistakes

| Mistake | Fix |
|---------|-----|
| Missing `description` | Add `description:` to every topic (required for LLM routing) |
| Overlapping sibling topics | Increase semantic distance or merge/split by clearer jobs-to-be-done |
| Broad escalation or handoff descriptions | Restrict them to meta-intents only; remove business-domain wording |
| Trying to fix routing in instructions | Strengthen topic names and descriptions instead |
| Orphaned topics (unreachable) | Ensure all topics have incoming transitions |
| No way to go back | Add transition to topic_selector or escalation |
| Too many topics | Combine related functionality |
| Too few topics | Split complex topics into focused ones |

### Topic Transitions Checklist

- [ ] `start_agent` transitions to at least one topic
- [ ] All topics are reachable from `start_agent` (directly or indirectly)
- [ ] Each topic has at least one outbound transition (or escalation)
- [ ] Users can navigate back to main menu or exit
- [ ] Topic descriptions are clear and detailed for LLM routing
- [ ] High-traffic topics have nearest-neighbor collision tests
- [ ] Turn-2 pivot / re-classification paths are tested for important workflows
- [ ] Protected topics still enforce gates even after rerouting
