"""Tests for sf-integration validate_integration.py validator."""
from __future__ import annotations

import pytest

from tests.hooks.conftest import (
    FIXTURES_DIR,
    parse_score,
    run_validator,
)

VALIDATOR = "sf-integration/hooks/scripts/validate_integration.py"
NC_DIR = FIXTURES_DIR / "namedCredentials"


@pytest.mark.hooks
class TestIntegrationGoodFiles:
    def test_oauth_credential_exits_cleanly(self):
        result = run_validator(VALIDATOR, str(NC_DIR / "Good_OAuth.namedCredential-meta.xml"))
        assert result.returncode == 0

    def test_oauth_detects_oauth_protocol(self):
        result = run_validator(VALIDATOR, str(NC_DIR / "Good_OAuth.namedCredential-meta.xml"))
        output = result.stdout
        assert "OAuth" in output or "oauth" in output.lower() or "Security" in output

    def test_oauth_credential_not_deployment_blocked(self):
        """FIX VERIFIED: Good OAuth credential should score well above the
        45% DEPLOYMENT BLOCKED threshold now that non-applicable categories
        are scored at max for XML files."""
        result = run_validator(VALIDATOR, str(NC_DIR / "Good_OAuth.namedCredential-meta.xml"))
        score = parse_score(result.stdout)
        assert score is not None
        achieved, total = score
        assert achieved >= 100, f"Good OAuth scored {achieved}/{total} — should be >=100"
        assert "DEPLOYMENT BLOCKED" not in result.stdout

    def test_oauth_scores_higher_than_noauth(self):
        good = run_validator(VALIDATOR, str(NC_DIR / "Good_OAuth.namedCredential-meta.xml"))
        bad = run_validator(VALIDATOR, str(NC_DIR / "Bad_NoAuth.namedCredential-meta.xml"))
        good_score = parse_score(good.stdout)
        bad_score = parse_score(bad.stdout)
        assert good_score is not None and bad_score is not None
        assert good_score[0] > bad_score[0]


@pytest.mark.hooks
class TestIntegrationBadFiles:
    def test_no_auth_detected(self):
        result = run_validator(VALIDATOR, str(NC_DIR / "Bad_NoAuth.namedCredential-meta.xml"))
        output = result.stdout.lower()
        assert "no authentication" in output or "noauthentication" in output

    def test_password_in_metadata_detected(self):
        result = run_validator(VALIDATOR, str(NC_DIR / "Bad_NoAuth.namedCredential-meta.xml"))
        output = result.stdout.lower()
        assert "password" in output


@pytest.mark.hooks
class TestIntegrationEdgeCases:
    def test_template_file_skipped(self, tmp_path):
        """Files with {{ }} template placeholders should be silently skipped."""
        f = tmp_path / "Template.namedCredential-meta.xml"
        f.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<NamedCredential xmlns="http://soap.sforce.com/2006/04/metadata">\n'
            "    <endpoint>{{API_URL}}</endpoint>\n"
            "    <protocol>{{AUTH_TYPE}}</protocol>\n"
            "</NamedCredential>"
        )
        result = run_validator(VALIDATOR, str(f))
        assert result.returncode == 0

    def test_small_file_skipped(self, tmp_path):
        """Files under 50 bytes should be silently skipped."""
        f = tmp_path / "Tiny.namedCredential-meta.xml"
        f.write_text("<NC/>")
        result = run_validator(VALIDATOR, str(f))
        assert result.returncode == 0

    def test_non_integration_file_skipped(self, tmp_path):
        """Non-integration files should not produce scoring output."""
        f = tmp_path / "random.txt"
        f.write_text("Just some text content here that is long enough to pass the 50 byte check.")
        result = run_validator(VALIDATOR, str(f))
        assert result.returncode == 0
