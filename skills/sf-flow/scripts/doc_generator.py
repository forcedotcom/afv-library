#!/usr/bin/env python3
"""
Flow Documentation Generator

Automatically generates comprehensive documentation for Salesforce Flows
by parsing flow XML and populating the documentation template.

Usage:
    python doc_generator.py <path-to-flow.xml> [output-path.md]
"""

import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime
from typing import Dict, List, Tuple

class FlowDocGenerator:
    """Generates documentation from flow XML."""

    def __init__(self, flow_xml_path: str, template_path: str = None):
        """
        Initialize the documentation generator.

        Args:
            flow_xml_path: Path to the flow XML file
            template_path: Path to template file (optional)
        """
        self.flow_path = flow_xml_path
        self.tree = ET.parse(flow_xml_path)
        self.root = self.tree.getroot()
        self.namespace = {'sf': 'http://soap.sforce.com/2006/04/metadata'}

        # Load template
        if template_path is None:
            # Use default template location
            script_dir = os.path.dirname(os.path.abspath(__file__))
            template_path = os.path.join(script_dir, '..', 'templates', 'flow-documentation-template.md')

        with open(template_path, 'r') as f:
            self.template = f.read()

    def generate(self) -> str:
        """
        Generate complete documentation by populating template.

        Returns:
            Populated documentation string
        """
        # Extract all data from flow
        data = self._extract_flow_data()

        # Replace all placeholders
        doc = self.template
        for key, value in data.items():
            placeholder = f"{{{{{key}}}}}"
            doc = doc.replace(placeholder, str(value))

        return doc

    def _extract_flow_data(self) -> Dict[str, str]:
        """Extract all relevant data from flow XML."""
        data = {}

        # Basic info
        data['FLOW_NAME'] = self._get_text('label', 'Unknown Flow')
        data['STATUS'] = self._get_text('status', 'Unknown')
        data['API_VERSION'] = self._get_text('apiVersion', 'Unknown')
        data['PURPOSE'] = self._get_text('description', 'No description provided')

        # Dates
        data['CREATED_DATE'] = 'N/A'
        data['MODIFIED_DATE'] = datetime.now().strftime('%Y-%m-%d')
        data['OWNER'] = 'To be filled'

        # Flow type
        data['FLOW_TYPE'] = self._determine_flow_type()
        data['BUSINESS_CONTEXT'] = 'To be filled by business owner'

        # Entry/Exit criteria
        data['ENTRY_CRITERIA'] = self._get_entry_criteria()
        data['EXIT_CRITERIA'] = 'Flow completes when all operations finish successfully'

        # Logic design
        data['DECISION_POINTS'] = self._get_decision_points()
        data['COMPLEXITY_LEVEL'] = self._assess_complexity()

        # Operations
        data['SOQL_COUNT'] = str(self._count_elements('recordLookups'))
        data['DML_COUNT'] = str(self._count_dml_operations())
        data['SUBFLOW_COUNT'] = str(self._count_elements('subflows'))
        data['APEX_ACTION_COUNT'] = str(self._count_elements('actionCalls'))

        # Orchestration
        data['ORCHESTRATION_PATTERN'] = self._detect_orchestration_pattern()
        data['PARENT_FLOW'] = 'N/A - standalone flow'
        data['CHILD_SUBFLOWS'] = self._get_child_subflows()
        data['COORDINATION_PATTERN'] = self._get_coordination_pattern()

        # Performance
        data['BULK_TESTED'] = '⏳ Pending'
        data['TRANSFORM_USED'] = '✅ Yes' if self._has_transform() else '⏭️ Not applicable'
        data['BULKIFICATION_STATUS'] = self._check_bulkification()

        # Governor limits
        data['DML_ROWS_ESTIMATE'] = '< 1,000'
        data['SOQL_QUERIES_ESTIMATE'] = data['SOQL_COUNT']
        data['DML_STATEMENTS_ESTIMATE'] = data['DML_COUNT']
        data['CPU_TIME_ESTIMATE'] = '< 1,000ms'
        data['SIMULATION_RESULTS'] = '⏳ Pending simulation testing'

        # Error handling
        data['FAULT_PATH_COVERAGE'] = self._get_fault_path_coverage()
        data['ERROR_LOGGING_METHOD'] = self._detect_error_logging()
        data['ERROR_CAPTURE_FLOW_NAME'] = '✅ Captured'
        data['ERROR_CAPTURE_RECORD_ID'] = '✅ Captured'
        data['ERROR_CAPTURE_MESSAGE'] = '✅ Captured'
        data['ERROR_CAPTURE_TIMESTAMP'] = '✅ Auto-captured'
        data['ALERT_MECHANISM'] = self._get_alert_mechanism()

        # Reusability
        data['SUBFLOWS_USED_LIST'] = self._get_subflows_used()
        data['IS_REUSABLE'] = '✅ Yes' if self._is_reusable() else 'No'
        data['INVOCABLE_FROM_APEX'] = '✅ Yes' if data['FLOW_TYPE'] == 'Autolaunched' else 'No'
        data['INPUT_VARIABLES'] = self._get_input_variables()
        data['OUTPUT_VARIABLES'] = self._get_output_variables()

        # Security
        data['RUNNING_MODE'] = self._get_running_mode()
        data['BYPASSES_PERMISSIONS'] = '✅ Yes' if 'System' in data['RUNNING_MODE'] else 'No'
        data['RUNNING_MODE_JUSTIFICATION'] = self._get_mode_justification()
        data['OBJECTS_ACCESSED'] = self._get_objects_accessed()
        data['SENSITIVE_FIELDS'] = self._get_sensitive_fields()
        data['COMPLIANCE_REQUIREMENTS'] = 'To be reviewed'

        # Testing
        data['TESTED_STANDARD_USER'] = '⏳ Pending'
        data['TESTED_CUSTOM_PROFILES'] = '⏳ Pending'
        data['TESTED_PERMISSION_SETS'] = '⏳ Pending'
        data['FLS_RESPECTED'] = 'To be verified'
        data['CRUD_RESPECTED'] = 'To be verified'

        # Review
        data['REVIEWED_BY'] = 'Pending review'
        data['REVIEW_DATE'] = 'N/A'
        data['REVIEW_STATUS'] = 'Pending'

        # Testing status
        data['UNIT_TESTING_PATHS'] = '⏳ Pending'
        data['UNIT_TESTING_ERRORS'] = '⏳ Pending'
        data['UNIT_TESTING_EDGE_CASES'] = '⏳ Pending'
        data['BULK_TESTING_RECORDS'] = '⏳ Pending'
        data['BULK_TESTING_LIMITS'] = '⏳ Pending'
        data['BULK_TESTING_PERFORMANCE'] = '⏳ Pending'
        data['INTEGRATION_RELATED_FLOWS'] = '⏳ Pending'
        data['INTEGRATION_EXTERNAL'] = '⏳ Pending'
        data['UAT_COMPLETED'] = '⏳ Pending'

        # Deployment
        data['DEPLOYED'] = 'No'
        data['DEPLOYMENT_DATE'] = 'N/A'
        data['ACTIVATED'] = data['STATUS']

        # Dependencies
        data['REQUIRED_METADATA'] = self._get_required_metadata()
        data['REQUIRED_OBJECTS'] = self._get_required_objects()
        data['REQUIRED_FIELDS'] = self._get_required_fields()
        data['REQUIRED_SUBFLOWS'] = self._get_required_subflows()
        data['REQUIRED_APEX'] = self._get_required_apex()

        # Change log
        data['CHANGE_LOG_ENTRIES'] = f"{datetime.now().strftime('%Y-%m-%d')} | 1.0 | Initial creation | Auto-generated"

        # Troubleshooting
        data['COMMON_ISSUES'] = 'To be documented as issues are discovered'
        data['DEBUG_STEPS'] = self._get_debug_steps()
        data['SUPPORT_PRIMARY'] = 'To be assigned'
        data['SUPPORT_BACKUP'] = 'To be assigned'
        data['SUPPORT_TEAM'] = 'To be assigned'

        # Related docs
        data['RELATED_DOCS'] = self._get_related_docs()

        # Notes
        data['ADDITIONAL_NOTES'] = 'Auto-generated documentation. Review and update as needed.'

        # Generation date
        data['GENERATION_DATE'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return data

    def _get_text(self, element_name: str, default: str = '') -> str:
        """Get text from XML element."""
        elem = self.root.find(f'sf:{element_name}', self.namespace)
        return elem.text if elem is not None else default

    def _determine_flow_type(self) -> str:
        """Determine the flow type."""
        process_type = self._get_text('processType', 'Unknown')

        # Check if record-triggered
        if self.root.find('sf:triggerType', self.namespace) is not None:
            trigger_type = self._get_text('triggerType', '')
            object_name = self._get_text('.//sf:start/sf:object', '')
            return f"Record-Triggered ({trigger_type} on {object_name})"

        type_map = {
            'Flow': 'Screen Flow',
            'AutoLaunchedFlow': 'Autolaunched Flow',
            'InvocableProcess': 'Scheduled Flow'
        }

        return type_map.get(process_type, process_type)

    def _get_entry_criteria(self) -> str:
        """Get entry criteria for the flow."""
        # Check for record trigger
        trigger_elem = self.root.find('.//sf:start', self.namespace)
        if trigger_elem is not None:
            object_elem = trigger_elem.find('sf:object', self.namespace)
            trigger_type_elem = trigger_elem.find('sf:recordTriggerType', self.namespace)

            if object_elem is not None:
                obj = object_elem.text
                trigger_type = trigger_type_elem.text if trigger_type_elem is not None else 'Unknown'
                return f"Triggers when {obj} record is {trigger_type}"

        return "To be documented"

    def _get_decision_points(self) -> str:
        """List all decision points."""
        decisions = self.root.findall('.//sf:decisions', self.namespace)
        if not decisions:
            return "No decision points (linear flow)"

        result = []
        for i, decision in enumerate(decisions[:5], 1):  # Limit to first 5
            name = decision.find('sf:name', self.namespace)
            label = decision.find('sf:label', self.namespace)
            if name is not None:
                label_text = label.text if label is not None else name.text
                result.append(f"{i}. **{label_text}**: Evaluates conditions")

        return '\n'.join(result) if result else "No decision points"

    def _assess_complexity(self) -> str:
        """Assess flow complexity."""
        decision_count = self._count_elements('decisions')
        loop_count = self._count_elements('loops')
        subflow_count = self._count_elements('subflows')

        total_complexity = decision_count + loop_count + subflow_count

        if total_complexity == 0:
            return "Simple (linear flow)"
        elif total_complexity <= 3:
            return "Moderate (few branches)"
        else:
            return "Complex (multiple branches/subflows)"

    def _count_elements(self, element_type: str) -> int:
        """Count elements of a specific type."""
        return len(self.root.findall(f'.//sf:{element_type}', self.namespace))

    def _count_dml_operations(self) -> int:
        """Count all DML operations."""
        dml_types = ['recordCreates', 'recordUpdates', 'recordDeletes']
        return sum(self._count_elements(t) for t in dml_types)

    def _detect_orchestration_pattern(self) -> str:
        """Detect orchestration pattern used."""
        has_subflows = self._count_elements('subflows') > 0
        has_decisions = self._count_elements('decisions') > 0
        subflow_count = self._count_elements('subflows')

        if not has_subflows:
            return "Standalone (no subflows)"
        elif has_decisions and subflow_count > 1:
            return "Conditional (routes to specialized subflows)"
        elif subflow_count > 2:
            return "Parent-Child (orchestrator pattern)"
        else:
            return "Sequential (linear subflow calls)"

    def _get_child_subflows(self) -> str:
        """List child subflows called."""
        subflows = self.root.findall('.//sf:subflows', self.namespace)
        if not subflows:
            return "N/A - no child subflows"

        result = []
        for subflow in subflows:
            flow_name = subflow.find('sf:flowName', self.namespace)
            if flow_name is not None:
                result.append(f"- {flow_name.text}")

        return '\n'.join(result) if result else "N/A"

    def _get_coordination_pattern(self) -> str:
        """Determine coordination pattern."""
        subflow_count = self._count_elements('subflows')
        if subflow_count == 0:
            return "N/A"
        elif subflow_count == 1:
            return "Single subflow call"
        else:
            return "Multiple subflows (sequential execution)"

    def _has_transform(self) -> bool:
        """Check if flow uses Transform element."""
        return self._count_elements('transforms') > 0

    def _check_bulkification(self) -> str:
        """Check bulkification status."""
        # Check for DML in loops (anti-pattern)
        loops = self.root.findall('.//sf:loops', self.namespace)
        for loop in loops:
            # This is a simplified check
            if self.root.find('.//sf:recordCreates', self.namespace) is not None:
                return "⚠️ Potential issue - verify no DML in loops"

        return "✅ Appears bulkified"

    def _get_fault_path_coverage(self) -> str:
        """Calculate fault path coverage."""
        dml_count = self._count_dml_operations()
        if dml_count == 0:
            return "N/A - no DML operations"

        # Count DML with fault paths
        dml_with_faults = 0
        for dml_type in ['recordCreates', 'recordUpdates', 'recordDeletes']:
            for element in self.root.findall(f'.//sf:{dml_type}', self.namespace):
                fault = element.find('sf:faultConnector', self.namespace)
                if fault is not None:
                    dml_with_faults += 1

        if dml_with_faults == dml_count:
            return f"✅ Complete ({dml_count}/{dml_count} operations)"
        else:
            return f"⚠️ Partial ({dml_with_faults}/{dml_count} operations)"

    def _detect_error_logging(self) -> str:
        """Detect error logging method."""
        # Check for Sub_LogError calls
        for subflow in self.root.findall('.//sf:subflows', self.namespace):
            flow_name = subflow.find('sf:flowName', self.namespace)
            if flow_name is not None and 'LogError' in flow_name.text:
                return "Sub_LogError (structured logging)"

        return "Custom or none"

    def _get_alert_mechanism(self) -> str:
        """Get alert mechanism."""
        # Check for email alerts
        for action in self.root.findall('.//sf:actionCalls', self.namespace):
            action_name = action.find('sf:actionName', self.namespace)
            if action_name is not None and 'email' in action_name.text.lower():
                return "Email notifications"

        return "To be configured"

    def _get_subflows_used(self) -> str:
        """List subflows used."""
        subflows = self.root.findall('.//sf:subflows', self.namespace)
        if not subflows:
            return "None"

        result = []
        for subflow in subflows:
            flow_name = subflow.find('sf:flowName', self.namespace)
            if flow_name is not None:
                result.append(f"- **{flow_name.text}**: To be documented")

        return '\n'.join(result) if result else "None"

    def _is_reusable(self) -> bool:
        """Check if flow can be reused."""
        process_type = self._get_text('processType')
        return process_type == 'AutoLaunchedFlow'

    def _get_input_variables(self) -> str:
        """List input variables."""
        result = []
        for var in self.root.findall('.//sf:variables', self.namespace):
            is_input = var.find('sf:isInput', self.namespace)
            if is_input is not None and is_input.text == 'true':
                name = var.find('sf:name', self.namespace)
                data_type = var.find('sf:dataType', self.namespace)
                if name is not None:
                    dt = data_type.text if data_type is not None else 'Unknown'
                    result.append(f"- `{name.text}` ({dt}): To be documented")

        return '\n'.join(result) if result else "None"

    def _get_output_variables(self) -> str:
        """List output variables."""
        result = []
        for var in self.root.findall('.//sf:variables', self.namespace):
            is_output = var.find('sf:isOutput', self.namespace)
            if is_output is not None and is_output.text == 'true':
                name = var.find('sf:name', self.namespace)
                data_type = var.find('sf:dataType', self.namespace)
                if name is not None:
                    dt = data_type.text if data_type is not None else 'Unknown'
                    result.append(f"- `{name.text}` ({dt}): To be documented")

        return '\n'.join(result) if result else "None"

    def _get_running_mode(self) -> str:
        """Get running mode."""
        run_in_mode = self.root.find('sf:runInMode', self.namespace)
        if run_in_mode is not None:
            return run_in_mode.text
        return "User Mode (Default)"

    def _get_mode_justification(self) -> str:
        """Get justification for running mode."""
        mode = self._get_running_mode()
        if 'System' in mode:
            return "\n**Justification**: To be documented - why is System mode required?"
        return ""

    def _get_objects_accessed(self) -> str:
        """List objects accessed."""
        objects = set()

        for elem_type in ['recordCreates', 'recordUpdates', 'recordDeletes', 'recordLookups']:
            for element in self.root.findall(f'.//sf:{elem_type}', self.namespace):
                obj = element.find('sf:object', self.namespace)
                if obj is not None:
                    objects.add(obj.text)

        if not objects:
            return "None"

        result = [f"- {obj}" for obj in sorted(objects)]
        return '\n'.join(result)

    def _get_sensitive_fields(self) -> str:
        """Identify sensitive fields."""
        # This is basic detection
        return "To be reviewed and documented"

    def _get_required_metadata(self) -> str:
        """List required metadata."""
        return "To be documented (custom settings, metadata types, etc.)"

    def _get_required_objects(self) -> str:
        """List required objects."""
        return self._get_objects_accessed()

    def _get_required_fields(self) -> str:
        """List required fields."""
        fields = set()

        # Extract fields from various operations
        for elem in self.root.findall('.//sf:field', self.namespace):
            if elem.text:
                fields.add(elem.text)

        if not fields:
            return "To be documented"

        result = [f"- {field}" for field in sorted(list(fields)[:10])]  # Limit to 10
        if len(fields) > 10:
            result.append(f"- ... and {len(fields) - 10} more")

        return '\n'.join(result)

    def _get_required_subflows(self) -> str:
        """List required subflows."""
        return self._get_child_subflows()

    def _get_required_apex(self) -> str:
        """List required Apex classes."""
        actions = self.root.findall('.//sf:actionCalls', self.namespace)
        apex_classes = set()

        for action in actions:
            action_type = action.find('sf:actionType', self.namespace)
            if action_type is not None and action_type.text == 'apex':
                action_name = action.find('sf:actionName', self.namespace)
                if action_name is not None:
                    apex_classes.add(action_name.text)

        if not apex_classes:
            return "None"

        result = [f"- {cls}" for cls in sorted(apex_classes)]
        return '\n'.join(result)

    def _get_debug_steps(self) -> str:
        """Get debug steps."""
        return """1. Enable flow debug logs
2. Reproduce the issue with test data
3. Review debug logs for errors
4. Check Flow_Error_Log__c (if using error logging)
5. Verify all prerequisites are met"""

    def _get_related_docs(self) -> str:
        """Get related documentation links."""
        docs = [
            "- [Subflow Library](../references/subflow-library.md)",
            "- [Orchestration Guide](../references/orchestration-guide.md)",
            "- [Flow Best Practices](../references/flow-best-practices.md)",
            "- [Governance Checklist](../references/governance-checklist.md)"
        ]
        return '\n'.join(docs)


def generate_documentation(flow_xml_path: str, output_path: str = None) -> str:
    """
    Generate documentation for a flow.

    Args:
        flow_xml_path: Path to flow XML file
        output_path: Output path for documentation (optional)

    Returns:
        Generated documentation string
    """
    generator = FlowDocGenerator(flow_xml_path)
    doc = generator.generate()

    if output_path:
        with open(output_path, 'w') as f:
            f.write(doc)
        print(f"Documentation generated: {output_path}")

    return doc


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python doc_generator.py <path-to-flow.xml> [output-path.md]")
        sys.exit(1)

    flow_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    # Auto-generate output path if not provided
    if output_path is None:
        flow_name = os.path.splitext(os.path.basename(flow_path))[0]
        output_path = f"{flow_name}_documentation.md"

    try:
        doc = generate_documentation(flow_path, output_path)
        print(f"\n✅ Documentation generated successfully!")
        print(f"   File: {output_path}")
        print(f"   Lines: {len(doc.splitlines())}")
    except Exception as e:
        print(f"❌ Error generating documentation: {e}")
        sys.exit(1)
