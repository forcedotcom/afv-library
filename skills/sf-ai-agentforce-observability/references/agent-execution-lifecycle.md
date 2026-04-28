<!-- Parent: sf-ai-agentforce-observability/SKILL.md -->
# Agent Execution Lifecycle — 6-Phase Model

How the Agentforce platform processes each user message internally, based on live Builder trace captures. Maps AgentScript syntax to the 13 real-time trace step types.

> **Visual version**: Generated runtime artifact at `~/.agent/diagrams/agent-execution-lifecycle.html` with Mermaid flowcharts, timing bars, and side-by-side script-to-trace mapping.

> **Data source**: Live Builder traces from a test agent, sandbox org, 2026-02-25.

---

## The 6 Phases

Every user message triggers this pipeline:

```
Phase 1: Input & Init          (automatic — platform-managed)
Phase 2: Topic Selection        (script-driven — AgentScript start_agent)
    ↓ Decision: LLM invoked go_* tool?
    ├─ Yes → Phase 3 + Phase 4
    └─ No  → Phase 5 (short-circuit)
Phase 3: Topic Transition       (automatic — TransitionStep)
Phase 4: Topic Execution        (LLM + actions — AgentScript topic)
Phase 5: Trust Layer            (automatic — grounding + safety)
Phase 6: Response Delivery      (automatic — final message)
```

**Full path (Turn 1)**: 1 → 2 → 3 → 4 → 5 → 6 — 46 steps, 4.6s
**Short-circuit (Turn 2)**: 1 → 2 → 5 → 6 — 15 steps, 2.6s

The short-circuit occurs when the Topic Selector has enough conversation context to respond directly without routing to a topic.

---

## Phase → Step Type Mapping

### Phase 1: Input & Init

| Step Type | Count | Duration | Data |
|-----------|-------|----------|------|
| UserInputStep | 1 | 0ms | User message text |
| SessionInitialStateStep | 1 | 6ms | Locale, input, conversation context |

### Phase 2: Topic Selection

| Step Type | Count | Duration | Data |
|-----------|-------|----------|------|
| NodeEntryStateStep | 1 | 5ms | 24 state variables for topic_selector |
| VariableUpdateStep | 3 | ~1ms each | Condition checks (routable_id, mutable_case_id) |
| BeforeReasoningStep | 1 | 5ms | 5 setup actions |
| VariableUpdateStep | 6 | ~1ms each | Progressive instruction assembly |
| BeforeReasoningIterationStep | 1 | 9ms | 8 actions (setup + instruction assembly) |
| EnabledToolsStep | 1 | 2ms | 5 tools (go_product_help, go_escalation, 3 guardrails) |
| LLMStep | 1 | 624ms | Tool invocation: go_product_help |
| VariableUpdateStep | 2 | 0ms | next_topic: "__EMPTY__" → "product_help" → "__EMPTY__" |

### Phase 3: Topic Transition

| Step Type | Count | Duration | Data |
|-----------|-------|----------|------|
| TransitionStep | 1 | 0ms | topic_selector → product_help, type: handoff, mode: manual |

### Phase 4: Topic Execution

| Step Type | Count | Duration | Data |
|-----------|-------|----------|------|
| NodeEntryStateStep | 1 | 0ms | State inherited from topic_selector |
| BeforeReasoningStep | 1 | 3ms | 3 setup actions |
| VariableUpdateStep | 1 | 0ms | Condition check |
| FunctionStep | 1 | 1313ms | "Update Session Routing" Flow action |
| VariableUpdateStep | 10+ | ~1ms each | session_routed → true, instruction assembly |
| BeforeReasoningIterationStep | 1 | 1363ms | 13 actions total |
| EnabledToolsStep | 1 | 4ms | 7 tools (confirm_at_home, confirm_not_home, wrap_up, exit_to_escalation, 3 guardrails) |
| LLMStep | 1 | 1045ms | Text response: "Are you currently at home..." |
| AfterReasoningStep | 1 | 2ms | turn_count: 0 → 1 |

### Phase 5: Trust Layer

| Step Type | Count | Duration | Data |
|-----------|-------|----------|------|
| ReasoningStep | 1 | 1003ms | category: GROUNDED, reason: "follows mandatory first question" |
| PlannerResponseStep | 1 | 0ms | safety_score: 0.99, all category_scores: 0 |

### Phase 6: Response Delivery

The `PlannerResponseStep` message is delivered to the user. No additional trace steps.

---

## Script → Trace Mapping Quick Reference

| AgentScript Construct | Trace Step Type | Notes |
|----------------------|-----------------|-------|
| `start_agent entry:` | NodeEntryStateStep | Initializes topic_selector state |
| `set @variables.x = ...` | VariableUpdateStep | One step per set statement |
| `instructions: ->` with `set` | VariableUpdateStep chain | Progressive instruction assembly |
| `actions:` block | EnabledToolsStep | Lists all available tools for the LLM |
| `reasoning:` | LLMStep | The actual LLM call with full prompt |
| `before_reasoning:` | BeforeReasoningStep | Setup actions before LLM call |
| `after_reasoning:` | AfterReasoningStep | Cleanup after LLM response |
| `run @actions.X` | FunctionStep | Flow/Apex action execution |
| `transition to` / `go_*` | TransitionStep | Topic-to-topic handoff |
| `if` condition | VariableUpdateStep | Condition → true/false on `AgentScriptInternal_condition` |
| `template(...)` expression | VariableUpdateStep | Evaluates template, updates `agent_instructions` |

---

## Timing Analysis

### Turn 1 (Full Path — 46 steps, 4,556ms)

| Component | Duration | Percentage |
|-----------|----------|------------|
| LLM calls (624 + 1045ms) | 1,669ms | 37% |
| Action calls (FunctionStep) | 1,313ms | 29% |
| Grounding evaluation | 1,003ms | 22% |
| Overhead (state, transitions) | 571ms | 12% |

### Turn 2 (Short-Circuit — 15 steps, 2,564ms)

| Component | Duration | Percentage |
|-----------|----------|------------|
| LLM calls (1034ms) | 1,034ms | 40% |
| Action calls | 0ms | 0% |
| Grounding evaluation | 1,241ms | 49% |
| Overhead | 289ms | 11% |

**Key insight**: Grounding evaluation costs ~1s on every turn — as expensive as an LLM call. It's the fixed cost of Agentforce's safety guarantees.

---

## Conversation Context Growth

The `messages_sent[]` array in LLMStep grows per turn:

- **Turn 1**: 3 messages (system prompt, user input, assembled instructions)
- **Turn 2**: 7 messages (system prompt, Turn 1 user/assistant/tool/assistant, Turn 2 user, instructions)

Each turn adds ~4 messages. After 10 turns, the LLM processes 30+ messages.

---

## Dynamic Instruction Assembly

Each `set` on `AgentScriptInternal_agent_instructions` generates one VariableUpdateStep that appends a line via template evaluation. The instructions are **reset to ""** at the start of each phase and rebuilt from scratch.

Topic Selector assembly (Turn 1, 6 steps):
```
Step  7: "" → "\nCustomer: Test Customer"
Step  8: → + "This agent specializes in product troubleshooting..."
Step  9: → + "ROUTING:"
Step 10: → + "- ANY product issue → Product Help"
Step 11: → + "- Customer requests human agent → Escalation"
Step 12: → + "- ANY non-product request → Escalation"
```

The final value becomes the last system message in the LLM prompt.

---

## State Variables (24 at Entry)

Full state captured at NodeEntryStateStep (Turn 1):

| Variable | Type | Initial Value | Purpose |
|----------|------|---------------|---------|
| `authenticated` | boolean | true | Pre-verified in session init |
| `customer_name` | string | "Test Customer" | Display name for templates |
| `at_home` | string | "unknown" | Controls instruction branching |
| `products_fetched` | boolean | false | Gates product lookup |
| `product_confirmed` | string | "pending" | Product selection state |
| `session_routed` | boolean | false | Set true after FunctionStep |
| `turn_count` | integer | 0 | Incremented in after_reasoning |
| `__user_input__` | string | "My camera..." | Current message (auto-set) |
| `__resolved_locale__` | string | "en_US" | Language for response |
| `__current_date_time__` | string | ISO timestamp | Auto-updated each turn |

---

## STDM Span Types (Testing Center Trace View)

When viewing session traces in Testing Center (not Builder), steps are collapsed into 6 color-coded span types:

| Span Type              | Color      | Maps to Builder Steps                     |
|------------------------|------------|-------------------------------------------|
| TOPIC_STEP             | Blue       | NodeEntryStateStep, TransitionStep         |
| LLM_STEP               | Purple     | LLMStep, EnabledToolsStep                  |
| ACTION_STEP            | Green      | FunctionStep                               |
| TRUST_GUARDRAILS_STEP  | Orange     | ReasoningStep, PlannerResponseStep         |
| SESSION_END            | Gray       | Session termination                        |
| SYSTEM_STEP            | Light gray | SessionInitialStateStep, VariableUpdateStep|

This mapping is critical for correlating Builder-level debugging with Testing Center trace analysis. A single TOPIC_STEP span in Testing Center may represent multiple NodeEntryStateStep + TransitionStep events at the Builder level.

---

## Related Documents

- [builder-trace-api.md](builder-trace-api.md) — Reverse-engineered API endpoints and capture methodology
- [data-model-reference.md](data-model-reference.md) — Complete 24-DMO STDM schema (persisted layer)
- [query-patterns.md](query-patterns.md) — Data Cloud SQL for persisted trace data
