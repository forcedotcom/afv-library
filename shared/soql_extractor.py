#!/usr/bin/env python3
"""
SOQL Extractor - Extract SOQL queries from Salesforce source files.

Supports extraction from:
- Apex classes (.cls, .trigger) - Inline [SELECT...] and Database.query()
- SOQL files (.soql) - Entire file is a query
- Anonymous Apex - Same as .cls

Provides context for each query:
- Line number
- Whether it's inside a loop
- Method/function name
- Query type (inline, dynamic, file)

Usage:
    from soql_extractor import SOQLExtractor

    # From file content
    extractor = SOQLExtractor(apex_code, "apex")
    queries = extractor.extract()

    for q in queries:
        print(f"Line {q['line']}: {q['query'][:50]}...")
        if q['in_loop']:
            print("  ⚠️ Warning: Query in loop!")
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class FileType(Enum):
    """File types for extraction."""
    APEX = "apex"
    SOQL = "soql"
    ANONYMOUS = "anonymous"


@dataclass
class ExtractedQuery:
    """A SOQL query extracted from source code."""
    query: str                          # The SOQL query
    line: int                           # Line number in source
    column: int = 0                     # Column number
    end_line: int = 0                   # End line for multi-line queries
    in_loop: bool = False               # True if query is inside a loop
    context: str = ""                   # Surrounding context (method name, etc.)
    query_type: str = "inline"          # "inline", "dynamic", "file"
    raw_match: str = ""                 # Original matched text

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'query': self.query,
            'line': self.line,
            'column': self.column,
            'end_line': self.end_line,
            'in_loop': self.in_loop,
            'context': self.context,
            'query_type': self.query_type,
        }


class SOQLExtractor:
    """
    Extract SOQL queries from various Salesforce source file types.

    Handles:
    - Inline SOQL: [SELECT ... FROM ...]
    - Dynamic SOQL: Database.query('SELECT ...')
    - SOQL files: Entire file is a query
    - Loop detection: Tracks if query is inside for/while/do

    Usage:
        extractor = SOQLExtractor(file_content, "apex")
        queries = extractor.extract()

        for q in queries:
            if q.in_loop:
                print(f"⚠️ SOQL in loop at line {q.line}")
    """

    # Patterns for SOQL extraction
    INLINE_SOQL_PATTERN = re.compile(
        r'\[\s*(SELECT\b[^\]]+)\]',
        re.IGNORECASE | re.DOTALL
    )

    # Database.query() and Database.queryWithBinds()
    DYNAMIC_SOQL_PATTERNS = [
        # Database.query('...')
        re.compile(
            r'Database\s*\.\s*query\s*\(\s*[\'"]([^"\']+)[\'"]',
            re.IGNORECASE
        ),
        # Database.query(stringVar) - capture variable name
        re.compile(
            r'Database\s*\.\s*query\s*\(\s*(\w+)\s*\)',
            re.IGNORECASE
        ),
        # Database.queryWithBinds
        re.compile(
            r'Database\s*\.\s*queryWithBinds\s*\(\s*[\'"]([^"\']+)[\'"]',
            re.IGNORECASE
        ),
    ]

    # Loop patterns to detect SOQL in loops
    LOOP_PATTERNS = [
        re.compile(r'\bfor\s*\(', re.IGNORECASE),
        re.compile(r'\bwhile\s*\(', re.IGNORECASE),
        re.compile(r'\bdo\s*\{', re.IGNORECASE),
    ]

    # Method/function pattern for context
    METHOD_PATTERN = re.compile(
        r'(?:public|private|protected|global|static|\s)+\s+'
        r'(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\([^)]*\)\s*\{',
        re.IGNORECASE
    )

    def __init__(self, content: str, file_type: str = "apex"):
        """
        Initialize the extractor.

        Args:
            content: Source file content
            file_type: One of "apex", "soql", "anonymous"
        """
        self.content = content
        self.file_type = FileType(file_type.lower())
        self.lines = content.split('\n')

    def extract(self) -> List[ExtractedQuery]:
        """
        Extract all SOQL queries from the content.

        Returns:
            List of ExtractedQuery objects
        """
        if self.file_type == FileType.SOQL:
            return self._extract_soql_file()
        else:
            return self._extract_apex()

    def _extract_soql_file(self) -> List[ExtractedQuery]:
        """Extract query from a .soql file (entire file is the query)."""
        # Clean the query - remove comments
        query = self._remove_comments(self.content)
        query = query.strip()

        if not query:
            return []

        # Find the first non-comment line for line number
        first_line = 1
        for i, line in enumerate(self.lines):
            stripped = line.strip()
            if stripped and not stripped.startswith('--') and not stripped.startswith('//'):
                first_line = i + 1
                break

        return [ExtractedQuery(
            query=query,
            line=first_line,
            end_line=len(self.lines),
            query_type="file",
            context="soql_file",
        )]

    def _extract_apex(self) -> List[ExtractedQuery]:
        """Extract SOQL queries from Apex code."""
        queries = []

        # Remove string literals that aren't SOQL to avoid false positives
        cleaned_content = self._mask_non_soql_strings(self.content)

        # Build loop regions map
        loop_regions = self._find_loop_regions(cleaned_content)

        # Build method context map
        method_contexts = self._find_method_contexts(self.content)

        # Extract inline SOQL
        for match in self.INLINE_SOQL_PATTERN.finditer(self.content):
            query = match.group(1).strip()
            query = self._normalize_query(query)

            pos = match.start()
            line = self._position_to_line(pos)
            end_line = self._position_to_line(match.end())

            in_loop = self._is_in_loop(pos, loop_regions)
            context = self._get_context(pos, method_contexts)

            queries.append(ExtractedQuery(
                query=query,
                line=line,
                end_line=end_line,
                in_loop=in_loop,
                context=context,
                query_type="inline",
                raw_match=match.group(0),
            ))

        # Extract dynamic SOQL
        for pattern in self.DYNAMIC_SOQL_PATTERNS:
            for match in pattern.finditer(self.content):
                captured = match.group(1)

                # If it's a variable name (not a query), note it but skip analysis
                if not captured.upper().startswith('SELECT'):
                    # It's a variable - we can't analyze dynamic queries
                    # Still record it for reporting
                    pos = match.start()
                    line = self._position_to_line(pos)
                    in_loop = self._is_in_loop(pos, loop_regions)

                    queries.append(ExtractedQuery(
                        query=f"[Dynamic: {captured}]",
                        line=line,
                        in_loop=in_loop,
                        context=self._get_context(pos, method_contexts),
                        query_type="dynamic_variable",
                    ))
                else:
                    query = self._normalize_query(captured)
                    pos = match.start()
                    line = self._position_to_line(pos)

                    queries.append(ExtractedQuery(
                        query=query,
                        line=line,
                        in_loop=self._is_in_loop(pos, loop_regions),
                        context=self._get_context(pos, method_contexts),
                        query_type="dynamic",
                    ))

        # Sort by line number
        queries.sort(key=lambda q: q.line)

        return queries

    def _remove_comments(self, text: str) -> str:
        """Remove SQL/Apex style comments."""
        # Remove single-line comments
        text = re.sub(r'--.*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'//.*$', '', text, flags=re.MULTILINE)
        # Remove multi-line comments
        text = re.sub(r'/\*[\s\S]*?\*/', '', text)
        return text

    def _mask_non_soql_strings(self, content: str) -> str:
        """
        Mask string literals that aren't SOQL queries.

        This prevents false positives from strings like 'SELECT' in error messages.
        """
        def replacer(match):
            string_content = match.group(1)
            # Keep SOQL strings, mask others
            if 'SELECT' in string_content.upper() and 'FROM' in string_content.upper():
                return match.group(0)
            return "'MASKED'"

        # Mask single-quoted strings
        result = re.sub(r"'([^']*)'", replacer, content)
        return result

    def _find_loop_regions(self, content: str) -> List[tuple]:
        """
        Find all loop regions in the code.

        Returns:
            List of (start_pos, end_pos) tuples for each loop
        """
        regions = []

        for pattern in self.LOOP_PATTERNS:
            for match in pattern.finditer(content):
                loop_start = match.start()
                # Find the matching closing brace
                loop_end = self._find_matching_brace(content, match.end())
                if loop_end > loop_start:
                    regions.append((loop_start, loop_end))

        return regions

    def _find_matching_brace(self, content: str, start: int) -> int:
        """Find the position of the matching closing brace."""
        depth = 0
        in_string = False
        string_char = None

        for i in range(start, len(content)):
            c = content[i]

            # Handle string literals
            if c in ('"', "'") and (i == 0 or content[i-1] != '\\'):
                if not in_string:
                    in_string = True
                    string_char = c
                elif c == string_char:
                    in_string = False
                continue

            if in_string:
                continue

            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return i

        return len(content)

    def _find_method_contexts(self, content: str) -> List[tuple]:
        """
        Find method boundaries for context.

        Returns:
            List of (start_pos, end_pos, method_name) tuples
        """
        contexts = []

        for match in self.METHOD_PATTERN.finditer(content):
            method_name = match.group(1)
            method_start = match.start()
            method_end = self._find_matching_brace(content, match.end())
            contexts.append((method_start, method_end, method_name))

        return contexts

    def _position_to_line(self, pos: int) -> int:
        """Convert character position to line number (1-based)."""
        return self.content[:pos].count('\n') + 1

    def _is_in_loop(self, pos: int, loop_regions: List[tuple]) -> bool:
        """Check if position is inside a loop."""
        for start, end in loop_regions:
            if start <= pos <= end:
                return True
        return False

    def _get_context(self, pos: int, method_contexts: List[tuple]) -> str:
        """Get the method context for a position."""
        for start, end, name in method_contexts:
            if start <= pos <= end:
                return name
        return "global"

    def _normalize_query(self, query: str) -> str:
        """Normalize a SOQL query for analysis."""
        # Remove excessive whitespace
        query = ' '.join(query.split())
        return query.strip()

    def get_queries_with_issues(self) -> List[Dict[str, Any]]:
        """
        Get queries that have potential issues.

        Returns:
            List of query dicts with 'issues' key containing issue descriptions
        """
        queries = self.extract()
        results = []

        for q in queries:
            issues = []

            if q.in_loop:
                issues.append({
                    'type': 'soql_in_loop',
                    'severity': 'HIGH',
                    'message': 'SOQL query inside loop - may cause governor limit issues'
                })

            if q.query_type == 'dynamic_variable':
                issues.append({
                    'type': 'dynamic_soql',
                    'severity': 'INFO',
                    'message': 'Dynamic SOQL with variable - cannot analyze query plan'
                })

            result = q.to_dict()
            result['issues'] = issues
            results.append(result)

        return results


def extract_soql_from_file(file_path: str) -> List[ExtractedQuery]:
    """
    Convenience function to extract SOQL from a file.

    Args:
        file_path: Path to the file

    Returns:
        List of ExtractedQuery objects
    """
    import os

    if not os.path.exists(file_path):
        return []

    with open(file_path, 'r') as f:
        content = f.read()

    # Determine file type
    file_lower = file_path.lower()
    if file_lower.endswith('.soql'):
        file_type = 'soql'
    elif file_lower.endswith(('.cls', '.trigger')):
        file_type = 'apex'
    else:
        file_type = 'apex'  # Default to apex

    extractor = SOQLExtractor(content, file_type)
    return extractor.extract()


# Standalone execution for testing
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python soql_extractor.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    queries = extract_soql_from_file(file_path)

    print(f"SOQL Extraction: {file_path}")
    print("=" * 50)
    print(f"Found {len(queries)} queries\n")

    for i, q in enumerate(queries, 1):
        print(f"Query #{i} (Line {q.line})")
        print(f"  Type: {q.query_type}")
        print(f"  Context: {q.context}")
        print(f"  In Loop: {'⚠️ YES' if q.in_loop else 'No'}")
        print(f"  Query: {q.query[:80]}{'...' if len(q.query) > 80 else ''}")
        print()
