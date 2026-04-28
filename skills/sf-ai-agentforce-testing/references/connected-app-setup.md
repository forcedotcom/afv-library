<!-- Parent: sf-ai-agentforce-testing/SKILL.md -->
# Authentication Guide for Agent Testing

Guide to authentication methods for agent preview and API-based testing.

---

## Overview

> **Current CLI behavior**: `sf agent preview` uses standard org authentication — no Connected App or ECA is required for simulated or live preview.

Agent testing uses **two different auth methods** depending on the testing approach:

| Testing Approach | Auth Method | Setup Required |
|------------------|-------------|----------------|
| **Preview (Simulated)** | Standard org auth | `sf org login web` |
| **Preview (Live)** | Standard org auth | `sf org login web` |
| **Agent Runtime API** (multi-turn) | External Client App (ECA) | Client Credentials flow |

---

## Preview Authentication

Both simulated and live preview modes use standard Salesforce CLI authentication. No Connected App or ECA is required.

For programmatic preview sessions, keep the auth model the same: published agents use standard org auth, and authoring-bundle sessions also use standard org auth but now require an explicit execution-mode flag on `sf agent preview start` (`--simulate-actions` or `--use-live-actions`).

### Authenticate to Your Org

```bash
# Web-based OAuth login
sf org login web --alias myorg

# Verify authentication
sf org display --target-org myorg
```

### Run Live Preview

```bash
# Simulated mode (default - no real actions executed)
sf agent preview --api-name Customer_Support_Agent --target-org myorg

# Live mode (real Flows/Apex execute)
sf agent preview --api-name Customer_Support_Agent --use-live-actions --target-org myorg

# Live mode with debug output
sf agent preview \
  --api-name Customer_Support_Agent \
  --use-live-actions \
  --apex-debug \
  --output-dir ./logs \
  --target-org myorg

# Save transcripts
sf agent preview \
  --api-name Customer_Support_Agent \
  --use-live-actions \
  --output-dir ./preview-logs \
  --target-org myorg
```

---

## Output Files

When using `--output-dir`, you get:

### transcript.json

Conversation record:

```json
{
  "conversationId": "0Af7X000000001",
  "messages": [
    {"role": "user", "content": "Where is my order?", "timestamp": "..."},
    {"role": "assistant", "content": "Let me check...", "timestamp": "..."}
  ],
  "status": "completed"
}
```

### responses.json

Full API details including action invocations:

```json
{
  "messages": [
    {
      "role": "function",
      "name": "get_order_status",
      "content": {
        "orderId": "a1J7X00000001",
        "status": "Shipped",
        "trackingNumber": "1Z999..."
      },
      "executionTimeMs": 450
    }
  ],
  "metrics": {
    "flowInvocations": 1,
    "apexInvocations": 0,
    "totalDuration": 3050
  }
}
```

### apex-debug.log

When using `--apex-debug`:

```
13:45:22.123 (123456789)|USER_DEBUG|[15]|DEBUG|Processing order lookup
13:45:22.234 (234567890)|SOQL_EXECUTE_BEGIN|[20]|Aggregations:0|SELECT Id, Status...
13:45:22.345 (345678901)|SOQL_EXECUTE_END|[20]|Rows:1
```

---

## Troubleshooting

### 401 Unauthorized

**Cause:** Org authentication expired or invalid.

**Solution:**
1. Re-authenticate: `sf org login web --alias [alias]`
2. Verify auth is valid: `sf org display --target-org [alias]`
3. Ensure user has Agentforce permissions

### Actions not executing

**Cause:** Actions require deployed Flows/Apex.

**Solution:**
1. Verify Flow is active via SOQL: `sf data query --query "SELECT Id, ActiveVersionId, Status FROM FlowDefinitionView WHERE ApiName = '[FlowName]'" --target-org [OrgAlias]`
2. Deploy/activate Flow via metadata: `sf project deploy start --metadata Flow:[FlowName] --target-org [OrgAlias]`
3. Verify Apex is deployed: `sf project deploy start --metadata ApexClass:[ClassName]`
4. Check agent is activated: `sf agent activate --api-name [Agent]`

### Timeout errors

**Cause:** Flow or Apex taking too long.

**Solution:**
1. Add debug logs: `--apex-debug`
2. Check Flow for long-running operations
3. Verify external callouts are responsive

---

## Agent Runtime API Auth (ECA)

For **multi-turn API testing** (not CLI preview), you need an External Client App with Client Credentials flow.

### Standard Auth vs ECA Comparison

| Aspect | Standard Auth (Preview) | Client Credentials (ECA) |
|--------|------------------------|--------------------------|
| **Used by** | `sf agent preview` (simulated + live) | Agent Runtime API (multi-turn testing) |
| **App type** | None required | External Client App (ECA) |
| **Auth flow** | Standard CLI auth (browser login) | Client Credentials (machine-to-machine) |
| **User interaction** | Browser redirect | None — fully automated |
| **Best for** | Manual interactive testing | Automated multi-turn API testing |
| **Setup guide** | This section | [ECA Setup Guide](eca-setup-guide.md) |

### Decision Flow

```
What are you testing?
    │
    ├─ Interactive preview (sf agent preview)?
    │   → Standard org auth (sf org login web) — no app setup needed
    │
    └─ Multi-turn API conversations?
        → Use External Client App (Client Credentials) — see eca-setup-guide.md
```

### When You Need an ECA

If you're doing **multi-turn API testing** via Agent Runtime API, you'll need:
- An **External Client App** with Client Credentials flow ([ECA Setup Guide](eca-setup-guide.md))
- Scopes: `api`, `chatbot_api`, `sfap_api`

Preview testing (simulated or live) only requires standard `sf org login web`.

---

## Related Skills

| Skill | Use For |
|-------|---------|
| sf-connected-apps | Create and manage Connected Apps and ECAs |
| sf-flow | Debug failing Flow actions |
| sf-apex | Debug failing Apex actions |
| sf-debug | Analyze debug logs |
