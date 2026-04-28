#!/usr/bin/env python3
"""
Message Timeline Analysis Template

Reconstructs conversation timelines for debugging agent behavior.
Shows all messages and steps in chronological order for a session.

Usage:
    python3 message-timeline.py --data-dir ./stdm_data --session-id "a0x..."
    python3 message-timeline.py --data-dir ./stdm_data --list-failed

Output includes:
- Chronological message flow
- Step details (LLM reasoning, action inputs/outputs)
- Topic transitions
- Timing information
"""

import argparse
import json
from pathlib import Path
from datetime import datetime

import polars as pl
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def load_data(data_dir: Path) -> dict:
    """Load all STDM entities as lazy frames."""
    return {
        "sessions": pl.scan_parquet(data_dir / "sessions" / "**/*.parquet"),
        "interactions": pl.scan_parquet(data_dir / "interactions" / "**/*.parquet"),
        "steps": pl.scan_parquet(data_dir / "steps" / "**/*.parquet"),
        "messages": pl.scan_parquet(data_dir / "messages" / "**/*.parquet"),
    }


def get_session_info(data: dict, session_id: str) -> dict:
    """Get session metadata."""
    session = (
        data["sessions"]
        .filter(pl.col("ssot__Id__c") == session_id)
        .collect()
    )

    if session.is_empty():
        return None

    row = session.row(0, named=True)
    return {
        "id": row.get("ssot__Id__c"),
        "agent": row.get("ssot__AiAgentApiName__c", "Unknown"),
        "start": row.get("ssot__StartTimestamp__c"),
        "end": row.get("ssot__EndTimestamp__c"),
        "end_type": row.get("ssot__AiAgentSessionEndType__c"),
    }


def get_timeline(data: dict, session_id: str) -> list:
    """Build chronological timeline of events."""
    # Get interactions for this session
    interactions = (
        data["interactions"]
        .filter(pl.col("ssot__AiAgentSessionId__c") == session_id)
        .collect()
    )

    interaction_ids = interactions["ssot__Id__c"].to_list()

    # Get messages
    messages = (
        data["messages"]
        .filter(pl.col("ssot__AiAgentInteractionId__c").is_in(interaction_ids))
        .collect()
    )

    # Get steps
    steps = (
        data["steps"]
        .filter(pl.col("ssot__AiAgentInteractionId__c").is_in(interaction_ids))
        .collect()
    )

    # Build timeline
    timeline = []

    # Add messages
    for row in messages.iter_rows(named=True):
        timeline.append({
            "type": "message",
            "timestamp": row.get("ssot__MessageSentTimestamp__c", ""),
            "interaction_id": row.get("ssot__AiAgentInteractionId__c"),
            "message_type": row.get("ssot__AiAgentInteractionMessageType__c"),
            "content": row.get("ssot__ContentText__c", ""),
        })

    # Add steps
    for row in steps.iter_rows(named=True):
        timeline.append({
            "type": "step",
            "timestamp": "",  # Steps don't have timestamps
            "interaction_id": row.get("ssot__AiAgentInteractionId__c"),
            "step_type": row.get("ssot__AiAgentInteractionStepType__c"),
            "name": row.get("ssot__Name__c"),
            "input": row.get("ssot__InputValueText__c"),
            "output": row.get("ssot__OutputValueText__c"),
        })

    # Add interactions (for topic info)
    for row in interactions.iter_rows(named=True):
        timeline.append({
            "type": "interaction",
            "timestamp": row.get("ssot__StartTimestamp__c", ""),
            "interaction_id": row.get("ssot__Id__c"),
            "interaction_type": row.get("ssot__AiAgentInteractionType__c"),
            "topic": row.get("ssot__TopicApiName__c"),
        })

    # Sort by timestamp (messages and interactions)
    timeline.sort(key=lambda x: x.get("timestamp") or "")

    return timeline


def print_timeline(session_info: dict, timeline: list, verbose: bool = False):
    """Print formatted timeline."""
    console.print("\n[bold cyan]🔍 SESSION TIMELINE[/bold cyan]")
    console.print("═" * 70)

    # Session header
    console.print(f"\nSession: [cyan]{session_info['id']}[/cyan]")
    console.print(f"Agent: {session_info['agent']}")
    console.print(f"Started: {session_info['start']}")
    console.print(f"Ended: {session_info['end']}")
    console.print(f"End Type: {session_info['end_type']}")

    console.print("\n" + "─" * 70)
    console.print("[bold]Timeline[/bold]")
    console.print("─" * 70)

    current_topic = None

    for event in timeline:
        if event["type"] == "interaction":
            if event.get("topic") != current_topic:
                current_topic = event.get("topic")
                console.print(f"\n[yellow]═══ Topic: {current_topic} ═══[/yellow]\n")

        elif event["type"] == "message":
            timestamp = event.get("timestamp", "")[:19] if event.get("timestamp") else ""
            msg_type = event.get("message_type", "")
            content = event.get("content", "")

            if msg_type == "INPUT":
                icon = "[green]→[/green]"
                label = "[green][INPUT][/green]"
            else:
                icon = "[blue]←[/blue]"
                label = "[blue][OUTPUT][/blue]"

            # Truncate long content
            if len(content) > 100 and not verbose:
                content = content[:97] + "..."

            console.print(f"{timestamp} {icon} {label}")
            console.print(f"   {content}\n")

        elif event["type"] == "step" and verbose:
            step_type = event.get("step_type", "")
            name = event.get("name", "")

            if step_type == "LLM_STEP":
                icon = "[magenta]🧠[/magenta]"
            else:
                icon = "[cyan]⚡[/cyan]"

            console.print(f"         {icon} [{step_type}] {name}")

            if event.get("input") and verbose:
                try:
                    input_data = json.loads(event["input"])
                    console.print(f"            Input: {json.dumps(input_data, indent=2)[:200]}")
                except:
                    console.print(f"            Input: {event['input'][:200]}")

            if event.get("output") and verbose:
                try:
                    output_data = json.loads(event["output"])
                    console.print(f"            Output: {json.dumps(output_data, indent=2)[:200]}")
                except:
                    console.print(f"            Output: {event['output'][:200]}")

            console.print()


def list_failed_sessions(data: dict, limit: int = 10) -> pl.DataFrame:
    """List sessions that failed or were escalated."""
    result = (
        data["sessions"]
        .filter(
            pl.col("ssot__AiAgentSessionEndType__c").is_in(["Escalated", "Abandoned", "Failed"])
        )
        .sort("ssot__StartTimestamp__c", descending=True)
        .head(limit)
    )

    return result.collect()


def main():
    parser = argparse.ArgumentParser(description="Analyze session message timeline")
    parser.add_argument("--data-dir", required=True, type=Path, help="STDM data directory")
    parser.add_argument("--session-id", type=str, help="Session ID to analyze")
    parser.add_argument("--list-failed", action="store_true", help="List failed/escalated sessions")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show step details")
    parser.add_argument("--output", type=Path, help="Export timeline to JSON")

    args = parser.parse_args()

    if not args.data_dir.exists():
        console.print(f"[red]Error: Data directory not found: {args.data_dir}[/red]")
        return 1

    data = load_data(args.data_dir)

    if args.list_failed:
        console.print("\n[bold]Failed/Escalated Sessions[/bold]")
        failed = list_failed_sessions(data)

        for row in failed.iter_rows(named=True):
            session_id = row.get("ssot__Id__c")
            agent = row.get("ssot__AiAgentApiName__c", "Unknown")
            end_type = row.get("ssot__AiAgentSessionEndType__c")
            start = row.get("ssot__StartTimestamp__c", "")[:19]

            icon = "🔄" if end_type == "Escalated" else "❌"
            console.print(f"  {icon} {session_id} | {agent} | {end_type} | {start}")

        console.print(f"\nTo debug a session, run:")
        console.print(f"  python3 message-timeline.py --data-dir {args.data_dir} --session-id <ID>")
        return 0

    if not args.session_id:
        console.print("[red]Error: --session-id required (or use --list-failed)[/red]")
        return 1

    session_info = get_session_info(data, args.session_id)
    if not session_info:
        console.print(f"[red]Error: Session not found: {args.session_id}[/red]")
        return 1

    timeline = get_timeline(data, args.session_id)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump({
                "session": session_info,
                "timeline": timeline
            }, f, indent=2)
        console.print(f"[green]✓ Timeline exported to {args.output}[/green]")
    else:
        print_timeline(session_info, timeline, args.verbose)

    return 0


if __name__ == "__main__":
    exit(main())
