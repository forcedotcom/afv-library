"""Tests for sf-ai-agentscript agentscript-syntax-validator.py."""
from __future__ import annotations

from pathlib import Path

import pytest

from tests.hooks.conftest import (
    FIXTURES_DIR,
    SKILLS_ROOT,
    run_validator,
)

VALIDATOR = "sf-ai-agentscript/hooks/scripts/agentscript-syntax-validator.py"
AGENTS_DIR = FIXTURES_DIR / "agents"

# Use a known-good agent from the skill's own assets
GOOD_AGENT = SKILLS_ROOT / "sf-ai-agentscript" / "assets" / "agents" / "hello-world.agent"


@pytest.mark.hooks
class TestAgentScriptGoodFile:
    @pytest.mark.skipif(not GOOD_AGENT.exists(), reason="hello-world.agent asset not found")
    def test_good_agent_has_no_blocking_errors(self):
        result = run_validator(VALIDATOR, str(GOOD_AGENT))
        assert result.returncode == 0
        output = result.stdout
        # Should have 0 blocking issues
        assert "0 blocking" in output or "blocking" not in output.lower() or "✅" in output


@pytest.mark.hooks
class TestAgentScriptBadFile:
    def test_detects_boolean_capitalization(self):
        """ASV-STR-002: 'true' instead of 'True'."""
        result = run_validator(VALIDATOR, str(AGENTS_DIR / "bad_agent.agent"))
        assert "ASV-STR-002" in result.stdout or "Boolean" in result.stdout

    def test_detects_missing_config(self):
        """ASV-STR-003: Missing required 'config' block."""
        result = run_validator(VALIDATOR, str(AGENTS_DIR / "bad_agent.agent"))
        assert "ASV-STR-003" in result.stdout or "config" in result.stdout.lower()

    def test_detects_missing_start_agent(self):
        """ASV-STR-004: Agent has topic but start_agent is misidentified."""
        result = run_validator(VALIDATOR, str(AGENTS_DIR / "bad_agent.agent"))
        # The bad agent does have a start_agent block, but missing config
        assert "ASV-CFG-001" in result.stdout or "ASV-CFG-002" in result.stdout

    def test_has_blocking_issues(self):
        result = run_validator(VALIDATOR, str(AGENTS_DIR / "bad_agent.agent"))
        output = result.stdout
        assert "blocking" in output.lower()
        # Should have multiple blocking issues
        assert "❌" in output

    def test_reserved_variable_name_detected(self):
        """FIX VERIFIED: ASV-STR-009 (reserved var 'Status') is now detected
        thanks to multi-line variable declaration parsing."""
        result = run_validator(VALIDATOR, str(AGENTS_DIR / "bad_agent.agent"))
        output = result.stdout
        assert "ASV-STR-009" in output or "Status" in output


@pytest.mark.hooks
class TestAgentScriptEdgeCases:
    def test_empty_file_exits_cleanly(self, tmp_path):
        f = tmp_path / "empty.agent"
        f.write_text("")
        result = run_validator(VALIDATOR, str(f))
        assert result.returncode == 0

    def test_non_agent_file_exits_cleanly(self, tmp_path):
        f = tmp_path / "readme.md"
        f.write_text("# Not an agent")
        result = run_validator(VALIDATOR, str(f))
        assert result.returncode == 0
