<!-- Parent: sf-ai-agentforce-testing/SKILL.md -->
# Deep Conversation History Patterns

Testing specific protocol stages in CLI tests using 4-8 turn `conversationHistory`.

---

## Overview

CLI tests are often described as "single-utterance" — but this is only half the story. By providing deep `conversationHistory` (4-8 turns of prior conversation), you can position the agent at a specific point in a multi-step protocol and test its behavior at that exact stage.

This transforms CLI tests from simple "utterance → topic" checks into precise protocol-stage validators:

| Without History | With Deep History |
|----------------|-------------------|
| Tests routing only (utterance → topic) | Tests behavior at any protocol stage |
| Stochastic routing for ambiguous inputs | Deterministic routing anchored by history |
| Cannot test mid-protocol actions | Can trigger specific actions at specific steps |
| Cannot test opt-out or exit paths | Can validate graceful opt-out handling |
| Cannot test session persistence | Can verify session stays alive after protocol |

---

## Why Deep History Eliminates Stochastic Routing

When a user sends an ambiguous utterance like "Thanks for the help" to an agent with multiple topics, the planner must decide between several valid destinations. Without history, this decision is non-deterministic — the same utterance may route to different topics on repeated runs.

**The `topic` field anchors routing.** In `conversationHistory`, agent turns include a `topic` field that tells the planner which topic was active. When the planner sees a history of turns within a specific topic, it biases routing toward that topic's continuation or natural follow-ups.

```yaml
# ❌ STOCHASTIC — "Thanks for the help" could route anywhere
- utterance: "Thanks for the help"
  expectedTopic: feedback_collection

# ✅ DETERMINISTIC — history anchors to account_support → feedback naturally follows
- utterance: "Thanks for the help"
  expectedTopic: feedback_collection
  conversationHistory:
    - role: user
      message: "I need help with my account"
    - role: agent
      topic: account_support
      message: "I'd be happy to help! I found your account. What do you need?"
    - role: user
      message: "Can you check my recent activity?"
    - role: agent
      topic: account_support
      message: "Here's your recent activity. Your last transaction was on Feb 10."
```

**Key detail:** The `topic` field in `conversationHistory` resolves **local developer names** (e.g., `account_support`, `feedback_collection`). You do NOT need the hash-suffixed runtime `developerName` in history — only in `expectedTopic` for promoted topics.

---

## Pattern A: Protocol Activation

**Goal:** Trigger a secondary protocol (e.g., feedback collection, survey, follow-up) after a completed business interaction.

**History depth:** 4 turns (2 user + 2 agent)

**Why it works:** The history establishes that a business interaction just completed, creating the natural entry point for a follow-up protocol.

```yaml
testCases:
  # After a completed business interaction, trigger feedback collection
  - utterance: "Thanks for the help"
    expectedTopic: [feedback_topic]
    expectedActions:
      - [feedback_action]
    conversationHistory:
      - role: user
        message: "I need to check my account status"
      - role: agent
        topic: [business_topic]
        message: "I found your account. Everything looks good — your balance is current."
      - role: user
        message: "Great, that answers my question"
      - role: agent
        topic: [business_topic]
        message: "Glad I could help! Is there anything else you need?"
```

**Without this history**, "Thanks for the help" would stochastically route to greeting, escalation, or off-topic — depending on the planner's confidence scores.

---

## Pattern B: Mid-Protocol Stage

**Goal:** Test agent behavior at step N of a multi-step protocol (e.g., after collecting a rating but before collecting detailed feedback).

**History depth:** 4-6 turns

**Why it works:** The history positions the agent mid-protocol, so the test utterance exercises the specific step you want to validate.

```yaml
testCases:
  # Agent has already asked for a rating — now test the follow-up question
  - utterance: "I'd give it a 4 out of 5"
    expectedTopic: [feedback_topic]
    expectedActions:
      - [store_feedback_action]
    expectedOutcome: "Agent acknowledges the rating and asks a follow-up question about what could be improved"
    conversationHistory:
      - role: user
        message: "I need help checking my order"
      - role: agent
        topic: [order_topic]
        message: "Your order #12345 is scheduled for delivery tomorrow."
      - role: user
        message: "Thanks, that's helpful"
      - role: agent
        topic: [feedback_topic]
        message: "Glad I could help! On a scale of 1-5, how would you rate your experience today?"
```

---

## Pattern C: Action Invocation via Deep History

**Goal:** Position the agent at the exact point where it needs to fire a specific action on the next utterance.

**History depth:** 6 turns

**Why it works:** The history completes all prerequisite steps (authentication, data collection) so the test utterance triggers the action directly.

```yaml
testCases:
  # Agent has verified identity and collected payment info — now trigger payment action
  - utterance: "Yes, please process the payment"
    expectedTopic: [payment_topic]
    expectedActions:
      - [process_payment_action]
    expectedOutcome: "Agent confirms the payment is being processed"
    conversationHistory:
      - role: user
        message: "I'd like to make a payment"
      - role: agent
        topic: [auth_topic]
        message: "I can help with that. For security, can you verify your name on the account?"
      - role: user
        message: "John Smith"
      - role: agent
        topic: [payment_topic]
        message: "Thanks, John. I found your account. Your current balance is $150. Would you like to pay the full amount?"
      - role: user
        message: "Yes, full amount"
      - role: agent
        topic: [payment_topic]
        message: "I'll process a payment of $150. Should I proceed?"
```

> **Note:** Actions fire during CLI test execution for the final utterance — but the *history turns* are simulated (no real actions execute during those turns). Only the test utterance triggers real action execution.

---

## Pattern D: Opt-Out / Negative Assertion

**Goal:** Verify the agent handles opt-out gracefully — no action should fire, and the agent should acknowledge the user's choice.

**History depth:** 4-6 turns

**Key technique:** Use `expectedActions: []` as a **deliberate negative assertion** — this documents the intent that NO action should fire. Combine with `expectedOutcome` to verify the agent's graceful response.

```yaml
testCases:
  # User declines feedback — agent should NOT invoke feedback action
  - utterance: "No thanks, I'm all set"
    expectedTopic: [feedback_topic]
    expectedActions: []    # ← DELIBERATE: documents intent that NO action fires
    expectedOutcome: "Agent gracefully accepts the opt-out without pushing for feedback"
    conversationHistory:
      - role: user
        message: "I need to check my account"
      - role: agent
        topic: [account_topic]
        message: "Your account looks good. Balance is current."
      - role: user
        message: "Great, thanks"
      - role: agent
        topic: [feedback_topic]
        message: "Glad I could help! Would you like to share feedback about your experience?"
```

### `expectedActions: []` vs Omitted

| Pattern | Meaning | Behavior |
|---------|---------|----------|
| `expectedActions:` omitted | "Not testing actions" | PASS regardless of what fires |
| `expectedActions: []` | "Testing that NO actions fire" | Currently same behavior (PASS regardless), but documents intent |

> **Best practice:** Use `expectedActions: []` explicitly for opt-out tests to document your intent, even though the CLI currently treats it the same as omitted. This makes the test self-documenting and future-proofs against framework changes.

---

## Pattern E: Session Persistence

**Goal:** After completing a full protocol (including all steps), verify the session is still alive by starting a new business interaction.

**History depth:** 8 turns (full protocol + new question)

**Why it works:** If the agent's session terminated during the protocol, the new utterance would fail or produce a generic greeting. A successful business-topic response proves the session survived.

```yaml
testCases:
  # After completing full feedback flow, start new business request
  - utterance: "Actually, can you also check on my recent order?"
    expectedTopic: [order_topic]
    expectedActions:
      - [order_lookup_action]
    expectedOutcome: "Agent acknowledges the new request and begins order lookup"
    conversationHistory:
      - role: user
        message: "I need help with my account"
      - role: agent
        topic: [account_topic]
        message: "I found your account. Everything looks good."
      - role: user
        message: "Thanks!"
      - role: agent
        topic: [feedback_topic]
        message: "Glad to help! Would you rate your experience 1-5?"
      - role: user
        message: "4 out of 5"
      - role: agent
        topic: [feedback_topic]
        message: "Thanks for the feedback! Is there anything else I can help with?"
      - role: user
        message: "No, that's all for feedback"
      - role: agent
        topic: [feedback_topic]
        message: "Got it! Let me know if you need anything else."
```

---

## expectedOutcome Gotcha: Judges TEXT, Not Actions

The `output_validation` assertion evaluates the agent's **text response** — it does NOT inspect action results, sObject writes, or internal state changes.

```yaml
# ❌ WRONG — references internal action behavior
expectedOutcome: "Agent should create a Survey_Result__c record with rating=4"

# ❌ WRONG — references sObject changes
expectedOutcome: "Agent should update the MessagingSession.Bot_Support_Path__c field"

# ✅ RIGHT — describes what the agent SAYS
expectedOutcome: "Agent acknowledges the rating and thanks the user for feedback"

# ✅ RIGHT — describes observable text behavior
expectedOutcome: "Agent confirms the payment is being processed and provides a confirmation number"
```

**Rule of thumb:** If you can't verify it by reading the agent's chat response, don't put it in `expectedOutcome`. Use `expectedActions` for action verification and `--verbose` output for action input/output inspection.

---

## History Length Guide

| Test Goal | Recommended Turns | Pattern |
|-----------|-------------------|---------|
| Simple topic anchoring | 2 (1 user + 1 agent) | Basic routing |
| Protocol activation | 4 (2 user + 2 agent) | Pattern A |
| Mid-protocol stage | 4-6 | Pattern B |
| Action invocation | 6 | Pattern C |
| Opt-out / negative assertion | 4-6 | Pattern D |
| Session persistence | 8 | Pattern E |

> **Diminishing returns:** Beyond 8 turns, the history becomes expensive to maintain and may hit token limits. If you need deeper history, consider splitting into separate test cases or using the multi-turn API (Phase A) instead.

---

## Related Documentation

| Resource | Link |
|----------|------|
| Test Spec Reference | [test-spec-reference.md](../references/test-spec-reference.md) |
| Multi-Turn Testing | [multi-turn-testing.md](multi-turn-testing.md) |
| CLI Deep History Template | [cli-deep-history-tests.yaml](../assets/cli-deep-history-tests.yaml) |
| Topic Name Resolution | [topic-name-resolution.md](topic-name-resolution.md) |
