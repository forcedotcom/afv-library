# Credits & Acknowledgments

This skill was built upon the collective wisdom of the Salesforce developer community. We gratefully acknowledge the following authors and resources whose ideas, patterns, and best practices have shaped this skill.

---

## Authors & Contributors

### James Simone
**[Joys of Apex](https://www.jamessimone.net/blog/)**

Key contributions:
- DML mocking pattern for fast tests
- Factory pattern for dependency injection
- Performant Apex test strategies
- Stub ID generation for test isolation

Referenced articles:
- [Mocking DML](https://www.jamessimone.net/blog/joys-of-apex/mocking-dml/)
- [Writing Performant Apex Tests](https://www.jamessimone.net/blog/joys-of-apex/writing-performant-apex-tests/)
- [Dependency Injection & Factory Pattern](https://www.jamessimone.net/blog/joys-of-apex/dependency-injection-factory-pattern/)
- [Mocking Apex History Records](https://www.jamessimone.net/blog/joys-of-apex/mocking-apex-history-records/)
- [Testing Custom Permissions](https://www.jamessimone.net/blog/joys-of-apex/testing-custom-permissions/)

### Beyond the Cloud (Piotr Gajek)
**[blog.beyondthecloud.dev](https://blog.beyondthecloud.dev/)**

Key contributions:
- Mocking vs Stubbing distinction
- Test Data Factory pattern with fluent interface
- Selector layer mocking strategies
- Query result mocking

Referenced articles:
- [Salesforce Mock in Apex Tests](https://blog.beyondthecloud.dev/blog/salesforce-mock-in-apex-tests)
- [Apex Test Data Factory](https://blog.beyondthecloud.dev/blog/apex-test-data-factory)
- [Why You Need a Selector Layer](https://blog.beyondthecloud.dev/blog/why-do-you-need-selector-layer)

### Apex Hours (Amit Chaudhary)
**[apexhours.com](https://www.apexhours.com/)**

Key contributions:
- Mocking framework fundamentals
- HttpCalloutMock patterns
- Test class best practices

Referenced articles:
- [Mocking Apex Tests](https://www.apexhours.com/mocking-apex-tests/)
- [Test Class Best Practices](https://www.apexhours.com/apex-test-class-best-practices/)
- [Testing Web Services Callouts](https://www.apexhours.com/testing-web-services-callouts-in-salesforce/)

---

## Official Salesforce Resources

- **Testing Best Practices**: [developer.salesforce.com/docs](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing_best_practices.htm)
- **StubProvider Interface**: [Apex Reference Guide](https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_interface_System_StubProvider.htm)
- **HttpCalloutMock Guide**: [Testing HTTP Callouts](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_restful_http_testing_httpcalloutmock.htm)
- **Trailhead**: [Apex Unit Testing](https://trailhead.salesforce.com/content/learn/modules/apex_testing)
- **Trailhead**: [Mock and Stub Objects](https://trailhead.salesforce.com/content/learn/modules/unit-testing-on-the-lightning-platform/mock-stub-objects)

---

## Key Patterns Integrated

| Pattern | Source | Integration |
|---------|--------|-------------|
| DML Mocking | James Simone | assets/dml-mock.cls |
| Mocking vs Stubbing | Beyond the Cloud | references/mocking-patterns.md |
| Test Data Factory | Beyond the Cloud | references/test-data-factory-guide.md |
| HttpCalloutMock | Apex Hours | assets/http-mock-response.cls |
| StubProvider | Salesforce Docs | assets/stub-provider-example.cls |
| Performant Tests | James Simone | references/performance-optimization.md |

---

## Philosophy

This skill integrates **concepts and patterns** from community resources, teaching Apex developers how to write fast, reliable, maintainable tests. The goal is to move beyond "75% coverage" toward true unit testing with proper isolation and mocking.

---

*If we've missed anyone whose work influenced this skill, please let us know so we can add proper attribution.*
