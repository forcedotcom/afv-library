# Credits & Acknowledgments

This skill family distills publicly shared Data Cloud implementation knowledge into sf-skills house style. Attribution is intentionally explicit because contributor credit is a core sf-skills principle.

---

## Primary Contributor

### Gnanasekaran Thoppae
**Primary contributor for the sf-datacloud family**

Key contributions:
- phase-based Data Cloud skill decomposition
- community `sf data360` CLI command coverage across the Data Cloud lifecycle
- operational gotchas for connections, mappings, identity resolution, search, segmentation, and activation
- practical install and verification workflows for the community runtime

---

## Public upstream sources distilled into this family

### gthoppae/sf-data360-skills
**Repository**: https://github.com/gthoppae/sf-data360-skills

Key contributions:
- Connect / Prepare / Harmonize / Segment / Act / Retrieve skill structure
- orchestration patterns for cross-phase Data Cloud work
- high-signal Data Cloud gotchas and command selection guidance

### gthoppae/sf-cli-plugin-data360
**Repository**: https://github.com/gthoppae/sf-cli-plugin-data360

Key contributions:
- deterministic `sf data360` runtime surface
- command taxonomy spanning connections, streams, DMOs, identity resolution, query, search index, activation, and more
- install, testing, and live-validation patterns for the community CLI

---

## Official Salesforce resources

### Salesforce Architects
- **Data Cloud Reference Architecture**: https://architect.salesforce.com/fundamentals/data-cloud

### Salesforce Documentation
- **Data Cloud Developer Documentation**: https://developer.salesforce.com/docs/data/data-cloud-dev/guide/dc-dev-about.html
- **Data Cloud Query Guide**: https://developer.salesforce.com/docs/data/data-cloud-query-guide/guide/dc-sql.html
- **Segment and activation documentation**: https://help.salesforce.com/

### Trailhead
- **Data Cloud Basics**
- **Identity Resolution**
- **Calculated Insights**
- **Segmentation and Activation**

---

## sf-skills distillation policy for this family

This family intentionally:
- keeps sf-skills naming consistency (`sf-datacloud-*`)
- keeps the external CLI plugin outside this repo
- favors deterministic helper scripts and reusable JSON templates
- rewrites examples into generic sf-skills-style guidance rather than copying workshop-specific payloads

See [UPSTREAM.md](UPSTREAM.md) for the maintenance contract.

---

## Special thanks

To the public Salesforce Data Cloud community for documenting practical patterns around data ingestion, harmonization, identity resolution, segmentation, and retrieval.
