# Credits & Acknowledgments

This skill was built upon the collective wisdom of the Salesforce OmniStudio community. We gratefully acknowledge the following authors and resources whose ideas, patterns, and best practices have shaped this skill.

---

## Authors & Contributors

### Jag Valaiyapathy
**sf-skills Project Creator**

Key contributions:
- sf-skills framework architecture and skill patterns
- Scoring rubric design (110-point system)
- Cross-skill orchestration model
- OmniStudio skill suite design

### David Ryan (weytani)
**Primary Contributor — sf-industry-commoncore-integration-procedure** — [GitHub](https://github.com/weytani)

Key contributions:
- Integration Procedure element type reference
- Error handling and rollback patterns
- Caching strategy documentation
- Best practices consolidation

---

## Official Salesforce Resources

### Salesforce OmniStudio Documentation
**[help.salesforce.com](https://help.salesforce.com/s/articleView?id=sf.os_integration_procedures.htm)**

Key contributions:
- Integration Procedure configuration reference
- Element type definitions and PropertySetConfig properties
- OmniProcess data model documentation
- Core namespace migration guidance

### Salesforce Trailhead — OmniStudio Modules
**[trailhead.salesforce.com](https://trailhead.salesforce.com/en/content/learn/modules/omnistudio-integration-procedures)**

Key contributions:
- Integration Procedure fundamentals
- Hands-on exercises for element configuration
- DataRaptor and IP chaining patterns
- OmniStudio Developer certification prep material

### Salesforce Architects
**[architect.salesforce.com](https://architect.salesforce.com/)**

Key contributions:
- OmniStudio architecture patterns
- Performance and scalability guidance
- Enterprise integration strategies

---

## Community Resources

### UnofficialSF Team
**[UnofficialSF.com](https://unofficialsf.com/)**

Key contributions:
- OmniStudio community resources and tutorials
- Integration Procedure pattern documentation
- DataRaptor best practices that inform IP design

### Salesforce Ben
**[salesforceben.com](https://www.salesforceben.com/)**

Key contributions:
- OmniStudio overview articles
- Integration Procedure vs Flow comparison guides
- Practical implementation tutorials

### Salesforce Stack Exchange
**[salesforce.stackexchange.com](https://salesforce.stackexchange.com/)**

Key contributions:
- Community Q&A on Integration Procedure issues
- PropertySetConfig troubleshooting solutions
- DataRaptor-IP integration patterns
- Core namespace migration solutions

### Vlocity / Industries CPQ Community
**Various community blogs and forums**

Key contributions:
- Integration Procedure patterns from Vlocity managed package era
- VlocityOpenInterface implementation patterns
- Enterprise-scale IP orchestration examples
- Migration guidance from Vlocity to OmniStudio Core

---

## Key Concepts Credited

### Element Composition Patterns
The element ordering and composition patterns draw from both Salesforce official documentation and community-established practices for multi-step server-side orchestrations.

### Error Handling and Rollback
The compensating action pattern for IP rollback was established by enterprise implementations where strict data integrity requirements demanded explicit undo logic across independent DML operations.

### Caching Strategies
Platform cache integration patterns for Integration Procedures were documented through community experience with high-volume OmniScript/FlexCard deployments that required performant data retrieval.

### Type/SubType Versioning
The versioning strategy using SubType for IP lifecycle management emerged from enterprise deployment practices managing multiple active versions across sandbox and production environments.

---

## Special Thanks

To the Salesforce OmniStudio community — developers, architects, and consultants — for continuously sharing knowledge about Integration Procedure design, performance optimization, and real-world implementation patterns.

---

*If we've missed anyone whose work influenced this skill, please let us know so we can add proper attribution.*
