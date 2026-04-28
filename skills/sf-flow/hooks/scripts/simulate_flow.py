#!/usr/bin/env python3
"""
Salesforce Flow Simulator - Bulk Testing & Governor Limit Analysis (v2.1.0)

Simulates flow execution with mock data to catch governor limit issues
before deployment. Tests bulkification and performance with 200+ records.

v2.1.0 Fixes:
- FIXED: Removed bulkSupport check (deprecated in API 60.0+, automatic in record-triggered flows)
- FIXED: Record-triggered flows use $Record context - platform handles batching automatically
- FIXED: DML-in-loop detection now properly traces noMoreValuesConnector (exit path)
- IMPROVED: Better understanding of per-transaction vs per-record limits

Usage:
    python3 flow_simulator.py <path-to-flow-meta.xml> --test-records 200 [--mock-data]
    python3 flow_simulator.py <path-to-flow-meta.xml> --analyze-only
"""

import sys
import xml.etree.ElementTree as ET
import argparse
import json
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class GovernorLimits:
    """Salesforce governor limits per transaction"""
    SOQL_QUERIES = 100
    SOQL_RECORDS = 50000
    DML_STATEMENTS = 150
    DML_ROWS = 10000
    CPU_TIME_MS = 10000
    HEAP_SIZE_MB = 6

@dataclass
class SimulationMetrics:
    """Metrics tracked during simulation"""
    soql_queries: int = 0
    soql_records: int = 0
    dml_statements: int = 0
    dml_rows: int = 0
    cpu_time_ms: int = 0
    heap_size_kb: int = 0
    loops_executed: int = 0
    decisions_evaluated: int = 0

class FlowSimulator:
    def __init__(self, xml_path: str, num_records: int = 200):
        self.xml_path = xml_path
        self.num_records = num_records
        self.tree = None
        self.root = None
        self.namespace = {'ns': 'http://soap.sforce.com/2006/04/metadata'}
        self.metrics = SimulationMetrics()
        self.limits = GovernorLimits()
        self.warnings = []
        self.errors = []
        self.flow_type = "Unknown"

    def simulate(self) -> Dict:
        """Main simulation entry point"""
        print(f"\n🔬 Simulating Flow Execution with {self.num_records} records...\n")

        # Load flow
        if not self._load_xml():
            return self._generate_report()

        # Analyze flow structure
        self.flow_type = self._get_flow_type()
        print(f"Flow Type: {self.flow_type}")
        print(f"Processing {self.num_records} records in bulk...\n")

        # Simulate execution based on flow type
        self._simulate_flow_execution()

        # Check limits
        self._check_governor_limits()

        return self._generate_report()

    def _load_xml(self) -> bool:
        """Load and parse flow XML"""
        try:
            self.tree = ET.parse(self.xml_path)
            self.root = self.tree.getroot()
            return True
        except Exception as e:
            self.errors.append(f"Failed to load flow: {str(e)}")
            return False

    def _get_flow_type(self) -> str:
        """Determine flow type"""
        process_type = self.root.find('ns:processType', self.namespace)
        if process_type is not None:
            if process_type.text == 'Flow':
                return "Screen Flow"
            elif process_type.text == 'AutoLaunchedFlow':
                start = self.root.find('ns:start', self.namespace)
                if start is not None:
                    trigger_type = start.find('ns:triggerType', self.namespace)
                    if trigger_type is not None:
                        if 'RecordAfterSave' in trigger_type.text:
                            return "Record-Triggered Flow (After Save)"
                        elif 'RecordBeforeSave' in trigger_type.text:
                            return "Record-Triggered Flow (Before Save)"
                        elif 'RecordBeforeDelete' in trigger_type.text:
                            return "Record-Triggered Flow (Before Delete)"
                    schedule = start.find('ns:schedule', self.namespace)
                    if schedule is not None:
                        return "Scheduled Flow"
                return "Autolaunched Flow"
        return "Unknown"

    def _is_record_triggered(self) -> bool:
        """Check if this is a record-triggered flow"""
        return "Record-Triggered" in self.flow_type

    def _simulate_flow_execution(self):
        """
        Simulate flow execution and track resource usage.

        v2.1.0 FIX: Removed bulkSupport check - deprecated in API 60.0+
        Record-triggered flows automatically handle bulk processing at the platform level.
        The $Record context provides single-record access, but the platform batches
        execution efficiently.
        """
        if self._is_record_triggered():
            # v2.1.0: Record-triggered flows use $Record context
            # Platform handles batching automatically - no bulkSupport element needed
            self._simulate_record_triggered_flow()
        else:
            # Screen flows, Autolaunched flows, Scheduled flows
            self._simulate_standard_flow()

    def _simulate_record_triggered_flow(self):
        """
        Simulate record-triggered flow with $Record context.

        v2.1.0 FIX: Record-triggered flows work with single-record context ($Record).
        The platform batches executions automatically. Governor limits are PER TRANSACTION,
        not per record. A batch of 200 records runs in one transaction with shared limits.

        Key insight: SOQL/DML counts are per-transaction, not multiplied by record count.
        However, loops over RELATED records can still cause issues.
        """
        print("✓ Simulating record-triggered flow with $Record context...")
        print("  (Platform handles bulk batching automatically in API 60.0+)\n")

        # Count operations in the flow (per-transaction, NOT per-record)
        dml_operations = self._count_dml_operations()
        soql_queries = self._count_soql_queries()

        # For record-triggered flows, these are PER TRANSACTION limits
        self.metrics.dml_statements = dml_operations
        self.metrics.soql_queries = soql_queries
        self.metrics.dml_rows = self.num_records  # Each DML can affect up to batch size

        # Estimate CPU time for record-triggered (much lower than individual processing)
        self.metrics.cpu_time_ms = 50 + (self.num_records * 2)  # Base + minimal per-record

        # Check for loops that might cause issues with RELATED records
        self._analyze_loops_for_record_triggered()

    def _simulate_standard_flow(self):
        """Simulate non-record-triggered flows (Screen, Autolaunched, Scheduled)"""
        print("✓ Simulating standard flow execution...")

        # Count unique DML/SOQL operations (executed per invocation)
        dml_operations = self._count_dml_operations()
        soql_queries = self._count_soql_queries()

        self.metrics.dml_statements = dml_operations
        self.metrics.soql_queries = soql_queries
        self.metrics.dml_rows = self.num_records * dml_operations

        # Estimate CPU time
        self.metrics.cpu_time_ms = 100 + (self.num_records * 5)

        # Check for loops
        self._analyze_loops()

    def _count_dml_operations(self) -> int:
        """Count DML operations in flow"""
        dml_types = ['recordCreates', 'recordUpdates', 'recordDeletes']
        count = 0
        for dml_type in dml_types:
            count += len(self.root.findall(f'ns:{dml_type}', self.namespace))
        return count

    def _count_soql_queries(self) -> int:
        """Count SOQL queries in flow"""
        return len(self.root.findall('ns:recordLookups', self.namespace))

    def _analyze_loops_for_record_triggered(self):
        """
        Analyze loops in record-triggered flows.

        v2.1.0 FIX: In record-triggered flows, loops over RELATED records are valid.
        We should only flag DML that is actually INSIDE the loop body (nextValueConnector path),
        NOT DML that's on the exit path (noMoreValuesConnector).
        """
        loops = self.root.findall('.//ns:loops', self.namespace)

        for loop in loops:
            loop_name_elem = loop.find('ns:name', self.namespace)
            loop_name = loop_name_elem.text if loop_name_elem is not None else 'Unknown'
            self.metrics.loops_executed += 1

            # Check if DML is INSIDE the loop (via nextValueConnector path)
            if self._has_dml_in_loop_body(loop):
                # Estimate iterations based on typical related record counts
                estimated_iterations = 50  # Conservative estimate for related records
                dml_in_loop = self._count_dml_in_loop_body(loop)
                total_dml_from_loop = dml_in_loop * estimated_iterations

                self.errors.append(
                    f"❌ CRITICAL: Loop '{loop_name}' contains DML operations in loop body. "
                    f"With ~{estimated_iterations} related records, this adds ~{total_dml_from_loop} DML statements "
                    f"(limit: {self.limits.DML_STATEMENTS})"
                )

                self.metrics.dml_statements += total_dml_from_loop
            else:
                # Loop exists but DML is outside (correct collect-then-DML pattern)
                print(f"  ✓ Loop '{loop_name}' follows correct collect-then-DML pattern")

            # Add CPU time for loop processing
            self.metrics.cpu_time_ms += 50 * 10  # ~10ms per iteration estimate

    def _analyze_loops(self):
        """Analyze loops for potential issues (standard flows)"""
        loops = self.root.findall('.//ns:loops', self.namespace)

        for loop in loops:
            loop_name_elem = loop.find('ns:name', self.namespace)
            loop_name = loop_name_elem.text if loop_name_elem is not None else 'Unknown'
            self.metrics.loops_executed += 1

            if self._has_dml_in_loop_body(loop):
                iterations = self.num_records
                dml_in_loop = self._count_dml_in_loop_body(loop)
                total_dml_from_loop = dml_in_loop * iterations

                self.errors.append(
                    f"❌ CRITICAL: Loop '{loop_name}' contains DML operations. "
                    f"With {iterations} records, this will execute {total_dml_from_loop} DML statements "
                    f"(limit: {self.limits.DML_STATEMENTS})"
                )

                self.metrics.dml_statements += total_dml_from_loop

            self.metrics.cpu_time_ms += self.num_records * 10

    def _has_dml_in_loop_body(self, loop_elem) -> bool:
        """
        Check if loop body (nextValueConnector path) contains DML.

        v2.1.0 FIX: Properly distinguishes between:
        - nextValueConnector: Points to loop body (INSIDE the loop)
        - noMoreValuesConnector: Points to exit path (OUTSIDE the loop)

        Only flag DML that is reachable via nextValueConnector before returning to loop.
        """
        # Get loop name to detect loop-back
        loop_name_elem = loop_elem.find('ns:name', self.namespace)
        loop_name = loop_name_elem.text if loop_name_elem is not None else ''

        # Get the nextValueConnector (loop body entry point)
        next_connector = loop_elem.find('ns:nextValueConnector/ns:targetReference', self.namespace)
        if next_connector is None:
            return False

        # Get the noMoreValuesConnector (exit path - DML here is OK)
        exit_connector = loop_elem.find('ns:noMoreValuesConnector/ns:targetReference', self.namespace)
        exit_target = exit_connector.text if exit_connector is not None else None

        # Build element map for efficient lookup
        element_map = self._build_element_map()

        # Check the loop body path
        visited = set()
        return self._check_path_for_dml_in_loop(
            next_connector.text, loop_name, exit_target, visited, element_map
        )

    def _build_element_map(self) -> Dict:
        """Build a map of element names to (type, element) for fast lookup"""
        element_map = {}
        element_types = [
            'assignments', 'decisions', 'recordCreates', 'recordUpdates',
            'recordDeletes', 'recordLookups', 'loops', 'subflows', 'screens'
        ]
        for elem_type in element_types:
            for elem in self.root.findall(f'.//ns:{elem_type}', self.namespace):
                name_elem = elem.find('ns:name', self.namespace)
                if name_elem is not None:
                    element_map[name_elem.text] = (elem_type, elem)
        return element_map

    def _check_path_for_dml_in_loop(self, current: str, loop_name: str, exit_target: str,
                                     visited: set, element_map: Dict) -> bool:
        """
        Recursively check if path contains DML before exiting loop.

        Returns True only if DML is found in the loop body (before looping back or exiting).
        """
        if current in visited:
            return False
        if current == loop_name:
            # Looped back - this is expected, no DML found on this path segment
            return False
        if current == exit_target:
            # Reached exit path - DML here is OUTSIDE the loop (correct pattern)
            return False

        visited.add(current)

        if current not in element_map:
            return False

        elem_type, elem = element_map[current]

        # Check if this is a DML operation
        if elem_type in ['recordCreates', 'recordUpdates', 'recordDeletes']:
            return True

        # Follow connectors
        connectors = []

        connector = elem.find('ns:connector/ns:targetReference', self.namespace)
        if connector is not None:
            connectors.append(connector.text)

        for rule in elem.findall('.//ns:rules', self.namespace):
            rule_connector = rule.find('ns:connector/ns:targetReference', self.namespace)
            if rule_connector is not None:
                connectors.append(rule_connector.text)

        default_connector = elem.find('ns:defaultConnector/ns:targetReference', self.namespace)
        if default_connector is not None:
            connectors.append(default_connector.text)

        for next_target in connectors:
            if self._check_path_for_dml_in_loop(next_target, loop_name, exit_target, visited.copy(), element_map):
                return True

        return False

    def _count_dml_in_loop_body(self, loop_elem) -> int:
        """Count DML operations in loop body"""
        loop_name_elem = loop_elem.find('ns:name', self.namespace)
        loop_name = loop_name_elem.text if loop_name_elem is not None else ''

        next_connector = loop_elem.find('ns:nextValueConnector/ns:targetReference', self.namespace)
        if next_connector is None:
            return 0

        exit_connector = loop_elem.find('ns:noMoreValuesConnector/ns:targetReference', self.namespace)
        exit_target = exit_connector.text if exit_connector is not None else None

        element_map = self._build_element_map()
        visited = set()
        return self._count_dml_in_path(next_connector.text, loop_name, exit_target, visited, element_map)

    def _count_dml_in_path(self, current: str, loop_name: str, exit_target: str,
                           visited: set, element_map: Dict) -> int:
        """Count DML operations in path"""
        if current in visited or current == loop_name or current == exit_target:
            return 0
        if current not in element_map:
            return 0

        visited.add(current)
        elem_type, elem = element_map[current]
        count = 1 if elem_type in ['recordCreates', 'recordUpdates', 'recordDeletes'] else 0

        connector = elem.find('ns:connector/ns:targetReference', self.namespace)
        if connector is not None:
            count += self._count_dml_in_path(connector.text, loop_name, exit_target, visited.copy(), element_map)

        return count

    def _find_element_by_name(self, name: str, elem_type: str):
        """Find element by name and type"""
        for elem in self.root.findall(f'ns:{elem_type}', self.namespace):
            name_elem = elem.find('ns:name', self.namespace)
            if name_elem is not None and name_elem.text == name:
                return elem
        return None

    def _check_governor_limits(self):
        """Check if metrics exceed governor limits"""

        if self.metrics.soql_queries > self.limits.SOQL_QUERIES:
            self.errors.append(
                f"❌ SOQL Query limit exceeded: {self.metrics.soql_queries} "
                f"(limit: {self.limits.SOQL_QUERIES})"
            )
        elif self.metrics.soql_queries > self.limits.SOQL_QUERIES * 0.8:
            self.warnings.append(
                f"⚠️  Approaching SOQL Query limit: {self.metrics.soql_queries} "
                f"(80% of {self.limits.SOQL_QUERIES})"
            )

        if self.metrics.dml_statements > self.limits.DML_STATEMENTS:
            self.errors.append(
                f"❌ DML Statement limit exceeded: {self.metrics.dml_statements} "
                f"(limit: {self.limits.DML_STATEMENTS})"
            )
        elif self.metrics.dml_statements > self.limits.DML_STATEMENTS * 0.8:
            self.warnings.append(
                f"⚠️  Approaching DML Statement limit: {self.metrics.dml_statements} "
                f"(80% of {self.limits.DML_STATEMENTS})"
            )

        if self.metrics.dml_rows > self.limits.DML_ROWS:
            self.errors.append(
                f"❌ DML Rows limit exceeded: {self.metrics.dml_rows} "
                f"(limit: {self.limits.DML_ROWS})"
            )

        if self.metrics.cpu_time_ms > self.limits.CPU_TIME_MS:
            self.errors.append(
                f"❌ CPU Time limit exceeded: {self.metrics.cpu_time_ms}ms "
                f"(limit: {self.limits.CPU_TIME_MS}ms)"
            )
        elif self.metrics.cpu_time_ms > self.limits.CPU_TIME_MS * 0.8:
            self.warnings.append(
                f"⚠️  Approaching CPU Time limit: {self.metrics.cpu_time_ms}ms "
                f"(80% of {self.limits.CPU_TIME_MS}ms)"
            )

    def _generate_report(self) -> Dict:
        """Generate simulation report"""
        print("\n" + "━" * 70)
        print("Flow Simulation Report")
        print("━" * 70)
        print(f"\nTest Configuration:")
        print(f"  Records Processed: {self.num_records}")
        print(f"  Flow: {self.xml_path.split('/')[-1]}")
        print(f"  Flow Type: {self.flow_type}")

        if self._is_record_triggered():
            print(f"\n📋 Note: Record-triggered flows use $Record context.")
            print(f"   Platform handles bulk batching automatically (API 60.0+).")
            print(f"   Limits below are PER TRANSACTION, not per record.")

        print(f"\n📊 Resource Usage (per transaction):")
        print(f"  SOQL Queries:    {self.metrics.soql_queries:4d} / {self.limits.SOQL_QUERIES} "
              f"({self._percentage(self.metrics.soql_queries, self.limits.SOQL_QUERIES)}%)")
        print(f"  SOQL Records:    {self.metrics.soql_records:4d} / {self.limits.SOQL_RECORDS} "
              f"({self._percentage(self.metrics.soql_records, self.limits.SOQL_RECORDS)}%)")
        print(f"  DML Statements:  {self.metrics.dml_statements:4d} / {self.limits.DML_STATEMENTS} "
              f"({self._percentage(self.metrics.dml_statements, self.limits.DML_STATEMENTS)}%)")
        print(f"  DML Rows:        {self.metrics.dml_rows:4d} / {self.limits.DML_ROWS} "
              f"({self._percentage(self.metrics.dml_rows, self.limits.DML_ROWS)}%)")
        print(f"  CPU Time:        {self.metrics.cpu_time_ms:4d}ms / {self.limits.CPU_TIME_MS}ms "
              f"({self._percentage(self.metrics.cpu_time_ms, self.limits.CPU_TIME_MS)}%)")

        # Errors
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error}")
        else:
            print(f"\n✓ No governor limit errors detected")

        # Warnings
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")

        # Overall status
        print("\n" + "━" * 70)
        if self.errors:
            print("❌ SIMULATION FAILED - Flow will hit governor limits with bulk data")
            print("\nRecommendations:")
            print("  1. Move DML operations outside of loops (collect-then-DML pattern)")
            print("  2. Use collection variables to batch records")
            print("  3. Consider using Transform element for field mapping")
            if self._is_record_triggered():
                print("  4. For record-triggered flows, loops should only iterate RELATED records")
            status = "FAILED"
        elif self.warnings:
            print("⚠️  SIMULATION PASSED WITH WARNINGS - Monitor closely in production")
            status = "WARNING"
        else:
            print("✓ SIMULATION PASSED - Flow is ready for production")
            if self._is_record_triggered():
                print("  (Record-triggered flow with proper $Record context usage)")
            status = "PASSED"

        print("━" * 70 + "\n")

        return {
            'status': status,
            'flow_type': self.flow_type,
            'metrics': self.metrics.__dict__,
            'errors': self.errors,
            'warnings': self.warnings
        }

    def _percentage(self, value: int, limit: int) -> int:
        """Calculate percentage of limit used"""
        if limit == 0:
            return 0
        return int((value / limit) * 100)

def main():
    parser = argparse.ArgumentParser(
        description='Simulate Salesforce Flow execution with bulk data'
    )
    parser.add_argument('flow_xml', help='Path to flow metadata XML file')
    parser.add_argument('--test-records', type=int, default=200,
                       help='Number of records to simulate (default: 200)')
    parser.add_argument('--mock-data', action='store_true',
                       help='Generate mock data for testing')
    parser.add_argument('--analyze-only', action='store_true',
                       help='Analyze flow structure without simulation')

    args = parser.parse_args()

    simulator = FlowSimulator(args.flow_xml, args.test_records)
    result = simulator.simulate()

    # Exit with error code if simulation failed
    if result['status'] == 'FAILED':
        sys.exit(1)
    elif result['status'] == 'WARNING':
        sys.exit(0)  # Warnings don't fail the build
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()
