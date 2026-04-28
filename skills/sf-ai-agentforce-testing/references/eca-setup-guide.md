<!-- Parent: sf-ai-agentforce-testing/SKILL.md -->
# External Client App (ECA) Setup for Agent API Testing

Guide for creating an External Client App with Client Credentials flow to authenticate with the Agent Runtime API.

---

## Overview

The Agent Runtime API requires **OAuth 2.0 Client Credentials flow**, which is different from the Web Server OAuth flow used by `sf agent preview`. This requires an **External Client App (ECA)**, not a standard Connected App.

### OAuth Flow Comparison

| Flow | Used By | App Type | User Interaction |
|------|---------|----------|-----------------|
| **Standard Org Auth** | `sf agent preview --use-live-actions` | None (standard `sf org login web`) | Browser login required |
| **Client Credentials** | Agent Runtime API (multi-turn testing) | External Client App (ECA) | None (machine-to-machine) |

> **Key Difference:** Client Credentials flow is machine-to-machine — no browser login needed. Perfect for automated testing.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Salesforce org with Agentforce | Agent must be published and activated |
| System Administrator profile | Required to create ECAs |
| My Domain enabled | Required for OAuth endpoints |
| Agent Runtime API access | Included with Agentforce license |

---

## Quick Setup

### Option 1: Use sf-connected-apps Skill (Recommended)

```
Skill(skill="sf-connected-apps", args="Create External Client App with Client Credentials flow for Agent Runtime API testing. Scopes: api, chatbot_api, sfap_api, refresh_token, offline_access")
```

### Option 2: Manual Setup via UI

Follow the steps below.

---

## Step-by-Step Manual Creation

### Step 1: Navigate to External Client App Setup

1. **Setup** → Quick Find → **App Manager**
2. Click **New Connected App** → Select **External Client App**
3. Or: **Setup** → Quick Find → **External Client Apps**

### Step 2: Basic Information

| Field | Value |
|-------|-------|
| **Name** | Agent API Testing |
| **API Name** | Agent_API_Testing |
| **Contact Email** | Your admin email |
| **Description** | ECA for Agent Runtime API multi-turn testing |

### Step 3: Configure Client Credentials

1. Under **OAuth Settings**:
   - **Enable Client Credentials Flow**: ✅ Checked
   - **Grant Type**: Client Credentials
2. **Callback URL**: Not required for Client Credentials (use `https://login.salesforce.com/services/oauth2/callback` if field is mandatory)

### Step 4: OAuth Scopes

| Scope | Purpose | Required |
|-------|---------|----------|
| `api` | Manage user data via APIs | ✅ Yes |
| `chatbot_api` | Access chatbot/agent services | ✅ Yes |
| `sfap_api` | Access the Salesforce API Platform | ✅ Yes |
| `refresh_token, offline_access` | Perform requests at any time | Recommended |

> **Minimum Required:** `api`, `chatbot_api`, and `sfap_api` together enable Agent Runtime API access.

### Additional OAuth Settings

| Setting | Value |
|---------|-------|
| **Enable Client Credentials Flow** | ✅ Checked |
| **Issue JWT-based access tokens for named users** | ✅ Checked |
| Require secret for Web Server Flow | ❌ Deselected |
| Require secret for Refresh Token Flow | ❌ Deselected |
| Require PKCE for Supported Authorization Flows | ❌ Deselected |

### Step 5: Execution User (Run As)

For Client Credentials flow, you must assign an **execution user**:

1. From your app settings, click the **Policy** tab
2. Click **Edit**
3. Under **OAuth Flows and External Client App Enhancements**:
   - Check **Enable Client Credentials Flow**
   - Set **Run As (Username)** to a user with at least API Only access
4. Save the changes

The execution user's permissions determine what the API can access:
- Must have at least API access
- Must have access to the agents being tested
- System Administrator profile works but use least-privilege when possible

### Step 6: Save and Retrieve Credentials

1. **Save** the External Client App
2. Click **Manage Consumer Details**
3. Verify identity (email/SMS code)
4. Copy:
   - **Consumer Key** (Client ID)
   - **Consumer Secret** (Client Secret)

> ⚠️ **Security:** Store credentials securely. Never commit them to source control or write them to files during testing. Keep them in shell variables within the conversation context only.

---

## Verify ECA Configuration

### Test Token Request

> **NEVER use `curl` for OAuth token validation.** Domains containing `--` (e.g., `my-org--sandbox.example.my.salesforce.com`) cause shell expansion failures with curl's `--` argument parsing. Use the credential manager script instead.

```bash
# Validate credentials via credential_manager.py (handles OAuth internally)
python3 ~/.claude/skills/sf-ai-agentforce-testing/hooks/scripts/credential_manager.py \
  validate --org-alias {org} --eca-name {eca}
```

The script outputs JSON with the validation result including token metadata (scopes, instance URL, token type).

### Expected Success Response

```json
{
  "access_token": "eyJ0bmsiOiJjb3JlL3Byb2QvM...(JWT token)",
  "signature": "HBb7Zf4aaOUlI1V...",
  "token_format": "jwt",
  "scope": "sfap_api chatbot_api api",
  "instance_url": "https://your-domain.my.salesforce.com",
  "id": "https://login.salesforce.com/id/00D.../005...",
  "token_type": "Bearer",
  "issued_at": "1700000000000",
  "api_instance_url": "https://api.salesforce.com"
}
```

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `invalid_client_id` | Wrong Consumer Key | Re-copy from ECA settings |
| `invalid_client` | Client Credentials not enabled | Enable in ECA OAuth settings |
| `invalid_grant` | No execution user assigned | Assign Run As user in ECA |
| `unsupported_grant_type` | Not an ECA (standard Connected App) | Create an External Client App, not Connected App |
| `INVALID_SESSION_ID` | Token expired or revoked | Re-authenticate |

---

## ECA vs Connected App: When to Use Which

| Scenario | Use | Why |
|----------|-----|-----|
| `sf agent preview --use-live-actions` | Standard org auth | No app setup needed (v2.121.7+) |
| Multi-turn API testing | External Client App (Client Credentials) | Machine-to-machine, no browser needed |
| CI/CD automated testing | External Client App (Client Credentials) | Non-interactive, scriptable |
| Manual ad-hoc testing | Either | Depends on test approach |

---

## Security Best Practices

| Practice | Description |
|----------|-------------|
| **Never write secrets to files** | Keep Consumer Key/Secret in shell variables only |
| **Use least-privilege execution user** | Don't use full admin if not needed |
| **Rotate secrets periodically** | Regenerate Consumer Secret quarterly |
| **Limit OAuth scopes** | Only include scopes needed for testing |
| **Monitor usage** | Review ECA login history in Setup |
| **Separate test and production ECAs** | Never reuse production credentials for testing |

---

## Integration with Testing Workflow

Once ECA is configured, the testing skill uses it as follows:

```
1. AskUserQuestion: "Do you have an ECA with Client Credentials?"
   │
   ├─ YES → Collect Consumer Key, Secret, My Domain URL
   │        (stored in conversation context only)
   │
   └─ NO → Delegate:
           Skill(skill="sf-connected-apps",
             args="Create ECA with Client Credentials for Agent API testing")
           Then collect credentials from user
   │
   ▼
2. Authenticate and retrieve access token
3. Query BotDefinition for agent ID
4. Begin multi-turn test execution
```

---

## Related Documentation

| Resource | Link |
|----------|------|
| Agent Runtime API | [agent-api-reference.md](agent-api-reference.md) |
| Connected App Setup (Web OAuth) | [connected-app-setup.md](connected-app-setup.md) |
| Multi-Turn Testing | [multi-turn-testing.md](multi-turn-testing.md) |
