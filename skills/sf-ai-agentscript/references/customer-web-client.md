<!-- Parent: sf-ai-agentscript/SKILL.md -->

# Phase 5.5: CustomerWebClient Surface Enablement

> ⚠️ **Without `CustomerWebClient` surface, Agent Builder Preview shows "Something went wrong" and Agent Runtime API / CLI testing returns `500 Internal Server Error`.**

**The Problem**: `connection messaging:` in the `.agent` file ONLY generates a `Messaging` plannerSurface during compilation. There is NO `connection customerwebclient:` DSL syntax — attempting it causes `ERROR_HTTP_404` on publish. Agent Builder Preview + CLI testing require `CustomerWebClient`, which must be manually patched after every publish.

## Post-Publish Patch Workflow (6 steps, required after EVERY publish)

```bash
# Step 1: Publish the agent (creates new version, e.g., v22)
sf agent publish authoring-bundle --api-name AgentName -o TARGET_ORG --json

# Step 2: Retrieve the compiled GenAiPlannerBundle
sf project retrieve start --metadata "GenAiPlannerBundle:AgentName_vNN" -o TARGET_ORG --json

# Step 3: Add CustomerWebClient plannerSurface to the XML (see template below)

# Step 4: Deactivate agent (deploy fails while active)
sf agent deactivate --api-name AgentName -o TARGET_ORG --json

# Step 5: Deploy patched bundle
sf project deploy start --metadata "GenAiPlannerBundle:AgentName_vNN" -o TARGET_ORG --json

# Step 6: Reactivate the same BotVersion created in Step 1
sf agent activate --api-name AgentName --version NN -o TARGET_ORG --json
```

> Use the same `NN` value from the `GenAiPlannerBundle:AgentName_vNN` version you just patched so the reactivation is deterministic.

## Step 3 — XML patch template

Add after existing `Messaging` plannerSurfaces block:
```xml
<!-- Add this SECOND plannerSurfaces block for CustomerWebClient -->
<plannerSurfaces>
    <adaptiveResponseAllowed>false</adaptiveResponseAllowed>
    <callRecordingAllowed>false</callRecordingAllowed>
    <outboundRouteConfigs>
        <escalationMessage>Your escalation message here.</escalationMessage>
        <outboundRouteName>Your_OmniChannel_Flow_Name</outboundRouteName>
        <outboundRouteType>OmniChannelFlow</outboundRouteType>
    </outboundRouteConfigs>
    <surface>SurfaceAction__CustomerWebClient</surface>
    <surfaceType>CustomerWebClient</surfaceType>
</plannerSurfaces>
```

> **Note**: The `outboundRouteConfigs` should mirror your Messaging surface config. If no escalation routing is configured, omit the `outboundRouteConfigs` block.

> **Note**: `EinsteinAgentApiChannel` surfaceType is NOT available on all orgs (see Known Issue 17). Use `CustomerWebClient` instead — it enables both Agent Builder Preview and Agent Runtime API access.

## ECA for Client Credentials Flow

The Agent Runtime API requires OAuth with `chatbot_api`, `sfap_api`, and `api` scopes. See `/sf-connected-apps` for ECA creation. If you only need interactive testing via `sf agent preview`, skip ECA setup — preview uses standard org auth (`sf org login web`, v2.121.7+).

## Validation

```bash
# Acquire token
curl -X POST "https://YOUR_DOMAIN.my.salesforce.com/services/oauth2/token" \
  -d "grant_type=client_credentials&client_id=KEY&client_secret=SECRET"

# Create agent session
curl -X POST "https://YOUR_DOMAIN.my.salesforce.com/einstein/ai-agent/v1" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"agentDefinitionId":"0XxXXXXXXXXXXXXXXX"}'
```

> **Symptom**: 500 error with `"errorCode": "UNKNOWN_EXCEPTION"` → Missing `CustomerWebClient` plannerSurface.
> **Symptom**: Agent Builder Preview → "Something went wrong. Refresh and try again." → Same root cause.
