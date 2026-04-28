# Credits & Acknowledgments

This skill was built upon the collective wisdom of the Salesforce DevOps community. We gratefully acknowledge the following authors, tools, and resources whose ideas and best practices have shaped this skill.

---

## Authors & Contributors

### Cloudity / sfdx-hardis Team
**[sfdx-hardis](https://github.com/hardisgroupcom/sfdx-hardis)** | **[Cloudity](https://cloudity.com/)**

Key contributions:
- Salesforce CI/CD tooling and patterns
- Deployment automation best practices
- Git-based DevOps workflows
- Metadata management strategies

### Matt Robison
**[Medium @matt.robison](https://medium.com/@matt.robison)**

Key contributions:
- CI/CD pipeline implementation guides
- GitHub Actions for Salesforce deployments
- Deployment automation patterns
- Test execution strategies

### Pablo / Salto
**[HappySoup.io](https://happysoup.io/)** | **[Salto](https://www.salto.io/)**

Key contributions:
- Metadata dependency management
- Deployment impact analysis
- DevOps tooling innovations
- Configuration management patterns

### Beyond the Cloud
**[blog.beyondthecloud.dev](https://blog.beyondthecloud.dev/)**

Key contributions:
- CI/CD tutorial series
- Deployment pipeline patterns
- Test class best practices
- Code coverage strategies

### Andrew Fawcett
**Salesforce Distinguished Technical Architect**

Key contributions:
- Enterprise deployment patterns
- Package development strategies
- Metadata API expertise
- Salesforce DX foundations

### [August Krys](https://github.com/not2technical)

Key contributions:
- deployment workflow corrections discovered through hands-on build experience
- clearer post-validation handoff guidance for permission assignment, test data, and smoke checks
- stronger sequencing between metadata deployment and downstream data setup

---

## Tools & Frameworks

### Salesforce CLI (sf v2)
- **Maintainer**: Salesforce
- **Repository**: https://github.com/salesforcecli/cli
- The foundation of all deployment operations in this skill

### CumulusCI
- **Maintainer**: Salesforce.org
- **Repository**: https://github.com/SFDO-Tooling/CumulusCI
- Influenced CI/CD workflow patterns

### sfdx-hardis
- **Maintainer**: Cloudity (Hardis Group)
- **Repository**: https://github.com/hardisgroupcom/sfdx-hardis
- License: AGPL-3.0
- Extensive CI/CD automation patterns

### GitHub Actions for Salesforce
- **Community**: Various contributors
- Deployment workflow templates and patterns

---

## Official Salesforce Resources

- **Salesforce CLI Documentation**: https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/
- **Salesforce DX Developer Guide**: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/
- **Metadata API Developer Guide**: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/
- **Salesforce DevOps Center**: https://help.salesforce.com/s/articleView?id=sf.devops_center_overview.htm
- **Trailhead DevOps Modules**: https://trailhead.salesforce.com/en/content/learn/trails/build-applications-with-cicd-on-salesforce

---

## Community Resources

### Salesforce Ben
**[salesforceben.com](https://www.salesforceben.com/)**
- DevOps tutorials and comparisons
- Deployment strategy guides
- CI/CD tool reviews

### SFXD Discord
**[SFXD Community](https://sfxd.github.io/)**
- Real-time DevOps discussions
- Troubleshooting support
- Best practice sharing

### Salesforce Stack Exchange
**[salesforce.stackexchange.com](https://salesforce.stackexchange.com/)**
- Community Q&A on deployment issues
- CLI troubleshooting
- Best practice discussions

### Apex Hours
**[apexhours.com](https://www.apexhours.com/)**
- Deployment webinars
- CI/CD tutorials
- Testing best practices

---

## Key Concepts Credited

### Two-Phase Deployment Pattern
The `--dry-run` validation before actual deployment pattern is a community-established best practice to prevent production failures, widely promoted across DevOps blogs and official Salesforce documentation.

### Quick Deploy Strategy
The workflow of validating with tests, then using quick deploy for actual deployment, originated from Salesforce release management best practices.

### Test Level Recommendations
The guidance on appropriate test levels (RunLocalTests vs RunAllTests vs RunSpecifiedTests) comes from community experience and official Salesforce deployment documentation.

### Incremental Deployment Strategy
The recommendation for small, frequent deployments over large batches is a DevOps industry best practice adapted for Salesforce by the community.

---

## Special Thanks

To the entire Salesforce DevOps community—release managers, architects, developers, and CI/CD engineers—for continuously improving deployment practices, building amazing tools, and sharing knowledge to make Salesforce deployments more reliable.

---

*If we've missed anyone whose work influenced this skill, please let us know so we can add proper attribution.*
