<!-- Parent: sf-ai-agentforce/SKILL.md -->
<!-- TIER: 2 | DETAILED REFERENCE -->
<!-- Read after: SKILL.md -->
<!-- Purpose: CLI command reference for Builder metadata workflows, shared lifecycle commands, and Agent Script handoff -->

# Agent CLI Commands Reference

> Current `sf agent` and `sf org` commands relevant to Builder metadata workflows, shared agent lifecycle operations, and Agent Script handoff.

## Overview

This file focuses on:
- shared lifecycle commands that matter in Builder-heavy work
- legacy / non-Agent Script spec-driven commands that still exist
- Agent Script handoff points that should route to `sf-ai-agentscript`

---

## Shared Lifecycle Commands

### sf org create agent-user

Creates the default Service Agent running user in the target org.

```bash
sf org create agent-user --target-org <alias> --json
sf org create agent-user --first-name Service --last-name Agent --target-org <alias> --json
sf org create agent-user --base-username service-agent@corp.com --target-org <alias> --json
```

The command auto-assigns the standard Service Agent profile and system permission sets. Use the returned username for running-user configuration.

| Flag | Required | Description |
|------|----------|-------------|
| `--target-org` | Yes | Alias or username of the target org |
| `--first-name` | No | Override the default first name |
| `--last-name` | No | Override the default last name |
| `--base-username` | No | Username base; the CLI appends a unique suffix |
| `--api-version` | No | Override API version |
| `--json` | No | Return output as JSON |

### sf agent activate

Makes a published agent available to users.

```bash
# Manual / interactive activation
sf agent activate --api-name <AgentApiName> --target-org <alias>

# CI / deterministic activation of a known BotVersion
sf agent activate --api-name <AgentApiName> --version <n> --target-org <alias> --json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--api-name` | No | API name of the agent to activate; if omitted, the CLI prompts you to choose |
| `--target-org` | Yes | Alias or username of the target org |
| `--api-version` | No | Override the API version used for the request |
| `--version` | No | BotVersion number to activate (`vX` in metadata corresponds to `--version X`) |
| `--json` | No | Format output as JSON |

> If you use `--json` without `--version`, the CLI activates the latest agent version. Prefer `--version` for CI/CD and reproducible rollout scripts.

### sf agent deactivate

Deactivates an active agent before major updates.

```bash
# Manual / interactive deactivation
sf agent deactivate --api-name <AgentApiName> --target-org <alias>

# Script-friendly deactivation
sf agent deactivate --api-name <AgentApiName> --target-org <alias> --json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--api-name` | No | API name of the agent to deactivate; if omitted, the CLI prompts you to choose |
| `--target-org` | Yes | Alias or username of the target org |
| `--api-version` | No | Override the API version used for the request |
| `--json` | No | Format output as JSON |

---

## Builder / Non-Agent Script Workflows

### sf agent create

Creates a non-Agent Script agent from a spec file.

```bash
sf agent create --name "My Agent" --api-name My_Agent --spec <path-to-spec.yaml> --target-org <alias> --json
```

> **Legacy / non-Agent Script path.** This is not the default workflow for this repository.

| Flag | Required | Description |
|------|----------|-------------|
| `--name` | No | Name (label) of the new agent |
| `--api-name` | No | API name of the new agent |
| `--spec` | No | Path to the local agent spec file |
| `--target-org` | Yes | Alias or username of the target org |
| `--preview` | No | Preview the generated agent without saving it |
| `--json` | No | Return output as JSON |

### sf agent generate agent-spec

Generates an agent spec YAML file interactively or with flags.

```bash
# Interactive full interview
sf agent generate agent-spec --full-interview

# Non-interactive with key flags
sf agent generate agent-spec \
  --type customer \
  --role "Customer support specialist" \
  --company-name "Acme Corp" \
  --company-description "Enterprise SaaS provider" \
  --tone formal \
  --output-file ./agent-spec.yaml

# Iterative refinement of existing spec
sf agent generate agent-spec --spec ./agent-spec.yaml
```

| Flag | Required | Description |
|------|----------|-------------|
| `--type` | No | Agent type: `customer` or `internal` |
| `--role` | No | Agent's role description |
| `--company-name` | No | Company name for agent context |
| `--company-description` | No | Company description for grounding |
| `--company-website` | No | Company website URL for enrichment |
| `--tone` | No | Conversational tone: `formal`, `casual`, or `neutral` |
| `--full-interview` | No | Interactive prompt for all properties |
| `--spec` | No | Path to existing spec YAML for iterative refinement |
| `--prompt-template` | No | Custom prompt template for spec generation |
| `--grounding-context` | No | Additional context for grounding the agent |
| `--force-overwrite` | No | Overwrite existing output file without prompting |
| `--enrich-logs` | No | Include enrichment logs in output |
| `--max-topics` | No | Maximum number of topics to generate |
| `--agent-user` | No | Default agent user for the spec |
| `--output-file` | No | Path for the output spec YAML file |

> Keep this as an optional ideation/bootstrap path. It is not the default authoring model for `sf-ai-agentscript`.

### sf agent generate template

Generates a BotTemplate for ISV packaging via managed packages on AppExchange.

```bash
sf agent generate template \
  --agent-file force-app/main/default/bots/My_Agent/My_Agent.bot-meta.xml \
  --agent-version 1 \
  --output-dir my-package \
  --source-org my-scratch-org \
  --json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--agent-file` | Yes | Path to the `.bot-meta.xml` file |
| `--agent-version` | Yes | BotVersion number to template |
| `--output-dir` | No | Directory where generated `BotTemplate` and `GenAiPlannerBundle` files are saved |
| `--source-org` | Yes | Namespaced scratch org that contains the source agent |
| `--json` | No | Return output as JSON |

> **Important:** This command works with Bot / BotVersion metadata and **does not** package agents created from Agent Script files.

---

## Agent Script Handoff

The following commands belong to the Agent Script workflow and are documented in:
[../../sf-ai-agentscript/references/cli-guide.md](../../sf-ai-agentscript/references/cli-guide.md)

- `sf agent generate authoring-bundle`
- `sf agent validate authoring-bundle`
- `sf agent publish authoring-bundle`

### sf agent generate authoring-bundle

Generates an authoring bundle from an agent spec YAML file, or from default boilerplate when `--no-spec` is used. This is primarily an Agent Script workflow.

```bash
sf agent generate authoring-bundle --no-spec --name "My Agent" --target-org <alias> --json
sf agent generate authoring-bundle --spec ./agent-spec.yaml --name "My Agent" --target-org <alias> --json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--spec` | No | Path to the agent spec YAML file |
| `--no-spec` | No | Skip spec generation and use default boilerplate |
| `--name` | No | Name (label) of the new authoring bundle; required with `--json` |
| `--api-name` | No | API name of the new authoring bundle |
| `--output-dir` | No | Directory where the authoring bundle files are generated |
| `--force-overwrite` | No | Overwrite an existing local authoring bundle without prompting |
| `--target-org` | Yes | Alias or username of the target org |
| `--json` | No | Return output as JSON |

> Use `sf-ai-agentscript` when this command is the main task.

---

## Preview Commands

### sf agent preview

Previews agent behavior interactively. This command is interactive and does not support `--json`.

```bash
# Published / activated agent
sf agent preview --api-name <AgentApiName> --target-org <alias>

# Published / activated agent with debug output
sf agent preview --api-name <AgentApiName> --use-live-actions --apex-debug --output-dir ./logs --target-org <alias>

# Local authoring bundle by API name
sf agent preview --authoring-bundle <BundleApiName> --target-org <alias>
```

| Flag | Required | Description |
|------|----------|-------------|
| `--api-name` | Yes* | API name of the activated published agent |
| `--authoring-bundle` | Yes* | API name of the authoring bundle metadata component |
| `--target-org` | Yes | Alias or username of the target org |
| `--use-live-actions` | No | Execute real Apex/Flows instead of LLM simulation |
| `--output-dir` | No | Directory for preview output/logs |
| `--apex-debug` | No | Include Apex debug logs in output |

*One of `--api-name` or `--authoring-bundle` is required.

> GA preview session commands also exist: `sf agent preview start`, `sf agent preview send`, and `sf agent preview end`. For scripted smoke-test workflows, see `sf-ai-agentscript` and `sf-ai-agentforce-testing`.

---

## Cross-Skill References

| Command Area | Skill | Notes |
|-------------|-------|-------|
| Builder metadata, Prompt Builder, Models API | [../SKILL.md](../SKILL.md) | This skill |
| Agent Script `.agent` files and authoring bundles | [../../sf-ai-agentscript/SKILL.md](../../sf-ai-agentscript/SKILL.md) | Code-first agent development |
| Deployment orchestration, CI/CD | [../../sf-deploy/SKILL.md](../../sf-deploy/SKILL.md) | Agent deployment workflows |
| Test execution, coverage analysis | [../../sf-ai-agentforce-testing/SKILL.md](../../sf-ai-agentforce-testing/SKILL.md) | `sf agent test run/list/results` |
