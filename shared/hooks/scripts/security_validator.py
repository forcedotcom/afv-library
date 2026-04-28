#!/usr/bin/env python3
"""
Security Validator for Salesforce Flows

Validates security and governance aspects of flows including:
- System mode vs User mode detection
- Sensitive field access warnings
- FLS/CRUD permission considerations
- Profile testing recommendations

All checks are ADVISORY - they provide warnings but do not block deployment.
"""

import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple

# Sensitive field patterns (regex)
SENSITIVE_FIELD_PATTERNS = [
    r".*SSN.*",
    r".*Social.*Security.*",
    r".*Password.*",
    r".*Credit.*Card.*",
    r".*Bank.*Account.*",
    r".*Routing.*Number.*",
    r".*Tax.*ID.*",
    r".*Driver.*License.*",
    r".*Passport.*",
    r".*Pin.*Code.*",
]

class SecurityValidator:
    """Validates security and governance aspects of Salesforce flows."""

    def __init__(self, flow_xml_path: str):
        """
        Initialize the security validator.

        Args:
            flow_xml_path: Path to the flow XML file
        """
        self.flow_path = flow_xml_path
        self.tree = ET.parse(flow_xml_path)
        self.root = self.tree.getroot()
        self.namespace = {'sf': 'http://soap.sforce.com/2006/04/metadata'}
        self.warnings = []
        self.recommendations = []

    def validate(self) -> Dict[str, any]:
        """
        Run all security validations.

        Returns:
            Dictionary containing validation results
        """
        results = {
            'running_mode': self._check_running_mode(),
            'sensitive_fields': self._check_sensitive_fields(),
            'object_access': self._check_object_access(),
            'warnings': self.warnings,
            'recommendations': self.recommendations,
            'severity': self._calculate_severity()
        }

        return results

    def _check_running_mode(self) -> Dict[str, any]:
        """
        Check if flow runs in System mode (bypasses FLS/CRUD).

        Returns:
            Dictionary with mode information and warnings
        """
        # Check for runInMode element
        run_in_mode = self.root.find('sf:runInMode', self.namespace)

        if run_in_mode is None:
            # Default mode (respects user permissions)
            return {
                'mode': 'User Mode (Default)',
                'bypasses_permissions': False,
                'warning': None
            }

        mode_value = run_in_mode.text

        if 'SystemMode' in mode_value:
            warning_msg = (
                f"ℹ️ ADVISORY: Flow runs in {mode_value}. "
                f"This bypasses FLS/CRUD permissions. "
                f"Is this intentional for your use case?"
            )
            self.warnings.append({
                'type': 'SYSTEM_MODE',
                'severity': 'MEDIUM',
                'message': warning_msg
            })

            # Add recommendation for profile testing
            self.recommendations.append(
                "Document why System mode is required and ensure appropriate security review"
            )

            return {
                'mode': mode_value,
                'bypasses_permissions': True,
                'warning': warning_msg
            }

        return {
            'mode': mode_value,
            'bypasses_permissions': False,
            'warning': None
        }

    def _check_sensitive_fields(self) -> List[Dict[str, str]]:
        """
        Check if flow accesses sensitive fields.

        Returns:
            List of sensitive field accesses with warnings
        """
        sensitive_fields_found = []

        # Check all field references in the flow
        field_elements = [
            'inputAssignments',  # Record Creates/Updates
            'filters',  # Record Lookups
            'assignmentItems',  # Assignments
        ]

        for element_type in field_elements:
            for element in self.root.findall(f'.//sf:{element_type}', self.namespace):
                field_elem = element.find('sf:field', self.namespace)
                if field_elem is not None:
                    field_name = field_elem.text

                    # Check against sensitive patterns
                    for pattern in SENSITIVE_FIELD_PATTERNS:
                        if re.match(pattern, field_name, re.IGNORECASE):
                            # Check if running in system mode
                            mode_info = self._check_running_mode()

                            if mode_info['bypasses_permissions']:
                                warning_msg = (
                                    f"ℹ️ ADVISORY: Sensitive field '{field_name}' accessed in System mode. "
                                    f"Ensure appropriate security controls and audit logging are in place."
                                )

                                self.warnings.append({
                                    'type': 'SENSITIVE_FIELD_SYSTEM_MODE',
                                    'severity': 'HIGH',
                                    'field': field_name,
                                    'message': warning_msg
                                })
                            else:
                                warning_msg = (
                                    f"ℹ️ ADVISORY: Sensitive field '{field_name}' accessed. "
                                    f"Verify field-level security is properly configured."
                                )

                                self.warnings.append({
                                    'type': 'SENSITIVE_FIELD_ACCESS',
                                    'severity': 'LOW',
                                    'field': field_name,
                                    'message': warning_msg
                                })

                            sensitive_fields_found.append({
                                'field': field_name,
                                'system_mode': mode_info['bypasses_permissions'],
                                'warning': warning_msg
                            })

                            # Add recommendation
                            self.recommendations.append(
                                f"Test field access for '{field_name}' with restricted user profiles"
                            )

        return sensitive_fields_found

    def _check_object_access(self) -> List[Dict[str, str]]:
        """
        Check which objects the flow accesses and recommend security testing.

        Returns:
            List of objects accessed with testing recommendations
        """
        objects_accessed = []

        # Check recordCreates, recordUpdates, recordDeletes, recordLookups
        access_elements = [
            ('recordCreates', 'CREATE'),
            ('recordUpdates', 'UPDATE'),
            ('recordDeletes', 'DELETE'),
            ('recordLookups', 'READ'),
        ]

        for element_name, operation in access_elements:
            for element in self.root.findall(f'.//sf:{element_name}', self.namespace):
                object_elem = element.find('sf:object', self.namespace)
                if object_elem is not None:
                    object_name = object_elem.text

                    objects_accessed.append({
                        'object': object_name,
                        'operation': operation
                    })

        # Remove duplicates
        unique_objects = {}
        for obj in objects_accessed:
            obj_name = obj['object']
            if obj_name not in unique_objects:
                unique_objects[obj_name] = []
            unique_objects[obj_name].append(obj['operation'])

        # Add recommendations for profile testing
        if unique_objects:
            self.recommendations.append(
                "Test flow with Standard User profile to verify CRUD permissions"
            )
            self.recommendations.append(
                "Test flow with custom profiles that have restricted object access"
            )

        return [
            {'object': obj, 'operations': list(set(ops))}
            for obj, ops in unique_objects.items()
        ]

    def _calculate_severity(self) -> str:
        """
        Calculate overall severity based on warnings.

        Returns:
            Severity level: LOW, MEDIUM, HIGH
        """
        if not self.warnings:
            return 'NONE'

        high_count = sum(1 for w in self.warnings if w.get('severity') == 'HIGH')
        medium_count = sum(1 for w in self.warnings if w.get('severity') == 'MEDIUM')

        if high_count > 0:
            return 'HIGH'
        elif medium_count > 0:
            return 'MEDIUM'
        else:
            return 'LOW'

    def generate_report(self) -> str:
        """
        Generate a human-readable security validation report.

        Returns:
            Formatted report string
        """
        results = self.validate()

        report = []
        report.append("\n" + "="*60)
        report.append("Security & Governance Validation Report")
        report.append("="*60)

        # Running Mode
        report.append(f"\n📋 Running Mode: {results['running_mode']['mode']}")
        if results['running_mode']['bypasses_permissions']:
            report.append("   ⚠️  ADVISORY: Bypasses FLS/CRUD permissions")
        else:
            report.append("   ✅ Respects user permissions")

        # Sensitive Fields
        if results['sensitive_fields']:
            report.append(f"\n🔐 Sensitive Fields Detected: {len(results['sensitive_fields'])}")
            for field_info in results['sensitive_fields']:
                report.append(f"   - {field_info['field']}")
        else:
            report.append("\n🔐 Sensitive Fields: None detected")

        # Object Access
        if results['object_access']:
            report.append(f"\n📊 Objects Accessed: {len(results['object_access'])}")
            for obj_info in results['object_access']:
                ops = ', '.join(obj_info['operations'])
                report.append(f"   - {obj_info['object']}: {ops}")

        # Warnings
        if results['warnings']:
            report.append(f"\n⚠️  Warnings ({results['severity']} severity):")
            for warning in results['warnings']:
                report.append(f"   {warning['message']}")
        else:
            report.append("\n✅ No security warnings")

        # Recommendations
        if results['recommendations']:
            report.append("\n💡 Recommendations:")
            for i, rec in enumerate(results['recommendations'], 1):
                report.append(f"   {i}. {rec}")

        report.append("\n" + "="*60)
        report.append("Note: These are ADVISORY warnings. Flow can be deployed.")
        report.append("="*60 + "\n")

        return "\n".join(report)


def validate_flow_security(flow_xml_path: str) -> Tuple[Dict, str]:
    """
    Validate security aspects of a flow and return results.

    Args:
        flow_xml_path: Path to the flow XML file

    Returns:
        Tuple of (results dict, formatted report)
    """
    validator = SecurityValidator(flow_xml_path)
    results = validator.validate()
    report = validator.generate_report()

    return results, report


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python security_validator.py <path-to-flow.xml>")
        sys.exit(1)

    flow_path = sys.argv[1]

    try:
        results, report = validate_flow_security(flow_path)
        print(report)

        # Exit with code based on severity (for CI/CD)
        # 0 = no warnings, 1 = low/medium, 2 = high
        if results['severity'] == 'HIGH':
            sys.exit(2)
        elif results['severity'] in ['LOW', 'MEDIUM']:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"Error validating flow: {e}")
        sys.exit(3)
