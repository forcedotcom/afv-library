<!-- Parent: sf-ai-agentforce-testing/SKILL.md -->

# Test Plan File Format

Test plans (`test-plan-{agent}.yaml`) capture the full interview output for reuse. See `assets/test-plan-template.yaml` for the complete schema.

## Key Sections

| Section | Purpose |
|---------|---------|
| `metadata` | Agent name, ID, org alias, timestamps |
| `credentials` | Path to `~/.sfagent/` credentials.env or `use_env: true` |
| `agent_metadata` | Topics, actions, type — populated by `agent_discovery.py` |
| `scenarios` | List of YAML scenario files + pattern filters |
| `partition` | Strategy (`by_category`/`by_count`/`sequential`) + worker count |
| `session_variables` | Context variables injected into every session |
| `execution` | Timeout, retry, verbose, rich output settings |

## Re-Running from a Saved Plan

When a user provides a test plan file, skip the interview entirely:

```
1. Load test-plan-{agent}.yaml
2. Validate credentials: credential_manager.py validate --org-alias {org} --eca-name {eca}
3. If invalid → ask user to update credentials only (skip other interview steps)
4. Load scenario files from plan
5. Apply partition strategy from plan
6. Execute (team or sequential based on worker_count)
```

This enables rapid re-runs after fixing agent issues — the user just says "re-run" and the skill picks up the saved plan.
