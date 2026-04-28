<!-- Parent: sf-ai-agentforce-testing/SKILL.md -->
# Agent Runtime API Reference

Reference for Salesforce Einstein Agent Runtime API v1 — the REST API used for multi-turn agent testing.

---

## Overview

The Agent Runtime API provides programmatic access to Agentforce agents via REST endpoints. Unlike the CLI-based Agent Testing Center (single-utterance tests), this API supports **multi-turn conversations** with full session lifecycle management.

> ⚠️ **Agent API is NOT supported for agents of type "Agentforce (Default)".** Only custom agents created via Agentforce Builder are supported.

| Feature | Agent Testing Center (CLI) | Agent Runtime API |
|---------|---------------------------|-------------------|
| Multi-turn conversations | ❌ No | ✅ Yes |
| Session state management | ❌ No | ✅ Yes |
| Context preservation testing | ❌ No | ✅ Yes |
| Topic re-matching validation | ❌ No | ✅ Yes |
| Requires AiEvaluationDefinition | ✅ Yes | ❌ No |
| Requires Agent Testing Center feature | ✅ Yes | ❌ No |
| Auth mechanism | sf CLI org auth | Client Credentials ECA |

---

## Base URL

```
https://api.salesforce.com/einstein/ai-agent/v1
```

> **Note:** This is the global Salesforce API endpoint, NOT your My Domain URL. The My Domain is passed as `instanceConfig.endpoint` within the session creation payload.

---

## Authentication

The Agent Runtime API requires an **OAuth 2.0 access token** obtained via **Client Credentials flow** from an External Client App (ECA).

> **NEVER use `curl` for OAuth token validation.** Domains containing `--` (e.g., `my-org--sandbox.example.my.salesforce.com`) cause shell expansion failures. The `agent_api_client.py` handles OAuth internally.

```bash
# Verify credentials work (credential_manager.py handles OAuth internally)
python3 ~/.claude/skills/sf-ai-agentforce-testing/hooks/scripts/credential_manager.py \
  validate --org-alias {org} --eca-name {eca}

# The agent_api_client.py and multi_turn_test_runner.py handle token acquisition
# automatically — you never need to manually obtain tokens.
```

**Required:** An External Client App configured with Client Credentials flow. See [ECA Setup Guide](eca-setup-guide.md).

---

## Endpoints

### 1. Create Session

Start a new agent conversation session.

**Request:**
```
POST /einstein/ai-agent/v1/agents/{agentId}/sessions
```

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Body:**
```json
{
  "externalSessionKey": "unique-uuid-per-session",
  "instanceConfig": {
    "endpoint": "https://your-domain.my.salesforce.com"
  },
  "streamingCapabilities": {
    "chunkTypes": ["Text"]
  },
  "bypassUser": true
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `externalSessionKey` | string | ✅ | Unique identifier for this session (UUID recommended) |
| `instanceConfig.endpoint` | string | ✅ | Your Salesforce My Domain URL (https://...) |
| `streamingCapabilities.chunkTypes` | array | ✅ | Response chunk types to receive (`["Text"]`) |
| `bypassUser` | boolean | ❌ | If `true`, use the agent-assigned user. If `false`, use the token user. Set `true` for Client Credentials testing. |
| `variables` | array | ❌ | Agent input variables. Each: `{"name": "$Context.X", "type": "Text", "value": "..."}` |

**Response (200 OK):**
```json
{
  "sessionId": "8e715939-a121-40ec-80e3-a8d1ac89da33",
  "_links": {
    "self": null,
    "messages": {
      "href": "https://api.salesforce.com/einstein/ai-agent/v1/sessions/8e715939.../messages/stream"
    },
    "session": {
      "href": "https://api.salesforce.com/einstein/ai-agent/v1/agents/0XxQZ.../sessions"
    },
    "end": {
      "href": "https://api.salesforce.com/einstein/ai-agent/v1/sessions/8e715939..."
    }
  },
  "messages": [
    {
      "type": "Inform",
      "id": "8e7cafae-0eb5-44b1-9195-21f1cd6e1f4b",
      "feedbackId": "",
      "planId": "",
      "isContentSafe": true,
      "message": "Hi, I'm an AI service assistant. How can I help you?",
      "result": [],
      "citedReferences": []
    }
  ]
}
```

> **Note:** The session start response includes an initial greeting message from the agent in the `messages` array.

**Error Responses:**

| Status | Meaning | Common Cause |
|--------|---------|--------------|
| 400 | Bad Request | Invalid agentId or malformed body |
| 401 | Unauthorized | Invalid or expired token |
| 403 | Forbidden | ECA scopes insufficient |
| 404 | Not Found | Agent not found or not activated |
| 429 | Rate Limited | Too many concurrent sessions |

---

### 2. Send Message

Send a user message within an active session.

**Request:**
```
POST /einstein/ai-agent/v1/sessions/{sessionId}/messages
```

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Body:**
```json
{
  "message": {
    "sequenceId": 1,
    "type": "Text",
    "text": "I need to cancel my appointment"
  }
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message.sequenceId` | integer | ✅ | Incrementing sequence number (1, 2, 3...) |
| `message.type` | string | ✅ | Message type (always `"Text"`) |
| `message.text` | string | ✅ | The user's message text |

> **CRITICAL:** `sequenceId` MUST increment by 1 for each message in the session. Reusing or skipping IDs causes errors.

**Response (200 OK):**
```json
{
  "messages": [
    {
      "type": "Inform",
      "id": "ceb6b5de-6063-4e39-bc02-91e9bf7da867",
      "metrics": {},
      "feedbackId": "0bc8720e-e010-4129-87bb-70caaa885ee4",
      "planId": "0bc8720e-e010-4129-87bb-70caaa885ee4",
      "isContentSafe": true,
      "message": "I'd be happy to help you cancel your appointment...",
      "result": [],
      "citedReferences": []
    }
  ],
  "_links": {
    "self": null,
    "messages": { "href": "https://api.salesforce.com/einstein/ai-agent/v1/sessions/{sessionId}/messages" },
    "messagesStream": { "href": "https://api.salesforce.com/einstein/ai-agent/v1/sessions/{sessionId}/messages/stream" },
    "session": { "href": "https://api.salesforce.com/einstein/ai-agent/v1/agents/{agentId}/sessions" },
    "end": { "href": "https://api.salesforce.com/einstein/ai-agent/v1/sessions/{sessionId}" }
  }
}
```

**Response Message Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Message type (see types below) |
| `id` | string | Unique message identifier |
| `message` | string | The agent's text response |
| `feedbackId` | string | ID for submitting feedback on this response |
| `planId` | string | ID of the execution plan |
| `isContentSafe` | boolean | Whether content passed safety checks |
| `result` | array | Action result data (empty if no actions executed) |
| `citedReferences` | array | Cited sources with optional inline metadata |

**Response Message Types:**

| Type | Description | When It Appears |
|------|-------------|-----------------|
| `Inform` | Informational response | Standard agent replies |
| `Confirm` | Confirmation request | Before executing an action |
| `Escalation` | Handoff to human | Escalation triggered |
| `SessionEnded` | Session terminated | Agent or system ends conversation |
| `ProgressIndicator` | Processing notification | Streaming: action in progress |
| `TextChunk` | Incremental text | Streaming: partial response |
| `EndOfTurn` | Turn complete | Streaming: response finished |

---

### 3. End Session

Terminate an active session and release resources.

**Request:**
```
DELETE /einstein/ai-agent/v1/sessions/{sessionId}
```

**Headers:**
```
Authorization: Bearer {access_token}
x-session-end-reason: UserRequest
```

> **IMPORTANT:** The `x-session-end-reason` header is required. Use `UserRequest` for normal session termination.

**Response (200 OK):**
```json
{
  "messages": [
    {
      "type": "SessionEnded",
      "id": "c5692ca0-ee1b-414a-9d96-4e7862456500",
      "reason": "ClientRequest",
      "feedbackId": ""
    }
  ],
  "_links": { ... }
}
```

> **Best Practice:** Always end sessions after testing to avoid resource leaks and rate limit issues.

---

### 4. Send Agent Variables

Variables can be passed at session start and (for editable variables) with messages.

**Session Start with Variables:**
```json
{
  "externalSessionKey": "{UUID}",
  "instanceConfig": { "endpoint": "https://{MY_DOMAIN_URL}" },
  "streamingCapabilities": { "chunkTypes": ["Text"] },
  "bypassUser": true,
  "variables": [
    { "name": "$Context.EndUserLanguage", "type": "Text", "value": "en_US" },
    { "name": "$Context.AccountId", "type": "Id", "value": "001XXXXXXXXXXXX" },
    { "name": "team_descriptor", "type": "Text", "value": "Premium Support" }
  ]
}
```

**Variable Types:**

| Type | Description |
|------|-------------|
| `Text` | String value |
| `Number` | Numeric value |
| `Boolean` | true/false |
| `Id` | Salesforce record ID |
| `Date` | Date value |
| `DateTime` | DateTime value |
| `Currency` | Currency value |
| `Object` | Complex object |

**Important Notes:**
- Context variables (`$Context.*`) are **read-only after session start** (except `$Context.EndUserLanguage`)
- Custom variables derived from custom fields: omit the `__c` suffix (e.g., `Conversation_Key__c` → `$Context.Conversation_Key`)
- Variables must have `Allow value to be set by API` checked in Agentforce Builder
- Only editable variables can be modified in a `send message` call

---

### 5. Submit Feedback

Submit feedback on an agent's response for Data 360 tracking.

**Request:**
```
POST /einstein/ai-agent/v1/sessions/{sessionId}/feedback
```

**Body:**
```json
{
  "feedbackId": "0bc8720e-e010-4129-87bb-70caaa885ee4",
  "feedback": "GOOD",
  "text": "Response was accurate and helpful"
}
```

Returns HTTP 201 on success.

---

## Agent ID Discovery

Before calling the API, you need the agent's `BotDefinition` ID:

```bash
# Query active agents in the org
sf data query --use-tooling-api \
  --query "SELECT Id, DeveloperName, MasterLabel FROM BotDefinition WHERE IsActive=true" \
  --result-format json --target-org [alias]
```

The `Id` field from the query result is the `{agentId}` used in session creation.

---

## Complete Multi-Turn Example

```bash
#!/bin/bash
# Multi-turn agent conversation test

SF_MY_DOMAIN="your-domain.my.salesforce.com"
CONSUMER_KEY="your_key"
CONSUMER_SECRET="your_secret"
AGENT_ID="0XxRM0000004ABC"

# 1. Get access token (use credential_manager.py to validate first)
# python3 ~/.claude/skills/sf-ai-agentforce-testing/hooks/scripts/credential_manager.py \
#   validate --org-alias {org} --eca-name {eca}
# The agent_api_client.py handles token acquisition automatically.
# For manual scripting, source credentials from ~/.sfagent/{org}/{eca}/credentials.env
source ~/.sfagent/${ORG_ALIAS}/${ECA_NAME}/credentials.env
SF_TOKEN=$(python3 -c "
from hooks.scripts.agent_api_client import AgentAPIClient
c = AgentAPIClient()
print(c._get_token())
")

# 2. Create session
SESSION_ID=$(curl -s -X POST \
  "https://api.salesforce.com/einstein/ai-agent/v1/agents/${AGENT_ID}/sessions" \
  -H "Authorization: Bearer ${SF_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "externalSessionKey":"'"$(uuidgen | tr A-Z a-z)"'",
    "instanceConfig":{"endpoint":"https://'"${SF_MY_DOMAIN}"'"},
    "streamingCapabilities":{"chunkTypes":["Text"]},
    "bypassUser":true
  }' | jq -r '.sessionId')

echo "Session: ${SESSION_ID}"

# 3. Turn 1: Initial request
R1=$(curl -s -X POST \
  "https://api.salesforce.com/einstein/ai-agent/v1/sessions/${SESSION_ID}/messages" \
  -H "Authorization: Bearer ${SF_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"message":{"sequenceId":1,"type":"Text","text":"I need to cancel my appointment"}}')
echo "Turn 1 Response: $(echo $R1 | jq -r '.messages[0].message')"

# 4. Turn 2: Follow-up
R2=$(curl -s -X POST \
  "https://api.salesforce.com/einstein/ai-agent/v1/sessions/${SESSION_ID}/messages" \
  -H "Authorization: Bearer ${SF_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"message":{"sequenceId":2,"type":"Text","text":"Actually, can I reschedule instead?"}}')
echo "Turn 2 Response: $(echo $R2 | jq -r '.messages[0].message')"

# 5. Turn 3: Context check
R3=$(curl -s -X POST \
  "https://api.salesforce.com/einstein/ai-agent/v1/sessions/${SESSION_ID}/messages" \
  -H "Authorization: Bearer ${SF_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"message":{"sequenceId":3,"type":"Text","text":"What was my original request about?"}}')
echo "Turn 3 Response: $(echo $R3 | jq -r '.messages[0].message')"

# 6. End session
curl -s -X DELETE \
  "https://api.salesforce.com/einstein/ai-agent/v1/sessions/${SESSION_ID}" \
  -H "Authorization: Bearer ${SF_TOKEN}"
echo "Session ended."
```

---

## Response Analysis

When analyzing multi-turn responses, check these indicators:

### Per-Turn Checklist

| Check | What to Look For | Pass Criteria |
|-------|------------------|---------------|
| **Non-empty** | Response has text content | `messages[0].message` is not empty |
| **Topic match** | Response language matches expected topic | Infer from response content and actions |
| **Action invoked** | Expected actions executed | `result.type` = `ActionResult` present |
| **Context retained** | References to prior turns | Agent acknowledges prior conversation |
| **Error-free** | No error indicators | No `Failure` or `Escalation` types (unless expected) |

### Error Indicators in Responses

| Indicator | Meaning | Action |
|-----------|---------|--------|
| `"type": "Failure"` | Action execution failed | Check Flow/Apex |
| `"type": "Escalation"` | Agent escalated to human | May be expected or failure |
| Empty `messages` array | Agent produced no response | Check agent activation |
| HTTP 500 on message send | Server-side error | Retry or check agent config |
| `"result": null` | No plan executed | Topic may not have matched |

---

## Rate Limits & Best Practices

### Rate Limits

| Resource | Limit | Notes |
|----------|-------|-------|
| Concurrent sessions per org | 10 | End sessions promptly |
| Messages per session | 50 | Sufficient for testing |
| Requests per minute | 100 | Per connected app |
| Session timeout | 15 min | Inactive sessions auto-close |

### Best Practices

1. **Always end sessions** — Call DELETE after each test scenario
2. **Unique session keys** — Use `uuidgen` for `externalSessionKey`
3. **Increment sequenceId** — Never reuse or skip sequence numbers
4. **Check for empty responses** — Agent may not respond if not activated
5. **Handle rate limits** — Add retry logic with backoff for 429 responses
6. **Keep credentials in memory** — Never write ECA secrets to files

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| 401 on token request | Wrong Consumer Key/Secret | Verify ECA credentials |
| 401 on API call | Token expired | Re-authenticate |
| 404 on session create | Wrong Agent ID | Re-query BotDefinition |
| 400 "Invalid session" | Session already ended | Create new session |
| 400 "Invalid sequenceId" | Wrong sequence number | Ensure incrementing from 1 |
| Empty response | Agent not activated | Activate and publish agent |
| "Rate limit exceeded" | Too many concurrent sessions | End unused sessions first |

---

## Related Documentation

| Resource | Link |
|----------|------|
| ECA Setup | [eca-setup-guide.md](eca-setup-guide.md) |
| Multi-Turn Testing | [multi-turn-testing.md](multi-turn-testing.md) |
