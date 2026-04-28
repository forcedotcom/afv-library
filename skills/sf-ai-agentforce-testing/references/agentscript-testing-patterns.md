<!-- Parent: sf-ai-agentforce-testing/SKILL.md -->
# Agent Script Testing Patterns

Testing guide for agents built with Agent Script (`.agent` files / AiAuthoringBundle). Covers the unique challenges of testing multi-topic Agent Script agents via CLI (`sf agent test`) and Agent Runtime API.

---

## Background: Why Agent Script Testing is Different

Agent Script agents use a **two-level action system**:

| Level | Where | What It Does | Example |
|-------|-------|-------------|---------|
| **Level 1: Definition** | `topic.actions:` block | Defines action with `target:` | `get_order_status: target: "apex://OrderStatusService"` |
| **Level 2: Invocation** | `reasoning.actions:` block | Invokes Level 1 via `@actions.<name>` | `check_status: @actions.get_order_status` |

Multi-topic agents also have a `start_agent` entry point that routes to topics via `@utils.transition to @topic.<name>`. This creates **transition actions** (e.g., `go_order_status`).

**The core testing challenge:** Single-utterance CLI tests have a "1 action per reasoning cycle" budget. For multi-topic agents, the first cycle is consumed by the topic transition — the actual business action never fires.

---

## Pattern 1: Routing Test

**Goal:** Verify `start_agent` routes to the correct topic based on user input.

**When to use:** Always — this is the first test for any Agent Script agent.

**Key insight:** The `expectedActions` captures the **transition action** (`go_<topic>`), NOT the business action.

```yaml
testCases:
  - utterance: "I want to check my order status"
    expectedTopic: order_status
    expectedActions:
      - go_order_status    # Transition action from start_agent
    expectedOutcome: "Agent should acknowledge and begin the order status flow"

  - utterance: "Check the status of my order"
    expectedTopic: order_status
    # Multiple phrasings for robust routing validation

  - utterance: "Where is my package?"
    expectedTopic: order_status
```

**What to verify in results:**
- `generatedData.topic` matches `expectedTopic`
- `actionsSequence` contains `go_<topic_name>`

---

## Pattern 2: Action Test with Conversation History

**Goal:** Test the actual business action (Apex/Flow) by pre-positioning the agent in the target topic.

**When to use:** For any action that requires the agent to already be in a topic (i.e., most actions beyond the initial routing).

**Key insight:** `conversationHistory` simulates prior turns so the agent starts in the target topic. The agent's response includes the `topic` field to establish context.

```yaml
testCases:
  - utterance: "The order ID is 801ak00001g59JlAAI"
    conversationHistory:
      - role: "user"
        message: "I want to check my order status"
      - role: "agent"
        topic: "order_status"
        message: "I'd be happy to help! Could you please provide the Order ID?"
    expectedTopic: order_status
    expectedActions:
      - get_order_status    # Level 1 DEFINITION name (NOT invocation name)
    expectedOutcome: "Agent retrieves order details including number, status, and amount"
```

**Conversation history format:**

| Field | Required | Description |
|-------|----------|-------------|
| `role` | Yes | `"user"` or `"agent"` |
| `message` | Yes | The message content |
| `topic` | Agent only | Topic name — **required for agent messages** to establish topic context |

**Common mistake:** Using the Level 2 invocation name (e.g., `check_status`) instead of the Level 1 definition name (e.g., `get_order_status`) in `expectedActions`. CLI results always report the **definition name**.

---

## Pattern 3: Error Handling Test

**Goal:** Verify the agent handles invalid input or missing data gracefully.

**When to use:** After validating the happy path (Pattern 2).

```yaml
testCases:
  # Invalid input — order not found
  - utterance: "My order ID is INVALID_XYZ_123"
    conversationHistory:
      - role: "user"
        message: "Check my order status"
      - role: "agent"
        topic: "order_status"
        message: "Sure! What is your Order ID?"
    expectedTopic: order_status
    expectedOutcome: "Agent should inform the user that the order was not found"

  # Missing required input — no ID provided
  - utterance: "I don't know my order ID"
    conversationHistory:
      - role: "user"
        message: "Check my order status"
      - role: "agent"
        topic: "order_status"
        message: "What is your Order ID?"
    expectedTopic: order_status
    expectedOutcome: "Agent should suggest alternative ways to find the order"
```

**Apex `WITH USER_MODE` errors:** If the Apex class uses `WITH USER_MODE`, the action silently returns 0 rows when the Einstein Agent User lacks permissions. The agent responds as if the record doesn't exist — no error message. Test this explicitly to catch permission gaps before production.

---

## Pattern 4: Escalation Test

**Goal:** Verify escalation works from both `start_agent` and within topics.

**When to use:** Always — escalation is a critical safety net.

```yaml
testCases:
  # Escalation from start_agent (before topic routing)
  - utterance: "I want to talk to a real person"
    expectedTopic: Escalation

  # Escalation from within a topic
  - utterance: "This isn't helping, let me speak to someone"
    conversationHistory:
      - role: "user"
        message: "Check my order status"
      - role: "agent"
        topic: "order_status"
        message: "What is your Order ID?"
    expectedTopic: Escalation

  # Non-escalation (agent should NOT escalate)
  - utterance: "I need help with my order"
    expectedTopic: order_status
    expectedOutcome: "Agent should begin helping with the order, not escalate"
```

---

## Pattern 5: Multi-Action Sequence Test

**Goal:** Test an agent that performs multiple actions in sequence (e.g., look up order, then create a case).

**When to use:** Agents with topics that chain multiple actions.

**Limitation:** CLI tests are single-utterance. To test multi-action sequences, use longer conversation histories.

```yaml
testCases:
  # First action in sequence
  - utterance: "Order ID is 801ak00001g59JlAAI"
    conversationHistory:
      - role: "user"
        message: "I have a problem with my order"
      - role: "agent"
        topic: "order_support"
        message: "I can help! What's the Order ID?"
    expectedTopic: order_support
    expectedActions:
      - get_order_details
    expectedOutcome: "Agent retrieves order details and asks about the problem"

  # Second action — using extended history from first action
  - utterance: "Yes, please create a case for this"
    conversationHistory:
      - role: "user"
        message: "I have a problem with my order"
      - role: "agent"
        topic: "order_support"
        message: "What's the Order ID?"
      - role: "user"
        message: "801ak00001g59JlAAI"
      - role: "agent"
        topic: "order_support"
        message: "I found your order #00000102 (Draft, $50,000). What issue are you experiencing?"
      - role: "user"
        message: "The order is wrong, I need to file a complaint"
      - role: "agent"
        topic: "order_support"
        message: "I'm sorry about that. Would you like me to create a support case?"
    expectedTopic: order_support
    expectedActions:
      - create_support_case
    expectedOutcome: "Agent creates a support case and provides the case number"
```

---

## Topic Name Discovery Workflow

Agent Script topic names in CLI test results may differ from the names in the `.agent` file. Follow this workflow to discover the actual runtime names:

### Step 1: Write Initial Spec

Use the topic name from the `.agent` file as your best guess:

```yaml
# In .agent file: "topic order_status:"
expectedTopic: order_status
```

### Step 2: Run First Test

```bash
sf agent test create --spec ./tests/spec.yaml --api-name MyTest --target-org dev
sf agent test run --api-name MyTest --wait 10 --result-format json --json --target-org dev
```

### Step 3: Extract Actual Topic Names

```bash
# Get the job ID from the run output
sf agent test results --job-id <JOB_ID> --result-format json --json --target-org dev \
  | jq '.result.testCases[].generatedData.topic'
```

### Step 4: Update Spec

Replace guessed topic names with actual runtime names from the results.

### Step 5: Re-Deploy and Re-Run

```bash
sf agent test create --spec ./tests/spec.yaml --api-name MyTest --force-overwrite --target-org dev
sf agent test run --api-name MyTest --wait 10 --result-format json --json --target-org dev
```

---

## Permission Pre-Check Guide

Agent Script agents with `WITH USER_MODE` Apex require the Einstein Agent User to have object permissions. Missing permissions cause **silent failures** — the query returns 0 rows with no error.

### Identifying Required Permissions

1. **Read the `.agent` file** — find all `target: "apex://ClassName"` entries
2. **Read each Apex class** — find SOQL queries with `WITH USER_MODE`
3. **Extract queried objects** — e.g., `FROM Order`, `FROM Account`
4. **Check `default_agent_user`** — the user profile in the `.agent` config block

### Verifying Permissions

```bash
# Find the Einstein Agent User's profile
sf data query --query "SELECT Id, ProfileId, Profile.Name FROM User WHERE Username = '<default_agent_user>' LIMIT 1" --target-org dev --json

# Check ObjectPermissions for the user's profile
sf data query --query "SELECT SObjectType, PermissionsRead FROM ObjectPermissions WHERE ParentId IN (SELECT Id FROM PermissionSet WHERE ProfileId = '<profile_id>') AND SObjectType IN ('Order', 'Account')" --target-org dev --json
```

### Fixing Missing Permissions

```bash
# Create a Permission Set (via Apex anonymous)
sf apex run --target-org dev <<'EOF'
PermissionSet ps = new PermissionSet(
    Name = 'Agent_Object_Access',
    Label = 'Agent Object Access'
);
insert ps;

ObjectPermissions op = new ObjectPermissions(
    ParentId = ps.Id,
    SObjectType = 'Order',
    PermissionsRead = true,
    PermissionsViewAllRecords = false
);
insert op;
EOF

# Assign to the Einstein Agent User
sf apex run --target-org dev <<'EOF'
User agentUser = [SELECT Id FROM User WHERE Username = '<default_agent_user>' LIMIT 1];
PermissionSet ps = [SELECT Id FROM PermissionSet WHERE Name = 'Agent_Object_Access' LIMIT 1];
insert new PermissionSetAssignment(AssigneeId = agentUser.Id, PermissionSetId = ps.Id);
EOF
```

---

## Agent Script vs GenAiPlannerBundle: Testing Differences

| Aspect | Agent Script (AiAuthoringBundle) | GenAiPlannerBundle |
|--------|----------------------------------|-------------------|
| **Metadata format** | `.agent` DSL file | XML files |
| **Action references** | `apex://Class` directly | GenAiFunction XML |
| **Topic routing** | `start_agent` → `@utils.transition` | LLM planner routing |
| **Action in CLI test** | Transition action only (1st cycle) | May get business action |
| **Test approach** | Use conversationHistory for actions | Standard single-utterance |
| **Discovery** | Parse `.agent` DSL | Parse XML files |
| **Permission model** | `default_agent_user` in config | Org-level profile |

---

## Quick Reference: CLI YAML Fields for Agent Script

```yaml
# REQUIRED top-level fields
name: "My Agent Tests"              # MasterLabel — deploy fails without
subjectType: AGENT                   # Must be AGENT
subjectName: My_Agent_Name           # config.developer_name from .agent file

testCases:
  - utterance: "user message"        # Required
    expectedTopic: topic_name        # From .agent topic block name
    expectedActions:                  # Flat list of strings
      - action_name                  # Level 1 definition name
    expectedOutcome: "description"   # LLM-as-judge evaluation
    conversationHistory:             # Pre-position in topic
      - role: "user"
        message: "prior user message"
      - role: "agent"
        topic: "topic_name"          # REQUIRED for agent messages
        message: "prior agent response"
```

---

## Related Resources

- [SKILL.md](../SKILL.md) — Main skill documentation (Phase B: Agent Script section)
- [test-spec-reference.md](../references/test-spec-reference.md) — Complete YAML schema reference and test spec guide
- [topic-name-resolution.md](topic-name-resolution.md) — Topic name format rules
- [agentscript-test-spec.yaml](../assets/agentscript-test-spec.yaml) — Template with all 5 patterns
