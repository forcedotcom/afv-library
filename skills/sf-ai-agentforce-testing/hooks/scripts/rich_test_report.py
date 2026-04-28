#!/usr/bin/env python3
"""
Unified Multi-Worker Test Report Aggregator

Merges N worker result JSON files into one Rich terminal report.
Run this after all swarm workers complete to see a single combined view.

Usage:
    python3 rich_test_report.py --results worker-1-results.json worker-2-results.json
    python3 rich_test_report.py --results /tmp/sf-test-*/worker-*-results.json

Output:
    1. Header Panel — agent name, worker count, total scenarios, duration
    2. Per-Worker Summary Table — pass/fail per worker with colored rows
    3. Failed Scenarios Tree — grouped by worker → scenario → failed turn
    4. Aggregate Summary Panel — combined pass/fail/checks totals

Author: Jag Valaiyapathy
License: MIT
"""

import argparse
import glob
import json
import os
import shutil
import sys

try:
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.tree import Tree
    from rich.text import Text
    from rich import box
except ImportError:
    print(
        "ERROR: rich library is required for this script.\n"
        "Install with: pip3 install rich",
        file=sys.stderr,
    )
    sys.exit(2)


def _detect_width(override: int = None) -> int:
    """Detect terminal width (tmux-aware).
    Priority: explicit override > $COLUMNS > shutil > 80.
    Clamped to [60, 300].
    """
    if override and override > 0:
        return max(60, min(override, 300))
    env_cols = os.environ.get("COLUMNS")
    if env_cols:
        try:
            return max(60, min(int(env_cols), 300))
        except ValueError:
            pass
    try:
        cols = shutil.get_terminal_size().columns
        if cols > 0:
            return max(60, min(cols, 300))
    except Exception:
        pass
    return 80


def load_results(file_paths):
    """Load and parse JSON result files from worker outputs."""
    results = []
    for fp in file_paths:
        try:
            with open(fp) as f:
                results.append(json.load(f))
        except (json.JSONDecodeError, OSError) as e:
            print(f"WARNING: Failed to load {fp}: {e}", file=sys.stderr)
    return results


def _count_checks(scenarios):
    """Count total and passed checks across all scenarios."""
    cp = ct = 0
    for sc in scenarios:
        for t in sc.get("turns", []):
            ev = t.get("evaluation", {})
            ct += ev.get("total_checks", 0)
            cp += ev.get("pass_count", 0)
    return cp, ct


def render_unified(results_list, console):
    """Render a unified Rich report from multiple worker result sets."""

    # ── 1. Header Panel ──────────────────────────────────────────────
    total_scenarios = sum(r["summary"]["total_scenarios"] for r in results_list)
    total_duration = sum(r.get("total_elapsed_ms", 0) for r in results_list) / 1000
    agent_id = results_list[0].get("agent_id", "Unknown")
    console.print(Panel(
        f"Agent: {agent_id}  |  Workers: {len(results_list)}  |  "
        f"Scenarios: {total_scenarios}  |  Duration: {total_duration:.1f}s",
        title="[bold]🧪 Unified Test Report[/bold]",
        border_style="bright_blue",
        box=box.DOUBLE,
    ))

    # ── 2. Per-Worker Summary Table ──────────────────────────────────
    table = Table(
        title="Worker Results",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold",
        expand=True,
    )
    table.add_column("Worker", style="bold", ratio=2, no_wrap=True)
    table.add_column("Scenarios", justify="center", ratio=2, no_wrap=True)
    table.add_column("Turns", justify="center", ratio=2, no_wrap=True)
    table.add_column("Checks", justify="center", ratio=2, no_wrap=True)
    table.add_column("Duration", justify="right", ratio=2, no_wrap=True)

    all_passed_global = True
    for i, r in enumerate(results_list, 1):
        s = r["summary"]
        sp, st = s["passed_scenarios"], s["total_scenarios"]
        tp, tt = s["passed_turns"], s["total_turns"]
        cp, ct = _count_checks(r.get("scenarios", []))
        el = r.get("total_elapsed_ms", 0) / 1000
        style = "green" if sp == st else "red"
        all_passed_global = all_passed_global and (sp == st)
        table.add_row(
            f"W{i}",
            f"[{style}]{sp}/{st}[/]",
            f"{tp}/{tt}",
            f"{cp}/{ct}",
            f"{el:.1f}s",
        )

    console.print(table)

    # ── 3. Failed Scenarios Tree ─────────────────────────────────────
    has_failures = False
    fail_tree = Tree("❌ [bold red]Failed Scenarios[/bold red]")

    for i, r in enumerate(results_list, 1):
        worker_has_failure = False
        worker_branch = None

        for sc in r.get("scenarios", []):
            if sc.get("status") != "passed":
                if not worker_has_failure:
                    worker_branch = fail_tree.add(f"[bold]Worker W{i}[/bold]")
                    worker_has_failure = True
                    has_failures = True

                sc_name = sc.get("name", "unnamed")
                sc_status = sc.get("status", "error")
                sc_icon = "❌" if sc_status == "failed" else "💥"
                sc_branch = worker_branch.add(f"{sc_icon} {sc_name}")

                for t in sc.get("turns", []):
                    ev = t.get("evaluation", {})
                    if not ev.get("passed", True):
                        turn_num = t.get("turn_number", "?")
                        user_msg = t.get("user_message", "")[:60]
                        turn_branch = sc_branch.add(
                            f"[dim]Turn {turn_num}:[/dim] \"{user_msg}\""
                        )

                        for c in ev.get("checks", []):
                            if not c["passed"]:
                                detail = c.get("detail", "")
                                detail_str = f" — {detail}" if detail else ""
                                turn_branch.add(
                                    f"[red]{c['name']}{detail_str}[/red]"
                                )

    if has_failures:
        console.print()
        console.print(fail_tree)

    # ── 4. Aggregate Summary Panel ───────────────────────────────────
    agg_sp = sum(r["summary"]["passed_scenarios"] for r in results_list)
    agg_st = sum(r["summary"]["total_scenarios"] for r in results_list)
    agg_tp = sum(r["summary"]["passed_turns"] for r in results_list)
    agg_tt = sum(r["summary"]["total_turns"] for r in results_list)
    agg_cp = agg_ct = 0
    for r in results_list:
        cp, ct = _count_checks(r.get("scenarios", []))
        agg_cp += cp
        agg_ct += ct

    agg_table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold", expand=True)
    agg_table.add_column("Metric", style="bold", ratio=2)
    agg_table.add_column("Result", justify="right", ratio=3)
    agg_table.add_column("Metric", style="bold", ratio=2)
    agg_table.add_column("Result", justify="right", ratio=3)

    s_style = "green" if agg_sp == agg_st else "red"
    t_style = "green" if agg_tp == agg_tt else "red"
    c_style = "green" if agg_cp == agg_ct else "red"

    agg_table.add_row(
        "Scenarios", f"[{s_style}]{agg_sp}/{agg_st} ✅[/]",
        "Turns", f"[{t_style}]{agg_tp}/{agg_tt} ✅[/]",
    )
    agg_table.add_row(
        "Checks", f"[{c_style}]{agg_cp}/{agg_ct} ✅[/]",
        "Duration", f"{total_duration:.1f}s",
    )

    verdict_style = "bold green" if all_passed_global else "bold red"
    verdict_text = "🏆 ALL SCENARIOS PASSED" if all_passed_global else "❌ SOME SCENARIOS FAILED"
    verdict = Text(verdict_text, style=verdict_style)

    border = "green" if all_passed_global else "red"
    panel = Panel(
        Group(agg_table, Text(""), verdict),
        title="📊 Aggregate Summary",
        border_style=border,
        box=box.DOUBLE,
    )
    console.print(panel)


def main():
    parser = argparse.ArgumentParser(
        description="Unified multi-worker test report aggregator using Rich",
    )
    parser.add_argument(
        "--results", nargs="+", required=True,
        help="Worker result JSON files (supports shell globs)",
    )
    parser.add_argument(
        "--width", type=int, default=None,
        help="Terminal width (auto-detected from $COLUMNS or terminal; fallback: 80)",
    )
    args = parser.parse_args()

    # Expand globs (shell may not expand them in all contexts)
    files = []
    for pattern in args.results:
        expanded = sorted(glob.glob(pattern))
        if expanded:
            files.extend(expanded)
        else:
            files.append(pattern)  # pass through for error reporting

    if not files:
        print("ERROR: No result files found", file=sys.stderr)
        sys.exit(2)

    results_list = load_results(files)
    if not results_list:
        print("ERROR: No valid result files loaded", file=sys.stderr)
        sys.exit(2)

    console = Console(force_terminal=True, width=_detect_width(args.width))
    render_unified(results_list, console)

    # Exit code: 0 if all passed, 1 if any failures
    all_passed = all(
        r["summary"].get("failed_scenarios", 0) == 0
        and r["summary"].get("error_scenarios", 0) == 0
        for r in results_list
    )
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
