# Flow Architecture Review Template

## Overview

**Flow Name**: [e.g., RTF_Account_IndustryChange_Orchestrator]
**Requested By**: [Developer Name]
**Request Date**: [YYYY-MM-DD]
**Target Deployment**: [Sandbox / UAT / Production]
**Review Type**: [ ] New Flow  [ ] Major Change  [ ] Security Review

---

## 1. Business Context

### 1.1 Business Requirement
**What business problem does this flow solve?**

[Describe the problem in 2-3 sentences]

**Success Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

### 1.2 Users Impacted
**Who will be affected by this flow?**

- **User Profiles**: [List profiles]
- **User Count**: [Approximate number]
- **User Locations**: [Geography, timezone considerations]

### 1.3 Business Impact
**What's the impact if this flow fails?**

- [ ] **Critical**: Blocks core business process
- [ ] **High**: Significant inconvenience, workaround available
- [ ] **Medium**: Minor inconvenience, limited scope
- [ ] **Low**: Nice-to-have, minimal impact

---

## 2. Technical Design

### 2.1 Flow Type & Trigger
**Type**: [ ] Record-Triggered  [ ] Screen  [ ] Autolaunched  [ ] Scheduled  [ ] Platform Event

**Trigger Details** (if applicable):
- **Object**: [e.g., Account]
- **Trigger Type**: [ ] Before-Save  [ ] After-Save  [ ] Before-Delete
- **Trigger Conditions**: [When does it fire?]
- **Expected Volume**: [Records per day/hour]

### 2.2 Architecture Pattern
**Which orchestration pattern is used?**

- [ ] **Standalone**: Single flow, no subflows
- [ ] **Parent-Child**: Orchestrator + multiple children
- [ ] **Sequential**: Pipeline of dependent steps
- [ ] **Conditional**: Router to specialized handlers

**Architecture Diagram** (if complex):
```
[Draw or describe flow structure]
Parent Flow
├── Child A
├── Child B
└── Child C
```

### 2.3 Dependencies
**What does this flow depend on?**

**Subflows**:
- [ ] Sub_LogError
- [ ] Sub_SendEmailAlert
- [ ] [Other subflows]

**Objects & Fields**:
- **Read**: [Object.Field, Object.Field]
- **Create**: [Object]
- **Update**: [Object.Field, Object.Field]
- **Delete**: [Object]

**External Integrations**:
- [ ] Apex Classes: [List]
- [ ] Platform Events: [List]
- [ ] HTTP Callouts: [Endpoints]
- [ ] None

**Custom Metadata/Settings**:
- [ ] [List any configuration dependencies]

---

## 3. Performance & Scalability

### 3.1 Volume Assessment
**Current Data Volume**:
- Records processed per day: [Number]
- Records processed per hour (peak): [Number]
- Average records per transaction: [Number]

**Future Growth**:
- Expected volume in 6 months: [Number]
- Expected volume in 12 months: [Number]
- Growth assumptions: [Describe]

### 3.2 Governor Limits Analysis
**Estimated Resource Usage**:
- SOQL Queries: [Number] / 100 limit
- DML Statements: [Number] / 150 limit
- DML Rows: [Number] / 10,000 limit
- CPU Time: [Milliseconds] / 10,000ms limit
- Subflow Depth: [Number] / 50 limit

**Bulk Testing**:
- [ ] Tested with 200+ records
- [ ] No governor limit errors
- [ ] Performance acceptable (<5 seconds per batch)
- [ ] Simulation mode passed

### 3.3 Optimization
**Performance Optimizations Applied**:
- [ ] No DML inside loops
- [ ] Transform element used (instead of loops)
- [ ] SOQL queries minimized
- [ ] Bulkified operations
- [ ] [Other optimizations]

**Identified Bottlenecks**:
[If any, describe and mitigation plan]

---

## 4. Security & Governance

### 4.1 Security Context
**Running Mode**:
- [ ] **User Mode** (respects FLS/CRUD - default)
- [ ] **System Mode with Sharing** (bypasses FLS/CRUD but respects sharing)
- [ ] **System Mode without Sharing** (bypasses all security)

**If System Mode, justification**:
[Why is System Mode required for this use case?]

### 4.2 Data Access
**Sensitive Data Accessed**:
- [ ] No sensitive data
- [ ] SSN / Tax ID
- [ ] Credit Card / Payment Info
- [ ] Health Information (PHI)
- [ ] Other: [Describe]

**Compliance Requirements**:
- [ ] GDPR
- [ ] HIPAA
- [ ] SOX
- [ ] PCI-DSS
- [ ] None
- [ ] Other: [Describe]

### 4.3 Permission Testing
**Testing Completed**:
- [ ] Standard User profile
- [ ] Custom restricted profiles
- [ ] Different permission sets
- [ ] Verified FLS respected
- [ ] Verified CRUD respected

**Security Review**:
- [ ] Security team review completed
- [ ] Reviewed by: [Name]
- [ ] Review date: [YYYY-MM-DD]

---

## 5. Error Handling & Observability

### 5.1 Error Handling
**Fault Paths**:
- [ ] All DML operations have fault paths
- [ ] Fault paths connect to error logging
- [ ] Critical failures stop execution
- [ ] Non-critical failures logged but don't block

**Error Logging**:
- [ ] Uses Sub_LogError subflow
- [ ] Custom error logging
- [ ] Logs to: [Object/System]

### 5.2 Monitoring & Alerting
**How will errors be detected?**
- [ ] Flow_Error_Log__c custom object
- [ ] Debug logs
- [ ] Platform Events
- [ ] Email notifications
- [ ] Slack/Teams alerts
- [ ] Other: [Describe]

**Who receives error alerts?**
- [Names/Teams/Distribution Lists]

### 5.3 Debugging
**Troubleshooting Plan**:
- **Primary Contact**: [Name/Email]
- **Backup Contact**: [Name/Email]
- **Documentation**: [Link to flow documentation]
- **Common Issues**: [Known issues and solutions]

---

## 6. Testing & Quality Assurance

### 6.1 Testing Completed
**Unit Testing**:
- [ ] All decision paths tested
- [ ] Error scenarios tested
- [ ] Edge cases tested
- [ ] Variable values verified

**Integration Testing**:
- [ ] Tested with related flows
- [ ] Tested with existing automation
- [ ] End-to-end user acceptance testing

**Bulk Testing**:
- [ ] 200+ records tested
- [ ] No governor limit errors
- [ ] Performance acceptable

**Security Testing**:
- [ ] Different profiles tested
- [ ] Permission edge cases tested

### 6.2 Test Evidence
**Test Results Summary**:
[Link to test results, screenshots, debug logs]

**Known Issues**:
[List any known issues and workarounds]

---

## 7. Deployment Plan

### 7.1 Deployment Strategy
**Deployment Path**:
- [ ] Dev Sandbox → Full Sandbox → UAT → Production
- [ ] Direct to Sandbox
- [ ] Other: [Describe]

**Deployment Method**:
- [ ] Change Set
- [ ] Metadata API
- [ ] DevOps Center
- [ ] VS Code Deployment
- [ ] Other: [Describe]

**Activation Strategy**:
- [ ] Deploy as Draft, activate after verification
- [ ] Activate immediately (emergency only)
- [ ] Phased activation (pilot users first)

### 7.2 Rollback Plan
**If issues arise, how to rollback?**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Rollback Risk Assessment**:
- [ ] **Low**: Can deactivate with no impact
- [ ] **Medium**: Deactivation may affect some users
- [ ] **High**: Difficult to rollback, extensive impacts

### 7.3 Communication Plan
**Who needs to be informed?**
- [ ] End users
- [ ] Support team
- [ ] Business stakeholders
- [ ] IT operations

**Communication Timeline**:
- [X days before]: Announcement
- [Deployment day]: Status updates
- [X days after]: Success confirmation

---

## 8. Maintenance & Ownership

### 8.1 Ownership
**Technical Owner**: [Name/Email]
**Business Owner**: [Name/Email]
**Team**: [Team Name]

### 8.2 Documentation
**Documentation Links**:
- Flow Documentation: [Link]
- User Guide: [Link]
- Support Documentation: [Link]

### 8.3 Maintenance Schedule
**Regular Reviews**:
- Monthly error log review: [Owner]
- Quarterly performance review: [Owner]
- Annual security review: [Owner]

---

## 9. Risk Assessment

### 9.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| [Risk 1] | High/Med/Low | High/Med/Low | [How to mitigate] |
| [Risk 2] | High/Med/Low | High/Med/Low | [How to mitigate] |
| [Risk 3] | High/Med/Low | High/Med/Low | [How to mitigate] |

### 9.2 Business Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| [Risk 1] | High/Med/Low | High/Med/Low | [How to mitigate] |
| [Risk 2] | High/Med/Low | High/Med/Low | [How to mitigate] |

### 9.3 Overall Risk Rating
- [ ] **Low Risk**: Proceed with deployment
- [ ] **Medium Risk**: Address mitigations before deployment
- [ ] **High Risk**: Requires additional review/approval

---

## 10. Review & Approval

### 10.1 Reviewer Feedback

**Technical Reviewer**: [Name/Email]
**Review Date**: [YYYY-MM-DD]

**Comments**:
[Feedback from technical reviewer]

**Decision**:
- [ ] **Approved**: Ready for deployment
- [ ] **Approved with Conditions**: [List conditions]
- [ ] **Rejected**: Requires changes: [List required changes]

---

### 10.2 Security Reviewer Feedback
*(Required if accessing sensitive data or using System Mode)*

**Security Reviewer**: [Name/Email]
**Review Date**: [YYYY-MM-DD]

**Comments**:
[Feedback from security reviewer]

**Decision**:
- [ ] **Approved**: No security concerns
- [ ] **Approved with Conditions**: [List conditions]
- [ ] **Rejected**: Security issues must be addressed

---

### 10.3 Architecture Reviewer Feedback
*(Required for complex orchestrations or critical business processes)*

**Architecture Reviewer**: [Name/Email]
**Review Date**: [YYYY-MM-DD]

**Comments**:
[Feedback from architecture reviewer]

**Decision**:
- [ ] **Approved**: Architecture is sound
- [ ] **Approved with Recommendations**: [List recommendations]
- [ ] **Rejected**: Architecture needs redesign

---

### 10.4 Final Approval

**Approver**: [Name/Title]
**Approval Date**: [YYYY-MM-DD]

**Final Decision**:
- [ ] **APPROVED FOR DEPLOYMENT**
- [ ] **REJECTED - REQUIRES CHANGES**

**Signature**: ___________________

**Notes**:
[Any final comments or special instructions]

---

## Post-Deployment Review

*(Complete 1 week after production deployment)*

**Deployed Date**: [YYYY-MM-DD]
**Reviewer**: [Name]
**Review Date**: [YYYY-MM-DD]

### Performance Metrics
- Error count (past 7 days): [Number]
- Average execution time: [Seconds]
- Governor limit warnings: [ ] Yes  [ ] No

### Issues Encountered
[List any production issues and resolutions]

### Lessons Learned
[What went well? What could be improved?]

### Follow-up Actions
- [ ] [Action 1]
- [ ] [Action 2]

---

## Document Version

**Version**: 1.0
**Last Updated**: [YYYY-MM-DD]
**Template Owner**: [Name/Team]
