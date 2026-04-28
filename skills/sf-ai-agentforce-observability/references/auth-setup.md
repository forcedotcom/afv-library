<!-- Parent: sf-ai-agentforce-observability/SKILL.md -->
# Authentication Setup

This skill uses JWT Bearer authentication to access the Data Cloud Query API. Authentication is configured via an **External Client App (ECA)** in Salesforce.

## Prerequisites

1. **Salesforce CLI** installed and authenticated to your org
2. **OpenSSL** for certificate generation
3. **Data Cloud** enabled in your org
4. **System Administrator** profile (or appropriate permissions for ECA setup)

---

## Quick Setup (5 Steps)

### Step 1: Generate JWT Certificate

```bash
# Create directory for JWT keys
mkdir -p ~/.sf/jwt

# Generate private key and self-signed certificate (valid 1 year)
# Naming convention: {org_alias}-agentforce-observability.key
openssl req -x509 -sha256 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout ~/.sf/jwt/YourOrg-agentforce-observability.key \
    -out ~/.sf/jwt/YourOrg-agentforce-observability.crt \
    -subj "/CN=AgentforceObservability/O=YourOrg"

# Secure the private key (required - Salesforce rejects world-readable keys)
chmod 600 ~/.sf/jwt/YourOrg-agentforce-observability.key
```

### Step 2: Create External Client App

In Salesforce Setup:

1. **Setup** → **External Client App Manager** → **New External Client App**
2. Fill in the basic details:

| Field | Value |
|-------|-------|
| Name | `Agentforce Observability` |
| API Name | `Agentforce_Observability` |
| Description | `JWT Bearer auth for Agentforce STDM extraction via Claude Code` |
| Distribution State | `Local` |

3. Click **Save**

### Step 3: Configure OAuth Settings

In the ECA → **OAuth Settings** tab:

| Setting | Value |
|---------|-------|
| Enable OAuth | ✅ Checked |
| Callback URL | `https://login.salesforce.com/services/oauth2/callback` |
| Selected OAuth Scopes | `cdp_query_api`, `refresh_token, offline_access` |
| Require PKCE | ❌ Unchecked (not needed for JWT Bearer) |
| Enable Client Credentials Flow | ❌ Optional |

**Upload Certificate:**
1. Check **Use digital signatures**
2. Click **Choose File**
3. Upload `~/.sf/jwt/{org}-agentforce-observability.crt`
4. Click **Save**

### Step 4: Configure App Policies

In the ECA → **Policies** tab:

| Setting | Value |
|---------|-------|
| Permitted Users | **Admin approved users are pre-authorized** |
| IP Relaxation | Relax IP restrictions (for CLI usage) |

**Add Your User:**
1. Click **Manage** → **Manage Profiles** or **Manage Permission Sets**
2. Add your user's profile or an appropriate permission set
3. Click **Save**

### Step 5: Get Consumer Key & Test

1. Go to ECA → **OAuth Settings** tab
2. Copy the **Consumer Key** (starts with `3MVG9...`)
3. Test authentication:

```bash
# Option 1: Pass consumer key directly
python3 scripts/cli.py test-auth \
    --org YourOrg \
    --consumer-key "3MVG9..."

# Option 2: Use environment variable
export SF_CONSUMER_KEY="3MVG9..."
python3 scripts/cli.py test-auth --org YourOrg
```

**Expected output:**
```
Testing Authentication
Org: YourOrg
Key: /Users/you/.sf/jwt/YourOrg-agentforce-observability.key

Getting org info...
Instance: https://your-org.my.salesforce.com
Username: your.user@example.com
Sandbox: True

Testing token generation...
✓ Token generated

Testing Data Cloud access...
✓ Data Cloud accessible

Authentication successful!
```

---

## Key Path Resolution

The CLI resolves the private key path in this order:

1. **Explicit `--key-path`** argument (highest priority)
2. **App-specific key**: `~/.sf/jwt/{org_alias}-agentforce-observability.key`
3. **Generic org key**: `~/.sf/jwt/{org_alias}.key` (fallback)

### Examples

```bash
# Uses app-specific key automatically
python3 scripts/cli.py test-auth --org YourOrg --consumer-key "..."
# → Resolves to: ~/.sf/jwt/YourOrg-agentforce-observability.key

# Explicit key path (overrides all defaults)
python3 scripts/cli.py test-auth --org YourOrg \
    --consumer-key "..." \
    --key-path ~/.sf/jwt/custom-key.key
```

---

## File Locations

| File | Location | Description |
|------|----------|-------------|
| Private Key | `~/.sf/jwt/{org}-agentforce-observability.key` | RSA private key (chmod 600) |
| Certificate | `~/.sf/jwt/{org}-agentforce-observability.crt` | X.509 cert uploaded to Salesforce |
| Consumer Key | `$SF_CONSUMER_KEY` or `--consumer-key` | From ECA OAuth Settings |

---

## Required OAuth Scopes

| Scope | Purpose | Required |
|-------|---------|----------|
| `cdp_query_api` | Execute Data Cloud SQL queries | ✅ Yes |
| `refresh_token, offline_access` | Server-to-server access | ✅ Yes |
| `cdp_profile_api` | Access profile and DMO metadata | Optional |

---

## Troubleshooting

### invalid_grant Error

```
RuntimeError: Token exchange failed: invalid_grant
```

**Causes & Fixes:**

| Cause | Fix |
|-------|-----|
| Certificate mismatch | Re-upload `.crt` file to ECA |
| Expired certificate | Regenerate with `openssl` (see Step 1) |
| User not authorized | Add user to ECA policies (see Step 4) |
| Wrong login URL | Verify sandbox detection is working |

**Verify certificate expiry:**
```bash
openssl x509 -enddate -noout -in ~/.sf/jwt/YourOrg-agentforce-observability.crt
```

### 403 Forbidden

```
RuntimeError: Access denied: Ensure ECA has cdp_query_api scope
```

**Fix:** Add `cdp_query_api` scope to the ECA OAuth Settings.

### Key Not Found

```
FileNotFoundError: Private key not found at ~/.sf/jwt/myorg.key
```

**Causes:**
1. Key file doesn't exist → Generate with Step 1
2. Wrong org alias → Check `sf org list` for correct alias
3. Using old naming convention → Rename to `{org}-agentforce-observability.key`

### Permission Denied on Key

```
PermissionError: [Errno 13] Permission denied: '~/.sf/jwt/...'
```

**Fix:**
```bash
chmod 600 ~/.sf/jwt/*.key
```

---

## Sandbox vs Production

The skill automatically detects sandbox orgs:

1. Reads `isSandbox` from `sf org display --json`
2. Uses `https://test.salesforce.com` for token exchange (sandboxes)
3. Uses `https://login.salesforce.com` for production

No additional configuration needed.

---

## Security Best Practices

1. **Protect private keys**: Always `chmod 600 ~/.sf/jwt/*.key`
2. **Rotate certificates annually**: Regenerate before expiration
3. **Use separate ECAs**: One per org/environment for isolation
4. **Never commit keys**: Add `*.key` to `.gitignore`
5. **Audit access**: Review ECA usage in Setup → Security → Connected Apps OAuth Usage

---

## Environment Variables

For automation/CI, set these environment variables:

```bash
# Consumer key (org-specific takes priority)
export SF_YOURORG_CONSUMER_KEY="3MVG9..."
# or generic fallback
export SF_CONSUMER_KEY="3MVG9..."
```

The CLI checks in this order:
1. `--consumer-key` argument
2. `SF_{ORG_ALIAS}_CONSUMER_KEY` (uppercase, hyphens to underscores)
3. `SF_CONSUMER_KEY`

---

## See Also

- [sf-connected-apps skill](../../sf-connected-apps/SKILL.md) - General ECA patterns
- [CLI Reference](cli-reference.md) - All command options
- [Troubleshooting](../references/troubleshooting.md) - More error solutions
