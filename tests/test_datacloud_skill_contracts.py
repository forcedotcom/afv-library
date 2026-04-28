from __future__ import annotations

import json
from pathlib import Path

from tests.datacloud_test_utils import (
    DATACLOUD_SKILLS,
    EXPECTED_COMMANDS,
    EXPECTED_FRONTMATTER_LINES,
    EXPECTED_HEADINGS,
    PHASE_SKILLS,
    ROOT,
    skill_text,
    split_frontmatter,
)


def test_all_datacloud_skill_files_exist_and_use_frontmatter() -> None:
    for skill in DATACLOUD_SKILLS:
        text = skill_text(skill)
        frontmatter, body = split_frontmatter(text)
        assert frontmatter.strip(), f"{skill} frontmatter should not be empty"
        assert body.strip(), f"{skill} body should not be empty"



def test_datacloud_skill_frontmatter_has_expected_identity_and_runtime_contract() -> None:
    for skill, expected_lines in EXPECTED_FRONTMATTER_LINES.items():
        frontmatter, _ = split_frontmatter(skill_text(skill))
        assert 'version: "1.0.0"' in frontmatter, f"{skill} should declare metadata.version"
        for expected in expected_lines:
            assert expected in frontmatter, f"{skill} is missing frontmatter line: {expected}"



def test_datacloud_skill_bodies_include_required_sections() -> None:
    for skill, headings in EXPECTED_HEADINGS.items():
        _, body = split_frontmatter(skill_text(skill))
        for heading in headings:
            assert heading in body, f"{skill} is missing required heading: {heading}"



def test_datacloud_skill_bodies_include_curated_command_examples() -> None:
    for skill, commands in EXPECTED_COMMANDS.items():
        _, body = split_frontmatter(skill_text(skill))
        for command in commands:
            assert command in body, f"{skill} should explicitly include command example: {command}"



def test_orchestrator_links_every_phase_skill_and_core_assets() -> None:
    _, body = split_frontmatter(skill_text("sf-datacloud"))

    for phase_skill in PHASE_SKILLS:
        assert phase_skill in body, f"orchestrator should link to {phase_skill}"

    for asset in [
        "data-stream.template.json",
        "dmo.template.json",
        "mapping.template.json",
        "identity-resolution.template.json",
        "segment.template.json",
        "activation.template.json",
        "search-index.template.json",
        "scripts/verify-plugin.sh",
        "scripts/bootstrap-plugin.sh",
        "scripts/diagnose-org.mjs",
        "references/feature-readiness.md",
    ]:
        assert asset in body, f"orchestrator should reference deterministic asset: {asset}"



def test_phase_skills_delegate_to_adjacent_phases_or_neighboring_skills() -> None:
    expected_links = {
        "sf-datacloud-connect": ["sf-datacloud-prepare", "sf-datacloud-harmonize", "sf-datacloud-retrieve"],
        "sf-datacloud-prepare": ["sf-datacloud-connect", "sf-datacloud-harmonize", "sf-datacloud-retrieve"],
        "sf-datacloud-harmonize": ["sf-datacloud-prepare", "sf-datacloud-segment", "sf-datacloud-retrieve"],
        "sf-datacloud-segment": ["sf-datacloud-harmonize", "sf-datacloud-act", "sf-datacloud-retrieve"],
        "sf-datacloud-act": ["sf-datacloud-segment", "sf-datacloud-retrieve", "sf-datacloud-connect"],
        "sf-datacloud-retrieve": ["sf-soql", "sf-datacloud-segment", "sf-ai-agentforce-observability"],
    }

    for skill, linked_skills in expected_links.items():
        _, body = split_frontmatter(skill_text(skill))
        for linked_skill in linked_skills:
            assert linked_skill in body, f"{skill} should mention neighboring skill handoff: {linked_skill}"


def test_datacloud_skills_reference_shared_readiness_helpers() -> None:
    for skill in DATACLOUD_SKILLS:
        _, body = split_frontmatter(skill_text(skill))
        if skill == "sf-datacloud":
            assert "scripts/diagnose-org.mjs" in body
            assert "feature-readiness.md" in body
        else:
            assert "diagnose-org.mjs" in body, f"{skill} should point to the shared readiness classifier"
            assert "feature-readiness.md" in body, f"{skill} should reference feature-readiness guidance"



def test_datacloud_examples_exist_for_connection_and_search_index_workflows() -> None:
    expected_json_files = [
        ROOT / "skills/sf-datacloud-connect/examples/connections/heroku-postgres.json",
        ROOT / "skills/sf-datacloud-connect/examples/connections/redshift.json",
        ROOT / "skills/sf-datacloud-connect/examples/connections/sharepoint-unstructured.json",
        ROOT / "skills/sf-datacloud-connect/examples/connections/snowflake-connection.json",
        ROOT / "skills/sf-datacloud-connect/examples/connections/ingest-api-connection.json",
        ROOT / "skills/sf-datacloud-connect/examples/connections/ingest-api-schema.json",
        ROOT / "skills/sf-datacloud-retrieve/examples/search-indexes/hybrid-structured.json",
        ROOT / "skills/sf-datacloud-retrieve/examples/search-indexes/vector-knowledge.json",
    ]
    for path in expected_json_files:
        assert path.exists(), f"Expected example file to exist: {path.relative_to(ROOT)}"
        content = path.read_text().strip()
        assert content, f"Example file should not be empty: {path.relative_to(ROOT)}"
        json.loads(content)

    expected_text_files = [
        ROOT / "skills/sf-datacloud-prepare/examples/ingestion-api/.env.example",
        ROOT / "skills/sf-datacloud-prepare/examples/ingestion-api/README.md",
        ROOT / "skills/sf-datacloud-prepare/examples/ingestion-api/send-data.py",
    ]
    for path in expected_text_files:
        assert path.exists(), f"Expected example file to exist: {path.relative_to(ROOT)}"
        content = path.read_text().strip()
        assert content, f"Example file should not be empty: {path.relative_to(ROOT)}"
