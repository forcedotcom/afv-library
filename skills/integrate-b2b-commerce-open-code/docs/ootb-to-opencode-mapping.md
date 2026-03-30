# OOTB to Open Code Component Mapping

Rules and examples for mapping out-of-the-box (OOTB) B2B Commerce component definitions to their open code equivalents.

## Naming Patterns

- **OOTB:** `{namespace}:{componentName}` (e.g., `commerce_builder:cartBadge`)
- **Open Code:** `site:{domain}{Context}[{Variant}]` in camelCase (e.g., `site:cartBadge`)

## Mapping Rules

| OOTB Pattern | Open Code Pattern | Notes |
|--------------|-------------------|-------|
| `commerce_builder/{name}` | `site/{name}` | Builder components map directly |
| `commerce_cart/{name}` | `site/cart{Name}Ui` | Cart runtime components get Ui suffix |
| `commerce/{name}` | `site/{name}Ui` | Runtime components get Ui suffix |
| `commerce/error` | `site/commonError` | Shared utilities use "common" domain |
| `commerce_builder/formattedCurrency` | `site/commonFormattedCurrency` | Common utilities |
| `commerce/formattedCurrency` | `site/commonFormattedCurrencyUi` | Runtime with Ui suffix |
| `commerce_my_account/myAccountLayout` | `site/themelayoutMyaccount` | Account layouts |
| `commerce/layoutSite` | `site/themelayoutSite` | Layout → themelayout domain |

## Examples

```
commerce_builder:cartContents       → site:cartContents
commerce_cart:items                 → site:cartItemsUi
commerce_builder:searchInput        → site:searchInput
commerce:searchInput                → site:searchInputUi
commerce:error                      → site:commonError
commerce_my_account:myAccountLayout → site:themelayoutMyaccount
```

## Applying the Mapping

1. **Parse** the OOTB component name — extract namespace and component name
2. **Match** against the mapping table above (check specific overrides like `commerce/error` before general rules)
3. **Generate** the open code component name
4. **Verify** the open code component exists in the cloned repo at:
   `.tmp/b2b-commerce-open-source-components/force-app/main/default/sfdc_cms__lwc/<componentName>`
5. If no mapping or component found, list available open code components and ask user to select manually

## Updating Site Metadata

For each `content.json` file where the OOTB component is found:
- Replace `"definition": "commerce_builder:cartBadge"` with `"definition": "site:cartBadge"`
- Preserve all other JSON properties — only the `definition` value changes
- Log every file modified and count total replacements
