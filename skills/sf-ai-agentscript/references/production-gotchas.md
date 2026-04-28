<!-- Parent: sf-ai-agentscript/SKILL.md -->

# PRODUCTION GOTCHAS: Billing, Determinism & Performance

## Credit Consumption Table

> **Key insight**: Framework operations are FREE. Only actions that invoke external services consume credits.

| Operation | Credits | Notes |
|-----------|---------|-------|
| `@utils.transition` | FREE | Framework navigation |
| `@utils.setVariables` | FREE | Framework state management |
| `@utils.escalate` | FREE | Framework escalation |
| `if`/`else` control flow | FREE | Deterministic resolution |
| `before_reasoning` | FREE | Deterministic pre-processing (see note below) |
| `after_reasoning` | FREE | Deterministic post-processing (see note below) |
| `reasoning` (LLM turn) | FREE | LLM reasoning itself is not billed |
| Prompt Templates | 2-16 | Per invocation (varies by complexity) |
| Flow actions | 20 | Per action execution |
| Apex actions | 20 | Per action execution |
| Any other action | 20 | Per action execution |

> **✅ Lifecycle Hooks**: The `before_reasoning:` and `after_reasoning:` lifecycle hooks are validated. Content goes **directly** under the block (no `instructions:` wrapper). See "Lifecycle Hooks" section below for correct syntax.

**Cost Optimization Pattern**: Fetch data once in `before_reasoning:`, cache in variables, reuse across topics.

## Lifecycle Hooks: `before_reasoning:` and `after_reasoning:`

```yaml
topic main:
   description: "Topic with lifecycle hooks"

   # BEFORE: Runs deterministically BEFORE LLM sees instructions
   before_reasoning:
      # Content goes DIRECTLY here (NO instructions: wrapper!)
      set @variables.pre_processed = True
      set @variables.customer_tier = "gold"

   # LLM reasoning phase
   reasoning:
      instructions: ->
         | Customer tier: {!@variables.customer_tier}
         | How can I help you today?

   # AFTER: Runs deterministically AFTER LLM finishes reasoning
   after_reasoning:
      # Content goes DIRECTLY here (NO instructions: wrapper!)
      set @variables.interaction_logged = True
      if @variables.needs_audit == True:
         set @variables.audit_flag = True
```

**Key Points:**
- Content goes **directly** under `before_reasoning:` / `after_reasoning:` (NO `instructions:` wrapper)
- Reliable primitives: `set`, `if`/`else`, `transition to`. `run` has inconsistent runtime behavior across bundle types — use it in `reasoning.actions:` or `instructions: ->` instead
- `before_reasoning:` is FREE (no credit cost) - use for data prep
- `after_reasoning:` is FREE (no credit cost) - use for logging, cleanup
- `transition to` works in `after_reasoning:` — but if a topic transitions mid-reasoning, the original topic's `after_reasoning:` does NOT run

**❌ WRONG Syntax (causes compile error):**
```yaml
before_reasoning:
   instructions: ->      # ❌ NO! Don't wrap with instructions:
      set @variables.x = True
```

**✅ CORRECT Syntax:**
```yaml
before_reasoning:
   set @variables.x = True   # ✅ Direct content under the block
```

## Supervision vs Handoff (Clarified Terminology)

| Term | Syntax | Behavior | Use When |
|------|--------|----------|----------|
| **Handoff** | `@utils.transition to @topic.X` | Control transfers completely, child generates final response | Checkout, escalation, terminal states |
| **Supervision** | `@topic.X` (as action reference) | Parent orchestrates, child returns, parent synthesizes | Expert consultation, sub-tasks |

```yaml
# HANDOFF - child topic takes over completely:
checkout: @utils.transition to @topic.order_checkout
   description: "Proceed to checkout"
# → @topic.order_checkout generates the user-facing response

# SUPERVISION - parent remains in control:
get_advice: @topic.product_expert
   description: "Consult product expert"
# → @topic.product_expert returns, parent topic synthesizes final response
```

**KNOWN BUG**: Adding ANY new action in Canvas view may inadvertently change Supervision references to Handoff transitions.

## Action Output Flags for Zero-Hallucination Routing

> **Key Pattern for Determinism**: Control what the LLM can see and say.

When defining actions in Agentforce Assets, use these output flags carefully:

| Flag | Effect | Use When |
|------|--------|----------|
| `filter_from_agent: True` | Hide from direct customer display (GA standard) | Output should stay hidden and does **not** need `is_used_by_planner` on the same field |
| `is_displayable: False` | Hide from direct customer display (compile-valid alias) | Preferred hide-from-user flag when the planner still needs the same prompt output field |
| `is_used_by_planner: True` | Planner can reason about the value | Decision-making, routing, response synthesis |

> ⚠️ Do **not** combine `filter_from_agent` and `is_used_by_planner` on the same output field. That combination is a known blocking parser/runtime conflict.

**Zero-Hallucination Intent Classification Pattern:**
```yaml
# In Agentforce Assets - Action Definition outputs:
outputs:
   intent_classification: string
      is_displayable: False     # Hide from direct display
      is_used_by_planner: True  # Planner can use for routing decisions

# In Agent Script - planner routes but the raw label is never shown directly:
topic intent_router:
   reasoning:
      instructions: ->
         run @actions.classify_intent
         set @variables.intent = @outputs.intent_classification

         if @variables.intent == "refund":
            transition to @topic.refunds
         if @variables.intent == "order_status":
            transition to @topic.orders
```

## `is_displayable: True` on Prompt Template Outputs

> **Production impact**: Agent returns blank/empty responses when prompt template action outputs have `is_displayable: True` set.

**The Problem**: Setting `is_displayable: True` (or toggling "Show in conversation" in the UI) on a prompt template action's output causes the platform to attempt direct rendering of the raw output. The rendering pipeline does not handle prompt template output format correctly, resulting in a blank response to the user — even though the trace shows the prompt template executed successfully.

```yaml
# ❌ WRONG — causes blank response for prompt template actions
outputs:
   response_text: string
      is_displayable: True     # Platform tries to render raw output → blank

# ✅ CORRECT — let the reasoner synthesize the output
outputs:
   response_text: string
      is_displayable: False    # Hide raw output from direct display
      is_used_by_planner: True # LLM reads and synthesizes into response
```

**Key Points:**
- This only affects prompt template actions (`prompt://` / `generatePromptResponse://` targets)
- `is_displayable: True` works correctly on non-prompt actions (Flow, Apex) where the output is a simple string
- The safest prompt-template default is `is_displayable: False` + `is_used_by_planner: True`
- `filter_from_agent: True` is the GA-standard hide-from-user flag, but on prompt outputs it is a worse fit when the planner also needs the value because `filter_from_agent` and `is_used_by_planner` cannot be combined on the same field in this runtime
- The reasoner naturally incorporates planner-visible outputs into its response — explicit display is unnecessary

**If the prompt action ran but the response is still missing, check these next:**
1. `is_displayable` is not `True`
2. `is_used_by_planner` is `True` on the output that should influence the reply
3. You did **not** combine `filter_from_agent` with `is_used_by_planner` on the same field
4. The action output is not a structured wrapper that still needs field extraction before deterministic use

> **Cross-reference**: See [known-issues.md](known-issues.md#issue-34) Issue 34.

---

## Raw `user_input` String Matching Is a Weak Deterministic Pattern

> **Production impact**: Substring checks on the last utterance look simple, but they are brittle for deterministic routing, cancellation handling, and revision detection.

**The Problem**: Branches such as `if @system_variables.user_input contains "never mind":` treat raw user text as if it were a normalized intent signal. That works inconsistently for real conversations because phrasing varies, punctuation varies, and the deterministic layer is not a robust intent classifier.

```yaml
# ❌ BRITTLE — raw utterance parsing as deterministic control flow
if @system_variables.user_input contains "never mind":
   transition to @topic.cancel_request

# ✅ SAFER — normalize the utterance first, then branch on explicit state
run @actions.classify_user_intent
   with utterance = @system_variables.user_input
   set @variables.cancel_requested = @outputs.cancel_requested

if @variables.cancel_requested == True:
   transition to @topic.cancel_request
```

**Use raw string checks only for light heuristics.** If a branch must deterministically gate behavior, normalize it into:
- a boolean (`cancel_requested`, `is_valid_url`)
- an enum/string (`intent = "cancel"`)
- or a pre-validated scalar returned by Flow/Apex

---

## Output Access Follows the Output Schema

> **Production impact**: Deterministic comparisons fail when a target returns a wrapper object and the script treats `@outputs.X` like a plain scalar.

**The Problem**: Some actions return structured outputs. In those cases, `@outputs.output` is an object envelope, not the final string/boolean you want to compare. The right accessor depends on the declared schema.

```yaml
# ❌ WRONG — assumes object output is already a boolean
set @variables.is_after_hours = @outputs.output

# ✅ CORRECT — access a concrete field only if the schema exposes it
set @variables.is_after_hours = @outputs.output.value
```

**Guidance:**
- If the action output is declared as `string`, `number`, or `boolean`, direct assignment is fine.
- If the output is declared as `object` or another structured type, inspect the contract before you branch on it.
- `.value` is a common wrapper field, but it is **not universal** — only use it when that field actually exists in the output schema.
- For deterministic branches, the safest design is to flatten the target output in Flow/Apex so Agent Script receives an explicit scalar such as `is_after_hours: boolean`.

---

## Action I/O Metadata Properties

> **Complete reference** for all metadata properties available on action definitions, inputs, and outputs.

**Action-Level Properties:**

| Property | Type | Effect |
|----------|------|--------|
| `label` | String | Display name in UI |
| `description` | String | LLM reads this for decision-making |
| `require_user_confirmation` | Boolean | Request user confirmation before execution (compiles; runtime no-op per Issue 6) |
| `include_in_progress_indicator` | Boolean | Show spinner during execution |
| `progress_indicator_message` | String | Custom spinner text |

**Input Properties:**

| Property | Type | Effect |
|----------|------|--------|
| `description` | String | Explains parameter to LLM |
| `label` | String | Display name in UI |
| `is_required` | Boolean | Marks input as mandatory for LLM |
| `is_user_input` | Boolean | LLM extracts value from conversation |
| `complex_data_type_name` | String | Lightning type mapping |

**Output Properties:**

| Property | Type | Effect |
|----------|------|--------|
| `description` | String | Explains output to LLM |
| `label` | String | Display name in UI |
| `filter_from_agent` | Boolean | `True` = hide from user display (GA standard) |
| `is_displayable` | Boolean | `False` = hide from user (compile-valid alias). Prefer this on prompt outputs when the planner still needs the value |
| `is_used_by_planner` | Boolean | `True` = LLM can reason about value |
| `developer_name` | String | Overrides the parameter's developer name |
| `complex_data_type_name` | String | Lightning type mapping |

> **Cross-reference**: `filter_from_agent: True` is the GA standard name. `is_displayable: False` is a compile-valid alias.

> ⚠️ For prompt-template outputs specifically, prefer `is_displayable: False` when the planner still needs the output. `filter_from_agent` is not a safe drop-in replacement there if you also need `is_used_by_planner`, because those two flags conflict on the same field.

**User Input Pattern** (`is_user_input: True`):
```yaml
inputs:
   customer_name: string
      description: "Customer's full name"
      is_user_input: True    # LLM pulls from what user already said
      is_required: True      # Must have a value before action executes
```

## Action Chaining with `run` Keyword

> **Known quirk**: Parent action may complain about inputs needed by chained action - this is expected.

```yaml
process_order: @actions.create_order
   with customer_id = @variables.customer_id
   run @actions.send_confirmation        # Chains after create_order completes
   set @variables.order_id = @outputs.id
```

**KNOWN BUG**: Chained actions with Prompt Templates don't properly map inputs using `Input:Query` format.

> **📖 For prompt template action definitions, input binding syntax, and grounded data patterns**, see [references/action-prompt-templates.md](../references/action-prompt-templates.md).

## Latch Variable Pattern for Topic Re-entry

> **Problem**: Topic selector doesn't properly re-evaluate after user provides missing input.

**Solution**: Use a "latch" variable to force re-entry:

```yaml
variables:
   verification_in_progress: mutable boolean = False

start_agent topic_selector:
   reasoning:
      instructions: ->
         if @variables.verification_in_progress == True:
            transition to @topic.verification
         | How can I help you today?
      actions:
         start_verify: @topic.verification
            description: "Start identity verification"
            set @variables.verification_in_progress = True

topic verification:
   reasoning:
      instructions: ->
         | Please provide your email to verify your identity.
      actions:
         verify: @actions.verify_identity
            with email = ...
            set @variables.verified = @outputs.success
            set @variables.verification_in_progress = False
```

## Loop Protection Guardrail

> Agent Scripts have a built-in guardrail that limits iterations to approximately **3-4 loops** before breaking out and returning to the Topic Selector.

**Best Practice**: Map out your execution paths and test for unintended circular references between topics.

## Token & Size Limits

| Limit Type | Value | Notes |
|------------|-------|-------|
| Max response size | 1,048,576 bytes (1MB) | Per agent response |
| Plan trace limit (Frontend) | 1M characters | For debugging UI |
| Transformed plan trace (Backend) | 32k tokens | Internal processing |
| Active/Committed Agents per org | 100 max | Org limit |

## Progress Indicators

```yaml
actions:
   fetch_data: @actions.get_customer_data
      description: "Fetch customer information"
      include_in_progress_indicator: True
      progress_indicator_message: "Fetching your account details..."
```

## VS Code Pull/Push NOT Supported

```bash
# ❌ ERROR when using source tracking:
Failed to retrieve components using source tracking:
[SfError [UnsupportedBundleTypeError]: Unsupported Bundle Type: AiAuthoringBundle

# ✅ WORKAROUND - Use CLI directly:
sf project retrieve start -m AiAuthoringBundle:MyAgent
sf agent publish authoring-bundle --api-name MyAgent -o TARGET_ORG
```

## Reserved `@InvocableVariable` Keywords

> **Validated March 2026**: Certain common words cannot be used as `@InvocableVariable` names in Apex classes called by Agent Script. Using them causes "SyntaxError: Unexpected '{keyword}'" during agent script compilation.

**Reserved names (cannot use as `@InvocableVariable`):**

| Reserved Name | Workaround | Example |
|---------------|------------|---------|
| `model` | `vehicle_model`, `data_model`, `model_name` | `@InvocableVariable public String vehicle_model;` |
| `description` | `issue_description`, `desc_text`, `description_field` | `@InvocableVariable public String issue_description;` |
| `label` | `label_text`, `display_label`, `label_field` | `@InvocableVariable public String label_text;` |

**How it manifests:**
- Apex compiles and deploys successfully (these are valid Apex identifiers)
- Error only appears when the Agent Script compiler processes the action's I/O schema
- Error message: `SyntaxError: Unexpected 'model'` (or `description`, `label`)
- Fix: Rename the `@InvocableVariable` in Apex, redeploy, then republish the agent

> **Cross-reference**: These same words are also reserved as Agent Script variable/field names. See [SKILL.md](../SKILL.md) reserved field names section.

## Boolean-to-String Coercion Hazard

> **Production impact**: Non-deterministic "Something went wrong" (SWW) errors scattered across turns. Extremely difficult to diagnose because failures are intermittent.

**The Problem**: When a Flow or Apex action outputs a `Boolean` value and you capture it into a `mutable string` variable, then compare with `== "true"`, the coercion is non-deterministic. Some turns coerce `True` -> `"true"` correctly; others produce `"True"`, `"1"`, or empty string — causing silent routing failures.

```yaml
# ❌ HAZARDOUS — Boolean output into string variable
variables:
   verified: mutable string = "false"

actions:
   verify: @actions.verify_user
      target: "flow://Verify_User"
      outputs:
         verified_result: boolean   # Flow outputs Boolean

# In reasoning:
set @variables.verified = @outputs.verified_result    # Boolean -> string coercion
if @variables.verified == "true":                     # Non-deterministic match!
   transition to @topic.protected_area
```

**Fix Option A** (preferred): Use `mutable boolean` and compare with `== True`:
```yaml
variables:
   verified: mutable boolean = False

# In reasoning:
set @variables.verified = @outputs.verified_result    # Boolean -> boolean, no coercion
if @variables.verified == True:                       # Deterministic!
   transition to @topic.protected_area
```

**Fix Option B**: Have the Flow/Apex output an explicit `String` ("true"/"false") instead of Boolean:
```yaml
# Flow/Apex outputs String "true" or "false" explicitly
outputs:
   verified_result: string   # Already a string, no coercion

# In reasoning:
set @variables.verified = @outputs.verified_result    # String -> string
if @variables.verified == "true":                     # Deterministic!
```

**Production validation**: Switching from Boolean->String coercion to explicit String output dropped SWW errors from scattered (multiple per session) to 1/61 turns (on an unrelated external callout).

---

## Escalation Fallback Loop

> **Production impact**: Agent enters infinite escalation loop when no human agents are available — user sees repeated "Connecting you..." messages until the 3-4 loop guardrail kicks in.

**The Problem**: `@utils.escalate` does not return a success/failure status. When no human agents are available (outside business hours, no Omni-Channel agents online), the escalation silently fails and the conversation re-enters the escalation topic, triggering the same logic again.

**Fix**: Use a latch variable in `before_reasoning:` to detect re-entry and route to a fallback:

```yaml
variables:
   escalation_attempted: mutable boolean = False

topic escalation:
   description: "Escalate to human agent"

   before_reasoning:
      if @variables.escalation_attempted == True:
         transition to @topic.leave_message
      set @variables.escalation_attempted = True

   reasoning:
      instructions: ->
         | Let me connect you with a support specialist.
      actions:
         handoff: @utils.escalate
            description: "Transfer to human agent"
```

**Key Points:**
- The `before_reasoning:` check is FREE (no credit cost) and runs deterministically before the LLM
- Always provide a graceful fallback topic (leave message, callback, self-service links)
- This pattern also prevents credit waste — each failed escalation loop costs LLM reasoning credits

> **Cross-reference**: See [known-issues.md](known-issues.md#issue-31) Issue 31. See [fsm-architecture.md](fsm-architecture.md) § Pattern 5 — Escalation with Availability Check.

---

## Language Block Quirks

- Hebrew and Indonesian appear **twice** in the language dropdown
- Selecting from the second set causes save errors
- Use `adaptive_response_allowed: True` for automatic language adaptation
