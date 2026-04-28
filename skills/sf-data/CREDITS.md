# Credits & Acknowledgments

This skill was built upon the collective wisdom of the Salesforce data and SOQL community. We gratefully acknowledge the following authors and resources whose ideas, patterns, and best practices have shaped this skill.

---

## Authors & Contributors

### Beyond the Cloud
**[blog.beyondthecloud.dev](https://blog.beyondthecloud.dev/)**

Key contributions:
- SOQL optimization techniques
- Bulk data handling patterns
- Query selectivity guidance
- Governor limits best practices

### James Simone
**[Joys of Apex](https://www.jamessimone.net/blog/)**

Key contributions:
- Test data factory patterns
- Selector pattern for data access
- Repository pattern for data abstraction

### Amit Chaudhary
**[Apex Hours](https://www.apexhours.com/)** | **[SalesforceCodex](https://salesforcecodex.com/)**

Key contributions:
- SOQL query optimization
- Bulk API usage patterns
- Data loader best practices

### [August Krys](https://github.com/not2technical)

Key contributions:
- describe-first test-data workflow corrections
- stronger pre-flight validation guidance for required fields, picklists, and createable fields
- bounded retry and manual-fallback patterns for org data setup

---

## Official Salesforce Resources

### Salesforce Documentation
- **SOQL and SOSL Reference**: https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/
- **Bulk API 2.0 Developer Guide**: https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/
- **Data Loader Guide**: https://help.salesforce.com/s/articleView?id=sf.data_loader.htm
- **Query Plan Tool**: https://help.salesforce.com/s/articleView?id=sf.working_with_the_query_plan_tool.htm

### Salesforce Trailhead
- **Apex Database & SOQL**: https://trailhead.salesforce.com/en/content/learn/modules/apex_database
- **Large Data Volumes**: https://trailhead.salesforce.com/en/content/learn/modules/large-data-volumes

---

## Frameworks & Libraries

### fflib Apex Common
- **Repository**: https://github.com/apex-enterprise-patterns/fflib-apex-common
- **Pattern**: Selector Layer for optimized data access

### Apex Mockery
- **Author**: Salesforce
- **Repository**: https://github.com/salesforce/apex-mockery
- **Use**: Mocking data access in unit tests

---

## Community Resources

### Salesforce Ben
**[salesforceben.com](https://www.salesforceben.com/)**
- Data management guides
- Bulk operation tutorials
- Data quality best practices

### Salesforce Stack Exchange
**[salesforce.stackexchange.com](https://salesforce.stackexchange.com/)**
- SOQL optimization discussions
- Bulk data solutions
- Query performance troubleshooting

---

## Key Concepts Credited

### Query Selectivity
The emphasis on indexed fields and selective filters comes from Salesforce's Query Plan Tool documentation and community performance optimization guides.

### Test Data Factory Pattern
The pattern of creating reusable test data factories is widely attributed to the Apex Enterprise Patterns community and documented in fflib.

### 251 Record Testing
The requirement to test with 251+ records (beyond the 200 batch boundary) is a community-established best practice for validating bulk behavior.

---

## Special Thanks

To the Salesforce data architecture community for continuously sharing query optimization techniques, bulk operation patterns, and data integrity best practices.

---

*If we've missed anyone whose work influenced this skill, please let us know so we can add proper attribution.*
