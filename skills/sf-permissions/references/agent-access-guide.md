<!-- Parent: sf-permissions/SKILL.md -->

# Agent Access Permissions & Visibility Troubleshooting

## Agent Access Permissions

Employee Agents require explicit access via the `<agentAccesses>` element in Permission Sets. Without this, users won't see the agent in the Lightning Experience Copilot panel.

**Permission Set XML Structure:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <agentAccesses>
        <agentName>Case_Assist</agentName>
        <enabled>true</enabled>
    </agentAccesses>
    <hasActivationRequired>false</hasActivationRequired>
    <label>Case Assist Agent Access</label>
</PermissionSet>
```

**Key Points:**
- `<agentName>` must match the agent developer/API name. For Agent Script, this is usually `config.developer_name`. For Builder-based agents, use the agent’s developer/API name exposed in metadata or Setup.
- Multiple `<agentAccesses>` elements can be included for multiple agents
- `<enabled>true</enabled>` grants access; `false` or omission denies access

**Deploy and Assign:**
```bash
# Deploy permission set
sf project deploy start --source-dir force-app/main/default/permissionsets/Agent_Access.permissionset-meta.xml -o TARGET_ORG

# Assign via Setup > Permission Sets > Manage Assignments
```

## Starter scaffold

Create `force-app/main/default/permissionsets/MyAgent_Access.permissionset-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <agentAccesses>
        <agentName>MyAgent</agentName>
        <enabled>true</enabled>
    </agentAccesses>
    <hasActivationRequired>false</hasActivationRequired>
    <label>MyAgent Access</label>
</PermissionSet>
```

```bash
sf project deploy start --source-dir force-app/main/default/permissionsets/MyAgent_Access.permissionset-meta.xml -o TARGET_ORG --json
sf org assign permset --name MyAgent_Access --on-behalf-of <username> -o TARGET_ORG --json
```

> If assignment fails, inspect the full `--json` failure payload first. Current CLI versions surface multiple permission-assignment errors in JSON output, which makes root-cause analysis much easier than retrying blindly.

---

## Visibility Troubleshooting

When an Agentforce Employee Agent is deployed but not visible to users:

### Step 1: Verify Agent Status
```bash
sf org open -p "/lightning/setup/EinsteinAgentforce/home" -o TARGET_ORG
# Agent should show Status: Active
```

### Step 2: Check for Agent Access Permission
```bash
# Retrieve permission sets to check for agentAccesses
sf project retrieve start -m "PermissionSet:*" -o TARGET_ORG

# Search for agentAccesses element
grep -r "agentAccesses" force-app/main/default/permissionsets/
```

### Step 3: Create Permission Set (if needed)
Create `force-app/main/default/permissionsets/MyAgent_Access.permissionset-meta.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <agentAccesses>
        <agentName>MyAgent</agentName>
        <enabled>true</enabled>
    </agentAccesses>
    <hasActivationRequired>false</hasActivationRequired>
    <label>MyAgent Access</label>
</PermissionSet>
```

### Common Issues
| Symptom | Cause | Solution |
|---------|-------|----------|
| No Agentforce icon | CopilotSalesforceUser PS not assigned | Assign CopilotSalesforceUser permission set |
| Icon visible, agent not in list | Missing agentAccesses | Add `<agentAccesses>` to permission set |
| Admin can activate the agent but employees still can’t see it | Missing `<agentAccesses>` on assigned Permission Set | Deploy and assign an access Permission Set |
| Agent visible, errors on open | Agent not fully published | Check agent logs in Setup |
| "Agent not found" error | Name mismatch | Ensure `<agentName>` matches the agent developer/API name exactly |
