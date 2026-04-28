<!-- Parent: sf-ai-agentforce-observability/SKILL.md -->
# Debugging Sessions

Examples for debugging specific agent sessions using STDM data.

---

## Finding Sessions to Debug

### List Failed/Escalated Sessions

```bash
stdm-extract debug-session --data-dir ./stdm_data --list-failed
```

**Output:**
```
Failed/Escalated Sessions (last 10)
═══════════════════════════════════════════════════════════

🔄 a0x001 | Customer_Support_Agent | Escalated | 2026-01-28T10:15
❌ a0x002 | Order_Tracking_Agent   | Failed    | 2026-01-28T09:45
🔄 a0x003 | Customer_Support_Agent | Escalated | 2026-01-28T08:30
...

To debug a session, run:
  stdm-extract debug-session --data-dir ./stdm_data --session-id <ID>
```

### Find via Python

```python
import polars as pl
from pathlib import Path

sessions = pl.scan_parquet(Path("./stdm_data/sessions/**/*.parquet"))

# Failed/escalated sessions
failed = sessions.filter(
    pl.col("ssot__AiAgentSessionEndType__c").is_in(["Escalated", "Failed", "Abandoned"])
).sort("ssot__StartTimestamp__c", descending=True).head(10).collect()

for row in failed.iter_rows(named=True):
    print(f"{row['ssot__Id__c']} | {row['ssot__AiAgentApiName__c']} | {row['ssot__AiAgentSessionEndType__c']}")
```

---

## Debug a Specific Session

### Basic Timeline

```bash
stdm-extract debug-session --data-dir ./stdm_data --session-id "a0x001"
```

**Output:**
```
🔍 SESSION TIMELINE
══════════════════════════════════════════════════════════════════════

Session: a0x001
Agent: Customer_Support_Agent
Started: 2026-01-28T10:15:23.000Z
Ended: 2026-01-28T10:19:55.000Z
End Type: Escalated

──────────────────────────────────────────────────────────────────────
Timeline
──────────────────────────────────────────────────────────────────────

═══ Topic: Order_Status ═══

2026-01-28T10:15:23 → [INPUT]
   Where is my order #12345?

2026-01-28T10:15:26 ← [OUTPUT]
   I can help you track your order. Let me look that up for you.
   Your order #12345 was shipped on January 25th and is expected...

═══ Topic: Return_Policy ═══

2026-01-28T10:16:45 → [INPUT]
   I want to return it, it's damaged

2026-01-28T10:16:48 ← [OUTPUT]
   I'm sorry to hear that. I can help you start a return. However, I
   need to transfer you to a specialist for damaged items...

═══ Topic: Escalation ═══

2026-01-28T10:17:02 → [INPUT]
   Yes, please transfer me

2026-01-28T10:17:05 ← [OUTPUT]
   I'm transferring you to a customer service representative now.
```

### Verbose Mode (Show Steps)

See LLM reasoning and action details:

```bash
stdm-extract debug-session --data-dir ./stdm_data --session-id "a0x001" --verbose
```

**Output (with steps):**
```
2026-01-28T10:15:23 → [INPUT]
   Where is my order #12345?

         🧠 [LLM_STEP] Intent Detection
         ⚡ [ACTION_STEP] Get_Order_Status
            Input: {"orderId": "12345"}
            Output: {"status": "Shipped", "carrier": "UPS", "tracking": "1Z..."}
         🧠 [LLM_STEP] Response Generation

2026-01-28T10:15:26 ← [OUTPUT]
   I can help you track your order...
```

### Export to JSON

For sharing or further analysis:

```bash
stdm-extract debug-session --data-dir ./stdm_data \
    --session-id "a0x001" \
    --verbose \
    --output ./debug/session_a0x001.json
```

**JSON structure:**
```json
{
  "session": {
    "id": "a0x001",
    "agent": "Customer_Support_Agent",
    "start": "2026-01-28T10:15:23.000Z",
    "end": "2026-01-28T10:19:55.000Z",
    "end_type": "Escalated"
  },
  "timeline": [
    {
      "type": "interaction",
      "timestamp": "2026-01-28T10:15:23.000Z",
      "interaction_id": "a0y001",
      "topic": "Order_Status"
    },
    {
      "type": "message",
      "timestamp": "2026-01-28T10:15:23.000Z",
      "message_type": "INPUT",
      "content": "Where is my order #12345?"
    },
    {
      "type": "step",
      "step_type": "ACTION_STEP",
      "name": "Get_Order_Status",
      "input": "{\"orderId\": \"12345\"}",
      "output": "{\"status\": \"Shipped\"...}"
    }
  ]
}
```

---

## Using the Python Template

For custom timeline analysis:

```bash
python3 assets/analysis/message-timeline.py \
    --data-dir ./stdm_data \
    --session-id "a0x001" \
    --verbose
```

---

## Debug Patterns

### Pattern 1: Why Did It Escalate?

Look for:
1. **Topic switches** - Did topics change unexpectedly?
2. **Action failures** - Did an action return an error?
3. **User frustration** - Repeated similar inputs?

```python
# Find the last few messages before escalation
timeline = analyzer.message_timeline("a0x001")
print(timeline.tail(10))
```

### Pattern 2: Action Failure Analysis

```python
# Find action steps with error outputs
steps = pl.read_parquet("./stdm_data/steps/data.parquet")

failed_actions = steps.filter(
    (pl.col("ssot__AiAgentInteractionStepType__c") == "ACTION_STEP") &
    (pl.col("ssot__OutputValueText__c").str.contains("error|Error|ERROR"))
)

print(failed_actions.select(["ssot__Name__c", "ssot__OutputValueText__c"]))
```

### Pattern 3: Long Sessions

Sessions with many turns often indicate problems:

```python
interactions = pl.read_parquet("./stdm_data/interactions/data.parquet")

long_sessions = interactions.filter(
    pl.col("ssot__AiAgentInteractionType__c") == "TURN"
).group_by("ssot__AiAgentSessionId__c").agg(
    pl.count().alias("turns")
).filter(pl.col("turns") > 10).collect()

print(f"Sessions with 10+ turns: {len(long_sessions)}")
```

### Pattern 4: Compare Successful vs Failed

```python
sessions = pl.read_parquet("./stdm_data/sessions/data.parquet")
interactions = pl.read_parquet("./stdm_data/interactions/data.parquet")

# Join and compare
joined = sessions.join(
    interactions.group_by("ssot__AiAgentSessionId__c").agg(
        pl.count().alias("turns")
    ),
    left_on="ssot__Id__c",
    right_on="ssot__AiAgentSessionId__c"
)

print(joined.group_by("ssot__AiAgentSessionEndType__c").agg([
    pl.col("turns").mean().alias("avg_turns"),
    pl.count().alias("sessions")
]))
```

---

## Bulk Session Debug

### Export Multiple Sessions

```python
from pathlib import Path
import json

session_ids = ["a0x001", "a0x002", "a0x003"]
output_dir = Path("./debug")
output_dir.mkdir(exist_ok=True)

for sid in session_ids:
    timeline = get_timeline(data, sid)
    session_info = get_session_info(data, sid)

    with open(output_dir / f"{sid}.json", "w") as f:
        json.dump({
            "session": session_info,
            "timeline": timeline
        }, f, indent=2)

    print(f"Exported {sid}")
```

---

## Tips

1. **Start with list-failed**: Find problem sessions quickly
2. **Use verbose mode**: Steps reveal why the agent took certain actions
3. **Export to JSON**: For sharing with team or deeper analysis
4. **Look at topic switches**: Unexpected changes often indicate confusion
5. **Check action outputs**: Failed actions are a common escalation cause

---

## Builder Debugging Views

The Agentforce Builder provides 4 views for real-time trace analysis:

| View | Purpose | Best For |
|------|---------|----------|
| Interaction Details | Turn-by-turn message flow | Understanding conversation flow |
| Trace Waterfall | Timeline of all steps with duration bars | Performance bottlenecks |
| Variable State | State snapshot at each step | Debugging conditional logic |
| Script View | Side-by-side script + execution highlight | Mapping script to trace |

**Tip**: Start with **Trace Waterfall** to identify slow steps, then switch to **Variable State** to inspect the data flowing through those steps. Use **Script View** when debugging Agent Script agents to see exactly which DSL line triggered each trace event.

---

## See Also

- [Analysis Examples](analysis-examples.md) - Aggregate analysis
- [Troubleshooting](../references/troubleshooting.md) - Common issues
- [Data Model Reference](../references/data-model-reference.md) - STDM schema
