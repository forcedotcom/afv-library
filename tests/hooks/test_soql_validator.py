"""Tests for sf-soql post-tool-validate.py validator."""
from __future__ import annotations

import pytest

from tests.hooks.conftest import (
    FIXTURES_DIR,
    run_validator,
)

VALIDATOR = "sf-soql/hooks/scripts/post-tool-validate.py"
QUERIES_DIR = FIXTURES_DIR / "queries"


@pytest.mark.hooks
class TestSoqlGoodQuery:
    def test_good_query_has_where(self):
        result = run_validator(VALIDATOR, str(QUERIES_DIR / "good_query.soql"))
        assert result.returncode == 0
        assert "Has WHERE" in result.stdout or "✅" in result.stdout

    def test_good_query_has_limit(self):
        result = run_validator(VALIDATOR, str(QUERIES_DIR / "good_query.soql"))
        assert "Has LIMIT" in result.stdout or "LIMIT" in result.stdout

    def test_good_query_no_critical_issues(self):
        result = run_validator(VALIDATOR, str(QUERIES_DIR / "good_query.soql"))
        output = result.stdout.lower()
        assert "invalid operator" not in output
        assert "unbalanced" not in output


@pytest.mark.hooks
class TestSoqlBadQuery:
    def test_bad_query_missing_where(self):
        result = run_validator(VALIDATOR, str(QUERIES_DIR / "bad_query.soql"))
        output = result.stdout
        assert "Missing WHERE" in output or "⚠️" in output

    def test_bad_query_missing_limit(self):
        result = run_validator(VALIDATOR, str(QUERIES_DIR / "bad_query.soql"))
        output = result.stdout
        assert "Missing LIMIT" in output or "LIMIT" in output


@pytest.mark.hooks
class TestSoqlSyntaxErrors:
    def test_detects_double_equals(self):
        result = run_validator(VALIDATOR, str(QUERIES_DIR / "syntax_error.soql"))
        assert "==" in result.stdout or "Invalid operator" in result.stdout

    def test_detects_unbalanced_parens(self):
        result = run_validator(VALIDATOR, str(QUERIES_DIR / "syntax_error.soql"))
        output = result.stdout.lower()
        assert "unbalanced" in output or "parenthes" in output


@pytest.mark.hooks
class TestSoqlEdgeCases:
    def test_empty_file_exits_silently(self, tmp_path):
        f = tmp_path / "empty.soql"
        f.write_text("")
        result = run_validator(VALIDATOR, str(f))
        assert result.returncode == 0

    def test_live_query_plan_degrades_gracefully(self):
        """Without a connected org, live query plan should show a message, not crash."""
        result = run_validator(VALIDATOR, str(QUERIES_DIR / "good_query.soql"))
        assert result.returncode == 0
        # Should mention no org or live query plan not available
        output = result.stdout.lower()
        assert "no org" in output or "not available" in output or "live query plan" in output or "org connected" in output
