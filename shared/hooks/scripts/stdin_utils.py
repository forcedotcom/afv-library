#!/usr/bin/env python3
"""
Shared stdin utilities for Claude Code hooks.

This module provides safe, non-blocking stdin reading for hook scripts.
Import this in any hook that needs to read JSON from stdin.

Usage:
    from stdin_utils import read_stdin_safe
    input_data = read_stdin_safe()
"""

import json
import sys


def read_stdin_safe(timeout_seconds: float = 0.1) -> dict:
    """
    Safely read JSON from stdin with timeout.

    Returns empty dict if:
    - stdin is a TTY (interactive terminal)
    - No data available within timeout
    - JSON parsing fails

    This prevents blocking when Claude Code doesn't pipe data correctly.

    Args:
        timeout_seconds: How long to wait for stdin data (default 0.1s)

    Returns:
        Parsed JSON dict, or empty dict on any error
    """
    # Skip if running interactively
    if sys.stdin.isatty():
        return {}

    try:
        if sys.platform == "win32":
            # On Windows, piped stdin is fully buffered — json.load reads
            # until EOF without blocking.  select.select() only works on
            # sockets on Windows, so we skip the readiness check entirely.
            return json.load(sys.stdin)
        else:
            import select
            # Use select to check if stdin has data (Unix only)
            readable, _, _ = select.select([sys.stdin], [], [], timeout_seconds)
            if not readable:
                return {}
            return json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, OSError, ValueError):
        return {}
