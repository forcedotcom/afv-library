# Component Replacement Workflow

Detailed steps for scanning site metadata, finding OOTB components, and replacing them with open code equivalents.

## Extracting All OOTB Components from Site Metadata

### Step 1: Scan Theme Layouts

- Search in: `force-app/main/default/digitalExperiences/site/<store-name>/sfdc_cms__themeLayout/*/content.json`
- Parse each `content.json` file
- Extract all values from `"definition"` keys

### Step 2: Scan Views

- Search in: `force-app/main/default/digitalExperiences/site/<store-name>/sfdc_cms__view/*/content.json`
- Parse each `content.json` file
- Extract all values from `"definition"` keys

### Step 3: Filter to OOTB Components

Keep any `"definition"` value that starts with `commerce` (covers `commerce_builder:*`, `commerce_cart:*`, `commerce:*`, `commerce_my_account:*`, and any other commerce namespaces).

### Step 4: Return Deduplicated List

Example output: `["commerce_builder:cartBadge", "commerce_builder:cartContents", "commerce/searchInput"]`

---

## Finding a Specific OOTB Component

1. Run the extraction above to get all OOTB components
2. Check if the target component exists in the list
3. If found: return the list of `content.json` files where it appears
4. If not found:
   - Inform user: "Component {name} not found in site metadata"
   - Display all components currently used in the site
   - Ask: "Would you like to replace one of these instead?"

---

## Replacing an OOTB Component

### Step 1: Determine Open Code Name

Apply the mapping rules from [ootb-to-opencode-mapping.md](ootb-to-opencode-mapping.md).

The OOTB component definition comes from `content.json` — any `"definition"` value starting with `commerce` is an OOTB component. Use the full definition value (e.g., `commerce_builder:cartBadge`) to apply the mapping.

### Step 2: Verify Open Code Component Exists

Check in cloned repo: `.tmp/b2b-commerce-open-source-components/force-app/main/default/sfdc_cms__lwc/`

If not found, list all available open code components and ask user to select.

### Step 3: Update Site Metadata

For each `content.json` file where the OOTB component is found:
- Replace the `"definition"` value only
- Preserve all other JSON properties and structure

### Step 4: Track Changes

- Log every file modified
- Count total replacements made
- Report summary to user
