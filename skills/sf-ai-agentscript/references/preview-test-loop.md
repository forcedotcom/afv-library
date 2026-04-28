<!-- Parent: sf-ai-agentscript/SKILL.md -->
# Preview Smoke Test Loop (Phase 3.5)

> Rapid feedback on `.agent` files before publish — no CWC patch, no activate, no cross-skill delegation.

---

## 1. Overview

**Purpose**: After Phase 3 validation passes, run 3-5 smoke test utterances against the agent using the programmatic `sf agent preview start/send/end --authoring-bundle` flow to catch topic routing, action invocation, and grounding issues *before* the formal publish/activate/test cycle.

**Why this matters**: The `--authoring-bundle` flag compiles the `.agent` file server-side **without publishing** — no CustomerWebClient patch, no activation step. This enables ~15s iteration cycles (vs ~90s for publish+activate), letting Claude Code fix issues in a tight inner loop.

**API used**: `/einstein/ai-agent/v1.1/preview/` endpoint (separate from the Runtime API used in Phase A testing). Traces are saved locally by the `sf` CLI.

**Trace location**: `~/.sf/sfdx/agents/{agent}/sessions/{sid}/traces/{planId}.json`

---

## 2. Prerequisites

| Requirement | Why | How to Verify |
|-------------|-----|---------------|
| Agent published at least once | Authoring bundle must exist in org for `--authoring-bundle` to work | `sf agent validate authoring-bundle --api-name AgentName -o ORG --json` |
| `sf` CLI v2.121.7+ | Required for `--authoring-bundle` and programmatic preview subcommands | `sf version --json` |
| Explicit preview mode chosen | Programmatic authoring-bundle preview now requires a mode flag | Pass exactly one of `--simulate-actions` or `--use-live-actions` to `sf agent preview start --authoring-bundle ...` |
| Valid `default_agent_user` in `.agent` file | Preview runs as this user | Query the exact username from the `.agent` config and confirm: `IsActive = true`, `UserType != AutomatedProcess`, and `Profile.Name = 'Einstein Agent User'` |
| Target org authenticated | Preview needs valid session | `sf org display -o ORG_ALIAS --json` |

> ⚠️ **First-time agents**: If the agent has NEVER been published, `sf agent preview start --authoring-bundle` returns a 500 error. Run Phase 5 (publish + activate) first, then come back to Phase 3.5 for subsequent iterations.

---

## 3. Step-by-Step Workflow

### Step 1: Start preview session using authoring bundle

```bash
SESSION_ID=$(sf agent preview start \
  --authoring-bundle AgentName \
  --simulate-actions \
  --target-org ORG_ALIAS --json 2>/dev/null \
  | jq -r '.result.sessionId')

echo "Session: $SESSION_ID"
```

### Step 2: Send smoke test utterance

```bash
RESPONSE=$(sf agent preview send \
  --session-id "$SESSION_ID" \
  --authoring-bundle AgentName \
  --utterance "I need help with my order" \
  --target-org ORG_ALIAS --json 2>/dev/null)

PLAN_ID=$(echo "$RESPONSE" | jq -r '.result.messages[-1].planId')
AGENT_RESPONSE=$(echo "$RESPONSE" | jq -r '.result.messages[-1].message')

echo "Plan ID: $PLAN_ID"
echo "Response: $AGENT_RESPONSE"
```

### Step 3: Repeat for each utterance

Send each derived utterance (see "Utterance Derivation" below), capturing each `PLAN_ID` for trace analysis.

```bash
# Store plan IDs for later trace analysis
PLAN_IDS=()

for UTTERANCE in "Where is my order?" "I want to return this" "Tell me a joke" "My order #123 is late"; do
  RESP=$(sf agent preview send \
    --session-id "$SESSION_ID" \
    --authoring-bundle AgentName \
    --utterance "$UTTERANCE" \
    --target-org ORG_ALIAS --json 2>/dev/null)
  PID=$(echo "$RESP" | jq -r '.result.messages[-1].planId')
  PLAN_IDS+=("$PID")
  echo "[$PID] $UTTERANCE → $(echo "$RESP" | jq -r '.result.messages[-1].message' | head -c 80)"
done
```

### Step 4: End session and get trace path

```bash
TRACES_PATH=$(sf agent preview end \
  --session-id "$SESSION_ID" \
  --authoring-bundle AgentName \
  --target-org ORG_ALIAS --json 2>/dev/null \
  | jq -r '.result.tracesPath')

echo "Traces at: $TRACES_PATH"
```

### Step 5: Read trace for each plan ID

```bash
# Read a specific trace
TRACE="$TRACES_PATH/$PLAN_ID.json"
```

---

## 4. Trace Analysis — 6 Checks with `jq`

Each check includes: what to look for, the `jq` command, how to interpret results, and what to fix.

### Check 1: Topic Routing

**What**: Did the utterance route to the expected topic?

```bash
jq '[.steps[] | select(.stepType == "TransitionStep") | .data.to]' "$TRACE"
```

**Expected**: Array contains the target topic name (e.g., `["order_mgmt"]`).

**If wrong or missing**:
- Empty array → agent stayed in Topic Selector (descriptions too vague)
- Wrong topic name → keyword overlap between topics

**Fix**: Expand `topic X: description:` with keywords from the test utterance. See Fix Strategies §5.

---

### Check 2: Action Invocation

**What**: Did the expected action get invoked?

```bash
jq '[.steps[] | select(.stepType == "FunctionStep") | .data.function]' "$TRACE"
```

**Expected**: Array contains the target action name (e.g., `["Get_Order_Status"]`).

**If missing (empty array)**:
- `available when:` guards too restrictive for the test context
- Action `description:` doesn't clearly match what the user asked for
- Action not listed in `reasoning.actions:` for this topic

**Fix**: Relax `available when:` guards, improve action description. See Fix Strategies §5.

---

### Check 3: Wrong Action Selected

**What**: An action was invoked, but it's the wrong one.

```bash
# Same jq as Check 2 — compare output against expected action name
jq '[.steps[] | select(.stepType == "FunctionStep") | .data.function]' "$TRACE"
```

**If wrong action**: Two actions have overlapping descriptions, and the planner picked the wrong one.

**Fix**: Differentiate action descriptions with exclusion language. Add `available when:` guards to the wrong action. See Fix Strategies §5.

---

### Check 4: Grounding Assessment

**What**: Is the agent's response grounded in actual data (not hallucinated)?

```bash
jq '[.steps[] | select(.stepType == "ReasoningStep") | .data.groundingAssessment]' "$TRACE"
```

**Expected**: `"GROUNDED"` for all reasoning steps.

**If `"UNGROUNDED"`**: The agent fabricated data instead of using action outputs or variable values.

**Fix**: Add explicit data references in `instructions: ->` block. Reference specific `{!@variables.X}` or `{!@outputs.Y}` values. See Fix Strategies §5.

---

### Check 5: Safety Score

**What**: Does the agent response meet safety thresholds?

```bash
jq '.steps[] | select(.stepType == "PlannerResponseStep") | .data.safetyScore' "$TRACE"
```

**Expected**: `.overall >= 0.9`

**If low**:
- Agent revealing internal system details
- Agent responding to harmful prompts without guardrails
- Missing safety instructions in `system:` block

**Fix**: Add explicit safety guidelines to `system: instructions:`. See Fix Strategies §5.

---

### Check 6: Tool Visibility

**What**: Are the expected actions visible to the planner?

```bash
jq '[.steps[] | select(.stepType == "EnabledToolsStep") | .data.enabled_tools]' "$TRACE"
```

**Expected**: Array includes the action names defined in the topic's `reasoning.actions:`.

**If missing**:
- `available when:` conditions not met for the test context
- Action defined in wrong topic
- Action `target:` protocol invalid (flow not deployed, apex class not found)

**Fix**: Check `available when:` conditions match the test state. Verify `target:` exists in org.

---

## 5. Fix Strategies Reference

| Failure | Target Block | Edit Strategy | Example |
|---------|-------------|---------------|---------|
| **TOPIC_NOT_MATCHED** | `topic X: description:` | Add keywords from test utterance | `"Handle orders"` → `"Handle order queries, order status, package tracking, shipping updates"` |
| **ACTION_NOT_INVOKED** | `reasoning.actions: X description:` | Make description more trigger-specific | `"Get order"` → `"Look up order status when user asks about their order, package, or delivery"` |
| **ACTION_NOT_INVOKED** | `available when:` | Relax guard condition | Remove overly restrictive `@variables.X == True` if variable isn't set yet |
| **WRONG_ACTION_SELECTED** | Both competing `description:` fields | Differentiate with exclusion language | Add `"NOT for returns"` to order action, `"ONLY for returns"` to refund action |
| **UNGROUNDED_RESPONSE** | `reasoning: instructions: ->` | Add explicit data references | `"Help the customer"` → `"Help the customer using {!@variables.order_data} from Get_Order action"` |
| **LOW_SAFETY_SCORE** | `system: instructions:` | Add safety guidelines | Add `CRITICAL: Never reveal internal system details or customer PII` |
| **TOOL_NOT_VISIBLE** | `available when:` | Ensure guard matches test state | Set test variables before action, or remove guards for initial smoke test |

### Fix Application Pattern

After identifying a failure:

1. **Edit the `.agent` file** — Apply the specific edit from the table above
2. **LSP auto-validates** — The edit triggers LSP validation automatically (Phase 3 re-runs)
3. **Re-run preview** — Start a new preview session with `--authoring-bundle` and re-send the failing utterance
4. **Re-check trace** — Verify the fix resolved the issue
5. **Max 3 iterations** — If still failing after 3 fix cycles, proceed to Phase 5 (publish) with warnings

---

## 6. Full Loop Walkthrough Example

A fictional `OrderSupport` agent with 2 topics: `order_mgmt` and `returns`.

### Initial `.agent` file (relevant excerpt)

```yaml
topic order_mgmt:
  description: "Handle orders"
  reasoning:
    actions:
      get_order: @actions.Get_Order_Status
        description: "Get order"
        available when @variables.order_id != ""

topic returns:
  description: "Handle returns"
  reasoning:
    actions:
      process_return: @actions.Process_Return
        description: "Process return"
```

### Iteration 1: Derive utterances and run preview

**Derived utterances** (one per topic + one guardrail + one multi-turn):
1. `"Where is my order?"` → should route to `order_mgmt`
2. `"I want to return this"` → should route to `returns`
3. `"Tell me a joke"` → should trigger guardrail (off-topic)
4. `"My order #123 is late"` → should route to `order_mgmt` and invoke `Get_Order_Status`

**Run preview:**

```bash
SESSION_ID=$(sf agent preview start --authoring-bundle OrderSupport --simulate-actions --target-org dev --json 2>/dev/null | jq -r '.result.sessionId')

RESP1=$(sf agent preview send --session-id "$SESSION_ID" --authoring-bundle OrderSupport --utterance "Where is my order?" --target-org dev --json 2>/dev/null)
PID1=$(echo "$RESP1" | jq -r '.result.messages[-1].planId')

# ... send remaining utterances, capture plan IDs ...

TRACES_PATH=$(sf agent preview end --session-id "$SESSION_ID" --authoring-bundle OrderSupport --target-org dev --json 2>/dev/null | jq -r '.result.tracesPath')
```

**Analyze trace for utterance 1:**

```bash
jq '[.steps[] | select(.stepType == "TransitionStep") | .data.to]' "$TRACES_PATH/$PID1.json"
# Output: []  ← EMPTY! Topic not matched!
```

**Diagnosis**: "Where is my order?" didn't route to `order_mgmt` because the description `"Handle orders"` is too vague — the planner couldn't confidently match it.

### Iteration 2: Fix topic description

**Edit `.agent` file:**

```yaml
# BEFORE
topic order_mgmt:
  description: "Handle orders"

# AFTER
topic order_mgmt:
  description: "Handle order queries, order status, package tracking, shipping updates, delivery questions"
```

**Re-run preview:**

```bash
SESSION_ID=$(sf agent preview start --authoring-bundle OrderSupport --simulate-actions --target-org dev --json 2>/dev/null | jq -r '.result.sessionId')
RESP1=$(sf agent preview send --session-id "$SESSION_ID" --authoring-bundle OrderSupport --utterance "Where is my order?" --target-org dev --json 2>/dev/null)
PID1=$(echo "$RESP1" | jq -r '.result.messages[-1].planId')
TRACES_PATH=$(sf agent preview end --session-id "$SESSION_ID" --authoring-bundle OrderSupport --target-org dev --json 2>/dev/null | jq -r '.result.tracesPath')

jq '[.steps[] | select(.stepType == "TransitionStep") | .data.to]' "$TRACES_PATH/$PID1.json"
# Output: ["order_mgmt"]  ← PASS!

jq '[.steps[] | select(.stepType == "FunctionStep") | .data.function]' "$TRACES_PATH/$PID1.json"
# Output: []  ← Get_Order_Status not invoked!
```

**Diagnosis**: Topic routing fixed, but `Get_Order_Status` action not invoked because:
1. `available when @variables.order_id != ""` — but `order_id` is empty (user didn't provide it yet)
2. Description `"Get order"` is too vague for the planner to match

### Iteration 3: Fix action description and guard

**Edit `.agent` file:**

```yaml
# BEFORE
get_order: @actions.Get_Order_Status
  description: "Get order"
  available when @variables.order_id != ""

# AFTER
get_order: @actions.Get_Order_Status
  description: "Look up order status when user asks about their order, package, delivery, or tracking"
  with order_id=...
```

**Re-run preview** → all 4 utterances pass → **proceed to Phase 5 (publish)**.

---

## 7. Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| **500 from `preview start`** | Agent never published (authoring bundle doesn't exist in org) | Run Phase 5 first (publish + activate), then return to Phase 3.5 |
| **`preview start` fails immediately for authoring bundle** | Missing execution-mode flag | Re-run with exactly one of `--simulate-actions` or `--use-live-actions` |
| **Empty traces directory** | `sf agent preview end` may not write traces in all CLI versions | Check `--json` output of `preview end` for inline trace data; upgrade CLI if needed |
| **`sessionId` is null** | Auth expired or org session invalid | Re-authenticate: `sf org login web --alias ORG_ALIAS` |
| **`SessionAmbiguous (5)`** | Multiple cached sessions exist for the same agent | Run `sf agent preview sessions --json`, pick the right session ID, and retry with `--session-id` |
| **No TransitionStep in trace** | Agent used Topic Selector but didn't route to any topic | Topic descriptions are too vague — add more keywords |
| **No FunctionStep in trace** | Planner didn't select any action | Check `available when:` guards and action descriptions |
| **`preview send` timeout** | Preview compilation taking too long | `.agent` file may be too complex; simplify or wait longer |
| **Session already ended** | Sending to an expired/ended session | Start a new session with `preview start` |

### Context Variable Limitations in Preview

> ⛔ `sf agent preview` does NOT support context/session variable injection. There are no `--context`, `--session-var`, or `--variables` flags on any preview subcommand.

| Variable Source | Works in Preview? | Alternative |
|----------------|:-----------------:|-------------|
| `@session.sessionID` | ❌ | Agent Runtime API with session context |
| `@context.customerId` | ❌ | Agent Runtime API with `contextVariables` |
| `@context.RoutableId` | ❌ | Agent Runtime API with `contextVariables` |
| Mutable vars (defaults) | ✅ | Works normally via default values |
| `with param=...` (slot-filling) | ✅ | Works normally via LLM extraction |

> **Impact**: If your agent relies on `@context` or `@session` variables for routing or guards, those paths CANNOT be tested via `sf agent preview`. Use the Agent Runtime API (`/einstein/ai-agent/v1`) with `contextVariables` in the request body instead.

---

## 8. Phase 3.5 vs Phase 4 Comparison

| Aspect | Phase 3.5 (Inner Loop) | Phase 4 (Formal Testing) |
|--------|----------------------|------------------------|
| **When** | Pre-publish (`--authoring-bundle`) | Post-publish + activate |
| **Scope** | 3-5 smoke utterances | 20-100+ test cases |
| **Depth** | Topic routing + action invocation | Multi-turn, re-matching, context preservation |
| **Speed** | ~15s per iteration (no publish needed) | ~90s+ per iteration (publish + CWC + activate) |
| **Fix loop** | Self-contained in sf-ai-agentscript | Cross-skill delegation to sf-ai-agentforce-testing |
| **Skill** | sf-ai-agentscript (internal) | sf-ai-agentforce-testing (Phase A/B/C) |
| **Auth** | sf CLI org auth (Named User JWT) | ECA + Client Credentials (for API testing) |
| **Traces** | Local `~/.sf/sfdx/agents/` JSON files | Agent Runtime API response + STDM |
| **Tools needed** | Bash, Read, Edit, `jq` | Python scripts, credential_manager, multi_turn_test_runner |

---

## Utterance Derivation Guide

Claude Code derives smoke utterances from the `.agent` file itself:

1. **One per non-start topic** — Based on `description:` keywords. Pick the most natural user phrasing.
2. **One that should trigger each key action** — Match the action's `description:` to a realistic user request.
3. **One off-topic utterance** — Tests guardrails (e.g., "Tell me a joke", "What's the weather?").
4. **One multi-turn pair** — If agent has topic transitions, send two related utterances to test handoff (e.g., "Check my order" → "Actually I want to return it").

**Example derivation** for an agent with topics `order_mgmt` (description: "order status, tracking") and `returns` (description: "refunds, exchanges"):

```
1. "Where is my order?"        → order_mgmt (from description keywords)
2. "I want to return this"     → returns (from description keywords)
3. "Can you look up order 123" → order_mgmt + Get_Order_Status action
4. "Tell me a joke"            → guardrail (off-topic)
5. "My order is late" → "Actually just process a return" → topic transition
```

---

## Quick Reference: The Full Loop

```
Phase 3 passes (LSP + CLI validation clean)
    │
    ▼
Derive 3-5 utterances from .agent file
    │
    ▼
┌─► sf agent preview start --authoring-bundle AgentName --simulate-actions
│       │
│       ▼
│   sf agent preview send (for each utterance)
│       │
│       ▼
│   sf agent preview end → get traces path
│       │
│       ▼
│   Read traces with jq → run 6 checks
│       │
│       ├── All pass → Proceed to Phase 5 (publish) ✅
│       │
│       └── Failures found → Edit .agent file → LSP re-validates
│               │
│               └── iteration < 3? ──────────────────────┐
│                       │                                  │
│                       ▼                                  │
└───────────────── Yes ─┘                                  │
                                                           │
                    No (3 iterations exhausted) ◄──────────┘
                        │
                        ▼
                    Phase 5 with warnings ⚠️
```
