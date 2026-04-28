<!-- Parent: sf-ai-agentscript/SKILL.md -->
# Advanced Action Patterns

> Context-aware descriptions, instruction references, and binding strategies

**Related**: [SKILL.md — Action Chaining](../SKILL.md) | [action-prompt-templates.md](action-prompt-templates.md)

---

## 1. Context-Aware Action Descriptions

The same underlying action can have **different descriptions** across topics. This improves LLM action selection by matching the description to the user's expertise level or business context.

### Beginner vs. Advanced Mode

```agentscript
topic beginner_help:
  reasoning:
    actions:
      search_help: @actions.search_knowledge_base
        description: "Search for help articles"

topic advanced_help:
  reasoning:
    actions:
      search_help: @actions.search_knowledge_base
        description: "Execute knowledge base query with advanced filters (type, date range, tags). Returns paginated results with relevance scoring. Supports Boolean operators and wildcards."
```

**Result**: Beginner users see simple language; advanced users see technical capabilities.

### `available when` + Description Override

Combine conditional availability with contextual descriptions for stronger control:

```agentscript
topic business_hours:
  reasoning:
    actions:
      create_case: @actions.create_support_case
        available when @variables.during_business_hours == True
        description: "Create a support case for immediate assignment to available agents"

topic after_hours:
  reasoning:
    actions:
      create_case: @actions.create_support_case
        available when @variables.during_business_hours == False
        description: "Create a support case for next-business-day follow-up"
```

### When to use description overrides

| Scenario | Use Override? |
|----------|--------------|
| Same action serves different user expertise levels | ✅ Yes |
| Same action has different context in different topics | ✅ Yes |
| Action is always used the same way | ❌ No — single description suffices |
| Action name alone is already clear | ❌ No — don't over-engineer |

---

## 2. Instruction Action References

The `{!@actions.action_name}` syntax embeds a **reference to the full action definition** (not just the name) into reasoning instructions. This gives the LLM richer context about the action's inputs, outputs, and purpose — improving selection accuracy when multiple actions could apply.

### Basic Syntax

```agentscript
topic business_hours_routing:
  data:
    @variables.next_open_time: ...

  reasoning:
    instructions: ->
      if @variables.next_open_time:
        | We are currently OUTSIDE business hours.
          The next available time is {!@variables.next_open_time}.
          Create a support case using {!@actions.create_case} to ensure
          follow-up during business hours.
      else:
        | We are currently WITHIN business hours.
          Connect the customer to live support using {!@actions.transfer_to_agent}.
```

### Conditional Instruction Patterns

Guide the LLM toward specific actions based on state:

```agentscript
topic identity_verification:
  reasoning:
    instructions: ->
      if @variables.verification_attempts < 3:
        | Verify identity using {!@actions.verify_email_code}
          or {!@actions.verify_phone_code}.
      else:
        | Maximum attempts reached. Escalate using {!@actions.escalate_to_security}.
```

```agentscript
topic order_inquiry:
  reasoning:
    instructions: ->
      if @variables.order_status == "shipped":
        | Track shipment using {!@actions.get_tracking_info}.
      if @variables.order_status == "processing":
        | Check status using {!@actions.get_fulfillment_status}.
      if @variables.order_status == "cancelled":
        | Process refund using {!@actions.initiate_refund}.
```

### Combining with `available when`

For maximum control, use both instruction references AND deterministic guards:

```agentscript
topic secure_operations:
  reasoning:
    instructions: ->
      if @variables.verified == True:
        | You can now access sensitive operations using {!@actions.view_account_details}.
      else:
        | Please verify your identity first.

    actions:
      view_account_details: @actions.get_account_info
        available when @variables.verified == True
        description: "View sensitive account information"
```

**Result**: Instruction guidance steers the LLM, while `available when` provides a deterministic safety net.

### Descriptions vs. References: When to Use Which

| Approach | When to Use |
|----------|-------------|
| **Description overrides** | Action needs different descriptions per topic/context |
| **Instruction references** | Need to explicitly guide LLM toward an action in instructions |
| **Both** | Maximum control — override description AND reference in instructions |

---

## 3. Input Binding Decision Matrix

Agent Script supports four input binding approaches. Use this matrix to choose:

| Binding | Syntax | Use When | Example |
|---------|--------|----------|---------|
| **LLM slot-filling** | `...` | User provides the value in conversation | `with query=...` |
| **Variable binding** | `@variables.X` | Data exists from prior turns or actions | `with id=@variables.customer_id` |
| **Fixed value** | literal | System constant or business rule | `with format="pdf"` |
| **Mixed** | combination | Complex actions needing multiple sources | See below |

### Mixed Binding Example

```agentscript
process_refund: @actions.process_refund_request
  with order_id=@variables.order_id          # Variable — from previous action
       reason=...                             # Slot-fill — user explains why
       amount=@variables.order_total          # Variable — stored value
       refund_method="original_payment"       # Fixed — business rule
       require_approval=True                  # Fixed — policy constant
```

### Combined Pattern: Capture → Reuse → Extend

```agentscript
# Step 1: Capture data from first action
search: @actions.search_products
  with query=...
  set @variables.product_id = @outputs.top_result_id

# Step 2: Reuse captured value + collect new input
add_to_cart: @actions.add_to_cart
  with product_id=@variables.product_id      # Reuse from step 1
       quantity=...                           # New user input
       apply_discount=True                    # Business rule
```

---

## 4. Callback Behavior Notes

These supplement the "Action Chaining with `run` Keyword" section in SKILL.md.

### Callbacks only execute if the parent action succeeds

```agentscript
verify_payment: @actions.verify_payment_method
  with payment_method_id=...
  set @variables.verified = @outputs.success
  run @actions.process_payment                 # Only runs if verify succeeds
    with payment_method_id=...
```

If `verify_payment_method` fails (Flow error, Apex exception), `process_payment` **will not execute**. Design your conversation flow to handle the failure case separately.

### Flatten, don't nest

```agentscript
# ❌ WRONG — nested callbacks (not allowed)
action1: @actions.first
  run @actions.second
    run @actions.third     # ERROR: Nested callbacks not supported

# ✅ CORRECT — sequential callbacks (flat structure)
action1: @actions.first
  run @actions.second
  run @actions.third
```

### Practical callback chain: Create → Notify → Log

```agentscript
create_case: @actions.create_support_case
  with subject=...
       description=...
       priority=@variables.priority
  set @variables.case_id = @outputs.id
  run @actions.notify_team
    with case_id=@variables.case_id
         priority=@variables.priority
  run @actions.log_case_creation
    with case_id=@variables.case_id
```

---

## 5. Additional Error Patterns

These supplement the "Common Issues" table in SKILL.md.

| Error | Cause | Fix |
|-------|-------|-----|
| Missing colon after action name | `my_action` instead of `my_action:` | Add colon: `my_action:` |
| Missing type annotation on input | `email:` with no type | Add type: `email: string` |
| Wrong target protocol | `flows://MyFlow` | Use `flow://MyFlow` (no trailing `s`) |
| `Input:` without quotes | `with Input:email=...` | Quote it: `with "Input:email"=...` |
| `...` as variable default | `my_var: mutable string = ...` | Use `""` for defaults; `...` is slot-filling only |
| Vague action description | `description: "Does a search"` | Be specific: `description: "Searches KB for articles matching the query"` |

---

---

## 6. JSON Parsing Pattern

Agent Script cannot parse JSON strings inline. When an action returns a JSON string that needs to be decomposed into individual fields, use a Flow or Apex action to parse it.

### Problem

```agentscript
# This will NOT work - cannot parse JSON inline in Agent Script
set @variables.name = @outputs.json_response["name"]     # Not supported
set @variables.email = @outputs.json_response.email       # May work for objects, not JSON strings
```

### Solution: Flow/Apex JSON Parser

```agentscript
# Step 1: Call the action that returns JSON
get_data: @actions.fetch_external_data
   with endpoint = "customer_profile"
   set @variables.raw_json = @outputs.response_body

# Step 2: Pass JSON to a parser action (Flow or Apex)
parse: @actions.parse_json_response
   with json_string = @variables.raw_json
   set @variables.customer_name = @outputs.name
   set @variables.customer_email = @outputs.email
   set @variables.customer_tier = @outputs.tier
```

### Apex Parser Example

```apex
public class JsonParserAction {
    public class ParseRequest {
        @InvocableVariable(required=true)
        public String jsonString;
    }

    public class ParseResult {
        @InvocableVariable public String name;
        @InvocableVariable public String email;
        @InvocableVariable public String tier;
    }

    @InvocableMethod(label='Parse Customer JSON')
    public static List<ParseResult> parse(List<ParseRequest> requests) {
        List<ParseResult> results = new List<ParseResult>();
        for (ParseRequest req : requests) {
            Map<String, Object> parsed = (Map<String, Object>) JSON.deserializeUntyped(req.jsonString);
            ParseResult result = new ParseResult();
            result.name = (String) parsed.get('name');
            result.email = (String) parsed.get('email');
            result.tier = (String) parsed.get('tier');
            results.add(result);
        }
        return results;
    }
}
```

> **Tip**: For complex nested JSON, create typed Apex wrapper classes instead of using `deserializeUntyped`.

---

*Consolidated from @kunello's [PR #20](https://github.com/Jaganpro/sf-skills/pull/20) research on Agent Script Recipes action configuration patterns.*
