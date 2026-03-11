---
name: Create and Retrieve B2B Commerce Storefront
description: Interactive guide to create a Commerce B2B Store and retrieve storefront metadata
tags: commerce, b2b, scom, scom b2b, commerce b2b, storefront, lwr, retrieve, metadata
category: commerce
requires_setup: true
setup_summary: Requires Commerce licenses; agent guides through store creation interactively
---

## Context

This interactive workflow guides you through creating a Commerce B2B Store in your Salesforce org and retrieving the auto-generated storefront metadata to your local repository.

**Important:** Commerce B2B consists of two components:
1. **Commerce Store (Backend)** - Runtime data configured in the org (NOT source-controllable)
2. **Storefront (Frontend)** - LWR Digital Experience site (source-controllable metadata)

The Store must be created first because it automatically generates the associated Digital Experience site.

> **See:** `rules/commerce/commerce-b2b-store-requirements.md` for detailed Store vs Storefront distinction

---

## Interactive Flow

### Step 1: Explain Commerce B2B Store Concept

**Agent should explain:**

Commerce B2B on Salesforce Core consists of two components that work together:

1. **Commerce Store (Backend)** - Runtime data configured in the org (WebStore records, buyer groups, pricing policies, payment settings). This is NOT source-controllable.

2. **Storefront (Frontend)** - LWR Digital Experience site for buyers. This IS source-controllable as metadata (ExperienceBundle).

The Store must be created in the org first because the setup wizard automatically generates the associated Digital Experience site with all necessary Commerce components configured correctly.

> **See:** `rules/commerce/commerce-b2b-store-requirements.md` for detailed Store vs Storefront distinction

---

### Step 2: Ask User to Create B2B Store

**Agent should provide these steps:**

1. In your Salesforce org, navigate to **Setup → Commerce → Stores**
   - OR use the Commerce app from **App Launcher → Commerce → Create Store**

2. Click **"Create Store"** or **"Setup New Store"**

3. Select **"B2B Store"** as the store type

4. Follow the store setup wizard:
   - **Store Name**: Choose a descriptive name (e.g., "My B2B Store")
     - ⚠️ Important: This name determines the folder name (spaces become underscores)
   - **Default Buyer Group**: Associate with Account objects
   - **Price Book**: Select or create price book
   - **Checkout Settings**: Configure checkout flow

5. Complete the wizard - it will automatically create:
   - WebStore record
   - Default buyer group and entitlement policies
   - Associated Digital Experience (LWR site)

6. Optionally configure:
   - Payment gateway (Stripe, Adyen, etc.)
   - Tax provider (Avalara, Vertex)
   - Shipping methods

**Agent should then ask:**
"Have you completed creating the B2B Store in your org? Please reply 'yes' when ready, and let me know the store name you used."

---

### Step 3: Get Confirmation from User

**Agent waits for:** User confirmation (e.g., "yes") and store name

**Agent validates:** Store name format
- No special characters
- Spaces in name will appear as underscores in folder (e.g., "My B2B Store" → "My_B2B_Store1")

**Agent acknowledges:** "Great! Let me list the available storefronts in your org..."

---

### Step 4: Run CLI Command to List LWR Sites

**Agent executes:**
```bash
sf org list metadata --metadata-type DigitalExperienceConfig
```

**Agent should:**
- Parse the output to extract site names
- Display as a numbered list for easy selection
- Explain: "The store name appears with underscores and may have a number suffix (e.g., 'My_B2B_Store1')"

**Example output format:**
```
Available Digital Experience sites:
1. My_B2B_Store1
2. Partner_Portal
3. Customer_Community
```

---

### Step 5: Let User Select Storefront

**Agent should ask:**
"Which site corresponds to your B2B Store? Enter the number or the full site name:"

**Agent validates:**
- Selection matches one of the available sites
- If unclear, ask user to confirm the exact name

**Agent confirms:** "Got it! I'll retrieve the metadata for [site-name]..."

---

### Step 6: Retrieve Storefront Metadata

**Agent executes:**
```bash
sf project retrieve start -m DigitalExperienceBundle:site/<selected-store-name>
```

**Agent should:**
- Show retrieval progress
- Confirm successful retrieval
- List the retrieved directory structure

**Expected output:**
```
Retrieved: force-app/main/default/digitalExperiences/site/My_B2B_Store1/
├── My_B2B_Store1.digitalExperience-meta.xml
├── sfdc_cms__view/ (home, current_cart, detail_*, list_*, etc.)
├── sfdc_cms__site/
├── sfdc_cms__route/
└── [other sfdc_cms__* directories]
```

---

### Step 7: Inform User About Next Steps

**Agent provides:**

✅ **Storefront metadata successfully retrieved!**

**What you can do next:**

1. **Customize the storefront:**
   - Add custom LWCs for unique B2B features
   - Modify page layouts in Experience Builder
   - Customize branding (colors, fonts, logos)
   - Add content pages (About Us, Contact, etc.)

2. **Version control:**
   ```bash
   git add force-app/main/default/digitalExperiences/
   git commit -m "feat: add B2B Commerce storefront metadata"
   ```

3. **Deploy to other orgs:**
   - First create B2B Store in target org with same name
   - Then deploy the metadata:
     ```bash
     sf project deploy start --source-dir force-app/main/default/digitalExperiences/site/My_B2B_Store1/
     ```

**📚 Documentation Resources:**
- [DigitalExperienceBundle Metadata](https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_digitalexperiencebundle.htm)
- [DigitalExperienceBundle Site](https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_digitalexperiencebundle_site.htm)
- [B2B Commerce Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.b2b_commerce_dev_guide.meta/b2b_commerce_dev_guide/)

**🎯 For Advanced Customization:**
See `rules/commerce/commerce-b2b-store-requirements.md` for:
- B2B-specific workflow patterns
- Custom LWC development guidelines
- Multi-org deployment strategies

---

## Important Notes

### ⚠️ Commerce Store Data vs Storefront Metadata

**What IS source-controllable (Storefront):**
- ✅ ExperienceBundle metadata (this prompt)
- ✅ Custom LWCs
- ✅ Page layouts and content
- ✅ Navigation structure

**What is NOT source-controllable (Commerce Store):**
- ❌ WebStore records (store settings, buyer groups)
- ❌ Product catalog data
- ❌ Price books and pricing rules
- ❌ Entitlement policies
- ❌ Inventory data
- ❌ Payment/tax/shipping configurations

**To migrate Commerce Store data between orgs:**
- Use Data Loader or Salesforce Data APIs
- Or recreate via Commerce app UI
- Or use Commerce APIs for programmatic setup

---

## Troubleshooting

### Issue: "No DigitalExperienceConfig found"

**Cause:** Store name mismatch or store not yet created

**Fix:**
1. Verify store exists: Setup → Commerce → Stores
2. Verify Experience site exists: Setup → Digital Experiences → All Sites
3. Check exact name (case-sensitive, underscores for spaces)
4. Try: `sf org list metadata --metadata-type DigitalExperienceConfig`

### Issue: "Deployment failed - Store not found"

**Cause:** Target org doesn't have a Commerce Store with matching name

**Fix:**
1. In target org, create Commerce Store with SAME NAME as source
2. Then deploy Experience metadata

### Issue: "Commerce components not rendering"

**Cause:** Store configuration missing or incorrect WebStore association

**Fix:**
1. Verify WebStore is active in target org
2. Check Experience is associated with correct WebStore
3. Verify buyer user has correct entitlements and permissions
