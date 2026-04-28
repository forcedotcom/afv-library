#!/usr/bin/env python3
"""
Salesforce Metadata Validator

Validates Salesforce metadata XML files against best practices.
120-point scoring across 6 categories:

1. Structure & Format (20 points)
   - Valid XML syntax
   - Correct namespace
   - API version requirements
   - File path structure

2. Naming Conventions (20 points)
   - API names (__c suffix)
   - PascalCase naming
   - Meaningful labels
   - Relationship naming patterns

3. Data Integrity (20 points)
   - Required field defaults
   - Numeric precision/scale
   - Picklist definitions
   - Relationship constraints

4. Security & FLS (20 points)
   - Field-level security considerations
   - Sensitive data patterns
   - Sharing model appropriateness

5. Documentation (20 points)
   - Descriptions present
   - Help text for user fields
   - Error messages for validation rules

6. Best Practices (20 points)
   - Permission Sets over Profiles
   - No hardcoded IDs
   - Global Value Sets for reusable picklists

Usage:
    python validate_metadata.py /path/to/metadata-file.xml
"""

import os
import re
import sys
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Optional


class MetadataValidator:
    """Validates Salesforce metadata XML files."""

    # Salesforce metadata namespace
    NAMESPACE = {'sf': 'http://soap.sforce.com/2006/04/metadata'}

    # Sensitive field patterns (potential PII/security concerns)
    SENSITIVE_PATTERNS = [
        r'ssn|social.?security',
        r'credit.?card|cc.?number',
        r'password|secret|token',
        r'bank.?account|routing.?number',
        r'tax.?id|ein|itin',
        r'driver.?license|passport',
    ]

    # Scoring categories
    CATEGORIES = {
        'structure_format': {'name': 'Structure & Format', 'max': 20, 'score': 20, 'issues': []},
        'naming_conventions': {'name': 'Naming Conventions', 'max': 20, 'score': 20, 'issues': []},
        'data_integrity': {'name': 'Data Integrity', 'max': 20, 'score': 20, 'issues': []},
        'security_fls': {'name': 'Security & FLS', 'max': 20, 'score': 20, 'issues': []},
        'documentation': {'name': 'Documentation', 'max': 20, 'score': 20, 'issues': []},
        'best_practices': {'name': 'Best Practices', 'max': 20, 'score': 20, 'issues': []},
    }

    def __init__(self, file_path: str):
        """Initialize validator with file path."""
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.tree = None
        self.root = None
        self.metadata_type = self._detect_metadata_type()
        self.categories = {k: dict(v) for k, v in self.CATEGORIES.items()}
        for cat in self.categories.values():
            cat['issues'] = []

    def _detect_metadata_type(self) -> str:
        """Detect metadata type from file name."""
        if self.file_name.endswith('.object-meta.xml'):
            return 'CustomObject'
        elif self.file_name.endswith('.field-meta.xml'):
            return 'CustomField'
        elif self.file_name.endswith('.profile-meta.xml'):
            return 'Profile'
        elif self.file_name.endswith('.permissionset-meta.xml'):
            return 'PermissionSet'
        elif self.file_name.endswith('.validationRule-meta.xml'):
            return 'ValidationRule'
        elif self.file_name.endswith('.recordType-meta.xml'):
            return 'RecordType'
        elif self.file_name.endswith('.layout-meta.xml'):
            return 'Layout'
        return 'Unknown'

    def _add_issue(self, category: str, severity: str, message: str, deduction: int = 0):
        """Add an issue to a category."""
        if category in self.categories:
            self.categories[category]['issues'].append({
                'severity': severity,
                'message': message
            })
            if deduction > 0:
                self.categories[category]['score'] = max(
                    0, self.categories[category]['score'] - deduction
                )

    def _get_text(self, element, tag: str, default: str = '') -> str:
        """Get text content of a child element."""
        child = element.find(f'sf:{tag}', self.NAMESPACE)
        if child is not None and child.text:
            return child.text.strip()
        # Try without namespace
        child = element.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return default

    def validate(self) -> Dict:
        """Run all validations and return results."""
        # Parse XML
        try:
            self.tree = ET.parse(self.file_path)
            self.root = self.tree.getroot()
        except ET.ParseError as e:
            self._add_issue('structure_format', 'CRITICAL', f'Invalid XML: {e}', 10)
            return self._build_results()
        except FileNotFoundError:
            self._add_issue('structure_format', 'CRITICAL', f'File not found: {self.file_path}', 20)
            return self._build_results()

        # Run validations by metadata type
        self._validate_structure()
        self._validate_naming()
        self._validate_data_integrity()
        self._validate_security()
        self._validate_documentation()
        self._validate_best_practices()

        return self._build_results()

    def _validate_structure(self):
        """Validate XML structure and format."""
        # Check namespace
        root_tag = self.root.tag
        if not root_tag.startswith('{http://soap.sforce.com/2006/04/metadata}'):
            # Check if it has any namespace
            if not root_tag.startswith('{'):
                self._add_issue(
                    'structure_format', 'WARNING',
                    'Missing Salesforce metadata namespace', 5
                )

        # Check file path structure
        if '/objects/' in self.file_path:
            if self.metadata_type == 'CustomField' and '/fields/' not in self.file_path:
                self._add_issue(
                    'structure_format', 'WARNING',
                    'Field files should be in objects/[ObjectName]/fields/', 3
                )
            if self.metadata_type == 'ValidationRule' and '/validationRules/' not in self.file_path:
                self._add_issue(
                    'structure_format', 'WARNING',
                    'Validation rules should be in objects/[ObjectName]/validationRules/', 3
                )

    def _validate_naming(self):
        """Validate naming conventions."""
        # Get API name
        api_name = self._get_text(self.root, 'fullName')
        label = self._get_text(self.root, 'label')

        # Custom objects/fields should end with __c
        if self.metadata_type in ['CustomObject', 'CustomField']:
            # Check filename for __c
            base_name = self.file_name.replace('.object-meta.xml', '').replace('.field-meta.xml', '')
            if not base_name.endswith('__c') and not base_name.startswith('standard-'):
                self._add_issue(
                    'naming_conventions', 'WARNING',
                    f'Custom metadata should have __c suffix: {base_name}', 3
                )

            # Check for PascalCase (allow underscores for API names)
            if api_name and not re.match(r'^[A-Z][a-zA-Z0-9_]*$', api_name.replace('__c', '')):
                self._add_issue(
                    'naming_conventions', 'INFO',
                    f'API name should use PascalCase: {api_name}', 2
                )

        # Check label is meaningful (not just API name)
        if label and api_name:
            api_clean = api_name.replace('__c', '').replace('_', ' ')
            if label.lower() == api_clean.lower():
                self._add_issue(
                    'naming_conventions', 'INFO',
                    'Label should be user-friendly, not just API name', 1
                )

        # Check for abbreviations in labels
        abbreviation_patterns = [
            (r'\bAcct\b', 'Account'),
            (r'\bOpp\b', 'Opportunity'),
            (r'\bCont\b', 'Contact'),
            (r'\bMgr\b', 'Manager'),
            (r'\bNum\b', 'Number'),
            (r'\bQty\b', 'Quantity'),
        ]
        if label:
            for pattern, suggestion in abbreviation_patterns:
                if re.search(pattern, label, re.IGNORECASE):
                    self._add_issue(
                        'naming_conventions', 'INFO',
                        f'Avoid abbreviations in labels. Consider using "{suggestion}"', 1
                    )
                    break

    def _validate_data_integrity(self):
        """Validate data integrity settings."""
        if self.metadata_type == 'CustomField':
            field_type = self._get_text(self.root, 'type')
            required = self._get_text(self.root, 'required')
            default_value = self._get_text(self.root, 'defaultValue')

            # Required fields should have defaults (except lookups)
            if required == 'true' and not default_value:
                if field_type not in ['Lookup', 'MasterDetail']:
                    self._add_issue(
                        'data_integrity', 'INFO',
                        'Required fields should consider having a default value', 2
                    )

            # Number/Currency fields should have precision/scale
            if field_type in ['Number', 'Currency', 'Percent']:
                precision = self._get_text(self.root, 'precision')
                scale = self._get_text(self.root, 'scale')
                if not precision or not scale:
                    self._add_issue(
                        'data_integrity', 'WARNING',
                        f'{field_type} fields should specify precision and scale', 3
                    )

            # Lookup/Master-Detail should have relationship name
            if field_type in ['Lookup', 'MasterDetail']:
                rel_name = self._get_text(self.root, 'relationshipName')
                if not rel_name:
                    self._add_issue(
                        'data_integrity', 'WARNING',
                        'Relationship fields should have relationshipName', 3
                    )

                # Check delete constraint for lookups
                if field_type == 'Lookup':
                    delete_constraint = self._get_text(self.root, 'deleteConstraint')
                    if not delete_constraint:
                        self._add_issue(
                            'data_integrity', 'INFO',
                            'Consider setting deleteConstraint for lookup fields', 2
                        )

        elif self.metadata_type == 'ValidationRule':
            # Check for error message
            error_message = self._get_text(self.root, 'errorMessage')
            if not error_message:
                self._add_issue(
                    'data_integrity', 'WARNING',
                    'Validation rules must have an error message', 5
                )
            elif len(error_message) < 10:
                self._add_issue(
                    'data_integrity', 'INFO',
                    'Error messages should be descriptive', 2
                )

    def _validate_security(self):
        """Validate security and FLS settings."""
        # Check for sensitive field patterns
        api_name = self._get_text(self.root, 'fullName', self.file_name)
        label = self._get_text(self.root, 'label', '')
        description = self._get_text(self.root, 'description', '')

        combined_text = f"{api_name} {label} {description}".lower()

        for pattern in self.SENSITIVE_PATTERNS:
            if re.search(pattern, combined_text, re.IGNORECASE):
                self._add_issue(
                    'security_fls', 'CRITICAL',
                    f'Potential sensitive data field detected. Ensure proper FLS and encryption.', 10
                )
                break

        # Check sharing model for objects
        if self.metadata_type == 'CustomObject':
            sharing_model = self._get_text(self.root, 'sharingModel')
            if sharing_model == 'ReadWrite':
                self._add_issue(
                    'security_fls', 'INFO',
                    'Public Read/Write sharing model - verify this is intentional', 2
                )

        # For Permission Sets/Profiles, check for ModifyAllData or ViewAllData
        if self.metadata_type in ['Profile', 'PermissionSet']:
            user_perms = self.root.findall('.//sf:userPermissions', self.NAMESPACE)
            for perm in user_perms:
                name = self._get_text(perm, 'name')
                enabled = self._get_text(perm, 'enabled')
                if enabled == 'true' and name in ['ModifyAllData', 'ViewAllData']:
                    self._add_issue(
                        'security_fls', 'WARNING',
                        f'{name} permission enabled - use with caution', 5
                    )

    def _validate_documentation(self):
        """Validate documentation elements."""
        description = self._get_text(self.root, 'description')
        help_text = self._get_text(self.root, 'inlineHelpText')

        # Check for description
        if self.metadata_type in ['CustomObject', 'CustomField', 'PermissionSet']:
            if not description:
                self._add_issue(
                    'documentation', 'WARNING',
                    'Add a description to explain the purpose', 5
                )
            elif len(description) < 20:
                self._add_issue(
                    'documentation', 'INFO',
                    'Description should be more detailed', 2
                )

        # Check for help text on user-facing fields
        if self.metadata_type == 'CustomField':
            field_type = self._get_text(self.root, 'type')
            # User-facing fields should have help text
            if field_type not in ['Formula', 'Summary'] and not help_text:
                self._add_issue(
                    'documentation', 'INFO',
                    'Consider adding help text for user guidance', 2
                )

        # Validation rules should have good error messages
        if self.metadata_type == 'ValidationRule':
            error_message = self._get_text(self.root, 'errorMessage')
            if error_message and not any(word in error_message.lower() for word in ['please', 'must', 'should', 'required']):
                self._add_issue(
                    'documentation', 'INFO',
                    'Error messages should be user-friendly and actionable', 2
                )

    def _validate_best_practices(self):
        """Validate against Salesforce best practices."""
        if self.metadata_type == 'Profile':
            self._add_issue(
                'best_practices', 'INFO',
                'Consider using Permission Sets instead of Profiles for granular access', 3
            )

        if self.metadata_type == 'CustomField':
            field_type = self._get_text(self.root, 'type')

            # Check for formula fields with hardcoded IDs
            if field_type == 'Formula':
                formula = self._get_text(self.root, 'formula')
                if formula and re.search(r'["\'][0-9a-zA-Z]{15,18}["\']', formula):
                    self._add_issue(
                        'best_practices', 'WARNING',
                        'Avoid hardcoded IDs in formulas - use Custom Settings or Custom Metadata', 5
                    )

            # Picklist fields should consider Global Value Sets
            if field_type == 'Picklist':
                value_set = self.root.find('.//sf:valueSetDefinition', self.NAMESPACE)
                if value_set is not None:
                    values = value_set.findall('.//sf:value', self.NAMESPACE)
                    if len(values) > 10:
                        self._add_issue(
                            'best_practices', 'INFO',
                            'Consider using a Global Value Set for reusable picklist values', 2
                        )

        if self.metadata_type == 'ValidationRule':
            # Check for bypass pattern
            formula = self._get_text(self.root, 'errorConditionFormula')
            if formula and '$Permission' not in formula and '$Setup' not in formula:
                self._add_issue(
                    'best_practices', 'INFO',
                    'Consider adding a bypass mechanism for admin/integration users', 3
                )

    def _build_results(self) -> Dict:
        """Build and return validation results."""
        total_score = sum(cat['score'] for cat in self.categories.values())
        max_score = sum(cat['max'] for cat in self.categories.values())

        # Calculate rating
        percentage = (total_score / max_score) * 100 if max_score > 0 else 0
        if percentage >= 90:
            rating = '⭐⭐⭐⭐⭐ Excellent'
        elif percentage >= 80:
            rating = '⭐⭐⭐⭐ Very Good'
        elif percentage >= 70:
            rating = '⭐⭐⭐ Good'
        elif percentage >= 60:
            rating = '⭐⭐ Needs Work'
        else:
            rating = '⭐ Critical Issues'

        return {
            'file_path': self.file_path,
            'metadata_type': self.metadata_type,
            'overall_score': total_score,
            'max_score': max_score,
            'rating': rating,
            'categories': {
                cat_key: {
                    'name': cat_data['name'],
                    'score': cat_data['score'],
                    'max_score': cat_data['max'],
                    'issues': cat_data['issues']
                }
                for cat_key, cat_data in self.categories.items()
            }
        }


def main():
    """CLI entry point with dual-mode input support."""
    import json

    file_path = None

    # Mode 1: Hook mode - read from stdin JSON (PostToolUse hooks)
    if not sys.stdin.isatty():
        try:
            hook_input = json.load(sys.stdin)
            tool_input = hook_input.get("tool_input", {})
            file_path = tool_input.get("file_path", "")
        except (json.JSONDecodeError, EOFError):
            pass

    # Mode 2: CLI mode - read from command-line argument
    if not file_path and len(sys.argv) >= 2:
        file_path = sys.argv[1]

    # Validate we have a file path
    if not file_path:
        print("Usage: python validate_metadata.py <metadata-file.xml>")
        sys.exit(1)

    # Only validate metadata files
    valid_extensions = [
        '.object-meta.xml', '.field-meta.xml', '.permissionset-meta.xml',
        '.profile-meta.xml', '.validationRule-meta.xml', '.recordType-meta.xml',
        '.layout-meta.xml'
    ]
    if not any(file_path.endswith(ext) for ext in valid_extensions):
        sys.exit(0)  # Silently skip non-metadata files

    validator = MetadataValidator(file_path)
    results = validator.validate()

    # Print results
    print(f"\n{'=' * 60}")
    print(f"🔍 Metadata Validation: {results['metadata_type']}")
    print(f"File: {os.path.basename(file_path)}")
    print(f"{'=' * 60}")
    print(f"\nScore: {results['overall_score']}/{results['max_score']} {results['rating']}")

    print("\nCategory Breakdown:")
    for cat_key, cat_data in results['categories'].items():
        score = cat_data['score']
        max_score = cat_data['max_score']
        name = cat_data['name']
        pct = int((score / max_score) * 100) if max_score > 0 else 0
        print(f"  ├─ {name}: {score}/{max_score} ({pct}%)")

    # Print issues
    all_issues = []
    for cat_data in results['categories'].values():
        all_issues.extend(cat_data['issues'])

    if all_issues:
        print("\nIssues Found:")
        for issue in all_issues:
            severity = issue['severity']
            message = issue['message']
            icon = {'CRITICAL': '🔴', 'WARNING': '🟡', 'INFO': '🔵'}.get(severity, '⚪')
            print(f"  {icon} [{severity}] {message}")
    else:
        print("\n✅ No issues found!")

    print()
    return 0 if results['overall_score'] >= 72 else 1


if __name__ == "__main__":
    sys.exit(main())
