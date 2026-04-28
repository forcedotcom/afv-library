#!/usr/bin/env python3
"""
SOQL Schema Validator — PreToolUse Hook

Validates sObject and field names in sf data query commands BEFORE execution
by running a targeted sf sobject describe against the actual org. Prevents
the common pattern of: query → fail (wrong name) → self-correct → retry.

How it works:
1. Reads Bash command from stdin
2. Skips non-query commands immediately (exit 0, ~0ms)
3. Extracts sObject name, field list, and --target-org from the SOQL
4. Runs: sf sobject describe --sobject <name> --target-org <org> --json
5. If sObject doesn't exist → BLOCK with error
6. If sObject exists → validate field names against describe output
7. On field mismatch → BLOCK with fuzzy "did you mean?" suggestion

No cache. Always fresh. One targeted describe per query (~2s).
"""

import difflib
import json
import os
import re
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

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


def extract_query_info(command: str) -> Optional[Dict]:
    """
    Extract sObject name, fields, target org, and tooling flag from an sf data query command.

    Returns None if the command is not an sf data query.
    """
    # Check if this is an sf data query command
    if not re.search(r'\bsf\s+data\s+query\b', command):
        return None

    # Extract the SOQL query string
    query_match = re.search(r'--query\s+["\']([^"\']+)["\']', command)
    if not query_match:
        # Try unquoted (less common)
        query_match = re.search(r'--query\s+(\S+)', command)
    if not query_match:
        return None

    soql = query_match.group(1).strip()

    # Extract FROM clause sObject
    from_match = re.search(r'\bFROM\s+(\w+)', soql, re.IGNORECASE)
    if not from_match:
        return None

    sobject_name = from_match.group(1)

    # Extract SELECT fields
    select_match = re.search(r'\bSELECT\s+(.+?)\s+FROM\b', soql, re.IGNORECASE)
    fields = []
    if select_match:
        field_str = select_match.group(1)
        # Split by comma, strip whitespace, handle COUNT() etc.
        for f in field_str.split(','):
            f = f.strip()
            # Skip aggregate functions, subqueries, *
            if f and not f.startswith('(') and f != '*' and '(' not in f:
                # Handle relationship fields like Account.Name → take last part
                if '.' in f:
                    f = f.split('.')[-1]
                fields.append(f)

    # Extract --target-org
    org_match = re.search(r'--target-org\s+(\S+)', command)
    target_org = org_match.group(1) if org_match else None

    # Check for --use-tooling-api
    use_tooling = '--use-tooling-api' in command

    return {
        'sobject': sobject_name,
        'fields': fields,
        'target_org': target_org,
        'use_tooling': use_tooling,
        'soql': soql,
    }


def describe_sobject(sobject_name: str, target_org: Optional[str], use_tooling: bool) -> Tuple[bool, Optional[Dict]]:
    """
    Run sf sobject describe to check if sObject exists and get its fields.

    Returns:
        (exists, describe_result) — exists is False if sObject not found.
    """
    cmd = ["sf", "sobject", "describe", "--sobject", sobject_name, "--json"]
    if target_org:
        cmd.extend(["--target-org", target_org])
    if use_tooling:
        cmd.append("--use-tooling-api")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=6)

        if result.returncode != 0:
            # Parse error to check if it's "not found"
            try:
                err = json.loads(result.stdout)
                if err.get("status") == 1 or "does not exist" in err.get("message", ""):
                    return (False, None)
            except (json.JSONDecodeError, KeyError):
                pass
            return (False, None)

        data = json.loads(result.stdout)
        return (True, data.get("result", {}))

    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        # On any error, allow the query (fail open)
        return (True, None)


def validate_fields(fields: List[str], describe_result: Dict) -> List[Dict]:
    """
    Validate field names against the describe result.

    Returns list of issues found.
    """
    if not describe_result or not fields:
        return []

    # Build set of valid field names (case-insensitive)
    valid_fields = {}
    for f in describe_result.get("fields", []):
        name = f.get("name", "")
        valid_fields[name.lower()] = name

    # Also add relationship names (e.g., Account.Name from lookup fields)
    for f in describe_result.get("fields", []):
        rel_name = f.get("relationshipName")
        if rel_name:
            valid_fields[rel_name.lower()] = rel_name

    issues = []
    all_valid_names = list(valid_fields.values())

    for field in fields:
        if field.lower() not in valid_fields:
            # Try fuzzy match
            matches = difflib.get_close_matches(field, all_valid_names, n=3, cutoff=0.6)
            suggestion = f" Did you mean: {', '.join(matches)}?" if matches else ""
            issues.append({
                "field": field,
                "suggestion": suggestion,
                "valid_count": len(all_valid_names),
            })

    return issues


def format_allow():
    """Return ALLOW response."""
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}


def format_block(reason: str, context: str = ""):
    """Return BLOCK response with reason."""
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    if context:
        output["hookSpecificOutput"]["additionalContext"] = context
    return output


def format_allow_with_context(context: str):
    """Return ALLOW with additional context (org field info)."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "additionalContext": context,
        }
    }


def main():
    """Main entry point."""
    input_data = read_stdin_safe(timeout_seconds=0.1)
    if not input_data:
        print(json.dumps(format_allow()))
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only process Bash commands
    if tool_name != "Bash":
        print(json.dumps(format_allow()))
        sys.exit(0)

    command = tool_input.get("command", "") if isinstance(tool_input, dict) else str(tool_input)
    if not command:
        print(json.dumps(format_allow()))
        sys.exit(0)

    # Extract query info — skip non-query commands (~0ms)
    query_info = extract_query_info(command)
    if not query_info:
        print(json.dumps(format_allow()))
        sys.exit(0)

    sobject = query_info['sobject']
    fields = query_info['fields']
    target_org = query_info['target_org']
    use_tooling = query_info['use_tooling']

    # Validate sObject via targeted describe (~2s)
    exists, describe_result = describe_sobject(sobject, target_org, use_tooling)

    if not exists:
        api_type = "Tooling API " if use_tooling else ""
        reason = f"{api_type}sObject '{sobject}' does not exist in this org."
        print(json.dumps(format_block(reason)))
        sys.exit(0)

    # sObject exists — validate fields
    if describe_result and fields:
        field_issues = validate_fields(fields, describe_result)

        if field_issues:
            issues_text = []
            for issue in field_issues:
                issues_text.append(f"Field '{issue['field']}' not found on {sobject}.{issue['suggestion']}")
            reason = " | ".join(issues_text)
            print(json.dumps(format_block(reason)))
            sys.exit(0)

        # All valid — inject field context for org awareness (3C)
        valid_field_names = [f.get("name") for f in describe_result.get("fields", []) if f.get("name")]
        if valid_field_names:
            context = f"✅ {sobject} validated ({len(valid_field_names)} fields available)"
            print(json.dumps(format_allow_with_context(context)))
            sys.exit(0)

    # All valid, no describe result (fail open)
    print(json.dumps(format_allow()))
    sys.exit(0)


if __name__ == "__main__":
    main()
