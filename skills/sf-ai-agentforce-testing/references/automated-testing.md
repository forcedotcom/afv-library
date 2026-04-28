<!-- Parent: sf-ai-agentforce-testing/SKILL.md -->

# Automated Testing (Python Scripts)

## Script Reference

| Script | Purpose | Dependencies |
|--------|---------|-------------|
| `agent_api_client.py` | Reusable Agent Runtime API v1 client (auth, sessions, messaging, variables) | stdlib only |
| `multi_turn_test_runner.py` | Multi-turn test orchestrator (reads YAML, executes, evaluates, Rich colored reports) | pyyaml, rich + agent_api_client |
| `rich_test_report.py` | Aggregate N worker result JSONs into one unified Rich terminal report | rich |
| `generate-test-spec.py` | Parse .agent files, generate CLI test YAML specs | stdlib only |
| `run-automated-tests.py` | Orchestrate full CLI test workflow with fix suggestions | stdlib only |

## CLI Flags (multi_turn_test_runner.py)

| Flag | Default | Purpose |
|------|---------|---------|
| `--report-file PATH` | none | Write Rich terminal report to file (ANSI codes included) — viewable with `cat` or `bat` |
| `--no-rich` | off | Disable Rich colored output; use plain-text format |
| `--width N` | auto | Override terminal width (auto-detects from $COLUMNS; fallback 80) |
| `--rich-output` | _(deprecated)_ | No-op — Rich is now default when installed |

## Multi-Turn Testing (Agent Runtime API)

```bash
# Install test runner dependency
pip3 install pyyaml

# Run multi-turn test suite against an agent
python3 {SKILL_PATH}/hooks/scripts/multi_turn_test_runner.py \
  --my-domain your-domain.my.salesforce.com \
  --consumer-key YOUR_KEY \
  --consumer-secret YOUR_SECRET \
  --agent-id 0XxRM0000004ABC \
  --scenarios assets/multi-turn-comprehensive.yaml \
  --output results.json --verbose

# Or set env vars and omit credential flags
export SF_MY_DOMAIN=your-domain.my.salesforce.com
export SF_CONSUMER_KEY=YOUR_KEY
export SF_CONSUMER_SECRET=YOUR_SECRET
python3 {SKILL_PATH}/hooks/scripts/multi_turn_test_runner.py \
  --agent-id 0XxRM0000004ABC \
  --scenarios assets/multi-turn-topic-routing.yaml \
  --var '$Context.AccountId=001XXXXXXXXXXXX' \
  --verbose

# Connectivity test (verify ECA credentials work)
python3 {SKILL_PATH}/hooks/scripts/agent_api_client.py
```

## CLI Testing (Agent Testing Center)

```bash
# Generate test spec from agent file
python3 {SKILL_PATH}/hooks/scripts/generate-test-spec.py \
  --agent-file /path/to/Agent.agent \
  --output specs/Agent-tests.yaml

# Run full automated workflow
python3 {SKILL_PATH}/hooks/scripts/run-automated-tests.py \
  --agent-name MyAgent \
  --agent-dir /path/to/project \
  --target-org dev
```

---

## Automated Test-Fix Loop

> **v2.0.0** | Supports both multi-turn API failures and CLI test failures

### Quick Start

```bash
# Run the test-fix loop (CLI tests)
{SKILL_PATH}/hooks/scripts/test-fix-loop.sh Test_Agentforce_v1 AgentforceTesting 3

# Exit codes:
#   0 = All tests passed
#   1 = Fixes needed (Claude Code should invoke sf-ai-agentforce)
#   2 = Max attempts reached, escalate to human
#   3 = Error (org unreachable, test not found, etc.)
```

### Claude Code Integration

```
USER: Run automated test-fix loop for Coral_Cloud_Agent

CLAUDE CODE:
1. Phase A: Run multi-turn scenarios via Python test runner
   python3 {SKILL_PATH}/hooks/scripts/multi_turn_test_runner.py \
     --agent-id ${AGENT_ID} \
     --scenarios assets/multi-turn-comprehensive.yaml \
     --output results.json --verbose
2. Analyze failures from results.json (10 categories)
3. If fixable: Skill(skill="sf-ai-agentscript", args="Fix...")
4. Re-run failed scenarios with --scenario-filter
5. Phase B (if available): Run CLI tests
6. Repeat until passing or max retries (3)
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CURRENT_ATTEMPT` | Current attempt number | 1 |
| `MAX_WAIT_MINUTES` | Timeout for test execution | 10 |
| `SKIP_TESTS` | Comma-separated test names to skip | (none) |
| `VERBOSE` | Enable detailed output | false |
