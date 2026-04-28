<!-- Parent: sf-ai-agentscript/SKILL.md -->
# Agent Script CLI Quick Reference

> Pro-Code Lifecycle: Git, CI/CD, and CLI for Agent Development

---

## The sf agent Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `sf project retrieve start` | Pull agent from org | `sf project retrieve start --metadata Agent:MyAgent --target-org sandbox` |
| `sf org create agent-user` | Create native Service Agent running user | `sf org create agent-user --target-org TARGET_ORG --json` |
| `sf agent validate authoring-bundle` | Check syntax before deploy | `sf agent validate authoring-bundle --api-name MyAgent -o TARGET_ORG` |
| `sf agent publish authoring-bundle` | Publish agent to org | `sf agent publish authoring-bundle --api-name MyAgent -o TARGET_ORG --json` |
| `sf agent test run` | Run batch tests | `sf agent test run --api-name MyTestDef --wait 10 -o TARGET_ORG --json` |
| `sf agent create` | Create non-Agent Script agent from spec file (legacy / not default for this skill) | `sf agent create --name "My Agent" --api-name MyAgent --spec agent-spec.yaml -o TARGET_ORG --json` |
| `sf agent generate agent-spec` | Generate agent specification | `sf agent generate agent-spec --type customer --role "Service Rep" --output-file agent-spec.yaml` |
| `sf agent generate authoring-bundle` | Scaffold authoring bundle | `sf agent generate authoring-bundle --no-spec --name "My Agent" -o TARGET_ORG --json` |
| `sf agent activate` | Activate agent (make live) | `sf agent activate --api-name MyAgent --version <n> -o TARGET_ORG --json` |
| `sf agent deactivate` | Deactivate agent (take offline) | `sf agent deactivate --api-name MyAgent -o TARGET_ORG --json` |
| `sf agent preview start` | Start programmatic preview session | `sf agent preview start --authoring-bundle MyAgent --simulate-actions -o TARGET_ORG --json` (or `--api-name MyAgent`) |
| `sf agent preview send` | Send utterance to preview session | `sf agent preview send --session-id <id> --authoring-bundle MyAgent --utterance "Hello" -o TARGET_ORG --json` |
| `sf agent preview end` | End preview session | `sf agent preview end --session-id <id> --authoring-bundle MyAgent -o TARGET_ORG --json` |
| `sf org open agent` | Open Agent Builder in browser | `sf org open agent --api-name MyAgent -o TARGET_ORG` |
| `sf org open authoring-bundle` | Open Agentforce Studio list view | `sf org open authoring-bundle -o TARGET_ORG` |

> ⚠️ **CRITICAL**: Use `sf agent publish authoring-bundle` for Agent Script deployment, NOT `sf project deploy start`. The metadata API deploy will fail with "Required fields are missing: [BundleType]".
>
> Default workflow for this skill: edit or generate the `.agent` bundle directly. Use `sf agent generate agent-spec` only when the user explicitly wants LLM-assisted topic ideation.
>
> ℹ️ **Managed packaging note:** `sf agent generate template` targets Bot / BotVersion metadata and is **not** a packaging path for Agent Script `.agent` bundles. See [known-issues.md](known-issues.md) for the current Agent Script packaging limitation.

---

## Create Service Agent User (GA)

```bash
sf org create agent-user --target-org TARGET_ORG --json
sf org create agent-user --first-name Service --last-name Agent --target-org TARGET_ORG --json
sf org create agent-user --base-username service-agent@corp.com --target-org TARGET_ORG --json
```

The native command assigns the standard Service Agent profile and system permission sets automatically. Use the returned username as the `default_agent_user` value.

## Authoring Bundle Structure

> ⚠️ **CRITICAL NAMING CONVENTION**: File must be named `AgentName.bundle-meta.xml`, NOT `AgentName.aiAuthoringBundle-meta.xml`. The metadata API expects `.bundle-meta.xml` suffix.

```
force-app/main/default/aiAuthoringBundles/
└── MyAgent/
    ├── MyAgent.agent           # Your Agent Script (REQUIRED)
    └── MyAgent.bundle-meta.xml # Metadata XML (REQUIRED)
```

### AgentName.bundle-meta.xml Content

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AiAuthoringBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <bundleType>AGENT</bundleType>
</AiAuthoringBundle>
```

> ⚠️ **COMMON ERROR**: Using `<BundleType>` (PascalCase) instead of `<bundleType>` (camelCase) will NOT cause errors, but the field name in the XML element is `bundleType` (lowercase b).

### Bundle Naming Rules

| Component | Convention | Example |
|-----------|------------|---------|
| Folder name | PascalCase or snake_case | `MyAgent/` or `My_Agent/` |
| Agent script | Same as folder + `.agent` | `MyAgent.agent` |
| Metadata XML | Same as folder + `.bundle-meta.xml` | `MyAgent.bundle-meta.xml` |

### Deployment Command (NOT sf project deploy!)

```bash
# ✅ CORRECT: Use sf agent publish authoring-bundle
sf agent publish authoring-bundle --api-name MyAgent -o TARGET_ORG

# ❌ WRONG: Do NOT use sf project deploy start
# This will fail with "Required fields are missing: [BundleType]"
```

---

## Pro-Code Workflow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 1 Retrieve  │ →  │ 2 Edit      │ →  │ 3 Validate  │ →  │ 4 Deploy    │
│ Pull agent  │    │ CLI/editor  │    │ Check syntax│    │ Push to prod│
│ from org    │    │ + Claude    │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### Step 1: Retrieve

```bash
# Retrieve from sandbox
sf project retrieve start --metadata Agent:MyAgent --target-org sandbox --json
```

> **⚠️ Flow Version Mismatch Warning**: `sf project retrieve start --metadata Flow:FlowName` retrieves the **latest** Flow version, which may be Draft or Obsolete — NOT necessarily the active version. The Agent Script publisher validates action I/O against the **active** Flow version's inputs/outputs. If the latest version has different I/O than the active version (e.g., a renamed input parameter), your action definition will compile locally but fail on publish.
>
> **How to verify the active Flow version's inputs:**
> ```bash
> # 1. Find the active version ID
> sf data query --query "SELECT ActiveVersionId, LatestVersionId FROM FlowDefinitionView WHERE ApiName = 'My_Flow_Name' LIMIT 1" -o TARGET_ORG --json
>
> # 2. If ActiveVersionId != LatestVersionId, inspect the active version:
> sf data query --query "SELECT Id, VersionNumber, Status FROM FlowVersionView WHERE FlowDefinitionViewId = 'DEFINITION_ID' AND Status = 'Active'" -o TARGET_ORG --json
> ```
> Always define your action `inputs:` / `outputs:` to match the **active** Flow version, not the latest retrieved metadata.

### Step 2: Edit

```bash
# Edit the agent script
vim force-app/main/default/aiAuthoringBundles/MyAgent/MyAgent.agent
```

### Step 3: Validate

```bash
# Validate authoring bundle syntax
sf agent validate authoring-bundle --api-name MyAgent -o TARGET_ORG --json
```

### Step 4: Publish

```bash
# Publish agent to org (4-step process: Validate → Publish → Retrieve → Deploy)
sf agent publish authoring-bundle --api-name MyAgent -o TARGET_ORG --json

# If publish fails AFTER validate/preview pass, retry without retrieve-back:
sf agent publish authoring-bundle --api-name MyAgent -o TARGET_ORG --skip-retrieve --json

# Expected output:
# ✔ Validate Bundle    ~1-2s
# ✔ Publish Agent      ~8-10s
# ✔ Retrieve Metadata  ~5-7s
# ✔ Deploy Metadata    ~4-6s
```

> ⚠️ Do NOT use `sf project deploy start` - it will fail with "Required fields are missing: [BundleType]"
>
> ⚠️ **Real-world failure split**:
> - If plain publish fails but `--skip-retrieve` succeeds, the problem is usually the CLI retrieve/deploy-back phase, not Agent Script compilation.
> - If publish still fails even with `--skip-retrieve`, suspect `default_agent_user` first.

### Step 5: Activate

> ⚠️ **Publishing does NOT activate.** The new BotVersion is created as `Inactive`. Tests, preview, and end users continue hitting the previously active version until you explicitly activate.

```bash
# Manual activation (choose interactively if you omit --version)
sf agent activate --api-name MyAgent -o TARGET_ORG

# CI / deterministic activation of a known BotVersion
sf agent activate --api-name MyAgent --version <n> -o TARGET_ORG --json

# Verify activation (optional)
sf data query --query "SELECT DeveloperName, VersionNumber, Status FROM BotVersion WHERE BotDefinition.DeveloperName = 'MyAgent' AND Status = 'Active' LIMIT 1" -o TARGET_ORG --json
```

> ℹ️ `sf agent activate` and `sf agent deactivate` now support `--json`.
> If you use `--json` without `--version`, the CLI activates the latest agent version. Prefer `--version` for CI/CD and reproducible rollouts.

---

## Testing Commands

```bash
# Run agent tests (--api-name refers to an AiEvaluationDefinition, not the agent)
sf agent test run --api-name MyTestDef --wait 10 -o TARGET_ORG --json
```

---

## Validation Commands

```bash
# Validate authoring bundle syntax
sf agent validate authoring-bundle --api-name MyAgent -o TARGET_ORG --json

# Run tests against test definition
sf agent test run --api-name MyTestDef --wait 10 -o TARGET_ORG --json
```

### Common Validation / Publish Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Internal Error, try again later` during **publish** | Often invalid `default_agent_user` for Service Agent | Verify the user exists, is active, is NOT `AutomatedProcess`, and has Profile.Name = `Einstein Agent User` |
| Plain publish fails, `--skip-retrieve` succeeds | CLI retrieve/deploy-back phase failed after successful publish | Re-run `sf agent publish authoring-bundle ... --skip-retrieve --json` |
| `SyntaxError: You cannot mix spaces and tabs` | Mixed indentation | Use consistent spacing |
| `Transition to undefined topic "@topic.X"` | Typo in topic name | Check spelling |
| `Variables cannot be both mutable AND linked` | Conflicting modifiers | Choose one modifier |

---

## Einstein Agent User Setup (Service Agents Only)

> This section applies to `AgentforceServiceAgent` only. `AgentforceEmployeeAgent` does NOT need an Einstein Agent User — it runs as the logged-in user. See [agent-user-setup.md](agent-user-setup.md) for the full provisioning workflow, CLI Fast Track, and Deploy → Test → Publish pattern.

### Query Existing Users

```bash
sf data query --query "SELECT Id, Username, IsActive FROM User WHERE Profile.Name = 'Einstein Agent User' AND IsActive = true" -o TARGET_ORG --json
```

### Native Pre-Publish Check (Recommended)

```bash
sf data query --query "
SELECT Username, IsActive, UserType, Profile.Name
FROM User
WHERE Username = 'prontorefund_agent@00Dxxxx.ext'
LIMIT 1
" -o TARGET_ORG --json
```

Use this native CLI check before publish for Service Agents. A passing result must show:
- a matching user record
- `IsActive = true`
- `UserType != AutomatedProcess`
- `Profile.Name = 'Einstein Agent User'`

This covers the most common real-world publish failure: a `default_agent_user` value that passes `sf agent validate` but fails `sf agent publish` because the user is missing, inactive, `AutomatedProcess`, or not on the **Einstein Agent User** profile.

### Native Pre-Publish Workflow

Use this exact sequence for production-safe Service Agent publishes:

```bash
# 1. Static validation
sf agent validate authoring-bundle --api-name MyAgent -o TARGET_ORG --json

# 2. Verify the exact default_agent_user from the .agent config
sf data query --query "
SELECT Username, IsActive, UserType, Profile.Name
FROM User
WHERE Username = 'myagent_agent@00Dxxxx.ext'
LIMIT 1
" -o TARGET_ORG --json

# 3. Smoke-test the authoring bundle (authoring bundles now require an explicit mode)
SESSION_ID=$(sf agent preview start --authoring-bundle MyAgent --simulate-actions -o TARGET_ORG --json | jq -r '.result.sessionId')
sf agent preview send --session-id "$SESSION_ID" --authoring-bundle MyAgent --utterance "hello" -o TARGET_ORG --json
sf agent preview end --session-id "$SESSION_ID" --authoring-bundle MyAgent -o TARGET_ORG --json

# 4. Publish
sf agent publish authoring-bundle --api-name MyAgent -o TARGET_ORG --json

# 5. If plain publish fails after validate + preview pass, retry:
sf agent publish authoring-bundle --api-name MyAgent -o TARGET_ORG --skip-retrieve --json
```

Interpretation:
- Plain publish fails, `--skip-retrieve` works → retrieve/deploy-back phase issue in the CLI path
- Both publish commands fail → inspect `default_agent_user`, action I/O, and other server-side publish constraints

### Create Einstein Agent User

**Option A: Scratch Org** (definition file):
```bash
sf org create user --definition-file config/einstein-agent-user.json -o TARGET_ORG
```

**Option B: Production/Sandbox** (direct record creation):
```bash
PROFILE_ID=$(sf data query \
  --query "SELECT Id FROM Profile WHERE Name = 'Einstein Agent User'" \
  -o TARGET_ORG --json | jq -r '.result.records[0].Id')

sf data create record --sobject User --values \
  "Username='{agent_name}_agent@{orgId}.ext' LastName='{AgentName} Agent' Email='placeholder@example.com' Alias='agntuser' ProfileId='${PROFILE_ID}' TimeZoneSidKey='America/Los_Angeles' LocaleSidKey='en_US' EmailEncodingKey='UTF-8' LanguageLocaleKey='en_US'" \
  -o TARGET_ORG --json
```

> **`sf org create user` only works in scratch orgs.** For production/sandbox, use `sf data create record`.

### Username Format

```
{agent_name}_agent@<org-id>.ext
```

Example: `automotive_agent@00dkd00000g7lv7.ext`

### Get Org ID

```bash
sf org display -o TARGET_ORG --json | jq -r '.result.id'
```

### Verify Permission Set Assignments

Both the system PS and custom PS must be assigned to the Einstein Agent User:

```bash
# Check system PS
sf data query --query "SELECT PermissionSet.Name FROM PermissionSetAssignment WHERE Assignee.Username = '<agent-username>' AND PermissionSet.Name = 'AgentforceServiceAgentUser'" -o TARGET_ORG --json

# Check custom PS
sf data query --query "SELECT PermissionSet.Name FROM PermissionSetAssignment WHERE Assignee.Username = '<agent-username>' AND PermissionSet.Name = '{AgentName}_Access'" -o TARGET_ORG --json

# All assigned PSs
sf data query --query "SELECT PermissionSet.Name FROM PermissionSetAssignment WHERE Assignee.Username = '<agent-username>'" -o TARGET_ORG --json
```

### Recommended Workflow: Deploy → Test → Publish

After user setup and permissions are configured, follow this order to avoid version management overhead:

1. **Deploy** agent bundle as unpublished metadata
2. **Test** with `sf agent preview start` — verify topics and actions
3. **Publish** only after tests pass — `sf agent publish authoring-bundle`
4. **Activate** separately — `sf agent activate` (publish does NOT auto-activate)

> See [agent-user-setup.md](agent-user-setup.md) Step 6 for the full workflow with CLI commands.

---

## CI/CD Integration

### GitHub Actions Example — 4-Step Deployment Pipeline

```yaml
name: Agent Deploy & Test
on: [push, pull_request]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      # Step 1: Deploy supporting metadata (Flows, Apex, Objects)
      - name: Deploy Supporting Metadata
        run: sf project deploy start --source-dir force-app -o TARGET_ORG --json

      # Step 2: Validate agent bundle syntax
      - name: Validate Agent Bundle
        run: sf agent validate authoring-bundle --api-name My_Agent -o TARGET_ORG --json

      # Step 3: Publish agent (4-step atomic: validate -> publish -> retrieve -> deploy)
      - name: Publish Agent
        run: sf agent publish authoring-bundle --api-name My_Agent -o TARGET_ORG --json

      # Step 4: Activate the published version
      - name: Activate Agent
        run: sf agent activate --api-name My_Agent --version "$AGENT_VERSION" -o TARGET_ORG --json

      # Optional: Run agent tests after activation
      - name: Run Agent Tests
        run: sf agent test run --api-name MyTestDef --wait 10 -o TARGET_ORG --json
```

Set `AGENT_VERSION` in the workflow environment to the BotVersion number you intend to activate.

### SF Agent CLI Error Codes (current high-signal set)

Use `sf <command> --help` for the full command-specific list. The most relevant current codes are:

| Command | Codes to expect | What they mean |
|---------|-----------------|----------------|
| `sf agent validate authoring-bundle` | `0, 1, 2, 3` | `Succeeded`, `Failed` (compilation errors), `NotFound`, `ServerError` |
| `sf agent publish authoring-bundle` | aligns with validate for compilation failures | publish now uses the same compilation-related codes as validate when Agent Script compilation fails |
| `sf agent preview start` | `0, 1, 2, 3, 4` | `Succeeded`, `Failed`, `NotFound`, `ServerError`, `PreviewStartFailed` |
| `sf agent preview send` | `0, 2, 4, 5` | `Succeeded`, `NotFound`, `PreviewSendFailed`, `SessionAmbiguous` |
| `sf agent preview end` | `0, 2, 4, 5` | `Succeeded`, `NotFound`, `PreviewEndFailed`, `SessionAmbiguous` |

**CI/CD guidance:**
- block immediately on `1+` for validate / publish
- if preview returns `SessionAmbiguous (5)`, run `sf agent preview sessions --json`, pick the right session, and retry with `--session-id`

---

## Deployment Pipeline

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Sandbox    │ ───▶ │   Staging   │ ───▶ │ Production  │
│   v1.3.0    │      │  Validate   │      │   v1.3.0    │
└─────────────┘      └─────────────┘      └─────────────┘
```

### 6-Step Pipeline

1. **Retrieve from Sandbox** - Pull latest agent bundle
2. **Validate Syntax** - Check Agent Script for errors
3. **Run Tests** - Execute automated agent tests
4. **Code Review** - Automated best practices checks
5. **Deploy to Production** - Push validated bundle
6. **Verify Deployment** - Confirm agent is active

---

## Agent Creation Commands

### Create Agent from Spec File

```bash
# Generate an agent specification YAML first
sf agent generate agent-spec \
  --type customer \
  --role "Customer Service Representative" \
  --company-name "Acme Corp" \
  --company-description "E-commerce platform" \
  --output-file agent-spec.yaml

# Create the agent from the spec
sf agent create \
  --name "My Service Agent" \
  --api-name MyServiceAgent \
  --spec agent-spec.yaml \
  -o TARGET_ORG --json
```

### Managed Packaging Status

`sf agent generate template` is **not** an Agent Script packaging workflow.
The current CLI command targets Bot / BotVersion metadata, requires a `.bot-meta.xml` file plus `--source-org`, and doesn't package `.agent` authoring bundles.

For Agent Script agents today:
- use source-driven deployment (`sf agent publish authoring-bundle`) for org rollout
- treat managed-package templating as unsupported for `.agent` bundles
- see [known-issues.md](known-issues.md) for the current packaging limitation

---

## Programmatic Preview (Non-Interactive)

> ⛔ **NEVER run bare `sf agent preview`** — it launches an interactive terminal requiring keyboard input. Claude Code CANNOT use it. **ALWAYS use subcommands**: `start`, `send`, `end` with `--json`.

```bash
# 1. Start a published-agent preview session
# Published agents always use live actions.
SESSION_ID=$(sf agent preview start --api-name MyAgent -o TARGET_ORG --json | jq -r '.result.sessionId')

# 2. Send utterances programmatically
sf agent preview send --session-id $SESSION_ID --api-name MyAgent --utterance "I need a refund" -o TARGET_ORG --json

# 3. Send follow-up messages
sf agent preview send --session-id $SESSION_ID --api-name MyAgent --utterance "Order #12345" -o TARGET_ORG --json

# 4. End the session
sf agent preview end --session-id $SESSION_ID --api-name MyAgent -o TARGET_ORG --json

# List cached preview sessions (no target-org flag)
sf agent preview sessions --json
```

### Preview Modes

| Target | Required flags | Behavior |
|--------|----------------|----------|
| Published agent (`--api-name`) | none | programmatic preview always uses live actions |
| Authoring bundle (`--authoring-bundle`) | exactly one of `--simulate-actions` or `--use-live-actions` | choose simulated vs real-action execution explicitly |

Additional preview flags:

| Flag | Purpose |
|------|---------|
| `--simulate-actions` | Use AI to simulate action execution. Required with `--authoring-bundle` when you want simulated mode. |
| `--use-live-actions` | Execute real Apex/Flows/Prompt Templates. Required with `--authoring-bundle` when you want live mode. |
| `--authoring-bundle` | Preview the local authoring bundle instead of a published Bot. |
| `--api-name` | Preview an activated published agent. |

```bash
# Authoring-bundle preview in simulated mode
SESSION_ID=$(sf agent preview start --authoring-bundle MyBundle --simulate-actions -o TARGET_ORG --json | jq -r '.result.sessionId')
sf agent preview send --session-id $SESSION_ID --authoring-bundle MyBundle --utterance "What can you help me with?" -o TARGET_ORG --json
sf agent preview end --session-id $SESSION_ID --authoring-bundle MyBundle -o TARGET_ORG --json

# Authoring-bundle preview in live mode
SESSION_ID=$(sf agent preview start --authoring-bundle MyBundle --use-live-actions -o TARGET_ORG --json | jq -r '.result.sessionId')
```

If `preview send` or `preview end` returns `SessionAmbiguous (5)`, run `sf agent preview sessions --json` and retry with the explicit `--session-id`.

---

## Activate / Deactivate Agent

After publishing, activate the agent to make it live. Deactivate before re-publishing updates.

```bash
# Activate agent manually (interactive version selection if omitted)
sf agent activate --api-name MyAgent -o TARGET_ORG

# Activate a specific BotVersion in CI / automation
sf agent activate --api-name MyAgent --version <n> -o TARGET_ORG --json

# Deactivate agent (takes it offline — required before re-publishing)
sf agent deactivate --api-name MyAgent -o TARGET_ORG --json
```

### Deterministic activation in CI

- `--version <n>` maps to the `vN` suffix of the agent's `BotVersion` metadata.
- If you omit `--version`, the CLI prompts you to choose a version interactively.
- If you use `--json` without `--version`, the CLI activates the latest agent version.
- For reproducible pipelines, pass the exact `--version` you intend to activate.

**Verify activation status**:
```bash
sf data query --query "SELECT DeveloperName, VersionNumber, Status FROM BotVersion WHERE BotDefinition.DeveloperName = 'MyAgent' AND Status = 'Active' LIMIT 1" -o TARGET_ORG --json
```

**Full update lifecycle**: Deactivate → Re-publish → Re-activate

```bash
# Update an already-active agent:
sf agent deactivate --api-name MyAgent -o TARGET_ORG --json
sf agent publish authoring-bundle --api-name MyAgent -o TARGET_ORG --json
sf agent activate --api-name MyAgent --version <n> -o TARGET_ORG --json
```

---

## Generate Authoring Bundle (`--no-spec`)

The `--no-spec` flag skips requiring an agent spec YAML file and uses default Agent Script boilerplate:

> **v2.126.4 change**: When `--json` is specified, `--name` is now **required**. The CLI no longer prompts interactively for missing flags in JSON mode — it errors instead. Always include `--name` when scripting with `--json`.

```bash
# Scaffold a new authoring bundle without an agent spec
sf agent generate authoring-bundle --no-spec --name "My Agent" -o TARGET_ORG --json

# With a spec file (standard flow)
sf agent generate authoring-bundle --spec agent-spec.yaml --name "My Agent" -o TARGET_ORG --json

# Overwrite existing bundle without confirmation (v2.125.1+)
sf agent generate authoring-bundle --spec agent-spec.yaml --name "My Agent" --force-overwrite -o TARGET_ORG --json
```

---

## Generate Agent Spec — Full Flag Reference

> Optional path only. In this repository, direct `.agent` authoring is the default path; spec generation is a bootstrap aid, not the primary authoring workflow.

| Flag | Values / Type | Description |
|------|---------------|-------------|
| `--type` | `customer \| internal` | **Required.** Agent audience type |
| `--role` | string | **Required.** Agent's role description |
| `--company-name` | string | Company name for context |
| `--company-description` | string | Company description for context |
| `--company-website` | URL | Company website URL for grounding |
| `--tone` | `formal \| casual \| neutral` | Conversational style |
| `--enrich-logs` | `true \| false` | Add agent conversation data to event logs |
| `--max-topics` | number | Maximum topics to generate (default: 5) |
| `--agent-user` | username | Einstein Agent User to assign |
| `--output-file` | path | Output path (default: `specs/agentSpec.yaml`) |
| `--full-interview` | *(flag)* | Prompt for both required AND optional flags |
| `--spec` | file path | Use existing spec for iterative refinement |
| `--prompt-template` | API name | Custom prompt template reference |
| `--grounding-context` | string | Context value for custom prompt template |
| `--force-overwrite` | *(flag)* | Overwrite existing spec without confirmation |

```bash
# Full example with optional flags
sf agent generate agent-spec \
  --type customer \
  --role "Customer Service Representative" \
  --company-name "Acme Corp" \
  --company-description "E-commerce platform" \
  --company-website "https://acme.example.com" \
  --tone formal \
  --enrich-logs true \
  --max-topics 8 \
  --agent-user "agent_user@00dxx000001234.ext" \
  --output-file specs/my-agent-spec.yaml

# Iterative refinement — feed existing spec back in
sf agent generate agent-spec \
  --spec specs/my-agent-spec.yaml \
  --max-topics 3 \
  --tone casual \
  --force-overwrite
```

---

## Browser Quick-Open Commands

```bash
# Open specific agent in Agentforce Builder
sf org open agent --api-name MyAgent -o TARGET_ORG

# Open Agentforce Studio (list view of all authoring bundles)
sf org open authoring-bundle -o TARGET_ORG

# Get URL only (for CI/CD logs or scripts)
sf org open agent --api-name MyAgent -o TARGET_ORG --url-only
```

---

<a id="three-phase-lifecycle"></a>

## Three-Phase Lifecycle

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   ✏️ Draft   │  →   │  🔒 Commit  │  →   │  ✅ Activate │
│   EDITABLE  │      │  READ-ONLY  │      │    LIVE     │
└─────────────┘      └─────────────┘      └─────────────┘
```

| Phase | Capabilities |
|-------|--------------|
| **Draft** | Edit freely, preview, run batch tests |
| **Commit** | Script frozen, version assigned, bundle compiled |
| **Activate** | Assign to Connections, go live, monitor |

> **Key Insight**: Commit doesn't deploy - it freezes. Activate makes it live.

---

## API Versioning Behavior

Agent versions share the same `agentId` (the `BotDefinition` / `Agent` record) but have **distinct version IDs**.

| Concept | Description |
|---------|-------------|
| `agentId` / `BotDefinition.Id` | Unique per agent — does NOT change between versions |
| `versionId` / `BotVersion.Id` | Unique per version — changes with each commit |
| Default API behavior | API calls target the **active** version unless a specific `versionId` is provided |

```bash
# The Agent Runtime API defaults to the active version:
curl -X POST ".../einstein/ai-agent/v1" \
  -d '{"agentDefinitionId": "0XxXXXXXXXXXXX"}'   # Uses active version

# To target a specific version (draft/committed), include versionId:
curl -X POST ".../einstein/ai-agent/v1" \
  -d '{"agentDefinitionId": "0XxXXXXXXXXXXX", "agentVersionId": "4KdXXXXXXXXXXX"}'
```

> **Key implication**: When testing draft versions via API, you must explicitly pass the version ID. Otherwise, the API will use the last activated version — which may not reflect your latest changes.

---

## ⛔ CLI Anti-Patterns

### DO NOT SOQL query metadata types

These are **metadata types**, NOT sObjects. SOQL queries against them return `INVALID_TYPE`.

| Type | ❌ WRONG (SOQL) | ✅ CORRECT (Metadata API) |
|------|-----------------|--------------------------|
| GenAiPlannerBundle | `SELECT ... FROM GenAiPlannerBundle` | `sf project retrieve start --metadata "GenAiPlannerBundle:Name"` |
| AiAuthoringBundle | `SELECT ... FROM AiAuthoringBundle` | `sf project retrieve start --metadata "AiAuthoringBundle:Name"` |
| GenAiFunction | `SELECT ... FROM GenAiFunction` | `sf project retrieve start --metadata "GenAiFunction:Name"` |

> For SOQL, query `BotDefinition` and `BotVersion` instead — these ARE sObjects.

### BotDefinition vs BotVersion field reference

| Field | BotDefinition | BotVersion |
|-------|:---:|:---:|
| Id, DeveloperName | ✅ | ✅ |
| MasterLabel | ✅ | ❌ |
| **Status** | ❌ | ✅ |
| VersionNumber | ❌ | ✅ |

> ⚠️ `Status` lives on `BotVersion`, NOT `BotDefinition`. Querying `BotDefinition.Status` returns "No such column."

### DO NOT run bare `sf agent preview`

| ❌ WRONG (interactive, hangs) | ✅ CORRECT (programmatic) |
|-------------------------------|--------------------------|
| `sf agent preview` | `sf agent preview start --authoring-bundle MyAgent --simulate-actions -o TARGET_ORG --json` |
| *(waits for keyboard input)* | `sf agent preview send --session-id $ID --authoring-bundle MyAgent --utterance "..." -o TARGET_ORG --json` |
| | `sf agent preview end --session-id $ID --authoring-bundle MyAgent -o TARGET_ORG --json` |

### DO NOT pass context variables via `sf agent preview`

> ⛔ `sf agent preview` does NOT support context or session variable injection. There are no `--context`, `--session-var`, or `--variables` flags.

| Variable Source | Works in Preview? | Alternative |
|----------------|:-----------------:|-------------|
| `@session.sessionID` | ❌ | Agent Runtime API with session context |
| `@context.customerId` | ❌ | Agent Runtime API with `contextVariables` |
| `@context.RoutableId` | ❌ | Agent Runtime API with `contextVariables` |
| Mutable vars (defaults) | ✅ | Works normally via default values |
| `with param=...` (slot-filling) | ✅ | Works normally via LLM extraction |
