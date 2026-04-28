# Flow Documentation: {{FLOW_NAME}}

**Status**: {{STATUS}}
**API Version**: {{API_VERSION}}
**Created**: {{CREATED_DATE}}
**Last Modified**: {{MODIFIED_DATE}}
**Owner**: {{OWNER}}

---

## Overview

**Purpose**: {{PURPOSE}}

**Flow Type**: {{FLOW_TYPE}}

**Business Context**: {{BUSINESS_CONTEXT}}

---

## Entry/Exit Criteria

### Entry Criteria
{{ENTRY_CRITERIA}}

### Exit Criteria
{{EXIT_CRITERIA}}

---

## Logic Design

### Decision Points
{{DECISION_POINTS}}

### Branching Complexity
**Complexity Level**: {{COMPLEXITY_LEVEL}}

### Operations Summary
- **SOQL Queries**: {{SOQL_COUNT}}
- **DML Operations**: {{DML_COUNT}}
- **Subflow Calls**: {{SUBFLOW_COUNT}}
- **Apex Actions**: {{APEX_ACTION_COUNT}}

---

## Orchestration & Architecture

### Architecture Pattern
**Pattern Used**: {{ORCHESTRATION_PATTERN}}

### Parent Flow
{{PARENT_FLOW}}

### Child Subflows Called
{{CHILD_SUBFLOWS}}

### Coordination Pattern
{{COORDINATION_PATTERN}}

---

## Performance & Bulk Safety

### Bulk Testing
- **Tested with 200+ records**: {{BULK_TESTED}}
- **Transform Element Used**: {{TRANSFORM_USED}}
- **Bulkification Status**: {{BULKIFICATION_STATUS}}

### Governor Limit Estimates
- **DML Rows**: {{DML_ROWS_ESTIMATE}} / 10,000
- **SOQL Queries**: {{SOQL_QUERIES_ESTIMATE}} / 100
- **DML Statements**: {{DML_STATEMENTS_ESTIMATE}} / 150
- **CPU Time**: {{CPU_TIME_ESTIMATE}} / 10,000ms

### Simulation Results
{{SIMULATION_RESULTS}}

---

## Error Handling & Observability

### Fault Paths
**Coverage**: {{FAULT_PATH_COVERAGE}}

### Error Logging
**Method**: {{ERROR_LOGGING_METHOD}}

**Error Capture**:
- Flow Name: {{ERROR_CAPTURE_FLOW_NAME}}
- Record ID: {{ERROR_CAPTURE_RECORD_ID}}
- Error Message: {{ERROR_CAPTURE_MESSAGE}}
- Timestamp: {{ERROR_CAPTURE_TIMESTAMP}}

### Alert Mechanism
{{ALERT_MECHANISM}}

---

## Reusability & Components

### Subflows Used
{{SUBFLOWS_USED_LIST}}

### Can Be Reused
**Reusable**: {{IS_REUSABLE}}

**Invocable from Apex**: {{INVOCABLE_FROM_APEX}}

### Input Variables
{{INPUT_VARIABLES}}

### Output Variables
{{OUTPUT_VARIABLES}}

---

## Security & Governance

### Running Mode
**Mode**: {{RUNNING_MODE}}

**Bypasses Permissions**: {{BYPASSES_PERMISSIONS}}

{{RUNNING_MODE_JUSTIFICATION}}

### Data Access

**Objects Accessed**:
{{OBJECTS_ACCESSED}}

**Sensitive Fields**:
{{SENSITIVE_FIELDS}}

### Compliance
{{COMPLIANCE_REQUIREMENTS}}

### Testing Coverage
- **Standard User Profile**: {{TESTED_STANDARD_USER}}
- **Custom Profiles**: {{TESTED_CUSTOM_PROFILES}}
- **Permission Sets**: {{TESTED_PERMISSION_SETS}}
- **FLS Respected**: {{FLS_RESPECTED}}
- **CRUD Respected**: {{CRUD_RESPECTED}}

### Architecture Review
- **Reviewed By**: {{REVIEWED_BY}}
- **Review Date**: {{REVIEW_DATE}}
- **Status**: {{REVIEW_STATUS}}

---

## Testing Status

### Unit Testing
- **All Paths Tested**: {{UNIT_TESTING_PATHS}}
- **Error Scenarios**: {{UNIT_TESTING_ERRORS}}
- **Edge Cases**: {{UNIT_TESTING_EDGE_CASES}}

### Bulk Testing
- **200+ Records**: {{BULK_TESTING_RECORDS}}
- **No Governor Limits**: {{BULK_TESTING_LIMITS}}
- **Performance**: {{BULK_TESTING_PERFORMANCE}}

### Integration Testing
- **Related Flows**: {{INTEGRATION_RELATED_FLOWS}}
- **External Systems**: {{INTEGRATION_EXTERNAL}}
- **UAT Completed**: {{UAT_COMPLETED}}

### Production Deployment
- **Deployed**: {{DEPLOYED}}
- **Deployment Date**: {{DEPLOYMENT_DATE}}
- **Activated**: {{ACTIVATED}}

---

## Dependencies

### Required Metadata
{{REQUIRED_METADATA}}

### Required Objects
{{REQUIRED_OBJECTS}}

### Required Fields
{{REQUIRED_FIELDS}}

### Required Subflows
{{REQUIRED_SUBFLOWS}}

### Required Apex Classes
{{REQUIRED_APEX}}

---

## Change Log

| Date | Version | Change Description | Modified By |
|------|---------|-------------------|-------------|
| {{CHANGE_LOG_ENTRIES}} |

---

## Troubleshooting

### Common Issues
{{COMMON_ISSUES}}

### Debug Steps
{{DEBUG_STEPS}}

### Support Contacts
- **Primary**: {{SUPPORT_PRIMARY}}
- **Backup**: {{SUPPORT_BACKUP}}
- **Team**: {{SUPPORT_TEAM}}

---

## Related Documentation

{{RELATED_DOCS}}

---

## Notes

{{ADDITIONAL_NOTES}}

---

*Generated automatically by SF-Flow Builder Documentation Generator*
*Generation Date: {{GENERATION_DATE}}*
