# Validation History: sf-ai-agentscript

This file tracks the validation history of the sf-ai-agentscript skill. Validation agents are deployed to a test org to verify that documented patterns still work with current Salesforce releases.

## Latest Validation

| Status | Date | Version | Agents Deployed | Test Org |
|--------|------|---------|-----------------|----------|
| ✅ PASS | 2026-02-17 | v2.2.0 | 24/24 | AgentforceTesting |

## Validation Agent Results

### Tier 1: Original Agents (13) — Re-validated

| Agent | Pattern Tested | Publish | Duration | Notes |
|-------|----------------|---------|----------|-------|
| Val_Minimal_Syntax | Core block structure | ✅ PASS | 16s | config, system, start_agent, topic blocks |
| Val_Arithmetic_Ops | +/- operators | ✅ PASS | 11s | Addition and subtraction working |
| Val_Comparison_Ops | Comparison operators | ✅ PASS | 12s | ==, !=, <, <=, >, >=, and, or, not |
| Val_Variable_Scopes | @variables namespace | ✅ PASS | 9s | mutable string/number/boolean |
| Val_Topic_Transitions | @utils.transition | ✅ PASS | 12s | Permanent handoffs between topics |
| Val_Latch_Pattern | Boolean re-entry | ✅ PASS | 14s | Latch variable for topic re-entry |
| Val_Loop_Guard | Iteration protection | ✅ PASS | 12s | Counter-based loop guard |
| Val_Interpolation | Variable injection | ✅ PASS | 9s | {!@variables.x} in strings |
| Val_Action_Properties | Action property validity | ✅ PASS | 13s | NEGATIVE: confirms invalid properties don't work |
| Val_Before_Reasoning | before_reasoning lifecycle | ✅ PASS | 9s | Direct content under block (no instructions: wrapper) |
| Val_After_Reasoning | after_reasoning lifecycle | ✅ PASS | 9s | Direct content under block (no instructions: wrapper) |
| Val_Label_Property | label: property | ✅ PASS | 9s | NEGATIVE: confirms label is NOT valid on @utils.transition (v2.2.0: IS valid on target-backed actions — see Val_Action_Meta_Props) |
| Val_Always_Expect_Input | always_expect_input | ✅ PASS | 11s | NEGATIVE: confirms not implemented |

### Tier 2: New Agents (3) — v1.9.0 Patterns

| Agent | Pattern Tested | Publish | Duration | Notes |
|-------|----------------|---------|----------|-------|
| Val_Else_Nested_If | else: + nested if | ✅ PASS | 9s | NEGATIVE: else: with nested if does NOT compile (Approach 3 INVALID) |
| Val_Step_Guard | Step counter re-entry guard | ✅ PASS | 14s | Step variable guards topic selector re-routing |
| Val_Multiple_Available_When | Multiple available when clauses | ✅ PASS | 14s | POSITIVE: Multiple available when on same action IS valid |

**Total Duration**: ~183s (16 agents — Tier 1+2 only)

### Tier 3: Flow/Apex Integration Agents (6) — v2.1.0 Patterns

| Agent | Pattern Tested | Expected | Actual | Notes |
|-------|----------------|----------|--------|-------|
| Val_Apex_Bare_Output | Bare @InvocableMethod output naming | ✅ PASS | ❌ FAIL | NEGATIVE FINDING: bare List<String> without @InvocableVariable wrappers is INCOMPATIBLE |
| Val_Datetime_IO | `datetime` type in action I/O | ✅ PASS | ✅ PASS | datetime maps to lightning__dateTimeStringType |
| Val_Name_Mismatch | Wrong output name vs Apex field | ❌ FAIL | ❌ FAIL | Expected: "invalid output 'wrong_name'" — confirmed exact-match required |
| Val_Partial_Output | Subset of target outputs declared | ✅ PASS | ✅ PASS | Can declare fewer outputs than the Apex class exposes |
| Val_No_Outputs | Inputs-only action (no outputs block) | ❌ FAIL | ❌ FAIL | Expected: "Internal Error" — outputs block specifically required |
| Val_Level1_Only | Level 1 definition without Level 2 invocation | ✅ PASS | ✅ PASS | Action definitions without @actions.X invocations are valid |

**Apex Test Classes Deployed**: `BareOutputAction.cls` (bare List<String> return), `DateTimeAction.cls` (DateTime with @InvocableVariable wrappers)

### Tier 4: Action Metadata Properties Agents (2) — v2.2.0 Patterns

| Agent | Pattern Tested | Expected | Actual | Notes |
|-------|----------------|----------|--------|-------|
| Val_Action_Meta_Props | Action-level metadata: label (action+topic+I/O), require_user_confirmation, include_in_progress_indicator, progress_indicator_message | ✅ PASS | ✅ PASS | All properties valid on target-backed actions (apex://TestApexAction) |
| Val_IO_Meta_Props | I/O-level metadata: is_required, is_user_input, is_displayable, is_used_by_planner | ✅ PASS | ✅ PASS | All I/O properties valid on target-backed actions (apex://TestApexAction) |

**Root Cause of v1.3.0 False Negatives**: `Val_Action_Properties` only tested properties on `@utils.transition` (utility actions without targets). These properties ARE valid on action definitions with `target:` (Level 1 actions). The skill incorrectly generalized "not valid on transitions" → "not valid anywhere."

## TDD Findings (v2.2.0)

### Finding 10: `label:` is valid on action definitions, topics, and I/O fields ✅

- **Pattern**: `label:` property on topic block, action definition, input fields, and output fields
- **Result**: All compile and publish successfully on `apex://TestApexAction` target
- **Impact**: Corrected "Features NOT Valid" table in SKILL.md → renamed to "Feature Validity by Context"
- **Scope**: Valid on target-backed actions; still NOT valid on `@utils.transition` (Val_Action_Properties confirms)

### Finding 11: `require_user_confirmation`, `include_in_progress_indicator`, `progress_indicator_message` valid on target-backed actions ✅

- **Pattern**: All three properties on an action definition with `target: "apex://TestApexAction"`
- **Result**: Compile and publish successfully
- **Impact**: Updated Feature Validity table: valid on actions with targets, not on `@utils.transition`
- **Note**: `require_user_confirmation` compiles but runtime confirmation dialog does not trigger (Issue 6 still OPEN)

### Finding 12: `is_required` and `is_user_input` valid as input metadata properties ✅

- **Pattern**: `is_required: True` and `is_user_input: True` on action input definitions
- **Result**: Both compile and publish successfully
- **Impact**: Added Input Properties table to actions-reference.md; clarified reserved field names in SKILL.md

### Finding 13: `is_displayable` and `is_used_by_planner` valid as output metadata properties ✅

- **Pattern**: `is_displayable: False` and `is_used_by_planner: True` on action output definitions
- **Result**: Both compile and publish successfully
- **Impact**: `is_displayable` confirmed as standard name for `filter_from_agent` (alias relationship documented)

## TDD Findings (v2.1.0)

### Finding 4: Bare `@InvocableMethod` is INCOMPATIBLE with Agent Script ❌

- **Pattern**: Apex class returning `List<String>` directly (no `@InvocableVariable` wrapper classes)
- **Rounds Tested**: 3 iterations — input name `name` (invalid), input name `input` (invalid), no inputs block (Internal Error)
- **Root Cause**: The framework requires `@InvocableVariable` annotations to discover bindable parameter names. Without wrapper classes, no I/O name can be matched.
- **Impact**: Added "Bare @InvocableMethod Pattern (NOT Compatible)" warning to SKILL.md and actions-reference.md
- **Rule**: Always use `@InvocableVariable` wrapper classes when targeting Apex from Agent Script

### Finding 5: `datetime` type works in action I/O ✅

- **Pattern**: `startDateTime: datetime` and `endDateTime: datetime` in action inputs/outputs targeting Apex `DateTime` params
- **Result**: Publishes successfully; maps to `lightning__dateTimeStringType` in Lightning type system
- **Impact**: Added `datetime` → `lightning__dateTimeStringType` to SKILL.md type mapping tables

### Finding 6: I/O names must exactly match `@InvocableVariable` field names ❌

- **Pattern**: Output name `wrong_name` when Apex class has `@InvocableVariable public String outputText`
- **Error**: `"invalid output 'wrong_name'"` at server-side compilation
- **Impact**: Added I/O Name Matching Rules section to SKILL.md and actions-reference.md with exact-match table

### Finding 7: Partial output declaration is valid ✅

- **Pattern**: Declaring only `outputText: string` when Apex class also has `inputText: string` as output
- **Result**: Publishes successfully — subset of outputs is valid
- **Impact**: Added "Partial Output Pattern" documentation to SKILL.md

### Finding 8: `outputs:` block specifically required (not just "I/O") ❌

- **Pattern**: Action with `inputs:` block but no `outputs:` block
- **Error**: `"Internal Error, try again later"` at server-side compilation
- **Impact**: Updated Issue 15 in known-issues.md — `outputs:` block is specifically required. `inputs:` alone is NOT sufficient.

### Finding 9: Level 1 without Level 2 is valid ✅

- **Pattern**: Action definition in topic `actions:` block with `target:`, `inputs:`, `outputs:` but NO `@actions.X` invocation in `reasoning.actions:`
- **Result**: Publishes successfully — action definitions exist for the planner without explicit invocation
- **Impact**: Added "Level 1 Without Level 2 Is Valid" note to SKILL.md Two-Level Action System section

## TDD Findings (v1.9.0)

### Finding 1: `else:` + nested `if` does NOT compile ❌

- **Pattern**: `else:` block containing a nested `if` statement (SKILL.md Approach 3)
- **Error**: `Unexpected 'if'` at the nested if line, cascading `Unexpected '@utils'`, `Missing colon`, `Invalid syntax`
- **Impact**: SKILL.md Approach 3 must be removed or marked INVALID
- **Workaround**: Use compound conditions (`if A and B:`) or sequential ifs
- **Note**: Local LSP validator PASSES this pattern — only server-side compiler rejects it

### Finding 2: `<>` not-equal operator does NOT compile ❌

- **Pattern**: `if @variables.x <> "value":` using `<>` as not-equal
- **Error**: `Unexpected '>' 44:29` — parser does not recognize `<>` as a token
- **Impact**: Remove `<>` from SKILL.md operator table; only `!=` is valid
- **Workaround**: Use `!=` operator (already validated in Val_Comparison_Ops)

### Finding 3: Multiple `available when` clauses ARE valid ✅

- **Pattern**: Two `available when` clauses on the same action
- **Result**: Compiles and publishes successfully
- **Impact**: SKILL.md constraint "One `available when` per action" is WRONG — remove it
- **Impact**: Common Issues entry "Duplicate 'available when' clause" is WRONG — remove it
- **Impact**: multi-step-workflow template pattern is CORRECT as-is

## Patterns Validated

Each validation agent tests specific patterns documented in SKILL.md:

1. **Val_Minimal_Syntax** → Core Syntax
   - `config` block with agent_name, agent_label, default_agent_user
   - `system` block with messages and instructions
   - `start_agent` block with reasoning and actions
   - `topic` block with description and reasoning

2. **Val_Arithmetic_Ops** → Expression Operators
   - Addition: `@variables.counter + 1`
   - Subtraction: `@variables.counter - 1`
   - Note: `*`, `/`, `%` are NOT supported

3. **Val_Comparison_Ops** → Expression Operators
   - Equality: `==`, not-equal: `!=`
   - Comparisons: `<`, `<=`, `>`, `>=`
   - Logical: `and`, `or`, `not`
   - Note: `<>` is NOT valid (see Finding 2)

4. **Val_Variable_Scopes** → Variable Namespaces
   - `mutable string` with default value
   - `mutable number` with default value
   - `mutable boolean` with default value
   - `set @variables.x = value` assignment

5. **Val_Topic_Transitions** → Topic Transitions
   - `@utils.transition to @topic.X` (permanent handoff)
   - Multi-step topic chains

6. **Val_Latch_Pattern** → Production Gotchas
   - Boolean flag initialization
   - Setting latch on entry
   - Checking latch in topic selector
   - Clearing latch on completion

7. **Val_Loop_Guard** → Production Gotchas
   - Iteration counter pattern
   - `available when` guard clause
   - Exit condition on max iterations

8. **Val_Interpolation** → Instruction Syntax
   - Basic interpolation: `{!@variables.x}`
   - Multiple variables in string
   - Conditional interpolation: `{!value if condition else alt}`

9. **Val_Action_Properties** → Action Properties on @utils.transition (NEGATIVE)
   - CONFIRMED NOT VALID on `@utils.transition`: require_user_confirmation, include_in_progress_indicator, output_instructions, progress_indicator_message
   - CONFIRMED VALID: description only (on @utils.transition)
   - **CORRECTED (v2.2.0)**: These properties ARE valid on action definitions with `target:` — see Val_Action_Meta_Props (#23)

10. **Val_Before_Reasoning** → Lifecycle Hooks
    - Content directly under `before_reasoning:` block
    - NO `instructions:` wrapper required

11. **Val_After_Reasoning** → Lifecycle Hooks
    - Content directly under `after_reasoning:` block
    - NO `instructions:` wrapper required

12. **Val_Label_Property** → label: on @utils.transition (NEGATIVE, scope-limited)
    - CONFIRMED NOT VALID on `@utils.transition` actions (v1.3.0)
    - **CORRECTED (v2.2.0)**: `label:` IS valid on target-backed action definitions, topics, and I/O fields — see Val_Action_Meta_Props (#23)

13. **Val_Always_Expect_Input** → Unimplemented Features (NEGATIVE)
    - CONFIRMED NOT VALID: `always_expect_input:` property

14. **Val_Else_Nested_If** → if/else Nesting (NEGATIVE)
    - CONFIRMED NOT VALID: `else:` block with nested `if` statement
    - CONFIRMED VALID: Compound conditions and sequential ifs as alternatives

15. **Val_Step_Guard** → Topic Re-Entry Protection
    - Step counter in `start_agent` guards topic selector
    - `workflow_active` boolean flag pattern
    - `available when` on step completion

16. **Val_Multiple_Available_When** → Action Guards
    - CONFIRMED VALID: Multiple `available when` clauses on same action
    - DISPROVES: "One available when per action" constraint in SKILL.md

17. **Val_Apex_Bare_Output** → Bare @InvocableMethod (NEGATIVE)
    - CONFIRMED NOT COMPATIBLE: Bare `List<String>` return without `@InvocableVariable` wrappers
    - 3 rounds tested: input name `name` (invalid), `input` (invalid), no inputs (Internal Error)
    - Rule: Always use `@InvocableVariable` wrapper classes for Agent Script actions

18. **Val_Datetime_IO** → DateTime Type in Action I/O
    - CONFIRMED VALID: `datetime` type in action inputs/outputs
    - Maps to `lightning__dateTimeStringType` in Lightning type system
    - Apex target: `DateTimeAction.cls` with `DateTime` wrapper params

19. **Val_Name_Mismatch** → I/O Name Matching (NEGATIVE)
    - CONFIRMED: I/O names must exactly match `@InvocableVariable` field names
    - Output name `wrong_name` vs Apex field `outputText` → `"invalid output 'wrong_name'"`

20. **Val_Partial_Output** → Partial Output Declaration
    - CONFIRMED VALID: Declaring subset of target outputs is acceptable
    - Declared `outputText` only from `TestApexAction` (which has both input and output wrappers)

21. **Val_No_Outputs** → Inputs-Only Action (NEGATIVE)
    - CONFIRMED: `outputs:` block is specifically required for publish
    - Action with `inputs:` but no `outputs:` → `"Internal Error, try again later"`
    - Validates Issue 15 nuance: outputs specifically required, not just "I/O"

22. **Val_Level1_Only** → Level 1 Without Level 2
    - CONFIRMED VALID: Action definition in topic `actions:` block without `@actions.X` in reasoning
    - Level 1 definitions (target + I/O) without Level 2 invocations publish successfully

23. **Val_Action_Meta_Props** → Action Metadata Properties (POSITIVE)
    - CONFIRMED VALID: `label:` on action definitions, topics, and I/O fields
    - CONFIRMED VALID: `require_user_confirmation: True` on target-backed actions (runtime Issue 6)
    - CONFIRMED VALID: `include_in_progress_indicator: True` on target-backed actions
    - CONFIRMED VALID: `progress_indicator_message:` on target-backed actions (both flow:// and apex://)
    - CORRECTS v1.3.0: Val_Action_Properties only tested @utils.transition (limited property support)

24. **Val_IO_Meta_Props** → I/O Metadata Properties (POSITIVE)
    - CONFIRMED VALID: `is_required: True` on action inputs
    - CONFIRMED VALID: `is_user_input: True` on action inputs (LLM extracts from conversation)
    - CONFIRMED VALID: `is_displayable: False` on action outputs (alias for `filter_from_agent`)
    - CONFIRMED VALID: `is_used_by_planner: True` on action outputs

## Validation Command

```bash
# Navigate to validation directory
cd sf-ai-agentscript/validation

# Deploy metadata first
sf project deploy start \
  --source-dir validation-agents/force-app/main/default/aiAuthoringBundles \
  --target-org AgentforceTesting --json

# Publish each agent
for agent in Val_Minimal_Syntax Val_Arithmetic_Ops Val_Comparison_Ops Val_Variable_Scopes \
  Val_Topic_Transitions Val_Latch_Pattern Val_Loop_Guard Val_Interpolation \
  Val_Action_Properties Val_Before_Reasoning Val_After_Reasoning \
  Val_Label_Property Val_Always_Expect_Input Val_Else_Nested_If \
  Val_Step_Guard Val_Multiple_Available_When \
  Val_Apex_Bare_Output Val_Datetime_IO Val_Name_Mismatch \
  Val_Partial_Output Val_No_Outputs Val_Level1_Only \
  Val_Action_Meta_Props Val_IO_Meta_Props; do
  sf agent publish authoring-bundle --api-name "$agent" --target-org AgentforceTesting --json
done
```

## Test Org Configuration

| Property | Value |
|----------|-------|
| **Target Org Alias** | `AgentforceTesting` |
| **Einstein Agent User** | `multistepworkflows@00dak00000gdhgd1068670160.ext` |
| **API Version** | 65.0 |
| **Instance URL** | `dak00000gdhgdeay-dev-ed.develop.my.salesforce.com` |

## History

| Date | Version | Status | Passed | Failed | Notes |
|------|---------|--------|--------|--------|-------|
| 2026-02-17 | v2.2.0 | ✅ PASS | 24/24 | 0 | 2 new action metadata agents (Val_Action_Meta_Props, Val_IO_Meta_Props). Findings: label valid on actions/topics/I/O, require_user_confirmation/include_in_progress_indicator/progress_indicator_message valid on target-backed actions, is_required/is_user_input valid on inputs, is_displayable/is_used_by_planner valid on outputs. Root cause: v1.3.0 only tested @utils.transition |
| 2026-02-17 | v2.1.0 | ✅ PASS | 22/22 | 0 | 6 new Flow/Apex integration agents. Findings: bare @InvocableMethod INCOMPATIBLE, datetime type WORKS, I/O names must exact-match, partial outputs VALID, outputs block REQUIRED, Level 1 without Level 2 VALID |
| 2026-02-14 | v1.9.0 | ✅ PASS | 16/16 | 0 | 3 new agents + re-validation against AgentforceTesting. Found: else+nested-if INVALID, <> INVALID, multiple available-when VALID |
| 2026-01-20 | v1.1.0 | ✅ PASS | 8/8 | 0 | Initial validation framework implementation (R6-Agentforce-SandboxFull) |

## Next Validation Due

**2026-03-19** (30 days from last validation)

---

## Troubleshooting

### If Validation Fails

1. **Check the error message** - Salesforce will indicate what syntax changed
2. **Update SKILL.md** - Document the new constraint or syntax requirement
3. **Fix the validation agent** - Update to use correct syntax
4. **Re-run validation** - Ensure all agents pass again
5. **Update this file** - Log the issue and resolution in History

### Common Issues

| Issue | Cause | Resolution |
|-------|-------|------------|
| `Nonexistent flag: --source-dir` | CLI version change | Use `sf agent publish authoring-bundle --api-name` instead |
| `Unknown error` on publish | Usually successful | Check full JSON output for actual status |
| `Default agent user not found` | Wrong org or user inactive | Query target org for Einstein Agent User |
| `AgentCompilationError` on deploy | Server-side compiler stricter than LSP | Fix agent, redeploy. Note: LSP may pass patterns the server rejects |
| `Unexpected 'if'` inside else: | else: + nested if not valid | Use compound conditions or sequential ifs |
| `Unexpected '>'` in condition | `<>` not-equal not valid | Use `!=` instead |
| jq parse errors on `--json` output | sf CLI emits control chars | Pipe through `tr -d '\000-\037'` before jq |
