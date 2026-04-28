<!-- Parent: sf-ai-agentscript/SKILL.md -->
# Instruction Resolution Guide

> One Pass. Top to Bottom. Before the LLM Sees Anything.

---

## The Three Phases

Agent Script instructions resolve in a predictable order. Understanding this flow gives you precise control over what the LLM sees and when actions execute.

| Phase | Icon | Name | Description |
|-------|------|------|-------------|
| 1 | ▶ | **Pre-LLM Setup** | Instructions resolve line-by-line, deterministically |
| 2 | ⚙ | **LLM Reasoning** | LLM sees only resolved text and available actions |
| 3 | ↻ | **Post-Action Loop** | After action completes, topic loops with updated variables |

---

## Phase 1: Pre-LLM Resolution

> Everything resolves top-to-bottom BEFORE the LLM processes them.

### What Happens

| Step | Description |
|------|-------------|
| **Conditions evaluate** | `if/else` logic evaluates and prunes paths |
| **Actions execute** | `run @actions.X` executes immediately |
| **Templates resolve** | Template syntax resolves to actual values |
| **Transitions short-circuit** | `transition to` can exit the topic immediately |

> ⚠️ **`run @actions.X` resolution scope**: The `run` directive resolves only against topic-level action definitions that declare a real `target:` field (`flow://`, `apex://`, `prompt://`, etc.). It does NOT work for reasoning-level utilities like `@utils.setVariables`, and it is also the wrong tool for topic-level utilities / delegations such as `@utils.transition` or `@topic.X`. If you need deterministic non-target behavior, use direct `set` / `transition to`. If you need utility-style behavior chosen from context, expose it in `reasoning.actions:` and let the LLM invoke it.

### Example

```yaml
topic refund_request:
  description: "Handle refund requests"
  reasoning:
    instructions: ->
      # --- PRE-LLM: These resolve BEFORE the LLM sees anything ---

      # Security gate - check attempt limit
      if @variables.attempt_count >= 3:
        transition to @topic.escalation

      # Load data deterministically
      run @actions.get_churn_score
        with customer_id = @variables.customer_id
        set @variables.churn_score = @outputs.score

      # Increment counter
      set @variables.attempt_count = @variables.attempt_count + 1

      # --- LLM INSTRUCTIONS: Only this text reaches the LLM ---
      | Customer churn score: {!@variables.churn_score}

      if @variables.churn_score >= 80:
        | Offer a full cash refund to retain this customer.
      else:
        | Offer a $10 credit as a goodwill gesture.
```

### Execution Timeline

```
┌─────────────────────────────────────────────────────────────────┐
│ ▶ PRE-LLM                                        [LINE-BY-LINE] │
├─────────────────────────────────────────────────────────────────┤
│ ● Message Received                                       ~10ms  │
│ ● Instructions Resolve                               ~50-500ms  │
│ ● Templates Hydrate                                       ~5ms  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 2: LLM Processing

> The LLM receives clean, final instructions with all values populated.

### What the LLM Sees

The LLM **never** sees your conditionals - only the resolved result.

**Your code:**
```yaml
instructions: ->
  | Customer churn score: {!@variables.churn_score}

  if @variables.churn_score >= 80:
    | Offer a full cash refund to retain this customer.
  else:
    | Offer a $10 credit as a goodwill gesture.
```

**What the LLM actually sees (if churn_score = 85):**
```
Customer churn score: 85
Offer a full cash refund to retain this customer.
```

### Action Visibility

The `available when` clause is also evaluated deterministically:

```yaml
actions:
  process_refund: @actions.process_refund
    description: "Issue the refund"
    available when @variables.is_verified == True
```

If `is_verified` is `False`, the LLM **never sees** `process_refund` as an option.

---

## Phase 3: Post-Action Loop

> When the LLM invokes an action, the topic loops back. Instructions resolve AGAIN.

### What Happens

| Step | Description |
|------|-------------|
| **Outputs stored** | LLM action completes, outputs stored in variables |
| **Re-resolve** | Topic instructions resolve again (same top-to-bottom pass) |
| **New conditions trigger** | Conditions can trigger based on new values |
| **Follow-up executes** | Deterministic follow-up actions run |

### The Loop Pattern

```
TURN 1: Initial Request
├─ User asks for refund
├─ Instructions resolve (refund_status is empty)
├─ LLM sees "Help the customer with their refund request"
├─ LLM calls process_refund action
└─ Action sets refund_status = "Approved"
         ↓ LOOP
TURN 2: After Action (Same Topic)
├─ Topic loops back
├─ Instructions resolve AGAIN
├─ Condition triggers: refund_status == "Approved"
├─ Deterministic action runs: create_crm_case
└─ Transition to success_confirmation
```

### Example: Deterministic Follow-Up

```yaml
topic refund_request:
  description: "Handle refund requests with deterministic follow-up"
  reasoning:
    instructions: ->
      # --- POST-ACTION CHECK: Did we just process a refund? ---
      # This block runs AGAIN after the LLM action completes!

      if @variables.refund_status == "Approved":
        # Deterministic follow-up - LLM cannot skip this!
        run @actions.create_crm_case
          with customer_id = @variables.customer_id
          with refund_amount = @variables.refund_amount
        transition to @topic.success_confirmation

      # --- PRE-LLM: Normal instruction flow ---
      | Customer churn score: {!@variables.churn_score}
      | Help the customer with their refund request.

    actions:
      process_refund: @actions.process_refund
        description: "Issue the refund"
        set @variables.refund_status = @outputs.status
        set @variables.refund_amount = @outputs.amount
```

> 💡 **KEY INSIGHT**: The post-action check pattern ensures business-critical follow-up actions ALWAYS execute. The LLM cannot "forget" or "decide not to" - it's code, not a suggestion.

---

## The Instruction Pattern Structure

### Recommended Order

```yaml
reasoning:
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

  actions:
    # LLM-selectable actions
    my_action: @actions.do_something
      set @variables.action_completed = True
```

### Why This Order Matters

1. **Post-action at TOP**: When the topic loops after action completion, the check triggers immediately
2. **Data loading next**: LLM needs current data to make decisions
3. **Instructions last**: LLM sees resolved values from data loading

---

## Execution Timeline Summary

| Phase | What Happens | Duration |
|-------|--------------|----------|
| **Pre-LLM** | Message received, instructions resolve, templates hydrate | ~60-515ms |
| **LLM** | LLM processes resolved instructions, decides on response/action | ~1-3s |
| **Post-Action** | Action executes, topic loops with updated variables | ~150-550ms |

---

## Common Patterns

### Pattern 1: Security Gate with Early Exit

```yaml
instructions: ->
  if @variables.failed_attempts >= 3:
    | Account locked due to too many attempts.
    transition to @topic.lockout  # Early exit - LLM never reasons

  | Please verify your identity.
```

### Pattern 2: Data-Dependent Instructions

```yaml
instructions: ->
  run @actions.get_account_tier
    set @variables.tier = @outputs.tier

  if @variables.tier == "Gold":
    | You're a Gold member! Enjoy priority support.
  if @variables.tier == "Silver":
    | Welcome back, Silver member.
  else:
    | Thanks for contacting support.
```

### Pattern 3: Action Chaining

```yaml
instructions: ->
  # Step 1 complete?
  if @variables.step1_done == True and @variables.step2_done == False:
    run @actions.step2
      set @variables.step2_done = True

  # Step 2 complete?
  if @variables.step2_done == True:
    transition to @topic.complete

  | Let's start with step 1.

actions:
  do_step1: @actions.step1
    set @variables.step1_done = True
```

---

## Syntax Patterns Reference

| Pattern | Purpose |
|---------|---------|
| `instructions: ->` | Arrow syntax enables inline expressions |
| `if @variables.x:` | Conditional - resolves BEFORE LLM |
| `run @actions.x` | Execute action during resolution |
| `set @var = @outputs.y` | Capture action output |
| Curly-bang: {!@variables.x} | Template injection into LLM text |
| `available when` | Control action visibility to LLM |
| `transition to @topic.x` | Deterministic topic change |

---

## Anti-Patterns to Avoid

### ❌ Data Load After LLM Text

```yaml
# WRONG - LLM sees empty values
instructions: ->
  | Customer name: {!@variables.name}  # name is empty!
  run @actions.load_customer
    set @variables.name = @outputs.name
```

### ✅ Correct Order

```yaml
# RIGHT - Load first, then reference
instructions: ->
  run @actions.load_customer
    set @variables.name = @outputs.name
  | Customer name: {!@variables.name}  # name is populated
```

### ❌ Post-Action Check at Bottom

```yaml
# WRONG - Never triggers because transition happens first
instructions: ->
  | Help with refund.
  transition to @topic.main  # Exits before check!

  if @variables.refund_done:
    run @actions.log_refund
```

### ✅ Post-Action Check at Top

```yaml
# RIGHT - Check first, then normal flow
instructions: ->
  if @variables.refund_done:
    run @actions.log_refund
    transition to @topic.success

  | Help with refund.
```

---

## What the LLM Actually Receives (Compilation Output)

> Validated via `sf agent preview` v1.1 trace data. See **sf-ai-agentforce-testing** Phase F for programmatic trace capture.

When a topic activates, the Agent Script DSL compiles into a **4-message prompt structure** sent to the LLM:

| # | Message Role | Content | Source |
|---|-------------|---------|--------|
| 1 | `system` | Protocol + resolved instructions | DSL compilation |
| 2 | `assistant` | Conversation history | Prior turns |
| 3 | `user` | Current utterance | User input |
| 4 | `system` | Late-injected context | `when` blocks + variables |

### System Message 1 — Main Prompt Structure

The first system message contains these sections IN ORDER:

1. **TOOL USAGE PROTOCOL** — How the LLM should invoke tools (JSON schema, parameter formatting)
2. **PROMPT INJECTION CRITERIA** — Instructions to detect and refuse injection attempts
3. **SAFETY GUARDRAILS** — Toxicity, PII, harmful content rules
4. **EQUALITY PRINCIPLES** — Non-discrimination guidelines
5. **LANGUAGE GUIDELINES** — Response language matching rules
6. **OFF-TOPIC RULES** — Topic boundary enforcement
7. **RESPONSE GUIDELINES** — Formatting, tone, length preferences
8. **PROHIBITED ACTIONS** — Actions the agent must never take
9. **Resolved `system.instructions`** — Your DSL `instructions: ->` block after one-pass resolution

The header varies by agent stage:
- **Topic Selector** → `"Topic Selector & Safety Router"`
- **Topic Agents** → `"Specialized Topic Agent"`

### System Message 4 — Late-Injected Context

Contains resolved `when` block instructions and customer context variables. This is where runtime context (`$Context.RoutableId`, custom variables) appears.

### Tool Definitions (`tools_sent[]`)

Actions compile into `tools_sent[]` as plain string names. Guardrails ALSO appear as tool names:
- Regular actions: `Get_Order_Status`, `Process_Refund`
- Guardrail tools: `Inappropriate_Content`, `Prompt_Injection`, `Reverse_Engineering`

**Per-iteration tool visibility changes** — tools shift between reasoning iterations based on topic transitions. Extract with:

```bash
jq '.steps[] | select(.stepType == "EnabledToolsStep") | .data.enabled_tools' trace.json
```

### Verifying Compilation Output

Use `jq` to extract the compiled prompt from trace files:

```bash
# Extract System Message 1 (your resolved instructions)
jq '.steps[] | select(.stepType == "LLMStep") | .data.prompt_content[0].content' trace.json

# Extract System Message 4 (late-injected context)
jq '.steps[] | select(.stepType == "LLMStep") | .data.prompt_content[3].content' trace.json

# Verify your instructions appear in the compiled output
jq -r '.steps[] | select(.stepType == "LLMStep") | .data.prompt_content[0].content' trace.json | grep -c "your instruction text"
```

---

## Key Takeaways

| # | Takeaway |
|---|----------|
| 1 | **One Pass Resolution** - Instructions resolve top-to-bottom BEFORE the LLM sees anything |
| 2 | **Inline Pattern** - Use `reasoning.instructions: ->` with inline conditionals |
| 3 | **LLM Sees Clean Text** - No if/else logic visible, no action calls visible |
| 4 | **Post-Action Loop** - Topic loops back after LLM action, instructions resolve AGAIN |
| 5 | **Deterministic Follow-Up** - Use post-action checks to guarantee critical actions |
| 6 | **4-Message Structure** - System (protocol) → Assistant (history) → User (utterance) → System (context) |
| 7 | **Guardrails as Tools** - Safety guardrails compile into both system prompt text AND tool definitions |
