<!-- Parent: sf-ai-agentscript/SKILL.md -->
# Debugging & Observability Guide

> Find the Leak Before It Finds You

---

## The Debugging Workflow

```
┌─────────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐
│ 📋 Interaction      │  →   │ 📊 Trace            │  →   │ ⚙️ Find the         │
│    Details          │      │    Waterfall        │      │    Leak             │
└─────────────────────┘      └─────────────────────┘      └─────────────────────┘
```

---

## The 4 Debugging Views

| Tab | Icon | Description |
|-----|------|-------------|
| 📋 Interaction Details | List | The Summary View |
| 📊 Trace Waterfall | Chart | The Technical View |
| ↔️ Variable State Tracking | Arrows | Entry vs. Exit Values |
| <> Script View with Linting | Code | Red Squiggles |

---

### View 1: Interaction Details (Summary)

**Purpose**: High-level chronological list with AI-generated summaries

**Shows:**
- ✅ Input received from user
- ✅ Reasoning decisions made
- ✅ Actions executed
- ✅ Output evaluation results

**Best For**: Quickly understanding WHAT happened

---

### View 2: Trace Waterfall (Technical)

**Purpose**: Granular view showing every internal step

**Shows:**
- ✅ Exact prompt sent to the LLM
- ✅ Latency for each span (milliseconds)
- ✅ Raw JSON input/output for every tool call
- ✅ Variable state at each step

**Best For**: Understanding WHY something happened

---

### View 3: Variable State Tracking

**Purpose**: Real-time table of variable Entry vs Exit values

**Shows:**
- ✅ Which variables changed during each span
- ✅ Critical security variables (verified, customer_id)
- ✅ Values LLM used vs values it should have used

**Best For**: Finding when LLM ignored variable state ("goal drift")

---

### View 4: Script View with Linting

**Purpose**: Agent Script code with real-time syntax validation

**Shows:**
- ✅ Missing required top-level blocks
- ✅ Indentation issues
- ✅ Missing required fields
- ✅ Invalid resource references

**Best For**: Catching errors before deployment

---

### View Selection Guide

| Question | Use This View |
|----------|---------------|
| "What happened in this conversation?" | **Interaction Details** |
| "What exactly did the LLM see?" | **Trace Waterfall** |
| "Why did the variable have wrong value?" | **Variable State** |
| "Why won't my agent compile?" | **Script View** |

---

## The 6 Span Types

| # | Span Type | Internal Name | Description |
|---|-----------|---------------|-------------|
| 1 | ➡️ **Topic Enter** | `topic_enter` | Execution enters a new topic |
| 2 | ▶ **before_reasoning** | `before_reasoning` | Deterministic pre-processing |
| 3 | 🧠 **reasoning** | `reasoning` | LLM processes instructions |
| 4 | ⚡ **Action Call** | `action_call` | Action invoked |
| 5 | → **Transition** | `transition` | Topic navigation |
| 6 | ✓ **after_reasoning** | `after_reasoning` | Deterministic post-processing |

---

## Reading a Trace Waterfall

### Example Timeline

```
SPAN                    DURATION    TIMELINE
────────────────────────────────────────────────────────────────────
➡️ Topic Enter          15ms        ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░
▶ before_reasoning      850ms       ████████████████████░░░░░░░░░░░░
🧠 reasoning            1250ms      ██████████████████████████████░░
⚡ Action Call          450ms       ██████████████░░░░░░░░░░░░░░░░░░
```

### Latency Benchmarks

| Span Type | Expected Duration | If Slower... |
|-----------|-------------------|--------------|
| `topic_enter` | 10-20ms | Check topic complexity |
| `before_reasoning` | 50-500ms | Data fetch issues |
| `reasoning` | 1-3s | Normal LLM latency |
| `action_call` | 100-500ms | External service slow |
| `after_reasoning` | 10-50ms | Logging overhead |

---

## Variable State Analysis

### Entry vs Exit Pattern

| Step | Variable | Entry | Exit | Problem? |
|------|----------|-------|------|----------|
| 1 | `customer_verified` | `False` | `False` | - |
| 2 | `customer_verified` | `False` | `True` | - |
| 3 | `refund_processed` | `False` | `True` | ⚠️ Processed while verified=False! |

> **KEY INSIGHT**: If a critical variable like `is_verified` was `False` when an action executed, you've found your leak point.

---

## Common Debug Patterns

### Pattern 1: Wrong Policy Applied

**Symptom**: Customer received wrong regional policy

**Trace Analysis:**
1. Check Variable State → `CustomerCountry` was empty at filter step
2. Check variable declaration → `mutable string = ""`
3. **Root Cause**: Should be `linked string` with `source: @session.Country`

**Fix:**
```yaml
# Wrong
CustomerCountry: mutable string = ""

# Correct
CustomerCountry: linked string
  source: @session.Country
```

---

### Pattern 2: Action Executed Without Authorization

**Symptom**: Refund processed without identity verification

**Trace Analysis:**
1. Check reasoning span → LLM selected `process_refund`
2. Check action definition → No `available when` guard
3. **Root Cause**: LLM could see and select unguarded action

**Fix:**
```yaml
# Wrong - no guard
process_refund: @actions.process_refund
  description: "Issue refund"

# Correct - guarded
process_refund: @actions.process_refund
  description: "Issue refund"
  available when @variables.customer_verified == True
```

---

### Pattern 3: Post-Action Logic Didn't Run

**Symptom**: CRM case wasn't created after refund approval

**Trace Analysis:**
1. Check instruction resolution order → Post-action check at bottom
2. Check transition → Topic transitioned before check could run
3. **Root Cause**: Post-action check must be at TOP

**Fix:**
```yaml
# Wrong - check at bottom
instructions: ->
  | Help with refund.
  transition to @topic.next

  if @variables.refund_done:  # Never reaches here!
    run @actions.log_refund

# Correct - check at TOP
instructions: ->
  if @variables.refund_done:
    run @actions.log_refund
    transition to @topic.success

  | Help with refund.
```

---

### Pattern 4: Infinite Loop

**Symptom**: Agent keeps returning to same topic

**Trace Analysis:**
1. Check transitions → `topic_enter` repeating for same topic
2. Check conditions → No exit condition defined
3. **Root Cause**: Missing state change or exit condition

**Fix:**
```yaml
# Wrong - no exit condition
instructions: ->
  | Continue processing.

# Correct - track state, add exit
instructions: ->
  if @variables.processing_complete == True:
    transition to @topic.done

  | Continue processing.
  set @variables.step_count = @variables.step_count + 1
```

---

### Pattern 5: LLM Ignores Variable State (Goal Drift)

**Symptom**: LLM makes decision contradicting variable value

**Trace Analysis:**
1. Check Variable State → Variable had correct value
2. Check resolved instructions → Condition should have pruned text
3. **Root Cause**: Using pipe syntax (`|`) instead of arrow (`->`)

**Fix:**
```yaml
# Wrong - pipe doesn't support conditionals
instructions: |
  if @variables.verified:
    Help the user.
  # This is literal text, not a condition!

# Correct - arrow enables conditionals
instructions: ->
  if @variables.verified:
    | Help the user.
  else:
    | Please verify first.
```

---

## Diagnostic Checklist

### Quick Triage

| Check | Command/Action |
|-------|----------------|
| Syntax valid? | `sf agent validate authoring-bundle --api-name MyAgent -o TARGET_ORG --json` |
| User exists? | `sf data query -q "SELECT Username FROM User WHERE Profile.Name='Einstein Agent User'"` |
| Topic exists? | Search for topic name in script |
| Variable initialized? | Check `variables:` block |

### Deep Investigation

| Issue | What to Check |
|-------|---------------|
| Wrong output | Variable State (Entry/Exit values) |
| Skipped logic | Instruction resolution order |
| Security bypass | `available when` guards |
| Data missing | Action target protocol, linked variable sources |
| Slow response | Trace Waterfall latencies |

---

## The Big Picture

> **"Prompts are suggestions. Guards are guarantees."**

The LLM might ignore your instructions. The only way to truly prevent unwanted behavior is through **deterministic guards** like `available when`.

**When you remove an action from the LLM's toolkit, it literally cannot invoke it. That's not a suggestion - that's enforcement.**

---

## Key Takeaways

| # | Takeaway |
|---|----------|
| 1 | **Two Views for Two Purposes** - Interaction Details for quick understanding, Trace Waterfall for forensics |
| 2 | **Entry vs Exit Reveals Problems** - Variable state changes show exactly when/where issues occurred |
| 3 | **`available when` Blocks Actions** - Makes unauthorized actions invisible, not just discouraged |
| 4 | **Post-Action at TOP** - Check for completed actions at the start of instructions |
| 5 | **Linked vs Mutable** - Wrong variable modifier causes empty values |

---

## Programmatic Trace Access via CLI

> `sf agent preview start/send/end` provides full v1.1 trace data with 13 step types — far richer than the 5-type STDM data in Builder UI.

### Workflow

```bash
# 1. Start preview session
SESSION_ID=$(sf agent preview start \
  --api-name My_Agent \
  --target-org myOrg --json 2>/dev/null | jq -r '.result.sessionId')

# 2. Send utterance(s)
PLAN_ID=$(sf agent preview send \
  --session-id "$SESSION_ID" \
  --api-name My_Agent \
  --utterance "I need help with my order" \
  --target-org myOrg --json 2>/dev/null | jq -r '.result.messages[-1].planId')

# 3. End session and get trace path
TRACES_PATH=$(sf agent preview end \
  --session-id "$SESSION_ID" \
  --api-name My_Agent \
  --target-org myOrg --json 2>/dev/null | jq -r '.result.tracesPath')

# 4. Analyze trace
jq '.' "$TRACES_PATH/$PLAN_ID.json"
```

### Key `jq` Recipes for Agent Script Debugging

```bash
TRACE="$TRACES_PATH/$PLAN_ID.json"

# What instructions did the LLM actually receive?
jq -r '.steps[] | select(.stepType == "LLMStep") | .data.prompt_content[0].content' "$TRACE"

# Which topic was selected and why?
jq '.steps[] | select(.stepType == "TransitionStep") | {from: .data.from, to: .data.to}' "$TRACE"

# What actions were available per iteration?
jq '.steps[] | select(.stepType == "EnabledToolsStep") | .data.enabled_tools' "$TRACE"

# Did any action fail?
jq '.steps[] | select(.stepType == "FunctionStep") | {fn: .function, error: .error}' "$TRACE"

# Variable state changes (verify instruction resolution)
jq '.steps[] | select(.stepType == "VariableUpdateStep") | {var: .data.variableName, old: .data.oldValue, new: .data.newValue}' "$TRACE"
```

### Trace ↔ Agent Script Mapping

| Agent Script Concept | Trace Step Type | What to Check |
|---------------------|-----------------|---------------|
| `instructions: ->` | `LLMStep.prompt_content[0]` | Verify resolved text appears |
| `when` blocks | `LLMStep.prompt_content[3]` | Verify late-injected context |
| `actions:` definitions | `EnabledToolsStep.enabled_tools` | Verify action visibility |
| `available when:` | `EnabledToolsStep` (per iteration) | Verify conditional filtering |
| `transition to` | `TransitionStep` | Verify from→to routing |
| `run @actions.X` | `FunctionStep` | Verify inline action execution |
| Variable assignments | `VariableUpdateStep` | Verify state mutations |

> For full trace schema and analysis patterns, see **sf-ai-agentforce-testing** [trace-analysis.md](../../sf-ai-agentforce-testing/references/trace-analysis.md).

---

## Planner Engine Note

Agent Script compiles against the Atlas planner engine. Legacy Java planner behavior is not relevant for Agent Script agents. If you encounter "it worked in dev but not in prod" issues, focus on variable state, action I/O, and permission differences rather than planner engine variations.
