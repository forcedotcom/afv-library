# Integration Skill Templates

Templates for creating new integration skills with automatic credential and endpoint security configuration.

## 📚 Available Templates

### 1. **example.cspTrustedSite-meta.xml** (Recommended)

Template for creating CSP Trusted Sites (modern approach, API 48+)

**Use for:** Allowing outbound HTTP callouts to external APIs

**Copy to:** `my-skill/assets/MyAPI.cspTrustedSite-meta.xml`

**Example:**
```xml
<CspTrustedSite xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>StripeAPI</fullName>
    <description>Stripe payment API endpoint</description>
    <endpointUrl>https://api.stripe.com</endpointUrl>
    <isActive>true</isActive>
    <context>All</context>
</CspTrustedSite>
```

---

### 2. **example.remoteSite-meta.xml** (Legacy Fallback)

Template for creating Remote Site Settings (works in all API versions)

**Use for:** Backward compatibility with older orgs (pre-API 48)

**Copy to:** `my-skill/assets/MyAPI.remoteSite-meta.xml`

**Example:**
```xml
<RemoteSiteSetting xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>StripeAPI</fullName>
    <description>Stripe payment API endpoint</description>
    <disableProtocolSecurity>false</disableProtocolSecurity>
    <isActive>true</isActive>
    <url>https://api.stripe.com</url>
</RemoteSiteSetting>
```

---

### 3. **setup-credentials-with-csp.sh** (Complete Setup Script)

Template for creating skill-specific setup scripts that handle:
- API credential configuration
- CSP Trusted Sites / Remote Site Settings deployment
- Automatic fallback logic

**Copy to:** `my-skill/scripts/setup-credentials.sh`

---

## 🚀 Creating a New Integration Skill

### Step 1: Copy Templates

```bash
# Create skill directory structure
mkdir -p my-stripe-skill/{assets,scripts,references}

# Copy endpoint security templates
cp scripts/templates/example.cspTrustedSite-meta.xml \
   my-stripe-skill/assets/StripeAPI.cspTrustedSite-meta.xml

cp scripts/templates/example.remoteSite-meta.xml \
   my-stripe-skill/assets/StripeAPI.remoteSite-meta.xml

# Copy setup script template
cp scripts/templates/setup-credentials-with-csp.sh \
   my-stripe-skill/scripts/setup-credentials.sh

chmod +x my-stripe-skill/scripts/setup-credentials.sh
```

### Step 2: Customize for Your API

**Edit `StripeAPI.cspTrustedSite-meta.xml`:**
```xml
<CspTrustedSite xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>StripeAPI</fullName>
    <description>Stripe payment processing API</description>
    <endpointUrl>https://api.stripe.com</endpointUrl>
    <isActive>true</isActive>
    <context>All</context>
</CspTrustedSite>
```

**Edit `StripeAPI.remoteSite-meta.xml`:**
```xml
<RemoteSiteSetting xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>StripeAPI</fullName>
    <description>Stripe payment processing API</description>
    <disableProtocolSecurity>false</disableProtocolSecurity>
    <isActive>true</isActive>
    <url>https://api.stripe.com</url>
</RemoteSiteSetting>
```

**Edit `setup-credentials.sh`:**
Replace these variables at the top of the script:
```bash
SKILL_NAME="Stripe"
CUSTOM_SETTING_NAME="StripeAPI"
CSP_NAME="StripeAPI"
API_KEY_URL="https://dashboard.stripe.com/apikeys"
```

### Step 3: Test

```bash
cd my-stripe-skill
./scripts/setup-credentials.sh AIZoom
```

**Expected output:**
```
╔══════════════════════════════════════════════════════════════╗
║        Stripe Integration - Credential Setup                ║
╚══════════════════════════════════════════════════════════════╝

► Validating org connection...
✓ Connected to org: AIZoom

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Enter your Stripe API key
Get it from: https://dashboard.stripe.com/apikeys
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

API Key (input hidden): [paste key]

✓ API key received

► Checking for API_Credentials__c Custom Setting...
✓ Custom Setting created

► Creating Stripe credential record...
✓ Credential created

► Configuring endpoint security (CSP Trusted Sites)...
✓ CSP Trusted Site configured

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Stripe integration configured successfully!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎉 Setup complete!
```

---

## 🔑 Key Concepts

### CSP Trusted Sites vs Remote Site Settings

| Feature | CSP Trusted Sites | Remote Site Settings |
|---------|-------------------|----------------------|
| **API Version** | 48+ (Spring '20+) | All versions |
| **Recommended** | ✅ Yes (modern) | ⚠️ Legacy only |
| **Context Control** | Granular (Apex, LWC, etc.) | Global |
| **Security** | Better (CSP standard) | Basic |
| **Setup** | Setup → CSP Trusted Sites | Setup → Remote Site Settings |

### Why Both Templates?

The setup script **automatically chooses** the right one:

```bash
# Modern org (API 48+)
→ Deploys CSP Trusted Site ✅

# Older org (pre-API 48)
→ Falls back to Remote Site Setting ✅

# Either exists already
→ Skips deployment ✅
```

**Result:** Works across all Salesforce org versions! 🎯

---

## 📋 Integration Skill Checklist

When creating a new integration skill, include:

- [ ] `assets/MyAPI.cspTrustedSite-meta.xml` (modern approach)
- [ ] `assets/MyAPI.remoteSite-meta.xml` (fallback)
- [ ] `scripts/setup-credentials.sh` (automated setup)
- [ ] `scripts/README.md` (usage documentation)
- [ ] `SKILL.md` (skill definition)
- [ ] `QUICKSTART.md` (quick start guide)
- [ ] `assets/MyCalloutService.cls` (Apex integration code)

---

## 🌟 Real-World Examples

### Example: Stripe Integration
```
sf-stripe/
├── assets/
│   ├── StripeAPI.cspTrustedSite-meta.xml
│   ├── StripeAPI.remoteSite-meta.xml
│   └── StripeCalloutService.cls
├── scripts/
│   ├── setup-credentials.sh
│   └── README.md
└── SKILL.md
```

---

## 🆘 Troubleshooting Templates

### "CspTrustedSite is not supported"
**Cause:** Org is older than API 48 (Spring '20)

**Fix:** Script automatically falls back to Remote Site Settings

### "Entity of type 'RemoteSiteSetting' is not available"
**Cause:** Querying RemoteSiteSetting is restricted in some orgs

**Fix:** Script handles this gracefully with `|| true`

### "Unable to lock row"
**Cause:** Someone else is editing the same CSP Trusted Site/Remote Site Setting

**Fix:** Wait a moment and run script again

---

## 💡 Best Practices

### 1. Always Include Both Templates

```bash
# Even if you only target modern orgs, include both:
my-skill/assets/MyAPI.cspTrustedSite-meta.xml  # Primary
my-skill/assets/MyAPI.remoteSite-meta.xml      # Fallback
```

**Why:** Users might have older orgs, and the script handles fallback automatically.

### 2. Use Descriptive Names

```bash
# ✅ Good - clear what API this is for
StripeAPI.cspTrustedSite-meta.xml
BlandAPI.cspTrustedSite-meta.xml
TwilioAPI.cspTrustedSite-meta.xml

# ❌ Bad - too generic
API.cspTrustedSite-meta.xml
Integration.cspTrustedSite-meta.xml
```

### 3. Security: Never Allow HTTP

```xml
<!-- Remote Site Settings -->
<disableProtocolSecurity>false</disableProtocolSecurity>  ✅ Correct

<disableProtocolSecurity>true</disableProtocolSecurity>   ❌ INSECURE!
```

### 4. Document Endpoint Requirements

In your skill's README, document:
- API base URL
- Whether CSP Trusted Site is needed
- Any special endpoint requirements

---

## 📚 Further Reading

- **Integration Skill:** `skills/sf-integration/`
- **Generic Scripts:** `scripts/README.md`
- **Salesforce CSP Docs:** https://help.salesforce.com/s/articleView?id=sf.csp_trusted_sites.htm
- **Remote Site Settings:** https://help.salesforce.com/s/articleView?id=sf.configuring_remoteproxy.htm

---

**Ready to create your first integration skill?** 🚀

Start with the Bland.ai example and adapt it for your API!
