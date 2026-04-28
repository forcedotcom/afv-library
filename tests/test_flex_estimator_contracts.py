from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "sf-flex-estimator"


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


FLEX = _load_module(
    "sf_flex_estimator_calculator",
    SKILL_DIR / "assets" / "calculators" / "flex_calculator.py",
)
VALIDATOR = _load_module(
    "sf_flex_estimator_validator",
    SKILL_DIR / "hooks" / "scripts" / "validate_estimate.py",
)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_skill_scaffold_exists() -> None:
    expected = [
        SKILL_DIR / "SKILL.md",
        SKILL_DIR / "README.md",
        SKILL_DIR / "CREDITS.md",
        SKILL_DIR / "LICENSE",
        SKILL_DIR / "assets" / "calculators" / "flex_calculator.py",
        SKILL_DIR / "assets" / "calculators" / "tier_multiplier.py",
        SKILL_DIR / "assets" / "templates" / "basic-agent-template.json",
        SKILL_DIR / "assets" / "templates" / "hybrid-agent-template.json",
        SKILL_DIR / "assets" / "templates" / "data-cloud-template.json",
        SKILL_DIR / "references" / "agentforce-pricing.md",
        SKILL_DIR / "references" / "data-cloud-pricing.md",
        SKILL_DIR / "references" / "calculation-methodology.md",
        SKILL_DIR / "references" / "common-use-cases.md",
        SKILL_DIR / "references" / "edge-cases.md",
        SKILL_DIR / "references" / "scoring-rubric.md",
        SKILL_DIR / "hooks" / "scripts" / "validate_estimate.py",
    ]

    missing = [path.relative_to(ROOT).as_posix() for path in expected if not path.exists()]
    assert not missing, f"Missing expected sf-flex-estimator files: {', '.join(missing)}"


def test_skill_frontmatter_identity() -> None:
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name: sf-flex-estimator" in text
    assert "version: \"1.1.0\"" in text
    assert "scenario planning" in text


def test_basic_template_per_invocation_cost() -> None:
    data = _json(SKILL_DIR / "assets" / "templates" / "basic-agent-template.json")
    agent = FLEX.extract_agent_structure(data)
    per_invocation_fc, breakdown = FLEX.calculate_per_invocation_cost(agent)

    assert per_invocation_fc == pytest.approx(70.0)
    assert breakdown["prompt_fc"] == pytest.approx(10)
    assert breakdown["action_fc"] == pytest.approx(60)
    assert breakdown["cost"] == pytest.approx(0.28)


def test_hybrid_template_scenarios_match_reference_values() -> None:
    data = _json(SKILL_DIR / "assets" / "templates" / "hybrid-agent-template.json")
    agent = FLEX.extract_agent_structure(data)
    dc_ops = FLEX.extract_dc_operations(data)

    scenarios = FLEX.generate_standard_scenarios(agent, dc_ops)
    by_name = {scenario.scenario_name: scenario for scenario in scenarios}

    assert len(scenarios) == 4
    assert by_name["Low (1K/month)"].total_monthly_fc == pytest.approx(121_465.0)
    assert by_name["Medium (10K/month)"].total_monthly_cost == pytest.approx(4_858.60)
    assert by_name["High (100K/month)"].dc_tiered_fc == pytest.approx(657_200.0)
    assert by_name["Enterprise (500K/month)"].dc_discount_percent == pytest.approx(42.32)


def test_data_cloud_only_template_generates_expected_medium_tiering() -> None:
    data = _json(SKILL_DIR / "assets" / "templates" / "data-cloud-template.json")
    agent = FLEX.extract_agent_structure(data)
    dc_ops = FLEX.extract_dc_operations(data)

    scenarios = FLEX.generate_standard_scenarios(agent, dc_ops)
    by_name = {scenario.scenario_name: scenario for scenario in scenarios}

    assert FLEX.calculate_per_invocation_cost(agent)[0] == pytest.approx(0.0)
    assert by_name["Medium (10K/month)"].dc_base_fc == pytest.approx(2_038_000.0)
    assert by_name["Medium (10K/month)"].dc_tiered_fc == pytest.approx(1_475_200.0)
    assert by_name["Medium (10K/month)"].total_monthly_cost == pytest.approx(5_900.80)


def test_tier_multiplier_reference_example() -> None:
    tiered_fc, discount_percent, _ = FLEX.apply_tiered_multiplier(5_000_000)
    assert tiered_fc == pytest.approx(2_660_000.0)
    assert discount_percent == pytest.approx(46.8)


def test_manual_validator_accepts_hybrid_template() -> None:
    data = _json(SKILL_DIR / "assets" / "templates" / "hybrid-agent-template.json")
    result = VALIDATOR.validate_estimate(data)

    assert result.passed is True
    assert result.score == pytest.approx(126)
    assert any("No scenarios found" in warning for warning in result.warnings)
