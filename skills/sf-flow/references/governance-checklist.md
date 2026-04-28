<!-- Parent: sf-flow/SKILL.md -->
# Flow Governance Checklist

## Overview

This checklist ensures that Salesforce Flows meet enterprise governance standards for security, performance, maintainability, and compliance. Use this before deploying flows to production.

## Pre-Development Phase

### 📋 Requirements Review

- [ ] **Business requirement documented** with clear success criteria
- [ ] **Stakeholders identified** (business owner, technical owner, security reviewer)
- [ ] **Scope defined** (which objects, which scenarios, which users)
- [ ] **Existing automation reviewed** (no conflicts with other flows, process builders, workflows)
- [ ] **Alternative solutions considered** (Apex trigger vs Flow vs declarative field updates)

### 🏗️ Architecture Planning

- [ ] **Orchestration pattern selected** (Parent-Child, Sequential, Conditional, or standalone)
- [ ] **Subflow reuse identified** (can use existing subflows from library?)
- [ ] **Data volume estimated** (how many records will this process?)
- [ ] **Governor limits reviewed** (will this exceed SOQL/DML limits?)
- [ ] **Integration points identified** (external callouts, platform events, Apex actions)

---

## Development Phase

### 💻 Technical Implementation

#### Naming & Organization
- [ ] **Flow name follows convention**: `{Type}_{Object}_{Purpose}` (e.g., `RTF_Account_UpdateIndustry`)
- [ ] **Description is clear and complete** (one-sentence summary of what flow does)
- [ ] **Elements have meaningful names** (no "Decision_0162847" default names)
- [ ] **Variables use type prefixes** (`var` for single, `col` for collection)
- [ ] **API version is current** (66.0 for Spring '26)

#### Performance & Bulkification
- [ ] **No DML inside loops** (CRITICAL - causes bulk failures)
- [ ] **Bulkified operations** (handles collections, not single records)
- [ ] **Transform element used** where applicable (faster than loops for field mapping)
  - Use Transform for: bulk field mapping, collection conversion, simple formulas
  - Use Loop for: per-record IF/ELSE, counters/flags, varying business rules
  - See `references/transform-vs-loop-guide.md` for decision criteria
  - ⚠️ Create Transform in Flow Builder UI, then deploy (complex XML)
- [ ] **SOQL queries minimized** (get all needed data in fewest queries)
- [ ] **Record lookups have appropriate filters** (don't query unnecessary records)

#### Error Handling
- [ ] **All DML operations have fault paths** connected
- [ ] **Fault paths connect to error logging** (Sub_LogError or custom)
- [ ] **Error messages are descriptive** (help with troubleshooting)
- [ ] **Critical failures stop execution** (fail-fast pattern)
- [ ] **Non-critical failures logged but don't block** (fire-and-forget for notifications)

#### Security & Permissions
- [ ] **Running mode documented** (System vs User mode - why?)
- [ ] **Sensitive fields identified** (SSN, credit card, passwords, etc.)
- [ ] **Object access documented** (which objects CREATE/READ/UPDATE/DELETE)
- [ ] **Field-level security considered** (will users have access to all fields?)
- [ ] **No hardcoded credentials** or sensitive data in flow

#### Reusability & Maintainability
- [ ] **Complex logic extracted to subflows** (>200 lines suggests need for subflow)
- [ ] **Subflows are single-purpose** (do one thing well)
- [ ] **Input/output variables clearly defined** (documented with descriptions)
- [ ] **Magic numbers avoided** (use named constants or custom metadata)
- [ ] **Auto-layout enabled** (locationX/Y = 0 for cleaner diffs)

---

## Testing Phase

### 🧪 Unit Testing

- [ ] **Flow tested independently** with representative data
- [ ] **All decision paths tested** (every branch, every outcome)
- [ ] **Error scenarios tested** (what happens when DML fails?)
- [ ] **Edge cases tested** (null values, empty strings, zero quantities)
- [ ] **Variable values verified** at each step (using debug mode)

### 📊 Bulk Testing

- [ ] **Tested with 200+ records** (Data Loader or bulk API)
- [ ] **No governor limit errors** (SOQL, DML, CPU time all under limits)
- [ ] **Performance acceptable** (<5 seconds per batch)
- [ ] **Debug logs reviewed** for warnings or inefficiencies
- [ ] **Simulation mode passed** (if using flow_simulator.py)

### 🔒 Security Testing

- [ ] **Tested with Standard User profile** (most restrictive)
- [ ] **Tested with custom profiles** that have limited object access
- [ ] **Tested with different permission sets** assigned
- [ ] **Verified FLS is respected** (fields without access don't cause errors)
- [ ] **Verified CRUD is respected** (operations without access fail gracefully)

### 🔗 Integration Testing

- [ ] **Tested with related flows** (no conflicts or race conditions)
- [ ] **Tested with existing automation** (Process Builder, Workflow Rules, Apex triggers)
- [ ] **Tested with Apex actions** (if flow calls Apex)
- [ ] **Tested with external integrations** (platform events, HTTP callouts)
- [ ] **End-to-end user acceptance testing** completed

---

## Pre-Production Phase

### 📝 Documentation

- [ ] **Flow documentation generated** (using documentation template)
- [ ] **Dependencies documented** (which subflows, objects, fields are required)
- [ ] **Configuration notes provided** (any required custom settings, metadata)
- [ ] **Rollback plan documented** (how to deactivate if issues arise)
- [ ] **Support documentation created** (for help desk/support team)

### 🔍 Code Review

- [ ] **Peer review completed** (another developer reviewed)
- [ ] **Security review completed** (if accessing sensitive data)
- [ ] **Architecture review completed** (if complex orchestration)
- [ ] **Best practices validated** (all items in this checklist)
- [ ] **Auto-fix recommendations applied** (from enhanced_validator.py)

### 🚦 Deployment Preparation

- [ ] **Deployment plan documented** (sandbox → UAT → production)
- [ ] **Change set or package created** (includes all dependencies)
- [ ] **Validation deployment successful** (--dry-run passed)
- [ ] **Activation strategy defined** (deploy as Draft, activate after monitoring)
- [ ] **Monitoring plan in place** (how to track errors post-deployment)

---

## Production Deployment

### 🚀 Deployment Day

- [ ] **Backup current automation** (export existing flows as reference)
- [ ] **Deploy during low-traffic window** (minimize user impact)
- [ ] **Deploy as Draft initially** (not activated until verified)
- [ ] **Verify deployment successful** (flow appears in Setup → Flows)
- [ ] **Test basic functionality** in production (with test records)

### 🔦 Monitoring

- [ ] **Activate flow** after initial verification
- [ ] **Monitor error logs** (Flow_Error_Log__c or debug logs)
- [ ] **Monitor performance** (Setup → Apex Jobs, flow interview records)
- [ ] **Monitor user feedback** (support tickets, user questions)
- [ ] **Review after 24 hours** (any unexpected behavior?)

### 🛠️ Post-Deployment

- [ ] **Document any issues** encountered during deployment
- [ ] **Update documentation** with production-specific notes
- [ ] **Communicate to users** (release notes, training, announcements)
- [ ] **Schedule follow-up review** (1 week, 1 month)
- [ ] **Archive old automation** (deactivate replaced Process Builders/Workflows)

---

## Ongoing Maintenance

### 📅 Regular Reviews

- [ ] **Monthly error log review** (any recurring failures?)
- [ ] **Quarterly performance review** (execution time trends)
- [ ] **Bi-annual security review** (still appropriate permissions?)
- [ ] **Annual architecture review** (still meets business needs?)
- [ ] **Update for new API versions** (leverage latest features)

### 🔄 Change Management

- [ ] **Change requests tracked** (JIRA, Salesforce cases, etc.)
- [ ] **Impact analysis documented** (what will change affect?)
- [ ] **Testing repeated** for changes (full checklist for major changes)
- [ ] **Version history maintained** (change log in flow description)
- [ ] **Deprecation plan** for old flows (when will they be deactivated?)

---

## Governance Scoring

### Calculate Your Governance Score

Assign points for completed items:
- **Pre-Development**: 10 items × 2 points = 20 points
- **Development**: 25 items × 2 points = 50 points
- **Testing**: 15 items × 3 points = 45 points
- **Pre-Production**: 15 items × 3 points = 45 points
- **Deployment**: 10 items × 2 points = 20 points
- **Ongoing**: 10 items × 2 points = 20 points

**Total Possible**: 200 points

### Governance Rating

| Score | Rating | Description |
|-------|--------|-------------|
| 180-200 | ⭐⭐⭐⭐⭐ Excellent | Enterprise-grade governance |
| 160-179 | ⭐⭐⭐⭐ Very Good | Strong governance with minor gaps |
| 140-159 | ⭐⭐⭐ Good | Acceptable governance, some improvements needed |
| 120-139 | ⭐⭐ Fair | Significant gaps, address before production |
| < 120 | ⭐ Poor | Not ready for production deployment |

**Minimum for Production**: 140+ (Good rating)

---

## Exception Process

### When to Request Exception

Sometimes strict governance isn't feasible. Request exception for:
- **Proof-of-concept flows** (not production-critical)
- **Emergency hotfixes** (security issues, critical bugs)
- **Temporary workarounds** (permanent solution in progress)

### Exception Request Template

```
Flow Name: [Name]
Exception Requested For: [Which checklist items?]
Reason: [Why can't you comply?]
Risk Assessment: [What's the risk of proceeding?]
Mitigation Plan: [How will you reduce risk?]
Timeline: [When will full compliance be achieved?]
Approver: [Who approved this exception?]
```

---

## Quick Reference Guide

### Priority Checks (Must-Do)

✅ **Top 5 Critical Items**:
1. No DML inside loops
2. All DML operations have fault paths
3. Tested with 200+ records (bulk testing)
4. Security testing with Standard User profile
5. Deployment plan and rollback documented

### Common Pitfalls

❌ **Top 5 Common Mistakes**:
1. Deploying directly to production (skip sandbox testing)
2. Activating immediately after deployment (skip verification)
3. No error logging (can't debug production issues)
4. Not testing bulk scenarios (fails with >200 records)
5. Ignoring security implications (system mode without review)

---

## Resources

### Tools
- **enhanced_validator.py**: Comprehensive 6-category validation (includes naming, security, performance, architecture)
- **flow_simulator.py**: Bulk testing simulation

### Documentation
- [Subflow Library](subflow-library.md): Reusable components
- [Orchestration Guide](orchestration-guide.md): Architecture patterns
- [Flow Best Practices](flow-best-practices.md): Security guidelines
- [Architecture Review Template](../assets/architecture-review-template.md): Formal review process

### Salesforce Resources
- [Flow Best Practices](https://help.salesforce.com/s/articleView?id=sf.flow_prep_bestpractices.htm)
- [Flow Limits](https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_flows.htm)
- [Security Guide](https://help.salesforce.com/s/articleView?id=sf.security_overview.htm)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-11-30 | Initial governance checklist |

---

## Support

Questions about this checklist?
1. Review related documentation above
2. Consult with Salesforce architect or admin
3. Request architecture review for complex flows

**Remember**: Governance isn't gatekeeping—it's protecting your org from technical debt, security issues, and poor user experiences. Take the time to do it right! 🛡️
