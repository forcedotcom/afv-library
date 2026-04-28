# sf-debug Credits & Acknowledgments

This skill incorporates knowledge, patterns, and insights from the Salesforce developer community. We acknowledge and thank the following contributors whose work has shaped this skill.

---

## Primary Sources

### Justus van den Berg
- **Source**: [Medium - Salesforce Apex Heap Size and CPU Time Limit](https://medium.com/@justusvandenberg)
- **Contribution**: Concrete performance benchmarks showing String.join() is 22x faster than string concatenation in loops
- **Key Insights**:
  - String concatenation: 11,767ms for 1,750 rows (then CPU limit hit)
  - String.join(): 539ms for 7,500 rows and still running
  - Heap allocation patterns and memory ceiling behavior
- **Integrated into**: `assets/cpu-heap-optimization.cls`, `references/benchmarking-guide.md`

### James Simone
- **Source**: [Joys of Apex - Benchmarking Matters](https://www.jamessimone.net/blog/joys-of-apex/benchmarking-matters/)
- **Contribution**: Dan Appleman's benchmarking technique for reliable performance testing
- **Key Insights**:
  - Use anonymous Apex for consistent test environment
  - Run multiple iterations to average out variance
  - System.currentTimeMillis() for accurate timing
  - Importance of testing with production-scale data
- **Integrated into**: `assets/benchmarking-template.cls`, `references/benchmarking-guide.md`

### Beyond the Cloud
- **Source**: [Beyond the Cloud - CPU Benchmarking](https://blog.beyondthecloud.dev/)
- **Contribution**: Loop performance analysis and iterator patterns
- **Key Insights**:
  - While loop outperforms enhanced for-loop at scale
  - Iterator caching reduces overhead
  - 10,000+ iteration benchmark data
- **Integrated into**: `references/benchmarking-guide.md`

### Apex Log Analyzer
- **Source**: [VS Code Marketplace - Apex Log Analyzer](https://marketplace.visualstudio.com/items?itemName=FinancialForce.lana)
- **Contribution**: Recommended tooling for log analysis
- **Key Features**:
  - Flame charts for visualizing method execution time
  - Call tree analysis
  - Database operation highlighting
  - Free and open-source
- **Integrated into**: `references/log-analysis-tools.md`, SKILL.md recommendations

### Dan Appleman (Advanced Apex Programming)
- **Source**: Advanced Apex Programming for Salesforce.com and Force.com (Book)
- **Contribution**: Foundational benchmarking methodology
- **Note**: Techniques referenced via James Simone's blog adaptation
- **Integrated into**: `assets/benchmarking-template.cls`

---

## Salesforce Official Resources

### Apex Developer Guide
- **Source**: [Salesforce Apex Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/)
- **Contribution**: Governor limit values, debug log event types
- **Integrated into**: `references/debug-log-reference.md`, SKILL.md

### Debug Log Reference
- **Source**: [Salesforce Debug Log Reference](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_debugging_debug_log.htm)
- **Contribution**: Official log event specifications
- **Integrated into**: `references/debug-log-reference.md`

---

## Community Knowledge

### Apex Hours (Amit Chaudhary)
- **Source**: [Apex Hours - Governor Limits](https://www.apexhours.com/)
- **Contribution**: Governor limit explanations and optimization strategies
- **Integrated into**: SKILL.md governor limit section

---

## How We Integrate Content

1. **Attribution**: All sources are credited in this file with direct links
2. **JSDoc Comments**: Templates include `@see` references to source blogs
3. **Documentation**: Docs reference original articles for deeper reading
4. **Transformation**: Blog concepts are adapted into reusable templates

---

## License

This skill is MIT licensed. Individual blog posts and external resources retain their original licenses. We encourage users to visit the original sources for the full context and additional insights.

---

*Last updated: December 2024*
