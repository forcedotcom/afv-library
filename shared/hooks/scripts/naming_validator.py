#!/usr/bin/env python3
"""
Naming Convention Validator for Salesforce Flows (v2.0.0)

Validates flow naming conventions based on industry best practices.
All checks are ADVISORY - they provide suggestions but do not block deployment.

Flow Naming Convention:
- Record-Triggered: RTF_<Object>_<Purpose>
- Screen Flow: Screen_<Purpose> or SCR_<Purpose>
- Autolaunched: Auto_<Purpose> or AL_<Purpose>
- Scheduled: Scheduled_<Purpose> or SCHED_<Purpose>
- Subflow: Sub_<Purpose> or UTIL_<Purpose>

Variable Naming Convention (v2.0.0):
- var_ : Regular variables (e.g., var_AccountName)
- col_ : Collections (e.g., col_ContactIds)
- rec_ : Record variables (e.g., rec_Account)
- inp_ : Input variables (e.g., inp_RecordId)
- out_ : Output variables (e.g., out_IsSuccess)

Button Naming Convention (v2.0.0):
- Action_[Verb]_[Object] (e.g., Action_Save_Contact)
"""

import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple

class NamingValidator:
    """Validates flow naming conventions."""

    # Naming patterns for different flow types
    NAMING_PATTERNS = {
        'AutoLaunchedFlow': {
            'patterns': [r'^Auto_[A-Z][A-Za-z0-9_]*$', r'^AL_[A-Z][A-Za-z0-9_]*$', r'^Sub_[A-Z][A-Za-z0-9_]*$'],
            'prefixes': ['Auto_', 'AL_', 'Sub_'],
            'description': 'Autolaunched flows should use Auto_, AL_, or Sub_ prefix'
        },
        'Flow': {
            'patterns': [r'^Screen_[A-Z][A-Za-z0-9_]*$', r'^SCR_[A-Z][A-Za-z0-9_]*$'],
            'prefixes': ['Screen_', 'SCR_'],
            'description': 'Screen flows should use Screen_ or SCR_ prefix'
        },
        'InvocableProcess': {
            'patterns': [r'^Scheduled_[A-Z][A-Za-z0-9_]*$', r'^SCHED_[A-Z][A-Za-z0-9_]*$'],
            'prefixes': ['Scheduled_', 'SCHED_'],
            'description': 'Scheduled flows should use Scheduled_ or SCHED_ prefix'
        }
    }

    # Special pattern for Record-Triggered flows (check in triggerType)
    RECORD_TRIGGERED_PATTERNS = [
        r'^RTF_[A-Z][A-Za-z][A-Za-z0-9]*_[A-Z][A-Za-z0-9_]*$',  # RTF_Account_UpdateIndustry
    ]

    def __init__(self, flow_xml_path: str):
        """
        Initialize the naming validator.

        Args:
            flow_xml_path: Path to the flow XML file
        """
        self.flow_path = flow_xml_path
        self.tree = ET.parse(flow_xml_path)
        self.root = self.tree.getroot()
        self.namespace = {'sf': 'http://soap.sforce.com/2006/04/metadata'}
        self.suggestions = []
        self.warnings = []

    def validate(self) -> Dict[str, any]:
        """
        Run all naming validations.

        Returns:
            Dictionary containing validation results
        """
        flow_label = self._get_flow_label()
        flow_type = self._get_flow_type()
        is_record_triggered = self._is_record_triggered()

        results = {
            'flow_label': flow_label,
            'flow_type': flow_type,
            'is_record_triggered': is_record_triggered,
            'follows_convention': False,
            'suggested_names': [],
            'warnings': self.warnings,
            'suggestions': self.suggestions
        }

        # Check naming convention
        if is_record_triggered:
            results['follows_convention'] = self._check_record_triggered_naming(flow_label)
            if not results['follows_convention']:
                results['suggested_names'] = self._suggest_record_triggered_names()
        else:
            results['follows_convention'] = self._check_standard_naming(flow_label, flow_type)
            if not results['follows_convention']:
                results['suggested_names'] = self._suggest_standard_names(flow_type)

        # Check element naming
        element_issues = self._check_element_naming()
        if element_issues:
            results['element_naming_issues'] = element_issues

        # Check variable naming (v2.0.0 prefixes)
        variable_issues = self._check_variable_naming()
        if variable_issues:
            results['variable_naming_issues'] = variable_issues

        # Check button naming (v2.0.0)
        button_issues = self._check_button_naming()
        if button_issues:
            results['button_naming_issues'] = button_issues

        return results

    def _get_flow_label(self) -> str:
        """Get the flow label (API name)."""
        label_elem = self.root.find('sf:label', self.namespace)
        return label_elem.text if label_elem is not None else "Unknown"

    def _get_flow_type(self) -> str:
        """Get the flow process type."""
        process_type_elem = self.root.find('sf:processType', self.namespace)
        return process_type_elem.text if process_type_elem is not None else "Unknown"

    def _is_record_triggered(self) -> bool:
        """Check if flow is record-triggered."""
        trigger_type = self.root.find('sf:triggerType', self.namespace)
        return trigger_type is not None

    def _check_record_triggered_naming(self, label: str) -> bool:
        """Check if record-triggered flow follows RTF_ convention."""
        for pattern in self.RECORD_TRIGGERED_PATTERNS:
            if re.match(pattern, label):
                return True

        # Generate warning
        warning_msg = (
            f"ℹ️ ADVISORY: Flow name '{label}' doesn't follow convention. "
            f"Record-triggered flows should use format: RTF_<Object>_<Purpose>"
        )
        self.warnings.append({
            'type': 'NAMING_CONVENTION',
            'severity': 'LOW',
            'message': warning_msg
        })

        return False

    def _check_standard_naming(self, label: str, flow_type: str) -> bool:
        """Check if standard flow follows naming convention."""
        if flow_type not in self.NAMING_PATTERNS:
            # Unknown flow type, can't validate
            return True

        patterns = self.NAMING_PATTERNS[flow_type]['patterns']
        for pattern in patterns:
            if re.match(pattern, label):
                return True

        # Generate warning
        prefixes = self.NAMING_PATTERNS[flow_type]['prefixes']
        prefix_str = ' or '.join(prefixes)
        warning_msg = (
            f"ℹ️ ADVISORY: Flow name '{label}' doesn't follow convention. "
            f"{self.NAMING_PATTERNS[flow_type]['description']} (e.g., {prefix_str}...)"
        )
        self.warnings.append({
            'type': 'NAMING_CONVENTION',
            'severity': 'LOW',
            'message': warning_msg
        })

        return False

    def _suggest_record_triggered_names(self) -> List[str]:
        """Suggest proper names for record-triggered flows."""
        # Try to extract object name from trigger
        obj_elem = self.root.find('.//sf:start/sf:object', self.namespace)
        object_name = obj_elem.text if obj_elem is not None else "Object"

        current_label = self._get_flow_label()

        # Generate suggestions
        suggestions = [
            f"RTF_{object_name}_UpdateRelated",
            f"RTF_{object_name}_ValidateData",
            f"RTF_{object_name}_SendNotifications",
        ]

        # Try to infer purpose from current name
        if '_' in current_label:
            parts = current_label.split('_')
            if len(parts) >= 2:
                purpose = '_'.join(parts[1:])
                suggestions.insert(0, f"RTF_{object_name}_{purpose}")

        self.suggestions.append(
            f"Consider renaming to: {suggestions[0]} (follows RTF_<Object>_<Purpose> convention)"
        )

        return suggestions

    def _suggest_standard_names(self, flow_type: str) -> List[str]:
        """Suggest proper names for standard flows."""
        if flow_type not in self.NAMING_PATTERNS:
            return []

        prefixes = self.NAMING_PATTERNS[flow_type]['prefixes']
        current_label = self._get_flow_label()

        suggestions = []
        for prefix in prefixes:
            # Remove any existing prefix
            clean_name = re.sub(r'^[A-Za-z]+_', '', current_label)
            # Capitalize first letter
            clean_name = clean_name[0].upper() + clean_name[1:] if clean_name else "Purpose"
            suggestions.append(f"{prefix}{clean_name}")

        if suggestions:
            self.suggestions.append(
                f"Consider renaming to: {suggestions[0]}"
            )

        return suggestions

    def _check_element_naming(self) -> List[Dict[str, str]]:
        """Check if flow elements have meaningful names (not default names)."""
        issues = []

        # Elements to check
        element_types = [
            'decisions', 'assignments', 'recordCreates', 'recordUpdates',
            'recordDeletes', 'recordLookups', 'subflows', 'actionCalls'
        ]

        for elem_type in element_types:
            for element in self.root.findall(f'.//sf:{elem_type}', self.namespace):
                name_elem = element.find('sf:name', self.namespace)
                if name_elem is not None:
                    name = name_elem.text

                    # Check for default names (contain random numbers)
                    if re.search(r'_\d{10,}', name) or re.match(r'^[A-Za-z]+_?\d+$', name):
                        issues.append({
                            'element_type': elem_type,
                            'name': name,
                            'suggestion': f"Use descriptive name instead of default '{name}'"
                        })

                        if len(issues) <= 3:  # Only warn about first 3
                            self.suggestions.append(
                                f"Element '{name}' uses default name - consider renaming for clarity"
                            )

        return issues

    def _check_variable_naming(self) -> List[Dict[str, str]]:
        """
        Check if variables follow naming conventions (v2.0.0 prefixes).

        Variable Prefixes:
        - var_ : Regular variables
        - col_ : Collections
        - rec_ : Record variables
        - inp_ : Input variables
        - out_ : Output variables
        """
        issues = []

        # Valid prefixes (v2.0.0)
        VALID_PREFIXES = ['var_', 'col_', 'rec_', 'inp_', 'out_']

        for variable in self.root.findall('.//sf:variables', self.namespace):
            name_elem = variable.find('sf:name', self.namespace)
            is_collection_elem = variable.find('sf:isCollection', self.namespace)
            is_input_elem = variable.find('sf:isInput', self.namespace)
            is_output_elem = variable.find('sf:isOutput', self.namespace)
            data_type_elem = variable.find('sf:dataType', self.namespace)

            if name_elem is not None:
                var_name = name_elem.text

                # Skip system variables
                if var_name.startswith('$'):
                    continue

                is_collection = is_collection_elem is not None and is_collection_elem.text == 'true'
                is_input = is_input_elem is not None and is_input_elem.text == 'true'
                is_output = is_output_elem is not None and is_output_elem.text == 'true'
                is_record = data_type_elem is not None and data_type_elem.text == 'SObject'

                # Check if any valid prefix is used
                has_valid_prefix = any(var_name.startswith(prefix) for prefix in VALID_PREFIXES)

                if has_valid_prefix:
                    continue  # Already follows convention

                # Determine recommended prefix based on variable type
                if is_collection:
                    recommended_prefix = 'col_'
                    reason = 'Collection variable'
                elif is_input:
                    recommended_prefix = 'inp_'
                    reason = 'Input variable'
                elif is_output:
                    recommended_prefix = 'out_'
                    reason = 'Output variable'
                elif is_record:
                    recommended_prefix = 'rec_'
                    reason = 'Record variable'
                else:
                    recommended_prefix = 'var_'
                    reason = 'Regular variable'

                # Generate suggestion
                clean_name = var_name
                # Remove old-style prefixes if present
                for old_prefix in ['var', 'col', 'rec']:
                    if var_name.lower().startswith(old_prefix) and len(var_name) > len(old_prefix):
                        if var_name[len(old_prefix)].isupper() or var_name[len(old_prefix)] == '_':
                            clean_name = var_name[len(old_prefix):].lstrip('_')
                            break

                suggested_name = f"{recommended_prefix}{clean_name}"

                issues.append({
                    'variable': var_name,
                    'issue': f'{reason} should use prefix "{recommended_prefix}"',
                    'suggestion': suggested_name
                })

                if len(issues) <= 3:
                    self.suggestions.append(
                        f"Variable '{var_name}' ({reason}) - consider '{suggested_name}'"
                    )

        return issues

    def _check_button_naming(self) -> List[Dict[str, str]]:
        """
        Check if screen buttons/actions follow naming convention (v2.0.0).

        Pattern: Action_[Verb]_[Object]
        Examples: Action_Save_Contact, Action_Submit_Application
        """
        issues = []

        # Check screen actions (buttons)
        for screen in self.root.findall('.//sf:screens', self.namespace):
            for field in screen.findall('.//sf:fields', self.namespace):
                field_type = field.find('sf:fieldType', self.namespace)

                # Check if it's a button/action type
                if field_type is not None and field_type.text in ['ComponentInstance', 'DisplayText']:
                    name_elem = field.find('sf:name', self.namespace)
                    if name_elem is not None:
                        button_name = name_elem.text

                        # Check if it follows Action_Verb_Object pattern
                        if 'button' in button_name.lower() or 'action' in button_name.lower():
                            if not re.match(r'^Action_[A-Z][a-z]+_[A-Z][A-Za-z]+$', button_name):
                                # Extract verb and object from current name if possible
                                parts = re.findall(r'[A-Z][a-z]+', button_name)
                                if len(parts) >= 2:
                                    suggested = f"Action_{parts[0]}_{parts[1]}"
                                else:
                                    suggested = f"Action_Perform_{button_name.replace('_', '')}"

                                issues.append({
                                    'button': button_name,
                                    'issue': 'Button name should follow Action_[Verb]_[Object] pattern',
                                    'suggestion': suggested
                                })

                                if len(issues) <= 2:
                                    self.suggestions.append(
                                        f"Button '{button_name}' - consider 'Action_[Verb]_[Object]' pattern"
                                    )

        return issues

    def generate_report(self) -> str:
        """
        Generate a human-readable naming validation report.

        Returns:
            Formatted report string
        """
        results = self.validate()

        report = []
        report.append("\n" + "="*60)
        report.append("Naming Convention Validation Report")
        report.append("="*60)

        # Flow naming
        report.append(f"\n📋 Flow Name: {results['flow_label']}")
        report.append(f"   Type: {results['flow_type']}")
        if results['is_record_triggered']:
            report.append("   Trigger: Record-Triggered")

        if results['follows_convention']:
            report.append("   ✅ Follows naming convention")
        else:
            report.append("   ℹ️  ADVISORY: Doesn't follow naming convention")
            if results['suggested_names']:
                report.append(f"\n   💡 Suggested names:")
                for name in results['suggested_names'][:3]:
                    report.append(f"      - {name}")

        # Element naming
        if 'element_naming_issues' in results and results['element_naming_issues']:
            count = len(results['element_naming_issues'])
            report.append(f"\n⚠️  Element Naming: {count} elements use default names")
            report.append("   Consider renaming for better readability")

        # Variable naming (v2.0.0)
        if 'variable_naming_issues' in results and results['variable_naming_issues']:
            count = len(results['variable_naming_issues'])
            report.append(f"\n⚠️  Variable Naming: {count} variables don't follow v2.0.0 convention")
            report.append("   Recommended prefixes: var_, col_, rec_, inp_, out_")

        # Button naming (v2.0.0)
        if 'button_naming_issues' in results and results['button_naming_issues']:
            count = len(results['button_naming_issues'])
            report.append(f"\n⚠️  Button Naming: {count} buttons don't follow convention")
            report.append("   Recommended pattern: Action_[Verb]_[Object]")

        # Suggestions
        if results['suggestions']:
            report.append(f"\n💡 Suggestions for Improvement:")
            for i, suggestion in enumerate(results['suggestions'][:5], 1):
                report.append(f"   {i}. {suggestion}")

        report.append("\n" + "="*60)
        report.append("Note: These are ADVISORY suggestions. Flow can be deployed.")
        report.append("="*60 + "\n")

        return "\n".join(report)


def validate_flow_naming(flow_xml_path: str) -> Tuple[Dict, str]:
    """
    Validate flow naming conventions and return results.

    Args:
        flow_xml_path: Path to the flow XML file

    Returns:
        Tuple of (results dict, formatted report)
    """
    validator = NamingValidator(flow_xml_path)
    results = validator.validate()
    report = validator.generate_report()

    return results, report


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python naming_validator.py <path-to-flow.xml>")
        sys.exit(1)

    flow_path = sys.argv[1]

    try:
        results, report = validate_flow_naming(flow_path)
        print(report)

        # Exit with code 0 (naming is advisory, never blocks)
        sys.exit(0)

    except Exception as e:
        print(f"Error validating flow naming: {e}")
        sys.exit(1)
