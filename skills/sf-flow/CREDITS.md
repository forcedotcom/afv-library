# Credits & Acknowledgments

This skill was built upon the collective wisdom of the Salesforce Flow community. We gratefully acknowledge the following authors and resources whose ideas, patterns, and best practices have shaped this skill.

---

## Authors & Contributors

### Jennifer Lee
**[Jenwlee.com](https://jenwlee.com/)** | **[YouTube](https://www.youtube.com/@Jenwlee)**

Key contributions:
- Flow best practices and design patterns
- Admin-focused Flow tutorials
- Salesforce Admin Evangelist insights
- Flow troubleshooting techniques

### UnofficialSF Team
**[UnofficialSF.com](https://unofficialsf.com/)**

Key contributions:
- Advanced Flow components and patterns
- Flow action library
- Lightning Flow community resources
- Screen Flow best practices

### Alex Edelstein
**VP of Product at Salesforce** | **UnofficialSF Co-founder**

Key contributions:
- Flow product vision and roadmap
- Advanced automation patterns
- Flow architecture best practices

### Amit Chaudhary
**[Apex Hours](https://www.apexhours.com/)** | **[SalesforceCodex](https://salesforcecodex.com/)**

Key contributions:
- Flow bulkification patterns
- Flow governor limits guidance
- Flow testing strategies
- Record-triggered flow best practices

### Sarah Pilzer
**Flow Expert & Community Contributor**

Key contributions:
- Loops in Flows optimization
- Collection variable patterns
- Flow performance optimization

### Beyond the Cloud
**[blog.beyondthecloud.dev](https://blog.beyondthecloud.dev/)**

Key contributions:
- Flow bulkification techniques
- Performance optimization patterns
- Best practices for record-triggered flows
- Governor limits awareness

### Neil Hohmann
**Salesforce Community Expert**

Key contributions:
- Flow architecture patterns
- Complex flow design strategies
- Subflow best practices

### Mermaid2SF Project
**[github.com/krukmat/Mermaid2SF](https://github.com/krukmat/Mermaid2SF)** | Author: Matias Kruk

Key contributions:
- Flow XML generation patterns (connector-based linking)
- Wait element structure (Duration, Date, Condition types)
- Deterministic XML output (alphabetical sorting for git-friendly diffs)
- Auto-layout coordinate patterns (locationX/Y = 0)
- Loop element connector structure (nextValueConnector, noMoreValuesConnector)

Research conducted December 2024 to identify Flow XML patterns for template improvements.

### Google Flow Lens
**[github.com/google/flow-lens](https://github.com/google/flow-lens)**

Key contributions:
- Flow XML → UML/Mermaid visualization patterns
- Flow structure analysis approaches
- Anti-pattern detection strategies

### Jalumchi Akpoke
**[LinkedIn](https://www.linkedin.com/in/jalumchi-akpoke/)** | 2X Salesforce Certified

Key contributions:
- Transform vs Loop decision pattern documentation
- Data mapping vs decision-making distinction
- Visual comparison of Loop+Assignment vs Transform flow patterns

Inspired by: **Shubham Bhardwaj** (YouTube video referenced in original post)

### Flow Best Practices Gap Analysis (January 2026)
**Community Consensus Best Practices**

Key contributions (added to `flow-best-practices.md`):
- "When NOT to Use Flow" — choosing Formula Fields, Validation Rules, Roll-Up Summary Fields over Flow when appropriate
- "Pre-Development Planning" — flowcharting and requirements documentation before building
- "When to Escalate to Apex" — recognizing when Invocable Apex is the better tool
- "Indexed Fields for Large Data Volumes" — query optimization for 100K+ record objects
- "Custom Metadata for Business Logic" — externalizing thresholds and settings
- "Flow & Element Descriptions" — Agentforce discoverability and maintenance documentation

Sources: Salesforce official documentation, Salesforce Architects guidance, Trailhead modules, community consensus from Salesforce Stack Exchange, and published Flow best practice articles.

---

## Official Salesforce Resources

- **Salesforce Flow Documentation**: https://help.salesforce.com/s/articleView?id=sf.flow.htm
- **Trailhead Flow Modules**: https://trailhead.salesforce.com/en/content/learn/trails/automate_business_processes
- **Salesforce Architects Blog**: https://architect.salesforce.com/
- **Flow Release Notes**: https://help.salesforce.com/s/articleView?id=release-notes.rn_forcecom_flow.htm

---

## Community Resources

### Salesforce Ben
**[salesforceben.com](https://www.salesforceben.com/)** | Founder: Ben McCarthy

Key contributions:
- Flow tutorials and guides
- Flow vs Process Builder comparisons
- Best practice articles
- [Flow Cheat Sheet](https://www.salesforceben.com/salesforce-flow-cheat-sheet-examples-infographic/) - Flow type selection, element reference, variable types
- [Using Custom Metadata to Build Dynamic, Scalable Flows](https://www.salesforceben.com/using-custom-metadata-to-build-dynamic-scalable-flows-in-salesforce/) - Two access patterns (Formula vs Get Records), ID storage warnings, migration checklist for hard-coded values (January 2026)

### Automation Champion
**[automationchampion.com](https://automationchampion.com/)**
- Flow automation patterns
- Record-triggered flow guides
- Screen flow examples

### Salesforce Stack Exchange
**[salesforce.stackexchange.com](https://salesforce.stackexchange.com/)**
- Community Q&A on Flow issues
- Best practice discussions
- Troubleshooting solutions

---

## Key Concepts Credited

### Bulkification Patterns
The concept of bulkifying flows to handle 200+ records efficiently comes from community best practices established by multiple contributors including Amit Chaudhary, Beyond the Cloud, and official Salesforce guidance.

### Auto-Layout Best Practices
The recommendation to use locationX/Y = 0 for cleaner git diffs originated from DevOps-focused community discussions about Flow metadata management.

### Fault Path Requirements
The emphasis on fault paths for all DML operations comes from production reliability patterns shared across the Salesforce admin and developer communities.

### XML Element Ordering
The strict alphabetical ordering requirement for Flow XML elements was documented by community members experiencing deployment issues and validated against Salesforce metadata API requirements.

---

## Special Thanks

To the entire Salesforce Flow community—admins, developers, architects, and MVPs—for continuously sharing knowledge, creating tutorials, and helping each other build better automations.

---

*If we've missed anyone whose work influenced this skill, please let us know so we can add proper attribution.*
