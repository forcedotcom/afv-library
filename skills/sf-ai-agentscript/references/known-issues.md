<!-- Parent: sf-ai-agentscript/SKILL.md -->
# Known Issues Tracker

> Unresolved platform bugs, limitations, and edge cases that affect Agent Script development. Unlike the "Common Issues & Fixes" table in SKILL.md (which covers resolved troubleshooting), this file tracks **open platform issues** where the root cause is in Salesforce, not in user code.

---

## Issue Template

```markdown
## Issue N: [Title]
- **Status**: OPEN | RESOLVED | WORKAROUND
- **Date Discovered**: YYYY-MM-DD
- **Affects**: [Component/workflow affected]
- **Symptom**: What the user sees
- **Root Cause**: Why it happens (if known)
- **Workaround**: How to get around it
- **Open Questions**: What we still don't know
- **References**: Links to related docs, issues, or discussions
```

---

## Open Issues

### Issue 1: Agent test files block `force-app` deployment
- **Status**: WORKAROUND
- **Date Discovered**: 2026-01-20
- **Affects**: `sf project deploy start --source-dir force-app`
- **Symptom**: Deployment hangs for 2+ minutes or times out when `AiEvaluationDefinition` metadata files exist under `force-app/`. The deploy may eventually succeed but with excessive wait times.
- **Root Cause**: `AiEvaluationDefinition` metadata type triggers server-side processing that blocks the deployment pipeline. The metadata type is not well-suited for source-dir deploys.
- **Workaround**: Move test definitions to a separate directory outside the main deploy path, or use `--metadata` flag to deploy specific types instead of `--source-dir`.
  ```bash
  # Instead of:
  sf project deploy start --source-dir force-app -o TARGET_ORG

  # Use targeted deployment:
  sf project deploy start --metadata AiAuthoringBundle:MyAgent -o TARGET_ORG
  ```
- **Open Questions**: Will Salesforce optimize `AiEvaluationDefinition` deploy performance in a future release?

---

### Issue 2: `sf agent publish` fails with namespace prefix on `apex://` targets
- **Status**: OPEN
- **Date Discovered**: 2026-02-01
- **Affects**: Namespaced orgs using `apex://` action targets
- **Symptom**: `sf agent publish authoring-bundle` fails with "invocable action does not exist" error, despite the Apex class being deployed and confirmed via SOQL query.
- **Root Cause**: Unknown. Unclear whether `apex://ClassName` or `apex://ns__ClassName` is the correct format in namespaced orgs. The publish step may not resolve namespace prefixes the same way as standard metadata deployment.
- **Workaround**: None confirmed. Potential approaches to try:
  1. Use `apex://ns__ClassName` format
  2. Use unmanaged classes (no namespace)
  3. Wrap Apex in a Flow and use `flow://` target instead
- **Open Questions**:
  - Does `apex://ns__ClassName` work?
  - Is this a bug or by-design limitation?
  - Does the same issue affect `flow://` targets with namespaced Flows?

---

### Issue 3: Agent packaging workflow unclear
- **Status**: OPEN
- **Date Discovered**: 2026-02-05
- **Affects**: ISV partners, AppExchange distribution
- **Symptom**: No documented way to package Agent Script agents for distribution. The `AiAuthoringBundle` metadata type has no known packaging equivalent to `BotTemplate`.
- **Root Cause**: Agent Script is newer than the packaging system. Salesforce has not published ISV packaging guidance for `.agent` files.
- **Workaround**: None. Current options:
  1. Distribute as source code (customer deploys manually)
  2. Use unlocked packages (may include `.agent` files but subscriber customization is untested)
  3. Convert to Agent Builder UI (GenAiPlannerBundle) for packaging — loses Agent Script benefits
- **Open Questions**:
  - Will `AiAuthoringBundle` be supported in 2GP managed packages?
  - Can subscribers modify `.agent` files post-install?
  - Is there a roadmap item for Agent Script packaging?

---

### Issue 4: Legacy `sf bot` CLI commands incompatible with Agent Script
- **Status**: OPEN
- **Date Discovered**: 2026-01-25
- **Affects**: Users migrating from Einstein Bots to Agent Script
- **Symptom**: Old `sf bot` and `sf bot version` commands were removed in sf CLI v2 — these commands no longer exist, not just "don't recognize Agent Script". Running any `sf bot` command returns "Command not found".
- **Root Cause**: The `sf bot` command family was deprecated and removed in sf CLI v2. It targeted `BotDefinition`/`BotVersion` metadata types. Agent Script uses `AiAuthoringBundle`, a completely separate metadata structure.
- **Workaround**: Use `sf agent` commands exclusively for Agent Script:
  ```bash
  # ❌ Old commands (don't work with Agent Script):
  sf bot list
  sf bot version list

  # ✅ New commands (for Agent Script):
  sf project retrieve start --metadata Agent:MyAgent
  sf agent validate authoring-bundle --api-name MyAgent
  sf agent publish authoring-bundle --api-name MyAgent
  ```
- **Open Questions**: Will Salesforce unify the `sf bot` and `sf agent` command families?

---

### Issue 5: Agent tests cannot be deployed/retrieved for source control
- **Status**: OPEN
- **Date Discovered**: 2026-02-06
- **Affects**: CI/CD pipelines, test version control
- **Symptom**: Tests created in the Agent Testing Center UI cannot be retrieved via `sf project retrieve start`. Old test XML format references `bot`/`version` fields that don't exist in Agent Script. No metadata type or CLI command exists for new-style agent tests.
- **Root Cause**: The Agent Testing Center was originally built for Einstein Bots. The test metadata schema hasn't been updated for Agent Script's `AiAuthoringBundle` structure. The `AiEvaluationDefinition` type exists but doesn't correspond to the Testing Center's UI-created tests.
- **Workaround**:
  1. Use YAML test spec files managed in source control (see `/sf-ai-agentforce-testing` skill)
  2. Treat UI-created tests as ephemeral / org-specific
  3. Use the Connect API directly to run tests programmatically
- **Open Questions**:
  - Will a new metadata type be introduced for Agent Script tests?
  - Can `AiEvaluationDefinition` be used with Agent Script agents?
  - Is there a roadmap for test portability?
- **References**: See `references/custom-eval-investigation.md` in `sf-ai-agentforce-testing` for related findings on custom evaluation data structure issues.

---

### Issue 6: `require_user_confirmation` does not trigger confirmation dialog
- **Status**: OPEN
- **Date Discovered**: 2026-02-14
- **Date Updated**: 2026-02-17 (TDD v2.2.0 — confirmed compiles on target-backed actions)
- **Affects**: Actions with `require_user_confirmation: True`
- **Symptom**: Setting `require_user_confirmation: True` on an action definition does not produce a user-facing confirmation dialog before execution. The action executes immediately without user confirmation.
- **Root Cause**: The property is parsed and saved without error, but the runtime does not implement the confirmation UX for Agent Script actions. It may only work for GenAiPlannerBundle actions in the Agent Builder UI.
- **TDD Update (v2.2.0)**: Property compiles and publishes successfully on action definitions with `target:` (both `flow://` and `apex://`). Val_Action_Meta_Props confirms compilation. The issue is purely runtime — the confirmation dialog never appears. Property is NOT valid on `@utils.transition` actions (Val_Action_Properties, v1.3.0).
- **Workaround**: Implement confirmation logic manually using a two-step pattern: (1) LLM asks user to confirm, (2) action has `available when @variables.user_confirmed == True` guard.
- **Open Questions**: Will this be implemented for AiAuthoringBundle in a future release?

---

### Issue 7: OOTB Asset Library actions may ship without proper quote wrapping
- **Status**: WORKAROUND
- **Date Discovered**: 2026-02-14
- **Affects**: Out-of-the-box (OOTB) actions from the Agentforce Asset Library
- **Symptom**: Some pre-built actions from the Asset Library have input parameters that are not properly quote-wrapped, causing parse errors when referenced in Agent Script.
- **Root Cause**: Asset Library actions were designed for the Agent Builder UI path, which handles quoting differently than Agent Script's text-based syntax.
- **Workaround**: When importing Asset Library actions, manually verify all input parameter names in the action definition. If a parameter name contains special characters or colons (e.g., `Input:query`), wrap it in quotes: `with "Input:query" = ...`
- **Open Questions**: Will Salesforce update Asset Library actions for Agent Script compatibility?

---

### Issue 8: Lightning UI components do not render on new planner
- **Status**: OPEN
- **Date Discovered**: 2026-02-14
- **Affects**: Agents using Lightning Web Components for rich UI rendering
- **Symptom**: Custom Lightning UI components referenced in agent actions do not render in the chat interface when using the newer planner engine. Components that worked with the legacy planner appear as plain text or are silently dropped.
- **Root Cause**: The newer planner (Atlas/Daisy) does not support the same Lightning component rendering pipeline as the legacy Java planner.
- **Workaround**: None for rich UI. Fall back to text-based responses or use the legacy planner if Lightning component rendering is critical.
- **Open Questions**: Is Lightning UI rendering on the roadmap for the new planner?

---

### Issue 9: Large action responses cause data loss from state
- **Status**: OPEN
- **Date Discovered**: 2026-02-14
- **Affects**: Actions returning large payloads (>50KB response data)
- **Symptom**: When an action returns a large response payload, subsequent variable access may return null or incomplete data. State appears to lose previously stored values.
- **Root Cause**: Action output data accumulates in conversation context without compaction. Very large responses may push earlier state data beyond the context window boundary.
- **Workaround**: Design Flow/Apex actions to return minimal, summarized data. Use `filter_from_agent: True` on outputs the LLM doesn't need. Avoid `SELECT *` patterns in data retrieval.
- **Open Questions**: Will automatic context compaction be added for action outputs?

---

### Issue 10: Agent fails if user lacks permission for ANY action
- **Status**: OPEN
- **Date Discovered**: 2026-02-14
- **Affects**: Agents with actions targeting secured resources
- **Symptom**: If the running user (Einstein Agent User or session user) lacks permission to execute ANY action defined in the agent — even actions in other topics — the entire agent may fail with a permission error rather than gracefully skipping the unauthorized action.
- **Root Cause**: The planner appears to validate permissions for all registered actions at startup, not lazily per-topic.
- **Workaround**: For **Service Agents**: Ensure the Einstein Agent User has both the `AgentforceServiceAgentUser` system PS AND a custom `{AgentName}_Access` PS with `<classAccesses>` for ALL Apex classes across all topics. Do NOT rely on the auto-generated `NextGen_{AgentName}_Permissions` — it is often incomplete (ORM1 testing: 3/4 classes, missing `ShipmentTracker`). For **Employee Agents**: Ensure each employee user has the custom PS assigned. See [agent-user-setup.md](agent-user-setup.md) for the full provisioning workflow and permission set XML template. Alternatively, split agents by permission boundary.
- **Open Questions**: Will the planner support lazy permission checking in a future release?

---

### Issue 11: Welcome/error interpolation written as a quoted string renders literally
- **Status**: WORKAROUND
- **Date Discovered**: 2026-02-14
- **Affects**: `system.messages.welcome` / `system.messages.error` when `{!...}` interpolation is authored inline
- **Symptom**: A message such as `welcome: "Hi {!@variables.user_preferred_name}!"` can display the `{!...}` token literally instead of rendering the variable value.
- **Root Cause**: System messages use a template-style rendering path for interpolation. Plain quoted string form is reliable for static text, but dynamic welcome/error messages should be authored in template/block form.
- **Workaround**: Replace quoted interpolation with block-form template syntax.

  **❌ Wrong**
  ```yaml
  system:
    messages:
      welcome: "Hi {!@variables.user_preferred_name}!"
      error: "Sorry, something went wrong."
  ```

  **✅ Correct**
  ```yaml
  system:
    messages:
      welcome: |
        Hi {!@variables.user_preferred_name}! How can I help?
      error: "Sorry, something went wrong."
  ```
- **Open Questions**: Should the validator auto-suggest template mode whenever `{!...}` appears on a quoted welcome/error line?

---

### Issue 12: System welcome/error messages are templates, not procedural instruction blocks
- **Status**: WORKAROUND
- **Date Discovered**: 2026-02-14
- **Affects**: `system.messages.welcome` / `system.messages.error` personalization
- **Symptom**: Authors sometimes expect welcome/error messages to behave like `reasoning.instructions: ->`, including conditional logic or step-by-step instruction resolution.
- **Root Cause**: `system.messages` supports simple template rendering, not the procedural control flow available in topic `instructions: ->` blocks.
- **Workaround**: Keep welcome/error messages to static text or direct variable references. Move `if` / `else`, `run`, or richer personalization logic into the first topic's `reasoning.instructions: ->` block.
- **Open Questions**: Will system messages eventually gain richer templating beyond direct variable injection?

---

### Issue 13: Related agent nodes fail in SOMA configuration
- **Status**: OPEN
- **Date Discovered**: 2026-02-14
- **Affects**: Multi-agent configurations using `related_agent` references
- **Symptom**: SOMA (Same Org Multi-Agent) configurations that reference related agents via node declarations fail with "Node does not have corresponding topic" error at runtime.
- **Root Cause**: The planner resolves agent references at compile time but may not correctly map cross-agent topic references when agents are deployed independently.
- **Workaround**: Use `@topic.X` delegation within the same agent instead of cross-agent references. For true multi-agent scenarios, use the `@utils.escalate` or connection-based handoff patterns.
- **Open Questions**: Will SOMA node resolution be fixed in a future planner update?

---

### Issue 14: Previously valid OpenAPI schemas now fail validation
- **Status**: OPEN
- **Date Discovered**: 2026-02-14
- **Affects**: External Service actions using OpenAPI 3.0 schemas
- **Symptom**: OpenAPI schemas that previously passed validation and worked with `externalService://` targets now fail with schema validation errors after org upgrades. No changes were made to the schema files.
- **Root Cause**: Salesforce tightened OpenAPI schema validation rules in recent releases. Schemas that were previously accepted with minor deviations (e.g., missing `info.version`, non-standard extensions) are now rejected.
- **Workaround**: Re-validate schemas against strict OpenAPI 3.0 spec. Common fixes: ensure `info.version` is present, remove non-standard `x-` extensions, verify all `$ref` paths resolve correctly.
- **Open Questions**: Will Salesforce publish the exact validation rules that changed?

---

### Issue 15: Action definitions without `outputs:` block cause "Internal Error" on publish
- **Status**: WORKAROUND
- **Date Discovered**: 2026-02-16
- **Date Updated**: 2026-02-17 (TDD v2.1.0 — clarified outputs specifically required)
- **Affects**: `sf agent publish authoring-bundle` with topic-level action definitions
- **Symptom**: `sf agent publish` returns "Internal Error, try again later" when topic-level action definitions have `target:` but no `outputs:` block. Also triggered when using `inputs:` without `outputs:`. LSP + CLI validation both PASS — error is server-side compilation only.
- **Root Cause**: The server-side compiler needs output type contracts to resolve `flow://` and `apex://` action targets. Without an `outputs:` block, the compiler cannot generate return bindings. The `inputs:` block alone is NOT sufficient — `outputs:` is specifically required.
- **Workaround**: Always include an `outputs:` block in action definitions. The `inputs:` block can be omitted if the target has no required inputs (the LLM will still slot-fill via `with param=...`), but `outputs:` must always be present.
- **TDD Validation**: `Val_No_Outputs` (v2.1.0) confirms inputs-only action definition → "Internal Error". `Val_Partial_Output` confirms declaring a subset of outputs IS valid. `Val_Apex_Bare_Output` confirms bare `@InvocableMethod` without wrapper classes also triggers this error.
- **Cross-reference**: See also Issue 27 — a related but distinct error occurs when action I/O is present but doesn't match ALL invocable target parameters.
- **Open Questions**: Will the compiler be updated to infer I/O schemas from the target's metadata?

---

### Issue 17: `EinsteinAgentApiChannel` surfaceType not available on all orgs
- **Status**: OPEN
- **Date Discovered**: 2026-02-16
- **Affects**: Agent Runtime API channel enablement via `plannerSurfaces` metadata
- **Symptom**: Adding `plannerSurfaces` with `surfaceType: EinsteinAgentApiChannel` causes deployment errors on some orgs. Valid surfaceType values on tested orgs: `Messaging`, `CustomerWebClient`, `Telephony`, `NextGenChat`.
- **Root Cause**: The `EinsteinAgentApiChannel` surfaceType may require specific org features or licenses that are not universally available.
- **Workaround**: Use `CustomerWebClient` for Agent Runtime API / CLI testing. This surfaceType is available on all tested orgs and enables API access.
- **Open Questions**: Is `EinsteinAgentApiChannel` limited to specific editions or feature flags?

---

### Issue 18: `connection messaging:` only generates `Messaging` plannerSurface — `CustomerWebClient` dropped on every publish
- **Status**: OPEN
- **Date Discovered**: 2026-02-17
- **Affects**: Agent Builder Preview, Agent Runtime API testing, CLI testing (`sf agent test`, `sf agent preview`)
- **Symptom**: After `sf agent publish authoring-bundle`, the compiled GenAiPlannerBundle only contains a `Messaging` plannerSurface. `CustomerWebClient` is never auto-generated. Agent Builder Preview shows "Something went wrong. Refresh and try again." because it requires `CustomerWebClient`.
- **Root Cause**: The `connection messaging:` DSL block only generates a `Messaging` plannerSurface during compilation. There is no `connection customerwebclient:` DSL syntax — attempting it causes `ERROR_HTTP_404` on publish. The compiler has no mechanism to auto-generate `CustomerWebClient`.
- **Impact**: Every publish overwrites the GenAiPlannerBundle, dropping any manually-added `CustomerWebClient` surface. This requires a post-publish patch after EVERY publish.
- **Workaround — 6-Step Post-Publish Patch Workflow:**
  1. `sf agent publish authoring-bundle --api-name AgentName -o TARGET_ORG --json` → creates new version (e.g., v22)
  2. `sf project retrieve start --metadata "GenAiPlannerBundle:AgentName_vNN" -o TARGET_ORG --json` → retrieve compiled bundle
  3. Manually add second `<plannerSurfaces>` block to the XML with `<surfaceType>CustomerWebClient</surfaceType>` (copy the existing `Messaging` block, change surfaceType and surface fields)
  4. `sf agent deactivate --api-name AgentName -o TARGET_ORG` → deactivate agent (deploy fails while active)
  5. `sf project deploy start --metadata "GenAiPlannerBundle:AgentName_vNN" -o TARGET_ORG --json` → deploy patched bundle
  6. `sf agent activate --api-name AgentName -o TARGET_ORG` → reactivate agent
- **Patch XML Example:**
  ```xml
  <!-- Add this AFTER the existing Messaging plannerSurfaces block -->
  <plannerSurfaces>
      <adaptiveResponseAllowed>false</adaptiveResponseAllowed>
      <callRecordingAllowed>false</callRecordingAllowed>
      <outboundRouteConfigs>
          <escalationMessage>One moment while I connect you with a support specialist.</escalationMessage>
          <outboundRouteName>Route_from_Your_Agent</outboundRouteName>
          <outboundRouteType>OmniChannelFlow</outboundRouteType>
      </outboundRouteConfigs>
      <surface>SurfaceAction__CustomerWebClient</surface>
      <surfaceType>CustomerWebClient</surfaceType>
  </plannerSurfaces>
  ```
- **Note**: The `outboundRouteConfigs` should mirror the Messaging surface config. If no routing is configured, omit `outboundRouteConfigs`.
- **Note**: `outboundRouteName` in compiled XML does NOT need `flow://` prefix — the publisher strips it during compilation. Both forms work in production XML.
- **Validated on**: Production org, 2026-02-17

---

### Issue 19: Comments inside `if` blocks treated as empty body
- **Status**: OPEN
- **Date Discovered**: 2026-03-04
- **Affects**: `if`/`else` blocks in `instructions: ->`
- **Symptom**: An `if` block containing only comments (e.g., `# TODO`) compiles but produces an empty body at runtime. The parser strips comments during tokenization, and the resulting `INDENT → DEDENT` with no executable statements creates a no-op branch that silently swallows the conditional path.
- **Root Cause**: Comments are not executable statements in Agent Script. The parser treats a comment-only block identically to an empty block.
- **Workaround**: Always include at least one executable statement (`| text`, `run`, `set`, or `transition`) in every `if`/`else` block. Never use comment-only blocks as placeholders.
  ```yaml
  # ❌ WRONG — empty body after comment stripping
  if @variables.premium == True:
    # TODO: add premium greeting

  # ✅ CORRECT — executable statement present
  if @variables.premium == True:
    | Welcome back, valued premium member!
  ```
- **Open Questions**: Will the compiler emit a warning for empty `if` bodies?

---

### Issue 20: GenAiPlannerBundle / AiAuthoringBundle / GenAiFunction NOT SOQL-queryable
- **Status**: WORKAROUND (by design — metadata types, not sObjects)
- **Date Discovered**: 2026-03-04
- **Affects**: Any workflow that attempts SOQL queries on agent metadata types
- **Symptom**: `SELECT ... FROM GenAiPlannerBundle` returns `INVALID_TYPE: GenAiPlannerBundle`. Same for `AiAuthoringBundle` and `GenAiFunction`. These types do not appear in `EntityDefinition` SOQL queries.
- **Root Cause**: These are **Metadata API types**, not sObjects. They exist in the metadata layer and are only accessible via `sf project retrieve start --metadata` or the Metadata API. This is by design, not a bug.
- **Workaround**: Use `sf project retrieve start --metadata "TypeName:ApiName"` instead of SOQL. For querying agent status/versions via SOQL, use `BotDefinition` and `BotVersion` sObjects.
  ```bash
  # ❌ WRONG — these are NOT sObjects
  sf data query --query "SELECT Id FROM GenAiPlannerBundle" -o ORG --json
  sf data query --query "SELECT Id FROM AiAuthoringBundle" -o ORG --json

  # ✅ CORRECT — use Metadata API
  sf project retrieve start --metadata "GenAiPlannerBundle:MyAgent_v1" -o ORG --json
  sf project retrieve start --metadata "AiAuthoringBundle:MyAgent" -o ORG --json

  # ✅ CORRECT — query sObjects for agent info
  sf data query --query "SELECT Id, DeveloperName FROM BotDefinition WHERE DeveloperName = 'MyAgent'" -o ORG --json
  sf data query --query "SELECT Id, VersionNumber, Status FROM BotVersion WHERE BotDefinition.DeveloperName = 'MyAgent'" -o ORG --json
  ```
- **Open Questions**: None — this is by design.

---

### Issue 21: Old GenAiPlannerBundle versions block Apex class deletion
- **Status**: WORKAROUND
- **Date Discovered**: 2026-03-10
- **Affects**: Apex class lifecycle when iterating agent versions
- **Symptom**: `sf project delete source --metadata ApexClass:MyClass` fails with "setup object in use" even though the Apex class is only referenced by inactive/old GenAiPlannerBundle versions. The current active bundle may reference a different (newer) Apex class, but old bundles still hold GenAiFunction references to the original.
- **Root Cause**: Each `sf agent publish authoring-bundle` creates a new GenAiPlannerBundle version. Old versions remain in the org and retain `GenAiPluginActionDefinition` records that reference the Apex class via `GenAiFunction`. The platform blocks deletion of any metadata referenced by ANY GenAiFunction — active or not.
- **Workaround**: Delete old bundles using the Orphan-Then-Delete pattern (Tooling API PATCH to null `PlannerId` on child `GenAiPluginDefinition` records, then DELETE the parent `GenAiPlannerBundle`). After all referring bundles are removed, the Apex class can be deleted normally.
  - **Note**: Apex test classes (not referenced by GenAiFunction) can be deleted freely at any time.
- **Open Questions**: Will Salesforce add cascade cleanup for inactive bundle versions?
- **References**: See [metadata-lifecycle.md](metadata-lifecycle.md) for the full Orphan-Then-Delete pattern and API comparison table.

---

### Issue 22: Flow version drift causes publish failure
- **Status**: WORKAROUND
- **Date Discovered**: 2026-03-10
- **Affects**: Action definitions targeting `flow://` with I/O schemas
- **Symptom**: `sf agent publish authoring-bundle` fails with I/O mismatch errors when the action's `inputs:` / `outputs:` block matches the latest Flow version but NOT the active Flow version. The publisher validates against the **active** version's I/O contract.
- **Root Cause**: `sf project retrieve start --metadata Flow:FlowName` retrieves the **latest** Flow version, which may be Draft or Obsolete. If the latest version renamed, added, or removed inputs/outputs compared to the active version, the locally-defined action I/O will not match what the publisher expects.
- **Example**: Flow `Locate_Items` has v2 (active) with input `IncomingCaseId` and v5 (latest, Obsolete) with input `RecordId`. Retrieving the Flow gives v5 metadata, so the developer defines `inputs: record_id: string` — but publish validates against v2's `IncomingCaseId`.
- **Workaround**: Before defining action I/O, verify the active Flow version's inputs:
  ```bash
  sf data query --query "SELECT ActiveVersionId, LatestVersionId FROM FlowDefinitionView WHERE ApiName = 'My_Flow' LIMIT 1" -o TARGET_ORG --json
  ```
  If `ActiveVersionId != LatestVersionId`, inspect the active version's I/O before writing your action definition.
- **Open Questions**: Will `sf project retrieve start` gain a `--active-version` flag for Flows?
- **References**: See [metadata-lifecycle.md](metadata-lifecycle.md) § "Flow Version Drift" and [cli-guide.md](cli-guide.md) § "Step 1: Retrieve" warning box.

---

### Issue 23: HTTP 500 on publish when `default_agent_user` is set for Employee Agent
- **Status**: WORKAROUND
- **Date Discovered**: 2026-03-11
- **Affects**: `sf agent publish authoring-bundle`
- **Symptom**: Publish fails with generic HTTP 500 error (no detailed message). Occurs when `default_agent_user` is included in the config block for an `AgentforceEmployeeAgent`, or when `default_agent_user` references a non-existent user for a Service Agent.
- **Root Cause**: The Einstein Platform tries to resolve the `default_agent_user` reference during publish. For Employee Agents, this field is invalid entirely. For Service Agents, if the user doesn't exist or lacks the Einstein Agent User profile, the API returns 500 instead of a descriptive error.
- **Workaround**: For Employee Agents, remove `default_agent_user` entirely and set `agent_type: "AgentforceEmployeeAgent"`. For Service Agents, verify the user exists and is truly valid for publish: active, not `AutomatedProcess`, and `Profile.Name = 'Einstein Agent User'`.
- **Extra diagnostic**: If `sf agent publish authoring-bundle --json` still fails after validate/preview pass, retry with `--skip-retrieve`. If `--skip-retrieve` succeeds, the failure was in the CLI retrieve/deploy-back phase rather than in the publish itself.
- **Open Questions**: Will the API return a descriptive error instead of 500? Will the CLI expose retrieve-phase failures separately from publish failures?

---

### Issue 24: Omitting `agent_type` silently defaults to Service Agent behavior
- **Status**: WORKAROUND
- **Date Discovered**: 2026-03-11
- **Affects**: Agent config block
- **Symptom**: Agent without explicit `agent_type` behaves as Service Agent. If `default_agent_user` is also missing, publish fails with HTTP 500. No warning or error is emitted about the missing field.
- **Root Cause**: The compiler defaults to `EinsteinServiceAgent` internally when `agent_type` is not specified.
- **Workaround**: Always set `agent_type` explicitly to `"AgentforceServiceAgent"` or `"AgentforceEmployeeAgent"`.
- **Open Questions**: Will the compiler emit a warning when `agent_type` is omitted?

---

### Issue 25: GenAiPluginDefinition Duplicate Name Collision

**Symptom**: Publish fails with `GenAiPluginDefinition` name conflict error.

**Cause**: When `start_agent` and a `topic` share the same API name, the generated GenAiPluginDefinition metadata collides — both produce identically-named plugin definitions.

**Workaround**: Ensure `start_agent` and all `topic` blocks use unique API names. A common pattern is to prefix the start agent name (e.g., `Start_My_Agent` vs `My_Agent_Topic`).

---

### Issue 26: `is_required: True` is a no-op for the planner
- **Status**: OPEN
- **Date Discovered**: 2026-03-11
- **Affects**: Action input definitions with `is_required: True`
- **Symptom**: Actions are invoked by the planner with empty or missing values for inputs marked `is_required: True`. The planner does not enforce the required constraint — it treats it as a hint, not a hard gate. Users expect the planner to refuse invocation until all required inputs are filled, but it proceeds regardless.
- **Root Cause**: The `is_required` property compiles and is stored in the GenAiFunction metadata, but the planner does not validate required inputs before action invocation. The property only influences LLM slot-filling behavior (the LLM _tries_ to collect the value but is not blocked from proceeding without it).
- **Workaround**: Use `available when` guards to enforce required inputs deterministically:
  ```yaml
  # ❌ INSUFFICIENT — planner ignores is_required
  inputs:
     order_id: string
        is_required: True

  # ✅ CORRECT — deterministic enforcement
  reasoning:
     actions:
        lookup: @actions.get_order
           available when @variables.order_id is not None
  ```
- **Open Questions**: Will the planner enforce `is_required` in a future release?
- **Cross-reference**: See syntax-reference.md § Action Metadata Properties, Common Pitfalls.

---

### Issue 27: ConcurrentModificationException when action I/O doesn't match invocable target
- **Status**: WORKAROUND (fix expected in 260.4)
- **Date Discovered**: 2026-03-11
- **Affects**: Action definitions with `inputs:` / `outputs:` blocks where the I/O schema does not declare ALL parameters on the invocable target
- **Symptom**: `sf agent publish authoring-bundle` fails with `ConcurrentModificationException` or "Internal Error" when the action definition's I/O schema is a subset of the target's invocable parameters. For example, if a Flow has 5 inputs but the action only declares 3, the server-side compiler throws an internal error.
- **Root Cause**: The compiler iterates over target parameters and agent I/O simultaneously. When the agent-side schema omits parameters that exist on the target, the iterator state becomes inconsistent, causing a `ConcurrentModificationException`.
- **Workaround**: Declare ALL inputs and outputs from the invocable target in the action definition, even parameters the agent doesn't use. Unused inputs can be given a default or left for the LLM to fill. Unused outputs can be marked `filter_from_agent: True`.
  ```yaml
  # ❌ WRONG — subset of target params causes ConcurrentModificationException
  inputs:
     customer_id: string
  # (target also has order_type, priority — not declared)

  # ✅ CORRECT — declare all target params
  inputs:
     customer_id: string
     order_type: string
        description: "Type of order"
     priority: string
        description: "Priority level"
  ```
- **Open Questions**: Fix expected in release 260.4. Will partial I/O schemas be supported?
- **Cross-reference**: Related to Issue 15 (missing outputs block). Issue 15 covers the case where `outputs:` is absent entirely; this issue covers the case where I/O is present but incomplete.

---

<a id="issue-28"></a>

### Issue 28: `date` primitive type in action I/O causes runtime error
- **Status**: WORKAROUND
- **Date Discovered**: 2026-03-11
- **Affects**: Action input/output definitions using `date` as the type
- **Symptom**: Actions with `date` typed inputs or outputs compile and publish without error, but fail at runtime with `'Date'` type error when the action is invoked. The LLM-provided value cannot be coerced into the platform's expected Date format.
- **Root Cause**: The `date` primitive in Agent Script compiles to a type that the action invocation runtime does not handle correctly. The runtime expects a specific ISO-8601 format that the LLM's slot-filled value does not match.
- **Workaround**: Use `object` type with `complex_data_type_name` referencing the Lightning date type:
  ```yaml
  # ❌ WRONG — causes runtime error 'Date'
  inputs:
     appointment_date: date

  # ✅ CORRECT — use object + Lightning type mapping
  inputs:
     appointment_date: object
        complex_data_type_name: "lightning__dateType"
  ```
- **Open Questions**: Will the `date` primitive be fixed to work in action I/O?
- **Cross-reference**: See syntax-reference.md § Variable Types, complex-data-types.md.

---

### Issue 29: ANTLR parser error for large/complex .agent files
- **Status**: OPEN
- **Date Discovered**: 2026-03-11
- **Affects**: Large `.agent` files (approximately 1,664+ lines observed)
- **Symptom**: The Agent Script parser (ANTLR-based) fails with a parser error when processing very large or highly complex `.agent` files. The error is non-specific and occurs during the parsing phase before any semantic validation.
- **Root Cause**: The ANTLR parser has practical limits on grammar complexity and token count. Very large agents with many topics, deep nesting, or extensive instruction blocks can exceed these limits.
- **Workaround**: None confirmed. Potential mitigations:
  1. Reduce agent size by simplifying instructions (move verbose prompts into Prompt Templates)
  2. Reduce topic count by consolidating related topics
  3. Use topic delegation (`@topic.X`) to split into multiple smaller agents
- **Open Questions**: What is the exact line/token limit? Will the parser be updated to handle larger files?

---

### Issue 30: 500 "Failed to create planner session" (widespread, multi-version)
- **Status**: OPEN
- **Date Discovered**: 2026-03-11
- **Affects**: Agent runtime — all agent types and versions
- **Symptom**: Agent returns HTTP 500 with "Failed to create planner session" when a user initiates a conversation. Error is intermittent and affects multiple orgs across different Salesforce releases. Not correlated with agent complexity, user permissions, or time of day.
- **Root Cause**: Unknown. The error originates in the planner session initialization layer. Suspected to be a transient infrastructure issue on the Einstein Platform side.
- **Workaround**: None reliable. Retry after a few minutes. If persistent:
  1. Deactivate and reactivate the agent
  2. Re-publish the authoring bundle (creates a new BotVersion)
  3. Contact Salesforce support with the session ID and timestamp
- **Open Questions**: Is this a known infrastructure issue with an ETA for fix?

---

<a id="issue-31"></a>

### Issue 31: Escalation loops when no human agents available
- **Status**: WORKAROUND
- **Date Discovered**: 2026-03-11
- **Affects**: `@utils.escalate` action in agents deployed without live human agents
- **Symptom**: When `@utils.escalate` is invoked but no human agents are available (e.g., outside business hours, no Omni-Channel agents online), the escalation fails silently and the conversation re-enters the same topic. This triggers the escalation logic again, creating an infinite loop. The built-in 3-4 loop guardrail eventually breaks the cycle, but the user receives confusing repeated messages.
- **Root Cause**: `@utils.escalate` does not return a success/failure status. There is no built-in mechanism to detect whether human agents are available before attempting escalation, and no way to handle a failed escalation gracefully.
- **Workaround**: Check agent availability before escalating, and provide a fallback path:
  ```yaml
  variables:
     escalation_attempted: mutable boolean = False

  topic escalation:
     description: "Escalate to human agent"
     reasoning:
        instructions: ->
           if @variables.escalation_attempted == True:
              | I'm sorry, but our team is currently unavailable.
              | Please try again during business hours or leave a message.
              transition to @topic.leave_message
           | Let me connect you with a support specialist.
        actions:
           handoff: @utils.escalate
              description: "Transfer to human agent"

     before_reasoning:
        if @variables.escalation_attempted == True:
           # Already tried — don't loop
           transition to @topic.leave_message
        set @variables.escalation_attempted = True
  ```
- **Open Questions**: Will `@utils.escalate` return a status code in a future release? Will a built-in availability check action be added?
- **Cross-reference**: See fsm-architecture.md § Pattern 5 (HANDOFF) — Escalation with Availability Check sub-pattern. See production-gotchas.md § Escalation Fallback Loop.

---

### Issue 32: Citations not rendering in NGA agents vs legacy agents
- **Status**: OPEN
- **Date Discovered**: 2026-03-11
- **Affects**: Next-Generation Agent (NGA / Agent Script) agents using knowledge bases with citations enabled
- **Symptom**: Despite enabling all citation settings (`citations_enabled: True`, `citations_url` configured, knowledge base attached), citations do not render in agent responses for NGA agents. The same knowledge base with citations works correctly in legacy Einstein Bot agents.
- **Root Cause**: The citation rendering pipeline is not fully implemented for the NGA/Agent Script agent runtime. Legacy agents use a different response rendering path that supports citation markup.
- **Workaround**: None for NGA agents. If citations are critical, use a legacy agent for knowledge-intensive topics, or include source URLs directly in the knowledge article content so they appear in the response text.
- **Open Questions**: Will citation rendering be added to the NGA runtime? Is there a timeline?

---

### Issue 33: `== []` and `set ... = []` — empty list literal not supported in expressions
- **Status**: WORKAROUND
- **Date Discovered**: 2026-03-12
- **Affects**: Expressions using `[]` literal for empty list comparison or assignment
- **Symptom**: Two related parse errors:
  1. `if @variables.my_list == []:` → parse error (`[` not allowed in expression position)
  2. `set @variables.my_list = []` → parse error (`[` not allowed in assignment position)
- **Root Cause**: The expression parser's sandboxed Python AST subset does not include list literal construction. `[]` is valid in `mutable list[T] = []` declarations (handled by the declaration parser), but NOT in runtime expressions.
- **Workaround**:
  - Empty check: `if @variables.my_list is None or len(@variables.my_list) == 0:`
  - Reset to empty: Use a dedicated empty list variable and copy:
    ```yaml
    variables:
       empty_temp: mutable list[string] = []
       my_list: mutable list[string] = []

    # To reset my_list at runtime:
    set @variables.my_list = @variables.empty_temp
    ```
- **Open Questions**: Will `[]` be added to the expression parser?
- **Cross-reference**: See syntax-reference.md § Expression Limitations.

---

<a id="issue-34"></a>

### Issue 34: `is_displayable: True` on prompt template outputs causes blank response
- **Status**: WORKAROUND
- **Date Discovered**: 2026-03-12
- **Affects**: Action outputs on prompt template actions (`prompt://` / `generatePromptResponse://` targets)
- **Symptom**: Setting `is_displayable: True` (or toggling "Show in conversation" in the UI) on a prompt template action's output causes the agent to return a blank or empty response. The prompt template executes correctly (visible in trace), but the response text is not surfaced to the user.
- **Root Cause**: When `is_displayable: True`, the platform attempts to render the raw prompt template output directly instead of letting the reasoner synthesize it. The rendering pipeline does not handle prompt template output format correctly, resulting in blank display.
- **Workaround**: Set `is_displayable: False` on prompt template outputs and let the reasoner synthesize the output into its response naturally. If the output should influence the reply or routing, also set `is_used_by_planner: True` on that field.
  ```yaml
  # ❌ WRONG — causes blank response
  outputs:
     response_text: string
        is_displayable: True

  # ✅ CORRECT — reasoner synthesizes output
  outputs:
     response_text: string
        is_displayable: False
        is_used_by_planner: True
  ```
- **Open Questions**: Will the rendering pipeline be updated to handle prompt template output with `is_displayable: True`?
- **Cross-reference**: See production-gotchas.md § `is_displayable: True` on Prompt Outputs.

---

### Issue 35: Topic `description:` with line breaks breaks the script
- **Status**: WORKAROUND
- **Date Discovered**: 2026-03-12
- **Affects**: `topic` and `start_agent` blocks with multi-line `description:` values
- **Symptom**: Including line breaks (literal newlines) inside a topic's `description: "..."` string causes the script to fail during parsing. The error is non-specific and may manifest as a syntax error on the following line.
- **Root Cause**: The topic `description:` parser expects a single-line string value. Unlike `instructions:` which supports `|` and `->` multiline syntax, `description:` does not have a multiline variant.
- **Workaround**: Keep topic descriptions on a single line. Remove all line breaks.
  ```yaml
  # ❌ WRONG — line break in description
  topic support:
     description: "Handles customer support requests
        including billing and technical issues"

  # ✅ CORRECT — single line
  topic support:
     description: "Handles customer support requests including billing and technical issues"
  ```
- **Open Questions**: Will `description:` gain multiline support (e.g., `description: |`)?

---

### Issue 36: Variable names conflict with system context variable mappings
- **Status**: WORKAROUND
- **Date Discovered**: 2026-03-12
- **Affects**: Variable declarations using names that match platform context variable field names
- **Symptom**: Declaring a variable with a name like `Locale` that matches an existing system context variable field name produces the error: "The field is already mapped to a Context Variable." The agent fails to compile.
- **Root Cause**: The platform reserves certain variable names for internal context variable mappings (e.g., `MessagingSession` fields like `Locale`, `Channel`, `Status`). These names collide with user-declared variables at the namespace level.
- **Workaround**: Use unique, prefixed names that avoid common MessagingSession and system field names:
  ```yaml
  # ❌ WRONG — collides with system context mapping
  variables:
     Locale: mutable string = ""

  # ✅ CORRECT — unique prefixed name
  variables:
     customer_locale: mutable string = ""
  ```
  **Known reserved names** (partial list): `Locale`, `Channel`, `Status`, `Origin`
- **Open Questions**: Will Salesforce publish a complete list of reserved context variable names?

---

### Issue 37: Draft version works but Committed version fails
- **Status**: OPEN
- **Date Discovered**: 2026-03-12
- **Affects**: Agent behavior difference between Draft and Committed/Active versions
- **Symptom**: Actions, variable updates, and topic routing that work correctly in Draft mode (preview) fail silently or produce different behavior in the Committed/Active version. The agent may skip actions, fail to update variables, or route incorrectly.
- **Root Cause**: Multiple potential causes reported: graph serialization differences between Draft and Committed compilation, action registry timing (Draft resolves actions lazily, Committed resolves eagerly), and stale cache from previous versions.
- **Workaround**: No universal workaround. Mitigation strategies:
  1. Re-commit (deactivate → re-publish → re-activate) to force a clean compilation
  2. Verify all action targets exist and are active in the org
  3. Compare Draft and Committed trace outputs to identify specific divergence points
- **Open Questions**: Will the Draft and Committed compilation paths be unified?

---

### Issue 38: Object variables not editable in preview
- **Status**: OPEN
- **Date Discovered**: 2026-03-12
- **Affects**: `sf agent preview` and Agent Builder Preview
- **Symptom**: Only scalar variable types (`string`, `number`, `boolean`) can be overridden in the preview interface. Object and list variables cannot be edited or injected — the UI does not provide input fields for complex types.
- **Root Cause**: The preview interface only renders scalar input controls. No JSON editor or structured input is provided for `object` or `list[T]` types.
- **Workaround**: For values needed during testing:
  1. Use scalar variables that can be set in preview, then assemble in logic
  2. Test object/list variable scenarios via the Agent Runtime API (Connect API) which accepts JSON payloads
  3. Pre-populate object variables in `before_reasoning:` for testing
- **Open Questions**: Will the preview interface add JSON editing for object/list variables?

---

<a id="issue-39"></a>

### Issue 39: `@context.*` linked sources not supported for NGA Service Agents
- **Status**: WORKAROUND
- **Date Discovered**: 2026-03-12
- **Affects**: Linked variables using `@context.*` sources in NGA Service Agents (ExternalCopilot / EinsteinServiceAgent)
- **Symptom**: Linked variables with `source: @context.currentRecordId`, `source: @context.customerId`, or other `@context.*` references produce "Unsupported data type" errors at runtime in NGA Service Agents. The variables compile and publish without error but fail when the agent starts a conversation.
- **Root Cause**: `@context.*` references resolve **page-level context** from Lightning Experience (LEX). This context is only available to **Employee Agents** embedded on LEX record pages where a `recordId` and user context are present. NGA Service Agents (chat, messaging) do not have LEX page context — they receive channel context via `@MessagingSession.*` instead.
- **Workaround**: For Service Agents, use `@MessagingSession.*` for channel context:
  ```yaml
  # ❌ WRONG for Service Agents — @context not available
  variables:
     customer_id: linked string
        source: @context.customerId

  # ✅ CORRECT for Service Agents — use messaging channel context
  variables:
     end_user_id: linked string
        source: @MessagingSession.MessagingEndUserId
     session_key: linked string
        source: @MessagingSession.MessagingSessionKey

  # ✅ CORRECT for Employee Agents on LEX — @context IS available
  variables:
     record_id: linked string
        source: @context.currentRecordId
  ```
- **Open Questions**: Will `@context.*` be extended to Service Agent channels?
- **Cross-reference**: See syntax-reference.md § Resource References, Common Linked Variable Sources.

---

<a id="issue-40"></a>

### Issue 40: Draft prompt template causes misleading publish errors for `generatePromptResponse://` actions
- **Status**: WORKAROUND
- **Date Discovered**: 2026-03-17
- **Affects**: `sf agent publish authoring-bundle` with `generatePromptResponse://` action targets
- **Symptom**: Publish fails with `invalid input parameters found: 'Input:query'` or `invalid output parameters found: 'promptResponse'` — implying the I/O names are wrong. Removing I/O blocks produces `Metadata API request failed: Metadata retrieval failed:` or `Internal Error, try again later`. `sf agent validate authoring-bundle` passes in all cases.
- **Root Cause**: The target prompt template is in **Draft** status. The platform cannot resolve the `generatePromptResponse://` target, but reports the failure as invalid I/O parameters or generic internal errors rather than indicating the template status.
- **Workaround**: Activate the prompt template in **Setup > Prompt Builder** before publishing. The original Agent Script syntax (with `"Input:X"` inputs and `promptResponse` output) publishes successfully once the template is Active. Pre-publish check: retrieve the template XML and verify `<status>Published</status>` or `<status>Active</status>`.
- **Open Questions**: Will Salesforce improve the error message to mention template status? Will `sf agent validate` add a target resolution check?
- **References**: [action-prompt-templates.md](action-prompt-templates.md#draft-template-publish-errors) — "Draft Template Publish Errors" section

---

## Resolved Issues

<a id="issue-16"></a>

### Issue 16: `connections:` (plural) wrapper block not valid — use `connection messaging:` (singular)
- **Status**: RESOLVED
- **Date Discovered**: 2026-02-16
- **Date Resolved**: 2026-02-16
- **Affects**: Agent Script escalation routing configuration
- **Symptom**: CLI validation rejects `connections:` (plural wrapper) block with `SyntaxError: Invalid syntax after conditional statement`.
- **Root Cause**: The correct syntax is `connection messaging:` (singular, standalone top-level block) — NOT the `connections:` plural wrapper shown in some docs and `future_recipes/`. The `connection <channel>:` block is a Beta Feature available on production orgs.
- **Resolution**: Use `connection messaging:` as a standalone block (no wrapper). Both minimal form (`adaptive_response_allowed` only) and full form (with `outbound_route_type`, `outbound_route_name`, `escalation_message`) are validated.
- **CRITICAL**: `outbound_route_name` requires `flow://` prefix — bare API name causes `ERROR_HTTP_404` on publish. Correct format: `"flow://My_Flow_Name"`.
- **All-or-nothing rule**: When `outbound_route_type` is present, all three route properties are required.
- **Note**: `outboundRouteName` in compiled XML does NOT need the `flow://` prefix — the publisher strips it during compilation. Both forms work in production XML.
- **Validated on**: Production org, 2026-02-16

<a id="issue-40-filter-planner-conflict"></a>

### Issue 40: `filter_from_agent` + `is_used_by_planner` on same output — `InvalidFormatError` with cascade

- **Status**: WORKAROUND
- **Severity**: High (Blocking)
- **Discovered**: 2026-03-17
- **Affects**: All Agent Script action output field declarations
- **Symptom**: Output fields that declare both `filter_from_agent` and `is_used_by_planner` produce `InvalidFormatError` with the message: _"Remove the 'is_used_by_planner' field and use only 'filter_from_agent'."_ More critically, this **invalidates the entire action definition**, causing cascading `ACTION_NOT_IN_SCOPE` errors everywhere the action is referenced — in `before_reasoning:` `run @actions.X` calls and `reasoning.actions:` invocations. The cascade makes the root cause very hard to diagnose because the error appears on action _references_, not on the offending output field.
- **Root Cause**: `filter_from_agent` and `is_used_by_planner` are mutually exclusive output visibility controls. When both are present, the Agent Script parser rejects the output field, which poisons the entire action definition and makes it invisible to all scopes.
- **Cascade Pattern**: One invalid output field on a shared action (e.g., `update_session` reused across topics) can trigger `ACTION_NOT_IN_SCOPE` errors in every topic that references it — often 4-6+ errors from a single root cause.
- **Workaround**: Use only `filter_from_agent: True` on outputs that should be hidden from the customer. Remove `is_used_by_planner` from those fields entirely. The planner can still reason about the output via `set @variables.X = @outputs.Y` bindings in reasoning actions.
- **Example**:
  ```yaml
  # ❌ WRONG — causes InvalidFormatError + cascade
  outputs:
     caseId: string
        filter_from_agent: True
        is_used_by_planner: False

  # ✅ CORRECT — filter_from_agent alone
  outputs:
     caseId: string
        filter_from_agent: True
  ```
- **Validator Rule**: `ASV-RUN-020` (Blocking)
- **Real-world impact**: Observed in a production agent — 6 output fields across 5 topics caused 4 cascading `ACTION_NOT_IN_SCOPE` errors that blocked publish.
- **Validated on**: Production sandbox, 2026-03-17

### Issue 41: Lifecycle arithmetic on mutable number crashes when variable is `None` at runtime

- **Status**: WORKAROUND
- **Severity**: High (Silent crash)
- **Discovered**: 2026-03-17
- **Affects**: `before_reasoning` / `after_reasoning` blocks with arithmetic on mutable number variables
- **Symptom**: Agent crashes silently with "unexpected error" when a `before_reasoning` block does `set @variables.counter = @variables.counter + 1` and the variable is `None` at runtime. The crash is `None + 1` — a type error in the expression evaluator. No useful error message is surfaced to the user or logs.
- **Root Cause**: Mutable number variables declared with `= 0` defaults can arrive as `None` at runtime. Known triggers: (1) Eval API / Testing Center state injection that omits the variable, (2) platform variable initialization bugs where defaults are not applied before the first `before_reasoning` execution.
- **Cascade Pattern**: Common in guardrail topics where a strike counter is incremented on every entry. All guardrail topics (e.g., `inappropriate_content`, `prompt_injection`, `reverse_engineering`) crash simultaneously since they share the same counter pattern.
- **Workaround**: Add a null guard before any arithmetic in lifecycle hooks:
  ```yaml
  # ❌ CRASHES when guardrail_strikes is None
  before_reasoning:
     set @variables.guardrail_strikes = @variables.guardrail_strikes + 1
     if @variables.guardrail_strikes >= 3:
        transition to @topic.escalation

  # ✅ SAFE — null guard prevents None + 1
  before_reasoning:
     if @variables.guardrail_strikes is None:
        set @variables.guardrail_strikes = 0
     set @variables.guardrail_strikes = @variables.guardrail_strikes + 1
     if @variables.guardrail_strikes >= 3:
        transition to @topic.escalation
  ```
- **Validator Rule**: `ASV-RUN-021` (Warning)
- **Validated on**: Production sandbox, 2026-03-17

### Issue 42: Raw `@system_variables.user_input` substring matching is brittle for deterministic routing

- **Status**: WORKAROUND
- **Date Discovered**: 2026-03-20
- **Affects**: Deterministic branching that uses `contains`, `startswith`, or `endswith` directly on `@system_variables.user_input`
- **Symptom**: Rules such as `if @system_variables.user_input contains "never mind":` appear simple, but cancellation/revision detection behaves inconsistently across real user phrasing. The branch may miss intent variants or fail to trigger when punctuation, casing, or phrasing changes.
- **Root Cause**: `@system_variables.user_input` is raw last-utterance text, not a normalized intent signal. Direct substring checks are too weak for control-flow-critical intent detection.
- **Workaround**: Normalize the utterance first via Flow, Apex, or a classifier action, then branch on an explicit boolean or enum.
  ```yaml
  # ❌ BRITTLE — raw text matching
  if @system_variables.user_input contains "never mind":
     transition to @topic.cancel_request

  # ✅ SAFER — normalize first
  run @actions.classify_user_intent
     with utterance = @system_variables.user_input
     set @variables.cancel_requested = @outputs.cancel_requested

  if @variables.cancel_requested == True:
     transition to @topic.cancel_request
  ```
- **Validator Rule**: `ASV-RUN-023` (Warning)
- **Open Questions**:
  - Will future runtime layers provide stronger deterministic utterance-matching semantics?
  - Will direct raw-text guards become portable enough to recommend for intent routing?

---

## Contributing

When you discover a new platform issue during an Agent Script session:

1. Add it to the **Open Issues** section using the template above
2. Assign the next sequential issue number
3. Set status to `OPEN` or `WORKAROUND`
4. Include the date discovered
5. Be specific about the symptom and any error messages
6. Note what you've tried so far under "Workaround"

When an issue is resolved:
1. Update the status to `RESOLVED`
2. Add the resolution date and what fixed it (e.g., "Fixed in Spring '26 release")
3. Move the issue to the **Resolved Issues** section

---

*Last updated: 2026-03-20 (v2.9.0)*
