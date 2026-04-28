#!/usr/bin/env python3
"""
Session Summary Analysis Template

Generates comprehensive session statistics from extracted STDM data.
Uses Polars lazy evaluation for memory-efficient processing.

Usage:
    python3 session-summary.py --data-dir ./stdm_data --output ./reports

Output includes:
- Sessions by agent
- End type distribution
- Daily session trends
- Average turns per session
"""

import argparse
from pathlib import Path
from datetime import datetime

import polars as pl
from rich.console import Console
from rich.table import Table

console = Console()


def load_data(data_dir: Path) -> dict:
    """Load all STDM entities as lazy frames."""
    return {
        "sessions": pl.scan_parquet(data_dir / "sessions" / "**/*.parquet"),
        "interactions": pl.scan_parquet(data_dir / "interactions" / "**/*.parquet"),
    }


def sessions_by_agent(data: dict) -> pl.DataFrame:
    """Calculate session counts and metrics by agent."""
    sessions = data["sessions"]
    interactions = data["interactions"]

    # Count turns per session
    turns = (
        interactions
        .filter(pl.col("ssot__AiAgentInteractionType__c") == "TURN")
        .group_by("ssot__AiAgentSessionId__c")
        .agg(pl.count().alias("turn_count"))
    )

    # Join with sessions and aggregate
    result = (
        sessions
        .join(
            turns,
            left_on="ssot__Id__c",
            right_on="ssot__AiAgentSessionId__c",
            how="left"
        )
        .group_by("ssot__AiAgentApiName__c")
        .agg([
            pl.count().alias("session_count"),
            pl.col("turn_count").mean().alias("avg_turns"),
            pl.col("turn_count").max().alias("max_turns"),
            pl.col("turn_count").min().alias("min_turns"),
        ])
        .sort("session_count", descending=True)
    )

    return result.collect()


def end_type_distribution(data: dict) -> pl.DataFrame:
    """Calculate session end type distribution."""
    result = (
        data["sessions"]
        .group_by("ssot__AiAgentSessionEndType__c")
        .agg(pl.count().alias("count"))
        .with_columns([
            (pl.col("count") / pl.col("count").sum() * 100)
            .round(1)
            .alias("percentage")
        ])
        .sort("count", descending=True)
    )

    return result.collect()


def daily_sessions(data: dict) -> pl.DataFrame:
    """Calculate daily session counts."""
    result = (
        data["sessions"]
        .with_columns([
            pl.col("ssot__StartTimestamp__c")
            .str.slice(0, 10)
            .alias("date")
        ])
        .group_by("date")
        .agg(pl.count().alias("session_count"))
        .sort("date")
    )

    return result.collect()


def print_summary(data_dir: Path):
    """Print comprehensive session summary."""
    console.print("\n[bold cyan]📊 SESSION SUMMARY REPORT[/bold cyan]")
    console.print(f"Data: {data_dir}")
    console.print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    console.print("═" * 60)

    data = load_data(data_dir)

    # Sessions by Agent
    console.print("\n[bold]Sessions by Agent[/bold]")
    agent_stats = sessions_by_agent(data)

    table = Table()
    table.add_column("Agent", style="cyan")
    table.add_column("Sessions", justify="right")
    table.add_column("Avg Turns", justify="right")
    table.add_column("Max Turns", justify="right")

    total_sessions = 0
    for row in agent_stats.iter_rows(named=True):
        agent = row.get("ssot__AiAgentApiName__c", "Unknown")
        sessions = row.get("session_count", 0)
        avg_turns = row.get("avg_turns", 0) or 0
        max_turns = row.get("max_turns", 0) or 0
        total_sessions += sessions

        table.add_row(
            str(agent),
            f"{sessions:,}",
            f"{avg_turns:.1f}",
            str(max_turns)
        )

    table.add_row("─" * 20, "─" * 10, "─" * 10, "─" * 10)
    table.add_row("Total", f"{total_sessions:,}", "", "", style="bold")

    console.print(table)

    # End Type Distribution
    console.print("\n[bold]End Type Distribution[/bold]")
    end_types = end_type_distribution(data)

    for row in end_types.iter_rows(named=True):
        end_type = row.get("ssot__AiAgentSessionEndType__c", "Unknown")
        count = row.get("count", 0)
        pct = row.get("percentage", 0)

        icon = "✅" if end_type == "Completed" else "🔄" if end_type == "Escalated" else "❌"
        console.print(f"  {icon} {end_type}: {count:,} ({pct}%)")

    # Daily Trend
    console.print("\n[bold]Daily Session Trend[/bold]")
    daily = daily_sessions(data)

    if len(daily) > 0:
        # Show last 7 days or all if less
        recent = daily.tail(7)
        for row in recent.iter_rows(named=True):
            date = row.get("date", "")
            count = row.get("session_count", 0)
            bar = "█" * min(count // 100, 50)  # Simple bar chart
            console.print(f"  {date}: {count:>6,} {bar}")


def export_csv(data_dir: Path, output_dir: Path):
    """Export summary data to CSV files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    data = load_data(data_dir)

    # Agent stats
    agent_stats = sessions_by_agent(data)
    agent_stats.write_csv(output_dir / "sessions_by_agent.csv")

    # End type distribution
    end_types = end_type_distribution(data)
    end_types.write_csv(output_dir / "end_type_distribution.csv")

    # Daily sessions
    daily = daily_sessions(data)
    daily.write_csv(output_dir / "daily_sessions.csv")

    console.print(f"\n[green]✓ Reports exported to {output_dir}[/green]")


def main():
    parser = argparse.ArgumentParser(description="Generate session summary statistics")
    parser.add_argument("--data-dir", required=True, type=Path, help="STDM data directory")
    parser.add_argument("--output", type=Path, help="Output directory for CSV export")
    parser.add_argument("--format", choices=["table", "csv", "json"], default="table")

    args = parser.parse_args()

    if not args.data_dir.exists():
        console.print(f"[red]Error: Data directory not found: {args.data_dir}[/red]")
        return 1

    if args.output:
        export_csv(args.data_dir, args.output)
    else:
        print_summary(args.data_dir)

    return 0


if __name__ == "__main__":
    exit(main())
