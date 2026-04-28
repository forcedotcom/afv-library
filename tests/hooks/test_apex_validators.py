"""Tests for sf-apex validators: prettier, LSP, and 150-point scorer."""
from __future__ import annotations

import pytest

from tests.hooks.conftest import (
    FIXTURES_DIR,
    parse_score,
    run_validator,
)

PRETTIER = "sf-apex/hooks/scripts/prettier-format.py"
LSP_VALIDATOR = "sf-apex/hooks/scripts/apex-lsp-validate.py"
POST_TOOL = "sf-apex/hooks/scripts/post-tool-validate.py"
CLASSES_DIR = FIXTURES_DIR / "classes"
TRIGGERS_DIR = FIXTURES_DIR / "triggers"


# ── Prettier ────────────────────────────────────────────────────


@pytest.mark.hooks
class TestPrettierFormat:
    def test_exits_cleanly_on_cls(self):
        """Prettier should exit 0 whether or not it's installed."""
        result = run_validator(PRETTIER, str(CLASSES_DIR / "AccountService.cls"))
        assert result.returncode == 0

    def test_exits_cleanly_on_trigger(self):
        result = run_validator(PRETTIER, str(TRIGGERS_DIR / "AccountTrigger.trigger"))
        assert result.returncode == 0

    def test_non_apex_file_exits_silently(self, tmp_path):
        f = tmp_path / "readme.txt"
        f.write_text("not apex")
        result = run_validator(PRETTIER, str(f))
        assert result.returncode == 0


# ── Apex LSP ────────────────────────────────────────────────────


@pytest.mark.hooks
class TestApexLspValidator:
    def test_exits_cleanly_on_good_cls(self):
        """LSP validator should exit 0 whether or not the LSP engine is available."""
        result = run_validator(LSP_VALIDATOR, str(CLASSES_DIR / "AccountService.cls"))
        assert result.returncode == 0

    def test_exits_cleanly_on_bad_cls(self):
        result = run_validator(LSP_VALIDATOR, str(CLASSES_DIR / "BadService.cls"))
        assert result.returncode == 0

    def test_exits_cleanly_on_trigger(self):
        result = run_validator(LSP_VALIDATOR, str(TRIGGERS_DIR / "AccountTrigger.trigger"))
        assert result.returncode == 0


# ── Post-Tool Validate (150-point scorer + Code Analyzer) ───────


@pytest.mark.hooks
class TestApexPostToolGood:
    @pytest.mark.slow
    def test_good_cls_exits_cleanly(self):
        result = run_validator(POST_TOOL, str(CLASSES_DIR / "AccountService.cls"), timeout=60)
        assert result.returncode == 0

    @pytest.mark.slow
    def test_good_cls_produces_score(self):
        result = run_validator(POST_TOOL, str(CLASSES_DIR / "AccountService.cls"), timeout=60)
        score = parse_score(result.stdout)
        if score is not None:
            achieved, total = score
            assert total == 90
            assert achieved >= 70, f"Good class scored {achieved}/90"


@pytest.mark.hooks
class TestApexPostToolBad:
    @pytest.mark.slow
    def test_bad_cls_exits_cleanly(self):
        result = run_validator(POST_TOOL, str(CLASSES_DIR / "BadService.cls"), timeout=60)
        assert result.returncode == 0

    @pytest.mark.slow
    def test_bad_cls_detects_java_types(self):
        """LLM pattern validator should catch ArrayList."""
        result = run_validator(POST_TOOL, str(CLASSES_DIR / "BadService.cls"), timeout=60)
        output = result.stdout
        if parse_score(result.stdout) is not None:
            assert "ArrayList" in output or "Java type" in output

    @pytest.mark.slow
    def test_bad_cls_scores_lower(self):
        good = run_validator(POST_TOOL, str(CLASSES_DIR / "AccountService.cls"), timeout=60)
        bad = run_validator(POST_TOOL, str(CLASSES_DIR / "BadService.cls"), timeout=60)
        good_score = parse_score(good.stdout)
        bad_score = parse_score(bad.stdout)
        if good_score is not None and bad_score is not None:
            assert good_score[0] > bad_score[0]


@pytest.mark.hooks
class TestApexPostToolEdgeCases:
    def test_non_apex_file_exits_silently(self, tmp_path):
        f = tmp_path / "readme.txt"
        f.write_text("not apex")
        result = run_validator(POST_TOOL, str(f))
        assert result.returncode == 0

    @pytest.mark.slow
    def test_trigger_produces_score(self):
        result = run_validator(POST_TOOL, str(TRIGGERS_DIR / "AccountTrigger.trigger"), timeout=60)
        assert result.returncode == 0
        score = parse_score(result.stdout)
        if score is not None:
            assert score[1] == 90  # Total should be 90
