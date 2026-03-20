---
name: switching-org
description: Switches the active Salesforce org (default target-org) using the Salesforce CLI. Use whenever someone wants to change which org CLI commands run against — whether they say "switch org", "change default org", "set my org to", "use alias", "point to", or describe wanting to work against a specific org, scratch org, sandbox, or production.
compatibility: Salesforce CLI (sf) v2+
metadata:
  version: "1.0"
---

# switching-org

Switches the active Salesforce org (default target-org) using the Salesforce CLI (sf). Supports either a username or an alias.

## Steps

1. Identify the org: the user provides a username or alias (`orgIdentifier`). If not provided, run `sf org list` to show authenticated orgs and ask the user which one to use.
2. Set the default org:
   - Local (default): `sf config set target-org <orgIdentifier>`
     - Applies only within the current project directory. Use this for normal project work.
   - Global (only if user explicitly requests): `sf config set target-org <orgIdentifier> --global`
     - Applies system-wide across all directories. Use when working outside a project or when the user asks for global scope.
   - If this fails, report the error and suggest running `sf org login web` if the org may not be authorized.
3. Verify:
   - `sf config get target-org --json`
   - Output confirmation: `Switched org (<scope>): <value>`
4. If verification fails, report the error and advise running `sf config get target-org`.

## Official Documentation

- Salesforce CLI config (unified) reference (sf):
  https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_config_commands_unified.htm#cli_reference_config_set_unified

## Notes

- Unified CLI uses keys like `target-org` and `target-dev-hub`. Legacy sfdx keys (`defaultusername`, `defaultdevhubusername`) are deprecated in this context.
- The sf CLI does not have `--local` or `--scope` flags for config set. Local scope is the default behavior.
