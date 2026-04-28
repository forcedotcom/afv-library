<!-- Parent: sf-ai-agentforce-testing/SKILL.md -->
# CLI Commands Reference

Complete reference for SF CLI commands related to Agentforce testing.

---

## ⚠️ CRITICAL: Agent Testing Center Required

**All `sf agent test` commands require Agent Testing Center feature enabled in your org.**

```bash
# Check if Agent Testing Center is enabled
sf agent test list --target-org [alias]

# If you get these errors, Agent Testing Center is NOT enabled:
# ❌ "Not available for deploy for this organization"
# ❌ "INVALID_TYPE: Cannot use: AiEvaluationDefinition in this organization"
```

See [SKILL.md](../SKILL.md#phase-0-prerequisites--agent-discovery) for prerequisites and enablement guidance.

---

## Command Overview

```
sf agent test
├── create          Create agent test in org from spec (requires Agent Testing Center)
├── list            List available test definitions (requires Agent Testing Center)
├── run             Start agent test execution (requires Agent Testing Center)
├── results         Get completed test results
└── resume          Resume incomplete test run

sf agent
├── preview         Interactive agent testing (works without Agent Testing Center)
├── generate
│   └── test-spec   Generate test specification YAML (interactive only - no --api-name flag)
└── (other agent commands in sf-ai-agentscript)
```

**Note:** `sf agent preview` works WITHOUT Agent Testing Center - useful for manual testing when automated tests are unavailable.

---

## Test Specification Generation

### sf agent generate test-spec

Generate a YAML test specification **interactively** (no batch/scripted mode available).

```bash
sf agent generate test-spec [--output-file <path>]
```

**⚠️ Important:** This command is **interactive only** when run without arguments. There is no `--api-name` flag to auto-generate from an existing agent. You must manually input test cases through the prompts.

**Flags:**

| Flag | Description |
|------|-------------|
| `--output-file` | Path for generated YAML (default: `specs/agentTestSpec.yaml`) |
| `--api-version` | Override API version |
| `--from-definition` | Path to existing XML `AiEvaluationDefinition` file — converts to YAML test spec format |
| `--force-overwrite` | Overwrite output file without confirmation prompt |

**Converting XML to YAML:**

```bash
# Convert existing XML test definition to YAML test spec
sf agent generate test-spec --from-definition force-app/main/default/aiEvaluationDefinitions/MyTest.aiEvaluationDefinition-meta.xml --force-overwrite
```

> **Note:** `--from-definition` converts an existing XML-based test definition to the newer YAML test spec format. Useful when migrating from manually-created XML metadata to the YAML-based workflow.

**⛔ Non-existent flags (DO NOT USE):**
- `--api-name` - Does NOT exist (common misconception)
- `--agent-name` - Does NOT exist
- `--from-agent` - Does NOT exist

**Interactive Prompts:**

The command interactively prompts for:
1. **Utterance** - Test input (user message)
2. **Expected topic** - Which topic should be selected
3. **Expected actions** - Which actions should be invoked
4. **Expected outcome** - Response validation rules
5. **Custom evaluations** - JSONPath expressions for complex validation
6. **Add another?** - Continue adding test cases

**Example:**

```bash
sf agent generate test-spec --output-file ./tests/support-agent-tests.yaml

# Interactive session:
# > Enter utterance: Where is my order?
# > Expected topic: order_lookup
# > Expected actions (comma-separated): get_order_status
# > Expected outcome: action_invoked
# > Add another test case? (y/n): y
```

---

## Test Creation

### sf agent test create

Create an agent test in the org from a YAML specification.

```bash
sf agent test create --spec <file> --target-org <alias> [--api-name <name>] [--force-overwrite]
```

**Required Flags:**

| Flag | Description |
|------|-------------|
| `-s, --spec` | Path to test spec YAML file |
| `-o, --target-org` | Target org alias or username |

**Optional Flags:**

| Flag | Description |
|------|-------------|
| `-n, --api-name` | API name for the test (auto-generated if omitted) |
| `--force-overwrite` | Skip confirmation if test exists |
| `--preview` | Dry-run - view metadata without deploying |

**Example:**

```bash
# Create test from spec
sf agent test create --spec ./tests/support-agent-tests.yaml --target-org dev

# Force overwrite existing test
sf agent test create --spec ./tests/updated-spec.yaml --api-name MyAgentTest --force-overwrite --target-org dev

# Preview without deploying
sf agent test create --spec ./tests/spec.yaml --preview --target-org dev
```

**Output:**

Creates `AiEvaluationDefinition` metadata in the org at:
```
force-app/main/default/aiEvaluationDefinitions/[TestName].aiEvaluationDefinition-meta.xml
```

---

## Test Execution

### sf agent test run

Execute agent tests asynchronously.

```bash
sf agent test run --api-name <name> --target-org <alias> [--wait <minutes>]
```

**Required Flags:**

| Flag | Description |
|------|-------------|
| `-n, --api-name` | Test API name (created via `test create`) |
| `-o, --target-org` | Target org alias or username |

**Optional Flags:**

| Flag | Description |
|------|-------------|
| `-w, --wait` | Minutes to wait for completion (default: async) |
| `-r, --result-format` | Output format: `human` (default), `json`, `junit`, `tap` |
| `-d, --output-dir` | Directory to save results |
| `--verbose` | Include detailed action data |

**Example:**

```bash
# Run test and wait up to 10 minutes
sf agent test run --api-name CustomerSupportTests --wait 10 --target-org dev

# Run async (returns job ID immediately)
sf agent test run --api-name MyAgentTest --target-org dev

# Run with JSON output for CI/CD
sf agent test run --api-name MyAgentTest --wait 15 --result-format json --output-dir ./results --target-org dev

# Run with verbose output
sf agent test run --api-name MyAgentTest --wait 10 --verbose --target-org dev
```

<a id="verbose-output---verbose"></a>

### Verbose Output (`--verbose`)

The `--verbose` flag adds detailed `generatedData` to test results, including action invocations with inputs/outputs, raw agent response text, and test session IDs.

**Additional fields in `generatedData` with `--verbose`:**

| Field | Type | Description |
|-------|------|-------------|
| `invokedActions` | stringified JSON | All action invocations per turn — inputs, outputs, latency |
| `generatedResponse` | string | Raw agent response text (pre-formatting) |
| `sessionId` | string | Test session UUID |

**Example `generatedData` with `--verbose`:**

```json
"generatedData": {
  "topic": "p_16jPl000000GwEX_Field_Support_Routing_16j8eeef13560aa",
  "actionsSequence": "['Field_Support_Updating_Messaging_Session_179c7c824b693d7']",
  "generatedResponse": "Looks like you're wanting assistance...",
  "invokedActions": "[[{\"function\":{\"name\":\"Field_Support_Updating_Messaging_Session_179c7c824b693d7\",\"input\":{\"deviceType\":\"Unknown\",\"recordId\":\"0Mwbb000007MGoTCAW\",\"supportPath\":\"Field Support\"},\"output\":{\"caseId\":null}},\"executionLatency\":3553}]]",
  "outcome": "Looks like you're wanting assistance...",
  "sessionId": "019c435a-be34-7ed5-bb1e-081a6e3be446"
}
```

> **Important:** `invokedActions` is a **stringified JSON** — the value is `"[[{...}]]"` (a string), NOT a parsed array. Parse it with `JSON.parse()` or `jq 'fromjson'` before traversing.

**Using `--verbose` to build JSONPath for custom evaluations:**

1. Run: `sf agent test run --api-name Test --wait 10 --verbose --result-format json --json --target-org dev`
2. Extract action data: `jq '.result.testCases[0].generatedData.invokedActions | fromjson'`
3. Build JSONPath: `$.generatedData.invokedActions[0][0].function.input.[fieldName]`

**Async Behavior:**

Without `--wait`, the command:
1. Starts the test
2. Returns a job ID
3. Exits immediately

Use `sf agent test results --job-id <id>` to retrieve results later.

---

## Test Results

### sf agent test results

Retrieve results from a completed test run.

```bash
sf agent test results --job-id <id> --target-org <alias> [--result-format <format>]
```

**⚠️ CRITICAL BUG:** The `--use-most-recent` flag is documented in `--help` but **NOT IMPLEMENTED** as of v2.123.1. The flag appears in the help text description and examples, but the actual flag parser does NOT accept it — you get a "Nonexistent flag" error. This is a confirmed Salesforce CLI bug. **ALWAYS use `--job-id` explicitly, or use `sf agent test resume --use-most-recent` instead (that command's flag works).**

**Flags:**

| Flag | Description |
|------|-------------|
| `-i, --job-id` | **(REQUIRED)** Job ID from `test run` command |
| `-o, --target-org` | Target org alias or username |
| `-r, --result-format` | Output format: `human`, `json`, `junit`, `tap` |
| `-d, --output-dir` | Directory to save results |
| `--verbose` | Show generated data including `invokedActions` with action inputs, outputs, and latency |

**⛔ Non-working flags (DO NOT USE):**
- `--use-most-recent` - Documented in help text but NOT implemented as of v2.123.1 (confirmed still broken since v2.108.6). Use `test resume --use-most-recent` or `--job-id` instead.

**Example:**

```bash
# Get results from specific job (REQUIRED - must use job-id)
sf agent test results --job-id 4KBak0000001btZGAQ --result-format json --target-org dev

# Save results to file
sf agent test results --job-id 4KBak0000001btZGAQ --output-dir ./results --target-org dev

# With verbose output to see action details
sf agent test results --job-id 4KBak0000001btZGAQ --verbose --target-org dev
```

**Getting the Job ID:**
The `sf agent test run` command outputs the job ID when it starts:
```
Job ID: 4KBak0000001btZGAQ
```
Save this ID to retrieve results later.

---

## Test Resume

### sf agent test resume

Resume or retrieve results from an incomplete test.

```bash
sf agent test resume --job-id <id> --target-org <alias> [--wait <minutes>]
```

**Flags:**

| Flag | Description |
|------|-------------|
| `-i, --job-id` | Job ID to resume |
| `-r, --use-most-recent` | Use the job ID of the most recent agent test run (alternative to `--job-id`) |
| `-o, --target-org` | Target org alias or username |
| `-w, --wait` | Minutes to wait for completion |
| `-r, --result-format` | Output format: `human`, `json`, `junit`, `tap` |
| `-d, --output-dir` | Directory to save results |
| `--verbose` | Show generated data including `invokedActions` with action inputs, outputs, and latency |

> **Note:** `--use-most-recent` works on `test resume` (verified on v2.123.1) but is broken on `test results`. Use `test resume --use-most-recent` as a workaround when you don't have the job ID handy.

**Example:**

```bash
# Resume specific job
sf agent test resume --job-id 0Ah7X0000000001 --wait 5 --target-org dev

# Resume most recent test run (works on test resume, unlike test results)
sf agent test resume --use-most-recent --wait 5 --target-org dev

# Resume with verbose output to see action details
sf agent test resume --job-id 0Ah7X0000000001 --wait 5 --verbose --target-org dev
```

---

## Context Variables

Context variables inject session-level data (record IDs, user info) into CLI test cases, enabling action flows to receive real record IDs instead of the topic's internal name.

### YAML Syntax

```yaml
testCases:
  - utterance: "I need help with my device"
    expectedTopic: Field_Support_Routing
    expectedActions:
      - Field_Support_Updating_Messaging_Session_179c7c824b693d7
    contextVariables:
      - name: RoutableId            # NOT $Context.RoutableId — bare name only
        value: "0Mwbb000007MGoTCAW"
      - name: CaseId
        value: "500XX0000000001"
```

**Key Rules:**
- `name` uses the **bare variable name** (e.g., `RoutableId`), NOT `$Context.RoutableId`
- The CLI framework adds the `$Context.` prefix automatically during XML generation
- Maps to `<contextVariable><variableName>` / `<variableValue>` in metadata XML

**Common Variables:**

| Variable | Purpose | Discovery Query |
|----------|---------|-----------------|
| `RoutableId` | MessagingSession ID for action flows | `SELECT Id FROM MessagingSession WHERE Status='Active' LIMIT 1` |
| `CaseId` | Case record ID | `SELECT Id FROM Case ORDER BY CreatedDate DESC LIMIT 1` |
| `EndUserId` | End user contact/person ID | `SELECT Id FROM Contact LIMIT 1` |
| `ContactId` | Contact record ID | `SELECT Id FROM Contact LIMIT 1` |

**Effect of `RoutableId`:**
- **Without RoutableId:** Action flows receive the topic's internal name (e.g., `p_16jPl000000GwEX_Field_Support_Routing_16j8eeef13560aa`) as `recordId`
- **With RoutableId:** Action flows receive a real MessagingSession ID (e.g., `0Mwbb000007MGoTCAW`) as `recordId`

> **Note:** Standard context variables (`RoutableId`, `CaseId`) do NOT unlock authentication-gated topics. Injecting them does not satisfy `User_Authentication` flows. However, **custom boolean auth-state variables** (e.g., `Verified_Check`) CAN bypass the authentication flow for testing post-auth business topics — inject the boolean variable as `true` via `contextVariables` to unlock gated topics directly.

---

## Custom Evaluations

Custom evaluations allow JSONPath-based assertions on action inputs and outputs, enabling precise validation of what data an action received or returned.

> **⚠️ SPRING '26 PLATFORM BUG:** Custom evaluations with `isReference: true` (JSONPath) are currently **BLOCKED** by a server-side bug. See [Known Issues](#critical-custom-evaluations-retry-bug-spring-26) below.

### YAML Syntax

```yaml
testCases:
  - utterance: "My doorbell camera isn't working"
    expectedTopic: p_16jPl000000GwEX_Field_Support_Routing_16j8eeef13560aa
    expectedActions:
      - Field_Support_Updating_Messaging_Session_179c7c824b693d7
    contextVariables:
      - name: RoutableId
        value: "0Mwbb000007MGoTCAW"
    customEvaluations:
      - label: "supportPath is Field Support"
        name: string_comparison
        parameters:
          - name: operator
            value: equals
            isReference: false
          - name: actual
            value: "$.generatedData.invokedActions[0][0].function.input.supportPath"
            isReference: true       # JSONPath resolved against generatedData
          - name: expected
            value: "Field Support"
            isReference: false
```

### Evaluation Types

**`string_comparison`** operators: `equals`, `contains`, `startswith`, `endswith`

**`numeric_comparison`** operators: `equals`, `greater_than`, `less_than`, `greater_than_or_equal`, `less_than_or_equal`

### JSONPath Patterns

Common JSONPath expressions for `invokedActions` (use `--verbose` to discover structure):

| Path | What It Returns |
|------|-----------------|
| `$.generatedData.invokedActions[0][0].function.name` | Action name |
| `$.generatedData.invokedActions[0][0].function.input.[field]` | Action input field value |
| `$.generatedData.invokedActions[0][0].function.output.[field]` | Action output field value |
| `$.generatedData.invokedActions[0][0].executionLatency` | Action execution latency (ms) |

### Workflow

1. **Run with `--verbose`** to see `generatedData.invokedActions` structure
2. **Parse the stringified JSON** to identify field names and values
3. **Build JSONPath expressions** targeting specific input/output fields
4. **Add `customEvaluations`** to your YAML test spec
5. **Deploy and run** — ⚠️ results may only be viewable in Testing Center UI due to Spring '26 bug

---

## Metrics

Metrics add platform quality scoring to test cases. They evaluate the agent's response quality using LLM-based grading or raw performance measurements.

### YAML Syntax

```yaml
testCases:
  - utterance: "I need help troubleshooting my thermostat"
    expectedTopic: Field_Support_Routing
    expectedOutcome: "Agent should offer troubleshooting assistance"
    metrics:
      - coherence
      - instruction_following
      - output_latency_milliseconds
    # Skip: conciseness (broken), completeness (misleading for routing agents)
```

### Available Metrics

| Metric | Score Range | Status | Description |
|--------|-------------|--------|-------------|
| `coherence` | 1-5 | ✅ Works (caveat) | Response clarity, grammar, and logical flow. Typically scores 4-5 for clear responses. **⚠️ Scores deflection agents poorly** (2-3) because it evaluates whether the response "answers" the user's literal question, not whether the agent behaved correctly. For deflection/guardrail tests, use `expectedOutcome` instead. |
| `completeness` | 1-5 | ⚠️ Misleading | How fully the response addresses the query. **Penalizes triage/routing agents** for transferring instead of "solving." |
| `conciseness` | 1-5 | 🔴 Broken | **Returns score=0** with empty `metricExplainability` on most tests. Platform bug. |
| `instruction_following` | 0-1 | ⚠️ Two bugs | Whether agent follows instructions. **Bug 1:** Labels "FAILURE" even at score=1 — check score value, ignore label. **Bug 2:** Crashes Testing Center UI — `No enum constant AiEvaluationMetricType.INSTRUCTION_FOLLOWING_EVALUATION`. Remove from metrics if users need UI. |
| `output_latency_milliseconds` | Raw ms | ✅ Works | Raw response latency. No pass/fail grading — useful for performance baselining. |

### Recommendations

- **Use:** `coherence` + `output_latency_milliseconds` for baseline quality scoring
- **Skip:** `conciseness` (broken) and `completeness` (misleading for routing agents)
- **Caution:** `instruction_following` — rely on the numeric score, not the PASS/FAILURE label

---

## Test Listing

### sf agent test list

List all agent test runs in the org.

```bash
sf agent test list --target-org <alias>
```

**Example:**

```bash
sf agent test list --target-org dev
```

**Output:**

```
Test Name                  Status      Created
─────────────────────────────────────────────────
CustomerSupportTests       Completed   2025-01-01
OrderAgentTests           Running     2025-01-01
FAQAgentTests             Failed      2024-12-30
```

---

## Interactive Preview

### sf agent preview

Test agent interactively via conversation.

```bash
sf agent preview --api-name <name> --target-org <alias> [options]
```

**Required Flags:**

| Flag | Description |
|------|-------------|
| `-n, --api-name` | Agent API name |
| `-o, --target-org` | Target org alias or username |

**Optional Flags:**

| Flag | Description |
|------|-------------|
| `--use-live-actions` | Execute real Flows/Apex (vs simulated) |
| `--authoring-bundle` | Specific authoring bundle to preview |
| `-d, --output-dir` | Directory to save transcripts |
| `-x, --apex-debug` | Capture Apex debug logs |

**Modes:**

| Mode | Command | Description |
|------|---------|-------------|
| **Simulated** | `sf agent preview --api-name Agent` | LLM simulates action results |
| **Live** | `sf agent preview --api-name Agent --use-live-actions` | Real Flows/Apex execute |

> **v2.121.7+**: When `--api-name` is omitted, the interactive agent selection now shows **(Published)** and **(Agent Script)** labels next to agent names to help distinguish agent types.

**Example:**

```bash
# Simulated preview (default - safe for testing)
sf agent preview --api-name Customer_Support_Agent --target-org dev

# Save transcripts
sf agent preview --api-name Customer_Support_Agent --output-dir ./logs --target-org dev

# Live preview with real actions
sf agent preview --api-name Customer_Support_Agent --use-live-actions --target-org dev

# Live preview with debug logs
sf agent preview --api-name Customer_Support_Agent --use-live-actions --apex-debug --output-dir ./logs --target-org dev
```

**Interactive Session:**

```
> Hello, how can I help you today?

You: Where is my order?

Agent: I'd be happy to help you check your order status. Let me look that up...
[Action: get_order_status invoked]
Your order #12345 is currently in transit and expected to arrive tomorrow.

You: [ESC to exit]

Save transcript? (y/n): y
Saved to: ./logs/transcript.json
```

### Programmatic Preview (Non-Interactive)

For CI/CD and automation, use the non-interactive preview subcommands:

```bash
# Published-agent session (programmatic preview uses live actions for published agents)
sf agent preview start --api-name My_Agent -o ORG --json

# Send an utterance to the session
sf agent preview send --session-id SESSION_ID --api-name My_Agent --utterance "Hello" -o ORG --json

# Send a follow-up utterance (same session for multi-turn)
sf agent preview send --session-id SESSION_ID --api-name My_Agent --utterance "Check order 12345" -o ORG --json

# End the session
sf agent preview end --session-id SESSION_ID --api-name My_Agent -o ORG --json

# Authoring-bundle session (must choose a mode explicitly)
sf agent preview start --authoring-bundle My_Agent --simulate-actions -o ORG --json
# or: sf agent preview start --authoring-bundle My_Agent --use-live-actions -o ORG --json
```

These subcommands enable automated conversation testing outside the interactive REPL. Authoring-bundle sessions no longer default to simulated mode — choose `--simulate-actions` or `--use-live-actions` explicitly. See also: `sf-ai-agentscript/references/cli-guide.md` for the full preview workflow.

**Output Files:**

When using `--output-dir`:
- `transcript.json` - Conversation record
- `responses.json` - Full API messages with internal details
- `apex-debug.log` - Debug logs (if `--apex-debug`)

---

## Result Formats

### Human (Default)

Formatted for terminal display with colors and tables.

```bash
sf agent test run --api-name Test --result-format human --target-org dev
```

### JSON

Machine-parseable for CI/CD pipelines.

```bash
sf agent test run --api-name Test --result-format json --target-org dev
```

**JSON Structure (actual format from `--result-format json --json`):**

```json
{
  "result": {
    "runId": "4KBbb...",
    "testCases": [
      {
        "testNumber": 1,
        "inputs": {
          "utterance": "Where is my order?"
        },
        "generatedData": {
          "topic": "p_16jPl000000GwEX_Order_Lookup_16j8eeef13560aa",
          "actionsSequence": "['get_order_status']",
          "outcome": "I can help you track your order...",
          "sessionId": "uuid-string"
        },
        "testResults": [
          {
            "name": "topic_assertion",
            "expectedValue": "order_lookup",
            "actualValue": "p_16jPl000000GwEX_Order_Lookup_16j8eeef13560aa",
            "result": "PASS",
            "score": 1
          },
          {
            "name": "actions_assertion",
            "expectedValue": "['get_order_status']",
            "actualValue": "['get_order_status', 'summarize_record']",
            "result": "PASS",
            "score": 1
          },
          {
            "name": "output_validation",
            "expectedValue": "",
            "actualValue": "I can help you track your order...",
            "result": "FAILURE",
            "errorMessage": "Skip metric result due to missing expected input"
          }
        ]
      }
    ]
  }
}
```

> **Note:** `output_validation` shows `FAILURE` when `expectedOutcome` is omitted — this is **harmless**. The `topic_assertion` and `actions_assertion` results are the primary pass/fail indicators.
```

### JUnit

XML format for test reporting tools.

```bash
sf agent test run --api-name Test --result-format junit --output-dir ./results --target-org dev
```

**JUnit Structure:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="CustomerSupportTests" tests="20" failures="2" time="45.2">
  <testcase name="route_to_order_lookup" classname="topic_routing" time="2.1"/>
  <testcase name="action_invocation_test" classname="action_invocation" time="3.2">
    <failure type="ACTION_NOT_INVOKED">Expected action get_order_status was not invoked</failure>
  </testcase>
</testsuite>
```

### TAP (Test Anything Protocol)

Simple text format for basic parsing.

```bash
sf agent test run --api-name Test --result-format tap --target-org dev
```

**TAP Output:**

```
TAP version 13
1..20
ok 1 route_to_order_lookup
ok 2 action_output_validation
not ok 3 complex_order_inquiry
  ---
  message: Expected get_order_status invoked 2 times, actual 1
  category: ACTION_INVOCATION_COUNT_MISMATCH
  ...
```

---

## Common Workflows

### Workflow 1: First-Time Test Setup

```bash
# 1. Generate test spec
sf agent generate test-spec --output-file ./tests/my-agent-tests.yaml

# 2. Edit YAML to add test cases (manual step)

# 3. Create test in org
sf agent test create --spec ./tests/my-agent-tests.yaml --api-name MyAgentTests --target-org dev

# 4. Run tests
sf agent test run --api-name MyAgentTests --wait 10 --target-org dev
```

### Workflow 2: CI/CD Pipeline

```bash
# Run tests with JSON output
sf agent test run --api-name MyAgentTests --wait 15 --result-format junit --output-dir ./results --target-org dev

# Check exit code
if [ $? -ne 0 ]; then
  echo "Agent tests failed"
  exit 1
fi
```

### Workflow 3: Debug Failing Agent

```bash
# 1. Run preview with debug logs
sf agent preview --api-name MyAgent --use-live-actions --apex-debug --output-dir ./debug --target-org dev

# 2. Analyze transcripts
cat ./debug/responses.json | jq '.messages'

# 3. Check debug logs
cat ./debug/apex-debug.log | grep ERROR
```

---

## Error Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| "Agent not found" | Agent not published | Run `sf agent publish authoring-bundle` |
| "Test not found" | Test not created | Run `sf agent test create` first |
| "401 Unauthorized" | Org auth expired | Re-authenticate: `sf org login web` |
| "Job ID not found" | Test timed out | Use `sf agent test resume` |
| "No results" | Test still running | Wait longer or use `--wait` |
| **"Nonexistent flag: --use-most-recent"** | `test results` CLI bug (confirmed v2.123.1) | Use `--job-id` explicitly, or use `test resume --use-most-recent` instead |
| **Topic assertion fails** | Expected topic doesn't match actual | Standard copilots use `MigrationDefaultTopic` - update test expectations |
| **"No matching records"** | Test data doesn't exist | Verify utterances reference actual org data |
| **Test exists confirmation hangs** | Interactive prompt in script | Use `echo "y" \| sf agent test create...` |
| **"RETRY" / "INTERNAL_SERVER_ERROR"** | Custom eval platform bug (Spring '26) | Skip custom evaluations or use Testing Center UI. See [Known Issues](#critical-custom-evaluations-retry-bug-spring-26) |
| **Metric score=0 on conciseness** | `conciseness` metric broken | Skip `conciseness` metric until platform patch |
| **"No enum constant AiEvaluationMetricType.INSTRUCTION_FOLLOWING_EVALUATION"** | Testing Center UI crashes when test suite includes `instruction_following` metric | Remove `- instruction_following` from YAML metrics and redeploy. CLI execution is unaffected. |

---

## ⚠️ Common Pitfalls (Lessons Learned)

### 1. Action Matching Uses Superset Logic

Action assertions use **flexible superset matching**:
- Expected: `[IdentifyRecordByName]`
- Actual: `[IdentifyRecordByName, SummarizeRecord]`
- Result: ✅ **PASS** (actual contains expected)

This means tests pass if the agent invokes *at least* the expected actions, even if it invokes additional ones.

### 2. Topic Names Vary by Agent Type

| Agent Type | Typical Topic Names |
|------------|---------------------|
| Standard Salesforce Copilot | `MigrationDefaultTopic` |
| Custom Agent | Custom names you define |
| Agentforce for Service | `GeneralCRM`, `OOTBSingleRecordSummary` |

**Best Practice:** Run one test first, check actual topic names in results, then update expectations.

### 3. Test Data Must Exist

Tests referencing specific records will fail if:
- The record doesn't exist (e.g., "Acme" account)
- The record name doesn't match exactly (case-sensitive)

**Best Practice:** Query org for actual data before writing tests:
```bash
sf data query --query "SELECT Name FROM Account LIMIT 5" --target-org dev
```

### 4. Two Fix Strategies Exist

| Agent Type | Fix Strategy |
|------------|--------------|
| Custom Agent (you control) | Fix agent via sf-ai-agentforce |
| Managed/Standard Agent | Fix test expectations in YAML |

---

## Topic Name Resolution in CLI Tests

When writing `expectedTopic` in YAML specs, the format depends on the topic type:

| Topic Type | YAML Value | Example |
|------------|-----------|---------|
| **Standard** (Escalation, Off_Topic, etc.) | `localDeveloperName` | `Escalation` |
| **Promoted** (p_16j... prefix) | Full runtime `developerName` with hash | `p_16jPl000000GwEX_Topic_16j8eeef13560aa` |

### Standard Topics

Standard topics like `Escalation`, `Off_Topic`, and `Inappropriate_Content` can use their short `localDeveloperName`. The CLI framework resolves these to the full hash-suffixed runtime name automatically.

```yaml
# ✅ Works — framework resolves to Escalation_16j9d687a53f890
- utterance: "I want to talk to a human"
  expectedTopic: Escalation
```

### Promoted Topics

Promoted topics (custom topics created in Setup UI) have an org-specific `p_16j...` prefix and a hash suffix. You MUST use the full runtime `developerName`:

```yaml
# ✅ Works — exact runtime developerName
- utterance: "My doorbell camera is offline"
  expectedTopic: p_16jPl000000GwEX_Field_Support_Routing_16j8eeef13560aa

# ❌ FAILS — localDeveloperName doesn't resolve for promoted topics
- utterance: "My doorbell camera is offline"
  expectedTopic: Field_Support_Routing
```

### Discovery Workflow

To discover actual runtime topic names:

1. Run a test with best-guess topic names
2. Get results: `sf agent test results --job-id <ID> --result-format json --json`
3. Extract actual names: `jq '.result.testCases[].generatedData.topic'`
4. Update YAML spec with actual runtime names
5. Re-deploy with `--force-overwrite` and re-run

See [topic-name-resolution.md](topic-name-resolution.md) for the complete guide.

---

## YAML Spec Gotchas

### `name:` Field is MANDATORY

The `name:` field (becomes MasterLabel in metadata) is **required**. Without it, deploy fails:

```
Error: Required fields are missing: [MasterLabel]
```

```yaml
# ✅ Correct
name: "My Agent Tests"
subjectType: AGENT
subjectName: My_Agent

# ❌ Wrong — missing name: field
subjectType: AGENT
subjectName: My_Agent
```

### `expectedActions` is a Flat String List

Action names are simple strings, NOT objects with `name`/`invoked`/`outputs`:

```yaml
# ✅ Correct — flat string list
expectedActions:
  - get_order_status
  - create_support_case

# ❌ Wrong — object format is NOT recognized
expectedActions:
  - name: get_order_status
    invoked: true
    outputs:
      - field: out_Status
        notNull: true
```

### Empty `expectedActions: []` Means "Not Testing"

An empty list or omitted `expectedActions` means "I'm not testing action invocation for this test case" — it will PASS even if the agent invokes actions.

### Missing `expectedOutcome` Causes Harmless ERROR

Omitting `expectedOutcome` causes `output_validation` to report `ERROR` status with:
> "Skip metric result due to missing expected input"

This is **harmless** — `topic_assertion` and `actions_assertion` still run and report correctly.

### CLI Tests Have No MessagingSession Context

The CLI test framework runs without a MessagingSession. Flows that need `recordId` (e.g., from `$Context.RoutableId`) will error at runtime. The agent typically handles this gracefully by asking for the information instead.

### Do NOT Add Fabricated Fields

These fields are NOT part of the CLI YAML schema and will be silently ignored or cause errors:
- `apiVersion`, `kind` — not recognized
- `metadata.name`, `metadata.agent` — use top-level `name:` and `subjectName:` instead
- `settings.timeout`, `settings.retryCount` — not recognized
- `category`, `description`, `expectedBehavior`, `expectedResponse` — not recognized by CLI

---

## Known Issues

### CRITICAL: Custom Evaluations RETRY Bug (Spring '26)

**Status**: 🔴 PLATFORM BUG — Blocks all `string_comparison` / `numeric_comparison` evaluations with JSONPath

**Error**: `INTERNAL_SERVER_ERROR: The specified enum type has no constant with the specified name: RETRY`

**Scope**:
- Server returns "RETRY" status for test cases with custom evaluations using `isReference: true`
- Results API endpoint crashes with HTTP 500 when fetching results
- Both filter expressions `[?(@.field == 'value')]` AND direct indexing `[0][0]` trigger the bug
- Tests WITHOUT custom evaluations on the same run complete normally

**Confirmed**: Direct `curl` to REST endpoint returns same 500 — NOT a CLI parsing issue

**Workaround**:
1. Use Testing Center UI (Setup → Agent Testing) — may display results
2. Skip custom evaluations until platform patch
3. Use `expectedOutcome` (LLM-as-judge) for response validation instead

**Tracking**: Discovered 2026-02-09 on sandbox (Spring '26). TODO: Retest after platform patch.

### MEDIUM: `conciseness` Metric Returns Score=0

**Status**: 🟡 Platform bug — metric evaluation appears non-functional

**Workaround**: Skip `conciseness` in metrics lists until platform patch.

### LOW: `instruction_following` FAILURE at Score=1

**Status**: 🟡 Threshold mismatch — score and label disagree

**Workaround**: Use the numeric `score` value (0 or 1) for evaluation. Ignore the PASS/FAILURE label.

### HIGH: `instruction_following` Crashes Testing Center UI

**Status**: 🔴 Blocks Testing Center UI entirely

**Error**: `No enum constant einstein.gpt.shared.testingcenter.enums.AiEvaluationMetricType.INSTRUCTION_FOLLOWING_EVALUATION`

**Scope**: Testing Center UI (Setup → Agent Testing) throws a Java exception when opening any test suite with `instruction_following` metric. CLI execution is unaffected.

**Workaround**: Remove `- instruction_following` from YAML metrics, redeploy via `sf agent test create --force-overwrite`.

**Discovered**: 2026-02-11.

---

## Related Commands

| Command | Skill | Purpose |
|---------|-------|---------|
| `sf agent publish authoring-bundle` | sf-ai-agentscript | Publish agent before testing |
| `sf agent validate authoring-bundle` | sf-ai-agentscript | Validate agent syntax |
| `sf agent activate` | sf-ai-agentscript | Activate for preview |
| `sf org login web` | - | Standard org auth for interactive or programmatic CLI preview |
