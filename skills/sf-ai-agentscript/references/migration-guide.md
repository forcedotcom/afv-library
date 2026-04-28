<!-- Parent: sf-ai-agentscript/SKILL.md -->
# Migration Guide: Agentforce Builder UI → Agent Script DSL

> This guide maps every concept from the Agentforce Builder UI (Setup > Agents) to its Agent Script DSL equivalent. Use it when converting existing agents from the visual builder to code.

---

## Builder UI → Agent Script Mapping

| # | Builder UI Concept | Agent Script Equivalent | Notes |
|---|-------------------|------------------------|-------|
| 1 | Topic name | `topic my_topic_name:` | Must use snake_case, max 80 chars |
| 2 | Classification description | `description: "..."` on topic | Helps LLM decide when to enter topic |
| 3 | Scope / "What this topic can do" | `reasoning.instructions` + available `actions` | Combined: instructions tell LLM what to do, actions tell it what tools are available |
| 4 | Instructions (numbered text boxes) | `reasoning: instructions:` | Use `->` for logic/expressions, `\|` for literal text |
| 5 | Flow actions | `target: flow://FlowName` | Flow must be Autolaunched and Active |
| 6 | Apex actions | `target: apex://ClassName` | Class must have `@InvocableMethod` |
| 7 | Prompt Template actions | `target: prompt://TemplateName` | `generatePromptResponse://TemplateName` is also valid; template must exist in org |
| 8 | "Collect from user" input | Slot-fill `...` operator | `with query = ...` — LLM extracts from conversation |
| 9 | "Show/Hide in conversation" toggle | `filter_from_agent: True` | On action output definitions |
| 10 | "Require Confirmation" toggle | `require_user_confirmation: True` | On action definitions |
| 11 | Guard Conditions | `available when` clause | `available when @variables.verified == True` |

---

## What's New in Agent Script (No Builder UI Equivalent)

These capabilities exist ONLY in Agent Script — they cannot be configured through the Builder UI:

| # | Feature | Description | Example |
|---|---------|-------------|---------|
| 1 | `before_reasoning:` hook | Deterministic pre-processing before LLM sees instructions | Set variables, load data, enforce gates |
| 2 | `after_reasoning:` hook | Deterministic post-processing after LLM finishes | Logging, cleanup, audit flags |
| 3 | Linked variables | Read-only variables bound to session/context sources | `source: @MessagingSession.Id` |
| 4 | Per-topic `system.instructions` override | Different system prompts for different topics | Customize LLM persona per topic |
| 5 | Topic delegation (supervision) | Call a topic as a function — it returns to caller | `@topic.expert` in `reasoning.actions` |
| 6 | Conditional transitions with `if/else` | Deterministic routing based on variable state | `if @variables.risk >= 80: transition to @topic.escalation` |
| 7 | Template arithmetic | Expression evaluation in text templates | `{!@variables.x + 1}` |
| 8 | Post-action loop pattern | Topic re-resolves after action, enabling check-at-top pattern | Deterministic post-action routing |
| 9 | Latch variables | Force topic re-entry after user provides input | Workaround for topic selector limitations |
| 10 | Connection block | Multi-channel escalation routing (messaging, voice) | Service Agent channel-specific escalation |

---

## Known Migration Gaps Requiring Manual Review

| Gap | Why it matters | What to do |
|-----|----------------|------------|
| Legacy renderer / component override behavior | Rich rendering configured in legacy builders may not map 1:1 into Agent Script metadata | Re-test migrated actions in preview and runtime; be prepared for text fallback where the legacy surface used custom renderers |
| Prompt-template input names containing `Input:` | Raw Agent Script requires quoted parameter names with `:` | Quote every prompt-template input key explicitly, for example `"Input:customerId"` |
| Exact quoted field names | Some visual editors can rewrite specially quoted field names during round-trip save/reformat | Keep the raw `.agent` file in source control as the source of truth and diff after UI edits |
| Legacy schema annotations | Some builder-era annotations and rendering hints do not have a direct Agent Script property | Record the intent in docs/comments and validate the migrated action manually instead of assuming automatic parity |
| Separate topic/action YAML files | Builder-era or generated assets may suggest extra per-topic files | Consolidate topic logic and action definitions in the `.agent` file unless a separate packaging system explicitly requires otherwise |

**Practical migration rule:** if a migrated action compiles but behaves differently, verify three things separately: (1) raw `.agent` syntax, (2) builder round-trip formatting, and (3) runtime behavior in the actual target surface.

---

## Side-by-Side: Simple Topic

### Builder UI Configuration

```
Topic Name: Order Lookup
Classification: Handles customer order status inquiries

Instructions:
  1. Ask the customer for their order number
  2. Look up the order using the Get Order Details action
  3. Share the order status with the customer

Actions:
  - Get Order Details (Flow: Get_Order_Details)
    Input: order_id (Collect from user)
    Output: status, estimated_delivery
```

### Agent Script Equivalent

```yaml
topic order_lookup:
   description: "Handles customer order status inquiries"

   actions:
      get_order_details:
         description: "Retrieves order information by order ID"
         inputs:
            order_id: string
               description: "Customer's order number"
         outputs:
            status: string
               description: "Current order status"
            estimated_delivery: string
               description: "Estimated delivery date"
         target: "flow://Get_Order_Details"

   reasoning:
      instructions: ->
         # Post-action check (if order was already looked up)
         if @variables.order_status != "":
            | Your order status is: {!@variables.order_status}
            | Estimated delivery: {!@variables.estimated_delivery}

         | I can help you check your order status.
         | Please provide your order number.
      actions:
         lookup: @actions.get_order_details
            with order_id = ...
            set @variables.order_status = @outputs.status
            set @variables.estimated_delivery = @outputs.estimated_delivery
```

**Key differences in the Agent Script version:**
- Explicit action definition with typed inputs/outputs and target
- Post-action check pattern (at TOP of instructions) enables deterministic routing after the action completes
- Variable injection (`{!@variables.X}`) for dynamic text
- Slot-fill (`...`) replaces "Collect from user"

---

## Side-by-Side: Verification Gate

### Builder UI Configuration

```
Topic Name: Identity Verification
Classification: Verifies customer identity before accessing account

Instructions:
  1. Ask the customer for their email address
  2. Use the Verify Identity action to check their email
  3. If verified, route to the Account Management topic
  4. After 3 failed attempts, escalate to a human agent

Actions:
  - Verify Identity (Apex: VerifyIdentityAction)
    Input: email (Collect from user)
    Output: verified (boolean)
  - Go to Account Management (Topic Transition)
  - Escalate (Escalate to Agent)
```

### Agent Script Equivalent

```yaml
variables:
   customer_verified: mutable boolean = False
   failed_attempts: mutable number = 0

topic identity_verification:
   description: "Verifies customer identity before accessing account"

   actions:
      verify_identity:
         description: "Checks customer identity by email"
         inputs:
            email: string
               description: "Customer email address"
         outputs:
            verified: boolean
               description: "Whether identity was verified"
         target: "apex://VerifyIdentityAction"

   reasoning:
      instructions: ->
         # Gate: Too many failures → escalate
         if @variables.failed_attempts >= 3:
            | Too many failed attempts. Connecting you with a human agent.
            transition to @topic.escalation

         # Gate: Already verified → proceed
         if @variables.customer_verified == True:
            transition to @topic.account_management

         | Please provide your email address to verify your identity.
      actions:
         verify: @actions.verify_identity
            with email = ...
            set @variables.customer_verified = @outputs.verified
            if @outputs.verified == False:
               set @variables.failed_attempts = @variables.failed_attempts + 1
         go_account: @utils.transition to @topic.account_management
            description: "Proceed to account management"
            available when @variables.customer_verified == True
         escalate_now: @utils.escalate
            description: "Transfer to human agent"
```

**Key differences in the Agent Script version:**
- Deterministic gates at top of instructions (cannot be bypassed by LLM)
- Explicit failure counter with arithmetic
- `available when` guard ensures the "proceed" action is invisible until verified
- `@utils.escalate` replaces the UI "Escalate to Agent" button

---

## Migration Checklist

When converting a Builder UI agent to Agent Script:

- [ ] **Export current config**: Document all topics, instructions, and actions from the UI
- [ ] **Map each topic**: Use the mapping table above to translate concepts
- [ ] **Identify implicit logic**: Builder UI often has implicit routing — make it explicit with `if/else`
- [ ] **Add deterministic gates**: Convert any "instruction-based" security to `available when` guards
- [ ] **Define variables**: Builder UI hides state management — declare all needed variables explicitly
- [ ] **Set action targets**: Ensure all Flows/Apex classes are deployed with correct API names
- [ ] **Test incrementally**: Validate each topic independently before combining
- [ ] **Verify `default_agent_user`**: Must be a valid Einstein Agent User in the target org

---

## Common Migration Pitfalls

| Pitfall | Description | Fix |
|---------|-------------|-----|
| Missing deterministic logic | Builder UI relies on LLM to follow instructions; Agent Script should enforce with code | Add `if/else` gates and `available when` guards |
| Implicit routing | Builder UI auto-routes between topics; Agent Script needs explicit transitions | Add `@utils.transition` actions for each topic change |
| Action naming conflicts | Builder UI action names may conflict with reserved words | Rename to avoid `description`, `label`, `escalate` |
| Missing variable declarations | Builder UI manages state implicitly | Declare all mutable/linked variables explicitly |
| Wrong instruction syntax | Builder UI text → `\|` (pipe) syntax; conditional logic → `->` (arrow) syntax | Use arrow when you need `if`, `run`, `set`, or `transition` |
| Renderer assumptions survived migration only in prose | Legacy descriptions may still mention a specific renderer even when the metadata no longer guarantees it | Re-validate rendering behavior in the target surface; treat description text as guidance, not a rendering contract |
| Prompt template bindings copied literally without quotes | `Input:...` names parse differently in text DSL than in UI forms | Quote prompt-template input keys explicitly in `.agent` files |
| Exact field names changed after save/re-open | Builder round-trip formatting can alter edge-case quoted keys | Diff the raw `.agent` after editing in UI if your action depends on an exact quoted field name |

---

*Last updated: 2026-04-03*
