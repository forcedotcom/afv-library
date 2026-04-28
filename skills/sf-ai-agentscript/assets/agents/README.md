# Complete Agent Examples & Starter Scaffolds

Examples and starter scaffolds for building complete, deployable agents.

## Learning Path

### Service Agent Examples
| Example | Complexity | Description |
|---------|------------|-------------|
| `hello-world.agent` | Beginner | Minimal viable Service Agent - start here |
| `simple-qa.agent` | Beginner | Single-topic Q&A agent |
| `multi-topic.agent` | Intermediate | Multi-topic routing agent |
| `production-faq.agent` | Advanced | Production-ready FAQ with escalation |

### Employee Agent Examples
| Example | Complexity | Description |
|---------|------------|-------------|
| `hello-world-employee.agent` | Beginner | Minimal viable Employee Agent - no dedicated user needed |

> **Service vs Employee**: Service Agents run as a dedicated Einstein Agent User and require `default_agent_user`, linked Messaging variables, and `connection` blocks. Employee Agents run as the logged-in user and need none of these. See [agent-user-setup.md](../../references/agent-user-setup.md) for details.

## Quick Start

1. Copy a starter example to your SFDX project if you want a scaffold:
   ```bash
   mkdir -p force-app/main/default/aiAuthoringBundles/My_Agent
   cp hello-world.agent force-app/main/default/aiAuthoringBundles/My_Agent/My_Agent.agent
   cp ../metadata/bundle-meta.xml force-app/main/default/aiAuthoringBundles/My_Agent/My_Agent.bundle-meta.xml
   ```

2. Validate and deploy:
   ```bash
   sf agent validate authoring-bundle --api-name My_Agent --target-org your-org --json
   sf agent publish authoring-bundle --api-name My_Agent --target-org your-org --json
   ```

> Default repo workflow: create or edit the target `.agent` directly. These files are optional examples/scaffolds, not a required template system.
>
> **System message tip**: Keep static `welcome` / `error` messages in quotes. If you personalize a system message with Agent Script interpolation such as `{!@variables.user_name}`, use block form with `|`. Template placeholders like `{{WelcomeMessage}}` in these scaffolds are pre-processing placeholders, not Agent Script runtime interpolation.

## Common Top-Level Blocks

Use this ordering convention for consistency in this skill's examples.

| Block | Required | Purpose |
|-------|----------|---------|
| `config:` | ✅ Yes | Deployment metadata (`developer_name`, `agent_label`, `agent_type`, etc.) |
| `variables:` | Optional | Data connections and state storage |
| `system:` | ✅ Yes | Agent personality and default messages |
| `connection:` | Optional | Escalation routing |
| `knowledge:` | Optional | Knowledge configuration |
| `language:` | Optional | Locale configuration |
| `start_agent` | ✅ Yes | Entry point topic (exactly one required) |
| `topic` | ✅ Yes | Conversation topics (one or more required) |

Official Salesforce materials can present these blocks in different sequences. This table reflects the convention used by this skill, not a universal compile rule.

## Next Steps

- [components/](../components/) - Reusable action and topic snippets
- [patterns/](../patterns/) - Advanced patterns for complex behaviors
- [metadata/](../metadata/) - Supporting metadata examples
