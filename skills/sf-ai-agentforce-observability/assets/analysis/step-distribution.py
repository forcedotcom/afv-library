#!/usr/bin/env python3
"""
Step Distribution Analysis Template

Analyzes the distribution of LLM and ACTION steps across agents and topics.
Helps identify which actions are most frequently used and potential bottlenecks.

Usage:
    python3 step-distribution.py --data-dir ./stdm_data
    python3 step-distribution.py --data-dir ./stdm_data --agent Customer_Support_Agent

Output includes:
- LLM vs ACTION step ratio
- Most common actions
- Steps per turn distribution
- Action success patterns
"""

import argparse
from pathlib import Path
from datetime import datetime

import polars as pl
from rich.console import Console
from rich.table import Table

console = Console()


def load_data(data_dir: Path) -> dict:
    """Load STDM entities as lazy frames."""
    return {
        "sessions": pl.scan_parquet(data_dir / "sessions" / "**/*.parquet"),
        "interactions": pl.scan_parquet(data_dir / "interactions" / "**/*.parquet"),
        "steps": pl.scan_parquet(data_dir / "steps" / "**/*.parquet"),
    }


def step_type_ratio(data: dict, agent_name: str = None) -> pl.DataFrame:
    """Calculate LLM vs ACTION step ratio."""
    steps = data["steps"]

    if agent_name:
        # Filter by agent
        sessions = data["sessions"]
        interactions = data["interactions"]

        session_ids = (
            sessions
            .filter(pl.col("ssot__AiAgentApiName__c") == agent_name)
            .select("ssot__Id__c")
        )

        interaction_ids = (
            interactions
            .join(session_ids, left_on="ssot__AiAgentSessionId__c", right_on="ssot__Id__c")
            .select(pl.col("ssot__Id__c").alias("interaction_id"))
        )

        steps = steps.join(
            interaction_ids,
            left_on="ssot__AiAgentInteractionId__c",
            right_on="interaction_id"
        )

    result = (
        steps
        .group_by("ssot__AiAgentInteractionStepType__c")
        .agg(pl.count().alias("count"))
        .with_columns([
            (pl.col("count") / pl.col("count").sum() * 100)
            .round(1)
            .alias("percentage")
        ])
        .sort("count", descending=True)
    )

    return result.collect()


def action_distribution(data: dict, agent_name: str = None, top_n: int = 20) -> pl.DataFrame:
    """Get most common action names."""
    steps = data["steps"]

    # Filter to ACTION_STEP only
    action_steps = steps.filter(
        pl.col("ssot__AiAgentInteractionStepType__c") == "ACTION_STEP"
    )

    if agent_name:
        sessions = data["sessions"]
        interactions = data["interactions"]

        session_ids = (
            sessions
            .filter(pl.col("ssot__AiAgentApiName__c") == agent_name)
            .select("ssot__Id__c")
        )

        interaction_ids = (
            interactions
            .join(session_ids, left_on="ssot__AiAgentSessionId__c", right_on="ssot__Id__c")
            .select(pl.col("ssot__Id__c").alias("interaction_id"))
        )

        action_steps = action_steps.join(
            interaction_ids,
            left_on="ssot__AiAgentInteractionId__c",
            right_on="interaction_id"
        )

    result = (
        action_steps
        .group_by("ssot__Name__c")
        .agg(pl.count().alias("count"))
        .sort("count", descending=True)
        .head(top_n)
    )

    return result.collect()


def steps_per_turn(data: dict) -> pl.DataFrame:
    """Calculate steps per turn distribution."""
    result = (
        data["steps"]
        .group_by("ssot__AiAgentInteractionId__c")
        .agg(pl.count().alias("step_count"))
        .group_by("step_count")
        .agg(pl.count().alias("turn_count"))
        .sort("step_count")
    )

    return result.collect()


def print_analysis(data_dir: Path, agent_name: str = None):
    """Print step distribution analysis."""
    console.print("\n[bold cyan]⚡ STEP DISTRIBUTION ANALYSIS[/bold cyan]")
    console.print(f"Data: {data_dir}")
    if agent_name:
        console.print(f"Agent: {agent_name}")
    console.print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    console.print("═" * 60)

    data = load_data(data_dir)

    # Step Type Ratio
    console.print("\n[bold]Step Type Ratio[/bold]")
    ratio = step_type_ratio(data, agent_name)

    for row in ratio.iter_rows(named=True):
        step_type = row.get("ssot__AiAgentInteractionStepType__c", "Unknown")
        count = row.get("count", 0)
        pct = row.get("percentage", 0)

        icon = "🧠" if step_type == "LLM_STEP" else "⚡"
        console.print(f"  {icon} {step_type}: {count:,} ({pct}%)")

    # Action Distribution
    console.print("\n[bold]Top Actions[/bold]")
    actions = action_distribution(data, agent_name)

    table = Table()
    table.add_column("#", justify="right", style="dim")
    table.add_column("Action Name", style="cyan")
    table.add_column("Count", justify="right")

    for i, row in enumerate(actions.iter_rows(named=True), 1):
        action = row.get("ssot__Name__c", "Unknown")
        count = row.get("count", 0)
        table.add_row(str(i), str(action), f"{count:,}")

    console.print(table)

    # Steps per Turn
    console.print("\n[bold]Steps per Turn Distribution[/bold]")
    spt = steps_per_turn(data)

    for row in spt.head(10).iter_rows(named=True):
        step_count = row.get("step_count", 0)
        turn_count = row.get("turn_count", 0)
        bar = "█" * min(turn_count // 10, 40)
        console.print(f"  {step_count:>2} steps: {turn_count:>6,} turns {bar}")


def main():
    parser = argparse.ArgumentParser(description="Analyze step distribution")
    parser.add_argument("--data-dir", required=True, type=Path, help="STDM data directory")
    parser.add_argument("--agent", type=str, help="Filter by agent API name")
    parser.add_argument("--output", type=Path, help="Output directory for CSV export")

    args = parser.parse_args()

    if not args.data_dir.exists():
        console.print(f"[red]Error: Data directory not found: {args.data_dir}[/red]")
        return 1

    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
        data = load_data(args.data_dir)

        ratio = step_type_ratio(data, args.agent)
        ratio.write_csv(args.output / "step_type_ratio.csv")

        actions = action_distribution(data, args.agent)
        actions.write_csv(args.output / "action_distribution.csv")

        console.print(f"[green]✓ Reports exported to {args.output}[/green]")
    else:
        print_analysis(args.data_dir, args.agent)

    return 0


if __name__ == "__main__":
    exit(main())
