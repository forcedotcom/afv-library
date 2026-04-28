# Credits & Acknowledgments

This skill was built upon the collective knowledge of the Salesforce OmniStudio community. We gratefully acknowledge the following tools, teams, and resources whose work informed and shaped this skill.

---

## Tools & Projects

### sf-explorer/omnistudio-mcp-server
**Community OmniStudio dependency analyzer**

Key contributions:
- Dependency graph construction patterns for OmniStudio components
- Cross-component traversal algorithms
- Impact analysis methodology for OmniScript, IP, FlexCard, and Data Mapper changes

### @salesforce/omnistudio-mcp (Official)
**Salesforce official FlexCard MCP server**

Key contributions:
- FlexCard Definition JSON schema reference
- Data source type definitions and parsing patterns
- Child card and action configuration structures

---

## Salesforce Teams

### Salesforce Industries Engineering
**OmniStudio platform development team**

Key contributions:
- Core namespace object model (OmniProcess, OmniUiCard, OmniDataTransform, OmniProcessElement)
- PropertySetConfig and Definition JSON schema design
- Namespace migration architecture (Vlocity → Core)
- `IsIntegrationProcedure` boolean discriminator on `OmniProcess` for distinguishing OmniScripts from Integration Procedures

---

## Official Salesforce Resources

### OmniStudio Documentation
- **OmniStudio Developer Guide**: https://developer.salesforce.com/docs/atlas.en-us.omnistudio.meta/omnistudio/
- **Industries Data Model Reference**: https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/
- **OmniStudio Standard Objects**: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_omniprocess.htm

### Trailhead Content
- **OmniStudio Trailhead Module**: https://trailhead.salesforce.com/content/learn/modules/omnistudio-components
- **Build OmniScripts Trail**: https://trailhead.salesforce.com/content/learn/trails/build-omnistudio-omniscripts
- **Build Integration Procedures Trail**: https://trailhead.salesforce.com/content/learn/modules/omnistudio-integration-procedures
- **Build FlexCards Trail**: https://trailhead.salesforce.com/content/learn/modules/omnistudio-flexcards

---

## Community Resources

### Salesforce Stack Exchange
**[salesforce.stackexchange.com](https://salesforce.stackexchange.com/)**
- OmniStudio namespace detection discussions
- PropertySetConfig parsing techniques
- Cross-component dependency questions and solutions

### Salesforce Ben
**[salesforceben.com](https://www.salesforceben.com/)**
- OmniStudio architecture overviews
- Migration guides for Vlocity to Core namespace

---

## Key Concepts Credited

### Namespace Detection via SOQL Probing
The pattern of probing `SELECT COUNT() FROM OmniProcess` (and Vlocity equivalents) to detect the installed namespace is a community-established practice for OmniStudio tooling.

### BFS Dependency Traversal
The breadth-first search algorithm for dependency graph construction follows standard graph traversal patterns adapted for OmniStudio's JSON-embedded reference model.

### Mermaid Visualization for Dependencies
The use of Mermaid diagrams for OmniStudio dependency visualization follows patterns from the sf-diagram-mermaid skill and the broader documentation-as-code community.

---

## Contributor

### David Ryan (weytani)
**Primary Contributor** — [GitHub](https://github.com/weytani)
- Namespace mapping research and validation
- Dependency extraction algorithm design
- Cross-skill orchestration pattern (sf-industry-commoncore-omnistudio-analyze → sf-industry-commoncore-datamapper → sf-industry-commoncore-integration-procedure → sf-industry-commoncore-omniscript → sf-industry-commoncore-flexcard)

---

## Special Thanks

To the Salesforce Industries engineering team for the Core namespace migration that unified OmniStudio's object model, and to the OmniStudio community for sharing namespace detection patterns and dependency analysis techniques that made this skill possible.

---

*If we've missed anyone whose work influenced this skill, please let us know so we can add proper attribution.*
