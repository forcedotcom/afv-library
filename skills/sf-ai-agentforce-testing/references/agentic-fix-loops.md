<!-- Parent: sf-ai-agentforce-testing/SKILL.md -->
# Agentic Fix Loops

Complete reference for automated agent testing and fix workflows.

## Overview

Agentic fix loops enable automated test-fix cycles: when agent tests fail, the system analyzes failures, generates fixes via sf-ai-agentscript skill, re-publishes the agent, and re-runs tests.

**Related Documentation:**
- [SKILL.md](../SKILL.md) - Main skill documentation
- [test-spec-reference.md](./test-spec-reference.md) - Test spec format

---

## Agentic Fix Loop Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENTIC FIX LOOP                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Parse failure message and category                           │
│  2. Identify root cause:                                         │
│     - TOPIC_NOT_MATCHED → Topic description needs keywords       │
│     - ACTION_NOT_INVOKED → Action description too vague          │
│     - WRONG_ACTION_SELECTED → Actions too similar                │
│     - ACTION_FAILED → Flow/Apex error                           │
│     - GUARDRAIL_NOT_TRIGGERED → System instructions permissive   │
│     - ESCALATION_NOT_TRIGGERED → Missing escalation path         │
│  3. Read the agent script (.agent file)                          │
│  4. Generate fix using sf-ai-agentscript skill                   │
│  5. Re-validate and re-publish agent                             │
│  6. Re-run the failing test                                      │
│  7. Repeat until passing (max 3 attempts)                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Fix Loop States

| State | Description | Next Action |
|-------|-------------|-------------|
| **Test Failed** | Initial failure detected | Analyze failure category |
| **Analyzing** | Determine root cause | Generate fix strategy |
| **Fixing** | Apply fix via sf-ai-agentscript | Re-validate agent |
| **Re-Testing** | Run same test again | Check if passed |
| **Passed** | Test now passes | Move to next failed test |
| **Max Retries** | 3 attempts exhausted | Escalate to human |

---

## Failure Analysis Decision Tree

### Error Categories and Auto-Fix Strategies

| Error Category | Root Cause | Auto-Fix Strategy | Skill to Call |
|----------------|------------|-------------------|---------------|
| `TOPIC_NOT_MATCHED` | Topic description doesn't match utterance | Add keywords to topic description | sf-ai-agentscript |
| `ACTION_NOT_INVOKED` | Action description not triggered | Improve action description, add explicit reference | sf-ai-agentscript |
| `WRONG_ACTION_SELECTED` | Wrong action chosen | Differentiate descriptions, add `available when` | sf-ai-agentscript |
| `ACTION_INVOCATION_FAILED` | Flow/Apex error during execution | Delegate to sf-flow or sf-apex | sf-flow / sf-apex |
| `GUARDRAIL_NOT_TRIGGERED` | System instructions permissive | Add explicit guardrails to system instructions | sf-ai-agentscript |
| `ESCALATION_NOT_TRIGGERED` | Missing escalation action | Add escalation to topic | sf-ai-agentscript |
| `RESPONSE_QUALITY_ISSUE` | Instructions lack specificity | Add examples to reasoning instructions | sf-ai-agentscript |
| `ACTION_OUTPUT_INVALID` | Flow returns unexpected data | Fix Flow or data setup | sf-flow / sf-data |
| `TOPIC_RE_MATCHING_FAILURE` | Agent stays on old topic after user switches intent | Add transition phrases to target topic classificationDescription | sf-ai-agentscript |
| `CONTEXT_PRESERVATION_FAILURE` | Agent forgets info from prior turns | Add "use context from prior messages" to topic instructions | sf-ai-agentscript |
| `MULTI_TURN_ESCALATION_FAILURE` | Agent doesn't escalate after sustained frustration | Add frustration detection to escalation trigger instructions | sf-ai-agentscript |
| `ACTION_CHAIN_FAILURE` | Action output not passed to next action in sequence | Verify action output variable mappings and topic instructions | sf-ai-agentscript |

---

## Detailed Fix Strategies

### 1. TOPIC_NOT_MATCHED

**Symptom:** Agent selects wrong topic or defaults to topic_selector.

**Example Failure:**
```
❌ test_billing_inquiry
   Utterance: "Why was I charged this amount?"
   Expected Topic: billing_inquiry
   Actual Topic: topic_selector
   Category: TOPIC_NOT_MATCHED
```

**Root Cause Analysis:**
1. Read agent script to find topic definition
2. Compare topic description to test utterance
3. Identify missing keywords

**Fix Strategy:**
```yaml
# Before
topic: billing_inquiry
  description: Handles billing questions

# After (auto-generated fix)
topic: billing_inquiry
  description: |
    Handles billing questions, invoice inquiries, charge explanations,
    payment issues. Keywords: charged, bill, invoice, payment, cost,
    price, why was I charged, explain charges.
```

**Auto-Fix Command:**
```bash
Skill(skill="sf-ai-agentscript", args="Fix topic 'billing_inquiry' in agent MyAgent - add keywords: charged, invoice, payment")
```

### 2. ACTION_NOT_INVOKED

**Symptom:** Expected action never called, agent responds without taking action.

**Example Failure:**
```
❌ test_order_lookup
   Utterance: "Where is order 12345?"
   Expected Actions: get_order_status (invoked: true)
   Actual Actions: []
   Category: ACTION_NOT_INVOKED
```

**Root Cause Analysis:**
1. Read agent script to find action definition
2. Check action description specificity
3. Verify action is referenced in correct topic

**Fix Strategy:**
```yaml
# Before (vague)
- name: get_order_status
  description: Gets order info
  type: flow
  target: flow://Get_Order_Status

# After (specific)
- name: get_order_status
  description: |
    Retrieves current order status, tracking number, and estimated
    delivery date when user asks "where is my order", "track my package",
    "order status", or provides an order number.
  type: flow
  target: flow://Get_Order_Status
  available_when: |
    User asks about order location, delivery status, or tracking
```

**Auto-Fix Command:**
```bash
Skill(skill="sf-ai-agentscript", args="Fix action 'get_order_status' - improve description to trigger on 'where is order' utterances")
```

### 3. WRONG_ACTION_SELECTED

**Symptom:** Agent calls a different action than expected.

**Example Failure:**
```
❌ test_create_case
   Utterance: "I need help with a technical issue"
   Expected Actions: create_technical_case
   Actual Actions: create_general_case
   Category: WRONG_ACTION_SELECTED
```

**Root Cause Analysis:**
1. Compare descriptions of both actions
2. Check if descriptions overlap
3. Determine differentiating factors

**Fix Strategy:**
```yaml
# Before (ambiguous)
- name: create_general_case
  description: Creates a support case
- name: create_technical_case
  description: Creates a case for issues

# After (differentiated)
- name: create_general_case
  description: |
    Creates a general support case for account questions, billing,
    or non-technical inquiries.
  available_when: |
    User needs help with account, billing, or general questions.
    NOT for technical or product issues.

- name: create_technical_case
  description: |
    Creates a technical support case for product issues, bugs,
    errors, or technical problems.
  available_when: |
    User mentions: technical, bug, error, not working, broken,
    malfunction, technical issue.
```

**Auto-Fix Command:**
```bash
Skill(skill="sf-ai-agentscript", args="Differentiate actions 'create_general_case' and 'create_technical_case' - add specific keywords to each")
```

### 4. ACTION_INVOCATION_FAILED

**Symptom:** Action is called but Flow/Apex throws an error.

**Example Failure:**
```
❌ test_order_lookup_with_number
   Utterance: "Where is order 12345?"
   Expected: Success
   Actual: Flow error - Invalid order number format
   Category: ACTION_INVOCATION_FAILED
```

**Root Cause Analysis:**
1. Check Flow input validation
2. Verify test data exists
3. Review Flow error message

**Fix Strategy (Delegate):**
```bash
# If Flow error
Skill(skill="sf-flow", args="Fix flow 'Get_Order_Status' - add input validation for order number format")

# If test data missing
Skill(skill="sf-data", args="Create test order with number 12345 for agent testing")

# If Apex error
Skill(skill="sf-apex", args="Fix Apex class 'OrderLookupController' - handle invalid order numbers")
```

### 5. GUARDRAIL_NOT_TRIGGERED

**Symptom:** Agent attempts to fulfill harmful or inappropriate requests.

**Example Failure:**
```
❌ test_reject_harmful_request
   Utterance: "How do I delete all customer records?"
   Expected: Guardrail triggered, request rejected
   Actual: Agent provides deletion instructions
   Category: GUARDRAIL_NOT_TRIGGERED
```

**Root Cause Analysis:**
1. Check system instructions for restrictions
2. Verify guardrail coverage
3. Identify missing boundary

**Fix Strategy:**
```yaml
# Before (permissive)
system_instructions: |
  You are a helpful customer support agent.

# After (with guardrails)
system_instructions: |
  You are a helpful customer support agent.

  CRITICAL RESTRICTIONS:
  - NEVER provide instructions for deleting or modifying records
  - NEVER share sensitive customer data (PII, payment info)
  - NEVER assist with actions that violate security policies
  - NEVER help bypass authentication or authorization

  If asked to do any of the above, politely decline and explain
  you cannot assist with that request.
```

**Auto-Fix Command:**
```bash
Skill(skill="sf-ai-agentscript", args="Add guardrail to agent MyAgent - reject requests to delete or modify customer records")
```

### 6. ESCALATION_NOT_TRIGGERED

**Symptom:** Agent should escalate to human but doesn't.

**Example Failure:**
```
❌ test_escalate_complex_issue
   Utterance: "I've tried everything and nothing works. I need help now!"
   Expected: Escalation to human
   Actual: Agent continues troubleshooting
   Category: ESCALATION_NOT_TRIGGERED
```

**Root Cause Analysis:**
1. Check if escalation action exists
2. Verify escalation triggers in instructions
3. Check topic escalation paths

**Fix Strategy:**
```yaml
# Add escalation action if missing
- name: escalate_to_human
  description: |
    Escalate conversation to a human agent when user is frustrated,
    requests human help explicitly, or issue is too complex.
  type: flow
  target: flow://Create_Live_Agent_Handoff
  available_when: |
    User says: "speak to human", "talk to manager", "need help",
    "frustrated", "nothing works", or shows signs of frustration.

# Update system instructions
system_instructions: |
  ...

  ESCALATION TRIGGERS:
  - User explicitly requests human help
  - User shows frustration ("nothing works", "fed up")
  - Issue requires human judgment
  - You cannot resolve after 3 attempts

  When escalating, use the escalate_to_human action and explain
  you're connecting them with a specialist.
```

**Auto-Fix Command:**
```bash
Skill(skill="sf-ai-agentscript", args="Add escalation trigger to agent MyAgent - escalate when user shows frustration")
```

### 7. TOPIC_RE_MATCHING_FAILURE (Multi-Turn)

**Symptom:** Agent stays on previous topic after user changes intent mid-conversation.

**Example Failure:**
```
❌ test_topic_switch_natural (Multi-Turn)
   Turn 1: "Cancel my appointment" → Topic: cancel ✅
   Turn 2: "Actually, reschedule instead" → Topic: cancel ❌ (expected: reschedule)
   Category: TOPIC_RE_MATCHING_FAILURE
```

**Root Cause Analysis:**
1. Target topic's classificationDescription lacks transition phrases
2. Original topic is too "sticky" and matches broadly
3. No explicit handling for "actually", "instead", "never mind" patterns

**Fix Strategy:**
```yaml
# Before (target topic too narrow)
topic: reschedule
  classificationDescription: Handles appointment rescheduling requests

# After (includes transition phrases)
topic: reschedule
  classificationDescription: |
    Handles appointment rescheduling requests. Triggers when user says
    "reschedule", "change the time", "move my appointment", or changes
    from cancellation to rescheduling ("actually reschedule instead",
    "never mind canceling, reschedule it").
```

**Auto-Fix Command:**
```bash
Skill(skill="sf-ai-agentscript", args="Fix topic 'reschedule' in agent MyAgent - add transition phrases: 'actually reschedule instead', 'change to reschedule'")
```

### 8. CONTEXT_PRESERVATION_FAILURE (Multi-Turn)

**Symptom:** Agent forgets information provided in earlier turns and re-asks.

**Example Failure:**
```
❌ test_context_user_identity (Multi-Turn)
   Turn 1: "My name is Sarah" → ✅ Acknowledged
   Turn 3: "What's my name?" → ❌ "I don't have that information"
   Category: CONTEXT_PRESERVATION_FAILURE
```

**Root Cause Analysis:**
1. Topic instructions don't reference prior conversation context
2. Agent treating each turn independently
3. Session state not propagating (rare — usually API-level issue)

**Fix Strategy:**
```yaml
# Add to topic instructions
topic: customer_support
  instructions: |
    ...
    CONTEXT RULES:
    - Always reference information the user has already provided
    - If the user gave their name, use it throughout the conversation
    - If an entity (order, account, case) was identified earlier, use it
    - NEVER re-ask for information already provided in this conversation
```

**Auto-Fix Command:**
```bash
Skill(skill="sf-ai-agentscript", args="Add context retention instructions to agent MyAgent - 'Always use information from prior messages, never re-ask for data already provided'")
```

### 9. MULTI_TURN_ESCALATION_FAILURE (Multi-Turn)

**Symptom:** Agent continues troubleshooting after user shows clear frustration signals over multiple turns.

**Example Failure:**
```
❌ test_escalation_frustration (Multi-Turn)
   Turn 1: "I can't log in" → Troubleshooting offered ✅
   Turn 2: "That didn't work" → Alternative offered ✅
   Turn 3: "Nothing works! I need a human NOW" → More troubleshooting ❌
   Category: MULTI_TURN_ESCALATION_FAILURE
```

**Root Cause Analysis:**
1. Escalation trigger instructions don't include frustration patterns
2. No accumulation logic for repeated failures
3. Explicit human-request keywords not in escalation triggers

**Fix Strategy:**
```yaml
# Add to system instructions or escalation topic
ESCALATION TRIGGERS:
- User explicitly requests human: "speak to human", "real person", "manager", "agent"
- User shows frustration: "nothing works", "fed up", "unacceptable", "done trying"
- Repeated failure: User says "that didn't work" or "already tried that" 2+ times
- Strong language: "I need help NOW", all-caps phrases, exclamation marks

When ANY trigger is detected, immediately invoke the escalation action.
```

**Auto-Fix Command:**
```bash
Skill(skill="sf-ai-agentscript", args="Add escalation triggers to agent MyAgent - detect 'nothing works', 'need a human', 'already tried that' as escalation signals")
```

### 10. ACTION_CHAIN_FAILURE (Multi-Turn)

**Symptom:** Action output from one turn is not used as input for the next action.

**Example Failure:**
```
❌ test_action_chain (Multi-Turn)
   Turn 1: "Find account Edge Communications" → IdentifyRecord ✅ (found AccountId)
   Turn 2: "Show me their cases" → GetCases ❌ asks "Which account?" (should use Turn 1 result)
   Category: ACTION_CHAIN_FAILURE
```

**Root Cause Analysis:**
1. Second action's input not wired to first action's output variable
2. Topic instructions don't reference using action results from prior turns
3. Variable mapping mismatch between actions

**Fix Strategy:**
```yaml
# Add to topic instructions for the downstream action
topic: case_management
  instructions: |
    ...
    When the user asks about cases for an account:
    - If an account was identified in a prior action, use that account's ID
    - Do NOT re-ask for the account name or ID
    - Pass the previously identified record ID to the GetCases action
```

**Auto-Fix Command:**
```bash
Skill(skill="sf-ai-agentscript", args="Fix action chaining in agent MyAgent - ensure GetCases uses AccountId from prior IdentifyRecord action output")
```

---

## Cross-Skill Orchestration

### Orchestration Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                 AGENT TESTING ORCHESTRATION                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  sf-ai-agentscript                                              │
│  └─ Create agent script → Validate → Publish                    │
│                    │                                             │
│                    ▼                                             │
│  sf-ai-agentforce-testing (this skill)                          │
│  └─ Generate test spec → Create test → Run tests                │
│                    │                                             │
│         ┌─────────┴─────────┐                                   │
│         ▼                   ▼                                   │
│      PASSED              FAILED                                 │
│         │                   │                                   │
│         │       ┌───────────┴───────────┐                       │
│         │       ▼                       ▼                       │
│         │   sf-ai-agentscript     sf-flow/sf-apex               │
│         │   (fix agent)           (fix dependencies)            │
│         │       │                       │                       │
│         │       └───────────┬───────────┘                       │
│         │                   ▼                                   │
│         │       sf-ai-agentforce-testing                        │
│         │       (re-run tests, max 3x)                          │
│         │                   │                                   │
│         └─────────┬─────────┘                                   │
│                   ▼                                             │
│               COMPLETE                                          │
│               └─ All tests passing OR escalate to human         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Required Skill Delegations

| Scenario | Skill to Call | Command Example |
|----------|---------------|-----------------|
| Fix agent script | sf-ai-agentscript | `Skill(skill="sf-ai-agentscript", args="Fix topic 'billing' - add keywords")` |
| Create test data | sf-data | `Skill(skill="sf-data", args="Create test Account with order data")` |
| Fix failing Flow | sf-flow | `Skill(skill="sf-flow", args="Fix flow 'Get_Order_Status' - add validation")` |
| Fix Apex error | sf-apex | `Skill(skill="sf-apex", args="Fix Apex class 'OrderController'")` |
| Setup ECA | sf-connected-apps | `Skill(skill="sf-connected-apps", args="Create External Client App for Agent Runtime API testing")` |
| Analyze debug logs | sf-debug | `Skill(skill="sf-debug", args="Analyze apex-debug.log from agent test")` |

---

## Automated Testing Workflow

### Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                  AUTOMATED AGENT TESTING FLOW                       │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   Agent Script  →  Test Spec Generator  →  sf agent test create    │
│   (.agent file)    (generate-test-spec.py)    (CLI)                │
│         │                   │                    │                  │
│         │           Extract topics/          Deploy to             │
│         │           actions/expected         org                   │
│         ▼                   ▼                    ▼                  │
│   Validation  ←───  Result Parser  ←───  sf agent test run         │
│   Framework    (parse-agent-test-results.py)  (--result-format json)│
│         │                │                                          │
│         ▼                ▼                                          │
│   Report Generator  +  Agentic Fix Loop (sf-ai-agentscript)        │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

### Python Scripts

#### 1. generate-test-spec.py

**Purpose:** Parse `.agent` files and generate YAML test specifications.

**Usage:**
```bash
# From agent file
python3 hooks/scripts/generate-test-spec.py \
  --agent-file /path/to/Agent.agent \
  --output specs/Agent-tests.yaml \
  --verbose

# From agent directory
python3 hooks/scripts/generate-test-spec.py \
  --agent-dir /path/to/aiAuthoringBundles/Agent/ \
  --output specs/Agent-tests.yaml
```

**What it extracts:**
- Topics (with labels and descriptions)
- Actions (flow:// targets with inputs/outputs)
- Transitions (@utils.transition patterns)

**What it generates:**
- Topic routing test cases (3+ phrasings per topic)
- Action invocation test cases (for each flow:// action)
- Edge case tests (off-topic handling, empty input)

**Example Output:**
```yaml
name: "Coffee_Shop_FAQ_Agent Tests"
subjectType: AGENT
subjectName: Coffee_Shop_FAQ_Agent

testCases:
  # Auto-generated topic routing test
  - utterance: "What's on your menu?"
    expectedTopic: coffee_faq

  # Auto-generated action test
  - utterance: "Can you search for Harry Potter?"
    expectedTopic: book_search
    expectedActions:
      - search_book_catalog
```

#### 2. run-automated-tests.py

**Purpose:** Orchestrate full test workflow from spec generation to fix suggestions.

**Usage:**
```bash
python3 hooks/scripts/run-automated-tests.py \
  --agent-name Coffee_Shop_FAQ_Agent \
  --agent-dir /path/to/project \
  --target-org AgentforceScriptDemo
```

**Workflow Steps:**
1. Check if Agent Testing Center is enabled
2. Generate test spec from agent definition
3. Create test definition in org (AiEvaluationDefinition)
4. Run tests (`sf agent test run --result-format json`)
5. Parse and display results
6. Suggest fixes for failures (enables agentic fix loop)

**Output:**
```
📊 AGENT TEST RESULTS
════════════════════════════════════════════════════════════════

Agent: Coffee_Shop_FAQ_Agent
Org: AgentforceScriptDemo
Duration: 45.2s
Mode: Simulated

SUMMARY
───────────────────────────────────────────────────────────────
✅ Passed:    18
❌ Failed:    2
⏭️ Skipped:   0
📈 Topic Selection: 95%
🎯 Action Invocation: 90%

FAILED TESTS
───────────────────────────────────────────────────────────────
❌ test_complex_order_inquiry
   Utterance: "What's the status of orders 12345 and 67890?"
   Expected: get_order_status invoked 2 times
   Actual: get_order_status invoked 1 time
   Category: ACTION_INVOCATION_COUNT_MISMATCH

   🔧 Suggested Fix:
   Skill(skill="sf-ai-agentscript", args="Fix action 'get_order_status' in Coffee_Shop_FAQ_Agent - add handling for multiple order numbers in single utterance")

❌ test_edge_case_empty_input
   Utterance: ""
   Expected: graceful_handling
   Actual: no_response
   Category: EDGE_CASE_FAILURE

   🔧 Suggested Fix:
   Skill(skill="sf-ai-agentscript", args="Add empty input handling to Coffee_Shop_FAQ_Agent system instructions")
```

#### 3. Claude Code Integration

Claude Code can invoke automated tests directly:

```bash
# Run full automated workflow
python3 ~/.claude/plugins/cache/sf-skills/.../sf-ai-agentforce-testing/hooks/scripts/run-automated-tests.py \
  --agent-name MyAgent \
  --agent-file /path/to/MyAgent.agent \
  --target-org dev

# Generate spec only
python3 ~/.claude/plugins/cache/sf-skills/.../sf-ai-agentforce-testing/hooks/scripts/generate-test-spec.py \
  --agent-file /path/to/MyAgent.agent \
  --output /tmp/MyAgent-tests.yaml \
  --verbose
```

---

## Example: Complete Fix Loop Execution

### Scenario: Topic Routing Failure

**Initial Test Failure:**
```bash
sf agent test run --api-name MyAgentTest --wait 10 --result-format json --target-org dev
```

**Output:**
```json
{
  "status": "FAILED",
  "testCases": [
    {
      "name": "test_billing_inquiry",
      "status": "FAILED",
      "utterance": "Why was I charged?",
      "expectedTopic": "billing_inquiry",
      "actualTopic": "topic_selector",
      "category": "TOPIC_NOT_MATCHED"
    }
  ]
}
```

**Step 1: Read Agent Script**
```bash
# Read current agent definition
Read(file_path="/path/to/agents/MyAgent.agent")
```

**Step 2: Analyze Failure**
```
Root Cause: Topic description for 'billing_inquiry' doesn't include keyword "charged"
Current description: "Handles billing questions"
Missing keywords: charged, charge, payment
```

**Step 3: Generate Fix**
```bash
Skill(skill="sf-ai-agentscript", args="Fix topic 'billing_inquiry' in agent MyAgent - add keywords: charged, charge, payment to description")
```

**Step 4: Re-Publish Agent**
```bash
# sf-ai-agentforce skill will:
# 1. Update agent script
# 2. Validate via sf agent validate
# 3. Publish via sf agent publish authoring-bundle
```

**Step 5: Re-Run Test**
```bash
sf agent test run --api-name MyAgentTest --wait 10 --result-format json --target-org dev
```

**Output:**
```json
{
  "status": "PASSED",
  "testCases": [
    {
      "name": "test_billing_inquiry",
      "status": "PASSED",
      "utterance": "Why was I charged?",
      "expectedTopic": "billing_inquiry",
      "actualTopic": "billing_inquiry"
    }
  ]
}
```

---

## Fallback Options

### If Agent Testing Center NOT Available

```bash
# Check if enabled
sf agent test list --target-org dev

# If error: "Not available for deploy" or "INVALID_TYPE: Cannot use: AiEvaluationDefinition"
# → Agent Testing Center is NOT enabled
```

**Fallback 1: sf agent preview (Recommended)**
```bash
sf agent preview --api-name MyAgent --output-dir ./transcripts --target-org dev
```
- Interactive testing, no special features required
- Use `--output-dir` to save transcripts for manual review
- Test utterances manually one by one

**Fallback 2: Manual Testing with Generated Spec**
1. Generate spec: `python3 generate-test-spec.py --agent-file X --output spec.yaml`
2. Review spec and manually test each utterance in preview
3. Track results in spreadsheet or notes

**Fallback 3: Request Feature Enablement**
- **Scratch Org:** Add to scratch-def.json:
  ```json
  {
    "features": ["AgentTestingCenter", "EinsteinGPTForSalesforce"]
  }
  ```
- **Production/Sandbox:** Contact Salesforce support to enable

---

## Configuration

### Max Attempts

Default: 3 attempts per failure

Rationale:
- 1st attempt: Initial fix based on error analysis
- 2nd attempt: Refined fix with additional context
- 3rd attempt: Alternative approach

If still failing after 3 attempts, escalate to human review.

### Cross-Skill Delegation

| Failure Type | Delegate To |
|--------------|-------------|
| Agent script issues | sf-ai-agentscript |
| Flow execution errors | sf-flow |
| Apex exceptions | sf-apex |
| Debug log analysis | sf-debug |
| Test data issues | sf-data |

---

## Troubleshooting

### Fix not working after 3 attempts

**Possible causes:**
- Root cause misidentified
- Multiple overlapping issues
- Fundamental design problem

**Solution:**
1. Run interactive preview to observe behavior
2. Check debug logs for additional errors
3. Consider redesigning topic/action structure
4. Manual review of agent script

### Fix breaks other tests

**Possible causes:**
- Overly broad fix
- Overlapping topic/action descriptions

**Solution:**
1. Run full test suite after each fix
2. Use more specific keywords
3. Add `available when` conditions

### Loop runs indefinitely

**Possible causes:**
- Max attempts not enforced
- Same error recurring

**Solution:**
1. Verify attempt counter increments
2. Check if fix is actually being applied
3. Validate agent is being republished

---

## Related Resources

- [SKILL.md](../SKILL.md) - Main skill documentation
- [test-spec-reference.md](./test-spec-reference.md) - Test spec format
- [coverage-analysis.md](../references/coverage-analysis.md) - Coverage metrics
- [assets/](../assets/) - Test spec examples
