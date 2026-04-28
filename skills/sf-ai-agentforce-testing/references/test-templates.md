<!-- Parent: sf-ai-agentforce-testing/SKILL.md -->

# Test Templates

## Multi-Turn Test Templates

| Template | Pattern | Scenarios | Location |
|----------|---------|-----------|----------|
| `multi-turn-topic-routing.yaml` | Topic switching | 4 | `assets/` |
| `multi-turn-context-preservation.yaml` | Context retention | 4 | `assets/` |
| `multi-turn-escalation-flows.yaml` | Escalation cascades | 4 | `assets/` |
| `multi-turn-comprehensive.yaml` | All 6 patterns | 6 | `assets/` |

## CLI Test Templates

| Template | Purpose | Location |
|----------|---------|----------|
| `basic-test-spec.yaml` | Quick start (3-5 tests) | `assets/` |
| `comprehensive-test-spec.yaml` | Full coverage (20+ tests) with context vars, metrics, custom evals | `assets/` |
| `context-vars-test-spec.yaml` | Context variable patterns (RoutableId, EndUserId, CaseId) | `assets/` |
| `custom-eval-test-spec.yaml` | Custom evaluations with JSONPath assertions (**⚠️ Spring '26 bug**) | `assets/` |
| `cli-auth-guardrail-tests.yaml` | Auth gate, guardrail, ambiguous routing, session tests (CLI) | `assets/` |
| `cli-deep-history-tests.yaml` | Deep conversation history patterns (protocol activation, mid-stage, opt-out, session persistence) | `assets/` |
| `guardrail-tests.yaml` | Security/safety scenarios | `assets/` |
| `escalation-tests.yaml` | Human handoff scenarios | `assets/` |
| `agentscript-test-spec.yaml` | Agent Script agents with conversationHistory pattern | `assets/` |
| `standard-test-spec.yaml` | Reference format | `assets/` |
