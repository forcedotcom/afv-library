# Credential Configuration Scripts

**Generic/reusable scripts** for configuring API credentials across sf-skills using modern Salesforce patterns.

> 💡 **Pattern:** Each skill should have its own `scripts/setup-credentials.sh` that's tailored to that skill. These scripts in `/scripts/` are generic templates that can be copied and customized.
>
> **Example:** See `skills/sf-integration/scripts/` for a skill-specific implementation.
>
> **Canonical source note:** The root `/scripts/` directory is the source of truth for these generic integration helpers. Matching copies may also exist under `skills/sf-integration/` for skill-local distribution; keep them in sync until packaging is consolidated.

---

## 🆕 Modern Approach: Enhanced Named Credentials

**Salesforce now recommends Enhanced Named Credentials** (External Credentials + Named Credentials) over the legacy approach.

### What Are Enhanced Named Credentials?

**Enhanced Named Credentials** = **External Credential** + **Named Credential** + **Endpoint Security**

```
External Credential (stores the API key securely)
         ↓
Named Credential (references the External Credential)
         ↓
Your HTTP Callout (uses callout:NamedCredentialName)
```

### Why Use Enhanced Named Credentials?

✅ **More secure** - Credentials encrypted by Salesforce platform
✅ **Flexible** - Supports multiple authentication protocols (Custom, Basic, OAuth, JWT)
✅ **Portable** - Easier to manage across multiple orgs
✅ **Modern** - Recommended by Salesforce for all new integrations
✅ **Programmable** - Can be configured via ConnectApi (no UI required!)

---

## 🎯 The Correct Order of Operations

**CRITICAL:** You must deploy components in this exact order:

```bash
# 1. Deploy External Credential metadata (defines the credential structure)
sf project deploy start \
  --source-dir force-app/main/default/externalCredentials/YourAPI.externalCredential-meta.xml \
  --target-org YourOrg

# 2. Deploy Named Credential metadata (references the External Credential)
sf project deploy start \
  --source-dir force-app/main/default/namedCredentials/YourAPI.namedCredential-meta.xml \
  --target-org YourOrg

# 3. Deploy endpoint security (allows outbound HTTP calls)
sf project deploy start \
  --source-dir force-app/main/default/cspTrustedSites/YourAPI.cspTrustedSite-meta.xml \
  --target-org YourOrg

# 4. Set the API key programmatically using our script
./scripts/configure-named-credential.sh YourExternalCredential yourPrincipalName YourOrg
```

**Why this order matters:**
- External Credential must exist before Named Credential can reference it
- Named Credential must exist before you can set credentials via ConnectApi
- Endpoint security must exist before making HTTP callouts

---

## 📦 What Gets Deployed

### 1. External Credential Metadata

**File:** `externalCredentials/YourAPI.externalCredential-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ExternalCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <authenticationProtocol>Custom</authenticationProtocol>
    <externalCredentialParameters>
        <parameterGroup>apiKeyPrincipal</parameterGroup>
        <parameterName>apiKeyPrincipal</parameterName>
        <parameterType>NamedPrincipal</parameterType>
        <sequenceNumber>1</sequenceNumber>
    </externalCredentialParameters>
    <label>Your API</label>
</ExternalCredential>
```

**Key fields:**
- `authenticationProtocol` - Custom, Basic, OAuth, JWT, etc.
- `parameterName` - Principal name (used in configure script)
- `label` - Display name in Salesforce UI

---

### 2. Named Credential Metadata

**File:** `namedCredentials/YourAPI.namedCredential-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<NamedCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <allowMergeFieldsInBody>false</allowMergeFieldsInBody>
    <allowMergeFieldsInHeader>true</allowMergeFieldsInHeader>
    <calloutStatus>Enabled</calloutStatus>
    <generateAuthorizationHeader>false</generateAuthorizationHeader>
    <label>Your API</label>
    <namedCredentialParameters>
        <parameterName>Url</parameterName>
        <parameterType>Url</parameterType>
        <parameterValue>https://api.yourservice.com</parameterValue>
    </namedCredentialParameters>
    <namedCredentialParameters>
        <externalCredential>YourExternalCredential</externalCredential>
        <parameterName>ExternalCredential</parameterName>
        <parameterType>Authentication</parameterType>
    </namedCredentialParameters>
    <namedCredentialType>SecuredEndpoint</namedCredentialType>
</NamedCredential>
```

**Key fields:**
- `externalCredential` - Must match External Credential developer name
- `parameterValue` (Url) - Base URL for API
- `namedCredentialType` - Must be "SecuredEndpoint" for Enhanced Named Credentials

---

### 3. Endpoint Security Metadata

**Modern:** CSP Trusted Site (API 48+ / Spring '20+)

**File:** `cspTrustedSites/YourAPI.cspTrustedSite-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CspTrustedSite xmlns="http://soap.sforce.com/2006/04/metadata">
    <context>All</context>
    <endpointUrl>https://api.yourservice.com</endpointUrl>
    <isActive>true</isActive>
    <isApplicableToConnectSrc>true</isApplicableToConnectSrc>
</CspTrustedSite>
```

**Legacy:** Remote Site Setting (all API versions)

**File:** `remoteSiteSettings/YourAPI.remoteSite-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<RemoteSiteSetting xmlns="http://soap.sforce.com/2006/04/metadata">
    <disableProtocolSecurity>false</disableProtocolSecurity>
    <isActive>true</isActive>
    <url>https://api.yourservice.com</url>
</RemoteSiteSetting>
```

**Tip:** Deploy both CSP and Remote Site for maximum compatibility!

---

## 🛠️ Scripts

### `configure-named-credential.sh` (Enhanced Named Credentials)

**Purpose:** Sets API keys for Enhanced Named Credentials programmatically using ConnectApi

**Usage:**
```bash
./scripts/configure-named-credential.sh <external-credential-name> <principal-name> <org-alias>
```

**Example:**
```bash
./scripts/configure-named-credential.sh VisualCrossingWeather weatherAPIKey AIZoom
```

**What it does:**
1. ✅ Validates org connection
2. ✅ Checks External Credential exists
3. ✅ Prompts for API key securely (input hidden)
4. ✅ Generates Apex code using ConnectApi.NamedCredentials.createCredential()
5. ✅ Executes Apex to store credential encrypted
6. ✅ Handles create (first-time) vs patch (update) automatically

**Prerequisites:**
- External Credential deployed
- Named Credential deployed
- Endpoint security (CSP/Remote Site) deployed
- Salesforce CLI authenticated to target org

**How it works under the hood:**
```apex
ConnectApi.CredentialInput newCredentials = new ConnectApi.CredentialInput();
newCredentials.externalCredential = 'YourExternalCredential';
newCredentials.principalName = 'yourPrincipalName';
newCredentials.authenticationProtocol = ConnectApi.CredentialAuthenticationProtocol.Custom;

Map<String, ConnectApi.CredentialValueInput> creds = new Map<String, ConnectApi.CredentialValueInput>();
ConnectApi.CredentialValueInput apiKeyParam = new ConnectApi.CredentialValueInput();
apiKeyParam.encrypted = true;
apiKeyParam.value = 'YOUR_API_KEY';
creds.put('apiKey', apiKeyParam);

newCredentials.credentials = creds;
ConnectApi.NamedCredentials.createCredential(newCredentials);
```

---

### `set-api-credential.sh` (Legacy Custom Settings)

**Purpose:** Sets API credentials using Custom Settings (older approach, still useful for dev/test)

**Usage:**
```bash
./scripts/set-api-credential.sh <setting-name> <api-key-or-dash> <org-alias>
```

**Example:**
```bash
# Secure input (recommended)
./scripts/set-api-credential.sh BlandAI - AIZoom

# Direct input (less secure)
./scripts/set-api-credential.sh BlandAI sk_live_abc123xyz AIZoom
```

**When to use Custom Settings:**
- ✅ Dev/test environments
- ✅ CI/CD pipelines (no Apex execution required)
- ✅ Simple API key authentication via query parameters
- ❌ NOT recommended for production

---

## 📚 Complete Example: Weather API Integration

### Step 1: Create Metadata Files

**External Credential:** `externalCredentials/VisualCrossingWeather.externalCredential-meta.xml`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<ExternalCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <authenticationProtocol>Custom</authenticationProtocol>
    <externalCredentialParameters>
        <parameterGroup>weatherAPIKey</parameterGroup>
        <parameterName>weatherAPIKey</parameterName>
        <parameterType>NamedPrincipal</parameterType>
        <sequenceNumber>1</sequenceNumber>
    </externalCredentialParameters>
    <label>Visual Crossing Weather</label>
</ExternalCredential>
```

**Named Credential:** `namedCredentials/VisualCrossingWeatherAPI.namedCredential-meta.xml`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<NamedCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <allowMergeFieldsInBody>false</allowMergeFieldsInBody>
    <allowMergeFieldsInHeader>true</allowMergeFieldsInHeader>
    <calloutStatus>Enabled</calloutStatus>
    <generateAuthorizationHeader>false</generateAuthorizationHeader>
    <label>Visual Crossing Weather API</label>
    <namedCredentialParameters>
        <parameterName>Url</parameterName>
        <parameterType>Url</parameterType>
        <parameterValue>https://weather.visualcrossing.com</parameterValue>
    </namedCredentialParameters>
    <namedCredentialParameters>
        <externalCredential>VisualCrossingWeather</externalCredential>
        <parameterName>ExternalCredential</parameterName>
        <parameterType>Authentication</parameterType>
    </namedCredentialParameters>
    <namedCredentialType>SecuredEndpoint</namedCredentialType>
</NamedCredential>
```

**CSP Trusted Site:** `cspTrustedSites/VisualCrossingWeatherAPI.cspTrustedSite-meta.xml`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<CspTrustedSite xmlns="http://soap.sforce.com/2006/04/metadata">
    <context>All</context>
    <endpointUrl>https://weather.visualcrossing.com</endpointUrl>
    <isActive>true</isActive>
</CspTrustedSite>
```

### Step 2: Deploy to Org (Correct Order!)

```bash
# 1. External Credential
sf project deploy start \
  --source-dir force-app/main/default/externalCredentials/VisualCrossingWeather.externalCredential-meta.xml \
  --target-org AIZoom

# 2. Named Credential (deploy together with CSP for efficiency)
sf project deploy start \
  --source-dir force-app/main/default/namedCredentials/VisualCrossingWeatherAPI.namedCredential-meta.xml \
  --source-dir force-app/main/default/cspTrustedSites/VisualCrossingWeatherAPI.cspTrustedSite-meta.xml \
  --target-org AIZoom
```

### Step 3: Set API Key

```bash
./scripts/configure-named-credential.sh VisualCrossingWeather weatherAPIKey AIZoom
# Enter your API key when prompted
```

### Step 4: Use in Apex

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:VisualCrossingWeatherAPI/VisualCrossingWebServices/rest/services/timeline/London');
req.setMethod('GET');

Http http = new Http();
HttpResponse res = http.send(req);
System.debug(res.getBody());
```

**Note:** The API key is automatically included in the request! No manual credential handling needed.

---

## 🔍 Troubleshooting

### "External Credential not found"
**Cause:** External Credential not deployed or wrong developer name
**Fix:** Deploy External Credential first, check spelling

### "Named Credential not found"
**Cause:** Named Credential not deployed
**Fix:** Deploy Named Credential after External Credential

### "There are no existing authentication credentials to update"
**Cause:** Using `patchCredential()` instead of `createCredential()`
**Fix:** Our script handles this automatically (tries create, falls back to patch)

### "Unable to connect to endpoint"
**Cause:** CSP Trusted Site or Remote Site Setting not deployed
**Fix:** Deploy endpoint security metadata

### "You can't set the visibility for a Custom Setting to Protected unless you are in a developer, sandbox, or scratch org"
**Cause:** Trying to deploy Custom Setting with `Protected` visibility to production org
**Fix:** Change visibility to `Public` for production orgs

---

## 🧹 Local Cleanup Helper

To remove common local/generated artifacts from your working tree:

```bash
./scripts/cleanup-local.sh          # Preview removals
./scripts/cleanup-local.sh --apply  # Delete matched local artifacts
```

This only targets local caches, virtual environments, trace output, and other generated workspace files. It does **not** modify tracked repository content.

---

## 📖 Additional Resources

- [Salesforce External Credentials Documentation](https://help.salesforce.com/s/articleView?id=sf.nc_create_edit_external_credential.htm)
- [ConnectApi.NamedCredentials Class](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_ConnectAPI_NamedCredentials_static_methods.htm)
- [CSP Trusted Sites Documentation](https://help.salesforce.com/s/articleView?id=sf.csp_trusted_sites.htm)

---

## 🎯 Key Takeaways

1. **Always use Enhanced Named Credentials** for new integrations
2. **Order matters** - External Credential → Named Credential → Endpoint Security → Set API Key
3. **Use our script** - `configure-named-credential.sh` handles ConnectApi complexity
4. **No UI required** - Everything can be automated via CLI + Apex
5. **Production-ready** - Credentials are encrypted and secure

---

**Questions?** Check skill-specific setup guides in each skill's directory (e.g., `skills/sf-integration/`)
