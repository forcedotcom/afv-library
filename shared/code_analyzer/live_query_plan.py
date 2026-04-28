#!/usr/bin/env python3
"""
Live Query Plan Analyzer - Real-time SOQL query plan analysis via Salesforce REST API.

Calls the Salesforce `explain` endpoint via `sf api request rest /query/?explain=...` to get actual query plan data:
- relativeCost (cost > 1 = non-selective)
- leadingOperationType (Index, TableScan, etc.)
- cardinality estimates
- notes[] with WHY optimizations aren't used

Usage:
    from code_analyzer.live_query_plan import LiveQueryPlanAnalyzer

    analyzer = LiveQueryPlanAnalyzer()
    if analyzer.is_org_available():
        result = analyzer.analyze("SELECT Id FROM Account WHERE Name = 'Acme'")
        if result.is_selective:
            print("Query is selective!")
        else:
            print(f"Non-selective (cost: {result.relative_cost})")
            for note in result.notes:
                print(f"  - {note.description}")
"""

import subprocess
import json
import re
import os
import urllib.parse
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field


@dataclass
class PlanNote:
    """A note from the query plan explaining optimization details."""
    description: str
    fields: List[str] = field(default_factory=list)
    table_enum_or_id: Optional[str] = None

    def __str__(self) -> str:
        return self.description


@dataclass
class QueryPlanResult:
    """Result from analyzing a SOQL query plan."""
    # Core selectivity
    is_selective: bool              # relativeCost <= 1.0
    relative_cost: float            # Actual cost from API (0.0 - 10+)

    # Operation details
    leading_operation: str          # "Index", "TableScan", "Sharing", etc.
    sobject_type: Optional[str]     # The SObject being queried

    # Cardinality
    cardinality: int                # Estimated rows returned
    sobject_cardinality: int        # Total records in object

    # Optimization notes
    notes: List[PlanNote] = field(default_factory=list)

    # Error handling
    success: bool = True
    error: Optional[str] = None

    # Raw data for debugging
    raw_plan: Optional[Dict[str, Any]] = None

    @property
    def selectivity_rating(self) -> str:
        """Human-readable selectivity rating."""
        if self.relative_cost <= 0.5:
            return "Excellent"
        elif self.relative_cost <= 1.0:
            return "Good (Selective)"
        elif self.relative_cost <= 2.0:
            return "Fair (Non-selective)"
        elif self.relative_cost <= 5.0:
            return "Poor"
        else:
            return "Critical"

    @property
    def icon(self) -> str:
        """Status icon based on selectivity."""
        if self.relative_cost <= 1.0:
            return "✅"
        elif self.relative_cost <= 2.0:
            return "⚠️"
        else:
            return "❌"


class LiveQueryPlanAnalyzer:
    """
    Analyzes SOQL queries using Salesforce's Query Plan API.

    Uses `sf api request rest /query/?explain=...` to call the REST API explain endpoint,
    which returns real query execution plans from the connected org.

    Usage:
        analyzer = LiveQueryPlanAnalyzer()

        # Check org connection
        if not analyzer.is_org_available():
            print("No org connected")
            return

        # Analyze a query
        result = analyzer.analyze("SELECT Id, Name FROM Account WHERE Industry = 'Tech'")

        if result.success:
            print(f"Cost: {result.relative_cost} ({result.selectivity_rating})")
            print(f"Operation: {result.leading_operation}")
            for note in result.notes:
                print(f"  Note: {note}")
        else:
            print(f"Error: {result.error}")
    """

    # Common bind variable patterns in Apex
    BIND_VAR_PATTERNS = [
        (r':(\w+)', "'001000000000000AAA'"),  # :accountId -> placeholder
        (r'\?', "'001000000000000AAA'"),       # ? -> placeholder (rare in SOQL)
    ]

    # Clauses to strip for query plan (not valid for explain)
    STRIP_CLAUSES = [
        r'\s+WITH\s+SECURITY_ENFORCED',
        r'\s+WITH\s+USER_MODE',
        r'\s+WITH\s+SYSTEM_MODE',
        r'\s+FOR\s+UPDATE',
        r'\s+FOR\s+VIEW',
        r'\s+FOR\s+REFERENCE',
    ]

    def __init__(self, target_org: Optional[str] = None, timeout_seconds: int = 15):
        """
        Initialize the analyzer.

        Args:
            target_org: Specific org alias/username. If None, uses default target-org.
            timeout_seconds: Timeout for sf CLI calls (default 15s)
        """
        self.target_org = target_org
        self.timeout_seconds = timeout_seconds
        self._cached_org_status: Optional[Tuple[bool, str]] = None

    def is_org_available(self) -> bool:
        """
        Check if a Salesforce org is connected and available.

        Returns:
            True if an org is connected and can be queried
        """
        available, _ = self._check_org()
        return available

    def get_target_org(self) -> Optional[str]:
        """
        Get the target org alias/username.

        Returns:
            Org alias or username, or None if not connected
        """
        _, org_name = self._check_org()
        return org_name if org_name else None

    def _check_org(self) -> Tuple[bool, Optional[str]]:
        """
        Check org availability and cache result.

        Returns:
            Tuple of (is_available, org_name)
        """
        if self._cached_org_status is not None:
            return self._cached_org_status

        try:
            if self.target_org:
                # Verify specified org exists
                result = subprocess.run(
                    ['sf', 'org', 'display', '--target-org', self.target_org, '--json'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    self._cached_org_status = (True, self.target_org)
                    return self._cached_org_status

            # Check default target-org
            result = subprocess.run(
                ['sf', 'config', 'get', 'target-org', '--json'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                results = data.get('result', [])
                if results:
                    org_value = results[0].get('value') if isinstance(results, list) else results.get('value')
                    if org_value:
                        self._cached_org_status = (True, org_value)
                        return self._cached_org_status

            self._cached_org_status = (False, None)
            return self._cached_org_status

        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            self._cached_org_status = (False, None)
            return self._cached_org_status

    def analyze(self, query: str) -> QueryPlanResult:
        """
        Analyze a SOQL query and return its execution plan.

        Args:
            query: The SOQL query to analyze (can include bind variables)

        Returns:
            QueryPlanResult with selectivity info, operation type, and notes
        """
        # Check org availability
        org_available, org_name = self._check_org()
        if not org_available:
            return QueryPlanResult(
                is_selective=False,
                relative_cost=0.0,
                leading_operation="Unknown",
                sobject_type=None,
                cardinality=0,
                sobject_cardinality=0,
                success=False,
                error="No Salesforce org connected. Run 'sf org login' first."
            )

        # Prepare query for API call
        prepared_query = self._prepare_query(query)

        if not prepared_query.strip():
            return QueryPlanResult(
                is_selective=False,
                relative_cost=0.0,
                leading_operation="Unknown",
                sobject_type=None,
                cardinality=0,
                sobject_cardinality=0,
                success=False,
                error="Empty query after preparation"
            )

        try:
            # Build command using the REST API explain endpoint
            encoded_query = urllib.parse.quote(prepared_query)
            cmd = [
                'sf', 'api', 'request', 'rest',
                f'/query/?explain={encoded_query}',
                '--json'
            ]

            # Add target org if specified
            if org_name:
                cmd.extend(['--target-org', org_name])

            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds
            )

            # Parse response
            if result.returncode != 0:
                # Try to extract error from JSON
                try:
                    error_data = json.loads(result.stdout)
                    error_msg = error_data.get('message', result.stderr or 'Unknown error')
                except json.JSONDecodeError:
                    error_msg = result.stderr.strip() or 'Query plan failed'

                return QueryPlanResult(
                    is_selective=False,
                    relative_cost=0.0,
                    leading_operation="Error",
                    sobject_type=self._extract_sobject(query),
                    cardinality=0,
                    sobject_cardinality=0,
                    success=False,
                    error=error_msg[:200]  # Truncate long errors
                )

            # Parse successful response
            return self._parse_plan_response(result.stdout, query)

        except subprocess.TimeoutExpired:
            return QueryPlanResult(
                is_selective=False,
                relative_cost=0.0,
                leading_operation="Timeout",
                sobject_type=self._extract_sobject(query),
                cardinality=0,
                sobject_cardinality=0,
                success=False,
                error=f"Query plan timed out after {self.timeout_seconds}s"
            )
        except FileNotFoundError:
            return QueryPlanResult(
                is_selective=False,
                relative_cost=0.0,
                leading_operation="Error",
                sobject_type=None,
                cardinality=0,
                sobject_cardinality=0,
                success=False,
                error="sf CLI not found - install Salesforce CLI"
            )
        except Exception as e:
            return QueryPlanResult(
                is_selective=False,
                relative_cost=0.0,
                leading_operation="Error",
                sobject_type=self._extract_sobject(query),
                cardinality=0,
                sobject_cardinality=0,
                success=False,
                error=f"Unexpected error: {str(e)[:100]}"
            )

    def _prepare_query(self, query: str) -> str:
        """
        Prepare a SOQL query for the explain API.

        - Replaces bind variables with placeholder IDs
        - Strips clauses not supported by explain endpoint
        - Normalizes whitespace

        Args:
            query: Original SOQL query (may include :bindVars)

        Returns:
            Cleaned query ready for API call
        """
        prepared = query

        # Replace bind variables with placeholder values
        for pattern, replacement in self.BIND_VAR_PATTERNS:
            prepared = re.sub(pattern, replacement, prepared)

        # Strip unsupported clauses
        for clause_pattern in self.STRIP_CLAUSES:
            prepared = re.sub(clause_pattern, '', prepared, flags=re.IGNORECASE)

        # Normalize whitespace
        prepared = ' '.join(prepared.split())

        return prepared.strip()

    def _parse_plan_response(self, stdout: str, original_query: str) -> QueryPlanResult:
        """
        Parse the sf api request rest /query/?explain=... JSON response.

        Args:
            stdout: JSON output from sf CLI
            original_query: Original query for context

        Returns:
            QueryPlanResult with parsed data
        """
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError as e:
            return QueryPlanResult(
                is_selective=False,
                relative_cost=0.0,
                leading_operation="ParseError",
                sobject_type=self._extract_sobject(original_query),
                cardinality=0,
                sobject_cardinality=0,
                success=False,
                error=f"Failed to parse response: {e}"
            )

        # The plan is in data.result.plans[] (sf CLI wraps the API response)
        result_data = data.get('result', data)
        plans = result_data.get('plans', [])

        if not plans:
            # No plans returned - might be an empty result
            return QueryPlanResult(
                is_selective=True,  # Assume empty = selective
                relative_cost=0.0,
                leading_operation="NoPlan",
                sobject_type=self._extract_sobject(original_query),
                cardinality=0,
                sobject_cardinality=0,
                success=True,
                raw_plan=result_data
            )

        # Use the first plan (primary execution plan)
        plan = plans[0]

        # Extract core metrics
        relative_cost = float(plan.get('relativeCost', 0.0))
        leading_op = plan.get('leadingOperationType', 'Unknown')
        cardinality = int(plan.get('cardinality', 0))
        sobject_cardinality = int(plan.get('sobjectCardinality', 0))
        sobject_type = plan.get('sobjectType', self._extract_sobject(original_query))

        # Parse notes
        notes = []
        for note_data in plan.get('notes', []):
            note = PlanNote(
                description=note_data.get('description', ''),
                fields=note_data.get('fields', []),
                table_enum_or_id=note_data.get('tableEnumOrId')
            )
            notes.append(note)

        # Determine selectivity (cost <= 1.0 is considered selective)
        is_selective = relative_cost <= 1.0

        return QueryPlanResult(
            is_selective=is_selective,
            relative_cost=relative_cost,
            leading_operation=leading_op,
            sobject_type=sobject_type,
            cardinality=cardinality,
            sobject_cardinality=sobject_cardinality,
            notes=notes,
            success=True,
            raw_plan=plan
        )

    def _extract_sobject(self, query: str) -> Optional[str]:
        """
        Extract the primary SObject name from a SOQL query.

        Args:
            query: SOQL query string

        Returns:
            SObject name or None
        """
        # Match: FROM ObjectName (with optional alias)
        match = re.search(r'\bFROM\s+(\w+)', query, re.IGNORECASE)
        return match.group(1) if match else None

    def analyze_multiple(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze multiple queries with context.

        Args:
            queries: List of dicts with 'query', 'line', 'context' keys

        Returns:
            List of dicts with original data plus 'plan' key containing QueryPlanResult
        """
        results = []

        for query_info in queries:
            query = query_info.get('query', '')
            result = self.analyze(query)

            results.append({
                **query_info,
                'plan': result
            })

        return results

    def get_optimization_suggestions(self, result: QueryPlanResult) -> List[str]:
        """
        Generate optimization suggestions based on query plan result.

        Args:
            result: QueryPlanResult from analyze()

        Returns:
            List of actionable suggestions
        """
        suggestions = []

        if not result.success:
            suggestions.append(f"Could not analyze query: {result.error}")
            return suggestions

        # Non-selective query
        if not result.is_selective:
            if result.leading_operation == "TableScan":
                suggestions.append(
                    "Query performs a full table scan. Add an indexed field to WHERE clause "
                    "(Id, Name, OwnerId, CreatedDate, or a custom indexed field)."
                )
            else:
                suggestions.append(
                    f"Query has relativeCost of {result.relative_cost:.1f} (>1.0 is non-selective). "
                    "Consider adding more selective filter criteria."
                )

        # Provide suggestions based on notes
        for note in result.notes:
            desc = note.description.lower()

            if "not indexed" in desc:
                field = note.fields[0] if note.fields else "the field"
                suggestions.append(
                    f"Field '{field}' is not indexed. Consider requesting a custom index "
                    "via Salesforce Support (requires Business/Enterprise+ edition)."
                )

            if "not selective" in desc:
                suggestions.append(
                    "WHERE clause filters are not selective enough. Add more restrictive conditions "
                    "or use indexed fields in equality comparisons."
                )

            if "negative filter" in desc:
                suggestions.append(
                    "Negative operators (!=, NOT IN, NOT LIKE) prevent index usage. "
                    "Consider restructuring to use positive conditions."
                )

        # High cardinality suggestions
        if result.sobject_cardinality > 100000 and result.cardinality > 10000:
            pct = (result.cardinality / result.sobject_cardinality) * 100
            if pct > 10:
                suggestions.append(
                    f"Query may return {result.cardinality:,} of {result.sobject_cardinality:,} records "
                    f"({pct:.1f}%). Consider adding LIMIT or more filters."
                )

        return suggestions


# Standalone execution for testing
if __name__ == '__main__':
    import sys

    analyzer = LiveQueryPlanAnalyzer()

    print("Live Query Plan Analyzer")
    print("=" * 50)

    if not analyzer.is_org_available():
        print("❌ No Salesforce org connected")
        print("   Run: sf org login web")
        sys.exit(1)

    print(f"✅ Connected to: {analyzer.get_target_org()}")
    print()

    # Test query
    test_query = sys.argv[1] if len(sys.argv) > 1 else "SELECT Id, Name FROM Account LIMIT 10"

    print(f"Query: {test_query[:80]}...")
    print("-" * 50)

    result = analyzer.analyze(test_query)

    if result.success:
        print(f"{result.icon} Selective: {result.is_selective}")
        print(f"📊 Relative Cost: {result.relative_cost:.2f} ({result.selectivity_rating})")
        print(f"📈 Operation: {result.leading_operation}")
        print(f"📋 Cardinality: {result.cardinality:,} / {result.sobject_cardinality:,}")

        if result.notes:
            print("\n📝 Notes:")
            for note in result.notes:
                print(f"   - {note}")

        suggestions = analyzer.get_optimization_suggestions(result)
        if suggestions:
            print("\n💡 Suggestions:")
            for s in suggestions:
                print(f"   - {s}")
    else:
        print(f"❌ Error: {result.error}")
