"""Tests for sf-lwc validators: template_validator, LWC LSP, and SLDS scorer."""
from __future__ import annotations

import pytest

from tests.hooks.conftest import (
    FIXTURES_DIR,
    run_validator,
)

TEMPLATE_VALIDATOR = "sf-lwc/hooks/scripts/template_validator.py"
LWC_LSP_VALIDATOR = "sf-lwc/hooks/scripts/lwc-lsp-validate.py"
LWC_POST_TOOL = "sf-lwc/hooks/scripts/post-tool-validate.py"
LWC_DIR = FIXTURES_DIR / "lwc"


# ── Template Validator ──────────────────────────────────────────


@pytest.mark.hooks
class TestTemplateValidatorGood:
    def test_clean_html_has_no_issues(self):
        result = run_validator(
            TEMPLATE_VALIDATOR,
            str(LWC_DIR / "goodComponent" / "goodComponent.html"),
        )
        assert result.returncode == 0
        output = result.stdout
        assert "No template anti-patterns" in output or "Critical (0)" in output or "0 issues" in output.lower()


@pytest.mark.hooks
class TestTemplateValidatorBad:
    def test_detects_inline_expression(self):
        result = run_validator(
            TEMPLATE_VALIDATOR,
            str(LWC_DIR / "badComponent" / "badComponent.html"),
        )
        output = result.stdout
        assert "Critical" in output or "CRITICAL" in output

    def test_detects_string_concatenation(self):
        result = run_validator(
            TEMPLATE_VALIDATOR,
            str(LWC_DIR / "badComponent" / "badComponent.html"),
        )
        assert "concatenation" in result.stdout.lower() or "+" in result.stdout

    def test_detects_ternary_operator(self):
        result = run_validator(
            TEMPLATE_VALIDATOR,
            str(LWC_DIR / "badComponent" / "badComponent.html"),
        )
        assert "ternary" in result.stdout.lower() or "?" in result.stdout

    def test_detects_length_access(self):
        result = run_validator(
            TEMPLATE_VALIDATOR,
            str(LWC_DIR / "badComponent" / "badComponent.html"),
        )
        assert ".length" in result.stdout

    def test_detects_vue_syntax(self):
        """FIX VERIFIED: v-for now visible in output after increasing critical[:10]."""
        result = run_validator(
            TEMPLATE_VALIDATOR,
            str(LWC_DIR / "badComponent" / "badComponent.html"),
        )
        assert "v-for" in result.stdout or "Vue" in result.stdout

    def test_detects_react_classname(self):
        """FIX VERIFIED: className now visible in output after increasing critical[:10]."""
        result = run_validator(
            TEMPLATE_VALIDATOR,
            str(LWC_DIR / "badComponent" / "badComponent.html"),
        )
        assert "className" in result.stdout or "React" in result.stdout

    def test_detects_arrow_function_in_handler(self):
        result = run_validator(
            TEMPLATE_VALIDATOR,
            str(LWC_DIR / "badComponent" / "badComponent.html"),
        )
        assert "arrow" in result.stdout.lower() or "=>" in result.stdout

    def test_detects_missing_key(self):
        result = run_validator(
            TEMPLATE_VALIDATOR,
            str(LWC_DIR / "badComponent" / "badComponent.html"),
        )
        assert "key" in result.stdout.lower()

    def test_detects_comparison_in_if_true(self):
        result = run_validator(
            TEMPLATE_VALIDATOR,
            str(LWC_DIR / "badComponent" / "badComponent.html"),
        )
        assert "comparison" in result.stdout.lower() or "if:true" in result.stdout.lower()


@pytest.mark.hooks
class TestTemplateValidatorEdgeCases:
    def test_non_lwc_html_path_skipped(self, tmp_path):
        """HTML file outside /lwc/ path should be skipped when run standalone."""
        f = tmp_path / "page.html"
        f.write_text("<template><p>{count > 0}</p></template>")
        result = run_validator(TEMPLATE_VALIDATOR, str(f))
        # Standalone mode checks for /lwc/ in path — should skip
        assert result.returncode == 0

    def test_empty_html_file(self, tmp_path):
        """Empty file should not crash."""
        d = tmp_path / "lwc" / "emptyComp"
        d.mkdir(parents=True)
        f = d / "emptyComp.html"
        f.write_text("")
        result = run_validator(TEMPLATE_VALIDATOR, str(f))
        assert result.returncode == 0


# ── LWC LSP Validator (graceful degradation) ────────────────────


@pytest.mark.hooks
class TestLwcLspValidator:
    def test_exits_cleanly(self):
        """LSP validator should exit 0 whether or not the LSP engine is available."""
        result = run_validator(
            LWC_LSP_VALIDATOR,
            str(LWC_DIR / "goodComponent" / "goodComponent.js"),
        )
        assert result.returncode == 0

    def test_does_not_crash_on_bad_file(self):
        result = run_validator(
            LWC_LSP_VALIDATOR,
            str(LWC_DIR / "badComponent" / "badComponent.js"),
        )
        assert result.returncode == 0


# ── LWC Post-Tool Validator (SLDS scoring) ──────────────────────


@pytest.mark.hooks
class TestLwcPostToolValidator:
    def test_js_file_exits_cleanly(self):
        result = run_validator(
            LWC_POST_TOOL,
            str(LWC_DIR / "goodComponent" / "goodComponent.js"),
        )
        assert result.returncode == 0

    def test_html_file_exits_cleanly(self):
        """Post-tool validator accepts HTML internally even though dispatcher
        only sends JS files to it. Test direct invocation."""
        result = run_validator(
            LWC_POST_TOOL,
            str(LWC_DIR / "goodComponent" / "goodComponent.html"),
        )
        assert result.returncode == 0
