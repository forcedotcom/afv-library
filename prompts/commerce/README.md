# Commerce Prompts

Prompts for building and managing Salesforce B2B Commerce storefronts.

## Overview

Commerce on Core enables you to build digital storefronts using Experience Cloud (LWR sites) integrated with Commerce capabilities for product catalogs, pricing, shopping cart, checkout, and order management.

### Two-Part Architecture

Commerce consists of two distinct but connected parts:

1. **Commerce Store** (Backend - Runtime Data)
   - WebStore configuration
   - Buyer groups and entitlements
   - Pricing policies
   - Payment, tax, shipping setup
   - Product catalog associations
   - **Created in org via Setup → Commerce app**
   - **NOT source-controllable**

2. **Storefront** (Frontend - Metadata)
   - Digital Experience (LWR site)
   - Page layouts and components
   - Custom LWCs
   - Branding and theme
   - **Source-controllable as ExperienceBundle**
   - **Deployable via Salesforce CLI**

## Usage Pattern

**Critical:** Always create Commerce Store in org FIRST, then retrieve the auto-generated storefront metadata.

### Correct Workflow

> See full interactive flow in `create-retrieve-b2b-storefront.md`

```bash
# 1. Create Commerce Store in org (via UI)
#    Setup → Commerce → Stores → Create Store

# 2. List available storefronts
sf org list metadata --metadata-type DigitalExperienceConfig

# 3. Retrieve the auto-generated storefront metadata
sf project retrieve start -m DigitalExperienceBundle:site/My_Store_Name

# 4. Customize with additional LWCs or pages
#    Add custom components, modify layouts in Experience Builder

# 5. Version control and deploy
git add force-app/main/default/digitalExperiences/
git commit -m "feat: add My Store storefront"
```

### ❌ Incorrect Approach

Don't manually create StorefrontName.digitalExperience-meta.xml from scratch. The Commerce setup wizard generates complex configurations that are difficult to replicate manually.

## Available Prompts

### Create and Retrieve B2B Commerce Storefront
**Use when:** You want to create a Commerce B2B Store and download the storefront to version control

**Prerequisites:**
- Commerce licenses available in org
- Experience Cloud enabled
- Salesforce CLI authorized with default org

**What it does:**
- Guides through interactive 7-step workflow
- Explains Store vs Storefront concept
- Lists available Digital Experiences in org
- Retrieves ExperienceBundle metadata
- Provides customization and deployment guidance

## Related Rules

Before using these prompts, review:

**`rules/commerce/commerce-b2b-store-requirements.md`**
- Explains Store vs Storefront distinction
- Details the required creation workflow
- Lists what is/isn't source-controllable
- Provides deployment checklist
- Contains agent guidance for interactive flow

## Common Scenarios

### Scenario 1: New B2B Store
```
1. Follow commerce-b2b-store-requirements.md rule
2. Create Store in org via Commerce app
3. Use "Create and Retrieve B2B Commerce Storefront" prompt
4. Customize with custom LWCs (hero banner, promotions)
5. Commit and deploy to other environments
```

### Scenario 2: Extend Existing Storefront
```
1. Retrieve current metadata if not already in repo
2. Create custom LWCs following LDS-first patterns
3. Add to pages in Experience Builder
4. Retrieve updated metadata
5. Commit changes
```

### Scenario 3: Multi-Org Deployment
```
1. In target org, create Commerce Store (same name as source)
2. Deploy storefront metadata from repo
3. Verify Commerce components render correctly
4. Configure org-specific settings (payment, tax, shipping)
```

## Best Practices

### ✅ Do:
- Create Commerce Store in org first (always!)
- Retrieve auto-generated storefront metadata
- Version control Experience metadata
- Use LDS-first approach for custom LWCs
- Document store configuration steps
- Test in Experience Builder before deploying

### ❌ Don't:
- Create StorefrontName.digitalExperience-meta.xml from scratch
- Deploy storefront without creating Store in target org
- Try to version control WebStore records (use data APIs)
- Skip the Commerce setup wizard
- Forget to associate Experience with WebStore

## File Structure

After retrieving a Commerce storefront:

```
force-app/main/default/
└── digitalExperiences/
    └── site/
        └── My_B2B_Store1/
            ├── My_B2B_Store1.digitalExperience-meta.xml  # Bundle metadata
            ├── sfdc_cms__view/                           # Pages
            │   ├── home/
            │   ├── current_cart/
            │   ├── current_checkout/
            │   ├── detail_*/                            # PDP
            │   └── list_*/                              # PLP
            ├── sfdc_cms__route/                         # URL routing
            ├── sfdc_cms__site/                          # Site settings
            ├── sfdc_cms__theme/                         # Theme config
            └── [other sfdc_cms__* directories]
```

## Tags

Commerce prompts use these tags:
- `b2b` - B2B Commerce specific
- `scom` - Salesforce Commerce
- `scom b2b` - Salesforce Commerce B2B
- `commerce b2b` - Commerce B2B specific
- `storefront` - Buyer-facing storefront (metadata)
- `store` - Backend store configuration (data)
- `lwr` - Lightning Web Runtime sites
- `retrieve` - Metadata retrieval operations
- `metadata` - Source-controllable assets

## Additional Resources

**Salesforce Documentation:**
- [B2B Commerce Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.b2b_commerce_dev_guide.meta/b2b_commerce_dev_guide/)
- [Experience Cloud LWR Sites](https://developer.salesforce.com/docs/platform/lwr-sites/guide/overview.html)
- [DigitalExperienceBundle Metadata](https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_digitalexperiencebundle.htm)

**Trailhead:**
- [B2B Commerce Basics](https://trailhead.salesforce.com/content/learn/modules/b2b-commerce-basics)
- [Build a B2B Commerce Store](https://trailhead.salesforce.com/content/learn/projects/build-a-b2b-commerce-store)

**CLI Commands:**
```bash
# List Commerce metadata
sf org list metadata --metadata-type DigitalExperienceConfig

# Retrieve storefront
sf project retrieve start -m DigitalExperienceBundle:site/StoreName

# Deploy storefront
sf project deploy start --source-dir force-app/main/default/digitalExperiences/site/StoreName/
```
