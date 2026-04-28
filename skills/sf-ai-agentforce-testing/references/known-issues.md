<!-- Parent: sf-ai-agentforce-testing/SKILL.md -->

# Known Issues & CLI Bugs

> **Last Updated**: 2026-02-11 | **Tested With**: sf CLI v2.118.16+

## RESOLVED: `sf agent test create` MasterLabel Error

**Status**: 🟢 RESOLVED — Add `name:` field to YAML spec

**Error**: `Required fields are missing: [MasterLabel]`

**Root Cause**: The YAML spec must include a `name:` field at the top level, which maps to `MasterLabel` in the `AiEvaluationDefinition` XML. Our templates previously omitted this field.

**Fix**: Add `name:` to the top of your YAML spec:
```yaml
name: "My Agent Tests"    # ← This was the missing field
subjectType: AGENT
subjectName: My_Agent
```

**If you still encounter issues**:
1. ✅ Use interactive `sf agent generate test-spec` wizard (interactive-only, no CLI flags)
2. ✅ Create tests via Salesforce Testing Center UI
3. ✅ Deploy XML metadata directly
4. ✅ **Use Phase A (Agent Runtime API) instead** — bypasses CLI entirely

## MEDIUM: Interactive Mode Not Scriptable

**Status**: 🟡 Blocks CI/CD automation

**Issue**: `sf agent generate test-spec` only works interactively.

**Workaround**: Use Python scripts in `hooks/scripts/` or Phase A multi-turn templates.

## MEDIUM: YAML vs XML Format Discrepancy

**Key Mappings**:
| YAML Field | XML Element / Assertion Type |
|------------|------------------------------|
| `expectedTopic` | `topic_assertion` |
| `expectedActions` | `actions_assertion` |
| `expectedOutcome` | `output_validation` |
| `contextVariables` | `contextVariable` (`variableName` / `variableValue`) |
| `customEvaluations` | `string_comparison` / `numeric_comparison` (`parameter`) |
| `metrics` | `expectation` (name only, no expectedValue) |

## LOW: BotDefinition Not Always in Tooling API

**Status**: 🟡 Handled automatically

**Issue**: In some org configurations, `BotDefinition` is not queryable via the Tooling API but works via the regular Data API (`sf data query` without `--use-tooling-api`).

**Fix**: `agent_discovery.py live` now has automatic fallback — if the Tooling API returns no results for BotDefinition, it retries with the regular API.

## LOW: `--use-most-recent` Not Implemented on `test results`

**Status**: 🟡 Confirmed broken on v2.123.1 (also broken on v2.108.6)

**Issue**: The `--use-most-recent` flag is documented in `sf agent test results --help` (appears in description and examples) but the flag parser does NOT accept it — returns "Nonexistent flag" error. This is a Salesforce CLI bug where the help text advertises a flag that was never wired into the command.

**Workaround**: Use `--job-id` explicitly with `test results`, or use `sf agent test resume --use-most-recent` instead (that command's flag works correctly as of v2.123.1).

**Scope**: Only affects `sf agent test results`. The `--use-most-recent` flag works correctly on `sf agent test resume`.

## CRITICAL: Custom Evaluations RETRY Bug (Spring '26)

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

## MEDIUM: `conciseness` Metric Returns Score=0

**Status**: 🟡 Platform bug — metric evaluation appears non-functional

**Issue**: The `conciseness` metric consistently returns `score: 0` with an empty `metricExplainability` field across all test cases (Spring '26).

**Workaround**: Skip `conciseness` in metrics lists until platform patch.

## LOW: `instruction_following` FAILURE at Score=1

**Status**: 🟡 Threshold mismatch — score and label disagree

**Issue**: The `instruction_following` metric labels results as "FAILURE" even when `score: 1` and the explanation text says the agent "follows instructions perfectly." This appears to be a pass/fail threshold configuration error on the platform side.

**Workaround**: Use the numeric `score` value (0 or 1) for evaluation. Ignore the PASS/FAILURE label.

## HIGH: `instruction_following` Crashes Testing Center UI

**Status**: 🔴 Blocks Testing Center UI entirely — separate from threshold bug above

**Error**: `Unable to get test suite: No enum constant einstein.gpt.shared.testingcenter.enums.AiEvaluationMetricType.INSTRUCTION_FOLLOWING_EVALUATION`

**Scope**: The Testing Center UI (Setup → Agent Testing) throws a Java exception when opening **any** test suite that includes the `instruction_following` metric. The CLI (`sf agent test run`) works fine — only the UI rendering is broken.

**Workaround**: Remove `- instruction_following` from the YAML metrics list and redeploy the test spec via `sf agent test create --force-overwrite`.

**Note**: This is a **different bug** from the threshold mismatch above. The threshold bug affects score interpretation; this bug blocks the entire UI from loading.

**Discovered**: 2026-02-11 on sandbox (Spring '26).

## MEDIUM: Topic Hash Drift on Agent Republish

**Status**: 🟡 Affects all hardcoded promoted topic names

**Issue**: The runtime `developerName` hash suffix (e.g., `Escalation_16j9d687a53f890`) changes each time an agent is republished. Tests with hardcoded full runtime names break silently — `topic_assertion` reports `FAILURE` because the expected hash no longer matches.

**Mitigation**:
1. Use `localDeveloperName` for standard topics (framework resolves automatically)
2. For promoted topics, re-run the [discovery workflow](../references/topic-name-resolution.md#discovery-workflow) after each agent publish
3. Keep a topic name mapping file that gets updated as part of the publish-and-test cycle

## INFO: API vs CLI Action Visibility Gap

**Status**: ℹ️ Informational — affects multi-turn API testing results

**Issue**: The multi-turn Agent Runtime API may report `has_action_result: false` or omit action results for actions that actually executed. This happens because Agent Script agents embed action outputs within `Inform` text messages rather than returning separate `ActionResult` message types.

**Impact**: Multi-turn API test assertions for `action_invoked` may fail even when the action ran correctly. CLI `--verbose` output is authoritative for action verification.

**Workaround**: When API tests show missing actions, cross-validate with CLI `--verbose` results. For Agent Script agents, prefer `response_contains` checks over `action_invoked` assertions.
