#!/usr/bin/env python3
"""Flex Credit calculator for Agentforce and Data Cloud."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

FC_COST = 0.004
PRIVATE_CONNECT_MULTIPLIER = 0.20

PROMPT_RATES: Dict[str, float] = {
    "starter": 2,
    "basic": 2,
    "standard": 4,
    "advanced": 16,
}

ACTION_RATES: Dict[str, float] = {
    "standard": 20,
    "custom": 20,
    "voice": 30,
    "sandbox": 16,
}

DC_RATES: Dict[str, float] = {
    "data_360_prep": 40,
    "data_360_unification": 75_000,
    "data_360_segmentation": 50,
    "data_360_activation": 60,
    "data_360_zero_copy_sharing": 60,
    "data_360_queries": 3,
    "data_360_unstructured_processing": 150,
    "data_360_intelligent_processing": 600,
    "data_360_streaming_pipeline": 3_500,
    "data_360_real_time_pipeline": 250_000,
    "data_360_code_extension": 40,
}

DC_ALIASES: Dict[str, str] = {
    "batch_internal": "data_360_prep",
    "batch_external": "data_360_prep",
    "prep": "data_360_prep",
    "profile_unification": "data_360_unification",
    "unification": "data_360_unification",
    "segmentation": "data_360_segmentation",
    "activation_batch": "data_360_activation",
    "activation_streaming": "data_360_activation",
    "queries": "data_360_queries",
    "unstructured": "data_360_unstructured_processing",
    "intelligent_processing": "data_360_intelligent_processing",
    "streaming": "data_360_streaming_pipeline",
    "real_time_pipeline": "data_360_real_time_pipeline",
    "zero_copy_sharing": "data_360_zero_copy_sharing",
    "code_extension": "data_360_code_extension",
}

TIER_THRESHOLDS: List[Tuple[float, float, float, str]] = [
    (0, 300_000, 1.0, "Tier 1"),
    (300_000, 1_500_000, 0.8, "Tier 2"),
    (1_500_000, 12_500_000, 0.4, "Tier 3"),
    (12_500_000, float("inf"), 0.2, "Tier 4"),
]


@dataclass
class AgentStructure:
    prompts: Dict[str, int] = field(default_factory=dict)
    actions: Dict[str, int] = field(default_factory=dict)
    token_overages: Dict[str, Any] = field(default_factory=lambda: {"prompts": 0, "actions": 0})

    def normalized(self) -> "AgentStructure":
        prompts = {k.lower(): int(v) for k, v in self.prompts.items() if int(v) != 0}
        actions = {k.lower(): int(v) for k, v in self.actions.items() if int(v) != 0}
        token_overages = self.token_overages or {"prompts": 0, "actions": 0}
        return AgentStructure(prompts=prompts, actions=actions, token_overages=token_overages)


@dataclass
class DataCloudOperations:
    operations: Dict[str, float] = field(default_factory=dict)
    private_connect: bool = False

    def normalized(self) -> "DataCloudOperations":
        normalized_ops: Dict[str, float] = {}
        for meter, volume in self.operations.items():
            canonical = normalize_meter_name(meter)
            normalized_ops[canonical] = normalized_ops.get(canonical, 0.0) + float(volume)
        return DataCloudOperations(operations=normalized_ops, private_connect=bool(self.private_connect))


@dataclass
class ScenarioVolumes:
    name: str
    agent_invocations: int
    dc_operations: Optional[Dict[str, float]] = None


@dataclass
class CostBreakdown:
    scenario_name: str
    agent_invocations: int
    af_prompt_fc: float
    af_action_fc: float
    af_token_overage_fc: float
    af_total_fc: float
    dc_base_fc: float
    dc_tiered_fc: float
    dc_discount_percent: float
    dc_private_connect_fc: float
    dc_total_fc: float
    total_monthly_fc: float
    total_monthly_cost: float
    total_annual_cost: float


def normalize_meter_name(meter: str) -> str:
    key = meter.strip().lower()
    return DC_ALIASES.get(key, key)


def empty_agent_structure() -> AgentStructure:
    return AgentStructure(
        prompts={"basic": 0, "standard": 0, "advanced": 0},
        actions={"standard": 0, "voice": 0, "sandbox": 0},
        token_overages={"prompts": 0, "actions": 0},
    )


def load_json(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def extract_agent_structure(data: Dict[str, Any]) -> AgentStructure:
    if not data:
        return empty_agent_structure()

    if "prompts" in data or "actions" in data:
        return AgentStructure(**data).normalized()

    nested = data.get("agent_structure")
    if isinstance(nested, dict):
        return AgentStructure(**nested).normalized()

    return empty_agent_structure()


def extract_dc_operations(data: Dict[str, Any]) -> Optional[DataCloudOperations]:
    if not data:
        return None

    if "operations" in data:
        return DataCloudOperations(**data).normalized()

    nested = data.get("data_cloud_operations")
    if isinstance(nested, dict):
        return DataCloudOperations(**nested).normalized()

    return None


def _weighted_extra_charge(base_breakdown: Dict[str, float], count: Any, total_components: int) -> float:
    if not count:
        return 0.0

    if isinstance(count, dict):
        raise TypeError("Dict-based overage handling is not supported by this helper")

    if total_components <= 0:
        return 0.0

    average_charge = base_breakdown["total_fc"] / total_components
    return float(count) * average_charge


def _explicit_prompt_overage_fc(prompt_overages: Dict[str, Any]) -> float:
    total = 0.0
    for tier, count in prompt_overages.items():
        total += PROMPT_RATES[tier.lower()] * float(count)
    return total


def _explicit_action_overage_fc(action_overages: Dict[str, Any]) -> float:
    total = 0.0
    for action_type, count in action_overages.items():
        total += ACTION_RATES[action_type.lower()] * float(count)
    return total


def calculate_per_invocation_cost(agent: AgentStructure) -> Tuple[float, Dict[str, float]]:
    agent = agent.normalized()

    prompt_fc = sum(PROMPT_RATES[tier] * count for tier, count in agent.prompts.items())
    action_fc = sum(ACTION_RATES[action_type] * count for action_type, count in agent.actions.items())

    prompt_count = sum(agent.prompts.values())
    action_count = sum(agent.actions.values())

    overage_fc = 0.0
    prompt_overages = (agent.token_overages or {}).get("prompts", 0)
    action_overages = (agent.token_overages or {}).get("actions", 0)

    if isinstance(prompt_overages, dict):
        overage_fc += _explicit_prompt_overage_fc(prompt_overages)
    else:
        overage_fc += _weighted_extra_charge(
            {"total_fc": prompt_fc}, prompt_overages, prompt_count
        )

    if isinstance(action_overages, dict):
        overage_fc += _explicit_action_overage_fc(action_overages)
    else:
        overage_fc += _weighted_extra_charge(
            {"total_fc": action_fc}, action_overages, action_count
        )

    total_fc = prompt_fc + action_fc + overage_fc

    breakdown = {
        "prompt_fc": round(prompt_fc, 2),
        "action_fc": round(action_fc, 2),
        "token_overage_fc": round(overage_fc, 2),
        "total_fc": round(total_fc, 2),
        "cost": round(total_fc * FC_COST, 4),
    }
    return round(total_fc, 2), breakdown


def calculate_dc_base_cost(dc_ops: DataCloudOperations) -> Tuple[float, Dict[str, Dict[str, float]]]:
    if not dc_ops:
        return 0.0, {}

    dc_ops = dc_ops.normalized()
    breakdown: Dict[str, Dict[str, float]] = {}
    total_fc = 0.0

    for meter, volume in dc_ops.operations.items():
        if meter not in DC_RATES:
            continue

        fc = float(volume) * DC_RATES[meter]
        breakdown[meter] = {
            "volume": round(float(volume), 4),
            "rate": DC_RATES[meter],
            "fc": round(fc, 2),
        }
        total_fc += fc

    return round(total_fc, 2), breakdown


def apply_tiered_multiplier(base_fc: float) -> Tuple[float, float, List[Dict[str, float]]]:
    if base_fc <= 0:
        return 0.0, 0.0, []

    remaining = float(base_fc)
    tiered_fc = 0.0
    tier_breakdown: List[Dict[str, float]] = []

    for start, end, multiplier, name in TIER_THRESHOLDS:
        if remaining <= 0:
            break

        tier_capacity = end - start
        fc_in_tier = min(remaining, tier_capacity)
        tier_value = fc_in_tier * multiplier
        tiered_fc += tier_value

        tier_breakdown.append(
            {
                "tier": name,
                "range_start": start,
                "range_end": end,
                "multiplier": multiplier,
                "base_fc": round(fc_in_tier, 2),
                "tiered_fc": round(tier_value, 2),
            }
        )
        remaining -= fc_in_tier

    discount_percent = ((base_fc - tiered_fc) / base_fc * 100) if base_fc > 0 else 0.0
    return round(tiered_fc, 2), round(discount_percent, 2), tier_breakdown


def calculate_scenario_cost(
    agent: AgentStructure,
    dc_ops: Optional[DataCloudOperations],
    scenario: ScenarioVolumes,
) -> CostBreakdown:
    per_invocation_fc, af_breakdown = calculate_per_invocation_cost(agent)
    af_total_fc = per_invocation_fc * scenario.agent_invocations

    dc_base_fc = 0.0
    dc_tiered_fc = 0.0
    dc_discount_percent = 0.0
    dc_private_connect_fc = 0.0

    if dc_ops and dc_ops.operations:
        effective_dc_ops = dc_ops
        if scenario.dc_operations is not None:
            effective_dc_ops = DataCloudOperations(
                operations=scenario.dc_operations,
                private_connect=dc_ops.private_connect,
            ).normalized()

        dc_base_fc, _ = calculate_dc_base_cost(effective_dc_ops)
        dc_tiered_fc, dc_discount_percent, _ = apply_tiered_multiplier(dc_base_fc)

        if effective_dc_ops.private_connect:
            dc_private_connect_fc = round(dc_tiered_fc * PRIVATE_CONNECT_MULTIPLIER, 2)

    dc_total_fc = round(dc_tiered_fc + dc_private_connect_fc, 2)
    total_monthly_fc = round(af_total_fc + dc_total_fc, 2)
    total_monthly_cost = round(total_monthly_fc * FC_COST, 2)
    total_annual_cost = round(total_monthly_cost * 12, 2)

    return CostBreakdown(
        scenario_name=scenario.name,
        agent_invocations=scenario.agent_invocations,
        af_prompt_fc=round(af_breakdown["prompt_fc"] * scenario.agent_invocations, 2),
        af_action_fc=round(af_breakdown["action_fc"] * scenario.agent_invocations, 2),
        af_token_overage_fc=round(af_breakdown["token_overage_fc"] * scenario.agent_invocations, 2),
        af_total_fc=round(af_total_fc, 2),
        dc_base_fc=round(dc_base_fc, 2),
        dc_tiered_fc=round(dc_tiered_fc, 2),
        dc_discount_percent=round(dc_discount_percent, 2),
        dc_private_connect_fc=round(dc_private_connect_fc, 2),
        dc_total_fc=round(dc_total_fc, 2),
        total_monthly_fc=round(total_monthly_fc, 2),
        total_monthly_cost=round(total_monthly_cost, 2),
        total_annual_cost=round(total_annual_cost, 2),
    )


def generate_standard_scenarios(
    agent: AgentStructure,
    dc_ops: Optional[DataCloudOperations] = None,
    scale_dc_volumes: bool = True,
) -> List[CostBreakdown]:
    scenarios = [
        ScenarioVolumes("Low (1K/month)", 1_000),
        ScenarioVolumes("Medium (10K/month)", 10_000),
        ScenarioVolumes("High (100K/month)", 100_000),
        ScenarioVolumes("Enterprise (500K/month)", 500_000),
    ]

    if dc_ops and dc_ops.operations and scale_dc_volumes:
        baseline_invocations = 1_000
        for scenario in scenarios:
            factor = scenario.agent_invocations / baseline_invocations
            scenario.dc_operations = {
                meter: round(volume * factor, 6)
                for meter, volume in dc_ops.normalized().operations.items()
            }

    return [calculate_scenario_cost(agent, dc_ops, scenario) for scenario in scenarios]


def _resolve_agent_and_dc(
    agent_path: Optional[str], dc_path: Optional[str]
) -> Tuple[AgentStructure, Optional[DataCloudOperations], Dict[str, Any], Dict[str, Any]]:
    agent_doc = load_json(agent_path) if agent_path else {}
    dc_doc = load_json(dc_path) if dc_path else agent_doc

    agent = extract_agent_structure(agent_doc)
    dc_ops = extract_dc_operations(dc_doc)
    if dc_ops is None:
        dc_ops = extract_dc_operations(agent_doc)

    return agent, dc_ops, agent_doc, dc_doc


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate Flex Credit estimates")
    parser.add_argument("--mode", required=True, choices=["structure", "scenarios", "tier-only"])
    parser.add_argument("--agent-def", help="Path to an agent or combined estimate JSON document")
    parser.add_argument("--dc-ops", help="Path to a Data Cloud or combined estimate JSON document")
    parser.add_argument("--base-fc", type=float, help="Base Data Cloud FC for tier-only mode")
    parser.add_argument("--output", help="Optional output JSON path")

    args = parser.parse_args()

    if args.mode == "tier-only":
        if args.base_fc is None:
            raise SystemExit("--base-fc is required for tier-only mode")
        tiered_fc, discount_percent, tier_breakdown = apply_tiered_multiplier(args.base_fc)
        result: Dict[str, Any] = {
            "base_fc": round(args.base_fc, 2),
            "tiered_fc": tiered_fc,
            "discount_percent": discount_percent,
            "tier_breakdown": tier_breakdown,
        }
    else:
        if not args.agent_def:
            raise SystemExit("--agent-def is required for structure and scenarios mode")

        agent, dc_ops, _, _ = _resolve_agent_and_dc(args.agent_def, args.dc_ops)

        if args.mode == "structure":
            per_invocation_fc, breakdown = calculate_per_invocation_cost(agent)
            result = {
                "per_invocation_fc": per_invocation_fc,
                "per_invocation_cost": round(per_invocation_fc * FC_COST, 4),
                "breakdown": breakdown,
            }
        else:
            scenarios = generate_standard_scenarios(agent, dc_ops)
            per_invocation_fc, breakdown = calculate_per_invocation_cost(agent)
            result = {
                "per_invocation_fc": per_invocation_fc,
                "per_invocation_cost": round(per_invocation_fc * FC_COST, 4),
                "breakdown": breakdown,
                "scenarios": [asdict(s) for s in scenarios],
            }

    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
