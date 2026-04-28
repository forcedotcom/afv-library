#!/usr/bin/env python3
"""
Prettier Auto-Format Hook for Apex files.

PostToolUse hook that runs prettier --write on .cls/.trigger files
after Write/Edit operations. Ensures consistent code formatting
before other validators run.

Requires: npm install -g prettier prettier-plugin-apex
Degrades gracefully if not installed.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

APEX_EXTENSIONS = {".cls", ".trigger"}

# Prettier runtime: local install at ~/.claude/prettier/ with prettier-plugin-apex
PRETTIER_DIR = Path.home() / ".claude" / "prettier"


def is_prettier_available() -> bool:
    """Check if prettier and prettier-plugin-apex are installed in the runtime dir."""
    npx_path = PRETTIER_DIR / "node_modules" / ".bin" / "prettier"
    return npx_path.exists()


def format_file(file_path: str) -> dict:
    """Run prettier on an Apex file and return the result."""
    if not os.path.exists(file_path):
        return {"formatted": False, "reason": "File not found"}

    ext = Path(file_path).suffix.lower()
    if ext not in APEX_EXTENSIONS:
        return {"formatted": False, "reason": "Not an Apex file"}

    if not is_prettier_available():
        return {"formatted": False, "reason": "prettier not installed (run sf-skills --update)"}

    # Read content before formatting
    try:
        with open(file_path, "r") as f:
            before = f.read()
    except Exception:
        return {"formatted": False, "reason": "Cannot read file"}

    # Run prettier from the runtime dir (where node_modules has the plugin)
    prettier_bin = str(PRETTIER_DIR / "node_modules" / ".bin" / "prettier")
    try:
        result = subprocess.run(
            [
                prettier_bin, "--write",
                "--plugin=prettier-plugin-apex",
                "--tab-width=4",
                "--print-width=120",
                os.path.abspath(file_path)
            ],
            capture_output=True, text=True, timeout=15,
            cwd=str(PRETTIER_DIR)
        )

        if result.returncode != 0:
            return {
                "formatted": False,
                "reason": f"prettier error: {result.stderr.strip()[:100]}"
            }

        # Read content after formatting
        with open(file_path, "r") as f:
            after = f.read()

        if before == after:
            return {"formatted": False, "reason": "Already formatted"}
        else:
            return {"formatted": True, "reason": "Auto-formatted by prettier"}

    except subprocess.TimeoutExpired:
        return {"formatted": False, "reason": "prettier timed out"}
    except Exception as e:
        return {"formatted": False, "reason": f"Error: {e}"}


def main():
    """Main entry point — reads hook input from stdin."""
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        print(json.dumps({"continue": True}))
        return

    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        print(json.dumps({"continue": True}))
        return

    result = format_file(file_path)

    if result.get("formatted"):
        output = {
            "continue": True,
            "output": f"✨ {result['reason']}: {Path(file_path).name}"
        }
    else:
        # Silent — don't pollute output when not formatted or unavailable
        output = {"continue": True}

    print(json.dumps(output))


if __name__ == "__main__":
    main()
