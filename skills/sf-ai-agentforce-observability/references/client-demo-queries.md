<!-- Parent: sf-ai-agentforce-observability/SKILL.md -->
# STDM Query Walkthrough - Client Demo

Step-by-step queries for exploring Session Tracing Data Model in Data Cloud Query Console.

## Data Model Hierarchy

```
ssot__AIAgentSession__dlm (Session)
    └── ssot__AIAgentInteraction__dlm (Turn)
            └── ssot__AIAgentInteractionStep__dlm (LLM/Actions)
            └── ssot__AIAgentMoment__dlm (Messages)
```

---

## Tab S1: All Sessions

**Purpose**: Overview of all agent sessions

```sql
-- S1: All Sessions (Overview)
SELECT
    ssot__Id__c AS SessionID,
    ssot__StartTimestamp__c AS StartTime,
    ssot__EndTimestamp__c AS EndTime,
    ssot__RelatedMessagingSessionId__c AS MessagingSessionID,
    ssot__AiAgentSessionEndType__c AS EndType
FROM ssot__AIAgentSession__dlm
ORDER BY ssot__StartTimestamp__c DESC
LIMIT 100
```

📋 **Copy a `SessionID` for the next query**

---

## Tab S2: Interactions for Session

**Purpose**: All turns/interactions within a session

```sql
-- S2: Interactions for Session
SELECT
    ssot__Id__c AS InteractionID,
    ssot__AiAgentSessionId__c AS SessionID,
    ssot__AiAgentInteractionType__c AS InteractionType,
    ssot__TopicApiName__c AS Topic,
    ssot__StartTimestamp__c AS StartTime,
    ssot__EndTimestamp__c AS EndTime
FROM ssot__AIAgentInteraction__dlm
WHERE ssot__AiAgentSessionId__c = '{{PASTE_SESSION_ID_HERE}}'
ORDER BY ssot__StartTimestamp__c
```

📋 **Copy an `InteractionID` for S3 and S4**

---

## Tab S3: Steps for Interaction

**Purpose**: LLM reasoning and action execution within a turn

```sql
-- S3: Steps for Interaction
SELECT
    ssot__Id__c AS StepID,
    ssot__AiAgentInteractionId__c AS InteractionID,
    ssot__AiAgentInteractionStepType__c AS StepType,
    ssot__Name__c AS ActionName,
    ssot__InputValueText__c AS InputJSON,
    ssot__OutputValueText__c AS OutputJSON
FROM ssot__AIAgentInteractionStep__dlm
WHERE ssot__AiAgentInteractionId__c = '{{PASTE_INTERACTION_ID_HERE}}'
```

**StepType values**: `LLM_STEP`, `ACTION_STEP`

---

## Tab S4: Messages for Interaction

**Purpose**: Actual user/agent conversation content

```sql
-- S4: Messages for Interaction
SELECT
    ssot__Id__c AS MessageID,
    ssot__AiAgentInteractionId__c AS InteractionID,
    ssot__AiAgentInteractionMessageType__c AS MessageType,
    ssot__ContentText__c AS Content,
    ssot__MessageSentTimestamp__c AS SentTime
FROM ssot__AIAgentMoment__dlm
WHERE ssot__AiAgentInteractionId__c = '{{PASTE_INTERACTION_ID_HERE}}'
ORDER BY ssot__MessageSentTimestamp__c
```

**MessageType values**: `INPUT` (user), `OUTPUT` (agent)

---

## Tab A1: Session Summary by End Type

**Purpose**: Aggregate sessions by how they ended

```sql
-- A1: Session Summary by End Type
SELECT
    ssot__AiAgentSessionEndType__c AS EndType,
    COUNT(*) AS SessionCount
FROM ssot__AIAgentSession__dlm
GROUP BY ssot__AiAgentSessionEndType__c
ORDER BY SessionCount DESC
```

---

## Tab A2: Topic Usage

**Purpose**: Which topics handle the most turns

```sql
-- A2: Topic Usage Analysis
SELECT
    ssot__TopicApiName__c AS Topic,
    COUNT(*) AS TurnCount
FROM ssot__AIAgentInteraction__dlm
WHERE ssot__AiAgentInteractionType__c = 'TURN'
GROUP BY ssot__TopicApiName__c
ORDER BY TurnCount DESC
```

---

## Tab A3: Action Invocations

**Purpose**: Which actions are called most frequently

```sql
-- A3: Action Invocation Frequency
SELECT
    ssot__Name__c AS ActionName,
    COUNT(*) AS InvocationCount
FROM ssot__AIAgentInteractionStep__dlm
WHERE ssot__AiAgentInteractionStepType__c = 'ACTION_STEP'
GROUP BY ssot__Name__c
ORDER BY InvocationCount DESC
```

---

## Demo Flow

1. **S1**: Run query, pick an interesting session (look for Escalated/Failed in EndType)
2. **S2**: Paste SessionID, see the conversation turns and topics
3. **S3**: Paste InteractionID, see LLM reasoning + action I/O
4. **S4**: Paste InteractionID, read the actual messages
5. **A1-A3**: Show aggregate insights

---

## Field Reference

| Friendly Name | Actual Field |
|---------------|--------------|
| SessionID | `ssot__Id__c` |
| StartTime | `ssot__StartTimestamp__c` |
| EndTime | `ssot__EndTimestamp__c` |
| EndType | `ssot__AiAgentSessionEndType__c` |
| InteractionID | `ssot__Id__c` |
| Topic | `ssot__TopicApiName__c` |
| StepType | `ssot__AiAgentInteractionStepType__c` |
| ActionName | `ssot__Name__c` |
| MessageType | `ssot__AiAgentInteractionMessageType__c` |
| Content | `ssot__ContentText__c` |
