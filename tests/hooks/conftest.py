"""Shared fixtures and helpers for validation hook tests."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pytest

# Repo root — two levels up from tests/hooks/
ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

# Validators live at skills/<skill>/hooks/scripts/ in the dev repo.
# In the installed layout they're at ~/.claude/skills/<skill>/hooks/scripts/.
# Override with VALIDATOR_ROOT env var for CI.
SKILLS_ROOT = Path(os.environ.get("VALIDATOR_ROOT", str(ROOT / "skills")))

# Shared Python modules the validators import from
SHARED_HOOKS_SCRIPTS = ROOT / "shared" / "hooks" / "scripts"
SHARED_DIR = ROOT / "shared"

# The dispatcher script itself
DISPATCHER_SCRIPT = SHARED_HOOKS_SCRIPTS / "validator-dispatcher.py"


def make_hook_input(
    file_path: str,
    tool_response: Optional[dict] = None,
    tool_name: str = "Write",
) -> dict:
    """Build the stdin JSON that the hook system sends to validators."""
    hook_input = {
        "tool_name": tool_name,
        "tool_input": {"file_path": str(file_path)},
    }
    if tool_response is not None:
        hook_input["tool_response"] = tool_response
    else:
        hook_input["tool_response"] = {"success": True}
    return hook_input


def _build_env(validator_rel_path: str) -> dict:
    """Build environment with PYTHONPATH for validator imports."""
    env = os.environ.copy()

    # The validator's own script directory (for sibling imports like validate_apex)
    validator_abs = SKILLS_ROOT / validator_rel_path
    validator_dir = str(validator_abs.parent)

    # Build PYTHONPATH: validator dir + shared hooks scripts + shared root
    python_paths = [
        validator_dir,
        str(SHARED_HOOKS_SCRIPTS),
        str(SHARED_DIR),
    ]
    existing = env.get("PYTHONPATH", "")
    if existing:
        python_paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(python_paths)

    # Disable org-aware checks by default (no SF org in CI)
    env.setdefault("AGENTSCRIPT_SKIP_ORG_CHECKS", "1")

    return env


def run_validator(
    validator_rel_path: str,
    file_path: str,
    tool_response: Optional[dict] = None,
    timeout: int = 30,
) -> subprocess.CompletedProcess:
    """Invoke a single validator via subprocess, piping stdin JSON.

    Args:
        validator_rel_path: Path relative to SKILLS_ROOT, e.g.
            "sf-metadata/hooks/scripts/validate_metadata.py"
        file_path: Absolute path to the file being validated.
        tool_response: Optional tool_response dict (defaults to {"success": true}).
        timeout: Subprocess timeout in seconds.

    Returns:
        CompletedProcess with stdout/stderr/returncode.
    """
    validator_abs = SKILLS_ROOT / validator_rel_path
    hook_input = make_hook_input(file_path, tool_response)

    return subprocess.run(
        [sys.executable, str(validator_abs)],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(SKILLS_ROOT),
        env=_build_env(validator_rel_path),
        check=False,
    )


def run_dispatcher(
    file_path: str,
    tool_response: Optional[dict] = None,
    timeout: int = 60,
) -> subprocess.CompletedProcess:
    """Invoke the central dispatcher, which routes to skill validators.

    The dispatcher resolves validators at SKILLS_ROOT (default ~/.claude/skills/).
    We override SKILLS_ROOT by patching the environment.
    """
    hook_input = make_hook_input(file_path, tool_response)
    env = os.environ.copy()

    # Shared hooks scripts on PYTHONPATH for stdin_utils import
    python_paths = [
        str(SHARED_HOOKS_SCRIPTS),
        str(SHARED_DIR),
    ]
    existing = env.get("PYTHONPATH", "")
    if existing:
        python_paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(python_paths)

    return subprocess.run(
        [sys.executable, str(DISPATCHER_SCRIPT)],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(SHARED_HOOKS_SCRIPTS),
        env=env,
        check=False,
    )


# ── Score parsing ──────────────────────────────────────────────

SCORE_RE = re.compile(r"(\d+)\s*/\s*(\d+)")


def parse_score(output: str) -> Optional[tuple[int, int]]:
    """Extract the first N/M score pattern from validator output.

    Returns (achieved, total) or None if no score found.
    """
    match = SCORE_RE.search(output)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None


# ── Pytest markers ─────────────────────────────────────────────

def pytest_configure(config):
    config.addinivalue_line("markers", "hooks: validation hook tests")
    config.addinivalue_line("markers", "org_required: tests requiring a connected Salesforce org")
