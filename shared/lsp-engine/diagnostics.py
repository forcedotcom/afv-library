#!/usr/bin/env python3
"""
Diagnostics Parser for LSP Output
=================================

This module formats LSP diagnostics into human-readable output
suitable for Claude Code hooks (auto-fix loop).

Features:
- Parses LSP diagnostic severity levels
- Formats errors/warnings for Claude to understand and fix
- Provides structured output for hook integration
"""

from typing import Dict, List, Any, Optional


# LSP Diagnostic Severity Levels
SEVERITY_ERROR = 1
SEVERITY_WARNING = 2
SEVERITY_INFO = 3
SEVERITY_HINT = 4

SEVERITY_NAMES = {
    SEVERITY_ERROR: "ERROR",
    SEVERITY_WARNING: "WARNING",
    SEVERITY_INFO: "INFO",
    SEVERITY_HINT: "HINT",
}

SEVERITY_ICONS = {
    SEVERITY_ERROR: "❌",
    SEVERITY_WARNING: "⚠️",
    SEVERITY_INFO: "ℹ️",
    SEVERITY_HINT: "💡",
}


class DiagnosticParser:
    """Parser for LSP diagnostic messages."""

    def __init__(self, diagnostics: List[Dict[str, Any]]):
        """
        Initialize the parser with diagnostics.

        Args:
            diagnostics: List of diagnostic objects from LSP
        """
        self.diagnostics = diagnostics

    def has_errors(self) -> bool:
        """Check if there are any errors (severity 1)."""
        return any(d.get("severity", 1) == SEVERITY_ERROR for d in self.diagnostics)

    def has_warnings(self) -> bool:
        """Check if there are any warnings (severity 2)."""
        return any(d.get("severity", 2) == SEVERITY_WARNING for d in self.diagnostics)

    def error_count(self) -> int:
        """Count errors."""
        return sum(1 for d in self.diagnostics if d.get("severity", 1) == SEVERITY_ERROR)

    def warning_count(self) -> int:
        """Count warnings."""
        return sum(1 for d in self.diagnostics if d.get("severity", 2) == SEVERITY_WARNING)

    def get_line_range(self, diagnostic: Dict[str, Any]) -> str:
        """Extract line range from diagnostic."""
        range_info = diagnostic.get("range", {})
        start = range_info.get("start", {})
        end = range_info.get("end", {})

        start_line = start.get("line", 0) + 1  # LSP is 0-indexed
        end_line = end.get("line", 0) + 1

        if start_line == end_line:
            return f"line {start_line}"
        return f"lines {start_line}-{end_line}"

    def format_single(self, diagnostic: Dict[str, Any]) -> str:
        """Format a single diagnostic message."""
        severity = diagnostic.get("severity", SEVERITY_ERROR)
        severity_name = SEVERITY_NAMES.get(severity, "UNKNOWN")
        icon = SEVERITY_ICONS.get(severity, "❓")

        message = diagnostic.get("message", "Unknown error")
        location = self.get_line_range(diagnostic)
        source = diagnostic.get("source", "agentscript")

        return f"{icon} [{severity_name}] {location}: {message} (source: {source})"

    def format_all(self) -> str:
        """Format all diagnostics as a string."""
        if not self.diagnostics:
            return ""

        lines = []
        for diag in self.diagnostics:
            lines.append(self.format_single(diag))

        return "\n".join(lines)


def format_diagnostics_for_claude(
    result: Dict[str, Any],
    file_path: Optional[str] = None,
    max_attempts: int = 3,
    current_attempt: int = 1,
) -> str:
    """
    Format LSP validation result for Claude Code hooks.

    This output is designed to be understood by Claude so it can
    automatically fix any issues found.

    Args:
        result: Validation result from LSPClient
        file_path: Path to the validated file
        max_attempts: Maximum fix attempts allowed
        current_attempt: Current attempt number

    Returns:
        Formatted string for hook output
    """
    # If LSP is not available or had an error
    if "error" in result and result["error"]:
        return f"⚠️ LSP validation skipped: {result['error']}"

    diagnostics = result.get("diagnostics", [])
    success = result.get("success", False)
    file_path = file_path or result.get("file_path", "unknown file")

    # No issues found
    if success and not diagnostics:
        return ""  # Empty output = success (hook convention)

    # Parse diagnostics
    parser = DiagnosticParser(diagnostics)
    error_count = parser.error_count()
    warning_count = parser.warning_count()

    # Build output for Claude
    lines = []

    # Header
    lines.append("=" * 60)
    lines.append(f"🔍 AGENT SCRIPT LSP VALIDATION RESULTS")
    lines.append(f"   File: {file_path}")
    lines.append(f"   Attempt: {current_attempt}/{max_attempts}")
    lines.append("=" * 60)
    lines.append("")

    # Summary
    if error_count > 0 or warning_count > 0:
        lines.append(f"Found {error_count} error(s), {warning_count} warning(s)")
        lines.append("")

    # Diagnostics
    if diagnostics:
        lines.append("ISSUES TO FIX:")
        lines.append("-" * 40)
        lines.append(parser.format_all())
        lines.append("")

    # Instructions for Claude
    if error_count > 0:
        lines.append("ACTION REQUIRED:")
        lines.append("Please fix the errors above and try again.")
        if current_attempt < max_attempts:
            lines.append(f"(Attempt {current_attempt}/{max_attempts})")
        else:
            lines.append("⚠️ Maximum attempts reached. Manual review may be needed.")

    lines.append("=" * 60)

    return "\n".join(lines)


def should_block_on_diagnostics(diagnostics: List[Dict[str, Any]]) -> bool:
    """
    Determine if the hook should block based on diagnostics.

    For auto-fix loop mode, we never block (return False).
    For strict mode, we block on errors (return True if errors exist).

    Args:
        diagnostics: List of diagnostic objects

    Returns:
        True if operation should be blocked
    """
    # In auto-fix loop mode, we don't block - just report
    return False


if __name__ == "__main__":
    # Test the formatters
    test_diagnostics = [
        {
            "severity": 1,
            "message": "Missing colon after 'system'",
            "range": {"start": {"line": 18, "character": 0}, "end": {"line": 18, "character": 6}},
            "source": "agentscript",
        },
        {
            "severity": 2,
            "message": "Indentation should be tabs, not spaces",
            "range": {"start": {"line": 25, "character": 0}, "end": {"line": 25, "character": 4}},
            "source": "agentscript",
        },
    ]

    result = {
        "success": False,
        "diagnostics": test_diagnostics,
        "file_path": "/test/example.agent",
    }

    print(format_diagnostics_for_claude(result))
