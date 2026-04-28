#!/usr/bin/env python3
"""Standalone Data Cloud tier multiplier calculator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

TIERS: List[Tuple[float, float, float, str]] = [
    (0, 300_000, 1.0, "Tier 1"),
    (300_000, 1_500_000, 0.8, "Tier 2"),
    (1_500_000, 12_500_000, 0.4, "Tier 3"),
    (12_500_000, float("inf"), 0.2, "Tier 4"),
]


def calculate_tiered_fc(base_fc: float, verbose: bool = False) -> Dict[str, object]:
    if base_fc <= 0:
        return {
            "base_fc": round(base_fc, 2),
            "tiered_fc": 0.0,
            "discount_percent": 0.0,
            "savings_fc": 0.0,
            "savings_dollars": 0.0,
            "tier_breakdown": [],
        }

    remaining = float(base_fc)
    tiered_fc = 0.0
    tier_breakdown = []

    for start, end, multiplier, label in TIERS:
        if remaining <= 0:
            break

        tier_capacity = end - start
        fc_in_tier = min(remaining, tier_capacity)
        fc_after_multiplier = fc_in_tier * multiplier
        savings = fc_in_tier - fc_after_multiplier
        tiered_fc += fc_after_multiplier

        if verbose or fc_in_tier > 0:
            discount_pct = round((1 - multiplier) * 100)
            tier_breakdown.append(
                {
                    "tier": label,
                    "range": f"{start:,.0f} - {end:,.0f} FC" if end != float('inf') else f"{start:,.0f}+ FC",
                    "multiplier": f"{multiplier:.1f}x",
                    "discount": f"{discount_pct}%",
                    "base_fc_in_tier": round(fc_in_tier, 2),
                    "tiered_fc_in_tier": round(fc_after_multiplier, 2),
                    "savings_in_tier": round(savings, 2),
                }
            )

        remaining -= fc_in_tier

    savings_fc = base_fc - tiered_fc
    discount_percent = (savings_fc / base_fc * 100) if base_fc > 0 else 0.0

    return {
        "base_fc": round(base_fc, 2),
        "tiered_fc": round(tiered_fc, 2),
        "discount_percent": round(discount_percent, 2),
        "savings_fc": round(savings_fc, 2),
        "savings_dollars": round(savings_fc * 0.004, 2),
        "tier_breakdown": tier_breakdown,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate cumulative Data Cloud tiering")
    parser.add_argument("--base-fc", type=float, required=True, help="Base monthly Data Cloud FC before tiering")
    parser.add_argument("--verbose", action="store_true", help="Include detailed tier breakdown")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print results")
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()

    result = calculate_tiered_fc(args.base_fc, verbose=args.verbose or args.pretty)

    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    if args.pretty:
        print("\n" + "=" * 60)
        print("Data Cloud Tiered Multiplier Calculation")
        print("=" * 60)
        print(f"\nBase FC:          {result['base_fc']:>15,.0f} FC")
        print(f"Tiered FC:        {result['tiered_fc']:>15,.0f} FC")
        print(f"Savings:          {result['savings_fc']:>15,.0f} FC (${result['savings_dollars']:,.2f})")
        print(f"Discount:         {result['discount_percent']:>15.2f}%")

        if result["tier_breakdown"]:
            print("\nTier Breakdown:")
            print("-" * 60)
            for tier in result["tier_breakdown"]:
                if tier["base_fc_in_tier"] > 0:
                    print(f"\n{tier['tier']} ({tier['range']})")
                    print(f"  Multiplier:     {tier['multiplier']:>8} ({tier['discount']} discount)")
                    print(f"  Base FC:        {tier['base_fc_in_tier']:>15,.0f} FC")
                    print(f"  After discount: {tier['tiered_fc_in_tier']:>15,.0f} FC")
                    print(f"  Savings:        {tier['savings_in_tier']:>15,.0f} FC")
        print("\n" + "=" * 60 + "\n")
    elif not args.output:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
