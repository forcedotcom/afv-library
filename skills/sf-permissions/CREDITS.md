# Credits & Attribution

## PSLab - Permission Set Lab

This skill was inspired by **PSLab**, an open-source Salesforce permission analysis tool created by **Oumaima Arbani**.

- **GitHub**: [github.com/OumArbani/PSLab](https://github.com/OumArbani/PSLab)
- **Author**: Oumaima Arbani
- **License**: MIT

### What We Learned from PSLab

PSLab's Apex implementation provided the conceptual foundation for this Python-based skill:

1. **Permission Hierarchy Visualization** - The tree structure approach for showing PS/PSG relationships
2. **Permission Detection Queries** - The SOQL patterns for finding "who has access to X"
3. **User Permission Analysis** - The approach to tracing permissions through PSG membership
4. **Setup Entity Access** - How to query Apex class, VF page, and Custom Permission access

### Why Python Instead of Apex?

While PSLab uses Apex deployed to the user's org, this skill uses Python with `simple-salesforce` for several reasons:

1. **No deployment required** - Works with any org via API
2. **Cross-org analysis** - Can compare permissions across multiple orgs
3. **CLI integration** - Fits the Claude Code terminal workflow
4. **Rich TUI output** - Better terminal visualization with the `rich` library

### License Compliance

This skill is a clean-room reimplementation of PSLab's concepts in Python. No code was directly copied. The SOQL query patterns are based on standard Salesforce APIs and are not copyrightable.

---

## Other Resources

### Salesforce Documentation

- [Permission Sets Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.securityImplGuide.meta/securityImplGuide/perm_sets_overview.htm)
- [Permission Set Groups](https://help.salesforce.com/s/articleView?id=sf.perm_set_groups.htm)
- [SetupEntityAccess Object](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_setupentityaccess.htm)

### Libraries Used

- **[simple-salesforce](https://github.com/simple-salesforce/simple-salesforce)** - Salesforce API client for Python (Apache 2.0)
- **[Rich](https://github.com/Textualize/rich)** - Terminal formatting library (MIT)
