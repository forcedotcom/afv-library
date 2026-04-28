# Agentforce Builder Scoring Rubric

## 100-point rubric

| Category | Points | What good looks like |
|---|---:|---|
| Agent configuration | 20 | Clear system guidance, correct agent user, usable welcome/error handling |
| Topic and action design | 25 | Strong routing descriptions, scoped topics, actions mapped to the right topic |
| Metadata quality | 20 | Valid GenAiFunction / GenAiPlugin structure, correct target types, clean I/O definitions |
| Integration patterns | 15 | Dependencies sequenced correctly, cross-skill orchestration used appropriately |
| Prompt / AI usage | 10 | GenAiPromptTemplate or Models API used only where it adds value |
| Deployment readiness | 10 | Validation complete, dependencies deployed, publish/activate flow understood |

## Thresholds

| Score | Meaning | Recommendation |
|---|---|---|
| 90–100 | Excellent | Ready to deploy |
| 80–89 | Very good | Minor cleanup only |
| 70–79 | Acceptable | Review before deploy |
| 60–69 | Needs work | Address issues before deploy |
| < 60 | Blocking | Do not deploy |

## Common downgrades

- vague topic descriptions
- unsupported / undeployed action targets
- missing or mismatched inputs/outputs
- trying to use Builder when Agent Script is the better fit
- forgetting that publish and activate are separate steps
