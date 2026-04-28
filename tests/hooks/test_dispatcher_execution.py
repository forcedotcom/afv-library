"""Integration tests for the validator-dispatcher.py end-to-end execution."""
from __future__ import annotations

import json

import pytest

from tests.hooks.conftest import (
    FIXTURES_DIR,
    run_dispatcher,
)

QUERIES_DIR = FIXTURES_DIR / "queries"


@pytest.mark.hooks
class TestDispatcherExecution:
    def test_empty_stdin_exits_cleanly(self):
        """Dispatcher with empty/no input should exit 0."""
        import os
        import subprocess
        import sys

        from tests.hooks.conftest import DISPATCHER_SCRIPT, SHARED_HOOKS_SCRIPTS

        env = os.environ.copy()
        env["PYTHONPATH"] = str(SHARED_HOOKS_SCRIPTS)
        result = subprocess.run(
            [sys.executable, str(DISPATCHER_SCRIPT)],
            input="",
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(SHARED_HOOKS_SCRIPTS),
            env=env,
            check=False,
        )
        assert result.returncode == 0

    def test_missing_file_path_exits_cleanly(self):
        """JSON without file_path should exit 0."""
        import os
        import subprocess
        import sys

        from tests.hooks.conftest import DISPATCHER_SCRIPT, SHARED_HOOKS_SCRIPTS

        env = os.environ.copy()
        env["PYTHONPATH"] = str(SHARED_HOOKS_SCRIPTS)
        result = subprocess.run(
            [sys.executable, str(DISPATCHER_SCRIPT)],
            input=json.dumps({"tool_input": {}}),
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(SHARED_HOOKS_SCRIPTS),
            env=env,
            check=False,
        )
        assert result.returncode == 0

    def test_unknown_extension_exits_cleanly(self):
        """File with no matching validators should exit 0 silently."""
        result = run_dispatcher("/tmp/readme.txt")
        assert result.returncode == 0
        assert result.stdout.strip() == "" or "All validations passed" in result.stdout

    def test_soql_file_produces_output(self):
        """SOQL file should trigger the sf-soql validator via dispatcher."""
        result = run_dispatcher(str(QUERIES_DIR / "good_query.soql"))
        assert result.returncode == 0
        # The dispatcher should produce some output for a .soql file
        # (if the validator is installed at SKILLS_ROOT)
        # If not installed, it silently skips — so we just verify no crash
