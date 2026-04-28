# Agent Script Activation Checklist

Use this file when `sf-ai-agentscript` is already active and you need the shortest possible pre-authoring / pre-publish checklist.

## 1. Route correctly

Use `sf-ai-agentscript` for:
- `.agent` files
- deterministic topic/state/action design
- Agent Script CLI workflows (`sf agent generate/publish`)

Do **not** use it for:
- Setup UI / Agent Builder maintenance → use `sf-ai-agentforce`
- agent testing strategy → use `sf-ai-agentforce-testing`
- persona design → use `sf-ai-agentforce-persona`

## 2. Blockers to check before editing

- Exactly one `start_agent`
- No mixed tabs and spaces
- `True` / `False` only
- No `else if`
- No nested `if`
- No top-level `actions:` block
- No `@inputs` inside `set`
- No default values on `linked` variables
- No `object` / `list` linked variables
- Use explicit `agent_type`
- Use `run @actions.X` only for topic-level action definitions that declare `target:`
- Do not branch directly on raw `@system_variables.user_input contains/startswith/endswith`
- Do not treat `contains` / `startswith` / `endswith` as the sole gate for critical routing or validation
- On prompt template outputs, prefer `is_displayable: False` + `is_used_by_planner: True`
- Do not assume `@outputs.X` is scalar; inspect the output schema before comparing or assigning it

## 3. Service Agent publish safety

For `AgentforceServiceAgent`:
- `default_agent_user` must exist
- user must be active
- user must not be `AutomatedProcess`
- `Profile.Name` must be `Einstein Agent User`
- target-backed actions usually require a custom `{AgentName}_Access` permission set

For `AgentforceEmployeeAgent`:
- omit `default_agent_user`

Full details:
- [agent-user-setup.md](agent-user-setup.md)
- [production-gotchas.md](production-gotchas.md)

## 4. Minimal authoring workflow

1. Define `config`, `system`, `start_agent`, and topics
2. Add `variables` only when state is needed
3. Define target-backed actions with complete `inputs:` and `outputs:`
4. Add deterministic guards with `available when`
5. Validate on save
6. Run preview smoke tests
7. Publish, then activate

## 5. Canonical deep references

- Syntax rules: [syntax-reference.md](syntax-reference.md)
- Actions and target protocols: [actions-reference.md](actions-reference.md)
- Production and runtime gotchas: [production-gotchas.md](production-gotchas.md)
- Preview loop: [preview-test-loop.md](preview-test-loop.md)
- Debugging: [debugging-guide.md](debugging-guide.md)
- Validator rules: [validator-rule-catalog.md](validator-rule-catalog.md)
