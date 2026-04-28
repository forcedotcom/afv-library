#!/usr/bin/env python3
"""
Debug Log Analyzer — PostToolUse Hook

Analyzes Salesforce debug log output from `sf apex get log` and `sf apex tail log`
commands. Detects common issues: exceptions, governor limit risks, SOQL/DML in loops,
and execution time.

Exits silently (no output) for non-debug-log commands so it doesn't interfere with
normal Bash hook flow.

Stdin JSON format (PostToolUse:Bash):
    {
        "tool_name": "Bash",
        "tool_input": {"command": "sf apex get log ..."},
        "tool_response": {"stdout": "...", "stderr": "...", "exitCode": 0}
    }
"""

import json
import re
import sys
from typing import List, Tuple

try:
    from stdin_utils import read_stdin_safe
except ImportError:
    def read_stdin_safe(timeout_seconds=0.1):
        if sys.stdin.isatty():
            return {}
        try:
            return json.load(sys.stdin)
        except Exception:
            return {}


def is_debug_log_command(command: str) -> bool:
    """Check if the command fetches Salesforce debug logs."""
    return bool(re.search(r'\bsf\s+apex\s+(get|tail)\s+log\b', command))


def find_exceptions(lines: List[str]) -> List[str]:
    """Extract EXCEPTION_THROWN and FATAL_ERROR entries."""
    results = []
    for i, line in enumerate(lines):
        if "EXCEPTION_THROWN" in line or "FATAL_ERROR" in line:
            # Include the next line for context if available
            detail = line.strip()
            if i + 1 < len(lines) and lines[i + 1].strip():
                detail += " | " + lines[i + 1].strip()
            results.append(detail)
    return results


def check_governor_limits(lines: List[str]) -> List[Tuple[str, int, int]]:
    """
    Check LIMIT_USAGE lines for any limits above 80%.

    Returns list of (limit_name, used, max) tuples.
    """
    results = []
    for line in lines:
        if "LIMIT_USAGE" not in line:
            continue
        # Pattern: "Number of SOQL queries: 95 out of 100"
        match = re.search(r'Number of (.+?):\s*(\d+)\s+out of\s+(\d+)', line)
        if match:
            name = match.group(1).strip()
            used = int(match.group(2))
            maximum = int(match.group(3))
            if maximum > 0 and (used / maximum) >= 0.8:
                results.append((name, used, maximum))
    return results


def detect_soql_dml_in_loops(lines: List[str]) -> List[str]:
    """
    Detect SOQL or DML operations inside loops by looking for repeated
    SOQL_EXECUTE_BEGIN or DML_BEGIN patterns within CODE_UNIT boundaries.
    """
    warnings = []
    soql_count = 0
    dml_count = 0
    in_code_unit = False

    for line in lines:
        if "CODE_UNIT_STARTED" in line:
            in_code_unit = True
            soql_count = 0
            dml_count = 0
        elif "CODE_UNIT_FINISHED" in line:
            if soql_count > 5:
                warnings.append(f"SOQL in loop risk: {soql_count} queries in one code unit")
            if dml_count > 5:
                warnings.append(f"DML in loop risk: {dml_count} DML ops in one code unit")
            in_code_unit = False
        elif in_code_unit:
            if "SOQL_EXECUTE_BEGIN" in line:
                soql_count += 1
            if "DML_BEGIN" in line:
                dml_count += 1

    return warnings


def extract_execution_time(lines: List[str]) -> str:
    """Extract total execution time from EXECUTION_FINISHED."""
    for line in reversed(lines):
        if "EXECUTION_FINISHED" in line:
            return line.strip()
    return ""


def analyze(output: str) -> str:
    """Analyze debug log output and return a structured summary."""
    lines = output.split("\n")

    exceptions = find_exceptions(lines)
    limits = check_governor_limits(lines)
    loop_warnings = detect_soql_dml_in_loops(lines)
    exec_time = extract_execution_time(lines)

    # If nothing notable found, stay quiet
    if not exceptions and not limits and not loop_warnings and not exec_time:
        return ""

    parts = []
    parts.append("Debug Log Analysis")
    parts.append("=" * 40)

    if exceptions:
        parts.append("")
        parts.append(f"EXCEPTIONS ({len(exceptions)}):")
        for exc in exceptions[:5]:  # Cap at 5
            parts.append(f"  - {exc[:200]}")

    if limits:
        parts.append("")
        parts.append("GOVERNOR LIMITS (>80%):")
        for name, used, maximum in limits:
            pct = int(used / maximum * 100) if maximum > 0 else 0
            parts.append(f"  - {name}: {used}/{maximum} ({pct}%)")

    if loop_warnings:
        parts.append("")
        parts.append("LOOP RISKS:")
        for w in loop_warnings[:5]:
            parts.append(f"  - {w}")

    if exec_time:
        parts.append("")
        parts.append(f"Execution: {exec_time[:200]}")

    return "\n".join(parts)


def main():
    data = read_stdin_safe()
    if not data:
        return

    # Only process Bash tool uses
    if data.get("tool_name") != "Bash":
        return

    command = data.get("tool_input", {}).get("command", "")
    if not is_debug_log_command(command):
        return

    stdout = data.get("tool_response", {}).get("stdout", "")
    if not stdout:
        return

    result = analyze(stdout)
    if result:
        print(result)


if __name__ == "__main__":
    main()
