<!-- Parent: sf-ai-agentscript/SKILL.md -->

# Minimal Working Examples

## Hello-World Agent Script

A complete, deployable agent with one topic, one action, and conditional logic:

```yaml
config:
  developer_name: "simple_agent"
  description: "A minimal working agent example"
  agent_type: "AgentforceServiceAgent"
  default_agent_user: "agent_user@yourorg.com"

system:
  messages:
    welcome: "Hello! How can I help you today?"
    error: "Sorry, something went wrong."
  instructions: "You are a helpful customer service agent."

variables:
  customer_verified: mutable boolean = False

topic main:
  description: "Main conversation handler"
  reasoning:
    instructions: ->
      if @variables.customer_verified == True:
        | You are speaking with a verified customer.
        | Help them with their request.
      else:
        | Please verify the customer's identity first.
    actions:
      verify: @actions.verify_customer
        description: "Verify customer identity"
        set @variables.customer_verified = @outputs.verified

start_agent entry:
  description: "Entry point for all conversations"
  reasoning:
    instructions: |
      Greet the customer and route to the main topic.
    actions:
      go_main: @utils.transition to @topic.main
        description: "Navigate to main conversation"
```

### Key Points

- **`config` block**: `developer_name` must match the folder name (case-sensitive)
- **`default_agent_user`**: Must be a valid Einstein Agent User in the target org — query with `sf data query`
- **`instructions: ->`**: Procedural mode enables `if`/`else` and `run` directives
- **`instructions: |`**: Literal mode for static text passed to the LLM
- **`set @variables.X = @outputs.Y`**: Captures action output into mutable state
- **`@utils.transition`**: Permanent handoff (does not return to calling topic)

### Personalized Welcome Message

Use quoted strings for static system messages, but switch `welcome` / `error` to template/block form when you need interpolation:

```yaml
variables:
  user_preferred_name: linked string
    source: @MessagingSession.UserPreferredName__c
    description: "Example linked variable source for first-turn personalization"

system:
  messages:
    welcome: |
      Hi {!@variables.user_preferred_name}! How can I help you today?
    error: "Sorry, something went wrong."
  instructions: "You are a helpful customer service agent."
```

- Use `|` for dynamic welcome/error messages that include `{!...}` references.
- Do **not** write dynamic system messages like `welcome: "Hi {!@variables.user_preferred_name}!"` — that quoted form can render literally.
- Keep quoted strings for static welcome/error text.
- Keep conditional logic in `reasoning.instructions: ->`; `system.messages` should stay as static text or direct variable templates.
