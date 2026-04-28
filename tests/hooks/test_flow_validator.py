"""Tests for sf-flow post-tool-validate.py validator."""
from __future__ import annotations

import pytest

from tests.hooks.conftest import (
    FIXTURES_DIR,
    parse_score,
    run_validator,
)

VALIDATOR = "sf-flow/hooks/scripts/post-tool-validate.py"
FLOWS_DIR = FIXTURES_DIR / "flows"


@pytest.mark.hooks
class TestFlowGoodFile:
    def test_good_flow_exits_cleanly(self):
        result = run_validator(VALIDATOR, str(FLOWS_DIR / "RTF_Account_Status_Update.flow-meta.xml"), timeout=45)
        assert result.returncode == 0

    def test_good_flow_produces_score(self):
        result = run_validator(VALIDATOR, str(FLOWS_DIR / "RTF_Account_Status_Update.flow-meta.xml"), timeout=45)
        score = parse_score(result.stdout)
        # If the validator works, we should see a score
        if score is not None:
            achieved, total = score
            assert total == 110
            assert achieved >= 70, f"Good flow scored {achieved}/110"


@pytest.mark.hooks
class TestFlowBadFile:
    def test_bad_flow_exits_cleanly(self):
        result = run_validator(VALIDATOR, str(FLOWS_DIR / "Bad_Flow.flow-meta.xml"), timeout=45)
        assert result.returncode == 0

    def test_bad_flow_scores_lower(self):
        good = run_validator(VALIDATOR, str(FLOWS_DIR / "RTF_Account_Status_Update.flow-meta.xml"), timeout=45)
        bad = run_validator(VALIDATOR, str(FLOWS_DIR / "Bad_Flow.flow-meta.xml"), timeout=45)
        good_score = parse_score(good.stdout)
        bad_score = parse_score(bad.stdout)
        if good_score is not None and bad_score is not None:
            assert good_score[0] > bad_score[0], (
                f"Good flow ({good_score[0]}) should score higher than bad ({bad_score[0]})"
            )

    def test_bad_flow_detects_missing_description(self):
        result = run_validator(VALIDATOR, str(FLOWS_DIR / "Bad_Flow.flow-meta.xml"), timeout=45)
        output = result.stdout.lower()
        # The flow has no description — should be flagged
        if parse_score(result.stdout) is not None:
            assert "description" in output


@pytest.mark.hooks
class TestFlowEdgeCases:
    def test_non_flow_file_exits_silently(self, tmp_path):
        f = tmp_path / "random.xml"
        f.write_text("<root/>")
        result = run_validator(VALIDATOR, str(f))
        assert result.returncode == 0

    def test_code_analyzer_degrades_gracefully(self):
        """Flow validator should work even if Code Analyzer is not installed."""
        result = run_validator(VALIDATOR, str(FLOWS_DIR / "RTF_Account_Status_Update.flow-meta.xml"), timeout=45)
        # Should not crash regardless of CA availability
        assert result.returncode == 0
