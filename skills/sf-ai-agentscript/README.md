# sf-ai-agentscript

🤖 **Agent Script DSL development for Salesforce Agentforce** - Write deterministic agents in a single `.agent` file with FSM architecture, instruction resolution, and hybrid reasoning.

> Default workflow: direct `.agent` authoring first. Spec generation and scaffolds are optional helpers, not the primary authoring model.

## Features

- ✅ **100-point scoring system** across 6 categories for quality assurance
- ✅ **Complete syntax reference** for Agent Script DSL
- ✅ **FSM architecture patterns** - Hub-and-spoke, verification gates, escalation chains
- ✅ **Instruction resolution guidance** - Three-phase execution model
- ✅ **Debugging support** - Trace analysis and forensic debugging
- ✅ **CLI deployment** - Retrieve, validate, deploy via `sf agent` commands
- ✅ **Cross-skill integration** - Works with sf-flow, sf-ai-agentforce-testing, sf-deploy

## Requirements

| Requirement | Value |
|-------------|-------|
| API Version | 66.0+ |
| License | Agentforce |
| Einstein Agent User | Required for Service Agents only |
| SF CLI | v2+ with agent commands |

## Installation

```bash
# Install as part of sf-skills
npx skills add Jaganpro/sf-skills

# Or install just this skill
npx skills add Jaganpro/sf-skills --skill sf-ai-agentscript
```

## Quick Start

### 1. Invoke the Skill
```
/sf-ai-agentscript
```

### 2. Describe Your Agent
Tell Claude what your agent should do, and it will generate a scored Agent Script.

### 3. Validate & Deploy
```bash
sf org create agent-user --target-org TARGET_ORG --json   # Service Agents only
sf agent validate authoring-bundle --api-name MyAgent -o TARGET_ORG --json
sf agent publish authoring-bundle --api-name MyAgent --target-org prod --json
```

## Scoring System

| Category | Points | Focus |
|----------|--------|-------|
| Structure & Syntax | 20 | Required blocks, indentation, required fields |
| Deterministic Logic | 25 | Security guards, post-action checks |
| Instruction Resolution | 20 | Arrow syntax, template injection |
| FSM Architecture | 15 | Topic separation, transitions |
| Action Configuration | 10 | Protocols, I/O mapping |
| Deployment Readiness | 10 | Valid user, clean validation |

**Thresholds:** 90+ Excellent | 80-89 Very Good | 70-79 Good | 60-69 Needs Work | <60 Critical

## Key Rules

1. **`default_agent_user` MUST exist (Service Agents)** - Not needed for Employee Agents. See [references/agent-user-setup.md](references/agent-user-setup.md)
2. **No mixed tabs/spaces** - Use consistent indentation throughout
3. **Booleans are `True`/`False`** - Python-style, not JavaScript
4. **Exactly one `start_agent`** - Single entry point required
5. **Use `available when` for security** - Don't rely on prompts
6. **Do not branch directly on raw `@system_variables.user_input` substring checks** - Normalize intent first
7. **Prompt template outputs should usually be `is_displayable: False` + `is_used_by_planner: True`** - Avoid blank responses
8. **Dynamic `system.messages.welcome` / `error` should use `|`** - Quoted strings are fine for static text, but if a system message contains `{!...}` interpolation, switch that message to template/block form
9. **Employee Agents do not need a dedicated running user** - They need end-user visibility via permission sets when surfaced in Lightning Experience

## Quick Syntax Reference

Common minimal layout (`connection:` and `knowledge:` omitted here because they are optional):

```yaml
# Block structure
config:        # Required: Agent metadata
variables:     # Optional: State management
system:        # Required: Messages and instructions
language:      # Optional: Locale settings
start_agent:   # Required: Entry point
topic:         # Required: Conversation handlers

# Instruction patterns
instructions: ->           # Arrow syntax for expressions
  if @variables.verified:  # Conditional (resolves before LLM)
    | Welcome back!        # Literal text for LLM
  run @actions.load_data   # Execute a topic-level target-backed action deterministically
  set @var = @outputs.val  # Capture output

# Action guards
actions:
  process: @actions.refund
    available when @variables.verified == True  # LLM can't see if False

# System message patterns
system:
  messages:
    welcome: "Hello!"                 # Static text: quotes are fine
    # welcome: |                       # Dynamic text with {!...}: use block form
    #   Hi {!@variables.user_name}!
```

## Documentation

| Document | Description |
|----------|-------------|
| [SKILL.md](SKILL.md) | Main entry point with scoring system |
| [references/](references/) | Comprehensive guides per topic |
| [references/](references/) | Quick reference guides |
| [assets/](assets/) | Example `.agent` files and starter scaffolds |

## Cross-Skill Workflow

```
/sf-flow → /sf-ai-agentscript → /sf-ai-agentforce-testing → /sf-deploy
   ↑              ↑                      ↑                      ↑
Create Flows   Write agent         Test routing           Deploy to org
```

## Official Resources

- [Agent Script Documentation](https://developer.salesforce.com/docs/ai/agentforce/guide/agent-script.html)
- [Agentforce Builder Guide](https://help.salesforce.com/s/articleView?id=sf.copilot_builder_overview.htm)
- [Agentforce DX Guide](https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx.html)

## License

MIT License - See [LICENSE](LICENSE)

---

Created by [Jag Valaiyapathy](https://github.com/Jaganpro)
