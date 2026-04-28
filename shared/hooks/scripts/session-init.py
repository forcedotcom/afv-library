#!/usr/bin/env python3
"""
Session Init Hook (SessionStart - Synchronous)
===============================================

Initializes session directory and cleans up stale sessions.
This hook runs SYNCHRONOUSLY before async hooks to ensure the session
directory exists before async hooks write to it.

BEHAVIOR:
1. Gets Claude Code's PID (parent process)
2. Cleans up session directories for dead processes
3. Creates ~/.claude/sessions/{PID}/ directory
4. Writes session.json marker with timestamp

The PID-keyed session directory enables:
- Multi-session isolation (each Claude Code gets its own state)
- Automatic stale session detection (statusline checks if PID is alive)
- Clean exit behavior (dead PIDs get cleaned up on next start)

Input: JSON via stdin (SessionStart event data)
Output: Silent (no stdout to avoid JSON validation issues)

Installation:
  Registered automatically by tools/install.py (SessionStart, sync — runs before async hooks)
"""

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

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


# Session directory base
SESSIONS_DIR = Path.home() / ".claude" / "sessions"


def is_pid_alive(pid: int) -> bool:
    """
    Check if a process is still running (cross-platform).

    On Unix, uses signal 0.  On Windows, uses kernel32.OpenProcess
    since os.kill() only supports SIGTERM there.
    """
    if sys.platform == "win32":
        try:
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid
            )
            if handle:
                ctypes.windll.kernel32.CloseHandle(handle)
                return True
            return False
        except (OSError, AttributeError):
            return False
    else:
        try:
            os.kill(pid, 0)  # Signal 0 = check existence
            return True
        except (OSError, ProcessLookupError):
            return False
        except PermissionError:
            # Process exists but we can't signal it (different user)
            return True


def cleanup_old_sessions():
    """
    Remove session directories for dead processes.

    Iterates through ~/.claude/sessions/ and removes any directory
    whose name is a PID that is no longer running.
    """
    if not SESSIONS_DIR.exists():
        return

    for session_dir in SESSIONS_DIR.iterdir():
        if not session_dir.is_dir():
            continue
        try:
            pid = int(session_dir.name)
            if not is_pid_alive(pid):
                # Process is dead, clean up its session directory
                shutil.rmtree(session_dir, ignore_errors=True)
        except ValueError:
            # Directory name is not a valid PID, skip it
            pass


def cleanup_stale_settings_hooks():
    """
    Defense-in-depth: remove sf-skills hooks from settings.json that reference
    missing script files. Runs at session start to self-heal from interrupted
    updates or installer re-exec failures.

    Silent: no stdout output (would break Claude Code JSON parsing).
    Fast: only reads/writes a small JSON file.
    Idempotent: no-op if no stale hooks exist.
    """
    settings_file = Path.home() / ".claude" / "settings.json"
    if not settings_file.exists():
        return

    try:
        settings = json.loads(settings_file.read_text())
    except (json.JSONDecodeError, IOError):
        return

    if "hooks" not in settings:
        return

    removed = 0
    for event_name in list(settings["hooks"].keys()):
        cleaned = []
        for hook_group in settings["hooks"][event_name]:
            # Identify sf-skills hooks via path heuristic
            is_sf = False
            for nested in hook_group.get("hooks", []):
                cmd = nested.get("command", "")
                if any(indicator in cmd for indicator in (
                    ".claude/hooks", ".claude\\hooks",
                    "sf-skills",
                    "shared/hooks", "shared\\hooks",
                )):
                    is_sf = True
                    break

            if not is_sf:
                cleaned.append(hook_group)
                continue

            # Verify all referenced scripts exist on disk
            all_exist = True
            for nested in hook_group.get("hooks", []):
                cmd = nested.get("command", "")
                parts = cmd.split()
                # Find the script path (first part containing a path separator)
                for part in parts[1:]:
                    if "/" in part or "\\" in part:
                        if not Path(part).exists():
                            all_exist = False
                        break

            if all_exist:
                cleaned.append(hook_group)
            else:
                removed += 1

        settings["hooks"][event_name] = cleaned
        if not cleaned:
            del settings["hooks"][event_name]

    if "hooks" in settings and not settings["hooks"]:
        del settings["hooks"]

    if removed > 0:
        try:
            settings_file.write_text(json.dumps(settings, indent=2))
        except IOError:
            pass


def is_clear_event(input_data: dict) -> bool:
    """
    Detect if this is a /clear command (SessionStart:clear) vs fresh session.

    Claude Code passes event type info that we can use to detect /clear.
    The hook event name includes ':clear' suffix for context clears.
    """
    # Check hook_event_name if provided (e.g., "SessionStart:clear")
    hook_event = input_data.get("hook_event_name", "") or input_data.get("hook_event", "")
    if ":clear" in hook_event.lower():
        return True

    # Check session_id pattern if available
    session_id = input_data.get("session_id", "")
    if session_id and ":clear" in session_id.lower():
        return True

    return False


def session_state_is_valid(session_dir: Path, pid: int) -> bool:
    """
    Check if session state files exist and are valid for this PID.

    Returns True if we can skip re-initialization on /clear.
    """
    session_file = session_dir / "session.json"
    if not session_file.exists():
        return False

    try:
        with open(session_file, 'r') as f:
            existing = json.load(f)

        # Verify PID matches (session is still ours)
        if existing.get("pid") != pid:
            return False

        # Check timestamp freshness (within last hour)
        timestamp_str = existing.get("timestamp", "")
        if timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str)
            age = datetime.now() - timestamp
            if age.total_seconds() > 3600:  # Older than 1 hour
                return False

        return True
    except (json.JSONDecodeError, ValueError, KeyError):
        return False


def main():
    """
    Main entry point for the hook.

    This hook is SYNCHRONOUS and runs FIRST in the SessionStart sequence.
    It must complete before any async hooks run
    so they have a session directory to write to.

    On /clear events, if valid session state exists, we skip re-initialization
    to prevent status bar flicker (org/LSP state files remain valid).
    """
    # Read input from stdin (SessionStart event data) - with timeout to prevent blocking
    input_data = read_stdin_safe(timeout_seconds=0.1)

    # Get Claude Code's PID (our parent process)
    # Note: This hook runs as a child of Claude Code, so getppid() gives us
    # the Claude Code process ID
    pid = os.getppid()
    session_dir = SESSIONS_DIR / str(pid)

    # On /clear: skip re-initialization if session state is still valid
    # This prevents status bar from resetting to "Loading..." unnecessarily
    if is_clear_event(input_data) and session_state_is_valid(session_dir, pid):
        # Session state is valid, skip re-initialization
        # Async hooks will also detect this and skip
        sys.exit(0)

    # Clean up old sessions first (dead PIDs)
    cleanup_old_sessions()

    # Defense-in-depth: auto-clean stale hooks from settings.json
    # (catches interrupted updates or installer re-exec failures)
    cleanup_stale_settings_hooks()

    # Create this session's directory
    session_dir.mkdir(parents=True, exist_ok=True)

    # Write session marker with timestamp
    # This timestamp is used by statusline to determine if state files are "fresh"
    state = {
        "timestamp": datetime.now().isoformat(),
        "pid": pid
    }
    with open(session_dir / "session.json", 'w') as f:
        json.dump(state, f, indent=2)

    # SILENT: No stdout output to avoid JSON validation errors
    sys.exit(0)


if __name__ == "__main__":
    main()
