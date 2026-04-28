# Credits

## sf-lwc Skill

Created by [Jag Valaiyapathy](https://github.com/Jaganpro)

## References & Inspiration

### Official Salesforce Documentation
- [LWC Component Reference](https://developer.salesforce.com/docs/component-library/overview/components) - Base component library
- [Lightning Web Components Guide](https://developer.salesforce.com/docs/platform/lwc/guide) - Official developer guide
- [SLDS Styling Hooks](https://developer.salesforce.com/docs/platform/lwc/guide/create-components-css-custom-properties.html) - CSS custom properties
- [SLDS 2 Transition Guide](https://www.lightningdesignsystem.com/2e1ef8501/p/8184ad-transition-to-slds-2) - Dark mode migration

### Community Resources
- [PICKLES Framework](https://www.salesforceben.com/the-ideal-framework-for-architecting-salesforce-lightning-web-components/) - David Picksley (Third Eye Consulting)
  - Prototype, Integrate, Composition, Kinetics, Libraries, Execution, Security methodology
- [James Simone's Blog](https://www.jamessimone.net/) - Advanced LWC patterns
  - [Composable Modal Pattern](https://www.jamessimone.net/blog/joys-of-apex/lwc-composable-modal/)
  - [Advanced Jest Testing](https://www.jamessimone.net/blog/joys-of-apex/advanced-lwc-jest-testing/)
  - [Joys of Apex](https://www.jamessimone.net/blog/) - broader LWC implementation patterns
  - [Dynamic LWC Creation](https://www.jamessimone.net/blog/joys-of-apex/dynamic-lwc-creation/)
- [LWC Recipes](https://github.com/trailheadapps/lwc-recipes) - Trailhead Apps (124+ component examples)

### SLDS 2 Dark Mode Resources
- [SLDS 2 Transition Guide](https://www.lightningdesignsystem.com/2e1ef8501/p/8184ad-transition-to-slds-2) - SLDS 2 migration guidance
- [SLDS Accessibility Overview](https://www.lightningdesignsystem.com/accessibility/overview/) - Accessibility guidance and foundations

### Spring '26 Release (API 66.0)
- [9 Features for Salesforce Developers in Spring '26](https://www.salesforceben.com/9-features-for-salesforce-developers-in-the-spring-26-release/) - Salesforce Ben
- [LWC Directives Reference](https://developer.salesforce.com/docs/platform/lwc/guide/reference-directives.html) - lwc:on directive documentation
- [GraphQL Mutations Guide](https://developer.salesforce.com/docs/platform/graphql/guide/mutations-use.html) - Salesforce GraphQL API
- [TypeScript in LWC Guide](https://developer.salesforce.com/docs/platform/lwc/guide/ts.html) - Official TypeScript documentation
- [@salesforce/lightning-types](https://www.npmjs.com/package/@salesforce/lightning-types) - NPM package for TypeScript types
- [LWC GitHub Releases](https://github.com/salesforce/lwc/releases) - LWC Engine changelog

### Saurabh Samir
**[Medium @saurabh.samirs](https://medium.com/@saurabh.samirs)**

Key contributions:
- lwc:spread directive patterns and best practices
- Dynamic attribute binding techniques
- Object spread and destructuring patterns for LWC

## Key Patterns Incorporated

| Pattern | Source | Description |
|---------|--------|-------------|
| PICKLES Framework | David Picksley | 7-step LWC architecture methodology |
| Render Cycle Helper | James Simone | Jest test utility for async rendering |
| Focus Trap Pattern | James Simone | Modal accessibility with ESC handling |
| GraphQL Wire Adapter | Salesforce Docs | Cursor-based pagination pattern |
| SLDS 2 Styling Hooks | SLDS Guide | `--slds-g-*` CSS variables for dark mode |
| lwc:spread Directive | Saurabh Samir | Dynamic attribute spreading pattern |
| lwc:on Directive | Spring '26 Docs | Dynamic event binding from JavaScript |
| GraphQL Mutations | Spring '26 Docs | `executeMutation` for create/update/delete |
| TypeScript LWC | Spring '26 Docs | Type-safe components with `@salesforce/lightning-types` |
| Complex Template Expressions | Spring '26 (Beta) | JavaScript expressions in templates |
| Agentforce Discoverability | Spring '26 Docs | `lightning__agentforce` capability |

## License

MIT License - See [LICENSE](../../LICENSE)
