<!-- Parent: sf-ai-agentforce-observability/SKILL.md -->
# Builder Trace API — Reverse-Engineered Internal Endpoint

How the Agentforce Builder's "Trace" tab renders real-time execution telemetry, the exact internal API endpoints, request/response schemas, and how to capture trace data programmatically.

> **Status**: ✅ Confirmed via live network capture (February 2026).

---

## Two-Layer Trace Architecture

The Agentforce Builder's Trace tab is powered by two distinct systems:

### Layer 1: Real-Time Execution Trace (Aura Controller)

The **live** trace rendered during Builder testing uses an **Aura controller action** — confirmed via CDP network capture:

| Aspect | Detail |
|--------|--------|
| **Endpoint** | `serviceComponent://ui.agent.authoring.components.aura.controller.AgentAuthoringController/ACTION$getSimulationPlanTraces` |
| **Protocol** | Aura framework (POST to `/aura`) |
| **Auth** | Cookie-based browser session (no explicit `Authorization` header) |
| **Trigger** | Called automatically after SSE stream delivers `INFORM` event |
| **Input** | `{ planId, sessionId, version: "1.0" }` |
| **Output** | `PlanSuccessResponse` with `plan[]` array of 13 step types |
| **Latency** | Real-time (called after agent responds) |
| **Persistence** | Transient — not stored in STDM |

### Layer 2: Persisted Session Tracing (STDM in Data Cloud)

After 5-15 minutes, a **subset** of trace data is persisted to Data Cloud across 24 DMOs:

| Aspect | Detail |
|--------|--------|
| **Storage** | Data Cloud (Data 360) |
| **Query API** | Data Cloud Query API (SQL-like) |
| **Auth** | JWT Bearer via External Client App |
| **Step Types** | 5 (vs 13 in real-time trace) |
| **Retention** | 13 months (prod) / 30 days (sandbox) |

See [data-model-reference.md](data-model-reference.md) and [query-patterns.md](query-patterns.md) for full STDM documentation.

---

## Confirmed Architecture

The Builder uses a **two-phase request pattern** per user message:

```
Phase 1: Message Delivery (SSE Stream)
┌─────────────────────────────────────────────────────────────────┐
│ Builder LWC → POST /einstein/ai-agent/v1/sessions/{id}/        │
│                     messages/stream                              │
│ Auth: Bearer token (JWT)                                        │
│ Body: {"message":{"type":"Text","text":"...","sequenceId":"N"}} │
│                                                                  │
│ Response: SSE stream with events:                                │
│   event: TEXT_CHUNK  → streaming word-by-word response           │
│   event: INFORM      → final message + planId + feedbackId       │
│   event: END_OF_TURN → turn complete                             │
└─────────────────────────────────────────────────────────────────┘
                    │
                    │ planId from INFORM event
                    ▼
Phase 2: Trace Retrieval (Aura Controller)
┌─────────────────────────────────────────────────────────────────┐
│ Builder LWC → POST /aura                                        │
│ Descriptor: AgentAuthoringController/getSimulationPlanTraces    │
│ Auth: Browser cookies (X-SFDC-Page-Cache, X-SFDC-Request-Id)   │
│ Params: { planId, sessionId, version: "1.0" }                  │
│                                                                  │
│ Response: PlanSuccessResponse with plan[] array                  │
│   → 13 step types, full variable state, LLM prompts, timing     │
└─────────────────────────────────────────────────────────────────┘
```

**Key discovery**: The `planId` returned in the SSE `INFORM` event is the same ID used to fetch the trace. This links the message stream to the execution trace.

---

## SSE Stream Schema (`/messages/stream`)

### Request

```
POST https://api.salesforce.com/einstein/ai-agent/v1/sessions/{sessionId}/messages/stream
Authorization: Bearer {jwt_token}
Content-Type: application/json
x-salesforce-region: us-west-2
X-B3-TraceId: {distributed_trace_id}
X-B3-SpanId: {span_id}
```

```json
{
  "message": {
    "type": "Text",
    "text": "Where is my order?",
    "sequenceId": "1"
  }
}
```

### SSE Event Types

| Event Type | Purpose | Key Fields |
|------------|---------|------------|
| `TEXT_CHUNK` | Streaming response text | `offset`, `message.message` (word/phrase) |
| `INFORM` | Final complete response | `message.message`, `planId`, `feedbackId`, `isContentSafe`, `citedReferences[]` |
| `END_OF_TURN` | Turn completion marker | `message.type: "EndOfTurn"` |

### INFORM Event Schema (Critical — Contains `planId`)

```json
{
  "timestamp": 1772000000000,
  "originEventId": "1772000000000-REQ",
  "traceId": "00000000000000001234567890abcdef",
  "offset": 0,
  "message": {
    "type": "Inform",
    "feedbackId": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "isContentSafe": true,
    "message": "I can help you with that. Let me look into it...",
    "id": "11111111-2222-3333-4444-555555555555",
    "metrics": {},
    "planId": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "result": [],
    "citedReferences": []
  }
}
```

> Note: `planId` and `feedbackId` are identical in the observed capture.

---

## Trace API Schema (`getSimulationPlanTraces`)

### Request (Aura)

```
POST /aura
Content-Type: application/x-www-form-urlencoded
X-SFDC-Page-Cache: {page_cache_id}
X-SFDC-Request-Id: {request_id}
X-B3-TraceId: {trace_id}
```

URL-encoded body (decoded):

```json
{
  "actions": [{
    "id": "48;a",
    "descriptor": "serviceComponent://ui.agent.authoring.components.aura.controller.AgentAuthoringController/ACTION$getSimulationPlanTraces",
    "callingDescriptor": "UNKNOWN",
    "params": {
      "planId": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
      "sessionId": "019xxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
      "version": "1.0"
    }
  }]
}
```

### Response: `PlanSuccessResponse`

```json
{
  "type": "PlanSuccessResponse",
  "planId": "aaaaaaaa-...",
  "sessionId": "019xxxxx-...",
  "intent": "DefaultTopic",
  "topic": "DefaultTopic",
  "plan": [
    { "type": "UserInputStep", ... },
    { "type": "SessionInitialStateStep", ... },
    { "type": "EnabledToolsStep", ... },
    { "type": "LLMStep", ... },
    ...
  ]
}
```

---

## Complete Step Type Taxonomy (13 Types)

> For the full execution lifecycle and how these steps map to AgentScript syntax, see [agent-execution-lifecycle.md](agent-execution-lifecycle.md).

Captured from a single agent turn (46 steps total):

| Step Type | Count | Description | Key Data Fields |
|-----------|-------|-------------|-----------------|
| `VariableUpdateStep` | 28 | Variable state change | `variable_updates[].{variable_name, variable_past_value, variable_new_value, variable_change_reason, directive_context}` |
| `BeforeReasoningIterationStep` | 3 | Pre-iteration setup | `agent_name`, `action_names[]` |
| `NodeEntryStateStep` | 2 | Topic/agent entry | `agent_name`, `directive_context`, `state_variables{}` |
| `BeforeReasoningStep` | 2 | Pre-reasoning setup | `agent_name`, `action_names[]` |
| `EnabledToolsStep` | 2 | Available tools list | `agent_name`, `enabled_tools[]`, `directive_context` |
| `LLMStep` | 2 | LLM call with full prompt | `agent_name`, `prompt_name`, `prompt_content`, `execution_latency`, `messages_sent[]`, `tools_sent[]`, `response_messages[]` |
| `UserInputStep` | 1 | User message | `message` |
| `SessionInitialStateStep` | 1 | Session init state | `variable_values{}`, `directive_context` |
| `TransitionStep` | 1 | Topic transition | `from_agent`, `to_agent`, `current_state{}`, `transition_type`, `transition_mode`, `directive_context` |
| `FunctionStep` | 1 | Flow/Apex action | `function.{name, input{}, output{}, errors}`, `executionLatency` |
| `AfterReasoningStep` | 1 | Post-reasoning cleanup | `agent_name`, `action_names[]` |
| `ReasoningStep` | 1 | Grounding evaluation | `category` (GROUNDED/UNGROUNDED), `reason` |
| `PlannerResponseStep` | 1 | Final response | `message`, `responseType`, `isContentSafe`, `safetyScore.category_scores{}` |

### Common Fields (All Step Types)

Every step has:

```json
{
  "startExecutionTime": 1772000000000,
  "endExecutionTime": 1772000000000,
  "type": "StepTypeName"
}
```

Timestamps are Unix epoch milliseconds.

---

## Detailed Step Schemas

### LLMStep (Most Data-Rich)

Contains the **full LLM prompt, tool definitions, and response** — the most valuable step for debugging.

```json
{
  "startExecutionTime": 1772000001000,
  "endExecutionTime": 1772000002880,
  "type": "LLMStep",
  "data": {
    "agent_name": "Topic Selector",
    "prompt_name": "topic_selector_prompt",
    "prompt_content": "[full prompt string, 4000+ chars]",
    "prompt_response": null,
    "execution_latency": 1879
  },
  "messages_sent": [
    {"role": "system", "content": "Topic Selector & Safety Router..."},
    {"role": "user", "content": "I need help with my order"},
    {"role": "system", "content": "Customer: Jane Doe..."}
  ],
  "tools_sent": [
    "go_order_support",
    "go_escalation",
    "Inappropriate_Content",
    "Prompt_Injection",
    "Reverse_Engineering"
  ],
  "response_messages": [
    {"role": "assistant", "content": "", "tool_invocation": {"name": "go_order_support", "arguments": "{}"}}
  ]
}
```

### FunctionStep (Action Execution)

Shows Flow/Apex invocation with input/output:

```json
{
  "startExecutionTime": 1772000003000,
  "endExecutionTime": 1772000005675,
  "type": "FunctionStep",
  "function": {
    "name": "Get_Order_Status",
    "input": {"orderId": "ORD-12345"},
    "output": {"status": "Shipped", "trackingNumber": "1Z999..."},
    "errors": null
  },
  "executionLatency": 2675
}
```

### TransitionStep (Topic Routing)

Shows topic-to-topic transitions with full state:

```json
{
  "startExecutionTime": 1772000002900,
  "endExecutionTime": 1772000002900,
  "type": "TransitionStep",
  "data": {
    "from_agent": "Topic Selector",
    "to_agent": "order_support",
    "current_state": {"authenticated": true, "customer_name": "Jane Doe", "...": "..."},
    "transition_type": "ROUTING",
    "transition_mode": "DIRECT",
    "directive_context": "on_message"
  }
}
```

### PlannerResponseStep (Final Output + Safety)

Contains the safety score breakdown:

```json
{
  "startExecutionTime": 1772000006800,
  "endExecutionTime": 1772000006800,
  "type": "PlannerResponseStep",
  "message": "I can help you track your order. Let me look that up...",
  "responseType": "Inform",
  "isContentSafe": true,
  "safetyScore": {
    "safetyScore": {
      "safety_score": 0.99,
      "category_scores": {
        "toxicity": 0, "hate": 0, "identity": 0, "violence": 0,
        "physical": 0, "sexual": 0, "profanity": 0, "biased": 0
      }
    }
  }
}
```

### ReasoningStep (Grounding Evaluation)

The agent's self-assessment of response quality:

```json
{
  "startExecutionTime": 1772000005600,
  "endExecutionTime": 1772000006800,
  "type": "ReasoningStep",
  "category": "GROUNDED",
  "reason": "The response follows the mandatory first question as instructed..."
}
```

---

## Real-Time → STDM Field Mapping (Confirmed)

| Real-Time Step Type (13) | Persisted STDM Step Type (5) | Data Loss |
|--------------------------|------------------------------|-----------|
| `UserInputStep` | `AIAgentInteractionMessage` (Input type) | None |
| `SessionInitialStateStep` | Not directly persisted | Full state lost |
| `NodeEntryStateStep` | `TOPIC_STEP` (partially) | State variables lost |
| `VariableUpdateStep` | `PreStepVariableText__c` / `PostStepVariableText__c` | Change reasons lost |
| `BeforeReasoningStep` | Not persisted | Action list lost |
| `BeforeReasoningIterationStep` | Not persisted | Iteration data lost |
| `EnabledToolsStep` | Not persisted | Tool list lost |
| `LLMStep` | `LLM_STEP` | Full prompt content lost; only input/output summaries kept |
| `TransitionStep` | `TOPIC_STEP` (partially) | Transition mode/type lost |
| `FunctionStep` | `ACTION_STEP` | Input/output preserved; latency lost |
| `AfterReasoningStep` | Not persisted | Cleanup data lost |
| `ReasoningStep` | `LLM_STEP` (ReactValidationPrompt) | Grounding category/reason lost |
| `PlannerResponseStep` | `AIAgentInteractionMessage` (Output type) | Safety scores lost; content preserved |

**Key finding**: The real-time trace contains **13 step types** vs **5 in STDM**. The most valuable debugging data (full LLM prompts, variable change reasons, safety scores, grounding evaluations) is **not persisted** to Data Cloud.

---

## Other Discovered Endpoints

### `postInteractionSummary` (Aura)

Called after trace retrieval. Sends the full agent script + conversation back for analytics:

```
Descriptor: aura://AuthoringAgentFamilyController/ACTION$postInteractionSummary
Params: {
  authoringAgentInteractionSummaryInputRepresentation: {
    projectId: "{project_id}",
    currentAFScript: "[full agent script JSON]",
    ...
  }
}
```

### `EvfSdkController/publishEvent` (Aura Telemetry)

Client-side observability events tagged `COPILOT_O11Y`:

```
Descriptor: aura://EvfSdkController/ACTION$publishEvent
Params: {
  event: {
    contextualData: {
      loggerName: "COPILOT_O11Y",
      loggerAppName: "AgentAuthoring:agentAuthoringBuilder"
    },
    feature: "EINSTEIN_..."
  }
}
```

---

## Auth Patterns (Confirmed)

| Endpoint | Auth Method | Header |
|----------|------------|--------|
| **SSE Stream** (`/messages/stream`) | JWT Bearer token | `Authorization: Bearer eyJ...` |
| **Aura Trace** (`/aura` + `getSimulationPlanTraces`) | Browser cookies | `X-SFDC-Page-Cache`, `X-SFDC-Request-Id` (no Authorization header) |
| **Aura Telemetry** (`/aura` + instrumentation) | Browser cookies | Same as above |

> **Important**: The trace endpoint (`getSimulationPlanTraces`) uses **cookie-based auth only**. It cannot be called with a standalone JWT token. You must maintain a browser session.

---

## Capture Methodology

### Option 1: CLI Preview Commands (Recommended)

The `sf agent preview start/send/end` commands provide programmatic access to the same v1.1 trace data without browser automation:

```bash
# Start session → send utterance → end and get traces
SESSION_ID=$(sf agent preview start --api-name My_Agent --target-org myOrg --json 2>/dev/null | jq -r '.result.sessionId')
PLAN_ID=$(sf agent preview send --session-id "$SESSION_ID" --api-name My_Agent --utterance "test" --target-org myOrg --json 2>/dev/null | jq -r '.result.messages[-1].planId')
TRACES_PATH=$(sf agent preview end --session-id "$SESSION_ID" --api-name My_Agent --target-org myOrg --json 2>/dev/null | jq -r '.result.tracesPath')

# Analyze trace
jq '.' "$TRACES_PATH/$PLAN_ID.json"
```

> For full workflow details, see **sf-ai-agentforce-testing** Phase F: trace-enriched preview testing. If you use `--authoring-bundle` instead of `--api-name`, remember that `preview start` now requires an explicit mode flag: `--simulate-actions` or `--use-live-actions`.

### Option 2: Manual HAR Export (Fallback)

1. Open DevTools (`Cmd+Opt+I`) → Network tab
2. Enable: ✅ Preserve log, ✅ Disable cache, Filter: Fetch/XHR
3. Send test messages in Builder
4. Right-click → "Save all as HAR with content"
5. Analyze with `jq` or the trace analyzer in `sf-ai-agentforce-testing`

### Key Findings

- The trace endpoint (`getSimulationPlanTraces`) returns the full `PlanSuccessResponse` with 13 step types
- CLI approach (`sf agent preview`) saves traces as JSON files automatically — no network interception needed
- Trace files contain complete LLM prompts, safety scores, grounding assessments, and action I/O

---

## Capture Log

Use this section to track your own capture sessions.

```
Org:              [your org alias]
Agent:            [agent API name]
Session ID:       [from SSE stream URL]
Plan ID:          [from INFORM event planId]
User message:     [test utterance]
Total requests:   [seen], [captured]
SSE streams:      [count]
Step types found: [count]
Steps in trace:   [count]
```

Key findings from initial investigation:
- Architecture is **Aura-based** (Hypothesis A confirmed)
- SSE stream at `api.salesforce.com` delivers messages; trace is fetched separately via Aura
- 13 step types in real-time vs 5 in persisted STDM
- Full LLM prompts, tool lists, and safety scores available only in real-time trace
- `planId` from INFORM event links messages to trace
- Cookie auth required for trace (no standalone API access)

---

## Programmatic Access Comparison

| API | Trace Depth | Step Types | Full Prompts | Safety Scores | Auth | Docs |
|-----|------------|------------|-------------|---------------|------|------|
| **Builder Trace** (this doc) | 13 step types, full state | 13 | ✅ Yes | ✅ Yes | Browser cookies | Internal |
| **Data Cloud STDM** | 5 step types, summaries | 5 | ❌ No | ❌ No | JWT Bearer | [query-patterns.md](query-patterns.md) |
| **Testing API** | Actions + topic only | N/A | ❌ No | ❌ No | OAuth | [Salesforce Docs](https://developer.salesforce.com/docs/einstein/genai/guide/testing-api-cli.html) |
| **Agent Runtime API** | Messages only — no trace | N/A | ❌ No | ❌ No | OAuth | [Salesforce Docs](https://developer.salesforce.com/docs/einstein/genai/guide/agent-api-overview.html) |

---

## Related Documents

- [Data Model Reference](data-model-reference.md) — Complete 24-DMO STDM schema (persisted layer)
- [Query Patterns](query-patterns.md) — Data Cloud SQL examples for persisted trace data
- [Debugging Sessions](debugging-sessions.md) — Session timeline reconstruction from STDM
- [Auth Setup](auth-setup.md) — JWT Bearer configuration for Data Cloud access
