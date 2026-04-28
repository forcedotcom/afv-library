# Credits & Acknowledgments

This skill was built upon the collective wisdom of the Salesforce integration community. We gratefully acknowledge the following authors and resources whose ideas, patterns, and best practices have shaped this skill.

---

## Authors & Contributors

### James Simone
**[Joys of Apex](https://www.jamessimone.net/blog/)**

Key contributions:
- Queueable callout patterns
- Async integration architecture
- Retry and error handling strategies

### Beyond the Cloud
**[blog.beyondthecloud.dev](https://blog.beyondthecloud.dev/)**

Key contributions:
- Named Credential best practices
- External Credential architecture (API 61+)
- Callout governor limits guidance

### Amit Chaudhary
**[Apex Hours](https://www.apexhours.com/)**

Key contributions:
- REST callout patterns
- SOAP integration guidance
- Platform Event design

### Salesforce Architects
**[architect.salesforce.com](https://architect.salesforce.com/)**

Key contributions:
- Integration architecture patterns
- Event-driven architecture designs
- Middleware selection guidance

---

## Official Salesforce Resources

### Documentation
- **Named Credentials Guide**: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_named_credentials.htm
- **External Credentials (API 61+)**: https://help.salesforce.com/s/articleView?id=sf.nc_external_credentials.htm
- **External Services**: https://help.salesforce.com/s/articleView?id=sf.external_services.htm
- **Platform Events Developer Guide**: https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/
- **Change Data Capture Guide**: https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/

### Trailhead
- **Apex Integration Services**: https://trailhead.salesforce.com/en/content/learn/modules/apex_integration_services
- **Platform Events Basics**: https://trailhead.salesforce.com/en/content/learn/modules/platform_events_basics
- **Event-Driven Architecture**: https://trailhead.salesforce.com/en/content/learn/trails/build-event-driven-architectures

---

## Frameworks & Patterns

### MuleSoft Integration Patterns
- **Repository**: https://github.com/mulesoft/anypoint-examples
- **Pattern**: API-led connectivity

### Salesforce Integration Patterns
- **Official Guide**: https://architect.salesforce.com/decision-guides/integration
- **Patterns**: Request-Reply, Fire-and-Forget, Batch Data Sync

---

## Community Resources

### Salesforce Ben
**[salesforceben.com](https://www.salesforceben.com/)**
- Integration tutorials
- Named Credential guides
- External Service patterns

### Unofficial SF
**[unofficialsf.com](https://unofficialsf.com/)**
- Flow HTTP Callout patterns
- External Services examples

### Salesforce Stack Exchange
**[salesforce.stackexchange.com](https://salesforce.stackexchange.com/)**
- Integration troubleshooting
- Callout best practices
- Event-driven discussions

---

## Key Concepts Credited

### Named Credential Architecture
The separation of authentication from authorization in Named Credentials follows Salesforce's modern security architecture introduced in API 61.

### Async Callout Patterns
The requirement to use Queueable or @future for callouts from triggers is documented in official Salesforce limits and best practices.

### Platform Event Design
Event-driven architecture patterns are based on Salesforce's Platform Events documentation and enterprise integration patterns.

### External Service Generation
Auto-generating Apex from OpenAPI/Swagger specs via External Services is a Salesforce platform feature with community-refined usage patterns.

---

## Special Thanks

To the Salesforce integration architecture community for continuously sharing callout patterns, authentication best practices, and event-driven design principles.

---

*If we've missed anyone whose work influenced this skill, please let us know so we can add proper attribution.*
