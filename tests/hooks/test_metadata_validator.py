"""Tests for sf-metadata validate_metadata.py validator."""
from __future__ import annotations

import pytest

from tests.hooks.conftest import (
    FIXTURES_DIR,
    parse_score,
    run_validator,
)

VALIDATOR = "sf-metadata/hooks/scripts/validate_metadata.py"
OBJECTS_DIR = FIXTURES_DIR / "objects"
PERMSETS_DIR = FIXTURES_DIR / "permissionsets"


@pytest.mark.hooks
class TestMetadataGoodFiles:
    def test_good_object_scores_high(self):
        result = run_validator(VALIDATOR, str(OBJECTS_DIR / "MyObject__c" / "MyObject__c.object-meta.xml"))
        assert result.returncode == 0
        score = parse_score(result.stdout)
        assert score is not None, f"No score in output: {result.stdout}"
        achieved, total = score
        assert total == 120
        assert achieved >= 110, f"Good object scored {achieved}/120"

    def test_good_field_scores_high(self):
        result = run_validator(VALIDATOR, str(OBJECTS_DIR / "MyObject__c" / "fields" / "GoodField__c.field-meta.xml"))
        assert result.returncode == 0
        score = parse_score(result.stdout)
        assert score is not None
        achieved, total = score
        assert achieved >= 110

    def test_good_permset_scores_perfect(self):
        result = run_validator(VALIDATOR, str(PERMSETS_DIR / "Good_PermSet.permissionset-meta.xml"))
        assert result.returncode == 0
        score = parse_score(result.stdout)
        assert score is not None
        achieved, total = score
        assert achieved == 120


@pytest.mark.hooks
class TestMetadataBadFiles:
    def test_ssn_field_detects_sensitive_data(self):
        result = run_validator(VALIDATOR, str(OBJECTS_DIR / "SSN_Object__c" / "fields" / "SSN_Number__c.field-meta.xml"))
        output = result.stdout.lower()
        assert "sensitive" in output or "ssn" in output

    def test_ssn_field_scores_lower(self):
        result = run_validator(VALIDATOR, str(OBJECTS_DIR / "SSN_Object__c" / "fields" / "SSN_Number__c.field-meta.xml"))
        score = parse_score(result.stdout)
        assert score is not None
        achieved, _ = score
        assert achieved < 115, f"Bad field should score lower, got {achieved}"

    def test_bad_permset_detects_view_all_data(self):
        result = run_validator(VALIDATOR, str(PERMSETS_DIR / "Bad_PermSet.permissionset-meta.xml"))
        output = result.stdout
        assert "ViewAllData" in output or "ModifyAllData" in output

    def test_bad_permset_detects_missing_description(self):
        result = run_validator(VALIDATOR, str(PERMSETS_DIR / "Bad_PermSet.permissionset-meta.xml"))
        output = result.stdout.lower()
        assert "description" in output

    def test_bad_permset_scores_lower_than_good(self):
        good = run_validator(VALIDATOR, str(PERMSETS_DIR / "Good_PermSet.permissionset-meta.xml"))
        bad = run_validator(VALIDATOR, str(PERMSETS_DIR / "Bad_PermSet.permissionset-meta.xml"))
        good_score = parse_score(good.stdout)
        bad_score = parse_score(bad.stdout)
        assert good_score is not None and bad_score is not None
        assert good_score[0] > bad_score[0]


@pytest.mark.hooks
class TestMetadataEdgeCases:
    def test_non_metadata_file_exits_silently(self, tmp_path):
        """Non-metadata extensions should produce no output."""
        f = tmp_path / "random.txt"
        f.write_text("not metadata")
        result = run_validator(VALIDATOR, str(f))
        assert result.returncode == 0

    def test_invalid_xml_returns_error(self, tmp_path):
        """Malformed XML should be caught."""
        f = tmp_path / "Broken.object-meta.xml"
        f.write_text("<CustomObject><broken>")
        result = run_validator(VALIDATOR, str(f))
        # Should either report an error or exit with non-zero
        output = (result.stdout + result.stderr).lower()
        has_error = "error" in output or "invalid" in output or "xml" in output
        assert has_error or result.returncode != 0
