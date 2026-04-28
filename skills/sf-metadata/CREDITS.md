# Credits & Acknowledgments

This skill was built upon the collective wisdom of the Salesforce metadata and schema design community. We gratefully acknowledge the following authors and resources whose ideas, patterns, and best practices have shaped this skill.

---

## Authors & Contributors

### Andy Fawcett
**[Salesforce Lightning Platform Enterprise Architecture](https://www.amazon.com/Lightning-Platform-Enterprise-Architecture-applications/dp/1789956714)**

Key contributions:
- Enterprise architecture patterns
- Schema design principles
- Metadata-driven development approaches

### Beyond the Cloud
**[blog.beyondthecloud.dev](https://blog.beyondthecloud.dev/)**

Key contributions:
- Custom field best practices
- Object relationship patterns
- Validation rule design

### Salesforce Architects
**[architect.salesforce.com](https://architect.salesforce.com/)**

Key contributions:
- Data model design patterns
- Security model architecture
- Multi-tenant schema considerations

### [August Krys](https://github.com/not2technical)

Key contributions:
- corrections that strengthened automatic Permission Set / FLS follow-up for new custom metadata
- emphasis that object permissions do not replace field-level visibility
- practical guidance for eligible-field Permission Set generation

---

## Official Salesforce Resources

### Documentation
- **Metadata API Developer Guide**: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/
- **Object Reference**: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/
- **Custom Metadata Types Guide**: https://developer.salesforce.com/docs/atlas.en-us.custom_metadata_types_devguide.meta/custom_metadata_types_devguide/
- **Permission Sets**: https://help.salesforce.com/s/articleView?id=sf.perm_sets_overview.htm

### Trailhead
- **Data Modeling**: https://trailhead.salesforce.com/en/content/learn/modules/data_modeling
- **Formulas and Validation Rules**: https://trailhead.salesforce.com/en/content/learn/modules/point_click_business_logic
- **Security Model**: https://trailhead.salesforce.com/en/content/learn/modules/data_security

---

## Frameworks & Tools

### sf CLI v2
- **Author**: Salesforce
- **Documentation**: https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/
- Primary tool for metadata operations

### SFDX Project Structure
- **Standard**: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_source_file_format.htm
- Metadata file organization patterns

---

## Community Resources

### Salesforce Ben
**[salesforceben.com](https://www.salesforceben.com/)**
- Schema design guides
- Field type selection tutorials
- Relationship best practices

### Apex Hours
**[apexhours.com](https://www.apexhours.com/)**
- Metadata management tutorials
- Custom metadata type patterns
- Declarative development guides

### Salesforce Stack Exchange
**[salesforce.stackexchange.com](https://salesforce.stackexchange.com/)**
- Schema design discussions
- Metadata API troubleshooting
- Best practice recommendations

---

## Key Concepts Credited

### Field-Level Security
The emphasis on FLS configuration after field deployment is a community-established best practice to ensure data visibility.

### Naming Conventions
Object and field naming conventions follow community standards and official Salesforce recommendations for readability and maintainability.

### Validation Rule Patterns
Formula-based validation patterns are derived from official documentation and refined by community implementations.

### Permission Set Model
The recommendation to use Permission Sets over Profiles for field access follows Salesforce's modern security architecture guidance.

---

## Special Thanks

To the Salesforce administration and architecture community for continuously sharing schema design patterns, security model best practices, and metadata management techniques.

---

*If we've missed anyone whose work influenced this skill, please let us know so we can add proper attribution.*
