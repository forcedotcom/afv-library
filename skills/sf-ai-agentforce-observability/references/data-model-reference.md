<!-- Parent: sf-ai-agentforce-observability/SKILL.md -->
# Session Tracing Data Model (STDM) Reference

Complete documentation of the Agentforce Session Tracing Data Model stored in Salesforce Data Cloud.

> **Source**: [Salesforce Help - Data Model for Agentforce Session Tracing](https://help.salesforce.com/s/articleView?id=ai.generative_ai_session_trace_data_model.htm)

## T6 Live API Discovery Summary ✅

**Validated: January 30, 2026** | **24 DMOs Found** | **233+ Test Points**

| Category | DMOs | Status | Notes |
|----------|------|--------|-------|
| **Session Tracing** | 5 | ✅ All Found | Session, Interaction, Step, Message, Participant |
| **Agent Optimizer** | 6 | ✅ All Found | Moment, Tag system (5 DMOs) |
| **GenAI Audit** | 13 | ✅ All Found | Generation, Quality, Feedback, Gateway |
| **RAG Quality** | 3 | ❌ Not Found | GenAIRetriever* DMOs don't exist |

**Key Discoveries:**
- Field naming: API uses `AiAgent` (lowercase 'i'), not `AIAgent`
- Agent name location: Stored on `Moment`, not `Session`
- New channel types: `NGC`, `Voice`, `Builder: Voice Preview`
- New agent types: `AgentforceEmployeeAgent`, `AgentforceServiceAgent`
- GenAI detector types: `TOXICITY` (9 categories), `PII` (4 types), `PROMPT_DEFENSE`, `InstructionAdherence`

## Overview

The STDM captures detailed telemetry from Agentforce agent conversations, enabling:
- **Debugging**: Understand why an agent behaved a certain way
- **Analytics**: Measure agent performance and usage patterns
- **Optimization**: Identify bottlenecks and improvement opportunities

The data model is a collection of DLOs (Data Lake Objects) and DMOs (Data Model Objects) that contain detailed session trace logs of agent behavior. Data is streamed to DLOs in Data 360 and then mapped to the applicable DMOs.

## Data Model Hierarchy

The Agentforce Analytics data model consists of two main components:
1. **Session Tracing Data Model** - Detailed turn-by-turn logs
2. **Optimization Data Model** - Moments and tagging for analytics

### Session Tracing Data Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    AIAgentSession (Session)                     │
│  One session = one complete conversation with an agent          │
├─────────────────────────────────────────────────────────────────┤
│  ssot__Id__c                    Primary key                     │
│  ssot__StartTimestamp__c        When session started            │
│  ssot__EndTimestamp__c          When session ended              │
│  ssot__AiAgentSessionEndType__c How session ended               │
└──────────────────────┬──────────────────────────────────────────┘
                       │
     ┌─────────────────┼─────────────────┬───────────────────┐
     │ 1:N             │ 1:N             │ 1:N               │ 1:N
     ▼                 ▼                 ▼                   ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│SessionParti- │ │ Interaction  │ │   Moment     │ │TagAssociation│
│   cipant     │ │   (Turn)     │ │ (Summaries)  │ │    ✅ NEW    │
├──────────────┤ ├──────────────┤ ├──────────────┤ ├──────────────┤
│AiAgentType   │ │ TURN /       │ │ Request/resp │ │ Links to     │
│AiAgentApiName│ │ SESSION_END  │ │ summaries    │ │ TagDefinition│
│Role          │ │ Topic routing│ │ Agent API    │ │ & Tag values │
└──────────────┘ └──────┬───────┘ └──────┬───────┘ └──────────────┘
                        │                │
            ┌───────────┼────────────────┼─────── N:M junction
            │ 1:N       │ 1:N            ▼
            ▼           ▼         ┌──────────────┐
     ┌────────────┐ ┌────────────┐│MomentInter-  │
     │ Interaction│ │ Interaction││action ✅ NEW │
     │   Message  │ │    Step    │├──────────────┤
     ├────────────┤ ├────────────┤│Links Moment ↔│
     │ Input/     │ │ LLM_STEP   ││ Interaction  │
     │ Output     │ │ ACTION_STEP│└──────────────┘
     │ messages   │ │ TOPIC_STEP │
     └────────────┘ │ INTERRUPT  │
                    │ SESSION_END│
                    └─────┬──────┘
                          │
                          │ links via GenerationId
                          ▼
                  ┌────────────────┐
                  │ GenAIGeneration│
                  │ (Trust Layer)  │
                  └───────┬────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │GenAIContent-   │
                  │ Quality        │
                  │ (Toxicity etc) │
                  └───────┬────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │GenAIContent-   │
                  │ Category       │
                  │ (Detectors)    │
                  └────────────────┘
```

**Key Relationships:**
- Session has multiple Participants (user, agent, human handoff)
- Session has multiple Interactions (turns)
- Session has multiple Moments (summaries)
- Each Interaction has Messages (actual user/agent text)
- Each Interaction has Steps (processing logic)
- Steps link to GenAIGeneration for quality metrics

## Entity Details

### AIAgentSession (ssot__AIAgentSession__dlm) ✅ T6 Verified

Represents an overarching container capturing contiguous interactions with one or more AI agents. A typical session might start when the customer asks their first question and end when the customer closes the agent chat window. Contains **18 fields**.

| Field API Name | Type | Description | Example |
|----------------|------|-------------|---------|
| `ssot__Id__c` | Text | Primary key - unique session identifier | `01999669-0a54-724f-80d6-9cb495a7cee4` |
| `ssot__StartTimestamp__c` | DateTime | Timestamp when the session began | `2026-01-28T10:15:23.000Z` |
| `ssot__EndTimestamp__c` | DateTime | Timestamp when the session concluded or timed out | `2026-01-28T10:19:55.000Z` |
| `ssot__AiAgentChannelType__c` | Text | Type of communication channel (see table below) | `SCRT2 - EmbeddedMessaging` |
| `ssot__AiAgentSessionEndType__c` | Text | How the session ended | `NOT_SET` |
| `ssot__VariableText__c` | Text | Key-value pairs of contextual session data | `{}` |
| `ssot__SessionOwnerId__c` | Text | ID of the participant who initiated the session | `0051234567890ABC` |
| `ssot__SessionOwnerObject__c` | Text | Name of DMO for Session Owner | `Individual` |
| `ssot__IndividualId__c` | Text (Lookup) | Reference to Individual record | `a0p...` |
| `ssot__PreviousSessionId__c` | Text (Lookup) | Reference to previous session (multi-agent) | `a0x...` |
| `ssot__RelatedMessagingSessionId__c` | Text | ID linking to messaging session origin ✅ | `5701234567890ABC` |
| `ssot__RelatedVoiceCallId__c` | Text | ID linking to voice call origin ✅ | `0Lx...` |
| `ssot__DataSourceId__c` | Text | Data source identifier | `null` |
| `ssot__DataSourceObjectId__c` | Text | Data source object identifier | `...` |
| `ssot__InternalOrganizationId__c` | Text | Internal org identifier | `null` |
| `KQ_Id__c` | Lookup | Key qualifier for ID | `null` |
| `KQ_IndividualId__c` | Lookup | Key qualifier for Individual | `null` |
| `KQ_PreviousSessionId__c` | Lookup | Key qualifier for PreviousSession | `null` |

**Session End Types:**

| Value | Description |
|-------|-------------|
| `Completed` | Session resolved successfully |
| `Escalated` | Transferred to human agent |
| `Abandoned` | User left without resolution |
| `Failed` | Session failed due to error |
| `NOT_SET` | End type not yet determined |

**Channel Types (Live API Verified - T6 Discovery):**

| Value | Occurrences | Description |
|-------|-------------|-------------|
| `E & O` | 13,894 | Einstein & Omni-Channel |
| `Builder` | 1,546 | Agent Builder testing |
| `SCRT2 - EmbeddedMessaging` | 957 | Embedded web messaging |
| `LightningDesktopCopilot` | 63 | Desktop copilot integration |
| `Voice` | 41 | Voice/speech channel |
| `PSTN` | 41 | Phone/PSTN channel |
| `Builder: Voice Preview` | 10 | Voice preview in Builder |
| `NGC` | 2 | Next-Gen Cloud (internal) |

---

### AIAgentSessionParticipant (ssot__AIAgentSessionParticipant__dlm) ✅ Verified

Represents an entity (human or AI) that takes part in an AIAgentSession.

| Field API Name | Type | Description | Example |
|----------------|------|-------------|---------|
| `ssot__Id__c` | Text | Primary key | `a0p1234567890ABC` |
| `ssot__AiAgentSessionId__c` | Text (Parent) | Reference to the specific AiAgentSession | `a0x1234567890ABC` |
| `ssot__AiAgentType__c` | Text | Type of AI Agent | `EinsteinServiceAgent` |
| `ssot__AiAgentTemplateApiName__c` | Text | Template used to create the agent | `Service_Agent_Template` |
| `ssot__AiAgentApiName__c` | Text | API name of the AI agent (if participant is AI) | `Customer_Support_Agent` |
| `ssot__AiAgentVersionApiName__c` | Text | API name of the AI agent version (if participant is AI) | `v1.2.3` |
| `ssot__StartTimestamp__c` | DateTime | Timestamp when participant joined the session | `2026-01-28T10:15:23.000Z` |
| `ssot__EndTimestamp__c` | DateTime | Timestamp when participant left/stopped interacting | `2026-01-28T10:19:55.000Z` |
| `ssot__ParticipantId__c` | Text | Reference to the record representing the participant | `0051234567890ABC` |
| `ssot__ParticipantObject__c` | Text | Name of DMO for the Participant record (e.g., `Individual`) | `Individual` |
| `ssot__ParticipantAttributeText__c` | Text | JSON key-value pairs of participant metadata | `{}` |
| `ssot__IndividualId__c` | Text (Lookup) | Reference to Individual if participant DMO is Individual | `a0i...` |
| `ssot__AiAgentSessionParticipantRole__c` | Text | Role of participant within the session | `Owner` |
| `ssot__ExternalSourceId__c` | Text | External system identifier for the participant | `ext-123` |
| `ssot__InternalOrganizationId__c` | Text | Internal org identifier | `00D...` |

**AI Agent Types (Live API Verified - T6 Discovery):**

| Value | Occurrences | Description |
|-------|-------------|-------------|
| `EinsteinServiceAgent` | 32,255 | Einstein Service Agent for customer support |
| `AgentforceEmployeeAgent` | 314 | Agentforce agent for employee-facing use cases |
| `AgentforceServiceAgent` | 171 | Agentforce service agent (newer platform) |
| `Employee` | 84 | Generic employee-type agent |

**Participant Roles (Live API Verified):**

| Value | Occurrences | Description |
|-------|-------------|-------------|
| `USER` | 16,431 | End user participating in the session |
| `AGENT` | 16,393 | AI agent participating in the session |

---

### AIAgentInteraction (ssot__AIAgentInteraction__dlm) ✅ T6 Verified

Represents a segment within a session. It typically begins with a user's request and ends when the AI agent provides a response to that request. Contains **20 fields**. Discovery shows **3,536 records** in a 30-day window.

| Field API Name | Type | Description | Example |
|----------------|------|-------------|---------|
| `ssot__Id__c` | Text | Primary key | `a0y1234567890ABC` |
| `ssot__AiAgentSessionId__c` | Text (Parent) | Reference to the parent session | `a0x1234567890ABC` |
| `ssot__AiAgentInteractionType__c` | Text | Interaction type (`TURN`, `SESSION_END`) | `TURN` |
| `ssot__PrevInteractionId__c` | Text (Lookup) | Reference to previous interaction (enables sequencing) | `a0y...` |
| `ssot__StartTimestamp__c` | DateTime | Timestamp when the interaction began | `2026-01-28T10:15:23.000Z` |
| `ssot__EndTimestamp__c` | DateTime | Timestamp when the interaction completed | `2026-01-28T10:15:26.000Z` |
| `ssot__TopicApiName__c` | Text | API name of the topic classified for this interaction | `Order_Tracking` |
| `ssot__AttributeText__c` | Text | JSON key-value pairs of additional metadata | `{"confidence": 0.95}` |
| `ssot__TelemetryTraceId__c` | Text | Identifier for distributed tracing (OpenTelemetry) | `abc123def456...` |
| `ssot__TelemetryTraceSpanId__c` | Text | Span ID within distributed tracing context | `span_xyz...` |
| `ssot__SessionOwnerId__c` | Text | ID of participant who initiated the session | `005...` |
| `ssot__SessionOwnerObject__c` | Text | DMO name for Session Owner | `Individual` |
| `ssot__IndividualId__c` | Text (Lookup) | Reference to Individual record | `a0i...` |
| `ssot__DataSourceId__c` | Text | Data source identifier | `null` |
| `ssot__DataSourceObjectId__c` | Text | Data source object identifier | `...` |
| `ssot__InternalOrganizationId__c` | Text | Internal org identifier | `null` |
| `KQ_*` | Lookup | Key qualifier fields for relationships | `null` |

**Interaction Types (Live API Verified):**

| Value | Description |
|-------|-------------|
| `TURN` | Normal user input → agent response cycle |
| `SESSION_END` | Final interaction marking session close |

**OpenTelemetry Integration**: The `TelemetryTraceId` and `TelemetryTraceSpanId` fields enable distributed tracing across system components, supporting export to platforms like Datadog, Splunk, and other OTEL-compatible tools.

---

### AIAgentInteractionMessage (ssot__AiAgentInteractionMessage__dlm) ✅ T6 Verified

Represents a single communication provided by the user or generated by the AI agent during a session. Contains **21 fields**.

| Field API Name | Type | Description | Example |
|----------------|------|-------------|---------|
| `ssot__Id__c` | Text | Primary key | `a0i1234567890ABC` |
| `ssot__AiAgentInteractionId__c` | Text (Parent) | Reference to the interaction | `a0y1234567890ABC` |
| `ssot__AiAgentSessionId__c` | Text (Lookup) | Reference to the session | `a0x...` |
| `ssot__AiAgentSessionParticipantId__c` | Text (Lookup) | Participant who sent the message | `a0p...` |
| `ssot__AiAgentInteractionMessageType__c` | Text | Message direction (`Input`/`Output`) | `Input` |
| `ssot__AiAgentInteractionMsgContentType__c` | Text | MIME content type | `text/plain` |
| `ssot__ContentText__c` | Text | Textual content | `What is the status of my order?` |
| `ssot__MessageSentTimestamp__c` | DateTime | Exact time when message was sent | `2026-01-28T10:15:23.000Z` |
| `ssot__ParentMessageId__c` | Text (Lookup) | Parent message (for threads) | `a0i...` |
| `ssot__SessionOwnerId__c` | Text | ID of session owner participant | `005...` |
| `ssot__SessionOwnerObject__c` | Text | DMO name for Session Owner | `Individual` |
| `ssot__IndividualId__c` | Text (Lookup) | Reference to Individual record | `a0i...` |
| `ssot__DataSourceId__c` | Text | Data source identifier | `null` |
| `ssot__DataSourceObjectId__c` | Text | Data source object identifier | `...` |
| `ssot__InternalOrganizationId__c` | Text | Internal org identifier | `null` |
| `KQ_*` | Lookup | Key qualifier fields | `null` |

**Message Types (Live API Verified):**

| Value | Occurrences | Description |
|-------|-------------|-------------|
| `Input` | 16,428 | User message to agent |
| `Output` | 16,390 | Agent response to user |

**Content Types (Live API Verified):**

| Value | Description |
|-------|-------------|
| `text/plain` | Plain text message |
| `application/json` | JSON-formatted content |

**Note:** InteractionMessage differs from Moment:
- **InteractionMessage**: Raw user/agent text per turn with threading support
- **Moment**: Summarized request/response with agent API name

---

### AIAgentInteractionStep (ssot__AIAgentInteractionStep__dlm) ✅ T6 Verified

Represents a discrete action or operation performed during an interaction to fulfill the user's request. Contains **23 fields**. Discovery shows **12,318 records** in a 30-day window.

| Field API Name | Type | Description | Example |
|----------------|------|-------------|---------|
| `ssot__Id__c` | Text | Primary key | `a0z1234567890ABC` |
| `ssot__AiAgentInteractionId__c` | Text (Parent) | Reference to the interaction this step belongs to | `a0y1234567890ABC` |
| `ssot__AiAgentInteractionStepType__c` | Text | Step type (see table below) | `LLM_STEP` |
| `ssot__Name__c` | Text | Name of the step/action performed | `Get_Order_Status` |
| `ssot__PrevStepId__c` | Text (Lookup) | Reference to previous step (linear sequencing) | `a0z...` |
| `ssot__StartTimestamp__c` | DateTime | Timestamp when step execution began | `2026-01-28T10:15:23.000Z` |
| `ssot__EndTimestamp__c` | DateTime | Timestamp when step execution completed | `2026-01-28T10:15:24.000Z` |
| `ssot__InputValueText__c` | Text | Input data provided to the step (JSON) | `{"orderId": "12345"}` |
| `ssot__OutputValueText__c` | Text | Output data resulting from step execution (JSON) | `{"status": "Shipped"}` |
| `ssot__PreStepVariableText__c` | Text | State of variables before step execution | `{"customer_id": "C001"}` |
| `ssot__PostStepVariableText__c` | Text | State of variables after step execution | `{"order_status": "Shipped"}` |
| `ssot__ErrorMessageText__c` | Text | Error details if step encountered issues | `Action timeout after 30s` |
| `ssot__AttributeText__c` | Text | JSON key-value pairs of additional metadata | `{"latency_ms": 150}` |
| `ssot__GenerationId__c` | Text | Reference to GenAIGeneration (LLM steps) | `gen_abc123...` |
| `ssot__GenAiGatewayRequestId__c` | Text | Reference to GenAIGatewayRequest (LLM steps) | `req_xyz...` |
| `ssot__GenAiGatewayResponseId__c` | Text | Reference to GenAIGatewayResponse (LLM steps) | `resp_xyz...` |
| `ssot__TelemetryTraceSpanId__c` | Text | Span ID for distributed tracing (OTEL) | `span_abc...` |
| `ssot__DataSourceId__c` | Text | Data source identifier | `null` |
| `ssot__DataSourceObjectId__c` | Text | Data source object identifier | `...` |
| `ssot__InternalOrganizationId__c` | Text | Internal org identifier | `null` |
| `KQ_*` | Lookup | Key qualifier fields (Id, InteractionId, PrevStepId) | `null` |

**Step Types (Live API Verified - T6 Discovery):**

| Value | Occurrences | Description | When Used |
|-------|-------------|-------------|-----------|
| `LLM_STEP` | 67,163 | LLM call execution | Intent detection, response generation |
| `TOPIC_STEP` | 16,236 | Topic classification/routing | Determining which topic handles the request |
| `SESSION_END` | 14,990 | Session termination | Final step when session closes |
| `ACTION_STEP` | 13,780 | Function/action execution | Calling flows, Apex actions |
| `INTERRUPT_STEP` | 5 | Interrupt processing | Handling interruptions (rare) |

**Common Step Names (Live API Verified):**

| Step Name | Step Type | Description |
|-----------|-----------|-------------|
| `AiCopilot__ReactInitialPrompt` | LLM_STEP | Initial planning/reasoning step |
| `AiCopilot__ReactTopicPrompt` | LLM_STEP | Topic classification/routing decision |
| `AiCopilot__ReactValidationPrompt` | LLM_STEP | Response validation (hallucination check) |
| `CLOSED_USER_REQUEST` | SESSION_END | Session termination by user request |
| `flash_agent` | LLM_STEP | Flash agent LLM invocation |
| `{Topic}.{Action}` | ACTION_STEP | Topic-specific actions (e.g., `Order_Status.Get_Order`) |

**Step Naming Convention:**
- LLM steps use format: `AiCopilot__{PromptName}` or `{agent_name}`
- Action steps use format: `{TopicApiName}.{ActionApiName}`
- Session end steps: `CLOSED_USER_REQUEST`, `ESCALATED`, etc.

**Note:** Steps use linear sequencing via `PrevStepId`. There is no hierarchical parent-child relationship (no `ParentStepId` field).

---

**GenAI Reference Fields:**

The Step entity includes references to every LLM call the reasoning engine makes, enabling joins with feedback data or guardrails metrics:
- `GenerationId` → Links to `GenAIGeneration__dlm` for quality analysis
- `GenAiGatewayRequestId` → Links to `GenAIGatewayRequest__dlm` for prompts
- `GenAiGatewayResponseId` → Links to `GenAIGatewayResponse__dlm` for raw responses

---

### AIAgentMoment (ssot__AiAgentMoment__dlm) ✅ T6 Verified

Represents summarized request/response pairs for analytics and optimization. Contains **13 fields**. Note: The agent API name is stored here (not on Session).

| Field API Name | Type | Description | Example |
|----------------|------|-------------|---------|
| `ssot__Id__c` | Text | Primary key | `a0m1234567890ABC` |
| `ssot__AiAgentSessionId__c` | Text (Parent) | FK to parent session | `a0x1234567890ABC` |
| `ssot__AiAgentApiName__c` | Text | API name of the agent | `Customer_Support_Agent` |
| `ssot__AiAgentVersionApiName__c` | Text | Version of the agent | `v1.2.3` |
| `ssot__RequestSummaryText__c` | Text | Summarized user request | `User asked about order status` |
| `ssot__ResponseSummaryText__c` | Text | Summarized agent response | `Provided tracking info` |
| `ssot__StartTimestamp__c` | DateTime | Moment start time | `2026-01-28T10:15:23.000Z` |
| `ssot__EndTimestamp__c` | DateTime | Moment end time | `2026-01-28T10:15:26.000Z` |
| `ssot__DataSourceId__c` | Text | Data source identifier | `null` |
| `ssot__DataSourceObjectId__c` | Text | Data source object identifier | `null` |
| `ssot__InternalOrganizationId__c` | Text | Internal org identifier | `null` |
| `KQ_*` | Lookup | Key qualifier fields | `null` |

**Moment vs Message:**
- **Moment**: High-level summaries with agent API name for analytics
- **InteractionMessage**: Raw user/agent text per turn with threading support

---

### AIAgentMomentInteraction (ssot__AiAgentMomentInteraction__dlm) ✅ NEW

Junction table linking Moments to Interactions, enabling many-to-many relationships between high-level summaries and detailed interaction data.

| Field API Name | Type | Description | Example |
|----------------|------|-------------|---------|
| `ssot__Id__c` | Text | Primary key | `a0j1234567890ABC` |
| `ssot__AiAgentMomentId__c` | Text (Lookup) | Reference to the Moment | `a0m...` |
| `ssot__AiAgentInteractionId__c` | Text (Lookup) | Reference to the Interaction | `a0y...` |
| `ssot__StartTimestamp__c` | DateTime | When this relationship was created | `2026-01-28T10:15:23.000Z` |
| `ssot__InternalOrganizationId__c` | Text | Internal org identifier | `00D...` |

---

### AIAgentTagDefinition (ssot__AiAgentTagDefinition__dlm) ✅ Verified

Defines tag metadata and structure for the Agentforce tagging system.

| Field API Name | Type | Description | Example |
|----------------|------|-------------|---------|
| `ssot__Id__c` | Text | Primary key | `a0t1234567890ABC` |
| `ssot__Name__c` | Text | Display name of the tag definition | `Escalation_Reason` |
| `ssot__DeveloperName__c` | Text | API-safe name of the tag definition | `Escalation_Reason` |
| `ssot__Description__c` | Text | Description of what the tag represents | `Reason for agent escalation` |
| `ssot__DataType__c` | Text | Data type of tag values | `Text` |
| `ssot__SourceType__c` | Text | How the tag is populated | `Generated` |
| `ssot__CreatedDate__c` | DateTime | When the definition was created | `2026-01-15T08:00:00.000Z` |
| `ssot__InternalOrganizationId__c` | Text | Internal org identifier | `00D...` |

**SourceType Values (Live API Verified):**

| Value | Description |
|-------|-------------|
| `Generated` | System-generated tags |
| `Predefined` | Admin-defined tags |

**DataType Values (Live API Verified):**

| Value | Description |
|-------|-------------|
| `Text` | Text/string values |
| `Integer` | Numeric values |

---

### AIAgentTag (ssot__AiAgentTag__dlm) ✅ Verified

Stores individual tag values associated with tag definitions.

| Field API Name | Type | Description | Example |
|----------------|------|-------------|---------|
| `ssot__Id__c` | Text | Primary key | `a0u1234567890ABC` |
| `ssot__AiAgentTagDefinitionId__c` | Text (Lookup) | Reference to the tag definition | `a0t...` |
| `ssot__Value__c` | Text | The tag value (e.g., rating, category code) | `5` |
| `ssot__Description__c` | Text | Human-readable description of the tag | `Customer frustrated with wait time` |
| `ssot__IsActive__c` | Boolean | Whether the tag is currently active | `true` |
| `ssot__CreatedDate__c` | DateTime | When the tag was created | `2026-01-28T10:15:23.000Z` |
| `ssot__InternalOrganizationId__c` | Text | Internal org identifier | `00D...` |

**Note:** The `Value` field typically contains numeric codes (1-5 for ratings) or short codes, while `Description` contains the human-readable explanation.

---

### AIAgentTagDefinitionAssociation (ssot__AiAgentTagDefinitionAssociation__dlm) ✅ Verified

Links tag definitions to specific agents or prompt templates, defining which tags apply to which agent configurations.

| Field API Name | Type | Description | Example |
|----------------|------|-------------|---------|
| `ssot__Id__c` | Text | Primary key | `a0w1234567890ABC` |
| `ssot__AiAgentTagDefinitionId__c` | Text (Lookup) | Reference to the tag definition | `a0t...` |
| `ssot__AiAgentApiName__c` | Text | API name of the agent this applies to | `Customer_Support_Agent` |
| `ssot__AiPromptTemplateId__c` | Text (Lookup) | Reference to prompt template | `a0p...` |
| `ssot__CreatedDate__c` | DateTime | When the association was created | `2026-01-15T08:00:00.000Z` |
| `ssot__InternalOrganizationId__c` | Text | Internal org identifier | `00D...` |

**Use Cases:**
- Define which tags are applicable to specific agents
- Link tagging to prompt templates for automatic tag application
- Configure agent-specific quality metrics

---

### AIAgentTagAssociation (ssot__AiAgentTagAssociation__dlm) ✅ Verified

Links tags to sessions and moments, enabling flexible categorization of agent interactions. Contains 15 fields.

| Field API Name | Type | Description | Example |
|----------------|------|-------------|---------|
| `ssot__Id__c` | Text | Primary key | `a0v1234567890ABC` |
| `ssot__AiAgentSessionId__c` | Text (Lookup) | Reference to the session | `a0x...` |
| `ssot__AiAgentMomentId__c` | Text (Lookup) | Reference to the moment | `a0m...` |
| `ssot__AiAgentTagDefinitionAssociationId__c` | Text (Lookup) | Reference to tag definition association | `a0w...` |
| `ssot__AiAgentTagId__c` | Text (Lookup) | Direct reference to the tag value ✅ NEW | `a0u...` |
| `ssot__AssociationReasonText__c` | Text | Reason/context for the tag association ✅ NEW | `User expressed frustration` |
| `ssot__CreatedDate__c` | DateTime | When the association was created | `2026-01-28T10:15:23.000Z` |
| `ssot__DataSourceId__c` | Text | Data source identifier | `null` |
| `ssot__DataSourceObjectId__c` | Text | Data source object identifier | `null` |
| `ssot__InternalOrganizationId__c` | Text | Internal org identifier | `null` |
| `KQ_*` | Lookup | Key qualifier fields for relationships | `null` |

**Use Cases:**
- Categorize sessions by customer sentiment
- Tag escalation reasons for analytics
- Apply business-specific labels to conversations
- Track tagging rationale via `AssociationReasonText`

---

## GenAI Audit & Feedback DMOs ✅ T6 Verified

The GenAI Trust Layer provides comprehensive tracking of LLM calls, quality metrics, and safety detections.

### GenAIGeneration (GenAIGeneration__dlm)

Records individual LLM generations. Contains 11 fields.

| Field API Name | Type | Description |
|----------------|------|-------------|
| `generationId__c` | Text | Primary key for joining with Steps |
| `generationResponseId__c` | Text | Response identifier |
| `responseText__c` | Text | Raw LLM response text |
| `maskedResponseText__c` | Text | PII-masked version of response |
| `responseParameters__c` | Text | Model parameters used |
| `feature__c` | Text | Feature that triggered generation |
| `cloud__c` | Text | Cloud identifier |
| `orgId__c` | Text | Organization ID |
| `timestamp__c` | DateTime | Generation timestamp |

### GenAIContentQuality (GenAIContentQuality__dlm)

Quality assessment for each generation. Contains 10 fields.

| Field API Name | Type | Description |
|----------------|------|-------------|
| `id__c` | Text | Primary key |
| `parent__c` | Text | FK to GenAIGeneration.generationId__c |
| `contentType__c` | Text | Type of content assessed |
| `isToxicityDetected__c` | Boolean | Overall toxicity flag |
| `feature__c` | Text | Feature identifier |
| `cloud__c` | Text | Cloud identifier |
| `orgId__c` | Text | Organization ID |
| `timestamp__c` | DateTime | Assessment timestamp |

### GenAIContentCategory (GenAIContentCategory__dlm)

Detailed detector results per quality assessment. Contains 10 fields.

| Field API Name | Type | Description |
|----------------|------|-------------|
| `id__c` | Text | Primary key |
| `parent__c` | Text | FK to GenAIContentQuality.id__c |
| `detectorType__c` | Text | Detector type (see table below) |
| `category__c` | Text | Detection category/result |
| `value__c` | Text | Confidence score (0.0-1.0) |
| `cloud__c` | Text | Cloud identifier |
| `orgId__c` | Text | Organization ID |
| `timestamp__c` | DateTime | Detection timestamp |

**Detector Types (Live API Verified - T6 Discovery):**

| Detector Type | Occurrences | Categories |
|---------------|-------------|------------|
| `TOXICITY` | 627,603 | `hate`, `identity`, `physical`, `profanity`, `safety_score`, `sexual`, `toxicity`, `violence`, `0` |
| `PROMPT_DEFENSE` | 119,050 | `aggregatePromptAttackScore`, `isPromptAttackDetected`, `0`, `1` |
| `PII` | 27,805 | `CREDIT_CARD`, `EMAIL_ADDRESS`, `PERSON`, `US_PHONE_NUMBER` |
| `InstructionAdherence` | 16,380 | `High`, `Low`, `Uncertain` |

### GenAIGatewayRequest (GenAIGatewayRequest__dlm)

Request details for LLM calls. Contains 30 fields (largest DMO).

| Field API Name | Type | Description |
|----------------|------|-------------|
| `gatewayRequestId__c` | Text | Primary key |
| `prompt__c` | Text | Full prompt sent to LLM |
| `maskedPrompt__c` | Text | PII-masked prompt |
| `model__c` | Text | Model name (e.g., `gpt-4`) |
| `provider__c` | Text | Model provider |
| `temperature__c` | Number | Temperature parameter |
| `promptTokens__c` | Number | Input token count |
| `completionTokens__c` | Number | Output token count |
| `totalTokens__c` | Number | Total tokens |
| `promptTemplateDevName__c` | Text | Prompt template developer name |
| `promptTemplateVersionNo__c` | Text | Prompt template version |
| `enableInputSafetyScoring__c` | Text | Input safety enabled flag |
| `enableOutputSafetyScoring__c` | Text | Output safety enabled flag |
| `enablePiiMasking__c` | Text | PII masking enabled flag |
| `sessionId__c` | Text | Related session ID |
| `userId__c` | Text | User who triggered request |
| `appType__c` | Text | Application type |
| `feature__c` | Text | Feature identifier |

### GenAIGatewayResponse (GenAIGatewayResponse__dlm)

Response metadata for LLM calls. Contains 8 fields.

| Field API Name | Type | Description |
|----------------|------|-------------|
| `generationRequestId__c` | Text | FK to GatewayRequest |
| `generationResponseId__c` | Text | Response identifier |
| `parameters__c` | Text | Response parameters JSON |
| `cloud__c` | Text | Cloud identifier |
| `orgId__c` | Text | Organization ID |
| `timestamp__c` | DateTime | Response timestamp |

### GenAIFeedback (GenAIFeedback__dlm)

User feedback on LLM responses. Contains 16 fields.

| Field API Name | Type | Description |
|----------------|------|-------------|
| `feedbackId__c` | Text | Primary key |
| `generationId__c` | Text | FK to Generation |
| `feedback__c` | Text | Feedback value (e.g., `GOOD`) |
| `action__c` | Text | User action taken |
| `source__c` | Text | Feedback source |
| `userId__c` | Text | User who gave feedback |
| `appType__c` | Text | Application type |
| `feature__c` | Text | Feature identifier |
| `timestamp__c` | DateTime | Feedback timestamp |

**Feedback Values:**

| Value | Description |
|-------|-------------|
| `GOOD` | Positive feedback (thumbs up) |
| `BAD` | Negative feedback (thumbs down) |

### GenAIFeedbackDetail (GenAIFeedbackDetail__dlm)

Detailed feedback with free-text comments. Contains 10 fields.

| Field API Name | Type | Description |
|----------------|------|-------------|
| `feedbackDetailId__c` | Text | Primary key |
| `parent__c` | Text | FK to Feedback |
| `feedbackText__c` | Text | Free-text feedback comment |
| `appFeedback__c` | Text | App-specific feedback |
| `feature__c` | Text | Feature identifier |

### Other GenAI DMOs

| DMO Name | Fields | Description |
|----------|--------|-------------|
| `GenAIAppGeneration__dlm` | 10 | Application-level generation records |
| `GenAIGatewayRequestTag__dlm` | 9 | Tags for gateway requests |
| `GenAIGtwyRequestMetadata__dlm` | 10 | Request metadata (type, JSON) |
| `GenAIGtwyObjRecord__dlm` | 13 | Object record references |
| `GenAIGtwyObjRecCitationRef__dlm` | 9 | Citation references |
| `GenAIGtwyRequestLLM__dlm` | 0 | LLM-specific request data (empty) |

### RAG Quality DMOs ❌ NOT FOUND

The following DMOs were probed but **do not exist** in the live API:

| DMO Name | Status | Notes |
|----------|--------|-------|
| `GenAIRetrieverResponse__dlm` | ❌ Not Found | Table does not exist |
| `GenAIRetrieverRequest__dlm` | ❌ Not Found | Table does not exist |
| `GenAIRetrieverQualityMetric__dlm` | ❌ Not Found | Table does not exist |

> **Note:** These DMOs may be available in future API versions or require specific enablement.

---

## Data Relationships

```sql
-- Session → Interactions
SELECT i.*
FROM ssot__AIAgentInteraction__dlm i
WHERE i.ssot__AiAgentSessionId__c = 'SESSION_ID';

-- Interaction → Steps
SELECT s.*
FROM ssot__AIAgentInteractionStep__dlm s
WHERE s.ssot__AiAgentInteractionId__c = 'INTERACTION_ID';

-- Interaction → Messages
SELECT m.*
FROM ssot__AIAgentMoment__dlm m
WHERE m.ssot__AiAgentInteractionId__c = 'INTERACTION_ID';
```

---

## Data Volume Considerations

| Scenario | Sessions/Day | Total Records/Day |
|----------|--------------|-------------------|
| Low volume | 100-1K | 10K-100K |
| Medium volume | 1K-10K | 100K-1M |
| High volume | 10K-100K | 1M-10M |
| Enterprise | 100K+ | 10M+ |

**Estimation Formula:**
```
Total records ≈ Sessions × Avg turns × (1 + Avg steps + 2)
Example: 10K sessions × 4 turns × 5 = 200K records
```

---

## Data Retention

Session tracing data in Data Cloud follows the org's data retention policy. Default:
- **Production**: 13 months
- **Sandbox**: 30 days

---

## Enabling Session Tracing

1. **Setup** → **Agentforce** → **Settings**
2. Enable **Session Tracing**
3. Configure which agents to trace
4. Wait 5-15 minutes for data to appear in Data Cloud

---

## Related Resources

- [Query Patterns](query-patterns.md) - Example queries
- [Analysis Cookbook](analysis-cookbook.md) - Common analysis patterns
- [Troubleshooting](troubleshooting.md) - Common issues
