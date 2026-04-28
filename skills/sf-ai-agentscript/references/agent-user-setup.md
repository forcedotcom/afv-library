<!-- Parent: sf-ai-agentscript/SKILL.md -->
# Agent User Setup & Permission Model

> Complete provisioning workflow for Einstein Agent Users and permission sets. Validated against representative Service Agent and Employee Agent scenarios.
>
> Preferred GA path: provision the Service Agent running user with `sf org create agent-user`. Use manual user creation only when you need custom user fields or the command is unavailable in the target org/tooling version.

**License Requirement:** PID_DigitalAgent (typically included with Agentforce licenses)

---

## Agent Type Decision Matrix

| Aspect | AgentforceServiceAgent | AgentforceEmployeeAgent |
|--------|------------------------|-------------------------|
| **Use Case** | Customer-facing, external users | Internal employees |
| **Runs As** | Dedicated Einstein Agent User | Logged-in user |
| **Einstein Agent User?** | Required | Not needed |
| **System PS (`AgentforceServiceAgentBase`, `AgentforceServiceAgentUser`, `EinsteinGPTPromptTemplateUser`)** | Required | Not needed |
| **Custom PS (`{AgentName}_Access`)** | Assigned to agent user | Assigned to employees |
| **`default_agent_user` in config** | Required | Omit entirely |
| **Respects Sharing Rules** | No (consistent permissions) | Yes (user's data access) |
| **Preferred setup path** | `sf org create agent-user` | Permission-set visibility via `<agentAccesses>` |

> **How to check agent type**: Look at the `agent_type` field in the `config:` block of your `.agent` file, or query: `sf data query --query "SELECT DeveloperName, Type FROM BotDefinition WHERE DeveloperName = 'AgentName'" -o TARGET_ORG --json`

---

## CLI Fast Track: Complete Workflow

**Preferred CLI-first workflow** (tested: ~8 minutes total):

```bash
# Step 1: Create the native Service Agent user
sf org create agent-user --target-org TARGET_ORG --json

# Optional: custom display name
sf org create agent-user \
  --first-name Service \
  --last-name Agent \
  --target-org TARGET_ORG --json

# Optional: custom username base
sf org create agent-user \
  --base-username service-agent@corp.com \
  --target-org TARGET_ORG --json

# Step 2: Verify the native system assignments
sf data query \
  --query "SELECT PermissionSet.Name FROM PermissionSetAssignment WHERE Assignee.Username = '<agent-username>' ORDER BY PermissionSet.Name" \
  -o TARGET_ORG --json

# Expected: AgentforceServiceAgentBase + AgentforceServiceAgentUser + EinsteinGPTPromptTemplateUser

# Step 3: Deploy custom Permission Set for agent-specific Apex / data access
sf project deploy start \
  --metadata PermissionSet:<AgentName>_Access \
  -o TARGET_ORG --json

# Step 4: Assign custom Permission Set
sf org assign permset \
  --name <AgentName>_Access \
  --on-behalf-of <agent-username> \
  -o TARGET_ORG --json

# If assignment fails, inspect the full JSON payload.
# Current CLI versions surface multiple assignment errors in --json output,
# which is much more useful than retrying blindly.

# Step 5: Verify all Permission Sets for the running user
sf data query \
  --query "SELECT PermissionSet.Name, PermissionSet.Label FROM PermissionSetAssignment WHERE Assignee.Username = '<agent-username>' ORDER BY PermissionSet.Name" \
  -o TARGET_ORG --json

# Expected: AgentforceServiceAgentBase + AgentforceServiceAgentUser + EinsteinGPTPromptTemplateUser + <AgentName>_Access

# Step 6: Set default_agent_user in the .agent config to the returned username

# Step 7: Validate and smoke-test before publish
sf agent validate authoring-bundle --api-name <AgentName> -o TARGET_ORG --json
SESSION_ID=$(sf agent preview start --authoring-bundle <AgentName> --simulate-actions -o TARGET_ORG --json | jq -r '.result.sessionId')
sf agent preview send --session-id "$SESSION_ID" --authoring-bundle <AgentName> --utterance "hello" -o TARGET_ORG --json
sf agent preview end --session-id "$SESSION_ID" --authoring-bundle <AgentName> -o TARGET_ORG --json

# Step 8: Publish and activate
sf agent publish authoring-bundle --api-name <AgentName> -o TARGET_ORG --json
sf agent activate --api-name <AgentName> --version <n> -o TARGET_ORG --json
```

**Critical Notes:**
- `sf org create agent-user` is the preferred GA path for Service Agent running-user setup.
- The native command auto-assigns the standard system profile and permission sets.
- Always test with preview BEFORE publishing to avoid version management overhead.
- Publishing does NOT activate — you must run `sf agent activate` separately.

---

## Manual fallback (only if native agent-user creation can't be used)

### Step 1: Create Einstein Agent User

Service agents need a dedicated service account with consistent permissions.

**Get Org ID first** (needed for username format):
```bash
sf org display -o TARGET_ORG --json | jq -r '.result.id'
```

**Query existing Einstein Agent Users** (skip creation if one exists):
```bash
sf data query --query "SELECT Id, Username, IsActive FROM User WHERE Profile.Name = 'Einstein Agent User' AND IsActive = true" -o TARGET_ORG --json
```

**Create the user** (if none exists):

1. Get the Einstein Agent User profile ID:
   ```bash
   sf data query --query "SELECT Id FROM Profile WHERE Name = 'Einstein Agent User'" -o TARGET_ORG --json
   ```

2. Create a user definition file (`config/einstein-agent-user.json`):
   ```json
   {
     "Username": "{agent_name}_agent@{orgId}.ext",
     "LastName": "{AgentName} Agent",
     "Email": "placeholder@example.com",
     "Alias": "agntuser",
     "ProfileId": "<profile-id-from-step-1>",
     "TimeZoneSidKey": "America/Los_Angeles",
     "LocaleSidKey": "en_US",
     "EmailEncodingKey": "UTF-8",
     "LanguageLocaleKey": "en_US",
     "UserPermissionsKnowledgeUser": true
   }
   ```

3. Create the user:

   **Option A: Scratch Org (Definition File)**
   ```bash
   sf org create user \
     --definition-file config/einstein-agent-user.json \
     -o TARGET_ORG
   ```

   **Option B: Production/Sandbox (Direct Record Creation)**
   ```bash
   # Get Profile ID first
   PROFILE_ID=$(sf data query \
     --query "SELECT Id FROM Profile WHERE Name = 'Einstein Agent User'" \
     -o TARGET_ORG --json | jq -r '.result.records[0].Id')

   # Create user directly
   sf data create record --sobject User --values \
     "Username='{agent_name}_agent@{orgId}.ext' LastName='{AgentName} Agent' Email='placeholder@example.com' Alias='agntuser' ProfileId='${PROFILE_ID}' TimeZoneSidKey='America/Los_Angeles' LocaleSidKey='en_US' EmailEncodingKey='UTF-8' LanguageLocaleKey='en_US'" \
     -o TARGET_ORG --json
   ```

   > **`sf org create user` only works in scratch orgs.** For production/sandbox, use `sf data create record`. Attempting `sf org create user` in a non-scratch org fails with an authorization error.

4. Verify creation:
   ```bash
   sf data query --query "SELECT Id, Username, IsActive FROM User WHERE Username = '{agent_name}_agent@{orgId}.ext'" -o TARGET_ORG --json
   ```

> **Username format**: `{agent_name}_agent@{orgId}.ext` (production) or `{agent_name}.{suffix}@{orgfarm}.salesforce.com` (dev/scratch). Always query the target org to confirm the exact format.

---

### Step 2: Assign Native System Permission Sets

**CRITICAL**: If you are not using `sf org create agent-user`, you must mirror the native system assignments BEFORE publishing the agent. Without them, publish or runtime execution can fail with generic errors.

**Assign these system permission sets:**
- `AgentforceServiceAgentBase`
- `AgentforceServiceAgentUser`
- `EinsteinGPTPromptTemplateUser`

**Via Setup UI:**
1. Setup > Permission Sets > assign `AgentforceServiceAgentBase`
2. Setup > Permission Sets > assign `AgentforceServiceAgentUser`
3. Setup > Permission Sets > assign `EinsteinGPTPromptTemplateUser`

**Via CLI:**
```bash
sf org assign permset --name AgentforceServiceAgentBase --on-behalf-of "{agent_name}_agent@{orgId}.ext" -o TARGET_ORG --json
sf org assign permset --name AgentforceServiceAgentUser --on-behalf-of "{agent_name}_agent@{orgId}.ext" -o TARGET_ORG --json
sf org assign permset --name EinsteinGPTPromptTemplateUser --on-behalf-of "{agent_name}_agent@{orgId}.ext" -o TARGET_ORG --json
```

**Verify assignments:**
```bash
sf data query --query "SELECT Id, PermissionSet.Name FROM PermissionSetAssignment WHERE Assignee.Username = '{agent_name}_agent@{orgId}.ext' AND PermissionSet.Name IN ('AgentforceServiceAgentBase', 'AgentforceServiceAgentUser', 'EinsteinGPTPromptTemplateUser')" -o TARGET_ORG --json
```

---

### Step 3: Create Custom Permission Set for Apex Classes

The custom PS grants the agent user permission to execute your Apex invocable actions.

**Naming convention**: `{AgentName}_Access` (e.g., `CustomerSupport_Access`)

**File**: `force-app/main/default/permissionsets/{AgentName}_Access.permissionset-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Grants access to {AgentName} Agent Apex classes</description>
    <hasActivationRequired>false</hasActivationRequired>
    <label>{AgentName} Access</label>

    <!-- Add one entry per Apex class the agent calls -->
    <classAccesses>
        <apexClass>YourApexClassName</apexClass>
        <enabled>true</enabled>
    </classAccesses>
    <!-- Repeat for ALL Apex classes referenced via apex:// in agent script -->
</PermissionSet>
```

**Key rule**: Include EVERY Apex class referenced via `apex://` in your agent script. Missing even one causes "invocable action does not exist" at runtime.

**Deploy the permission set:**
```bash
sf project deploy start --source-dir force-app/main/default/permissionsets/{AgentName}_Access.permissionset-meta.xml -o TARGET_ORG --json
```

---

### Step 4: Assign Custom Permission Set to Agent User

**Via CLI:**
```bash
sf org assign permset --name {AgentName}_Access --on-behalf-of "{agent_name}_agent@{orgId}.ext" -o TARGET_ORG --json
```

**Verify both permission sets are assigned:**
```bash
sf data query --query "SELECT PermissionSet.Name FROM PermissionSetAssignment WHERE Assignee.Username = '{agent_name}_agent@{orgId}.ext'" -o TARGET_ORG --json
```

Expected output should include all of these:
- `AgentforceServiceAgentBase` (system)
- `AgentforceServiceAgentUser` (system)
- `EinsteinGPTPromptTemplateUser` (system)
- `{AgentName}_Access` (custom)

---

### Step 5: Set `default_agent_user` in Agent Config

In your `.agent` file:
```yaml
config:
  developer_name: "AgentName"
  description: "Your agent description"
  agent_type: "AgentforceServiceAgent"
  default_agent_user: "{agent_name}_agent@{orgId}.ext"  # Service agents ONLY
```

> Official docs may describe `default_agent_user` as an API name or ID. In this skill, the standard operational path is to store the concrete username returned by `sf org create agent-user`, because that is the easiest value to verify in org queries and publish troubleshooting.

**Before publishing, verify the actual user object** — not just the username string:

```bash
sf data query --query "
SELECT Username, IsActive, UserType, Profile.Name
FROM User
WHERE Username = '{agent_name}_agent@{orgId}.ext'
LIMIT 1
" -o TARGET_ORG --json
```

A valid Service Agent user must satisfy all of these:
- user exists
- `IsActive = true`
- `UserType != AutomatedProcess`
- `Profile.Name = 'Einstein Agent User'`

This catches cases where `sf agent validate` passes but `sf agent publish` later fails because the configured user is missing, inactive, `AutomatedProcess`, or not on the **Einstein Agent User** profile.

**Recommended native sequence:**
1. `sf agent validate authoring-bundle --api-name <AgentName> -o TARGET_ORG --json`
2. Run the exact `sf data query` above for `default_agent_user`
3. Smoke-test with `sf agent preview start` / `send` / `end`
4. Publish with `sf agent publish authoring-bundle`
5. If publish fails after validate + preview pass, retry with `--skip-retrieve`

---

### Step 6: Deploy, Test, Publish & Activate

> **Validated workflow pattern**: Deploy as unpublished metadata, test with preview, then publish only when tests pass. This avoids version management overhead during iteration.

#### 6.1: Deploy Agent Bundle (Unpublished)

```bash
sf project deploy start \
  --source-dir force-app/main/default/aiAuthoringBundles/<AgentName> \
  -o TARGET_ORG --json
```

This deploys the agent as **unpublished metadata** — you can edit freely without version management.

#### 6.2: Test with Preview (Before Publishing)

```bash
SESSION_ID=$(sf agent preview start \
  --authoring-bundle <AgentName> \
  --use-live-actions \
  -o TARGET_ORG --json | jq -r '.result.sessionId')

sf agent preview send \
  --session-id "$SESSION_ID" \
  --authoring-bundle <AgentName> \
  --utterance "hello" \
  -o TARGET_ORG --json

sf agent preview end \
  --session-id "$SESSION_ID" \
  --authoring-bundle <AgentName> \
  -o TARGET_ORG --json
```

**What to test:**
1. All topics trigger correctly
2. All Apex actions execute without "Insufficient Privileges" errors
3. Agent responds with expected data
4. No compilation errors

If testing reveals problems, edit your agent script or Apex classes, redeploy, and test again — no publish required.

> See [preview-test-loop.md](preview-test-loop.md) for the complete smoke test workflow with `jq` trace analysis recipes.

#### 6.3: Publish Agent

**Only publish after all tests pass.**

```bash
# First try the standard publish path
sf agent publish authoring-bundle \
  --api-name <AgentName> \
  -o TARGET_ORG --json

# If that fails after validate/preview pass, retry without retrieve-back
sf agent publish authoring-bundle \
  --api-name <AgentName> \
  -o TARGET_ORG --skip-retrieve --json
```

> **Publishing does NOT activate.** The new BotVersion is created as `Inactive`. You must explicitly activate.
>
> **Why `--skip-retrieve` matters**: In org-backed testing, some publishes succeeded in the org but the CLI failed in the retrieve/deploy-back phase. `--skip-retrieve` isolates that tooling issue.

#### 6.4: Activate Agent

```bash
# Manual activation
sf agent activate \
  --api-name <AgentName> \
  -o TARGET_ORG

# CI / deterministic activation of a known BotVersion
sf agent activate \
  --api-name <AgentName> \
  --version <n> \
  -o TARGET_ORG --json
```

> `sf agent activate` now supports `--json`.
> If you use `--json` without `--version`, the CLI activates the latest agent version. Prefer `--version` for CI/CD and reproducible rollouts.

#### 6.5: Verify Activation

```bash
sf data query \
  --query "SELECT Id, DeveloperName, Status FROM BotVersion WHERE BotDefinition.DeveloperName = '<AgentName>' ORDER BY CreatedDate DESC LIMIT 1" \
  -o TARGET_ORG --json
```

**Expected:** `Status = 'Active'`

**After publish:** Any further changes require version management. Test thoroughly before publishing.

---

## Employee Agent Setup

Employee agents run as the logged-in user. The permission model is simpler.

### What You DO NOT Need

- No Einstein Agent User creation
- No native Service Agent system permission sets (`AgentforceServiceAgentBase`, `AgentforceServiceAgentUser`, `EinsteinGPTPromptTemplateUser`)
- No `default_agent_user` in agent config

### What You DO Need

Custom permission set(s) assigned to **employees** who will use the agent.

### Step 1: Create Custom Permission Set

Same XML template as Step 3 above. Include `<classAccesses>` for all Apex classes the agent calls.

### Step 2: Assign to Employees

Assign the custom PS to employees (not to a service account):

```bash
sf org assign permset --name {AgentName}_Access --on-behalf-of "employee@company.com" -o TARGET_ORG --json
```

Or use Permission Set Groups for role-based access.

### Step 3: Configure Agent Script (No `default_agent_user`)

```yaml
config:
  developer_name: "Employee_Agent"
  description: "Internal employee assistant"
  agent_type: "AgentforceEmployeeAgent"
  # NO default_agent_user — agent runs as logged-in user
```

### Step 4: Publish

```bash
sf agent publish authoring-bundle --api-name Employee_Agent -o TARGET_ORG --json
```

### Common Mistakes with Employee Agents

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Including `default_agent_user` | HTTP 500 on publish | Remove the field entirely |
| Omitting `agent_type` | Defaults to Service Agent, then fails if no agent user | Set `agent_type: "AgentforceEmployeeAgent"` explicitly |
| Including Messaging-linked variables | Unnecessary bloat, may cause errors if Messaging not configured | Remove `EndUserId`, `RoutableId`, `ContactId` linked vars |
| Including `connection messaging:` block | Service Agent only -- causes errors for Employee Agent | Remove the entire connection block |
| Including `language:` block | Not required for Employee agents | Optional -- remove to keep minimal |

---

## Auto-Generated Permission Set Warning

Salesforce auto-generates `NextGen_{AgentName}_Permissions` when an agent is published. **Do NOT rely on this PS.** It is often incomplete.

**Representative example:**
- Agent script referenced 4 Apex classes: `IdentityVerificationService`, `RiskScoringService`, `OrderLookupService`, `ShipmentTrackingService`
- Auto-generated `NextGen_Support_Agent_Permissions` only included 3 classes (missing `ShipmentTrackingService`)
- Runtime error: "invocable action track_delivery does not exist"
- Fix: Created custom `Support_Agent_Access` with all 4 classes — no errors

**Best practice**: Always create your own custom `{AgentName}_Access` PS with explicit `<classAccesses>` for every Apex class. Ignore the auto-generated PS.

---

## End-to-End Verification Checklist

Run this combined query to verify all setup steps for a Service Agent:

```bash
# 1. Einstein Agent User exists and is active
sf data query --query "SELECT Id, Username, IsActive, Profile.Name FROM User WHERE Username = '{agent_name}_agent@{orgId}.ext'" -o TARGET_ORG --json

# 2. Native system PS assigned
sf data query --query "SELECT PermissionSet.Name FROM PermissionSetAssignment WHERE Assignee.Username = '{agent_name}_agent@{orgId}.ext' AND PermissionSet.Name IN ('AgentforceServiceAgentBase', 'AgentforceServiceAgentUser', 'EinsteinGPTPromptTemplateUser')" -o TARGET_ORG --json

# 3. Custom PS assigned
sf data query --query "SELECT PermissionSet.Name FROM PermissionSetAssignment WHERE Assignee.Username = '{agent_name}_agent@{orgId}.ext' AND PermissionSet.Name = '{AgentName}_Access'" -o TARGET_ORG --json

# 4. All permission sets for user (combined view)
sf data query --query "SELECT PermissionSet.Name, PermissionSet.Label FROM PermissionSetAssignment WHERE Assignee.Username = '{agent_name}_agent@{orgId}.ext'" -o TARGET_ORG --json

# 5. Agent config has default_agent_user
# Check your .agent file's config: block

# 6. Agent publishes successfully
sf agent publish authoring-bundle --api-name AgentName -o TARGET_ORG --json
```

**Checklist:**
- [ ] Einstein Agent User created and active (`IsActive = true`)
- [ ] Profile is "Einstein Agent User" (or "Minimum Access - Salesforce")
- [ ] `AgentforceServiceAgentBase`, `AgentforceServiceAgentUser`, and `EinsteinGPTPromptTemplateUser` system PS assigned
- [ ] Custom `{AgentName}_Access` PS deployed with ALL Apex classes
- [ ] Custom PS assigned to the agent user
- [ ] `default_agent_user` set in `.agent` config block
- [ ] Agent tested with preview before publishing
- [ ] Agent publishes without error
- [ ] Agent activated (publish does NOT auto-activate)

---

## Common Pitfalls (Validated)

### 1. "Internal Error" on First Publish
- **Cause:** Publishing before the native Service Agent system assignments are in place
- **Prevention:** Prefer `sf org create agent-user`, or manually assign all Step 2 system permission sets before publishing (Step 6.3)
- **Result:** First-time publish success (no retries needed)

### 2. "Insufficient Privileges" on Apex Actions
- **Cause:** Missing `<classAccesses>` in custom permission set
- **Prevention:** Custom PS template includes all Apex classes (Step 3)
- **Result:** All actions execute without permission errors

### 3. Testing After Publishing
- **Cause:** Publishing before testing, then needing version management for fixes
- **Prevention:** Deploy → Test → Publish workflow (Step 6.1-6.3)
- **Result:** No version management overhead during development

### 4. Wrong User Creation Command
- **Cause:** Using `sf org create user` in non-scratch orgs
- **Prevention:** Step 1 provides correct commands for each org type (Option A vs B)
- **Result:** User created successfully without authorization errors

### 5. Auto-Generated Permission Set Gaps
- **Cause:** Relying on `NextGen_{AgentName}_Permissions` (often incomplete)
- **Prevention:** Custom PS with explicit Apex access (Step 3)
- **Result:** All Apex classes accessible from the start

### 6. Forgot to Activate After Publish
- **Cause:** Assuming publish automatically activates
- **Prevention:** Step 6 splits publish and activate into separate steps with verification
- **Result:** Agent is both published AND activated

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| "Internal Error" on publish | One or more native Service Agent system permission sets missing | Prefer `sf org create agent-user`, or assign Step 2 system PS manually, wait 2-3 min, retry publish |
| "Insufficient Privileges" at runtime | Custom PS missing or incomplete `<classAccesses>` | Verify custom PS includes ALL Apex classes, redeploy + reassign |
| "invocable action does not exist" | Apex class not in custom PS (auto-generated PS incomplete) | Create custom `{AgentName}_Access` with all `<classAccesses>` (Step 3) |
| "Invalid default_agent_user" | Username typo or user not active | Query Einstein Agent Users, verify exact username + `IsActive = true` |
| Agent runs but returns wrong data | Employee agent using wrong user context | Verify `agent_type` — Service agents use dedicated user, Employee agents use logged-in user |
| `sf org create user` fails | Used in production/sandbox org | Use `sf data create record` instead (Step 1, Option B) |
| Native system behavior differs from local assumptions | Running user was created manually instead of with the native command | Re-check with `sf org create agent-user --help` and verify `AgentforceServiceAgentBase`, `AgentforceServiceAgentUser`, and `EinsteinGPTPromptTemplateUser` assignments |

---

## Permission Set XML Template (Complete Example)

**CustomerSupport agent** (5 Apex classes):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Grants access to Automotive Support Agent Apex classes</description>
    <hasActivationRequired>false</hasActivationRequired>
    <label>Automotive Support Access</label>

    <classAccesses>
        <apexClass>VehicleLookupService</apexClass>
        <enabled>true</enabled>
    </classAccesses>
    <classAccesses>
        <apexClass>ErrorCodeDiagnosticsService</apexClass>
        <enabled>true</enabled>
    </classAccesses>
    <classAccesses>
        <apexClass>CheckEngineDiagnosticsService</apexClass>
        <enabled>true</enabled>
    </classAccesses>
    <classAccesses>
        <apexClass>BehaviorAnalysisService</apexClass>
        <enabled>true</enabled>
    </classAccesses>
    <classAccesses>
        <apexClass>ServiceSchedulerService</apexClass>
        <enabled>true</enabled>
    </classAccesses>
</PermissionSet>
```

---

*Validated against representative Service Agent and Employee Agent scenarios. Last validated: 2026-03-07.*
