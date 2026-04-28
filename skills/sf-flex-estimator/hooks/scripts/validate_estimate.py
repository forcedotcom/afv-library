#!/usr/bin/env python3
"""Manual validation helper for Flex Credit estimate inputs and outputs."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

VALID_PROMPT_TIERS = {"starter", "basic", "standard", "advanced"}
VALID_ACTION_TYPES = {"standard", "custom", "voice", "sandbox"}

METER_ALIASES = {
    "batch_internal": "data_360_prep",
    "batch_external": "data_360_prep",
    "queries": "data_360_queries",
    "segmentation": "data_360_segmentation",
    "streaming": "data_360_streaming_pipeline",
    "activation_batch": "data_360_activation",
    "activation_streaming": "data_360_activation",
    "profile_unification": "data_360_unification",
    "unstructured": "data_360_unstructured_processing",
    "intelligent_processing": "data_360_intelligent_processing",
    "real_time_pipeline": "data_360_real_time_pipeline",
    "code_extension": "data_360_code_extension",
}

DC_REASONABLE_RANGES: Dict[str, Tuple[float, float]] = {
    "data_360_prep": (0.1, 50_000),
    "data_360_unification": (0.01, 1_000),
    "data_360_segmentation": (0.1, 10_000),
    "data_360_activation": (0.1, 10_000),
    "data_360_zero_copy_sharing": (0.1, 10_000),
    "data_360_queries": (0.001, 100_000),
    "data_360_unstructured_processing": (1, 100_000),
    "data_360_intelligent_processing": (1, 100_000),
    "data_360_streaming_pipeline": (0.01, 1_000),
    "data_360_real_time_pipeline": (0.001, 1_000),
    "data_360_code_extension": (0.1, 100_000),
}

REASONABLE_PROMPTS = (0, 20)
REASONABLE_ACTIONS = (0, 50)
REASONABLE_INVOCATIONS = (100, 10_000_000)
TYPICAL_PER_INVOCATION_RANGE = (4, 500)


@dataclass
class ValidationResult:
    passed: bool
    score: int
    max_score: int
    errors: List[str]
    warnings: List[str]
    recommendations: List[str]


def normalize_meter(meter: str) -> str:
    key = meter.strip().lower()
    return METER_ALIASES.get(key, key)


def extract_agent_structure(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if "agent_structure" in data and isinstance(data["agent_structure"], dict):
        return data["agent_structure"]
    if "prompts" in data or "actions" in data:
        return data
    return None


def extract_dc_operations(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if "data_cloud_operations" in data and isinstance(data["data_cloud_operations"], dict):
        return data["data_cloud_operations"]
    if "operations" in data:
        return data
    return None


def validate_agent_structure(agent_data: Optional[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    if not agent_data:
        return errors, warnings

    prompts = agent_data.get("prompts", {})
    actions = agent_data.get("actions", {})

    total_prompts = sum(int(v) for v in prompts.values())
    total_actions = sum(int(v) for v in actions.values())

    if total_prompts < REASONABLE_PROMPTS[0]:
        warnings.append("Prompt count is below the normal range.")
    if total_prompts > REASONABLE_PROMPTS[1]:
        warnings.append(f"Many prompts configured ({total_prompts}). Consider consolidation.")

    if total_actions > REASONABLE_ACTIONS[1]:
        warnings.append(f"Many actions configured ({total_actions}). Consider consolidation or batching.")

    for tier in prompts:
        if tier.lower() not in VALID_PROMPT_TIERS:
            errors.append(f"Unknown prompt tier: {tier}")

    for action_type in actions:
        if action_type.lower() not in VALID_ACTION_TYPES:
            errors.append(f"Unknown action type: {action_type}")

    token_overages = agent_data.get("token_overages", {}) or {}
    prompt_overages = token_overages.get("prompts", 0)
    if isinstance(prompt_overages, (int, float)) and total_prompts > 0:
        overage_percent = float(prompt_overages) / total_prompts
        if overage_percent > 0.30:
            warnings.append(f"High prompt overage rate ({overage_percent:.1%}).")

    return errors, warnings


def validate_dc_operations(dc_data: Optional[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    if not dc_data:
        return errors, warnings

    operations = dc_data.get("operations", {})
    if not operations:
        warnings.append("Data Cloud operations document is present but contains no operations.")
        return errors, warnings

    normalized_ops: Dict[str, float] = {}
    for meter, volume in operations.items():
        canonical = normalize_meter(meter)
        normalized_ops[canonical] = normalized_ops.get(canonical, 0.0) + float(volume)

    for meter, volume in normalized_ops.items():
        if meter not in DC_REASONABLE_RANGES:
            warnings.append(f"Unknown Data Cloud meter: {meter}")
            continue

        min_volume, max_volume = DC_REASONABLE_RANGES[meter]
        if volume < min_volume:
            warnings.append(f"{meter}: very low volume ({volume}).")
        elif volume > max_volume:
            warnings.append(f"{meter}: very high volume ({volume}). Please confirm.")

    if normalized_ops.get("data_360_streaming_pipeline", 0) > 0:
        warnings.append("Streaming usage detected. Confirm that real-time latency is actually required.")

    if normalized_ops.get("data_360_unification", 0) > 10:
        warnings.append("Unification volume is high. Recheck cadence and identity-resolution scope.")

    return errors, warnings


def validate_scenarios(scenarios: Optional[List[Dict[str, Any]]]) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    if not scenarios:
        warnings.append("No scenarios found in estimate.")
        return errors, warnings

    for scenario in scenarios:
        name = scenario.get("scenario_name", "Unknown")
        for required in ["agent_invocations", "total_monthly_fc", "total_monthly_cost"]:
            if required not in scenario:
                errors.append(f"{name}: scenario missing required field {required}")

        invocations = int(scenario.get("agent_invocations", 0) or 0)
        if invocations < REASONABLE_INVOCATIONS[0]:
            warnings.append(f"{name}: very low invocation count ({invocations}).")
        elif invocations > REASONABLE_INVOCATIONS[1]:
            warnings.append(f"{name}: very high invocation count ({invocations:,}).")

        af_total = float(scenario.get("af_total_fc", 0) or 0)
        if invocations > 0 and af_total > 0:
            per_invocation = af_total / invocations
            if per_invocation < TYPICAL_PER_INVOCATION_RANGE[0]:
                warnings.append(f"{name}: low per-invocation cost ({per_invocation:.1f} FC).")
            elif per_invocation > TYPICAL_PER_INVOCATION_RANGE[1]:
                warnings.append(f"{name}: high per-invocation cost ({per_invocation:.1f} FC).")

        dc_base = float(scenario.get("dc_base_fc", 0) or 0)
        dc_tiered = float(scenario.get("dc_tiered_fc", 0) or 0)
        if dc_base > 300_000 and dc_tiered >= dc_base:
            errors.append(f"{name}: Data Cloud tiering does not appear to have been applied.")

        pc = float(scenario.get("dc_private_connect_fc", 0) or 0)
        if pc > 0 and dc_tiered > 0:
            expected_pc = round(dc_tiered * 0.20, 2)
            if abs(pc - expected_pc) / expected_pc > 0.01:
                errors.append(f"{name}: Private Connect appears inconsistent with tiered Data Cloud FC.")

    return errors, warnings


def calculate_score(errors: List[str], warnings: List[str]) -> int:
    score = 130
    score -= len(errors) * 10
    score -= len(warnings) * 2
    return max(0, score)


def validate_estimate(data: Dict[str, Any]) -> ValidationResult:
    errors: List[str] = []
    warnings: List[str] = []
    recommendations: List[str] = []

    agent_data = extract_agent_structure(data)
    dc_data = extract_dc_operations(data)
    scenarios = data.get("scenarios")

    if not agent_data and not dc_data:
        errors.append("Estimate must contain agent_structure, data_cloud_operations, or both.")

    agent_errors, agent_warnings = validate_agent_structure(agent_data)
    dc_errors, dc_warnings = validate_dc_operations(dc_data)
    scenario_errors, scenario_warnings = validate_scenarios(scenarios)

    errors.extend(agent_errors + dc_errors + scenario_errors)
    warnings.extend(agent_warnings + dc_warnings + scenario_warnings)

    if dc_data and dc_data.get("private_connect"):
        recommendations.append("Double-check that Private Connect is truly required, since it adds 20% to tiered Data Cloud FC.")

    if dc_data and normalize_meter("streaming") in {normalize_meter(m) for m in dc_data.get("operations", {})}:
        recommendations.append("Compare a lower-streaming alternative if latency requirements allow it.")

    if agent_data:
        prompts = sum(int(v) for v in agent_data.get("prompts", {}).values())
        actions = sum(int(v) for v in agent_data.get("actions", {}).values())
        if actions > prompts and actions >= 5:
            recommendations.append("Action count may be the dominant cost driver. Look for consolidation opportunities.")

    score = calculate_score(errors, warnings)
    passed = len(errors) == 0 and score >= 78

    return ValidationResult(
        passed=passed,
        score=score,
        max_score=130,
        errors=errors,
        warnings=warnings,
        recommendations=recommendations,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a Flex Credit estimate JSON document")
    parser.add_argument("--input", required=True, help="Path to estimate JSON")
    parser.add_argument("--verbose", action="store_true", help="Pretty-print output")
    args = parser.parse_args()

    try:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - CLI path
        print(f"Error loading estimate: {exc}", file=sys.stderr)
        raise SystemExit(1)

    result = validate_estimate(data)

    if args.verbose:
        print("\n" + "=" * 60)
        print("Flex Credit Estimate Validation")
        print("=" * 60)
        print(f"\nStatus: {'✅ PASSED' if result.passed else '❌ FAILED'}")
        print(f"Score: {result.score}/{result.max_score} ({result.score / result.max_score * 100:.1f}%)")

        if result.errors:
            print(f"\n❌ Errors ({len(result.errors)}):")
            for error in result.errors:
                print(f"  - {error}")

        if result.warnings:
            print(f"\n⚠️  Warnings ({len(result.warnings)}):")
            for warning in result.warnings:
                print(f"  - {warning}")

        if result.recommendations:
            print("\n💡 Recommendations:")
            for recommendation in result.recommendations:
                print(f"  - {recommendation}")

        print("\n" + "=" * 60 + "\n")
    else:
        print(
            json.dumps(
                {
                    "passed": result.passed,
                    "score": result.score,
                    "max_score": result.max_score,
                    "errors": result.errors,
                    "warnings": result.warnings,
                    "recommendations": result.recommendations,
                },
                indent=2,
            )
        )

    raise SystemExit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
