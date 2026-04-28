#!/usr/bin/env python3
"""
Output Formatter - Terminal-friendly output for validation results.

Produces formatted output combining:
- Custom sf-skills scoring (150-point for Apex, etc.)
- Code Analyzer V5 findings
- Engine availability status
- Issue list with severity icons

Usage:
    output = format_validation_output(
        file_name="AccountService.cls",
        merged_score=merged,
        custom_issues=custom_issues,
        ca_violations=ca_violations,
    )
    print(output)
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


# Severity icons for terminal display
SEVERITY_ICONS = {
    "CRITICAL": "",
    "HIGH": "",
    "MODERATE": "",
    "WARNING": "",
    "LOW": "",
    "INFO": "",
}

# Category status icons
STATUS_ICONS = {
    "pass": "",
    "partial": "",
    "fail": "",
}


@dataclass
class FormattedIssue:
    """A formatted issue for display."""
    severity: str
    icon: str
    source: str
    line: int
    message: str
    fix: Optional[str] = None
    rule: Optional[str] = None


def format_validation_output(
    file_name: str,
    final_score: int,
    final_max: int,
    rating: str,
    rating_stars: int,
    category_scores: Dict[str, tuple],  # {category: (score, max)}
    engines_used: List[str],
    engines_unavailable: List[str],
    issues: List[FormattedIssue],
    scan_time_ms: int = 0,
) -> str:
    """
    Format complete validation output for terminal display.

    Args:
        file_name: Name of file being validated
        final_score: Final combined score
        final_max: Maximum possible score
        rating: Rating label (e.g., "Very Good")
        rating_stars: Number of stars (1-5)
        category_scores: Dict of category -> (score, max)
        engines_used: List of CA engines that ran
        engines_unavailable: List of unavailable engines
        issues: List of FormattedIssue objects
        scan_time_ms: Scan duration in milliseconds

    Returns:
        Formatted string for terminal output
    """
    lines = []

    # Header
    lines.append("")
    lines.append(f" Apex Validation: {file_name}")
    lines.append("" * 60)

    # Score with rating
    stars = "" * rating_stars + "" * (5 - rating_stars)
    lines.append(f" Score: {final_score}/{final_max} {stars} {rating}")

    # Category breakdown
    if category_scores:
        lines.append("")
        lines.append(" Category Breakdown:")
        for category, (score, max_score) in category_scores.items():
            if max_score > 0:
                if score == max_score:
                    icon = STATUS_ICONS["pass"]
                elif score >= max_score * 0.7:
                    icon = STATUS_ICONS["partial"]
                else:
                    icon = STATUS_ICONS["fail"]

                diff = ""
                if score < max_score:
                    diff = f" (-{max_score - score})"

                # Format category name nicely
                display_name = category.replace("_", " ").title()
                lines.append(f"   {icon} {display_name}: {score}/{max_score}{diff}")

    # Code Analyzer status
    lines.append("")
    if engines_used:
        lines.append(f" Code Analyzer Engines: {', '.join(engines_used)}")
    else:
        lines.append(" Code Analyzer: Not available")

    if engines_unavailable:
        lines.append(f"    Unavailable: {', '.join(engines_unavailable)}")

    if scan_time_ms > 0:
        lines.append(f"    Scan time: {scan_time_ms}ms")

    # Issues
    if issues:
        lines.append("")
        lines.append(f" Issues Found ({len(issues)}):")

        # Sort by severity
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2, "WARNING": 3, "LOW": 4, "INFO": 5}
        sorted_issues = sorted(issues, key=lambda x: severity_order.get(x.severity, 5))

        # Display up to 15 issues
        for issue in sorted_issues[:15]:
            source_tag = f"[{issue.source}]" if issue.source else ""
            line_tag = f"L{issue.line}" if issue.line else ""

            # Truncate message if too long
            message = issue.message
            if len(message) > 70:
                message = message[:67] + "..."

            lines.append(f"   {issue.icon} {issue.severity} {source_tag} {line_tag}: {message}")

            if issue.fix:
                fix = issue.fix
                if len(fix) > 60:
                    fix = fix[:57] + "..."
                lines.append(f"      Fix: {fix}")

        if len(issues) > 15:
            lines.append(f"   ... and {len(issues) - 15} more issues")
    else:
        lines.append("")
        lines.append(" No issues found!")

    # Footer
    lines.append("" * 60)

    return "\n".join(lines)


def format_score_summary(
    final_score: int,
    final_max: int,
    rating: str,
    rating_stars: int,
) -> str:
    """Format just the score line."""
    stars = "" * rating_stars + "" * (5 - rating_stars)
    return f" Score: {final_score}/{final_max} {stars} {rating}"


def format_issues_list(
    issues: List[FormattedIssue],
    max_issues: int = 15,
) -> str:
    """Format just the issues list."""
    if not issues:
        return " No issues found!"

    lines = [f" Issues Found ({len(issues)}):"]

    severity_order = {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2, "WARNING": 3, "LOW": 4, "INFO": 5}
    sorted_issues = sorted(issues, key=lambda x: severity_order.get(x.severity, 5))

    for issue in sorted_issues[:max_issues]:
        source_tag = f"[{issue.source}]" if issue.source else ""
        line_tag = f"L{issue.line}" if issue.line else ""
        message = issue.message[:70] + "..." if len(issue.message) > 70 else issue.message

        lines.append(f"   {issue.icon} {issue.severity} {source_tag} {line_tag}: {message}")

    if len(issues) > max_issues:
        lines.append(f"   ... and {len(issues) - max_issues} more issues")

    return "\n".join(lines)


def format_engine_status(
    engines_used: List[str],
    engines_unavailable: List[str],
) -> str:
    """Format engine availability status."""
    lines = []

    if engines_used:
        lines.append(f" Code Analyzer Engines: {', '.join(engines_used)}")
    else:
        lines.append(" Code Analyzer: Not available")

    if engines_unavailable:
        lines.append(f"    Unavailable: {', '.join(engines_unavailable)}")

    return "\n".join(lines)


def create_issue(
    severity: str,
    source: str,
    message: str,
    line: int = 0,
    fix: Optional[str] = None,
    rule: Optional[str] = None,
) -> FormattedIssue:
    """Create a FormattedIssue with proper icon."""
    icon = SEVERITY_ICONS.get(severity.upper(), "")
    return FormattedIssue(
        severity=severity.upper(),
        icon=icon,
        source=source,
        line=line,
        message=message,
        fix=fix,
        rule=rule,
    )


def merge_issues(
    custom_issues: List[Dict[str, Any]],
    ca_violations: List[Dict[str, Any]],
) -> List[FormattedIssue]:
    """
    Merge custom issues and CA violations into formatted issues list.

    Args:
        custom_issues: Issues from custom sf-skills validator
        ca_violations: Violations from Code Analyzer

    Returns:
        Combined list of FormattedIssue objects
    """
    issues = []

    # Add custom issues
    for issue in custom_issues:
        issues.append(create_issue(
            severity=issue.get("severity", "INFO"),
            source="sf-skills",
            message=issue.get("message", ""),
            line=issue.get("line", 0),
            fix=issue.get("fix"),
            rule=issue.get("rule"),
        ))

    # Add CA violations
    for violation in ca_violations:
        engine = violation.get("engine", "CA")
        issues.append(create_issue(
            severity=violation.get("severity_label", "INFO"),
            source=f"CA:{engine}",
            message=violation.get("message", ""),
            line=violation.get("line", 0),
            rule=violation.get("rule"),
        ))

    return issues


def format_compact_summary(
    file_name: str,
    final_score: int,
    final_max: int,
    issue_count: int,
) -> str:
    """Format a compact one-line summary."""
    status = "" if issue_count == 0 else ""
    return f"{status} {file_name}: {final_score}/{final_max} ({issue_count} issues)"


if __name__ == "__main__":
    # Demo output
    from score_merger import MergedScore

    category_scores = {
        "bulkification": (25, 25),
        "security": (20, 25),
        "testing": (25, 25),
        "architecture": (18, 20),
        "clean_code": (18, 20),
        "error_handling": (15, 15),
        "performance": (10, 10),
        "documentation": (7, 10),
    }

    issues = [
        create_issue("CRITICAL", "CA:pmd", "SOQL query inside loop", 25, "Move query outside loop"),
        create_issue("HIGH", "CA:pmd", "Empty catch block", 40, "Log or handle exception"),
        create_issue("MODERATE", "sf-skills", "Public method missing ApexDoc", 12),
        create_issue("LOW", "CA:regex", "Trailing whitespace", 1),
    ]

    output = format_validation_output(
        file_name="AccountService.cls",
        final_score=138,
        final_max=150,
        rating="Very Good",
        rating_stars=4,
        category_scores=category_scores,
        engines_used=["pmd", "regex", "sfge"],
        engines_unavailable=["eslint"],
        issues=issues,
        scan_time_ms=1250,
    )

    print(output)
