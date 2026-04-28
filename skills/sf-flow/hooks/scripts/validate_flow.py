#!/usr/bin/env python3
"""
Enhanced Flow Validator with 6-Category Scoring (v2.2.0)

Validates Salesforce Flows across 6 best practice categories:
1. Design & Naming
2. Logic & Structure
3. Architecture & Orchestration
4. Performance & Bulk Safety
5. Error Handling & Observability
6. Security & Governance

v2.2.0 New Validations (Lightning Flow Scanner Parity):
- HardcodedId detection - 15/18 char Salesforce ID patterns
- HardcodedUrl detection - Non-Salesforce URLs that break portability
- UnusedVariable detection - Variables defined but never referenced
- UnconnectedElement detection - Orphaned elements with no connectors
- RecursiveAfterUpdate detection - CRITICAL infinite loop prevention
- SOQLQueryInLoop (upgraded) - Path tracing like DML detection
- ActionCallsInLoop - Apex action callout limit risk
- DuplicateDMLBetweenScreens - Back button data issues
- AutoLayout check - Canvas mode preference
- CopyAPIName detection - "Copy_X_Of" lazy naming pattern

v2.1.0 Fixes:
- FIXED: DML-in-loop detection now traces actual connector paths
- FIXED: Subflow recommendation now applies to all flow types (RTFs CAN call subflows via XML on API 66.0+)
- FIXED: Error logging detection includes inline patterns (not just subflows)
- IMPROVED: Better understanding of $Record context in record-triggered flows

v2.0.0 New Validations:
- storeOutputAutomatically detection (data leak prevention)
- Same-object query anti-pattern ($Record recommendation)
- Complex formula in loops warning
- Missing filters on Get Records
- Null check after Get Records
- getFirstRecordOnly recommendation
- Scheduled flow activation warning

All non-critical checks are ADVISORY - they provide recommendations but don't block deployment.
"""

import xml.etree.ElementTree as ET
from typing import Dict, List
import sys
import os

# Import validators from shared location (canonical installed path)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))  # sf-flow/
SHARED_SCRIPTS = os.path.join(os.path.expanduser("~"), ".claude", "hooks", "scripts")
sys.path.insert(0, SHARED_SCRIPTS)
from naming_validator import NamingValidator
from security_validator import SecurityValidator


class EnhancedFlowValidator:
    """Comprehensive flow validator with 6-category scoring."""

    def __init__(self, flow_xml_path: str):
        """
        Initialize the enhanced validator.

        Args:
            flow_xml_path: Path to the flow XML file
        """
        self.flow_path = flow_xml_path
        self.tree = ET.parse(flow_xml_path)
        self.root = self.tree.getroot()
        self.namespace = {'sf': 'http://soap.sforce.com/2006/04/metadata'}

        # Initialize sub-validators
        self.naming_validator = NamingValidator(flow_xml_path)
        self.security_validator = SecurityValidator(flow_xml_path)

        # Scoring
        self.scores = {}
        self.max_scores = {
            'design_naming': 20,
            'logic_structure': 20,
            'architecture_orchestration': 15,
            'performance_bulk': 20,
            'error_handling': 20,
            'security_governance': 15
        }
        self.total_max = sum(self.max_scores.values())

    def validate(self) -> Dict:
        """
        Run comprehensive validation across all categories.

        Returns:
            Dictionary with scores, issues, and recommendations
        """
        results = {
            'flow_name': self._get_flow_label(),
            'api_version': self._get_api_version(),
            'categories': {},
            'overall_score': 0,
            'rating': '',
            'recommendations': [],
            'critical_issues': [],
            'warnings': [],
            'advisory_suggestions': []
        }

        # Run all category validations
        results['categories']['design_naming'] = self._validate_design_naming()
        results['categories']['logic_structure'] = self._validate_logic_structure()
        results['categories']['architecture_orchestration'] = self._validate_architecture()
        results['categories']['performance_bulk'] = self._validate_performance()
        results['categories']['error_handling'] = self._validate_error_handling()
        results['categories']['security_governance'] = self._validate_security()

        # Calculate overall score
        total_score = sum(cat['score'] for cat in results['categories'].values())
        results['overall_score'] = total_score
        results['rating'] = self._get_rating(total_score)

        # Collect all recommendations
        for category in results['categories'].values():
            results['recommendations'].extend(category.get('recommendations', []))
            results['critical_issues'].extend(category.get('critical_issues', []))
            results['warnings'].extend(category.get('warnings', []))
            results['advisory_suggestions'].extend(category.get('advisory', []))

        return results

    def _validate_design_naming(self) -> Dict:
        """Validate Design & Naming (max 20 points)."""
        score = self.max_scores['design_naming']
        issues = []
        recommendations = []
        advisory = []

        # Run naming validator
        naming_results = self.naming_validator.validate()

        # Naming convention (5 points)
        if not naming_results['follows_convention']:
            score -= 5
            advisory.append({
                'category': 'Naming',
                'message': f"Flow name doesn't follow convention",
                'suggestion': naming_results['suggested_names'][0] if naming_results['suggested_names'] else 'Use standard prefix'
            })

        # Description present (5 points)
        description = self._get_text('description')
        if not description or len(description) < 20:
            score -= 5
            advisory.append({
                'category': 'Documentation',
                'message': 'Flow description missing or too short',
                'suggestion': 'Add clear description (minimum 20 characters)'
            })

        # Element naming (5 points)
        if 'element_naming_issues' in naming_results and len(naming_results['element_naming_issues']) > 0:
            issue_count = len(naming_results['element_naming_issues'])
            deduction = min(5, issue_count)
            score -= deduction
            advisory.append({
                'category': 'Element Naming',
                'message': f'{issue_count} elements use default names',
                'suggestion': 'Rename elements for better readability'
            })

        # Variable naming (5 points)
        if 'variable_naming_issues' in naming_results and len(naming_results['variable_naming_issues']) > 0:
            issue_count = len(naming_results['variable_naming_issues'])
            deduction = min(5, issue_count)
            score -= deduction
            advisory.append({
                'category': 'Variable Naming',
                'message': f'{issue_count} variables don\'t follow convention',
                'suggestion': 'Use "var" prefix for single values, "col" for collections'
            })

        # ═══════════════════════════════════════════════════════════════════════
        # NEW v2.2.0: Copy API name detection (lazy naming)
        # ═══════════════════════════════════════════════════════════════════════
        copy_names = self._check_copy_api_name()
        if copy_names:
            score -= 2
            advisory.append({
                'category': 'Element Naming',
                'message': f'{len(copy_names)} elements have "Copy_of" naming: {", ".join(copy_names[:3])}',
                'suggestion': 'Rename copied elements with meaningful names'
            })

        return {
            'score': max(0, score),
            'max_score': self.max_scores['design_naming'],
            'issues': issues,
            'recommendations': recommendations,
            'advisory': advisory
        }

    def _validate_logic_structure(self) -> Dict:
        """Validate Logic & Structure (max 20 points)."""
        score = self.max_scores['logic_structure']
        critical_issues = []
        warnings = []
        advisory = []

        # DML in loops (CRITICAL - 10 points)
        if self._has_dml_in_loops():
            score -= 10
            critical_issues.append({
                'severity': 'CRITICAL',
                'message': '❌ DML operations found inside loops - WILL CAUSE BULK FAILURES',
                'fix': 'Move DML outside loops, collect records in collection first'
            })

        # ═══════════════════════════════════════════════════════════════════════
        # NEW v2.2.0: SOQL queries in loops (path tracing)
        # ═══════════════════════════════════════════════════════════════════════
        if self._has_soql_in_loops():
            score -= 8
            critical_issues.append({
                'severity': 'CRITICAL',
                'message': '❌ SOQL queries found inside loops - WILL HIT GOVERNOR LIMITS',
                'fix': 'Query records before loop, use collection variable'
            })

        # ═══════════════════════════════════════════════════════════════════════
        # NEW v2.2.0: Action calls in loops (callout limit risk)
        # ═══════════════════════════════════════════════════════════════════════
        if self._check_action_calls_in_loop():
            score -= 5
            warnings.append({
                'severity': 'HIGH',
                'message': '⚠️ Apex action calls found inside loops - callout limit risk',
                'suggestion': 'Consider bulkifying the action or calling outside the loop'
            })

        # ═══════════════════════════════════════════════════════════════════════
        # NEW v2.0.0: Complex formula in loops warning
        # ═══════════════════════════════════════════════════════════════════════
        if self._has_formula_in_loops():
            score -= 2
            advisory.append({
                'category': 'Performance',
                'message': 'Formula variables detected with loops - potential CPU impact',
                'suggestion': 'Test with bulk data; complex formulas in loops can cause CPU timeouts'
            })

        # Decision complexity (5 points)
        decision_count = self._count_elements('decisions')
        if decision_count > 5:
            score -= 3
            advisory.append({
                'category': 'Complexity',
                'message': f'{decision_count} decision points - consider simplification',
                'suggestion': 'Break into subflows or use simpler business rules'
            })

        # Transform element usage (5 points)
        if self._should_use_transform() and not self._has_transform():
            score -= 5
            advisory.append({
                'category': 'Performance',
                'message': 'Loop with field mapping detected - Transform element recommended',
                'suggestion': 'Transform is 30-50% faster than loops for field mapping'
            })

        return {
            'score': max(0, score),
            'max_score': self.max_scores['logic_structure'],
            'critical_issues': critical_issues,
            'warnings': warnings,
            'advisory': advisory
        }

    def _validate_architecture(self) -> Dict:
        """Validate Architecture & Orchestration (max 15 points)."""
        score = self.max_scores['architecture_orchestration']
        advisory = []
        recommendations = []

        # Orchestration pattern (5 points)
        subflow_count = self._count_elements('subflows')
        decision_count = self._count_elements('decisions')

        if subflow_count == 0:
            # Check if flow is complex enough to warrant subflows
            total_elements = sum([
                self._count_elements('recordCreates'),
                self._count_elements('recordUpdates'),
                self._count_elements('recordDeletes'),
                self._count_elements('recordLookups'),
                decision_count
            ])

            if total_elements > 10:
                score -= 3
                advisory.append({
                    'category': 'Orchestration',
                    'message': 'Complex flow with no subflows - consider breaking into components',
                    'suggestion': 'Use Parent-Child pattern for better maintainability'
                })

        # Modularity (5 points)
        line_count = self._estimate_line_count()
        if line_count > 300:
            score -= 5
            advisory.append({
                'category': 'Modularity',
                'message': f'Flow is very large (~{line_count} lines) - hard to maintain',
                'suggestion': 'Break into orchestrator + specialized subflows'
            })

        # Reusability (5 points)
        if self._is_autolaunched() and not self._has_input_output():
            score -= 3
            advisory.append({
                'category': 'Reusability',
                'message': 'Autolaunched flow without input/output variables',
                'suggestion': 'Add input/output variables for reusability'
            })

        # ═══════════════════════════════════════════════════════════════════════
        # NEW v2.2.0: Unused variables (dead code)
        # ═══════════════════════════════════════════════════════════════════════
        unused_vars = self._check_unused_variables()
        if unused_vars:
            score -= 2
            advisory.append({
                'category': 'Clean Code',
                'message': f'{len(unused_vars)} unused variables: {", ".join(unused_vars[:3])}',
                'suggestion': 'Remove unused variables to reduce clutter'
            })

        # ═══════════════════════════════════════════════════════════════════════
        # NEW v2.2.0: Unconnected elements (orphaned)
        # ═══════════════════════════════════════════════════════════════════════
        orphaned = self._check_unconnected_elements()
        if orphaned:
            score -= 3
            advisory.append({
                'category': 'Clean Code',
                'message': f'{len(orphaned)} orphaned elements: {", ".join(orphaned[:3])}',
                'suggestion': 'Remove or connect orphaned elements'
            })

        # ═══════════════════════════════════════════════════════════════════════
        # NEW v2.2.0: Auto-Layout preference
        # ═══════════════════════════════════════════════════════════════════════
        if self._check_auto_layout():
            advisory.append({
                'category': 'Canvas',
                'message': 'Flow uses manual positioning instead of Auto-Layout',
                'suggestion': 'Consider enabling Auto-Layout for consistent element arrangement'
            })

        return {
            'score': max(0, score),
            'max_score': self.max_scores['architecture_orchestration'],
            'recommendations': recommendations,
            'advisory': advisory
        }

    def _validate_performance(self) -> Dict:
        """Validate Performance & Bulk Safety (max 20 points)."""
        score = self.max_scores['performance_bulk']
        critical_issues = []
        warnings = []
        advisory = []

        # Bulkification (10 points)
        if self._has_dml_in_loops():  # Already checked, but critical for performance
            score -= 10
            # Already added to critical issues in logic_structure

        # ═══════════════════════════════════════════════════════════════════════
        # NEW v2.0.0: storeOutputAutomatically detection (data leak + performance)
        # ═══════════════════════════════════════════════════════════════════════
        store_auto_issues = self._has_store_output_automatically()
        if store_auto_issues:
            score -= 3
            warnings.append({
                'severity': 'MEDIUM',
                'message': f"⚠️ 'Store all fields' enabled in Get Records: {', '.join(store_auto_issues[:3])}",
                'suggestion': 'Specify only needed fields to prevent data leaks and improve performance'
            })

        # ═══════════════════════════════════════════════════════════════════════
        # NEW v2.0.0: Same-object query anti-pattern
        # ═══════════════════════════════════════════════════════════════════════
        same_object_issues = self._has_same_object_query()
        if same_object_issues:
            score -= 2
            advisory.append({
                'category': 'Performance',
                'message': f"Querying trigger object again: {', '.join(same_object_issues[:3])}",
                'suggestion': 'Use $Record to access trigger record fields instead of querying'
            })

        # ═══════════════════════════════════════════════════════════════════════
        # NEW v2.0.0: Missing filters on Get Records
        # ═══════════════════════════════════════════════════════════════════════
        no_filter_issues = self._get_lookups_without_filters()
        if no_filter_issues:
            score -= 2
            advisory.append({
                'category': 'Performance',
                'message': f"Get Records without filters: {', '.join(no_filter_issues[:3])}",
                'suggestion': 'Add filter conditions to limit query results and improve performance'
            })

        # ═══════════════════════════════════════════════════════════════════════
        # NEW v2.0.0: getFirstRecordOnly recommendation
        # ═══════════════════════════════════════════════════════════════════════
        first_record_issues = self._get_lookups_without_first_record_only()
        if first_record_issues:
            advisory.append({
                'category': 'Performance',
                'message': f"Consider getFirstRecordOnly=true: {', '.join(first_record_issues[:3])}",
                'suggestion': 'Use getFirstRecordOnly when expecting a single record'
            })

        # ═══════════════════════════════════════════════════════════════════════
        # NEW v2.2.0: Hardcoded IDs (deployment failure risk)
        # ═══════════════════════════════════════════════════════════════════════
        hardcoded_ids = self._check_hardcoded_ids()
        if hardcoded_ids:
            score -= 5
            warnings.append({
                'severity': 'HIGH',
                'message': f'⚠️ Hardcoded Salesforce IDs detected in {len(hardcoded_ids)} elements',
                'suggestion': 'Use variables, Custom Labels, or Custom Metadata for IDs'
            })

        # ═══════════════════════════════════════════════════════════════════════
        # NEW v2.2.0: Hardcoded URLs (environment portability)
        # ═══════════════════════════════════════════════════════════════════════
        hardcoded_urls = self._check_hardcoded_urls()
        if hardcoded_urls:
            score -= 2
            advisory.append({
                'category': 'Portability',
                'message': f'Hardcoded URLs in {len(hardcoded_urls)} elements: {", ".join(hardcoded_urls[:3])}',
                'suggestion': 'Use Custom Labels or Named Credentials for URLs'
            })

        # ═══════════════════════════════════════════════════════════════════════
        # NEW v2.2.0: DML between screens (back button issue)
        # ═══════════════════════════════════════════════════════════════════════
        dml_between_screens = self._check_duplicate_dml_between_screens()
        if dml_between_screens:
            score -= 3
            warnings.append({
                'severity': 'MEDIUM',
                'message': f'⚠️ DML operations between screens: {", ".join(dml_between_screens[:3])}',
                'suggestion': 'DML between screens can cause data issues with browser back button'
            })

        # SOQL queries (5 points)
        soql_count = self._count_elements('recordLookups')
        if soql_count > 50:
            score -= 5
            warnings.append({
                'severity': 'HIGH',
                'message': f'⚠️ {soql_count} SOQL queries detected - may exceed governor limits',
                'suggestion': 'Consolidate queries or use bulkified patterns'
            })
        elif soql_count > 30:
            score -= 3
            advisory.append({
                'category': 'Performance',
                'message': f'{soql_count} SOQL queries - monitor for governor limits',
                'suggestion': 'Test with bulk data (200+ records)'
            })

        # DML operations (5 points)
        dml_count = self._count_dml_operations()
        if dml_count > 100:
            score -= 5
            warnings.append({
                'severity': 'HIGH',
                'message': f'⚠️ {dml_count} DML operations - may exceed governor limits',
                'suggestion': 'Consolidate DML operations where possible'
            })
        elif dml_count > 50:
            score -= 2
            advisory.append({
                'category': 'Performance',
                'message': f'{dml_count} DML operations - monitor for governor limits',
                'suggestion': 'Test with bulk data (200+ records)'
            })

        return {
            'score': max(0, score),
            'max_score': self.max_scores['performance_bulk'],
            'critical_issues': critical_issues,
            'warnings': warnings,
            'advisory': advisory
        }

    def _validate_error_handling(self) -> Dict:
        """Validate Error Handling & Observability (max 20 points)."""
        score = self.max_scores['error_handling']
        critical_issues = []
        warnings = []
        advisory = []

        # ═══════════════════════════════════════════════════════════════════════
        # NEW v2.2.0: Recursive after-update detection (CRITICAL - infinite loop)
        # ═══════════════════════════════════════════════════════════════════════
        if self._check_recursive_after_update():
            score -= 10
            critical_issues.append({
                'severity': 'CRITICAL',
                'message': '❌ INFINITE LOOP RISK: After-save flow updates same object without entry conditions',
                'fix': 'Add entry conditions to prevent recursive triggering'
            })

        # Fault paths (10 points)
        dml_count = self._count_dml_operations()
        if dml_count > 0:
            dml_with_faults = self._count_dml_with_fault_paths()
            if dml_with_faults < dml_count:
                missing = dml_count - dml_with_faults
                deduction = min(10, missing * 2)
                score -= deduction
                warnings.append({
                    'severity': 'MEDIUM',
                    'message': f'⚠️ {missing} DML operations missing fault paths',
                    'suggestion': 'Add fault paths to all DML operations for error handling'
                })

        # ═══════════════════════════════════════════════════════════════════════
        # NEW v2.0.0: Null check after Get Records
        # ═══════════════════════════════════════════════════════════════════════
        null_check_issues = self._get_lookups_without_null_check()
        if null_check_issues:
            score -= 2
            advisory.append({
                'category': 'Error Prevention',
                'message': f"Get Records may need null checks: {', '.join(null_check_issues[:3])}",
                'suggestion': 'Add Decision element to check for null before using query results'
            })

        # Error logging (10 points)
        has_error_logging = self._has_error_logging()
        if dml_count > 0 and not has_error_logging:
            score -= 10
            advisory.append({
                'category': 'Observability',
                'message': 'No structured error logging detected',
                'suggestion': 'Use Sub_LogError subflow in fault paths for better debugging'
            })

        return {
            'score': max(0, score),
            'max_score': self.max_scores['error_handling'],
            'critical_issues': critical_issues,
            'warnings': warnings,
            'advisory': advisory
        }

    def _validate_security(self) -> Dict:
        """Validate Security & Governance (max 15 points)."""
        score = self.max_scores['security_governance']
        warnings = []
        advisory = []

        # Run security validator
        security_results = self.security_validator.validate()

        # System mode (5 points)
        if security_results['running_mode']['bypasses_permissions']:
            score -= 3
            advisory.append({
                'category': 'Security',
                'message': 'Flow runs in System mode - bypasses FLS/CRUD',
                'suggestion': 'Document justification and ensure security review'
            })

        # Sensitive fields (5 points)
        if len(security_results['sensitive_fields']) > 0:
            score -= 2
            advisory.append({
                'category': 'Security',
                'message': f'{len(security_results["sensitive_fields"])} sensitive fields accessed',
                'suggestion': 'Test with restricted profiles and document security measures'
            })

        # ═══════════════════════════════════════════════════════════════════════
        # NEW v2.0.0: Scheduled flow activation warning
        # ═══════════════════════════════════════════════════════════════════════
        if self._is_scheduled_flow() and self._is_active():
            advisory.append({
                'category': 'Governance',
                'message': 'Active scheduled flow detected - runs automatically',
                'suggestion': 'Ensure thorough testing before activation; scheduled flows run without user interaction'
            })

        # API version (5 points)
        api_version = float(self._get_api_version())
        if api_version < 66.0:
            score -= 5
            advisory.append({
                'category': 'Governance',
                'message': f'API version {api_version} is outdated (current: 66.0)',
                'suggestion': 'Update to latest API version for new features'
            })

        return {
            'score': max(0, score),
            'max_score': self.max_scores['security_governance'],
            'warnings': warnings,
            'advisory': advisory
        }

    # Helper methods
    def _get_flow_label(self) -> str:
        """Get flow label."""
        return self._get_text('label', 'Unknown')

    def _get_api_version(self) -> str:
        """Get API version."""
        return self._get_text('apiVersion', '0.0')

    def _get_text(self, element_name: str, default: str = '') -> str:
        """Get text from XML element."""
        elem = self.root.find(f'sf:{element_name}', self.namespace)
        return elem.text if elem is not None else default

    def _count_elements(self, element_type: str) -> int:
        """Count elements of a specific type."""
        return len(self.root.findall(f'.//sf:{element_type}', self.namespace))

    def _count_dml_operations(self) -> int:
        """Count all DML operations."""
        return sum([
            self._count_elements('recordCreates'),
            self._count_elements('recordUpdates'),
            self._count_elements('recordDeletes')
        ])

    def _has_dml_in_loops(self) -> bool:
        """
        Check if DML operations exist inside loops by tracing connector paths.

        v2.1.0 FIX: Now properly traces connectors to determine if DML is actually
        inside the loop path (nextValueConnector) vs. outside (noMoreValuesConnector).

        The correct pattern is:
        - Loop → Assignment (collect records) → back to Loop
        - Loop (noMoreValuesConnector) → DML (OUTSIDE loop - this is correct!)

        We should only flag DML that is reachable via nextValueConnector path.
        """
        loops = self.root.findall('.//sf:loops', self.namespace)
        if not loops:
            return False

        # Build element lookup map for faster access
        element_map = self._build_element_map()

        for loop in loops:
            loop_name_elem = loop.find('sf:name', self.namespace)
            loop_name = loop_name_elem.text if loop_name_elem is not None else ''

            # Get the nextValueConnector target (this is the loop body - INSIDE the loop)
            next_connector = loop.find('sf:nextValueConnector/sf:targetReference', self.namespace)
            if next_connector is None:
                continue

            # Get the noMoreValuesConnector target (this is OUTSIDE the loop)
            exit_connector = loop.find('sf:noMoreValuesConnector/sf:targetReference', self.namespace)
            exit_target = exit_connector.text if exit_connector is not None else None

            # Trace the path from nextValueConnector, stopping at the loop itself or exit
            visited = set()
            if self._has_dml_in_path(next_connector.text, loop_name, exit_target, visited, element_map):
                return True

        return False

    def _build_element_map(self) -> Dict[str, ET.Element]:
        """Build a map of element names to elements for fast lookup."""
        element_map = {}
        element_types = [
            'assignments', 'decisions', 'recordCreates', 'recordUpdates',
            'recordDeletes', 'recordLookups', 'loops', 'subflows', 'screens',
            'actionCalls', 'waits', 'transforms'
        ]
        for elem_type in element_types:
            for elem in self.root.findall(f'.//sf:{elem_type}', self.namespace):
                name_elem = elem.find('sf:name', self.namespace)
                if name_elem is not None:
                    element_map[name_elem.text] = (elem_type, elem)
        return element_map

    def _has_dml_in_path(self, current: str, loop_name: str, exit_target: str,
                         visited: set, element_map: Dict) -> bool:
        """
        Recursively check if a path contains DML operations.

        Args:
            current: Current element name to check
            loop_name: Name of the loop we started from (to detect loop-back)
            exit_target: The noMoreValuesConnector target (path after loop exits)
            visited: Set of visited elements to prevent infinite loops
            element_map: Map of element names to (type, element) tuples

        Returns:
            True if DML is found in the loop body path
        """
        if current in visited:
            return False
        if current == loop_name:
            # We've looped back to the loop itself - this is expected, no DML found on this path
            return False
        if current == exit_target:
            # We've reached the exit path - DML here is OUTSIDE the loop (correct pattern)
            return False

        visited.add(current)

        if current not in element_map:
            return False

        elem_type, elem = element_map[current]

        # Check if this element is a DML operation
        if elem_type in ['recordCreates', 'recordUpdates', 'recordDeletes']:
            return True

        # Follow all connectors from this element
        connectors = []

        # Standard connector
        connector = elem.find('sf:connector/sf:targetReference', self.namespace)
        if connector is not None:
            connectors.append(connector.text)

        # Fault connector (don't follow - error path)
        # Decision rules
        for rule in elem.findall('.//sf:rules', self.namespace):
            rule_connector = rule.find('sf:connector/sf:targetReference', self.namespace)
            if rule_connector is not None:
                connectors.append(rule_connector.text)

        # Default connector for decisions
        default_connector = elem.find('sf:defaultConnector/sf:targetReference', self.namespace)
        if default_connector is not None:
            connectors.append(default_connector.text)

        # Recursively check all paths
        for next_target in connectors:
            if self._has_dml_in_path(next_target, loop_name, exit_target, visited.copy(), element_map):
                return True

        return False

    def _has_transform(self) -> bool:
        """Check if flow uses Transform element."""
        return self._count_elements('transforms') > 0

    def _should_use_transform(self) -> bool:
        """Check if flow should use Transform element."""
        # Has loops and assignments (field mapping pattern)
        return self._count_elements('loops') > 0 and self._count_elements('assignments') > 0

    def _count_dml_with_fault_paths(self) -> int:
        """Count DML operations with fault paths."""
        count = 0
        for dml_type in ['recordCreates', 'recordUpdates', 'recordDeletes']:
            for element in self.root.findall(f'.//sf:{dml_type}', self.namespace):
                fault = element.find('sf:faultConnector', self.namespace)
                if fault is not None:
                    count += 1
        return count

    def _has_error_logging(self) -> bool:
        """
        Check if flow has error logging.

        v2.1.0 FIX: Now also detects inline error logging patterns, not just subflows.
        """
        # Check for subflow-based error logging
        for subflow in self.root.findall('.//sf:subflows', self.namespace):
            flow_name = subflow.find('sf:flowName', self.namespace)
            if flow_name is not None and 'LogError' in flow_name.text:
                return True

        # Check for inline error logging patterns (v2.1.0)
        # Pattern 1: Assignment that references $Flow.FaultMessage
        for assignment in self.root.findall('.//sf:assignments', self.namespace):
            for item in assignment.findall('.//sf:assignmentItems', self.namespace):
                value_elem = item.find('sf:value/sf:elementReference', self.namespace)
                if value_elem is not None and 'FaultMessage' in (value_elem.text or ''):
                    return True

        # Pattern 2: Record create with Error_Log or similar object
        for create in self.root.findall('.//sf:recordCreates', self.namespace):
            # Check input reference for error-related naming
            input_ref = create.find('sf:inputReference', self.namespace)
            if input_ref is not None:
                ref_text = input_ref.text or ''
                if any(pattern in ref_text.lower() for pattern in ['error', 'log', 'fault']):
                    return True

            # Check object type
            obj = create.find('sf:object', self.namespace)
            if obj is not None:
                obj_text = obj.text or ''
                if any(pattern in obj_text.lower() for pattern in ['error', 'log']):
                    return True

        return False


    def _estimate_line_count(self) -> int:
        """Estimate line count of flow XML."""
        # Rough estimate based on element count
        total_elements = sum([
            self._count_elements('decisions'),
            self._count_elements('assignments'),
            self._count_elements('recordCreates'),
            self._count_elements('recordUpdates'),
            self._count_elements('recordDeletes'),
            self._count_elements('recordLookups'),
            self._count_elements('subflows'),
            self._count_elements('loops')
        ])
        return total_elements * 15  # ~15 lines per element

    def _is_autolaunched(self) -> bool:
        """Check if flow is autolaunched."""
        process_type = self._get_text('processType')
        return process_type == 'AutoLaunchedFlow'

    def _has_input_output(self) -> bool:
        """Check if flow has input or output variables."""
        for var in self.root.findall('.//sf:variables', self.namespace):
            is_input = var.find('sf:isInput', self.namespace)
            is_output = var.find('sf:isOutput', self.namespace)
            if (is_input is not None and is_input.text == 'true') or \
               (is_output is not None and is_output.text == 'true'):
                return True
        return False

    # ═══════════════════════════════════════════════════════════════════════
    # NEW VALIDATION HELPERS (v2.0.0)
    # ═══════════════════════════════════════════════════════════════════════

    def _has_store_output_automatically(self) -> List[str]:
        """
        Check for recordLookups with storeOutputAutomatically=true.
        This stores ALL fields and can cause data leaks and performance issues.

        Returns:
            List of element names with this issue
        """
        issues = []
        for lookup in self.root.findall('.//sf:recordLookups', self.namespace):
            store_auto = lookup.find('sf:storeOutputAutomatically', self.namespace)
            if store_auto is not None and store_auto.text == 'true':
                name = lookup.find('sf:name', self.namespace)
                element_name = name.text if name is not None else 'Unknown'
                issues.append(element_name)
        return issues

    def _get_trigger_object(self) -> str:
        """Get the object that triggers this record-triggered flow."""
        start = self.root.find('.//sf:start', self.namespace)
        if start is not None:
            obj = start.find('sf:object', self.namespace)
            if obj is not None:
                return obj.text
        return ''

    def _has_same_object_query(self) -> List[str]:
        """
        Check if record-triggered flow queries the same object it triggers on.
        This is an anti-pattern - use $Record instead.

        Returns:
            List of element names that query the trigger object
        """
        trigger_object = self._get_trigger_object()
        if not trigger_object:
            return []

        issues = []
        for lookup in self.root.findall('.//sf:recordLookups', self.namespace):
            obj = lookup.find('sf:object', self.namespace)
            if obj is not None and obj.text == trigger_object:
                name = lookup.find('sf:name', self.namespace)
                element_name = name.text if name is not None else 'Unknown'
                issues.append(element_name)
        return issues

    def _has_formula_in_loops(self) -> bool:
        """
        Check if complex formulas are referenced inside loops.
        This can cause CPU timeout with large datasets.
        """
        # Check for formula variables
        formulas = self.root.findall('.//sf:formulas', self.namespace)
        if not formulas:
            return False

        # Check if loops exist
        loops = self.root.findall('.//sf:loops', self.namespace)
        if not loops:
            return False

        # Simplified check: if flow has both formulas and loops, warn
        # A more sophisticated check would trace the execution path
        return len(formulas) > 0 and len(loops) > 0

    def _get_lookups_without_filters(self) -> List[str]:
        """
        Get recordLookups elements without filter conditions.
        Unbounded queries can hit governor limits.

        Returns:
            List of element names without filters
        """
        issues = []
        for lookup in self.root.findall('.//sf:recordLookups', self.namespace):
            filters = lookup.findall('sf:filters', self.namespace)
            if not filters:
                name = lookup.find('sf:name', self.namespace)
                element_name = name.text if name is not None else 'Unknown'
                issues.append(element_name)
        return issues

    def _get_lookups_without_null_check(self) -> List[str]:
        """
        Check for recordLookups that may not have null checks.
        Simplified check - looks for decision elements after lookups.

        Returns:
            List of element names that may need null checks
        """
        # This is a simplified heuristic - full analysis would require graph traversal
        lookup_count = self._count_elements('recordLookups')
        decision_count = self._count_elements('decisions')

        # If we have lookups but few decisions, some may lack null checks
        if lookup_count > 0 and decision_count < lookup_count:
            issues = []
            for lookup in self.root.findall('.//sf:recordLookups', self.namespace):
                name = lookup.find('sf:name', self.namespace)
                element_name = name.text if name is not None else 'Unknown'
                issues.append(element_name)
            return issues[:lookup_count - decision_count]  # Return likely unchecked ones
        return []

    def _get_lookups_without_first_record_only(self) -> List[str]:
        """
        Get recordLookups where single record is expected but getFirstRecordOnly is not set.
        Heuristic: element name suggests single record (Get, var, rec prefix without 's').

        Returns:
            List of element names that could use getFirstRecordOnly
        """
        issues = []
        single_indicators = ['Get', 'var_', 'rec_', 'record', 'single', 'one']
        collection_indicators = ['col_', 'list', 'all', 'many', 'multiple', 'records']

        for lookup in self.root.findall('.//sf:recordLookups', self.namespace):
            get_first = lookup.find('sf:getFirstRecordOnly', self.namespace)

            # Skip if already set to true
            if get_first is not None and get_first.text == 'true':
                continue

            name = lookup.find('sf:name', self.namespace)
            element_name = name.text if name is not None else ''

            # Check if name suggests single record
            is_likely_single = any(ind.lower() in element_name.lower() for ind in single_indicators)
            is_likely_collection = any(ind.lower() in element_name.lower() for ind in collection_indicators)

            if is_likely_single and not is_likely_collection:
                issues.append(element_name)

        return issues

    # ═══════════════════════════════════════════════════════════════════════
    # NEW VALIDATION CHECKS (v2.2.0) - Lightning Flow Scanner Parity
    # ═══════════════════════════════════════════════════════════════════════

    def _check_hardcoded_ids(self) -> List[str]:
        """
        Check for hardcoded Salesforce IDs in the flow.
        IDs are 15 or 18 character alphanumeric strings starting with specific prefixes.

        Returns:
            List of element names containing hardcoded IDs
        """
        issues = []
        # Salesforce ID pattern: 15 or 18 chars, starts with 001, 003, 005, etc.
        # Common prefixes: 001 (Account), 003 (Contact), 005 (User), 00Q (Lead), etc.
        id_pattern = r'\b(001|003|005|006|00Q|00U|00G|00e|00D|00k|00T|00P|00I|00O|a[0-9A-Za-z]{2})[a-zA-Z0-9]{12,15}\b'

        # Check all text content in the flow
        for elem in self.root.iter():
            if elem.text:
                import re
                matches = re.findall(id_pattern, elem.text)
                if matches:
                    # Find the parent element name
                    parent = elem
                    while parent is not None:
                        name_elem = parent.find('sf:name', self.namespace)
                        if name_elem is not None:
                            issues.append(name_elem.text)
                            break
                        parent = parent.getparent() if hasattr(parent, 'getparent') else None
                    if parent is None:
                        issues.append('Unknown element')

        return list(set(issues))  # Deduplicate

    def _check_hardcoded_urls(self) -> List[str]:
        """
        Check for hardcoded URLs in the flow.
        URLs should use Custom Labels or Custom Metadata for environment portability.

        Returns:
            List of element names containing hardcoded URLs
        """
        issues = []
        import re
        # URL pattern - matches http:// or https:// URLs
        url_pattern = r'https?://[^\s<>"\'\}]+'

        # Allowed patterns (Salesforce system URLs)
        allowed_patterns = [
            r'https?://\{!\$Api\.Partner_Server_URL',
            r'https?://.*\.salesforce\.com',
            r'https?://.*\.force\.com',
        ]

        for elem in self.root.iter():
            if elem.text:
                matches = re.findall(url_pattern, elem.text)
                for match in matches:
                    # Skip allowed patterns
                    is_allowed = any(re.match(pattern, match) for pattern in allowed_patterns)
                    if not is_allowed:
                        # Find element name
                        parent = elem
                        while parent is not None:
                            name_elem = parent.find('sf:name', self.namespace)
                            if name_elem is not None:
                                issues.append(name_elem.text)
                                break
                            parent = parent.getparent() if hasattr(parent, 'getparent') else None

        return list(set(issues))

    def _check_unused_variables(self) -> List[str]:
        """
        Check for variables that are defined but never referenced.

        Returns:
            List of unused variable names
        """
        # Get all defined variables
        defined_vars = set()
        for var in self.root.findall('.//sf:variables', self.namespace):
            name = var.find('sf:name', self.namespace)
            if name is not None:
                defined_vars.add(name.text)

        # Get all referenced variables (in elementReference, inputReference, etc.)
        referenced_vars = set()
        reference_tags = ['elementReference', 'inputReference', 'outputReference', 'value']

        for tag in reference_tags:
            for elem in self.root.findall(f'.//{{{self.namespace["sf"]}}}{tag}', self.namespace):
                if elem.text:
                    # Variable references can be like "varName" or "varName.field"
                    var_name = elem.text.split('.')[0]
                    referenced_vars.add(var_name)

        # Also check formula expressions for variable references
        for formula in self.root.findall('.//sf:formulas', self.namespace):
            expr = formula.find('sf:expression', self.namespace)
            if expr is not None and expr.text:
                # Simple extraction of variable-like tokens
                import re
                tokens = re.findall(r'\{!\s*(\w+)', expr.text)
                referenced_vars.update(tokens)

        # Find unused
        unused = defined_vars - referenced_vars
        return list(unused)

    def _check_unconnected_elements(self) -> List[str]:
        """
        Check for elements that have no incoming connectors (orphaned elements).
        Excludes Start element and variables.

        Returns:
            List of unconnected element names
        """
        # Get all element names
        all_elements = set()
        element_types = [
            'assignments', 'decisions', 'recordCreates', 'recordUpdates',
            'recordDeletes', 'recordLookups', 'loops', 'subflows', 'screens',
            'actionCalls', 'waits', 'transforms'
        ]

        for elem_type in element_types:
            for elem in self.root.findall(f'.//sf:{elem_type}', self.namespace):
                name = elem.find('sf:name', self.namespace)
                if name is not None:
                    all_elements.add(name.text)

        # Get all connector targets (elements that are connected TO)
        connected_elements = set()

        # Start element target
        start = self.root.find('.//sf:start', self.namespace)
        if start is not None:
            start_connector = start.find('sf:connector/sf:targetReference', self.namespace)
            if start_connector is not None:
                connected_elements.add(start_connector.text)

        # All other connectors
        for connector in self.root.findall('.//sf:targetReference', self.namespace):
            if connector.text:
                connected_elements.add(connector.text)

        # Find unconnected (orphaned) elements
        orphaned = all_elements - connected_elements
        return list(orphaned)

    def _check_recursive_after_update(self) -> bool:
        """
        Check if an after-save record-triggered flow updates the same object
        without proper entry conditions (infinite loop risk).

        Returns:
            True if recursive update pattern detected
        """
        # Only applies to record-triggered flows
        start = self.root.find('.//sf:start', self.namespace)
        if start is None:
            return False

        trigger_type = start.find('sf:triggerType', self.namespace)
        if trigger_type is None or trigger_type.text != 'RecordAfterSave':
            return False

        # Get trigger object
        trigger_object = start.find('sf:object', self.namespace)
        if trigger_object is None:
            return False
        trigger_obj_name = trigger_object.text

        # Check if flow updates the same object
        for update in self.root.findall('.//sf:recordUpdates', self.namespace):
            obj = update.find('sf:object', self.namespace)
            input_ref = update.find('sf:inputReference', self.namespace)

            # Direct object match
            if obj is not None and obj.text == trigger_obj_name:
                # Check for entry conditions
                has_entry_conditions = False
                filter_logic = start.find('sf:filterLogic', self.namespace)
                filters = start.findall('sf:filters', self.namespace)

                if filter_logic is not None or len(filters) > 0:
                    has_entry_conditions = True

                if not has_entry_conditions:
                    return True

            # $Record reference (updating trigger record)
            if input_ref is not None and input_ref.text == '$Record':
                has_entry_conditions = False
                filter_logic = start.find('sf:filterLogic', self.namespace)
                filters = start.findall('sf:filters', self.namespace)

                if filter_logic is not None or len(filters) > 0:
                    has_entry_conditions = True

                if not has_entry_conditions:
                    return True

        return False

    def _has_soql_in_loops(self) -> bool:
        """
        Check if SOQL queries (recordLookups) exist inside loops by tracing connector paths.
        Similar to _has_dml_in_loops but for queries.

        Returns:
            True if SOQL found inside loop path
        """
        loops = self.root.findall('.//sf:loops', self.namespace)
        if not loops:
            return False

        element_map = self._build_element_map()

        for loop in loops:
            loop_name_elem = loop.find('sf:name', self.namespace)
            loop_name = loop_name_elem.text if loop_name_elem is not None else ''

            next_connector = loop.find('sf:nextValueConnector/sf:targetReference', self.namespace)
            if next_connector is None:
                continue

            exit_connector = loop.find('sf:noMoreValuesConnector/sf:targetReference', self.namespace)
            exit_target = exit_connector.text if exit_connector is not None else None

            visited = set()
            if self._has_soql_in_path(next_connector.text, loop_name, exit_target, visited, element_map):
                return True

        return False

    def _has_soql_in_path(self, current: str, loop_name: str, exit_target: str,
                          visited: set, element_map: dict) -> bool:
        """
        Recursively check if a path contains SOQL operations (recordLookups).
        """
        if current in visited:
            return False
        if current == loop_name:
            return False
        if current == exit_target:
            return False

        visited.add(current)

        if current not in element_map:
            return False

        elem_type, elem = element_map[current]

        # Check if this element is a SOQL operation
        if elem_type == 'recordLookups':
            return True

        # Follow connectors
        connectors = []
        connector = elem.find('sf:connector/sf:targetReference', self.namespace)
        if connector is not None:
            connectors.append(connector.text)

        for rule in elem.findall('.//sf:rules', self.namespace):
            rule_connector = rule.find('sf:connector/sf:targetReference', self.namespace)
            if rule_connector is not None:
                connectors.append(rule_connector.text)

        default_connector = elem.find('sf:defaultConnector/sf:targetReference', self.namespace)
        if default_connector is not None:
            connectors.append(default_connector.text)

        for next_target in connectors:
            if self._has_soql_in_path(next_target, loop_name, exit_target, visited.copy(), element_map):
                return True

        return False

    def _check_action_calls_in_loop(self) -> bool:
        """
        Check if Apex action calls exist inside loops (callout limit risk).

        Returns:
            True if action calls found inside loop path
        """
        loops = self.root.findall('.//sf:loops', self.namespace)
        if not loops:
            return False

        element_map = self._build_element_map()

        for loop in loops:
            loop_name_elem = loop.find('sf:name', self.namespace)
            loop_name = loop_name_elem.text if loop_name_elem is not None else ''

            next_connector = loop.find('sf:nextValueConnector/sf:targetReference', self.namespace)
            if next_connector is None:
                continue

            exit_connector = loop.find('sf:noMoreValuesConnector/sf:targetReference', self.namespace)
            exit_target = exit_connector.text if exit_connector is not None else None

            visited = set()
            if self._has_action_in_path(next_connector.text, loop_name, exit_target, visited, element_map):
                return True

        return False

    def _has_action_in_path(self, current: str, loop_name: str, exit_target: str,
                            visited: set, element_map: dict) -> bool:
        """Check if path contains actionCalls."""
        if current in visited or current == loop_name or current == exit_target:
            return False

        visited.add(current)

        if current not in element_map:
            return False

        elem_type, elem = element_map[current]

        if elem_type == 'actionCalls':
            return True

        connectors = []
        connector = elem.find('sf:connector/sf:targetReference', self.namespace)
        if connector is not None:
            connectors.append(connector.text)

        for rule in elem.findall('.//sf:rules', self.namespace):
            rule_connector = rule.find('sf:connector/sf:targetReference', self.namespace)
            if rule_connector is not None:
                connectors.append(rule_connector.text)

        default_connector = elem.find('sf:defaultConnector/sf:targetReference', self.namespace)
        if default_connector is not None:
            connectors.append(default_connector.text)

        for next_target in connectors:
            if self._has_action_in_path(next_target, loop_name, exit_target, visited.copy(), element_map):
                return True

        return False

    def _check_duplicate_dml_between_screens(self) -> List[str]:
        """
        Check for DML operations between screen elements.
        This can cause issues with the back button in screen flows.

        Returns:
            List of DML element names between screens
        """
        issues = []
        screens = self.root.findall('.//sf:screens', self.namespace)

        if len(screens) < 2:
            return issues

        # Build a simple flow graph
        element_map = self._build_element_map()

        for screen in screens:
            screen_name = screen.find('sf:name', self.namespace)
            if screen_name is None:
                continue

            # Check path from this screen to next screen
            connector = screen.find('sf:connector/sf:targetReference', self.namespace)
            if connector is None:
                continue

            # Follow path until we hit another screen
            visited = set()
            current = connector.text

            while current and current not in visited:
                visited.add(current)

                if current not in element_map:
                    break

                elem_type, elem = element_map[current]

                # Found another screen - stop
                if elem_type == 'screens':
                    break

                # Found DML between screens
                if elem_type in ['recordCreates', 'recordUpdates', 'recordDeletes']:
                    name = elem.find('sf:name', self.namespace)
                    if name is not None:
                        issues.append(name.text)

                # Move to next element
                next_connector = elem.find('sf:connector/sf:targetReference', self.namespace)
                current = next_connector.text if next_connector is not None else None

        return list(set(issues))

    def _check_auto_layout(self) -> bool:
        """
        Check if flow uses Auto-Layout (Canvas mode preference).

        Returns:
            True if NOT using Auto-Layout (manual positioning)
        """
        # Check for processMetadataValues with Canvas positioning
        for pmv in self.root.findall('.//sf:processMetadataValues', self.namespace):
            name = pmv.find('sf:name', self.namespace)
            if name is not None and name.text == 'CanvasMode':
                value = pmv.find('sf:value/sf:stringValue', self.namespace)
                if value is not None and value.text == 'AUTO_LAYOUT_CANVAS':
                    return False  # Using Auto-Layout - good

        # If no CanvasMode found or not AUTO_LAYOUT, it's manual
        return True

    def _check_copy_api_name(self) -> List[str]:
        """
        Check for elements with "Copy_X_Of" naming pattern (lazy naming).

        Returns:
            List of element names matching the copy pattern
        """
        issues = []
        import re
        copy_pattern = r'^Copy_\d+_of_|^Copy_of_'

        element_types = [
            'assignments', 'decisions', 'recordCreates', 'recordUpdates',
            'recordDeletes', 'recordLookups', 'loops', 'subflows', 'screens',
            'actionCalls', 'variables', 'formulas'
        ]

        for elem_type in element_types:
            for elem in self.root.findall(f'.//sf:{elem_type}', self.namespace):
                name = elem.find('sf:name', self.namespace)
                if name is not None and re.match(copy_pattern, name.text, re.IGNORECASE):
                    issues.append(name.text)

        return issues

    def _is_scheduled_flow(self) -> bool:
        """Check if this is a scheduled flow."""
        start = self.root.find('.//sf:start', self.namespace)
        if start is not None:
            trigger_type = start.find('sf:triggerType', self.namespace)
            if trigger_type is not None and trigger_type.text == 'Scheduled':
                return True
            schedule = start.find('sf:schedule', self.namespace)
            if schedule is not None:
                return True
        return False

    def _is_active(self) -> bool:
        """Check if flow status is Active."""
        status = self._get_text('status')
        return status == 'Active'

    def _get_rating(self, score: int) -> str:
        """Get rating based on score."""
        percentage = (score / self.total_max) * 100

        if percentage >= 95:
            return "⭐⭐⭐⭐⭐ Excellent"
        elif percentage >= 85:
            return "⭐⭐⭐⭐ Very Good"
        elif percentage >= 75:
            return "⭐⭐⭐ Good"
        elif percentage >= 60:
            return "⭐⭐ Fair"
        else:
            return "⭐ Needs Improvement"

    def generate_report(self) -> str:
        """Generate comprehensive validation report."""
        results = self.validate()

        report = []
        report.append("\n" + "═"*70)
        report.append(f"   Flow Validation Report: {results['flow_name']} (API {results['api_version']})")
        report.append("═"*70)

        # Overall score
        report.append(f"\n🎯 Best Practices Score: {results['overall_score']}/{self.total_max} {results['rating']}")

        # Category breakdown
        report.append("\n" + "─"*70)
        report.append("CATEGORY BREAKDOWN:")
        report.append("─"*70)

        categories = {
            'design_naming': '📋 Design & Naming',
            'logic_structure': '🧩 Logic & Structure',
            'architecture_orchestration': '🏗️  Architecture & Orchestration',
            'performance_bulk': '⚡ Performance & Bulk Safety',
            'error_handling': '🔧 Error Handling & Observability',
            'security_governance': '🔒 Security & Governance'
        }

        for key, label in categories.items():
            cat = results['categories'][key]
            score = cat['score']
            max_score = cat['max_score']
            percentage = (score / max_score) * 100

            status = "✅" if percentage == 100 else "⚠️" if percentage >= 70 else "❌"
            report.append(f"\n{status} {label}: {score}/{max_score} ({percentage:.0f}%)")

            # Show issues
            if cat.get('critical_issues'):
                for issue in cat['critical_issues']:
                    report.append(f"   ❌ CRITICAL: {issue['message']}")

            if cat.get('warnings'):
                for warning in cat['warnings'][:2]:  # Limit to 2
                    report.append(f"   ⚠️  {warning['message']}")

            if cat.get('advisory'):
                for adv in cat['advisory'][:2]:  # Limit to 2
                    report.append(f"   ℹ️  {adv['message']}")

        # Critical issues summary
        if results['critical_issues']:
            report.append("\n" + "═"*70)
            report.append("❌ CRITICAL ISSUES (Must Fix):")
            report.append("═"*70)
            for issue in results['critical_issues']:
                report.append(f"\n{issue['message']}")
                report.append(f"   Fix: {issue['fix']}")

        # Recommendations
        if results['advisory_suggestions']:
            report.append("\n" + "═"*70)
            report.append("💡 Recommendations for Improvement:")
            report.append("═"*70)
            for i, adv in enumerate(results['advisory_suggestions'][:5], 1):
                report.append(f"\n{i}. [{adv['category']}] {adv['message']}")
                report.append(f"   → {adv['suggestion']}")

        # Footer
        report.append("\n" + "═"*70)
        if results['critical_issues']:
            report.append("⛔ DEPLOYMENT BLOCKED - Fix critical issues first")
        else:
            report.append("✅ DEPLOYMENT APPROVED (advisory recommendations provided)")
        report.append("═"*70)

        # Deployment reminder - always shown when approved
        if not results['critical_issues']:
            report.append("")
            report.append("📦 NEXT STEP - Use sf-deploy skill (REQUIRED):")
            report.append("─"*70)
            report.append("   Skill(skill=\"sf-deploy\")")
            report.append("   Request: \"Deploy flow to [target-org] with --dry-run first\"")
            report.append("")
            report.append("   ⚠️  NEVER use 'sf project deploy' directly via Bash")
            report.append("   ✅  ALWAYS use sf-deploy skill for consistent deployment")
            report.append("═"*70)

        report.append("\n")

        return "\n".join(report)


def validate_flow(flow_xml_path: str) -> Dict:
    """
    Validate a flow and return results.

    Args:
        flow_xml_path: Path to flow XML file

    Returns:
        Validation results dictionary
    """
    validator = EnhancedFlowValidator(flow_xml_path)
    return validator.validate()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python enhanced_validator.py <path-to-flow.xml>")
        sys.exit(1)

    flow_path = sys.argv[1]

    try:
        validator = EnhancedFlowValidator(flow_path)
        report = validator.generate_report()
        print(report)

        # Exit code based on critical issues
        results = validator.validate()
        sys.exit(1 if results['critical_issues'] else 0)

    except Exception as e:
        print(f"Error validating flow: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
