<!-- Parent: sf-ai-agentforce-testing/SKILL.md -->

# Trace Analysis Reference

> **Phase F** of the testing skill — trace-enriched preview testing via `sf agent preview start/send/end`.

## Trace File Location

```
~/.sf/sfdx/agents/{agent_api_name}/sessions/{session_id}/traces/{plan_id}.json
```

Each `sf agent preview send` returns a `planId`. After `sf agent preview end`, traces are written to disk at the path above.

---

## PlanSuccessResponse Schema

The v1.1 trace format contains a top-level `steps` array. Each step has a `stepType` and type-specific `data`.

### 13 Step Types

| # | Step Type | Phase | Purpose |
|---|-----------|-------|---------|
| 1 | `UserInputStep` | Input | User's utterance entering the planner |
| 2 | `SessionInitialStateStep` | Init | Session-level state at conversation start |
| 3 | `NodeEntryStateStep` | Init | Per-node (topic) state on entry |
| 4 | `VariableUpdateStep` | State | Variable mutations during execution |
| 5 | `BeforeReasoningStep` | Pre-LLM | State snapshot before LLM reasoning begins |
| 6 | `BeforeReasoningIterationStep` | Pre-LLM | Per-iteration context (iteration count, available tools) |
| 7 | `EnabledToolsStep` | Pre-LLM | Tools visible to LLM this iteration |
| 8 | `LLMStep` | LLM | Full prompt, response, tokens, latency |
| 9 | `ReasoningStep` | LLM | Grounding assessment (GROUNDED/UNGROUNDED) |
| 10 | `FunctionStep` | Action | Action execution with inputs, outputs, errors |
| 11 | `TransitionStep` | Routing | Topic-to-topic transitions (from → to) |
| 12 | `AfterReasoningStep` | Post-LLM | State after reasoning completes |
| 13 | `PlannerResponseStep` | Response | Final response with safety scores |

### Common Fields

Every step includes:
- `stepType` — one of the 13 types above
- `timestamp` — ISO-8601 execution time
- `data` — type-specific payload (see below)

### Key Type-Specific Fields

**LLMStep** (richest data):
```json
{
  "stepType": "LLMStep",
  "data": {
    "prompt_content": [
      {"role": "system", "content": "...protocol + resolved instructions..."},
      {"role": "assistant", "content": "...conversation history..."},
      {"role": "user", "content": "...current utterance..."},
      {"role": "system", "content": "...late-injected context..."}
    ],
    "response_content": "LLM response text",
    "tools_sent": ["Action_1", "Action_2", "Inappropriate_Content"],
    "model": "sfdc_ai__DefaultGPT4o",
    "execution_latency": 1234,
    "input_tokens": 500,
    "output_tokens": 150
  }
}
```

**ReasoningStep**:
```json
{
  "stepType": "ReasoningStep",
  "data": {
    "groundingAssessment": "GROUNDED",
    "reasoningText": "The agent determined..."
  }
}
```

**FunctionStep**:
```json
{
  "stepType": "FunctionStep",
  "data": {
    "function": "Get_Order_Status",
    "arguments": {"orderId": "ORD-123"},
    "result": {"status": "Shipped"},
    "error": null,
    "executionLatency": 456
  }
}
```

**TransitionStep**:
```json
{
  "stepType": "TransitionStep",
  "data": {
    "from": "Topic_Selector",
    "to": "Order_Management"
  }
}
```

**VariableUpdateStep**:
```json
{
  "stepType": "VariableUpdateStep",
  "data": {
    "variableName": "order_id",
    "oldValue": null,
    "newValue": "ORD-123"
  }
}
```

**EnabledToolsStep**:
```json
{
  "stepType": "EnabledToolsStep",
  "data": {
    "enabled_tools": ["Get_Order_Status", "Process_Refund", "Inappropriate_Content", "Prompt_Injection"]
  }
}
```

**PlannerResponseStep**:
```json
{
  "stepType": "PlannerResponseStep",
  "data": {
    "responseText": "Your order ORD-123 has been shipped.",
    "safetyScore": {
      "overall": 0.98,
      "toxicity": 0.01,
      "prompt_injection": 0.02,
      "pii_detection": 0.0
    }
  }
}
```

---

## LLM 4-Message Prompt Structure

Each `LLMStep.data.prompt_content` contains exactly 4 messages:

| # | Role | Content | Source |
|---|------|---------|--------|
| 1 | `system` | Protocol + compiled instructions | Agent Script DSL compilation |
| 2 | `assistant` | Conversation history | Prior turns |
| 3 | `user` | Current utterance | User input |
| 4 | `system` | Late-injected context | `when` blocks + resolved variables |

### System Message 1 Sections (in order)

1. TOOL USAGE PROTOCOL
2. PROMPT INJECTION CRITERIA
3. SAFETY GUARDRAILS
4. EQUALITY PRINCIPLES
5. LANGUAGE GUIDELINES
6. OFF-TOPIC RULES
7. RESPONSE GUIDELINES
8. PROHIBITED ACTIONS
9. Resolved `system.instructions` from Agent Script

Header varies by stage:
- **Topic Selector**: `"Topic Selector & Safety Router"`
- **Topic Agent**: `"Specialized Topic Agent"`

---

## Analysis Patterns (jq Recipes)

### 1. Grounding Check

```bash
# Extract grounding assessments
jq '[.steps[] | select(.stepType == "ReasoningStep") | {
  assessment: .data.groundingAssessment,
  text: .data.reasoningText
}]' trace.json

# Flag ungrounded responses
jq '[.steps[] | select(.stepType == "ReasoningStep" and .data.groundingAssessment == "UNGROUNDED")]' trace.json
```

### 2. Safety Score Analysis

```bash
# Extract safety scores from final response
jq '.steps[] | select(.stepType == "PlannerResponseStep") | .data.safetyScore' trace.json

# Flag low safety scores (< 0.9)
jq '.steps[] | select(.stepType == "PlannerResponseStep") |
  .data.safetyScore | to_entries[] | select(.value < 0.9)' trace.json
```

### 3. LLM Prompt Extraction

```bash
# Full system prompt (compiled instructions)
jq -r '.steps[] | select(.stepType == "LLMStep") | .data.prompt_content[0].content' trace.json

# Late-injected context (when blocks + variables)
jq -r '.steps[] | select(.stepType == "LLMStep") | .data.prompt_content[3].content' trace.json

# Verify specific instruction text appears
jq -r '.steps[] | select(.stepType == "LLMStep") | .data.prompt_content[0].content' trace.json \
  | grep -c "your expected instruction"
```

### 4. Action I/O Analysis

```bash
# All actions with inputs and outputs
jq '[.steps[] | select(.stepType == "FunctionStep") | {
  action: .data.function,
  inputs: .data.arguments,
  output: .data.result,
  error: .data.error,
  latency_ms: .data.executionLatency
}]' trace.json

# Failed actions only
jq '[.steps[] | select(.stepType == "FunctionStep" and .data.error != null)]' trace.json
```

### 5. Variable State Diff

```bash
# All variable changes
jq '[.steps[] | select(.stepType == "VariableUpdateStep") | {
  variable: .data.variableName,
  old: .data.oldValue,
  new: .data.newValue
}]' trace.json
```

### 6. Timing Breakdown

```bash
# LLM latency per step
jq '[.steps[] | select(.stepType == "LLMStep") | {
  model: .data.model,
  latency_ms: .data.execution_latency,
  input_tokens: .data.input_tokens,
  output_tokens: .data.output_tokens
}]' trace.json

# Action latency
jq '[.steps[] | select(.stepType == "FunctionStep") | {
  action: .data.function,
  latency_ms: .data.executionLatency
}]' trace.json
```

### 7. Topic Routing

```bash
# All transitions
jq '[.steps[] | select(.stepType == "TransitionStep") | {
  from: .data.from,
  to: .data.to
}]' trace.json
```

### 8. Tool Visibility per Iteration

```bash
# Tools available at each reasoning iteration
jq '[.steps[] | select(.stepType == "EnabledToolsStep") | .data.enabled_tools]' trace.json

# Diff tools between iterations
jq '[.steps[] | select(.stepType == "EnabledToolsStep") | .data.enabled_tools] |
  if length > 1 then [.[0] - .[1], .[1] - .[0]] else "single iteration" end' trace.json
```

---

## trace_analyzer.py Usage

The `trace_analyzer.py` script in `hooks/scripts/` provides programmatic analysis:

```python
from hooks.scripts.trace_analyzer import TraceAnalyzer
from pathlib import Path

# Load from CLI trace directory
analyzer = TraceAnalyzer.from_cli_traces(
    Path("~/.sf/sfdx/agents/My_Agent/sessions/abc-123/traces/")
)

# Analysis methods
analyzer.conversation_timeline()    # Full turn-by-turn timeline
analyzer.grounding_report()         # Grounding assessment summary
analyzer.safety_report()            # Safety score analysis
analyzer.variable_diff_report()     # Variable state changes
analyzer.action_report()            # Action execution details
analyzer.routing_report()           # Topic transition analysis
analyzer.timing_report()            # Latency breakdown
analyzer.agentscript_suggestions()  # Fix suggestions for Agent Script

# Prompt validation (new in v2.2)
analyzer.prompt_validation(["Help with refunds", "Check order status"])

# Output
analyzer.render_terminal(console)   # Rich terminal output
analyzer.to_json(Path("analysis.json"))  # JSON export
summary = analyzer.to_summary()     # Dict summary
```

### CLI Usage

```bash
# Analyze traces from a specific session
python3 hooks/scripts/trace_analyzer.py \
  --traces-dir ~/.sf/sfdx/agents/My_Agent/sessions/abc-123/traces/

# With JSON output
python3 hooks/scripts/trace_analyzer.py \
  --traces-dir ~/.sf/sfdx/agents/My_Agent/sessions/abc-123/traces/ \
  --output analysis.json
```

---

## Cross-Skill References

| Topic | Skill | Document |
|-------|-------|----------|
| DSL compilation output | `sf-ai-agentscript` | `references/instruction-resolution.md` § "What the LLM Actually Receives" |
| Programmatic trace access | `sf-ai-agentscript` | `references/debugging-guide.md` § "Programmatic Trace Access via CLI" |
| Historical session data (STDM) | `sf-ai-agentforce-observability` | `SKILL.md` — Data Cloud extraction pipeline |
| Builder trace architecture | `sf-ai-agentforce-observability` | `references/builder-trace-api.md` — v1.1 endpoint discovery |
