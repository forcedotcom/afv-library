#!/usr/bin/env python3
"""
Code Analyzer Output Parser - JSON result normalization and filtering.

Provides utilities for:
- Parsing raw Code Analyzer JSON output
- Normalizing violations into a consistent format
- Filtering violations by severity, engine, or tags
- Grouping violations by file, rule, or category

Usage:
    # Parse raw output
    violations = parse_ca_output(raw_json)

    # Filter by severity
    critical = filter_by_severity(violations, max_severity=2)

    # Group by file
    by_file = group_by_file(violations)
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from collections import defaultdict


# Severity labels mapping
SEVERITY_LABELS = {
    1: "CRITICAL",
    2: "HIGH",
    3: "MODERATE",
    4: "LOW",
    5: "INFO",
}

# Reverse mapping
SEVERITY_VALUES = {v: k for k, v in SEVERITY_LABELS.items()}


@dataclass
class NormalizedViolation:
    """Normalized violation with consistent fields."""
    rule: str
    engine: str
    severity: int
    severity_label: str
    message: str
    file: str
    line: int
    end_line: int
    column: int
    end_column: int
    tags: List[str]
    resources: List[str]
    raw: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule": self.rule,
            "engine": self.engine,
            "severity": self.severity,
            "severity_label": self.severity_label,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "end_line": self.end_line,
            "column": self.column,
            "end_column": self.end_column,
            "tags": self.tags,
            "resources": self.resources,
        }


def normalize_violation(raw_violation: Dict[str, Any]) -> NormalizedViolation:
    """
    Normalize a single violation from CA output.

    Args:
        raw_violation: Raw violation dict from CA JSON output

    Returns:
        NormalizedViolation with consistent fields
    """
    # Get primary location
    locations = raw_violation.get("locations", [])
    primary_idx = raw_violation.get("primaryLocationIndex", 0)

    if locations and primary_idx < len(locations):
        primary_loc = locations[primary_idx]
    else:
        primary_loc = {}

    # Get severity
    severity = raw_violation.get("severity", 5)
    severity_label = SEVERITY_LABELS.get(severity, "UNKNOWN")

    return NormalizedViolation(
        rule=raw_violation.get("rule", ""),
        engine=raw_violation.get("engine", "unknown"),
        severity=severity,
        severity_label=severity_label,
        message=raw_violation.get("message", ""),
        file=primary_loc.get("file", ""),
        line=primary_loc.get("startLine", 0),
        end_line=primary_loc.get("endLine", 0),
        column=primary_loc.get("startColumn", 0),
        end_column=primary_loc.get("endColumn", 0),
        tags=raw_violation.get("tags", []),
        resources=raw_violation.get("resources", []),
        raw=raw_violation,
    )


def parse_ca_output(raw_output: Dict[str, Any]) -> List[NormalizedViolation]:
    """
    Parse Code Analyzer JSON output into normalized violations.

    Args:
        raw_output: Full JSON output from Code Analyzer

    Returns:
        List of NormalizedViolation objects
    """
    violations = []

    for raw_violation in raw_output.get("violations", []):
        # Skip engine instantiation errors
        if raw_violation.get("rule") == "UninstantiableEngineError":
            continue

        violations.append(normalize_violation(raw_violation))

    return violations


def filter_by_severity(
    violations: List[NormalizedViolation],
    min_severity: int = 1,
    max_severity: int = 5,
) -> List[NormalizedViolation]:
    """
    Filter violations by severity range.

    Args:
        violations: List of violations
        min_severity: Minimum severity (1=Critical, 5=Info)
        max_severity: Maximum severity

    Returns:
        Filtered list of violations
    """
    return [
        v for v in violations
        if min_severity <= v.severity <= max_severity
    ]


def filter_by_engine(
    violations: List[NormalizedViolation],
    engines: List[str],
) -> List[NormalizedViolation]:
    """
    Filter violations by engine name.

    Args:
        violations: List of violations
        engines: List of engine names to include

    Returns:
        Filtered list of violations
    """
    engine_set = set(e.lower() for e in engines)
    return [v for v in violations if v.engine.lower() in engine_set]


def filter_by_tags(
    violations: List[NormalizedViolation],
    tags: List[str],
    match_all: bool = False,
) -> List[NormalizedViolation]:
    """
    Filter violations by tags.

    Args:
        violations: List of violations
        tags: List of tags to match
        match_all: If True, violation must have all tags. If False, any tag.

    Returns:
        Filtered list of violations
    """
    tag_set = set(t.lower() for t in tags)

    def matches(v: NormalizedViolation) -> bool:
        v_tags = set(t.lower() for t in v.tags)
        if match_all:
            return tag_set.issubset(v_tags)
        else:
            return bool(tag_set & v_tags)

    return [v for v in violations if matches(v)]


def filter_by_rule(
    violations: List[NormalizedViolation],
    rules: List[str],
    exclude: bool = False,
) -> List[NormalizedViolation]:
    """
    Filter violations by rule name.

    Args:
        violations: List of violations
        rules: List of rule names
        exclude: If True, exclude these rules. If False, include only these.

    Returns:
        Filtered list of violations
    """
    rule_set = set(r.lower() for r in rules)

    if exclude:
        return [v for v in violations if v.rule.lower() not in rule_set]
    else:
        return [v for v in violations if v.rule.lower() in rule_set]


def filter_custom(
    violations: List[NormalizedViolation],
    predicate: Callable[[NormalizedViolation], bool],
) -> List[NormalizedViolation]:
    """
    Filter violations with custom predicate.

    Args:
        violations: List of violations
        predicate: Function that returns True for violations to keep

    Returns:
        Filtered list of violations
    """
    return [v for v in violations if predicate(v)]


def group_by_file(
    violations: List[NormalizedViolation],
) -> Dict[str, List[NormalizedViolation]]:
    """
    Group violations by file path.

    Args:
        violations: List of violations

    Returns:
        Dict mapping file path to list of violations
    """
    grouped = defaultdict(list)
    for v in violations:
        grouped[v.file].append(v)
    return dict(grouped)


def group_by_rule(
    violations: List[NormalizedViolation],
) -> Dict[str, List[NormalizedViolation]]:
    """
    Group violations by rule name.

    Args:
        violations: List of violations

    Returns:
        Dict mapping rule name to list of violations
    """
    grouped = defaultdict(list)
    for v in violations:
        grouped[v.rule].append(v)
    return dict(grouped)


def group_by_engine(
    violations: List[NormalizedViolation],
) -> Dict[str, List[NormalizedViolation]]:
    """
    Group violations by engine.

    Args:
        violations: List of violations

    Returns:
        Dict mapping engine name to list of violations
    """
    grouped = defaultdict(list)
    for v in violations:
        grouped[v.engine].append(v)
    return dict(grouped)


def group_by_severity(
    violations: List[NormalizedViolation],
) -> Dict[str, List[NormalizedViolation]]:
    """
    Group violations by severity label.

    Args:
        violations: List of violations

    Returns:
        Dict mapping severity label to list of violations
    """
    grouped = defaultdict(list)
    for v in violations:
        grouped[v.severity_label].append(v)
    return dict(grouped)


def sort_violations(
    violations: List[NormalizedViolation],
    by: str = "severity",
    reverse: bool = False,
) -> List[NormalizedViolation]:
    """
    Sort violations.

    Args:
        violations: List of violations
        by: Sort key - "severity", "line", "file", "rule", "engine"
        reverse: Reverse sort order

    Returns:
        Sorted list of violations
    """
    key_funcs = {
        "severity": lambda v: v.severity,
        "line": lambda v: v.line,
        "file": lambda v: v.file.lower(),
        "rule": lambda v: v.rule.lower(),
        "engine": lambda v: v.engine.lower(),
    }

    key_func = key_funcs.get(by, key_funcs["severity"])
    return sorted(violations, key=key_func, reverse=reverse)


def deduplicate_violations(
    violations: List[NormalizedViolation],
    by: str = "rule_line",
) -> List[NormalizedViolation]:
    """
    Deduplicate violations.

    Args:
        violations: List of violations
        by: Dedup key - "rule" (same rule), "rule_line" (same rule and line),
            "message" (same message)

    Returns:
        Deduplicated list of violations
    """
    seen = set()
    result = []

    for v in violations:
        if by == "rule":
            key = v.rule
        elif by == "rule_line":
            key = (v.rule, v.file, v.line)
        elif by == "message":
            key = v.message
        else:
            key = (v.rule, v.file, v.line)

        if key not in seen:
            seen.add(key)
            result.append(v)

    return result


def get_violation_counts(violations: List[NormalizedViolation]) -> Dict[str, int]:
    """
    Get count of violations by severity.

    Args:
        violations: List of violations

    Returns:
        Dict with counts per severity and total
    """
    counts = {
        "total": len(violations),
        "critical": 0,
        "high": 0,
        "moderate": 0,
        "low": 0,
        "info": 0,
    }

    for v in violations:
        if v.severity == 1:
            counts["critical"] += 1
        elif v.severity == 2:
            counts["high"] += 1
        elif v.severity == 3:
            counts["moderate"] += 1
        elif v.severity == 4:
            counts["low"] += 1
        else:
            counts["info"] += 1

    return counts


def to_dict_list(violations: List[NormalizedViolation]) -> List[Dict[str, Any]]:
    """Convert list of violations to list of dicts."""
    return [v.to_dict() for v in violations]


if __name__ == "__main__":
    # Demo with sample data
    sample_output = {
        "violations": [
            {
                "rule": "AvoidSoqlInLoops",
                "engine": "pmd",
                "severity": 1,
                "message": "SOQL query found inside loop",
                "tags": ["Performance", "Apex"],
                "locations": [
                    {"file": "AccountService.cls", "startLine": 25, "startColumn": 5}
                ],
                "primaryLocationIndex": 0,
            },
            {
                "rule": "EmptyCatchBlock",
                "engine": "pmd",
                "severity": 2,
                "message": "Empty catch block",
                "tags": ["ErrorHandling", "Apex"],
                "locations": [
                    {"file": "AccountService.cls", "startLine": 40, "startColumn": 9}
                ],
                "primaryLocationIndex": 0,
            },
        ]
    }

    violations = parse_ca_output(sample_output)
    print(f"Parsed {len(violations)} violations")

    for v in violations:
        print(f"  [{v.severity_label}] {v.rule}: {v.message}")

    counts = get_violation_counts(violations)
    print(f"\nCounts: {counts}")
