<!-- Parent: sf-ai-agentforce-testing/SKILL.md -->

# 4-Step Interview Flow (Testing Center Wizard)

When the testing skill is invoked, follow these 4 steps in order.
Each step mirrors one tab of the Salesforce Testing Center "New Test" wizard.

> **Skip the interview** if the user provides a `test-plan-{agent}.yaml` file — load it directly and jump to execution.

## Step 1: Basic Information

| Input | Source | Fallback |
|-------|--------|----------|
| Skill Path | Auto-resolve from `${SKILL_HOOKS}` env var (strip `/hooks` suffix). If unset → hardcoded `~/.claude/skills/sf-ai-agentforce-testing`. | Hardcoded path |
| Agent Name | User provided or auto-discover via `agent_discovery.py` | AskUserQuestion |
| Org Alias | User provided or `.sf/config.json` → `target-org` | AskUserQuestion |
| Description | ALWAYS ask — used for test generation context | AskUserQuestion |
| Test Type | User selects: CLI / API / Both | AskUserQuestion |

```
AskUserQuestion:
  questions:
    - question: "Which agent do you want to test?"
      header: "Agent"
      options:
        - label: "Discover from org (Recommended)"
          description: "Auto-discover agents via agent_discovery.py live"
        - label: "I know the API name"
          description: "I'll provide the BotDefinition DeveloperName directly"
    - question: "What is your target org alias?"
      header: "Org"
      options:
        - label: "{auto-detected org alias} (Recommended)"
          description: "Detected from .sf/config.json target-org"
        - label: "Different org"
          description: "I'll provide a different org alias"
    - question: "What is this test suite validating?"
      header: "Description"
      options:
        - label: "Topic routing accuracy"
          description: "Verify utterances route to correct topics"
        - label: "Guardrail & safety compliance"
          description: "Test deflection, injection, and abuse handling"
        - label: "Full agent coverage"
          description: "Comprehensive coverage across all topics, actions, and edge cases"
    - question: "What type of testing?"
      header: "Test Type"
      options:
        - label: "CLI Testing Center (Recommended)"
          description: "Single-utterance tests via sf agent test — no ECA required"
        - label: "Multi-turn API"
          description: "Multi-turn conversations via Agent Runtime API — requires ECA"
        - label: "Both"
          description: "CLI tests first, then multi-turn API for conversation flow validation"
```

**Auto-runs after Step 1:**
- Skill path resolution (`SKILL_HOOKS` env var or hardcoded fallback)
- Agent metadata retrieval: `python3 {SKILL_PATH}/hooks/scripts/agent_discovery.py live --target-org {org} --agent-name {agent}`
- Testing Center availability check: `sf agent test list -o {org}`

## Step 2: Test Conditions

| Input | Source | Fallback |
|-------|--------|----------|
| Context Variables | Extract from agent metadata (`attributeMappings` where `mappingType=ContextVariable`) | AskUserQuestion |
| Record IDs | User provides or auto-discover from org | AskUserQuestion |
| Credentials | Auto-discover via `credential_manager.py` (API only) | AskUserQuestion |

```
AskUserQuestion:
  questions:
    - question: "Your agent uses context variables: {discovered_vars}. Provide test record IDs?"
      header: "Variables"
      options:
        - label: "Use test record IDs (Recommended)"
          description: "I'll provide real MessagingSession and Case IDs for testing"
        - label: "Auto-discover from org"
          description: "Query the org for recent MessagingSession and Case records"
        - label: "Skip context variables"
          description: "WARNING: Auth topics will likely fail without RoutableId + CaseId"
    - question: "How should conversation history be set up?"
      header: "History"
      options:
        - label: "Single-turn only (Recommended for CLI)"
          description: "Each test is an independent utterance — no prior context"
        - label: "Include multi-turn patterns"
          description: "Add conversationHistory entries for context retention tests"
```

> **⚠️ WARNING:** If the agent has a `User_Authentication` topic, you MUST provide `$Context.RoutableId` and `$Context.CaseId`. Without them, the verification flow fails → agent escalates → `SessionEnded` on Turn 1.

## Step 3: Test Data (HUMAN-IN-THE-LOOP)

Claude generates test cases based on agent metadata, then presents for review.

**Generation inputs:**
- Agent topics + `classificationDescription` from each topic
- System instructions + guardrails from agent metadata
- Description from Step 1 (guides test focus)
- Context variables from Step 2

**Generation rules:**
- ALWAYS include `expectedOutcome` with behavioral description
- Group by category: auth routing, escalation, guardrail, edge cases, global instructions
- Include `$Context.` variables on every test case that needs session context
- Omit `expectedTopic` for ambiguous routing — use `expectedOutcome` instead
- Add `# Description:` comment block at the top of each YAML file

```
AskUserQuestion:
  questions:
    - question: "I generated {N} test cases across {M} categories. Review the test plan?"
      header: "Review"
      options:
        - label: "Approve all (Recommended)"
          description: "Deploy and run all generated test cases as-is"
        - label: "Add more tests"
          description: "I'll suggest additional scenarios to cover"
        - label: "Remove tests"
          description: "I'll identify tests to remove from the suite"
        - label: "Edit specific tests"
          description: "I'll modify specific utterances or expected values"
```

## Step 4: Evaluations & Deploy

```
AskUserQuestion:
  questions:
    - question: "Which quality metrics to include?"
      header: "Metrics"
      multiSelect: true
      options:
        - label: "coherence (Recommended)"
          description: "Response clarity and logical flow — scores 4-5 for clear responses"
        - label: "output_latency_milliseconds (Recommended)"
          description: "Raw latency in ms — useful for performance baselining"
        - label: "instruction_following (CLI only — crashes UI)"
          description: "Whether agent follows instructions. Works in CLI but breaks Testing Center UI"
    - question: "Deploy and run strategy?"
      header: "Strategy"
      options:
        - label: "Swarm: parallel deploy+run (Recommended for 3+ suites)"
          description: "Use agent teams to deploy and run suites in parallel — fastest for large test sets"
        - label: "Sequential: one suite at a time"
          description: "Deploy and run each suite sequentially — simpler but slower"
```

**After confirmation:**
1. Save test plan as `test-plan-{agent_name}.yaml`
2. Deploy suites via `sf agent test create --spec`
3. Run suites via `sf agent test run`
4. Collect results via `sf agent test results --job-id`
5. Present formatted results summary
