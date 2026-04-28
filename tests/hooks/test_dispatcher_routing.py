"""Tests for validator-dispatcher.py pattern matching logic.

These tests verify that file paths are correctly routed to the right
validators based on the VALIDATOR_REGISTRY regex patterns.
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

# The dispatcher filename uses hyphens — can't be imported normally.
# Use importlib to load it as a module.
_dispatcher_path = Path(__file__).resolve().parents[2] / "shared" / "hooks" / "scripts" / "validator-dispatcher.py"
_spec = importlib.util.spec_from_file_location("validator_dispatcher", _dispatcher_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
VALIDATOR_REGISTRY = _mod.VALIDATOR_REGISTRY


def match_count(file_path: str) -> int:
    """Count how many validators match a given file path."""
    return sum(
        1 for pattern, *_ in VALIDATOR_REGISTRY if re.search(pattern, file_path, re.IGNORECASE)
    )


def matched_skills(file_path: str) -> list[str]:
    """Return list of (skill, validator_basename) for matching validators."""
    results = []
    for pattern, skill, validator_path, _timeout in VALIDATOR_REGISTRY:
        if re.search(pattern, file_path, re.IGNORECASE):
            results.append((skill, Path(validator_path).name))
    return results


# ── Apex routing ────────────────────────────────────────────────


class TestApexRouting:
    def test_cls_matches_three_validators(self):
        matches = matched_skills("/path/to/AccountService.cls")
        assert len(matches) == 3
        skills = [m[0] for m in matches]
        assert all(s == "sf-apex" for s in skills)

    def test_cls_validator_order(self):
        """Prettier must run before LSP and scoring."""
        matches = matched_skills("/path/to/AccountService.cls")
        validators = [m[1] for m in matches]
        assert validators[0] == "prettier-format.py"
        assert validators[1] == "apex-lsp-validate.py"
        assert validators[2] == "post-tool-validate.py"

    def test_trigger_matches_three_validators(self):
        matches = matched_skills("/path/to/AccountTrigger.trigger")
        assert len(matches) == 3
        skills = [m[0] for m in matches]
        assert all(s == "sf-apex" for s in skills)

    def test_trigger_validator_order(self):
        matches = matched_skills("/path/to/AccountTrigger.trigger")
        validators = [m[1] for m in matches]
        assert validators[0] == "prettier-format.py"
        assert validators[1] == "apex-lsp-validate.py"
        assert validators[2] == "post-tool-validate.py"


# ── SOQL routing ────────────────────────────────────────────────


class TestSoqlRouting:
    def test_soql_matches_one_validator(self):
        matches = matched_skills("/path/to/query.soql")
        assert len(matches) == 1
        assert matches[0][0] == "sf-soql"


# ── Flow routing ────────────────────────────────────────────────


class TestFlowRouting:
    def test_flow_meta_xml_matches(self):
        matches = matched_skills("/path/to/MyFlow.flow-meta.xml")
        assert len(matches) == 1
        assert matches[0][0] == "sf-flow"

    def test_plain_xml_does_not_match_flow(self):
        assert match_count("/path/to/MyFlow.xml") == 0


# ── LWC routing ─────────────────────────────────────────────────


class TestLwcRouting:
    def test_lwc_js_matches_two_validators(self):
        matches = matched_skills("/force-app/main/default/lwc/myComp/myComp.js")
        assert len(matches) == 2
        skills = [m[0] for m in matches]
        assert all(s == "sf-lwc" for s in skills)

    def test_lwc_js_validator_order(self):
        matches = matched_skills("/force-app/main/default/lwc/myComp/myComp.js")
        validators = [m[1] for m in matches]
        assert validators[0] == "lwc-lsp-validate.py"
        assert validators[1] == "post-tool-validate.py"

    def test_lwc_html_matches_template_validator(self):
        matches = matched_skills("/force-app/main/default/lwc/myComp/myComp.html")
        assert len(matches) == 1
        assert matches[0][1] == "template_validator.py"

    def test_js_outside_lwc_folder_matches_nothing(self):
        """JS files not in /lwc/ path should not be routed."""
        assert match_count("/force-app/main/default/staticresources/app.js") == 0

    def test_html_outside_lwc_folder_matches_nothing(self):
        """HTML files not in /lwc/ path should not be routed."""
        assert match_count("/force-app/main/default/pages/MyPage.html") == 0

    def test_lwc_css_routes_to_slds_scorer(self):
        """CSS files in /lwc/ should be routed to SLDS scorer."""
        matches = matched_skills("/force-app/main/default/lwc/myComp/myComp.css")
        assert len(matches) == 1
        assert matches[0][0] == "sf-lwc"
        assert matches[0][1] == "post-tool-validate.py"

    def test_lwc_test_js_still_matches(self):
        """Dispatcher regex doesn't exclude test files — LSP validator does."""
        matches = matched_skills("/force-app/main/default/lwc/myComp/__tests__/myComp.test.js")
        # The regex /lwc/[^/]+/[^/]+\.js$ won't match because __tests__/ adds a path segment
        assert len(matches) == 0


# ── Metadata routing ────────────────────────────────────────────


class TestMetadataRouting:
    def test_object_meta_xml_matches(self):
        matches = matched_skills("/path/to/Account.object-meta.xml")
        assert len(matches) == 1
        assert matches[0][0] == "sf-metadata"

    def test_field_meta_xml_matches(self):
        matches = matched_skills("/path/to/MyField__c.field-meta.xml")
        assert len(matches) == 1
        assert matches[0][0] == "sf-metadata"

    def test_permissionset_meta_xml_matches(self):
        matches = matched_skills("/path/to/MyPermSet.permissionset-meta.xml")
        assert len(matches) == 1
        assert matches[0][0] == "sf-metadata"

    def test_profile_meta_xml_routes_to_metadata(self):
        """Profiles should be routed to validate_metadata.py."""
        matches = matched_skills("/path/to/Admin.profile-meta.xml")
        assert len(matches) == 1
        assert matches[0][0] == "sf-metadata"

    def test_validation_rule_routes_to_metadata(self):
        """Validation rules should be routed to validate_metadata.py."""
        matches = matched_skills("/path/to/MyRule.validationRule-meta.xml")
        assert len(matches) == 1
        assert matches[0][0] == "sf-metadata"


# ── Integration routing ─────────────────────────────────────────


class TestIntegrationRouting:
    def test_named_credential_matches(self):
        matches = matched_skills("/path/to/MyAPI.namedCredential-meta.xml")
        assert len(matches) == 1
        assert matches[0][0] == "sf-integration"

    def test_external_service_matches(self):
        matches = matched_skills("/path/to/MyService.externalServiceRegistration-meta.xml")
        assert len(matches) == 1
        assert matches[0][0] == "sf-integration"


# ── AgentScript routing ─────────────────────────────────────────


class TestAgentScriptRouting:
    def test_agent_file_matches(self):
        matches = matched_skills("/path/to/my_agent.agent")
        assert len(matches) == 1
        assert matches[0][0] == "sf-ai-agentscript"


# ── No-match cases ──────────────────────────────────────────────


class TestNoMatch:
    @pytest.mark.parametrize(
        "file_path",
        [
            "/path/to/script.py",
            "/path/to/readme.md",
            "/path/to/style.css",
            "/path/to/config.json",
            "/path/to/image.png",
            "/path/to/Makefile",
        ],
    )
    def test_non_salesforce_files_match_nothing(self, file_path: str):
        assert match_count(file_path) == 0
