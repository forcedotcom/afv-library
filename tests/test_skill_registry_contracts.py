from __future__ import annotations

from pathlib import Path

from tests.datacloud_test_utils import ROOT, load_registry


def test_registry_contains_every_sf_skill_directory() -> None:
    registry_skills = load_registry()["skills"]
    skill_dirs = sorted(path.name for path in (ROOT / "skills").glob("sf-*") if path.is_dir())

    missing = [skill for skill in skill_dirs if skill not in registry_skills]
    assert not missing, f"skills-registry.json is missing entries for: {', '.join(missing)}"



def test_registry_does_not_reference_missing_sf_skill_directories() -> None:
    registry_skills = load_registry()["skills"]
    skill_dirs = {path.name for path in (ROOT / "skills").glob("sf-*") if path.is_dir()}

    extra = sorted(skill for skill in registry_skills if skill.startswith("sf-") and skill not in skill_dirs)
    assert not extra, f"skills-registry.json references missing skill directories: {', '.join(extra)}"
