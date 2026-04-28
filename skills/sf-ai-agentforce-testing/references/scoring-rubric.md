<!-- Parent: sf-ai-agentforce-testing/SKILL.md -->

# Scoring System (100 Points)

| Category | Points | Key Rules |
|----------|--------|-----------|
| **Topic Selection Coverage** | 15 | All topics have test cases; various phrasings tested |
| **Action Invocation** | 15 | All actions tested with valid inputs/outputs |
| **Multi-Turn Topic Re-matching** | 15 | Topic switching accuracy across turns |
| **Context Preservation** | 15 | Information retention across turns |
| **Edge Case & Guardrail Coverage** | 15 | Negative tests; guardrails; escalation |
| **Test Spec / Scenario Quality** | 10 | Proper YAML; descriptions; clear expectations |
| **Agentic Fix Success** | 15 | Auto-fixes resolve issues within 3 attempts |

## Scoring Thresholds

```
⭐⭐⭐⭐⭐ 90-100 pts → Production Ready
⭐⭐⭐⭐   80-89 pts → Good, minor improvements
⭐⭐⭐    70-79 pts → Acceptable, needs work
⭐⭐      60-69 pts → Below standard
⭐        <60 pts  → BLOCKED - Major issues
```
