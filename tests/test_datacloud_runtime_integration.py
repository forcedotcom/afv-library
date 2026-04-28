from __future__ import annotations

import pytest

from tests.datacloud_test_utils import (
    CLI_HELP_COMMANDS,
    ENABLED_ORG_ALIAS,
    PARTIAL_ORG_ALIAS,
    output_json,
    output_text,
    run,
    sf_data360_available,
)

pytestmark = pytest.mark.integration



def _require_runtime() -> None:
    if not sf_data360_available():
        pytest.skip("sf data360 runtime is not installed; run bootstrap-plugin.sh first")



def _require_partial_org_alias() -> str:
    if not PARTIAL_ORG_ALIAS:
        pytest.skip("Set SF_DATACLOUD_PARTIAL_ORG_ALIAS to run partial-org Data Cloud integration tests")
    return PARTIAL_ORG_ALIAS



def _require_enabled_org_alias() -> str:
    if not ENABLED_ORG_ALIAS:
        pytest.skip("Set SF_DATACLOUD_ENABLED_ORG_ALIAS to run enabled-org Data Cloud integration tests")
    return ENABLED_ORG_ALIAS



def test_all_curated_datacloud_cli_commands_exist_in_installed_runtime() -> None:
    _require_runtime()

    for command in CLI_HELP_COMMANDS:
        result = run(command, timeout=180)
        assert result.returncode == 0, output_text(result)



def test_verify_plugin_script_allows_partial_org_feature_gating() -> None:
    _require_runtime()
    org_alias = _require_partial_org_alias()

    result = run(["bash", "skills/sf-datacloud/scripts/verify-plugin.sh", org_alias], timeout=300)
    output = output_text(result)

    assert result.returncode == 0, output
    assert "sf data360 runtime detected" in output
    assert f"org alias '{org_alias}' is authenticated" in output
    assert "Verification complete." in output



def test_diagnose_org_classifies_partial_org_feature_gates() -> None:
    _require_runtime()
    org_alias = _require_partial_org_alias()

    result = run(
        [
            "node",
            "skills/sf-datacloud/scripts/diagnose-org.mjs",
            "-o",
            org_alias,
            "--phase",
            "all",
            "--describe-table",
            "ssot__Individual__dlm",
            "--json",
        ],
        timeout=600,
    )
    output = output_text(result)
    data = output_json(result)

    assert result.returncode == 0, output
    assert data["runtime"]["state"] == "ok"
    assert data["org"]["alias"] == org_alias
    assert data["core"]["dmos"]["state"] in {"enabled_empty", "enabled_populated"}
    assert data["phases"]["prepare"]["checks"]["dataStreams"]["state"] == "feature_gated"
    assert data["phases"]["prepare"]["checks"]["dataStreams"]["code"] == "CdpDataStreams"
    assert data["phases"]["act"]["checks"]["activationPlatforms"]["state"] == "feature_gated"
    assert data["phases"]["act"]["checks"]["activationPlatforms"]["code"] == "CdpActivationExternalPlatform"
    assert data["phases"]["retrieve"]["checks"]["queryDescribe"]["state"] in {"query_service_unavailable", "table_not_found"}
    assert any("Feature Manager" in item or "Data Cloud Setup" in item for item in data["guidance"])



def test_diagnose_org_classifies_enabled_org_with_real_dmos_and_activation_catalog() -> None:
    _require_runtime()
    org_alias = _require_enabled_org_alias()

    result = run(
        [
            "node",
            "skills/sf-datacloud/scripts/diagnose-org.mjs",
            "-o",
            org_alias,
            "--phase",
            "all",
            "--json",
        ],
        timeout=600,
    )
    output = output_text(result)
    data = output_json(result)

    assert result.returncode == 0, output
    assert data["core"]["doctor"]["state"] == "ok"
    assert data["core"]["dataSpaces"]["state"] == "enabled_populated"
    assert data["phases"]["harmonize"]["checks"]["dmos"]["state"] == "enabled_populated"
    assert data["phases"]["harmonize"]["checks"]["dmos"]["sample"]["name"].startswith("ssot__")
    assert data["phases"]["act"]["checks"]["activationPlatforms"]["state"] == "enabled_populated"
    assert data["phases"]["act"]["checks"]["activationPlatforms"]["count"] > 0
    assert data["phases"]["act"]["checks"]["activationPlatforms"]["sample"]["name"]
