<!-- Parent: sf-ai-agentforce-testing/SKILL.md -->

# Phase A4: Multi-Turn Execution Details

Execute conversations via Agent Runtime API using the **reusable Python scripts** in `hooks/scripts/`.

> ⚠️ **Agent API is NOT supported for agents of type "Agentforce (Default)".** Only custom agents created via Agentforce Builder are supported.

## Option 1: Run Test Scenarios from YAML Templates (Recommended)

Use the multi-turn test runner to execute entire scenario suites:

```bash
# Run comprehensive test suite against an agent
python3 {SKILL_PATH}/hooks/scripts/multi_turn_test_runner.py \
  --my-domain "${SF_MY_DOMAIN}" \
  --consumer-key "${CONSUMER_KEY}" \
  --consumer-secret "${CONSUMER_SECRET}" \
  --agent-id "${AGENT_ID}" \
  --scenarios assets/multi-turn-comprehensive.yaml \
  --verbose

# Run specific scenario within a suite
python3 {SKILL_PATH}/hooks/scripts/multi_turn_test_runner.py \
  --my-domain "${SF_MY_DOMAIN}" \
  --consumer-key "${CONSUMER_KEY}" \
  --consumer-secret "${CONSUMER_SECRET}" \
  --agent-id "${AGENT_ID}" \
  --scenarios assets/multi-turn-topic-routing.yaml \
  --scenario-filter topic_switch_natural \
  --verbose

# With context variables and JSON output for fix loop
python3 {SKILL_PATH}/hooks/scripts/multi_turn_test_runner.py \
  --my-domain "${SF_MY_DOMAIN}" \
  --consumer-key "${CONSUMER_KEY}" \
  --consumer-secret "${CONSUMER_SECRET}" \
  --agent-id "${AGENT_ID}" \
  --scenarios assets/multi-turn-comprehensive.yaml \
  --var '$Context.AccountId=001XXXXXXXXXXXX' \
  --var '$Context.EndUserLanguage=en_US' \
  --output results.json \
  --verbose
```

**Exit codes:** `0` = all passed, `1` = some failed (fix loop should process), `2` = execution error

## Option 2: Use Environment Variables (cleaner for repeated runs)

```bash
export SF_MY_DOMAIN="your-domain.my.salesforce.com"
export SF_CONSUMER_KEY="your_key"
export SF_CONSUMER_SECRET="your_secret"
export SF_AGENT_ID="0XxRM0000004ABC"

# Now run without credential flags
python3 {SKILL_PATH}/hooks/scripts/multi_turn_test_runner.py \
  --scenarios assets/multi-turn-comprehensive.yaml \
  --verbose
```

## Option 3: Python API for Ad-Hoc Testing

For custom scenarios or debugging, use the client directly:

```python
from hooks.scripts.agent_api_client import AgentAPIClient

client = AgentAPIClient(
    my_domain="your-domain.my.salesforce.com",
    consumer_key="...",
    consumer_secret="..."
)

# Context manager auto-ends session
with client.session(agent_id="0XxRM000...") as session:
    r1 = session.send("I need to cancel my appointment")
    print(f"Turn 1: {r1.agent_text}")

    r2 = session.send("Actually, reschedule instead")
    print(f"Turn 2: {r2.agent_text}")

    r3 = session.send("What was my original request?")
    print(f"Turn 3: {r3.agent_text}")
    # Check context preservation
    if "cancel" in r3.agent_text.lower():
        print("✅ Context preserved")

# With initial variables
variables = [
    {"name": "$Context.AccountId", "type": "Id", "value": "001XXXXXXXXXXXX"},
    {"name": "$Context.EndUserLanguage", "type": "Text", "value": "en_US"},
]
with client.session(agent_id="0Xx...", variables=variables) as session:
    r1 = session.send("What orders do I have?")
```

**Connectivity Test:**
```bash
# Verify ECA credentials and API connectivity
python3 {SKILL_PATH}/hooks/scripts/agent_api_client.py
# Reads SF_MY_DOMAIN, SF_CONSUMER_KEY, SF_CONSUMER_SECRET from env
```

## Per-Turn Analysis Checklist

The test runner automatically evaluates each turn against expectations defined in the YAML template:

| # | Check | YAML Key | How Evaluated |
|---|-------|----------|---------------|
| 1 | Response non-empty? | `response_not_empty: true` | `messages[0].message` has content |
| 2 | Correct topic matched? | `topic_contains: "cancel"` | Heuristic: inferred from response text |
| 3 | Expected actions invoked? | `action_invoked: true` | Checks for `result` array entries |
| 4 | Response content? | `response_contains: "reschedule"` | Substring match on response |
| 5 | Context preserved? | `context_retained: true` | Heuristic: checks for prior-turn references |
| 6 | Guardrail respected? | `guardrail_triggered: true` | Regex patterns for refusal language |
| 7 | Escalation triggered? | `escalation_triggered: true` | Checks for `Escalation` message type |
| 8 | Response excludes? | `response_not_contains: "error"` | Substring exclusion check |

See [Agent API Reference](../references/agent-api-reference.md) for complete response format.
