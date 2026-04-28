# Credits

## sf-industry-commoncore-flexcard Skill

Primary Contributor: [David Ryan (weytani)](https://github.com/weytani)

## References & Inspiration

### Primary Inspiration

- **@salesforce/omnistudio-mcp** - Official Salesforce OmniStudio MCP server for FlexCard metadata authoring and validation. This is the primary inspiration for the skill's data source binding patterns and definition structure.
- **sf-explorer/omnistudio-mcp-server** - Community OmniStudio MCP server focused on dependency analysis across FlexCards, Integration Procedures, and OmniScripts.

### Official Salesforce Documentation

- [OmniStudio FlexCards Trailhead](https://trailhead.salesforce.com/content/learn/modules/omnistudio-flexcards) - Official Trailhead module covering FlexCard fundamentals
- [OmniStudio Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/omnistudio_flexcards.htm) - Technical reference for OmniUiCard metadata
- [Salesforce Industries Help](https://help.salesforce.com/s/articleView?id=sf.os_flexcards.htm) - FlexCard configuration and administration guide
- [OmniStudio Data Sources](https://help.salesforce.com/s/articleView?id=sf.os_flexcards_data_sources.htm) - Data source types and configuration

### Salesforce Industries Engineering

- Salesforce Industries engineering team for the OmniStudio platform, FlexCard runtime, and declarative data binding framework

### Trailhead Learning Resources

- [Build OmniStudio FlexCards](https://trailhead.salesforce.com/content/learn/modules/omnistudio-flexcards) - Hands-on FlexCard creation
- [OmniStudio Integration Procedures](https://trailhead.salesforce.com/content/learn/modules/omnistudio-integration-procedures) - Companion module for data source IPs
- [OmniStudio OmniScripts](https://trailhead.salesforce.com/content/learn/modules/omnistudio-omniscripts) - Companion module for OmniScript actions

## Key Patterns Incorporated

| Pattern | Source | Description |
|---------|--------|-------------|
| IP Data Source Binding | @salesforce/omnistudio-mcp | Integration Procedure merge field mapping |
| Dependency Analysis | sf-explorer/omnistudio-mcp-server | Cross-component dependency chain validation |
| Card Layout Patterns | Salesforce Industries Docs | Single, list, tabbed, and flyout card types |
| OmniScript Launch Actions | OmniStudio Trailhead | Action button configuration for guided processes |
| Conditional Visibility | OmniStudio Developer Guide | Data-driven show/hide rules for fields and states |
| 130-Point Scoring Rubric | David Ryan (weytani) | Validation framework across 7 quality categories |

## License

MIT License - See [LICENSE](../../LICENSE)
