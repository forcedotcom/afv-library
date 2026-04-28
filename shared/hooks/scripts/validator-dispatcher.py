#!/usr/bin/env python3
"""
Validator Dispatcher (FIX 2)
============================

PostToolUse hook that routes to skill-specific validators based on file patterns.
This enables skill-specific validation without requiring SKILL.md frontmatter parsing.

Architecture:
  1. Receives Write/Edit hook context via stdin
  2. Extracts file_path from tool_input
  3. Matches file pattern to determine which skill's validator to run
  4. Executes the appropriate validator(s)
  5. Returns combined validation output

Usage:
  Called via hooks.json as PostToolUse hook on Write|Edit operations.

Example hooks.json entry:
  "PostToolUse": [
    {
      "matcher": "Write|Edit",
      "hooks": [
        {
          "type": "command",
          "command": "python3 ./shared/hooks/scripts/validator-dispatcher.py",
          "timeout": 10000
        }
      ]
    }
  ]
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Dict

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

# Get the base directory (shared/hooks/scripts/)
SCRIPT_DIR = Path(__file__).parent
SHARED_HOOKS_DIR = SCRIPT_DIR.parent  # shared/hooks/
# Skills are at ~/.claude/skills/ in the native layout
SKILLS_ROOT = Path.home() / ".claude" / "skills"

# Default and heavy validator timeouts (seconds)
DEFAULT_TIMEOUT = 10
HEAVY_TIMEOUT = 30

# File pattern to validator mapping
# Each entry: (regex_pattern, skill_name, validator_path, timeout_seconds)
VALIDATOR_REGISTRY: List[tuple] = [
    # Agent Script files (.agent)
    (
        r"\.agent$",
        "sf-ai-agentscript",
        "sf-ai-agentscript/hooks/scripts/agentscript-syntax-validator.py",
        DEFAULT_TIMEOUT,
    ),

    # Apex class files (.cls) - auto-format (runs BEFORE validation)
    (
        r"\.cls$",
        "sf-apex",
        "sf-apex/hooks/scripts/prettier-format.py",
        DEFAULT_TIMEOUT,
    ),

    # Apex trigger files (.trigger) - auto-format (runs BEFORE validation)
    (
        r"\.trigger$",
        "sf-apex",
        "sf-apex/hooks/scripts/prettier-format.py",
        DEFAULT_TIMEOUT,
    ),

    # Apex class files (.cls) - LSP syntax validation
    (
        r"\.cls$",
        "sf-apex",
        "sf-apex/hooks/scripts/apex-lsp-validate.py",
        HEAVY_TIMEOUT,
    ),

    # Apex class files (.cls) - 150-point scoring + Code Analyzer
    (
        r"\.cls$",
        "sf-apex",
        "sf-apex/hooks/scripts/post-tool-validate.py",
        HEAVY_TIMEOUT,
    ),

    # Apex trigger files (.trigger) - LSP syntax validation
    (
        r"\.trigger$",
        "sf-apex",
        "sf-apex/hooks/scripts/apex-lsp-validate.py",
        HEAVY_TIMEOUT,
    ),

    # Apex trigger files (.trigger) - 150-point scoring + Code Analyzer
    (
        r"\.trigger$",
        "sf-apex",
        "sf-apex/hooks/scripts/post-tool-validate.py",
        HEAVY_TIMEOUT,
    ),

    # SOQL query files (.soql) - 100-point scoring + Live Query Plan
    (
        r"\.soql$",
        "sf-soql",
        "sf-soql/hooks/scripts/post-tool-validate.py",
        DEFAULT_TIMEOUT,
    ),

    # Flow metadata files (.flow-meta.xml) - imports validate_flow + Code Analyzer
    (
        r"\.flow-meta\.xml$",
        "sf-flow",
        "sf-flow/hooks/scripts/post-tool-validate.py",
        HEAVY_TIMEOUT,
    ),

    # LWC JavaScript files - LSP syntax validation (in lwc/ folders)
    (
        r"/lwc/[^/]+/[^/]+\.js$",
        "sf-lwc",
        "sf-lwc/hooks/scripts/lwc-lsp-validate.py",
        HEAVY_TIMEOUT,
    ),

    # LWC JavaScript files - SLDS 2 scoring (in lwc/ folders)
    (
        r"/lwc/[^/]+/[^/]+\.js$",
        "sf-lwc",
        "sf-lwc/hooks/scripts/post-tool-validate.py",
        HEAVY_TIMEOUT,
    ),

    # LWC HTML templates (in lwc/ folders)
    (
        r"/lwc/[^/]+/[^/]+\.html$",
        "sf-lwc",
        "sf-lwc/hooks/scripts/template_validator.py",
        DEFAULT_TIMEOUT,
    ),

    # Custom Object metadata
    (
        r"\.object-meta\.xml$",
        "sf-metadata",
        "sf-metadata/hooks/scripts/validate_metadata.py",
        DEFAULT_TIMEOUT,
    ),

    # Custom Field metadata
    (
        r"\.field-meta\.xml$",
        "sf-metadata",
        "sf-metadata/hooks/scripts/validate_metadata.py",
        DEFAULT_TIMEOUT,
    ),

    # Permission Set metadata
    (
        r"\.permissionset-meta\.xml$",
        "sf-metadata",
        "sf-metadata/hooks/scripts/validate_metadata.py",
        DEFAULT_TIMEOUT,
    ),

    # Integration configuration (Named Credentials, External Services)
    (
        r"\.(namedCredential|externalServiceRegistration)-meta\.xml$",
        "sf-integration",
        "sf-integration/hooks/scripts/validate_integration.py",
        DEFAULT_TIMEOUT,
    ),

    # LWC CSS files - SLDS 2 scoring (in lwc/ folders)
    (
        r"/lwc/[^/]+/[^/]+\.css$",
        "sf-lwc",
        "sf-lwc/hooks/scripts/post-tool-validate.py",
        HEAVY_TIMEOUT,
    ),

    # Profile metadata
    (
        r"\.profile-meta\.xml$",
        "sf-metadata",
        "sf-metadata/hooks/scripts/validate_metadata.py",
        DEFAULT_TIMEOUT,
    ),

    # Validation Rule metadata
    (
        r"\.validationRule-meta\.xml$",
        "sf-metadata",
        "sf-metadata/hooks/scripts/validate_metadata.py",
        DEFAULT_TIMEOUT,
    ),

]


def find_validators_for_file(file_path: str) -> List[Dict]:
    """Find all validators that match the given file path."""
    validators = []

    for pattern, skill_name, validator_path, timeout in VALIDATOR_REGISTRY:
        if re.search(pattern, file_path, re.IGNORECASE):
            full_validator_path = SKILLS_ROOT / validator_path
            if full_validator_path.exists():
                validators.append({
                    "skill": skill_name,
                    "validator": str(full_validator_path),
                    "pattern": pattern,
                    "timeout": timeout
                })

    return validators


def run_validator(validator_path: str, hook_input: dict, timeout: int = 8) -> Optional[str]:
    """Run a validator script and capture its output."""
    try:
        # Pass the hook input via stdin (same format the validator expects)
        result = subprocess.run(
            [sys.executable, validator_path],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(SKILLS_ROOT)
        )

        # Combine stdout and stderr
        output = result.stdout.strip()
        if result.stderr.strip():
            output += "\n" + result.stderr.strip()

        return output if output else None

    except subprocess.TimeoutExpired:
        return f"⚠️ Validator timed out: {Path(validator_path).name}"
    except FileNotFoundError:
        return f"⚠️ Validator not found: {validator_path}"
    except Exception as e:
        return f"⚠️ Validator error: {e}"


def format_output(results: List[Dict], file_path: str) -> str:
    """Format validation results for display."""
    if not results:
        return ""

    lines = []
    lines.append("")
    lines.append("═" * 60)
    lines.append("🔍 VALIDATION RESULTS")
    lines.append("═" * 60)
    lines.append(f"📄 File: {Path(file_path).name}")
    lines.append("")

    has_output = False
    for result in results:
        if result.get("output"):
            has_output = True
            lines.append(f"📦 {result['skill']} validator:")
            lines.append(result["output"])
            lines.append("")

    if not has_output:
        lines.append("✅ All validations passed")

    lines.append("─" * 60)

    return "\n".join(lines)


def main():
    """Main entry point for the dispatcher."""
    # Read hook input from stdin with timeout to prevent blocking
    hook_input = read_stdin_safe(timeout_seconds=0.1)
    if not hook_input:
        sys.exit(0)

    # Extract file path
    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        sys.exit(0)

    # Find matching validators
    validators = find_validators_for_file(file_path)

    if not validators:
        # No validators match this file type
        sys.exit(0)

    # Run each validator and collect results
    results = []
    for validator_info in validators:
        output = run_validator(validator_info["validator"], hook_input, timeout=validator_info["timeout"])
        results.append({
            "skill": validator_info["skill"],
            "output": output
        })

    # Check if any validator produced output
    has_output = any(r.get("output") for r in results)

    if not has_output:
        sys.exit(0)

    # Format and output results
    formatted = format_output(results, file_path)

    # Output as hook response
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": formatted
        }
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
