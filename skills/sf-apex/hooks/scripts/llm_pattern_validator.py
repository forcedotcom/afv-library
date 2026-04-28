#!/usr/bin/env python3
"""
LLM Pattern Validator for Apex Code.

Detects common mistakes that LLMs make when generating Salesforce Apex code:
1. Java types (ArrayList, HashMap, StringBuilder, etc.)
2. Hallucinated methods (addMilliseconds, stream(), etc.)
3. Unsafe Map access (Map.get() without null checks)
4. Missing SOQL fields (accessing fields not in query)

This validator is ADVISORY - it provides warnings but does not block operations.

Source: https://salesforcediaries.com/2026/01/16/llm-mistakes-in-apex-lwc-salesforce-code-generation-rules/
"""

import re
import os
from typing import Dict, List, Tuple, Set


class LLMPatternValidator:
    """Detects LLM-specific anti-patterns in Apex code."""

    # Java types that don't exist in Apex
    JAVA_TYPES = {
        'ArrayList': 'List',
        'HashMap': 'Map',
        'HashSet': 'Set',
        'StringBuffer': 'String or List<String> + String.join()',
        'StringBuilder': 'String or List<String> + String.join()',
        'LinkedList': 'List',
        'TreeMap': 'Map',
        'Vector': 'List',
        'Hashtable': 'Map',
        'LinkedHashMap': 'Map',
        'TreeSet': 'Set',
        'LinkedHashSet': 'Set',
        'ArrayDeque': 'List',
        'Stack': 'List',
        'Queue': 'List',
        'PriorityQueue': 'List',
    }

    # Methods that don't exist in Apex but LLMs commonly generate
    HALLUCINATED_METHODS = [
        # DateTime methods
        (r'\.addMilliseconds\s*\(', 'Datetime.addMilliseconds() does not exist. Use addSeconds() instead.'),
        (r'\.addMicroseconds\s*\(', 'Datetime.addMicroseconds() does not exist. Apex has no sub-second precision.'),
        (r'DateTime\.today\s*\(\)', 'DateTime.today() does not exist. Use Date.today() or DateTime.now().'),
        (r'Datetime\.today\s*\(\)', 'Datetime.today() does not exist. Use Date.today() or Datetime.now().'),

        # Java stream operations
        (r'\.stream\s*\(\)', 'stream() does not exist in Apex. Use for loops instead.'),
        (r'\.collect\s*\(', 'collect() does not exist in Apex. Use for loops to build collections.'),
        (r'\.filter\s*\(\s*\w+\s*->', 'Lambda filter() does not exist in Apex. Use for loops with if statements.'),
        (r'\.map\s*\(\s*\w+\s*->', 'Lambda map() does not exist in Apex. Use for loops.'),
        (r'\.forEach\s*\(\s*\w+\s*->', 'Lambda forEach() does not exist in Apex. Use for loops.'),
        (r'\.reduce\s*\(', 'reduce() does not exist in Apex. Use a loop with an accumulator.'),
        (r'\.flatMap\s*\(', 'flatMap() does not exist in Apex. Use nested for loops.'),

        # Map methods from Java
        (r'\.getOrDefault\s*\(', 'Map.getOrDefault() does not exist. Use: map.get(key) ?? defaultValue'),
        (r'\.putIfAbsent\s*\(', 'Map.putIfAbsent() does not exist. Use: if (!map.containsKey(key)) map.put(key, value)'),
        (r'\.computeIfAbsent\s*\(', 'Map.computeIfAbsent() does not exist. Use containsKey() check instead.'),
        (r'\.computeIfPresent\s*\(', 'Map.computeIfPresent() does not exist. Use containsKey() check instead.'),
        (r'\.merge\s*\(', 'Map.merge() does not exist in Apex.'),
        (r'\.entrySet\s*\(\)', 'Map.entrySet() does not exist. Use map.keySet() and map.get() instead.'),

        # String methods from Java
        (r'String\.format\s*\([^)]*%[sdf]', 'String.format() in Apex uses different syntax. Use String.format(template, args).'),
        (r'\.charAt\s*\(\d+\)', 'String.charAt() does not exist. Use substring(index, index+1) or split(\'\')[index].'),
        (r'\.toCharArray\s*\(\)', 'String.toCharArray() does not exist. Use split(\'\') to get List<String>.'),
        (r'\.getBytes\s*\(\)', 'String.getBytes() does not exist. Use Blob.valueOf(str) instead.'),
        (r'\.matches\s*\(', 'String.matches() does not exist. Use Pattern.matches(regex, input).'),

        # List/Collection methods from Java
        (r'\.addAll\s*\(\s*\d+\s*,', 'List.addAll(index, collection) does not exist. Only addAll(collection) is supported.'),
        (r'\.subList\s*\(', 'List.subList() does not exist. Use a loop or clone and remove.'),
        (r'\.toArray\s*\([^)]*\)', 'List.toArray(T[]) does not exist. Collections are already typed in Apex.'),

        # Other common hallucinations
        (r'Objects\.equals\s*\(', 'Objects.equals() does not exist. Use == or custom comparison.'),
        (r'Objects\.hash\s*\(', 'Objects.hash() does not exist. Use String.valueOf() for simple hashing.'),
        (r'Optional\s*<', 'Optional<T> does not exist in Apex. Use null checks instead.'),
        (r'\.orElse\s*\(', 'orElse() does not exist in Apex. Use null coalescing: value ?? default.'),
        (r'\.ifPresent\s*\(', 'ifPresent() does not exist in Apex. Use null checks.'),
    ]

    # Patterns for unsafe Map access
    MAP_ACCESS_PATTERNS = [
        # Direct method call on Map.get() result without null check
        r'(\w+)\.get\s*\([^)]+\)\s*\.\s*\w+\s*\(',  # map.get(key).method()
        r'(\w+)\.get\s*\([^)]+\)\s*\.\s*\w+\s*[^?]',  # map.get(key).property (not safe nav)
    ]

    def __init__(self, file_path: str):
        """
        Initialize the validator with an Apex file.

        Args:
            file_path: Path to .cls or .trigger file
        """
        self.file_path = file_path
        self.content = ""
        self.lines = []
        self.issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
                self.lines = self.content.split('\n')
        except Exception as e:
            self.issues.append({
                'severity': 'ERROR',
                'category': 'file',
                'message': f'Cannot read file: {e}',
                'line': 0
            })

    def validate(self) -> Dict:
        """
        Run all LLM pattern validations.

        Returns:
            Dictionary with validation results
        """
        if not self.content:
            return {
                'file': os.path.basename(self.file_path),
                'issues': self.issues,
                'issue_count': len(self.issues)
            }

        # Run all checks
        self._check_java_types()
        self._check_hallucinated_methods()
        self._check_unsafe_map_access()
        self._check_soql_field_coverage()

        return {
            'file': os.path.basename(self.file_path),
            'issues': self.issues,
            'issue_count': len(self.issues)
        }

    def _check_java_types(self):
        """Check for Java collection types that don't exist in Apex."""
        for java_type, apex_alternative in self.JAVA_TYPES.items():
            # Pattern: JavaType<...> or new JavaType<...>
            pattern = rf'\b{java_type}\s*<'

            for i, line in enumerate(self.lines, 1):
                # Skip comments
                stripped = line.strip()
                if stripped.startswith('//') or stripped.startswith('*'):
                    continue

                if re.search(pattern, line):
                    self.issues.append({
                        'severity': 'CRITICAL',
                        'category': 'java_type',
                        'message': f'Java type "{java_type}" does not exist in Apex',
                        'line': i,
                        'fix': f'Use {apex_alternative} instead',
                        'source': 'llm-pattern-validator'
                    })

    def _check_hallucinated_methods(self):
        """Check for methods that LLMs commonly hallucinate."""
        for pattern, message in self.HALLUCINATED_METHODS:
            for i, line in enumerate(self.lines, 1):
                # Skip comments
                stripped = line.strip()
                if stripped.startswith('//') or stripped.startswith('*'):
                    continue

                if re.search(pattern, line, re.IGNORECASE):
                    self.issues.append({
                        'severity': 'CRITICAL',
                        'category': 'hallucinated_method',
                        'message': message,
                        'line': i,
                        'source': 'llm-pattern-validator'
                    })

    def _check_unsafe_map_access(self):
        """Check for Map.get() without null safety."""
        # More sophisticated check: look for Map.get() followed by . without ?
        # Skip if there's a containsKey check nearby or safe navigation

        map_get_pattern = r'(\w+)\.get\s*\(([^)]+)\)\s*\.(?!\s*\?)'

        for i, line in enumerate(self.lines, 1):
            # Skip comments
            stripped = line.strip()
            if stripped.startswith('//') or stripped.startswith('*'):
                continue

            # Skip lines with safe navigation operator
            if '?.' in line:
                continue

            matches = re.finditer(map_get_pattern, line)
            for match in matches:
                map_var = match.group(1)
                key_expr = match.group(2)

                # Check if there's a containsKey check in the surrounding context
                # Look at the previous 5 lines for a containsKey check
                context_start = max(0, i - 6)
                context = '\n'.join(self.lines[context_start:i])

                # Also check if there's an if (map_var != null) check
                has_null_check = (
                    f'containsKey({key_expr})' in context or
                    f'{map_var}.containsKey' in context or
                    f'{map_var} != null' in context or
                    f'{map_var} == null' in context or
                    'if (' in self.lines[i-1] if i > 0 else False
                )

                if not has_null_check:
                    self.issues.append({
                        'severity': 'WARNING',
                        'category': 'unsafe_map_access',
                        'message': f'Potential NPE: {map_var}.get() used without null check',
                        'line': i,
                        'fix': f'Use {map_var}.get({key_expr})?.property or check containsKey() first',
                        'source': 'llm-pattern-validator'
                    })

    def _check_soql_field_coverage(self):
        """
        Check for potential SOQL field coverage issues.

        This is a simplified check that looks for common patterns where
        fields might be accessed but not queried.
        """
        # Find SOQL queries and extract field lists
        soql_pattern = r'\[\s*SELECT\s+([^F][^\]]+?)\s+FROM\s+(\w+)'

        soql_queries = []
        for i, line in enumerate(self.lines, 1):
            matches = re.finditer(soql_pattern, line, re.IGNORECASE)
            for match in matches:
                fields_str = match.group(1)
                sobject = match.group(2)

                # Parse field names (simplified)
                fields = set()
                for field in fields_str.split(','):
                    field = field.strip()
                    # Handle relationship fields like Account.Name
                    if '(' not in field:  # Skip subqueries
                        fields.add(field.lower())

                soql_queries.append({
                    'line': i,
                    'sobject': sobject,
                    'fields': fields
                })

        # This is a very simplified check - just warn if a query has very few fields
        # and later code accesses many properties
        for query in soql_queries:
            if len(query['fields']) <= 2 and 'id' in query['fields']:
                # Very minimal query - might be missing fields
                # Check following lines for field access patterns
                query_line = query['line']
                following_lines = '\n'.join(self.lines[query_line:min(query_line + 20, len(self.lines))])

                # Count distinct field accesses that look like sobject.Field
                field_access_pattern = rf"\.([A-Z][a-zA-Z0-9_]+)(?:\s*[;,\)\]\}}=]|\s*!=|\s*==)"
                accessed_fields = set(re.findall(field_access_pattern, following_lines))

                # If accessing many more fields than queried, warn
                if len(accessed_fields) > len(query['fields']) + 2:
                    self.issues.append({
                        'severity': 'INFO',
                        'category': 'soql_field_coverage',
                        'message': f"SOQL on line {query_line} queries {len(query['fields'])} fields but code may access more",
                        'line': query_line,
                        'fix': 'Verify all accessed fields are in the SELECT clause',
                        'source': 'llm-pattern-validator'
                    })


def validate_apex_llm_patterns(file_path: str) -> Dict:
    """
    Validate an Apex file for LLM-specific anti-patterns.

    Args:
        file_path: Path to .cls or .trigger file

    Returns:
        Dictionary with validation results
    """
    validator = LLMPatternValidator(file_path)
    return validator.validate()


def format_output(results: Dict) -> str:
    """Format validation results for display."""
    issues = results.get('issues', [])

    if not issues:
        return ""

    output_parts = []
    output_parts.append("")
    output_parts.append(f"🤖 LLM Pattern Check: {results['file']}")
    output_parts.append("─" * 50)

    # Group by severity
    critical = [i for i in issues if i['severity'] == 'CRITICAL']
    warnings = [i for i in issues if i['severity'] == 'WARNING']
    info = [i for i in issues if i['severity'] == 'INFO']

    if critical:
        output_parts.append(f"🔴 Critical ({len(critical)}):")
        for issue in critical[:5]:
            output_parts.append(f"   L{issue['line']}: {issue['message']}")
            if issue.get('fix'):
                output_parts.append(f"      💡 {issue['fix']}")

    if warnings:
        output_parts.append(f"🟡 Warnings ({len(warnings)}):")
        for issue in warnings[:3]:
            output_parts.append(f"   L{issue['line']}: {issue['message']}")
            if issue.get('fix'):
                output_parts.append(f"      💡 {issue['fix']}")

    if info and not critical and not warnings:
        output_parts.append(f"ℹ️ Info ({len(info)}):")
        for issue in info[:2]:
            output_parts.append(f"   L{issue['line']}: {issue['message']}")

    remaining = len(issues) - len(critical[:5]) - len(warnings[:3]) - (len(info[:2]) if not critical and not warnings else 0)
    if remaining > 0:
        output_parts.append(f"   ... and {remaining} more issues")

    output_parts.append("─" * 50)
    output_parts.append("📚 See: sf-apex/references/llm-anti-patterns.md")

    return "\n".join(output_parts)


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python llm_pattern_validator.py <file.cls|file.trigger>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    results = validate_apex_llm_patterns(file_path)

    # Print formatted output
    output = format_output(results)
    if output:
        print(output)
    else:
        print(f"✅ No LLM anti-patterns detected in {results['file']}")

    # Return non-zero if critical issues
    critical_count = sum(1 for i in results['issues'] if i['severity'] == 'CRITICAL')
    sys.exit(0)  # Advisory only - don't block
