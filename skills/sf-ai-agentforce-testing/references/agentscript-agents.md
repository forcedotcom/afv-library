<!-- Parent: sf-ai-agentforce-testing/SKILL.md -->

# Agent Script Agents (AiAuthoringBundle) — Testing Guide

Agent Script agents (`.agent` files in `aiAuthoringBundles/`) deploy as `BotDefinition` and use the same `sf agent test` CLI commands. However, they have unique testing challenges:

## Two-Level Action System

- **Level 1 (Definition):** `topic.actions:` block — defines actions with `target: "apex://ClassName"`
- **Level 2 (Invocation):** `reasoning.actions:` block — invokes via `@actions.<name>` with variable bindings

## Single-Utterance Limitation

Multi-topic Agent Script agents with `start_agent` routing have a "1 action per reasoning cycle" budget in CLI tests. The first cycle is consumed by the **transition action** (`go_<topic>`). The actual business action (e.g., `get_order_status`) fires in a second cycle that single-utterance tests don't reach.

**Solution — Use `conversationHistory`:**
```yaml
testCases:
  # ROUTING TEST — captures transition action only
  - utterance: "I want to check my order status"
    expectedTopic: order_status
    expectedActions:
      - go_order_status          # Transition action from start_agent

  # ACTION TEST — use conversationHistory to skip routing
  - utterance: "The order ID is 801ak00001g59JlAAI"
    conversationHistory:
      - role: "user"
        message: "I want to check my order status"
      - role: "agent"
        topic: "order_status"    # Pre-positions agent in target topic
        message: "I'd be happy to help! Could you provide the Order ID?"
    expectedTopic: order_status
    expectedActions:
      - get_order_status         # Level 1 DEFINITION name (NOT invocation name)
    expectedOutcome: "Agent retrieves and displays order details"
```

## Key Rules for Agent Script CLI Tests

- `expectedActions` uses the **Level 1 definition name** (e.g., `get_order_status`), NOT the Level 2 invocation name (e.g., `check_status`)
- Agent Script topic names may differ in org — use the [topic name discovery workflow](../references/topic-name-resolution.md)
- Agents with `WITH USER_MODE` Apex require the Einstein Agent User to have object permissions — missing permissions cause **silent failures** (0 rows, no error)
- `subjectName` in the YAML spec maps to `config.developer_name` in the `.agent` file

## Agent Script API Testing Caveat

Agent Script agents embed action results differently via the Agent Runtime API:
- **Agent Builder agents**: Return separate `ActionResult` message types with structured data
- **Agent Script agents**: Embed action outputs within `Inform` text messages — no separate `ActionResult` type

This means:
- `action_invoked: true` (boolean) may fail even when the action runs — use `response_contains` to verify action output instead
- `action_invoked: "action_name"` uses `plannerSurfaces` fallback parsing but is less reliable
- For robust testing, prefer `response_contains` / `response_contains_any` checks over `action_invoked`

## Templates & Docs

- Template: [agentscript-test-spec.yaml](../assets/agentscript-test-spec.yaml) — 5 test patterns (CLI)
- Template: [multi-turn-agentscript-comprehensive.yaml](../assets/multi-turn-agentscript-comprehensive.yaml) — 6 multi-turn API scenarios
- Guide: [agentscript-testing-patterns.md](../references/agentscript-testing-patterns.md) — detailed patterns with worked examples

## Automated Test Spec Generation

```bash
python3 {SKILL_PATH}/hooks/scripts/generate-test-spec.py \
  --agent-file /path/to/Agent.agent \
  --output tests/agent-spec.yaml --verbose

# Generates both routing tests (with transition actions) and
# action tests (with conversationHistory for apex:// targets)
```

## Agent Discovery

```bash
# Discover Agent Script agents alongside XML-based agents
python3 {SKILL_PATH}/hooks/scripts/agent_discovery.py local \
  --project-dir /path/to/project --agent-name MyAgent
# Returns type: "AiAuthoringBundle" for .agent files
```
