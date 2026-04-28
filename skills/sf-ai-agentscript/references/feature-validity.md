<!-- Parent: sf-ai-agentscript/SKILL.md -->

# Feature Validity by Context (TDD Validated v2.2.0)

> **Key distinction**: Many action metadata properties are valid on **action definitions with targets** (`flow://`, `apex://`) but NOT on **utility actions** (`@utils.transition`). The v1.3.0 finding that tested only `@utils.transition` was too narrow — v2.2.0 corrects this.

| Feature | On `@utils.transition` | On action definitions with `target:` | Notes |
|---------|------------------------|---------------------------------------|-------|
| `label:` on topics | ❌ v1.3.0 | ✅ v2.2.0 | Valid on topic blocks |
| `label:` on actions | ❌ v1.3.0 | ✅ v2.2.0 | Valid on Level 1 action definitions |
| `label:` on I/O fields | ❌ v1.3.0 | ✅ v2.2.0 | Valid on inputs/outputs |
| `require_user_confirmation:` | ❌ | ✅ v2.2.0 | Compiles; runtime no-op (Issue 6) |
| `include_in_progress_indicator:` | ❌ | ✅ v2.2.0 | Shows spinner during action execution |
| `progress_indicator_message:` | ❌ | ✅ v2.2.0 | Works on both `flow://` and `apex://` |
| `output_instructions:` | ❌ | ❓ Untested | Not tested on target-backed actions |
| `always_expect_input:` | ❌ | ❌ | NOT implemented anywhere |

**What works on `@utils.transition` actions:**
```yaml
actions:
   go_next: @utils.transition to @topic.next
      description: "Navigate to next topic"   # ✅ ONLY description works
```

**What works on action definitions with `target:`:**
```yaml
actions:
   process_order:
      label: "Process Order"                            # ✅ Display label
      description: "Process the customer's order"       # ✅ LLM description
      require_user_confirmation: True                   # ✅ Compiles (runtime Issue 6)
      include_in_progress_indicator: True               # ✅ Shows spinner
      progress_indicator_message: "Processing..."       # ✅ Custom spinner message
      inputs:
         order_id: string
            label: "Order ID"                           # ✅ I/O display label
            description: "The order identifier"
      outputs:
         status: string
            label: "Order Status"                       # ✅ I/O display label
            description: "Current order status"
      target: "apex://OrderProcessor"
```
