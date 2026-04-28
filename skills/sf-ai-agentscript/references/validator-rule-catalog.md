# Agent Script Validator Rule Catalog

> Source of truth for the automatic `.agent` write/edit validator at `hooks/scripts/agentscript-syntax-validator.py`.
>
> Validator output prefixes findings with stable rule IDs like `[ASV-STR-015]` so teams can search this catalog, commit messages, and incident notes consistently.

## Severity Model

| Severity | Meaning | Typical action |
|---|---|---|
| **Blocking** | High-confidence compiler, publish, or severe runtime-break pattern | Fix before preview/publish |
| **Warning** | Portability, runtime, org-drift, or best-practice risk | Review before publish |
| **Info / N/A** | Checklist-only status when a rule is not applicable | No action |

## Rule Prefixes

| Prefix | Area |
|---|---|
| `ASV-STR-*` | Core structure / parse safety |
| `ASV-CFG-*` | Config / identity semantics |
| `ASV-CON-*` | Connection routing rules |
| `ASV-ORG-*` | Org-aware existence / permission checks |
| `ASV-RUN-*` | Runtime / planner / publish gotchas |
| `ASV-QLT-*` | Quality / maintainability heuristics |

---

## Structure Rules

| Rule ID | Severity | Check | Encoded behavior |
|---|---|---|---|
| `ASV-STR-001` | Blocking | Indentation consistency | Errors when tabs and spaces are mixed in leading indentation. |
| `ASV-STR-002` | Blocking | Boolean capitalization | Errors on lowercase `true` / `false` in assignment-style lines; requires `True` / `False`. |
| `ASV-STR-003` | Blocking | Required top-level blocks | Requires `config`, `system`, and exactly one `start_agent`. |
| `ASV-STR-004` | Blocking | Exactly one `start_agent` | Errors on zero or multiple `start_agent` blocks. |
| `ASV-STR-005` | Blocking | Topic / start collision | Errors if a `start_agent` name collides with a `topic` API name. |
| `ASV-STR-006` | Blocking | Naming rules | Enforces Salesforce-style API names: starts with letter, alnum/underscore only, no trailing/consecutive underscores, max 80 chars. |
| `ASV-STR-007` | Blocking | Invalid `connections:` wrapper | Errors on top-level `connections:`; use `connection messaging:` etc. |
| `ASV-STR-008` | Blocking | `mutable` + `linked` conflict | Errors if a variable line combines both modifiers. |
| `ASV-STR-009` | Warning | Context-colliding variable names | Warns on names like `Locale`, `Channel`, `Status`, `Origin`. |
| `ASV-STR-010` | Blocking | Undefined variable references | Errors on `@variables.X` references in executable lines when `X` is undeclared. |
| `ASV-STR-011` | Blocking | Undefined topic references | Errors on `@topic.X` when `topic X:` / `start_agent X:` is missing. |
| `ASV-STR-012` | Warning | Topic/start description formatting | Warns when `topic` / `start_agent` `description:` appears multiline or block-scalar based. |
| `ASV-STR-013` | Warning | Lifecycle `instructions:` wrapper | Warns when `before_reasoning:` / `after_reasoning:` nests `instructions:` instead of direct content. |
| `ASV-STR-014` | Blocking | Empty conditional bodies | Errors on `if` / `else` blocks that contain no executable body. |
| `ASV-STR-015` | Blocking | `else if` unsupported | Errors on literal `else if`. |
| `ASV-STR-016` | Blocking | Nested `if` unsupported | Errors when an `if`/`else` is nested inside another conditional block. |
| `ASV-STR-017` | Blocking | Top-level `actions:` unsupported | Errors on root-level `actions:` blocks. |
| `ASV-STR-018` | Blocking | Linked variable defaults | Errors when a `linked` variable declares `= ...`. |
| `ASV-STR-019` | Blocking | Linked variable container types | Errors on `linked object` and `linked list[...]`. |
| `ASV-STR-020` | Blocking | Ellipsis misuse | Errors when `...` is used outside slot-fill style `with param=...` bindings. |
| `ASV-STR-021` | Blocking | Reserved variable / I/O field names | Errors when variables or action I/O fields use reserved names such as `description`, `label`, `is_required`, `is_displayable`, `is_used_by_planner`, `model`. |

---

## Config / Identity Rules

| Rule ID | Severity | Check | Encoded behavior |
|---|---|---|---|
| `ASV-CFG-001` | Blocking | Config completeness | Requires an identifier (`developer_name` or legacy `agent_name`) and description (`description` or compatibility `agent_description`). |
| `ASV-CFG-002` | Blocking / Warning | Agent type semantics | Errors when Service Agents omit `default_agent_user`, Employee Agents include it, or `agent_type` is invalid. Warns when `agent_type` is omitted but `default_agent_user` implies Service Agent fallback. |
| `ASV-CFG-003` | Warning | Duplicate config description fields | Warns when both `description:` and `agent_description:` are defined in the same config block. |
| `ASV-CFG-004` | Warning | `default_agent_user` inline comments | Warns when `default_agent_user:` contains trailing inline comments / extra text. |
| `ASV-CFG-005` | Warning | Optional config field shape | Warns on malformed optional config fields such as non-boolean `enable_enhanced_event_logs` or empty `company` / `role` / `agent_version` / `user_locale`. |
| `ASV-CFG-006` | Blocking | Topic system override syntax | Errors on topic-level shorthand `system: "..."`; enforces nested `system:` + `instructions:` shape. |

---

## Connection Rules

| Rule ID | Severity | Check | Encoded behavior |
|---|---|---|---|
| `ASV-CON-001` | Blocking | Route property completeness | If any route property is used on `connection messaging:` / `voice:` / `web:`, all required route fields must be present: `outbound_route_type`, `outbound_route_name`, `escalation_message`. |
| `ASV-CON-002` | Blocking | Route target prefix | Errors when `outbound_route_name` does not start with `flow://`. |
| `ASV-CON-003` | Warning | Route type portability | Warns when `outbound_route_type` is not the TDD-validated `OmniChannelFlow`. |

---

## Org-Aware Rules

| Rule ID | Severity | Check | Encoded behavior |
|---|---|---|---|
| `ASV-ORG-001` | Blocking / Warning | Service Agent user existence | Queries the resolved target org and verifies `default_agent_user` exists, is active, is not `AutomatedProcess`, and has profile `Einstein Agent User`. Warns if the org query cannot run. |
| `ASV-ORG-002` | Warning | Required Service Agent assignments | Warns when the Service Agent user is missing a verified `AgentforceServiceAgentUser` assignment or expected `{AgentName}_Access` assignment for target-backed actions. |
| `ASV-ORG-003` | Warning | Apex permission coverage | Warns when the custom `{AgentName}_Access` permission set lacks `SetupEntityAccess` / `<classAccesses>` for apex targets or cannot be verified. |
| `ASV-ORG-004` | Blocking / Warning | Flow target readiness | Errors when `flow://` action targets are missing or inactive in the resolved org. Warns if the org query cannot run. |
| `ASV-ORG-005` | Warning | Other target protocol review | Warns when target protocols cannot be permission-checked automatically. |
| `ASV-ORG-006` | Blocking / Warning | Apex target existence | Errors when `apex://` targets do not exist in the resolved org. Warns if the org query cannot run. |
| `ASV-ORG-007` | Blocking / Warning | Connection route Flow readiness | Errors when connection `outbound_route_name: flow://...` targets are missing or inactive in the resolved org. Warns if the org query cannot run. |

---

## Runtime / Publish Gotchas

| Rule ID | Severity | Check | Encoded behavior |
|---|---|---|---|
| `ASV-RUN-001` | Blocking | Empty list literal gotchas | Errors on `== []`, `!= []`, and `set ... = []`. |
| `ASV-RUN-002` | Warning | `@inputs` in `set` | Warns on `set @variables.x = @inputs.y`. |
| `ASV-RUN-003` | Blocking | Bare `run` action names | Errors on `run foo`; requires `run @actions.foo`. |
| `ASV-RUN-004` | Blocking | Invalid metadata on `@utils.transition` | Errors when transition utilities use target-action-only metadata such as `label`, `require_user_confirmation`, etc. |
| `ASV-RUN-005` | Warning | Prompt output displayability | Warns on prompt/generatePromptResponse outputs with `is_displayable: True`. |
| `ASV-RUN-006` | Warning | `date` in action I/O | Warns when action inputs/outputs use primitive `date`; recommends Lightning date object mapping. |
| `ASV-RUN-007` | Warning | `is_required: True` planner gap | Warns when required inputs exist without an `available when` guard. |
| `ASV-RUN-008` | Warning | Agent-type-specific messaging patterns | Warns on Messaging config for Employee Agents and related mismatches. |
| `ASV-RUN-009` | Blocking | Pipe content in lifecycle hooks | Errors when `before_reasoning:` / `after_reasoning:` contains `|` prompt lines. |
| `ASV-RUN-010` | Warning | Lifecycle `run` portability | Warns on `run @actions.X` inside lifecycle hooks. |
| `ASV-RUN-011` | Blocking | Missing target action `outputs:` | Errors when a target-backed action definition omits `outputs:`. |
| `ASV-RUN-012` | Warning | Multiple `available when` portability | Warns when an action declares more than one `available when` clause. |
| `ASV-RUN-013` | Warning | `require_user_confirmation` runtime gap | Warns on `require_user_confirmation: True` because runtime dialogs are unreliable. |
| `ASV-RUN-014` | Blocking | `run` resolves outside target-backed definition scope | Errors when `run @actions.X` points at a reasoning-only utility, a topic-level utility/delegation without `target:`, or an unresolved action name instead of a topic-level target-backed action definition. |
| `ASV-RUN-015` | Warning | Welcome/error interpolation in quoted string form | Warns when a system welcome/error line appears to combine inline `{!...}` interpolation with plain string form instead of template/block form. |
| `ASV-RUN-016` | Warning | Welcome/error folded-scalar guidance | Warns when system welcome/error messages use folded scalars (`>`); prefer literal block style (`|`) for dynamic or multiline message text. |
| `ASV-RUN-017` | Warning | Service Agent `@context.*` sources | Warns on linked `@context.*` sources in Service Agent files because support is surface-dependent. |
| `ASV-RUN-018` | Warning | Escalation fallback heuristic | Warns when `@utils.escalate` is present without an obvious fallback / latch pattern. |
| `ASV-RUN-019` | Warning | Large-file parser risk | Warns when line/topic/action counts cross heuristic complexity thresholds. |
| `ASV-RUN-020` | Blocking | Output `filter_from_agent` + `is_used_by_planner` conflict | Errors when an action output field declares both `filter_from_agent` and `is_used_by_planner`. These are mutually exclusive visibility controls; the combination causes `InvalidFormatError` and cascading `ACTION_NOT_IN_SCOPE` failures that make the entire action invisible to `before_reasoning` and `reasoning` blocks. |
| `ASV-RUN-021` | Warning | Lifecycle arithmetic without null guard | Warns when `before_reasoning` or `after_reasoning` does arithmetic on a mutable number variable (e.g., `set @variables.X = @variables.X + 1`) without a preceding `if @variables.X is None:` guard. Mutable number variables can arrive as `None` at runtime via Eval API state injection or platform initialization bugs, causing silent `None + 1` crashes. |
| `ASV-RUN-022` | Warning | Platform guardrail topic conflict | Warns when custom topics duplicate the platform's 3 built-in guardrail tools (`Inappropriate Content Guardrail`, `Prompt Injection Guardrail`, `Reverse Engineering Guardrail`). The platform auto-injects these tools into every topic's `EnabledToolsStep`. Custom topics with names containing `inappropriate`, `prompt_injection`, or `reverse_engineering` create 3+3 tool duplication in the LLM tool set, confusing the planner and causing "unexpected error" crashes. Recommended: remove custom guardrail topics and let the platform handle content moderation. |
| `ASV-RUN-023` | Warning | Raw `user_input` string matching | Warns when deterministic guards use `contains` / `startswith` / `endswith` directly on `@system_variables.user_input`. Raw last-utterance text is not a stable intent signal; normalize it into a boolean or enum first. |
| `ASV-RUN-024` | Warning | String-method guard portability | Warns when deterministic guards rely on `contains` / `startswith` / `endswith` for control-flow-critical validation. These operators may compile, but they are not portable enough to be the sole routing or validation gate. |
| `ASV-RUN-025` | Warning | Hidden prompt outputs without planner visibility | Warns when a prompt target output is hidden from direct display (`is_displayable: False` or `filter_from_agent: True`) but is not planner-visible. This often leads to "action ran but response is missing" behavior. |
| `ASV-RUN-026` | Warning | Structured output assigned directly to scalar variable | Warns when an action output declared as `object`/`list[...]` is assigned directly to a scalar `@variables.X`. The output likely needs property access (for example `.value` if present in the schema) or flattening upstream in Flow/Apex. |

---

## Quality / Maintainability Heuristics

| Rule ID | Severity | Check | Encoded behavior |
|---|---|---|---|
| `ASV-QLT-001` | Warning | Transition naming convention | Warns when utility transitions do not use the recommended `go_to_` prefix. |
| `ASV-QLT-002` | Warning | Duplicate action descriptions | Warns when sibling actions reuse near-identical descriptions, reducing planner clarity. |
| `ASV-QLT-003` | Warning | Duplicate topic descriptions | Warns when topic/start descriptions are near-identical, reducing topic-selection clarity. |
| `ASV-QLT-004` | Warning | Sensitive action guard suggestion | Warns when obviously sensitive target-backed actions lack `available when` guards. |
| `ASV-QLT-005` | Warning | Post-action check ordering | Warns when status-completion checks appear after LLM prompt lines instead of before them. |

---

## Checklist Sections Emitted by the Validator

The hook groups findings into these report sections:

1. **Structure**
2. **Agent identity**
3. **Connections**
4. **Targets & permissions**
5. **Runtime gotchas**
6. **Quality**

This grouping is intentionally broader than the rule prefixes so operators can scan reports quickly without memorizing every ID.

## Authoring Guidance

- Treat **blocking** IDs as pre-publish must-fix items.
- Add rule IDs to commit messages when fixing platform regressions, for example: `fix(agent): resolve ASV-RUN-011 missing outputs on flow action`.
- When the validator emits a warning that is intentionally accepted, record the reason in code comments or PR notes using the rule ID.
- Keep this catalog in sync with `hooks/scripts/agentscript-syntax-validator.py` whenever a rule is added, removed, or re-severitized.
