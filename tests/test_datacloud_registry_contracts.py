from __future__ import annotations

from tests.datacloud_test_utils import DATACLOUD_SKILLS, PROMPT_FIXTURES, entry_matches_prompt, load_registry


def test_registry_contains_all_datacloud_skills_with_basic_trigger_metadata() -> None:
    registry = load_registry()
    skills = registry["skills"]

    for skill in DATACLOUD_SKILLS:
        assert skill in skills, f"skills-registry.json is missing {skill}"
        entry = skills[skill]
        assert entry.get("keywords"), f"{skill} should define keywords"
        assert entry.get("intentPatterns"), f"{skill} should define intentPatterns"
        assert entry.get("description"), f"{skill} should define a description"
        assert entry.get("triggerWhen"), f"{skill} should define triggerWhen"
        assert entry.get("doNotTriggerWhen"), f"{skill} should define doNotTriggerWhen"
        assert entry.get("priority") in {"low", "medium", "high"}, f"{skill} should define a supported priority"



def test_registry_includes_background_operation_rules_for_long_running_datacloud_steps() -> None:
    registry = load_registry()
    background_operations = registry["background_operations"]

    assert background_operations["sf-datacloud-harmonize"]["commands"] == [
        "sf data360 identity-resolution run",
        "sf data360 data-graph refresh",
    ]
    assert background_operations["sf-datacloud-segment"]["commands"] == [
        "sf data360 segment publish",
        "sf data360 calculated-insight run",
    ]
    assert background_operations["sf-datacloud-retrieve"]["commands"] == [
        "sf data360 query async-create",
    ]



def test_registry_matches_representative_prompt_fixtures_for_each_datacloud_skill() -> None:
    skills = load_registry()["skills"]

    for skill, prompt in PROMPT_FIXTURES.items():
        assert entry_matches_prompt(skills[skill], prompt), (
            f"Representative prompt should match registry entry for {skill}: {prompt}"
        )
