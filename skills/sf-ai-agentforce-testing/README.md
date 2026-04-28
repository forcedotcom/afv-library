# sf-ai-agentforce-testing

Comprehensive Agentforce testing skill with test execution, coverage analysis, and agentic fix loops. Test agents, analyze topic/action coverage, and automatically fix failing agents.

## Features

- **Test Execution**: Run agent tests via sf CLI with result analysis
- **Test Spec Generation**: Create YAML test specifications
- **Coverage Analysis**: Topic selection, action invocation coverage
- **Preview Mode**: Interactive simulated and live agent testing
- **Agentic Fix Loop**: Automatically fix failing agents and re-test
- **100-Point Scoring**: Validation across 5 categories

## Installation

```bash
# Install as part of sf-skills
npx skills add Jaganpro/sf-skills

# Or install just this skill
npx skills add Jaganpro/sf-skills --skill sf-ai-agentforce-testing
```

## Quick Start

### 1. Invoke the skill

```
Skill: sf-ai-agentforce-testing
Request: "Run agent tests for Customer_Support_Agent in org dev"
```

### 2. Common operations

| Operation | Example Request |
|-----------|-----------------|
| Run tests | "Run agent tests for MyAgent in org dev" |
| Generate spec | "Generate test spec for Customer_Support_Agent" |
| Preview agent | "Preview MyAgent with simulated actions" |
| Live preview | "Test MyAgent with live actions" |
| Coverage report | "Show topic coverage for MyAgent" |
| Fix loop | "Run agent tests and fix failures automatically" |

## Key Commands

⚠️ **Agent Testing Center Required**: Commands marked with 🔒 require Agent Testing Center feature enabled in org.

```bash
# Check if Agent Testing Center is available
sf agent test list --target-org [alias]
# Error "INVALID_TYPE" or "Not available" = NOT enabled

# Generate test specification (interactive only - no --api-name flag)
sf agent generate test-spec --output-file ./tests/spec.yaml

# 🔒 Create test in org (requires Agent Testing Center)
sf agent test create --spec ./tests/spec.yaml --target-org [alias]

# 🔒 Run agent tests (requires Agent Testing Center)
sf agent test run --api-name AgentName --wait 10 --result-format json --target-org [alias]

# Get test results
sf agent test results --job-id JOB_ID --result-format json --target-org [alias]

# Interactive preview (works WITHOUT Agent Testing Center)
sf agent preview --api-name AgentName --target-org [alias]

# Interactive preview (live actions)
sf agent preview --api-name AgentName --use-live-actions --target-org [alias]
```

> `sf agent preview` still uses simulated mode by default for the interactive REPL.
> For programmatic preview sessions, authoring bundles now require an explicit mode on `sf agent preview start`: `--simulate-actions` or `--use-live-actions`.

## Scoring System (100 Points)

| Category | Points | Focus |
|----------|--------|-------|
| Topic Selection | 25 | All topics have test cases |
| Action Invocation | 25 | All actions tested with I/O |
| Edge Case Coverage | 20 | Negative tests, boundaries |
| Test Spec Quality | 15 | Proper YAML, descriptions |
| Agentic Fix Success | 15 | Auto-fixes resolve issues |

## Test Thresholds

| Level | Score | Meaning |
|-------|-------|---------|
| Production Ready | 90+ | Deploy with confidence |
| Good | 80-89 | Minor improvements needed |
| Acceptable | 70-79 | Needs work before production |
| Blocked | <70 | Major issues to resolve |

## Cross-Skill Integration

| Related Skill | When to Use |
|---------------|-------------|
| sf-ai-agentscript | Create/fix agent scripts (recommended) |
| sf-ai-agentforce | Agentforce platform setup (Agent Builder, GenAi metadata) |
| sf-connected-apps | External Client App setup for Agent Runtime API testing |
| sf-data | Generate test data for actions |
| sf-flow | Fix failing Flow actions |
| sf-debug | Analyze agent error logs |

## Agentic Test-Fix Loop

When enabled, the skill will:
1. Run agent tests and capture failures
2. Analyze failure types (topic routing, action invocation, guardrails)
3. Call sf-ai-agentscript to generate fixes
4. Re-validate and re-publish agent
5. Re-run tests (max 3 iterations)
6. Report final status

## Documentation

- [CLI Commands Reference](references/cli-commands.md)
- [Test Spec Reference](references/test-spec-reference.md)
- [Connected App Setup](references/connected-app-setup.md)
- [Coverage Analysis](references/coverage-analysis.md)
- [Agentic Fix Loops](references/agentic-fix-loops.md)

## Requirements

- sf CLI v2
- Target Salesforce org with Agentforce enabled
- Agent published and activated for testing
- Standard org auth for CLI preview (`sf org login web`)

## License

MIT License. See LICENSE file.
Copyright (c) 2024-2025 Jag Valaiyapathy
