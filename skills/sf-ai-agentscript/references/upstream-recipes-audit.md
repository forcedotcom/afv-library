<!-- Parent: sf-ai-agentscript/SKILL.md -->

# Upstream Recipes Audit

> Audit target: [`trailheadapps/agent-script-recipes`](https://github.com/trailheadapps/agent-script-recipes)
>
> Audited against upstream commit: `9c9017691db4a90bc73189371d7d540e1d9f077c` (Mar 2026)

This document explains how this skill uses TrailheadApps as an input source without treating it as the sole source of truth.

## Audit Summary

**Verdict:** useful and worth tracking, but not authoritative by itself.

Use TrailheadApps for:
- example structures
- emerging syntax patterns
- recipe-style action and topic composition
- corroborating evidence when it matches official docs and downstream org behavior

Do **not** use TrailheadApps alone as the final truth for:
- Service Agent user requirements
- publish-time permission behavior
- `connection messaging:` / `connections:` syntax
- lifecycle hook runtime guarantees
- config field canonical naming

## What Upstream Confirms

| Upstream finding | Evidence | Our verdict | Action in this skill |
|---|---|---|---|
| `developer_name` is canonical | Commit `9aa5ee2` changed `.airules/AGENT_SCRIPT.md` from `agent_name` to `developer_name` | Confirmed | Keep `developer_name` as canonical |
| Always use `@actions.` prefixes | Commit `b790a6f` added explicit guidance for `run`, templates, and instruction text | Confirmed | Keep validator/doc guidance |
| `run @actions.X` does not work for reasoning-level utilities | Commit `25e6865` documents `run` resolving only against topic-level `actions:` with `target:` | Confirmed | Keep `instruction-resolution.md` and validator guidance |
| Employee Agents are now the dominant recipe model | Commit `60ca531` switched recipes to `AgentforceEmployeeAgent` | Confirmed | Treat upstream as Employee-Agent-heavy |

## Where Upstream Is Stale or Inconsistent

| Upstream pattern | Evidence | Our verdict | Guidance |
|---|---|---|---|
| `connections:` plural wrapper | `.airules/AGENT_SCRIPT.md` still shows `connections:` top-level ordering; `future_recipes/escalationPatterns` still uses it | Stale / contradicts downstream validation | Prefer `connection messaging:` only |
| Config `description:` shown as primary field | `.airules/AGENT_SCRIPT.md` config block and current recipes still use `description:` | Aligned with official/public usage | Prefer `description:` in public docs/examples; keep `agent_description:` compatibility in local tooling |
| `before_reasoning` removed from rules but still appears in recipes | Main rules removed it, but `future_recipes/customerServiceAgent` still uses it | Internally inconsistent | Keep lifecycle-hook docs, but be cautious about runtime guarantees |
| Service Agent coverage is weak | Current repo is almost entirely Employee-Agent examples and has effectively no real Service-Agent `.agent` corpus | Incomplete source for Service-Agent authoring | Prefer this skill's service-user and publish docs |

## Specific Upstream References Worth Knowing

### 1. `developer_name` migration
- Commit: `9aa5ee2`
- Meaning: upstream moved away from `agent_name` in `.airules/AGENT_SCRIPT.md`
- Impact: aligns with this skill's canonical field choice

### 2. Bare action name fix
- Commit: `b790a6f`
- Meaning: upstream now explicitly warns against bare action names and recommends `@actions.` references everywhere
- Impact: supports this skill's validator rule

### 3. `run @actions.X` scope clarification
- Commit: `25e6865`
- Meaning: `run` resolves against topic-level target-backed actions, not reasoning-level utilities like `@utils.setVariables`
- Impact: supports this skill's instruction-resolution guidance

### 4. Employee-Agent bias
- Commit: `60ca531`
- Meaning: recipes moved broadly toward Employee Agent examples
- Impact: upstream is now less representative of Service Agent deployment realities

## Maintenance Policy for This Skill

When upstream and local evidence disagree, use this priority order:

1. official Salesforce docs
2. local `sf agent validate` / `preview` / `publish` behavior in real orgs
3. this skill's TDD and field validation corpus
4. upstream/community examples

## Recommended Ongoing Audit Checklist

When reviewing new TrailheadApps commits, specifically check for:
- config field changes (`developer_name`, `description`, `agent_type`, and any compatibility behavior around `agent_description`)
- lifecycle hook additions/removals
- connection block syntax
- target protocol examples (`flow://`, `apex://`, `prompt://`)
- Service vs Employee agent assumptions
- examples that contradict known publish/runtime behavior

## Current Decision Log

- **Adopted from upstream:** `developer_name`, public config `description:`, `@actions.` prefix guidance, `run` vs utility clarification
- **Not adopted from upstream:** plural `connections:` wrapper, implicit Employee-Agent bias as general guidance
- **Handled cautiously:** lifecycle hooks and `run` inside lifecycle hooks
