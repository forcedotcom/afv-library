#!/usr/bin/env python3
"""Validate Agent Script asset examples using profile-aware expectations.

Why this exists:
- Some files under assets/ are complete standalone templates.
- Some are reusable partial snippets that intentionally omit top-level blocks.
- Some are structurally valid but depend on org-specific resources.

This harness runs the main Agent Script validator against every asset file, then
interprets results according to `assets/validation-profiles.json`.
"""

from __future__ import annotations

import json
from collections import defaultdict
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "hooks/scripts/agentscript-syntax-validator.py"
PROFILES_PATH = ROOT / "assets/validation-profiles.json"


def load_validator():
    spec = spec_from_file_location("agentscript_validator", VALIDATOR_PATH)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.AgentScriptValidator


def extract_rule_id(message: str) -> str | None:
    if message.startswith("[") and "]" in message:
        return message[1 : message.index("]")]
    return None


def load_profiles() -> Dict:
    with PROFILES_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_file_map(profiles_payload: Dict) -> Dict[str, Dict]:
    file_map: Dict[str, Dict] = {}
    for profile in profiles_payload.get("profiles", []):
        for file_path in profile.get("files", []):
            resolved = str(Path(file_path).resolve())
            if resolved in file_map:
                raise SystemExit(f"Duplicate profile assignment for {file_path}")
            file_map[resolved] = profile
    return file_map


def main() -> int:
    AgentScriptValidator = load_validator()
    profiles_payload = load_profiles()
    file_map = build_file_map(profiles_payload)

    asset_files = sorted((ROOT / "assets").rglob("*.agent"))
    unprofiled = [str(path.resolve()) for path in asset_files if str(path.resolve()) not in file_map]
    if unprofiled:
        print("❌ Unprofiled asset files detected:")
        for path in unprofiled:
            print(f"  - {path}")
        return 1

    profile_stats: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {
            "files": 0,
            "blocking": 0,
            "warnings": 0,
            "unexpected_blocking": 0,
            "unexpected_warnings": 0,
        }
    )
    unexpected_blockers: List[Tuple[str, str]] = []
    unexpected_warnings: List[Tuple[str, str]] = []

    for path in asset_files:
        profile = file_map[str(path.resolve())]
        allowed_blocking_ids = set(profile.get("allowBlockingIds", []))
        allowed_warning_ids = set(profile.get("allowWarningIds", []))

        validator = AgentScriptValidator(path.read_text(encoding="utf-8"), str(path))
        result = validator.validate()

        profile_name = profile["name"]
        profile_stats[profile_name]["files"] += 1
        profile_stats[profile_name]["blocking"] += len(result["errors"])
        profile_stats[profile_name]["warnings"] += len(result["warnings"])

        for _, _, message in result["errors"]:
            rule_id = extract_rule_id(message)
            if rule_id not in allowed_blocking_ids:
                unexpected_blockers.append((str(path), message))
                profile_stats[profile_name]["unexpected_blocking"] += 1

        for _, _, message in result["warnings"]:
            rule_id = extract_rule_id(message)
            if rule_id not in allowed_warning_ids:
                unexpected_warnings.append((str(path), message))
                profile_stats[profile_name]["unexpected_warnings"] += 1

    print("Asset validation profile summary")
    print("-------------------------------")
    for profile in profiles_payload.get("profiles", []):
        stats = profile_stats[profile["name"]]
        print(
            f"- {profile['name']}: {stats['files']} files, "
            f"{stats['blocking']} raw blocking findings ({stats['unexpected_blocking']} unexpected), "
            f"{stats['warnings']} raw warnings ({stats['unexpected_warnings']} unexpected)"
        )

    failed = False
    if unexpected_blockers:
        failed = True
        print("\n❌ Unexpected blocking findings:")
        for path, message in unexpected_blockers[:20]:
            print(f"- {path}\n    {message}")
        if len(unexpected_blockers) > 20:
            print(f"  ... and {len(unexpected_blockers) - 20} more")

    if unexpected_warnings:
        failed = True
        print("\n❌ Unexpected warnings:")
        for path, message in unexpected_warnings[:20]:
            print(f"- {path}\n    {message}")
        if len(unexpected_warnings) > 20:
            print(f"  ... and {len(unexpected_warnings) - 20} more")

    if failed:
        return 1

    print("\n✅ All asset files matched their configured blocking and warning expectations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
