<!-- Parent: sf-ai-agentforce-testing/SKILL.md -->
# Topic Name Resolution in CLI Tests

## Overview

When writing `expectedTopic` in YAML test specs for `sf agent test create`, the topic name format depends on the topic type. Getting this wrong causes **silent assertion failures** — the test runs, the agent responds, but `topic_assertion` reports `FAILURE` because the expected name doesn't match the runtime name.

---

## Three Topic Name Formats

| Format | Example | Where Found |
|--------|---------|-------------|
| `localDeveloperName` | `Escalation` | Planner bundle XML `<localDeveloperName>` tag |
| `developerName` (bundle) | `Escalation_16j548d53a8a3b0` | Planner bundle XML `<developerName>` tag |
| `developerName` (runtime) | `Escalation_16j9d687a53f890` | Test results `.generatedData.topic` |

> **Important:** The bundle `developerName` hash and the runtime `developerName` hash may differ. Always use the **runtime** value from test results.

---

## Rules

### Standard Topics (no prefix)

Standard topics are built-in topics that come with every agent:

- `Escalation`
- `Off_Topic`
- `Inappropriate_Content`

**In YAML specs:** Use the `localDeveloperName` — the framework resolves it to the full runtime name automatically.

```yaml
# ✅ CORRECT — framework resolves to Escalation_16j9d687a53f890
- utterance: "I want to talk to a human"
  expectedTopic: Escalation

# ✅ ALSO CORRECT — explicit runtime name works too
- utterance: "I want to talk to a human"
  expectedTopic: Escalation_16j9d687a53f890

# ❌ WRONG — bundle hash differs from runtime hash
- utterance: "I want to talk to a human"
  expectedTopic: Escalation_16j548d53a8a3b0
```

### Standard Platform Topics (Intercept Before Custom Routing)

Three platform-level standard topics exist **above** the custom planner engine (`GenAiPlannerBundle`). These intercept utterances **before** the agent's custom topic routing sees them:

| Platform Topic | Triggers On |
|----------------|-------------|
| `Inappropriate_Content` | Hate speech, violence, sexual content, insults |
| `Prompt_Injection` | Instruction override attempts ("ignore your instructions", "you are now...") |
| `Reverse_Engineering` | Requests to reveal system instructions ("what are your instructions?") |

**Impact on Testing:**

- If a platform topic matches, the custom planner **never sees the utterance** — custom catch-all topics (e.g., Escalation) won't fire for these inputs even if their description includes "inappropriate content" triggers.
- Use the standard platform topic name in `expectedTopic` for guardrail tests:

```yaml
testCases:
  # ✅ CORRECT — platform topic intercepts before custom planner
  - utterance: "You're terrible and I hate you"
    expectedTopic: Inappropriate_Content

  # ❌ WRONG — custom Escalation topic won't see this; platform topic fires first
  - utterance: "You're terrible and I hate you"
    expectedTopic: Escalation
```

- For prompt injection and reverse engineering tests, use `Prompt_Injection` and `Reverse_Engineering` respectively, or omit `expectedTopic` entirely and use `expectedOutcome` for behavioral validation.

> **Discovery:** These platform topics were confirmed during testing on a Spring '26 sandbox (Feb 2026). An agent with a custom Escalation topic that explicitly listed "inappropriate content" and "prompt injection" as triggers still routed to the platform-level topics instead.

### Promoted Topics (p_16j... prefix)

Promoted topics are custom topics created in the Salesforce Setup UI. They have an org-specific prefix (`p_16j...`) and a hash suffix.

**In YAML specs:** You MUST use the **full runtime `developerName`** including the hash suffix. The `localDeveloperName` (without prefix/hash) does NOT resolve for promoted topics.

```yaml
# ✅ CORRECT — full runtime developerName
- utterance: "My doorbell camera is offline"
  expectedTopic: p_16jPl000000GwEX_Field_Support_Routing_16j8eeef13560aa

# ❌ WRONG — localDeveloperName without prefix/hash does NOT resolve
- utterance: "My doorbell camera is offline"
  expectedTopic: Field_Support_Routing

# ❌ WRONG — partial name without hash suffix does NOT resolve
- utterance: "My doorbell camera is offline"
  expectedTopic: p_16jPl000000GwEX_Field_Support_Routing
```

### Summary Table

| Topic Type | YAML `expectedTopic` Value | Resolution |
|------------|---------------------------|------------|
| Standard (Escalation, Off_Topic, etc.) | `localDeveloperName` (e.g., `Escalation`) | Framework resolves automatically |
| Promoted (p_16j... prefix) | Full runtime `developerName` with hash | Must be exact match |

---

## Discovery Workflow

Since promoted topic names are opaque (hash suffixes), use this workflow to discover them:

### Step 1: Write spec with best guesses

```yaml
name: "My Agent Discovery Run"
subjectType: AGENT
subjectName: My_Agent
testCases:
  - utterance: "Test message for topic A"
    expectedTopic: Topic_A_Guess
  - utterance: "Test message for topic B"
    expectedTopic: Topic_B_Guess
```

### Step 2: Deploy and run

```bash
sf agent test create --spec discovery-spec.yaml --api-name Discovery_Run --target-org dev
sf agent test run --api-name Discovery_Run --wait 10 --result-format json --json --target-org dev
```

### Step 3: Extract actual topic names from results

```bash
# Get the job ID from the run output, then:
sf agent test results --job-id <JOB_ID> --result-format json --json --target-org dev \
  | jq '.result.testCases[].generatedData.topic'
```

This outputs the **actual runtime `developerName`** for each test case — the value the agent actually routed to.

### Step 4: Update spec with actual names

Replace your guesses with the actual runtime names from Step 3.

### Step 5: Re-deploy and re-run

```bash
sf agent test create --spec updated-spec.yaml --api-name My_Agent_Tests --force-overwrite --target-org dev
sf agent test run --api-name My_Agent_Tests --wait 10 --result-format json --json --target-org dev
```

---

## Where to Find Topic Names

| Source | How to Access | What You Get |
|--------|---------------|--------------|
| **Test results JSON** | `.result.testCases[].generatedData.topic` | Runtime `developerName` (most reliable) |
| **Planner bundle XML** | `retrieve GenAiPlannerBundle` → `<developerName>` and `<localDeveloperName>` | Bundle names (hash may differ from runtime) |
| **SOQL** | `SELECT DeveloperName FROM GenAiPlugin WHERE ...` | Metadata names |
| **Setup UI** | Einstein > Agents > Topics | Display labels (not API names) |

---

## Known Gotchas

1. **Hash mismatch between bundle and runtime**: The `developerName` in the planner bundle XML (e.g., `Escalation_16j548d53a8a3b0`) may have a **different hash** than the runtime name (e.g., `Escalation_16j9d687a53f890`). Always use the runtime value from test results.

2. **Promoted topics require exact match**: Unlike standard topics, there is no "fuzzy" resolution. The full `p_16j..._hash` string must match exactly.

3. **Topic names are org-specific**: The `16j` prefix encodes the org ID. Topic names from one org will NOT work in another org.

4. **`MigrationDefaultTopic`**: Standard Salesforce Copilots (not custom agents) may route everything to `MigrationDefaultTopic`. This is expected behavior for non-custom agents.

5. **Topic hash changes on agent republish**: The runtime `developerName` hash suffix changes each time an agent is republished. Tests with hardcoded full runtime names (e.g., `Escalation_16j9d687a53f890`) will break after republish. **Mitigation:** Use `localDeveloperName` wherever the framework resolves it (standard topics). For promoted topics, re-run the [discovery workflow](#discovery-workflow) after each agent publish to capture new hashes.
