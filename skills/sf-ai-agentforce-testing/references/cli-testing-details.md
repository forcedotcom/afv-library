<!-- Parent: sf-ai-agentforce-testing/SKILL.md -->

# CLI Testing Details

## B1.5: Topic Name Resolution

Topic name format in `expectedTopic` depends on the topic type:

| Topic Type | YAML Value | Resolution |
|------------|-----------|------------|
| **Standard** (Escalation, Off_Topic) | `localDeveloperName` (e.g., `Escalation`) | Framework resolves automatically |
| **Promoted** (p_16j... prefix) | Full runtime `developerName` with hash | Must be exact match |

**Standard topics** like `Escalation` can use the short name — the CLI framework resolves to the hash-suffixed runtime name.

**Promoted topics** (custom topics created in Setup UI) MUST use the full runtime `developerName` including hash suffix. The short `localDeveloperName` does NOT resolve.

**Discovery workflow:**
1. Write spec with best guesses for topic names
2. Deploy and run: `sf agent test run --api-name X --wait 10 --result-format json --json`
3. Extract actual names: `jq '.result.testCases[].generatedData.topic'`
4. Update spec with actual runtime names
5. Re-deploy with `--force-overwrite` and re-run

See [topic-name-resolution.md](../references/topic-name-resolution.md) for the complete guide.

## B1.6: Known CLI Gotchas

| Gotcha | Detail |
|--------|--------|
| `name:` mandatory | Deploy fails: "Required fields are missing: [MasterLabel]" |
| `expectedActions` is flat strings | `- action_name` NOT `- name: action_name, invoked: true` |
| Empty `expectedActions: []` | Means "not testing" — PASS even when actions invoked |
| Missing `expectedOutcome` | `output_validation` reports ERROR — harmless |
| No MessagingSession context | Flows needing `recordId` error (agent handles gracefully) |
| `--use-most-recent` broken on `test results` | Confirmed broken on v2.123.1. Use `--job-id` for `test results`, or use `test resume --use-most-recent` (works) |
| contextVariables `name` format | Both `RoutableId` and `$Context.RoutableId` work — runtime resolves both. Prefer `$Context.` prefix for clarity. |
| customEvaluations RETRY bug | **⚠️ Spring '26:** Server returns RETRY → REST API 500. See [Known Issues](known-issues.md). |
| `conciseness` metric broken | Returns score=0, empty explanation — platform bug |
| `instruction_following` threshold | Labels FAILURE even at score=1 — use score value, ignore label |

## B1.7: Context Variables

Context variables inject session-level data (record IDs, user info) into CLI test cases. Without them, action flows receive the topic's internal name as `recordId`. With them, they receive a real record ID.

**When to use:** Any test case where action flows need real record IDs (e.g., updating a MessagingSession, creating a Case).

**YAML syntax:**
```yaml
contextVariables:
  - name: "$Context.RoutableId"   # Prefixed format (recommended)
    value: "0Mwbb000007MGoTCAW"
  - name: "$Context.CaseId"
    value: "500XX0000000001"
```

**Key rules:**
- Both prefixed (`$Context.RoutableId`) and bare (`RoutableId`) formats work — the **runtime resolves both**
- `$Context.` prefix is recommended as it matches the Merge Field syntax used in Flow Builder and Apex
- The CLI passes the `name` verbatim to `<contextVariable><variableName>` in XML metadata — no prefix is added or stripped

**Discovery — find valid IDs:**
```bash
sf data query --query "SELECT Id FROM MessagingSession WHERE Status='Active' LIMIT 1" --target-org [alias]
sf data query --query "SELECT Id FROM Case ORDER BY CreatedDate DESC LIMIT 1" --target-org [alias]
```

**Verified effect (IRIS testing, 2026-02-09):**
- Without `RoutableId`: action receives `recordId: "p_16jPl000000GwEX_Field_Support_Routing_16j8eeef13560aa"` (topic name)
- With `RoutableId`: action receives `recordId: "0Mwbb000007MGoTCAW"` (real MessagingSession ID)

> **Note:** Standard context variables (`RoutableId`, `CaseId`) do NOT unlock authentication-gated topics. Injecting them does not satisfy `User_Authentication` flows. However, **custom boolean auth-state variables** (e.g., `Verified_Check`) CAN bypass the authentication flow — inject the boolean variable as `true` via `contextVariables` to test post-auth business topics directly.

See [context-vars-test-spec.yaml](../assets/context-vars-test-spec.yaml) for a dedicated template.

## B1.8: Metrics

Metrics add platform quality scoring to test cases. Specify as a flat list of metric names in the YAML.

**YAML syntax:**
```yaml
metrics:
  - coherence
  - instruction_following
  - output_latency_milliseconds
```

**Available metrics (observed behavior from IRIS testing, 2026-02-09):**

| Metric | Score Range | Status | Notes |
|--------|-------------|--------|-------|
| `coherence` | 1-5 | ✅ Works | Scores 4-5 for clear responses. Recommended. |
| `completeness` | 1-5 | ⚠️ Misleading | Penalizes triage/routing agents for "not solving" — skip for routing agents. |
| `conciseness` | 1-5 | 🔴 Broken | Returns score=0, empty explanation. Platform bug. |
| `instruction_following` | 0-1 | ⚠️ Threshold bug | Labels "FAILURE" at score=1 when explanation says "follows perfectly." |
| `output_latency_milliseconds` | Raw ms | ✅ Works | No pass/fail — useful for performance baselining. |

**Recommendation:** Use `coherence` + `output_latency_milliseconds` for baseline quality. Skip `conciseness` (broken) and `completeness` (misleading for routing agents).

## B1.9: Custom Evaluations (⚠️ Spring '26 Bug)

Custom evaluations allow JSONPath-based assertions on action inputs and outputs — e.g., "verify the action received `supportPath = 'Field Support'`."

**YAML syntax:**
```yaml
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

**Evaluation types:**
- `string_comparison`: `equals`, `contains`, `startswith`, `endswith`
- `numeric_comparison`: `equals`, `greater_than`, `less_than`, `greater_than_or_equal`, `less_than_or_equal`

**Building JSONPath expressions:**
1. Run tests with `--verbose` to see `generatedData.invokedActions`
2. Parse the stringified JSON (it's `"[[{...}]]"`, not a parsed array)
3. Common paths: `$.generatedData.invokedActions[0][0].function.input.[field]`

> **⚠️ BLOCKED — Spring '26 Platform Bug:** Custom evaluations with `isReference: true` cause the server to return "RETRY" status. The results API crashes with `INTERNAL_SERVER_ERROR`. This is server-side (confirmed via direct `curl`). **Workaround:** Use `expectedOutcome` (LLM-as-judge) or the Testing Center UI until patched.

See [custom-eval-test-spec.yaml](../assets/custom-eval-test-spec.yaml) for a dedicated template.
