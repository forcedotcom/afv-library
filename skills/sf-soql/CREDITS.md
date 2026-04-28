# Credits & Acknowledgments

This skill was built upon the collective wisdom of the Salesforce developer community. We gratefully acknowledge the following authors and resources whose ideas, patterns, and best practices have shaped this skill.

---

## Authors & Contributors

### James Simone
**[Joys of Apex](https://www.jamessimone.net/blog/)**

Key contributions:
- Repository Pattern for SOQL abstraction
- Strongly-typed Query Builder concepts
- Testing-focused query design
- Field dependency management

Referenced articles:
- [Repository Pattern](https://www.jamessimone.net/blog/joys-of-apex/repository-pattern/)
- [Strongly Typed Query Builder](https://www.jamessimone.net/blog/joys-of-apex/you-need-a-strongly-typed-query-builder/)
- [Strongly Typed Parent & Child Queries](https://www.jamessimone.net/blog/joys-of-apex/strongly-typed-parent-and-child-queries/)

### Beyond the Cloud (Piotr Gajek)
**[blog.beyondthecloud.dev](https://blog.beyondthecloud.dev/)**

Key contributions:
- Selector Layer architecture concepts
- Query composition over inheritance
- FLS and sharing mode best practices
- Query mocking for unit tests

Referenced articles:
- [Why You Need a Selector Layer](https://blog.beyondthecloud.dev/blog/why-do-you-need-selector-layer)
- [SOQL Lib concepts](https://blog.beyondthecloud.dev/blog/soql-lib) (patterns only, not the library)
- [Salesforce Mock in Apex Tests](https://blog.beyondthecloud.dev/blog/salesforce-mock-in-apex-tests)

### Apex Hours (Amit Chaudhary)
**[apexhours.com](https://www.apexhours.com/)**

Key contributions:
- Governor limits guidance
- SOQL & SOSL performance tuning
- Bulkification patterns
- Anti-pattern documentation

Referenced articles:
- [SOQL & SOSL Performance Tuning](https://www.apexhours.com/soql-sosl-performance-tuning/)
- [Governor Limits in Salesforce](https://www.apexhours.com/governor-limits-in-salesforce/)
- [How to Resolve Too many SOQL Queries 101](https://www.apexhours.com/too-many-soql-queries-101/)
- [Bulkification of Apex Triggers](https://www.apexhours.com/bulkification-of-apex-triggers/)

### Medium Contributors

**Saurabh Samir**
- [5 Bulkification Patterns to Avoid SOQL/DML Limits](https://medium.com/@saurabh.samirs/salesforce-apex-triggers-5-bulkification-patterns-to-avoid-soql-dml-limits-f4e9c8bbfb3a)

---

## Official Salesforce Resources

- **Query Optimization Guide**: [help.salesforce.com - Improve SOQL Query Performance](https://help.salesforce.com/s/articleView?id=000387172)
- **Developer Guide**: [SOQL & SOSL Reference](https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/)
- **Trailhead**: [Apex & .NET Basics - Efficient Database Queries](https://trailhead.salesforce.com/content/learn/modules/database_basics_dotnet/writing_efficient_queries)

---

## Key Patterns Integrated

| Pattern | Source | Integration |
|---------|--------|-------------|
| Selector Layer | Beyond the Cloud | references/selector-patterns.md |
| Bulkification | Apex Hours, Medium | assets/bulkified-query-pattern.cls |
| Anti-patterns | Multiple sources | references/anti-patterns.md |
| Query Plan Analysis | Salesforce Docs | SKILL.md, optimization-patterns.soql |

---

## Philosophy

This skill integrates **concepts and patterns** from community resources, not specific libraries as dependencies. The goal is to teach Apex developers how to write efficient, maintainable SOQL using vanilla Apex patterns that don't require external package installation.

---

*If we've missed anyone whose work influenced this skill, please let us know so we can add proper attribution.*
