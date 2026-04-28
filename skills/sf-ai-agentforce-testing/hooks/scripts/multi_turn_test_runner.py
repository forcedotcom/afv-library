#!/usr/bin/env python3
"""
Multi-Turn Agent Test Runner

Executes multi-turn test scenarios against Agentforce agents via the Agent Runtime API.
Reads YAML scenario templates, manages sessions, evaluates per-turn expectations,
and produces structured JSON results for the agentic fix loop.

Usage:
    # Basic usage with scenario file:
    python3 multi_turn_test_runner.py \
        --my-domain your-domain.my.salesforce.com \
        --consumer-key YOUR_KEY \
        --consumer-secret YOUR_SECRET \
        --agent-id 0XxRM0000004ABC \
        --scenarios assets/multi-turn-comprehensive.yaml

    # With context variables:
    python3 multi_turn_test_runner.py \
        --my-domain your-domain.my.salesforce.com \
        --consumer-key YOUR_KEY \
        --consumer-secret YOUR_SECRET \
        --agent-id 0XxRM0000004ABC \
        --scenarios assets/multi-turn-topic-routing.yaml \
        --var '$Context.AccountId=001XXXXXXXXXXXX' \
        --var '$Context.EndUserLanguage=en_US'

    # With JSON output for fix loop:
    python3 multi_turn_test_runner.py \
        --agent-id 0XxRM0000004ABC \
        --scenarios assets/multi-turn-comprehensive.yaml \
        --output results.json \
        --verbose

    # From environment variables (no args needed for credentials):
    export SF_MY_DOMAIN=your-domain.my.salesforce.com
    export SF_CONSUMER_KEY=YOUR_KEY
    export SF_CONSUMER_SECRET=YOUR_SECRET
    export SF_AGENT_ID=0XxRM0000004ABC
    python3 multi_turn_test_runner.py --scenarios assets/multi-turn-comprehensive.yaml

Exit Codes:
    0 = All scenarios passed
    1 = Some scenarios failed (fix loop should process results)
    2 = Execution error (auth failure, connection error, etc.)

Dependencies:
    - pyyaml (pip3 install pyyaml) — for YAML template parsing
    - agent_api_client.py (sibling module) — Agent Runtime API client

Author: Jag Valaiyapathy
License: MIT
"""

import argparse
import concurrent.futures
import json
import os
import re
import shutil
import sys
import textwrap
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import sibling module
sys.path.insert(0, str(Path(__file__).parent))
from agent_api_client import (
    AgentAPIClient, AgentSession, TurnResult, AgentAPIError, parse_variables,
)

# YAML import with helpful error
try:
    import yaml
except ImportError:
    print(
        "ERROR: pyyaml is required for YAML template parsing.\n"
        "Install with: pip3 install pyyaml",
        file=sys.stderr,
    )
    sys.exit(2)

# Rich library (optional — graceful fallback to legacy Unicode formatting)
try:
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.rule import Rule
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


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


# ═══════════════════════════════════════════════════════════════════════════
# Streaming Console (Rich-powered verbose output to stderr)
# ═══════════════════════════════════════════════════════════════════════════

class StreamingConsole:
    """Rich-powered streaming output to stderr during test execution.

    Provides styled, thread-safe progress output while scenarios run.
    Falls back to plain print() when Rich is unavailable or --no-rich is set.
    """

    def __init__(self, enabled: bool = True, width: int = None, use_rich: bool = True, codeblock: bool = False):
        self._enabled = enabled
        self._lock = threading.Lock()
        self._codeblock = codeblock and enabled
        self._width = _detect_width(width)
        if self._codeblock:
            # Codeblock mode: plain text + emojis to stdout, no ANSI.
            # Line-buffering ensures each print() flushes immediately so
            # output streams line-by-line in Claude Code's Bash tool.
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(line_buffering=True)
            self._console = None
            self._rich = False
        elif enabled and HAS_RICH and use_rich:
            # Write to stdout (not stderr) so ANSI codes render in real-time
            # in CLI tools like Claude Code that only interpret ANSI on stdout
            # during streaming. Line-buffer ensures each print() flushes immediately.
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(line_buffering=True)
            self._console = Console(
                stderr=False, force_terminal=True,
                width=_detect_width(width), highlight=False,
            )
            self._rich = True
        else:
            self._console = None
            self._rich = False

    # ── Run-level ──────────────────────────────────────────────────────

    def run_header(self, total: int, file: str, mode: str):
        """Print a header at the start of the entire test run."""
        if not self._enabled:
            return
        with self._lock:
            if self._codeblock:
                W = self._width
                print("━" * W, flush=True)
                print(f"  🧪 Agentforce Multi-Turn Test", flush=True)
                print(f"  Running {total} scenario{'s' if total != 1 else ''} [{mode}]", flush=True)
                print(f"  File: {file}", flush=True)
                print("━" * W, flush=True)
            elif self._rich:
                self._console.rule(
                    f"[bold]Running {total} scenario{'s' if total != 1 else ''} [{mode}][/bold]",
                    style="bright_blue",
                )
                self._console.print(f"  [dim]File: {file}[/dim]")
            else:
                print(f"\nRunning {total} scenario(s) from {file} [{mode}]...", file=sys.stderr)

    def auth_success(self):
        """Print authentication success indicator."""
        if not self._enabled:
            return
        with self._lock:
            if self._codeblock:
                print("  ✅ Authenticated", flush=True)
            elif self._rich:
                self._console.print("  [bold green]✅ Authenticated[/bold green]")
            else:
                print("✅ Authentication successful", file=sys.stderr)

    # ── Scenario-level ────────────────────────────────────────────────

    def scenario_start(self, name: str, idx: int, total: int, variables: list = None,
                        description: str = None):
        """Print scenario separator with name and progress counter."""
        if not self._enabled:
            return
        with self._lock:
            if self._codeblock:
                W = self._width
                label = f" Scenario {idx}/{total}: {name} "
                pad = W - len(label)
                left = pad // 2
                right = pad - left
                print(flush=True)
                print(flush=True)
                print(f"{'─' * left}{label}{'─' * right}", flush=True)
                if description:
                    print(f"  {description}", flush=True)
                print(flush=True)
            elif self._rich:
                self._console.print()
                self._console.print()
                self._console.rule(
                    f"[bold]Scenario {idx}/{total}: {name}[/bold]",
                    style="cyan",
                )
                if variables:
                    var_names = ", ".join(v["name"] for v in variables)
                    self._console.print(f"  [dim]Variables: {var_names}[/dim]")
            else:
                print(f"\n\n  ▶ Scenario: {name}", file=sys.stderr)
                if variables:
                    print(f"    Variables: {[v['name'] for v in variables]}", file=sys.stderr)

    # ── Turn-level ────────────────────────────────────────────────────

    def turn_start(self, num: int, total: int, message: str):
        """Print the user message being sent for this turn."""
        if not self._enabled:
            return
        with self._lock:
            if self._codeblock:
                W = self._width
                prefix = f"  Turn {num}/{total}  👤 "
                user_display = message.replace("\n", " ")
                avail = W - len(prefix) - 2  # 2 for quotes
                if len(user_display) > avail:
                    user_display = user_display[:avail - 3] + "..."
                print(f"{prefix}\"{user_display}\"", flush=True)
            else:
                truncated = message[:50] + "..." if len(message) > 50 else message
                if self._rich:
                    self._console.print(
                        f"\n  Turn {num}/{total}  "
                        f"[bright_green]👤 \"{truncated}\"[/bright_green]"
                    )
                else:
                    print(f"    Turn {num}: \"{truncated}\"", file=sys.stderr)

    def agent_response(self, turn_result):
        """Print the agent's response with metadata badges.

        Text wraps across multiple lines with consistent indentation so
        continuation lines align under the opening quote character.
        """
        if not self._enabled:
            return

        text = turn_result.agent_text
        elapsed_s = turn_result.elapsed_ms / 1000
        types = turn_result.message_types
        is_failure = "Failure" in types

        with self._lock:
            if self._codeblock:
                indent = "            "      # 12 spaces
                cont   = "                "  # 16 spaces (align under opening quote)
                if is_failure:
                    print(f"{indent}⚠️  [Failure] (no response)  ({elapsed_s:.1f}s)", flush=True)
                else:
                    display = text.replace("\n", " ")
                    badges = ""
                    if turn_result.has_escalation:
                        badges += "  ↗ escalation"
                    if turn_result.has_action_result:
                        badges += "  ⚡ action"
                    suffix = f"  ({elapsed_s:.1f}s){badges}"
                    wrap_width = max(self._width - len(cont) - 1, 30)
                    wrapped = textwrap.wrap(display, width=wrap_width) or [""]
                    if len(wrapped) == 1:
                        print(f"{indent}🤖 \"{wrapped[0]}\"{suffix}", flush=True)
                    else:
                        print(f"{indent}🤖 \"{wrapped[0]}", flush=True)
                        for mid in wrapped[1:-1]:
                            print(f"{cont}{mid}", flush=True)
                        print(f"{cont}{wrapped[-1]}\"{suffix}", flush=True)
                return  # early return for codeblock — skip Rich/plain branches

            if self._rich:
                if is_failure:
                    self._console.print(
                        f"            [bold yellow]⚠️  \\[Failure] (no response)[/bold yellow]"
                        f"  [dim]({elapsed_s:.1f}s)[/dim]"
                    )
                else:
                    # Escape Rich markup brackets in agent text
                    display = text.replace("\n", " ").replace("[", "\\[")
                    # Build suffix badges
                    badges = ""
                    if turn_result.has_escalation:
                        badges += "  [yellow]↗ escalation[/yellow]"
                    if turn_result.has_action_result:
                        badges += "  [cyan]⚡ action[/cyan]"
                    suffix = f"  [dim]({elapsed_s:.1f}s)[/dim]{badges}"
                    # Word-wrap: 12-space indent + 🤖(2 cols) + space + " = 16 cols
                    indent = "            "      # 12 spaces
                    cont   = "                "  # 16 spaces (align under opening quote)
                    avail = max((self._console.width or 80) - 16 - 1, 30)
                    lines = textwrap.wrap(display, width=avail) or [""]

                    if len(lines) == 1:
                        self._console.print(
                            f"{indent}[bright_magenta]🤖 \"{lines[0]}\"[/bright_magenta]{suffix}"
                        )
                    else:
                        self._console.print(
                            f"{indent}[bright_magenta]🤖 \"{lines[0]}[/bright_magenta]"
                        )
                        for mid_line in lines[1:-1]:
                            self._console.print(
                                f"[bright_magenta]{cont}{mid_line}[/bright_magenta]"
                            )
                        self._console.print(
                            f"[bright_magenta]{cont}{lines[-1]}\"[/bright_magenta]{suffix}"
                        )
            else:
                if is_failure:
                    print(f"      ⚠️  [Failure] (no response)  ({elapsed_s:.1f}s)", file=sys.stderr)
                else:
                    display = text.replace("\n", " ")
                    badges = ""
                    if turn_result.has_escalation:
                        badges += "  ↗ escalation"
                    if turn_result.has_action_result:
                        badges += "  ⚡ action"
                    suffix = f"  ({elapsed_s:.1f}s){badges}"
                    # Word-wrap: 6-space indent + 🤖(2) + space + " = 10 cols
                    indent = "      "      # 6 spaces
                    cont   = "          "  # 10 spaces (align under opening quote)
                    avail = max(_detect_width() - 10 - 1, 30)
                    lines = textwrap.wrap(display, width=avail) or [""]

                    if len(lines) == 1:
                        print(f"{indent}🤖 \"{lines[0]}\"{suffix}", file=sys.stderr)
                    else:
                        print(f"{indent}🤖 \"{lines[0]}", file=sys.stderr)
                        for mid_line in lines[1:-1]:
                            print(f"{cont}{mid_line}", file=sys.stderr)
                        print(f"{cont}{lines[-1]}\"{suffix}", file=sys.stderr)

    def turn_result(self, evaluation: dict):
        """Print check results for a completed turn."""
        if not self._enabled:
            return
        checks = evaluation.get("checks", [])
        pass_count = evaluation.get("pass_count", 0)
        total_checks = evaluation.get("total_checks", 0)
        all_passed = evaluation.get("passed", False)

        with self._lock:
            if self._codeblock:
                indent = "            "  # 12 spaces
                if all_passed:
                    print(f"{indent}✅ {pass_count}/{total_checks} checks passed", flush=True)
                else:
                    failed = [c for c in checks if not c["passed"]]
                    for fc in failed:
                        detail = fc.get("detail", "")
                        print(f"{indent}❌ {fc['name']} — {detail}", flush=True)
                    print(f"{indent}{pass_count}/{total_checks} checks passed", flush=True)
                return

            if self._rich:
                if all_passed:
                    self._console.print(
                        f"    [green]✅ {pass_count}/{total_checks} checks passed[/green]"
                    )
                else:
                    failed = [c for c in checks if not c["passed"]]
                    for fc in failed:
                        detail = fc.get("detail", "")
                        self._console.print(
                            f"    [red]❌ {fc['name']}[/red] [dim]— {detail}[/dim]"
                        )
                    self._console.print(
                        f"    [dim]{pass_count}/{total_checks} checks passed[/dim]"
                    )
            else:
                if all_passed:
                    print(f"      ✅ {pass_count}/{total_checks} checks passed", file=sys.stderr)
                else:
                    failed = [c for c in checks if not c["passed"]]
                    for fc in failed:
                        print(f"      ❌ {fc['name']}: {fc['detail']}", file=sys.stderr)

    def turn_retry(self, attempt: int, max_retries: int, reason: str):
        """Print a retry indicator for a failed turn attempt."""
        if not self._enabled:
            return
        with self._lock:
            if self._codeblock:
                print(f"            ⟳ Retry {attempt}/{max_retries}: {reason}", flush=True)
            elif self._rich:
                self._console.print(
                    f"    [dim yellow]⟳ Retry {attempt}/{max_retries}: {reason}[/dim yellow]"
                )
            else:
                print(f"      ⟳ Retry {attempt}/{max_retries}: {reason}", file=sys.stderr)

    # ── Error-level ───────────────────────────────────────────────────

    def scenario_error(self, error_type: str, message: str):
        """Print an error that terminated a scenario."""
        if not self._enabled:
            return
        with self._lock:
            if self._codeblock:
                print(f"    ❌ {error_type}: {message}", flush=True)
            elif self._rich:
                self._console.print(
                    f"    [bold red]❌ {error_type}:[/bold red] [red]{message}[/red]"
                )
            else:
                print(f"    ❌ {error_type}: {message}", file=sys.stderr)

    # ── Utility ───────────────────────────────────────────────────────

    def api_log(self, msg: str):
        """Print a dim API debug log line. Suppressed in codeblock mode."""
        if not self._enabled or self._codeblock:
            return
        with self._lock:
            if self._rich:
                self._console.print(f"  [dim]api: {msg}[/dim]")
            else:
                print(f"  [api] {msg}", file=sys.stderr)

    def file_written(self, label: str, path: str):
        """Print a dim file-written indicator."""
        if not self._enabled:
            return
        with self._lock:
            if self._codeblock:
                print(f"  📄 {label}: {path}", flush=True)
            elif self._rich:
                self._console.print(f"  [dim]📄 {label}: {path}[/dim]")
            else:
                print(f"\n📄 {label}: {path}", file=sys.stderr)

    def scenario_end(self, scenario_result: dict):
        """Print per-scenario result line after all turns complete."""
        if not self._enabled:
            return
        status = scenario_result.get("status", "error")
        pass_t = scenario_result.get("pass_count", 0)
        total_t = scenario_result.get("total_turns", 0)
        elapsed_s = scenario_result.get("elapsed_ms", 0) / 1000

        with self._lock:
            if self._codeblock:
                icon = {"passed": "✅", "failed": "❌", "error": "💥"}.get(status, "⚠️")
                print(flush=True)
                print(f"  Result: {icon} {status.upper()} — {pass_t}/{total_t} turns passed │ {elapsed_s:.1f}s", flush=True)
            elif self._rich:
                if status == "passed":
                    self._console.print(
                        f"\n  [bold green]✅ PASSED[/] — {pass_t}/{total_t} turns │ {elapsed_s:.1f}s"
                    )
                elif status == "failed":
                    self._console.print(
                        f"\n  [bold red]❌ FAILED[/] — {pass_t}/{total_t} turns │ {elapsed_s:.1f}s"
                    )
                else:
                    self._console.print(
                        f"\n  [bold yellow]💥 ERROR[/] — {pass_t}/{total_t} turns │ {elapsed_s:.1f}s"
                    )
            else:
                icon = {"passed": "✅", "failed": "❌", "error": "💥"}.get(status, "⚠️")
                print(f"\n  {icon} {status.upper()} — {pass_t}/{total_t} turns │ {elapsed_s:.1f}s", file=sys.stderr)

    def run_summary(self, results: dict):
        """Print the final run summary block."""
        if not self._enabled:
            return
        summary = results.get("summary", {})
        sp = summary.get("passed_scenarios", 0)
        st = summary.get("total_scenarios", 0)
        tp = summary.get("passed_turns", 0)
        tt = summary.get("total_turns", 0)
        dur = results.get("total_elapsed_ms", 0) / 1000

        # Count checks across all scenarios
        cp = ct = 0
        for s in results.get("scenarios", []):
            for t in s.get("turns", []):
                ev = t.get("evaluation", {})
                ct += ev.get("total_checks", 0)
                cp += ev.get("pass_count", 0)

        all_passed = summary.get("failed_scenarios", 0) == 0 and summary.get("error_scenarios", 0) == 0

        with self._lock:
            if self._codeblock:
                W = self._width
                print(flush=True)
                print(flush=True)
                print("📊 SUMMARY", flush=True)
                print("═" * W, flush=True)
                print(f"  Scenarios    {sp}/{st} ✅     Turns       {tp}/{tt} ✅", flush=True)
                print(f"  Checks       {cp}/{ct} ✅    Duration    {dur:.1f}s", flush=True)
                print(flush=True)
                if all_passed:
                    print("  ✅ ALL SCENARIOS PASSED", flush=True)
                else:
                    print("  ❌ SOME SCENARIOS FAILED", flush=True)
                print("═" * W, flush=True)
            elif self._rich:
                self._console.print()
                if all_passed:
                    self._console.print(
                        f"  [bold green]📊 SUMMARY — {sp}/{st} scenarios ✅ │ "
                        f"{tp}/{tt} turns │ {cp}/{ct} checks │ {dur:.1f}s[/]"
                    )
                    self._console.print("  [bold green]🏆 ALL SCENARIOS PASSED[/]")
                else:
                    self._console.print(
                        f"  [bold red]📊 SUMMARY — {sp}/{st} scenarios │ "
                        f"{tp}/{tt} turns │ {cp}/{ct} checks │ {dur:.1f}s[/]"
                    )
                    self._console.print("  [bold red]❌ SOME SCENARIOS FAILED[/]")
            else:
                print(f"\n📊 SUMMARY — {sp}/{st} scenarios │ {tp}/{tt} turns │ {cp}/{ct} checks │ {dur:.1f}s", file=sys.stderr)
                if all_passed:
                    print("🏆 ALL SCENARIOS PASSED", file=sys.stderr)
                else:
                    print("❌ SOME SCENARIOS FAILED", file=sys.stderr)


# ═══════════════════════════════════════════════════════════════════════════
# Turn Evaluation
# ═══════════════════════════════════════════════════════════════════════════

# Patterns that indicate a guardrail was triggered (agent declined the request)
GUARDRAIL_PATTERNS = [
    # Hard refusals
    r"(?i)i\s*(?:can(?:'t|not)|am\s+(?:not\s+)?(?:able|allowed))\s+(?:to\s+)?(?:help|assist|provide|share|do\s+that)",
    r"(?i)(?:sorry|apologies?)[\s,]+(?:but\s+)?i\s+(?:can(?:'t|not))",
    r"(?i)(?:not\s+)?(?:able|allowed|permitted)\s+to\s+(?:provide|share|disclose|give)",
    r"(?i)(?:against|violates?)\s+(?:my|our|the)\s+(?:policy|policies|guidelines|rules)",
    r"(?i)(?:sensitive|confidential|private)\s+(?:information|data)",
    r"(?i)i\s+(?:must|need\s+to)\s+(?:decline|refuse|respectfully)",
    # Soft redirects (agent scope-limits without explicit refusal)
    r"(?i)i(?:'m|\s+am)\s+(?:here|designed|built)\s+to\s+(?:help|assist)\s+with",
    r"(?i)(?:that'?s?|this\s+is)\s+(?:outside|beyond)\s+(?:my|the)\s+(?:scope|area)",
    r"(?i)(?:my|our)\s+(?:specialty|focus|expertise)\s+is",
]

# Patterns that suggest escalation (agent handing off to human)
ESCALATION_PATTERNS = [
    r"(?i)(?:connect|transfer|escalat)\w*\s+(?:you\s+)?(?:to|with)\s+(?:a\s+)?(?:human|agent|specialist|representative|someone|person|team)",
    r"(?i)(?:let\s+me\s+)?(?:get|find)\s+(?:you\s+)?(?:a\s+)?(?:human|real\s+person|specialist|agent)",
    r"(?i)(?:hand|pass)\w*\s+(?:you\s+)?(?:off|over)\s+to",
    # Soft escalation (acknowledging inability + offering human help)
    r"(?i)(?:please\s+)?hold\s+(?:on|while)\s+(?:I|we)\s+(?:connect|transfer)",
    r"(?i)(?:I'?d?\s+like\s+to|let\s+me)\s+(?:connect|get)\s+you\s+(?:with|to)",
    r"(?i)(?:at\s+this\s+time|currently).*(?:unable|cannot)\s+to\s+transfer",
]


def evaluate_turn(
    turn: TurnResult,
    expectations: Dict[str, Any],
    prior_turns: List[TurnResult],
) -> Dict[str, Any]:
    """
    Evaluate a single turn's response against its expectations.

    Args:
        turn: The TurnResult to evaluate.
        expectations: Dict of expectation checks (from YAML).
        prior_turns: All turns that came before this one (for context checks).

    Returns:
        Dict with 'passed', 'failed', 'checks' (list of individual check results).
    """
    checks = []

    for check_name, expected_value in expectations.items():
        result = _run_check(check_name, expected_value, turn, prior_turns)
        checks.append(result)

    passed = [c for c in checks if c["passed"]]
    failed = [c for c in checks if not c["passed"]]

    return {
        "passed": len(failed) == 0,
        "pass_count": len(passed),
        "fail_count": len(failed),
        "total_checks": len(checks),
        "checks": checks,
    }


def _run_check(
    name: str, expected: Any, turn: TurnResult, prior_turns: List[TurnResult]
) -> Dict[str, Any]:
    """Run a single expectation check against a turn."""
    check = {
        "name": name,
        "expected": expected,
        "passed": False,
        "actual": None,
        "detail": "",
    }

    text = turn.agent_text.lower()

    try:
        if name == "response_not_empty":
            check["actual"] = turn.has_response
            check["passed"] = turn.has_response == expected
            check["detail"] = f"Response {'has' if turn.has_response else 'has no'} content"

        elif name == "response_contains":
            if isinstance(expected, bool):
                check["passed"] = False
                check["detail"] = (
                    "response_contains expects a string, got bool. "
                    "Use response_not_empty for boolean checks."
                )
            else:
                val = str(expected).lower()
                found = val in text
                check["actual"] = found
                check["passed"] = found
                check["detail"] = f"'{expected}' {'found' if found else 'not found'} in response"

        elif name == "response_contains_any":
            found_any = any(v.lower() in text for v in expected)
            found_which = [v for v in expected if v.lower() in text]
            check["actual"] = found_which
            check["passed"] = found_any
            check["detail"] = f"Found: {found_which}" if found_any else f"None of {expected} found"

        elif name == "response_not_contains":
            val = expected.lower()
            found = val in text
            check["actual"] = not found
            check["passed"] = not found
            check["detail"] = f"'{expected}' {'absent (good)' if not found else 'found (bad)'}"

        elif name == "topic_contains":
            # Heuristic: infer topic from response language (API doesn't return topic name)
            # Use word-boundary matching to avoid false positives on substrings
            val = expected.lower()
            found = bool(re.search(rf"\b{re.escape(val)}\b", text))
            check["actual"] = found
            check["passed"] = found
            check["detail"] = (
                f"Topic keyword '{expected}' {'inferred' if found else 'not found'} in response"
                " (heuristic — word-boundary match)"
            )

        elif name == "escalation_triggered":
            has_esc = turn.has_escalation or _matches_patterns(turn.agent_text, ESCALATION_PATTERNS)
            check["actual"] = has_esc
            check["passed"] = has_esc == expected
            check["detail"] = (
                f"Escalation {'detected' if has_esc else 'not detected'}"
                f" (types: {turn.message_types})"
            )

        elif name == "guardrail_triggered":
            is_declined = _matches_patterns(turn.agent_text, GUARDRAIL_PATTERNS)
            check["actual"] = is_declined
            check["passed"] = is_declined == expected
            check["detail"] = (
                f"Guardrail {'triggered' if is_declined else 'not triggered'}"
            )

        elif name == "action_invoked":
            has_action = turn.has_action_result
            if isinstance(expected, bool):
                # For Agent Script agents, action results are embedded in
                # Inform text — has_action_result is always False.  Fall back
                # to checking planner_surfaces on each message.
                if not has_action:
                    has_action = any(
                        bool(getattr(m, "planner_surfaces", None))
                        for m in turn.agent_messages
                    )
                check["actual"] = has_action
                check["passed"] = has_action == expected
                check["detail"] = (
                    f"Action result {'present' if has_action else 'absent'}"
                    f" (expected: {expected})"
                )
            else:
                # String: check action was invoked AND the action name matches
                action_name = str(expected)
                raw_json = json.dumps(turn.raw_response)
                name_found = action_name.lower() in raw_json.lower()
                # Fallback for Agent Script: search planner_surfaces
                if not has_action:
                    has_action = any(
                        bool(getattr(m, "planner_surfaces", None))
                        for m in turn.agent_messages
                    )
                    if has_action and not name_found:
                        # Check planner_surfaces for the action name
                        for m in turn.agent_messages:
                            for ps in getattr(m, "planner_surfaces", []):
                                if action_name.lower() in json.dumps(ps).lower():
                                    name_found = True
                                    break
                check["actual"] = has_action and name_found
                check["passed"] = has_action and name_found
                if not has_action:
                    check["detail"] = (
                        f"No action result (expected action '{action_name}'). "
                        f"Note: Agent Script agents may not expose action results "
                        f"via API — use response_contains instead."
                    )
                elif not name_found:
                    check["detail"] = f"Action invoked but '{action_name}' not found in response"
                else:
                    check["detail"] = f"Action '{action_name}' invoked successfully"

        elif name == "has_action_result":
            check["actual"] = turn.has_action_result
            check["passed"] = turn.has_action_result == expected

        elif name == "turn_elapsed_max":
            elapsed = turn.elapsed_ms
            check["actual"] = elapsed
            check["passed"] = elapsed <= expected
            check["detail"] = (
                f"Turn took {elapsed:.0f}ms (max: {expected}ms)"
                if elapsed <= expected
                else f"Turn took {elapsed:.0f}ms — EXCEEDED max {expected}ms"
            )

        elif name == "response_acknowledges_change":
            # Heuristic: look for acknowledgment phrases
            ack_patterns = [
                r"(?i)(?:instead|sure|of\s+course|no\s+problem|let\s+me|I'?ll)",
                r"(?i)(?:change|switch|update|rather|reschedule)",
            ]
            acknowledged = _matches_patterns(turn.agent_text, ack_patterns)
            check["actual"] = acknowledged
            check["passed"] = acknowledged
            check["detail"] = "Response acknowledges intent change" if acknowledged else "No acknowledgment detected"

        elif name == "response_offers_help":
            help_patterns = [
                r"(?i)(?:help|assist|can\s+I|would\s+you\s+like|let\s+me|try|here)",
            ]
            offers_help = _matches_patterns(turn.agent_text, help_patterns)
            check["actual"] = offers_help
            check["passed"] = offers_help
            check["detail"] = "Help offered" if offers_help else "No help offered"

        elif name == "response_offers_alternative":
            alt_patterns = [
                r"(?i)(?:alternatively|another\s+option|you\s+(?:could|can)\s+also|try|instead|otherwise|how\s+about)",
            ]
            has_alt = _matches_patterns(turn.agent_text, alt_patterns)
            check["actual"] = has_alt
            check["passed"] = has_alt
            check["detail"] = "Alternative offered" if has_alt else "No alternative detected"

        elif name == "response_acknowledges_error":
            err_patterns = [
                r"(?i)(?:sorry|apologize|error|issue|problem|unfortunately|went\s+wrong)",
                r"(?i)(?:could\s+not|couldn'?t|cannot|unable\s+to)\s+(?:find|locate|retrieve|process)",
                r"(?i)(?:no\s+(?:results?|records?|matches?|order)|not\s+found|doesn'?t\s+exist)",
            ]
            acknowledged = _matches_patterns(turn.agent_text, err_patterns)
            check["actual"] = acknowledged
            check["passed"] = acknowledged
            check["detail"] = "Error acknowledged" if acknowledged else "No error acknowledgment"

        elif name == "resumes_normal":
            # Check that the response is non-empty and doesn't contain guardrail language
            is_normal = turn.has_response and not _matches_patterns(turn.agent_text, GUARDRAIL_PATTERNS)
            check["actual"] = is_normal
            check["passed"] = is_normal
            check["detail"] = "Normal conversation resumed" if is_normal else "Did not resume normally"

        elif name == "no_re_ask_for":
            # Check that the agent doesn't re-ask for information already provided
            re_ask_patterns = [
                rf"(?i)(?:what|which|could\s+you\s+(?:please\s+)?(?:provide|give|tell)).*{re.escape(expected.lower())}",
                rf"(?i)(?:can\s+you|please)\s+(?:provide|share|give|tell).*{re.escape(expected.lower())}",
            ]
            re_asked = _matches_patterns(turn.agent_text, re_ask_patterns)
            check["actual"] = not re_asked
            check["passed"] = not re_asked
            check["detail"] = (
                f"Agent did NOT re-ask for '{expected}' (good)"
                if not re_asked
                else f"Agent RE-ASKED for '{expected}' (bad)"
            )

        elif name == "response_references":
            val = str(expected).lower()
            found = val in text
            check["actual"] = found
            check["passed"] = found
            check["detail"] = f"Reference to '{expected}' {'found' if found else 'not found'}"

        elif name == "response_references_both":
            found_all = all(str(v).lower() in text for v in expected)
            missing = [str(v) for v in expected if str(v).lower() not in text]
            check["actual"] = found_all
            check["passed"] = found_all
            check["detail"] = f"All references found" if found_all else f"Missing: {missing}"

        elif name == "context_retained":
            # Soft check: the response is non-empty and doesn't indicate confusion
            confusion_patterns = [
                r"(?i)I\s+don'?t\s+have\s+(?:that|this)\s+information",
                r"(?i)(?:could|can)\s+you\s+(?:please\s+)?(?:remind|tell)\s+me\s+again",
                r"(?i)I'?m\s+not\s+(?:sure|aware)\s+(?:what|which)",
            ]
            no_confusion = turn.has_response and not _matches_patterns(turn.agent_text, confusion_patterns)
            check["actual"] = no_confusion
            check["passed"] = no_confusion
            check["detail"] = "Context appears retained" if no_confusion else "Context may be lost"

        elif name == "context_uses":
            val = str(expected).lower()
            found = val in text
            check["actual"] = found
            check["passed"] = found
            check["detail"] = f"Context '{expected}' {'used' if found else 'not used'} in response"

        elif name == "action_uses_variable":
            # Heuristic: extract keyword from variable name and check agent didn't re-ask
            keyword = _extract_variable_keyword(str(expected))
            if keyword:
                re_ask_patterns = [
                    rf"(?i)(?:what|which|could\s+you\s+(?:please\s+)?(?:provide|give|tell)).*{re.escape(keyword)}",
                    rf"(?i)(?:can\s+you|please)\s+(?:provide|share|give|tell).*{re.escape(keyword)}",
                ]
                re_asked = _matches_patterns(turn.agent_text, re_ask_patterns)
                check["actual"] = not re_asked
                check["passed"] = not re_asked
                check["detail"] = (
                    f"Variable {expected} appears used (agent did not re-ask for '{keyword}')"
                    if not re_asked
                    else f"Agent re-asked for '{keyword}' — variable {expected} may not be used"
                )
            else:
                check["actual"] = "cannot_verify"
                check["passed"] = True  # Soft pass if we can't extract a keyword
                check["detail"] = f"Variable {expected} usage cannot be verified from response alone (check STDM)"

        elif name == "action_uses_prior_output":
            # Heuristic: check that agent doesn't re-ask for data from prior action
            if prior_turns:
                re_ask = _matches_patterns(turn.agent_text, [
                    r"(?i)which\s+(?:account|record|order|contact|case)",
                    r"(?i)(?:could|can)\s+you\s+(?:provide|specify|tell\s+me)",
                ])
                check["actual"] = not re_ask
                check["passed"] = not re_ask
                check["detail"] = (
                    "Agent used prior action output (no re-ask)"
                    if not re_ask
                    else "Agent may have re-asked for prior action data"
                )
            else:
                check["actual"] = True
                check["passed"] = True
                check["detail"] = "First turn — no prior output to check"

        elif name == "conversation_resolved":
            # Heuristic: response indicates resolution
            resolve_patterns = [
                r"(?i)(?:anything\s+else|is\s+there\s+anything|glad\s+I\s+could|happy\s+to\s+help)",
                r"(?i)(?:done|complete|resolved|taken\s+care\s+of|all\s+set)",
            ]
            resolved = _matches_patterns(turn.agent_text, resolve_patterns)
            check["actual"] = resolved
            check["passed"] = resolved
            check["detail"] = "Conversation appears resolved" if resolved else "Resolution not detected"

        elif name == "response_declines_gracefully":
            decline_patterns = [
                r"(?i)(?:I'?m\s+)?(?:not\s+(?:able|equipped)|(?:can(?:'t|not))\s+(?:help|assist|provide))",
                r"(?i)(?:outside|beyond)\s+(?:my|the)\s+(?:scope|area|capabilities)",
                r"(?i)(?:focus|specialize)\s+(?:on|in)\s+(?:other|different)",
            ]
            declined = _matches_patterns(turn.agent_text, decline_patterns) or \
                       _matches_patterns(turn.agent_text, GUARDRAIL_PATTERNS)
            check["actual"] = declined
            check["passed"] = declined
            check["detail"] = "Gracefully declined" if declined else "Did not decline"

        elif name == "response_matches_regex":
            try:
                match = re.search(expected, turn.agent_text)
                check["actual"] = bool(match)
                check["passed"] = bool(match)
                check["detail"] = (
                    f"Regex '{expected}' matched" if match
                    else f"Regex '{expected}' did not match"
                )
            except re.error as regex_err:
                check["passed"] = False
                check["detail"] = f"Invalid regex '{expected}': {regex_err}"

        elif name == "response_length_min":
            actual_len = len(turn.agent_text.strip())
            check["actual"] = actual_len
            check["passed"] = actual_len >= expected
            check["detail"] = (
                f"Response length {actual_len} >= {expected} (min)"
                if actual_len >= expected
                else f"Response length {actual_len} < {expected} (min)"
            )

        elif name == "response_length_max":
            actual_len = len(turn.agent_text.strip())
            check["actual"] = actual_len
            check["passed"] = actual_len <= expected
            check["detail"] = (
                f"Response length {actual_len} <= {expected} (max)"
                if actual_len <= expected
                else f"Response length {actual_len} > {expected} (max)"
            )

        elif name == "action_result_contains":
            results = turn.action_results
            results_str = json.dumps(results) if results else ""
            found = str(expected).lower() in results_str.lower()
            check["actual"] = found
            check["passed"] = found
            if not results:
                check["detail"] = f"No action results to search for '{expected}'"
                check["passed"] = False
            elif found:
                check["detail"] = f"'{expected}' found in action results"
            else:
                check["detail"] = f"'{expected}' not found in action results"

        else:
            check["detail"] = f"Unknown check '{name}' — skipped"
            check["passed"] = True  # Don't fail on unknown checks

    except Exception as e:
        check["detail"] = f"Check error: {e}"
        check["passed"] = False

    return check


def _matches_patterns(text: str, patterns: List[str]) -> bool:
    """Check if text matches any of the given regex patterns."""
    return any(re.search(p, text) for p in patterns)


def _extract_variable_keyword(variable_name: str) -> Optional[str]:
    """
    Extract a human-readable keyword from a variable name for re-ask detection.

    Examples:
        "$Context.AccountId" → "account"
        "$Context.EndUserLanguage" → "language"
        "CaseId" → "case"
        "Verified_Check" → "verified"
    """
    # Strip $Context. prefix
    name = variable_name.replace("$Context.", "").replace("$", "")
    # Split on camelCase or underscores
    parts = re.split(r'(?<=[a-z])(?=[A-Z])|_', name)
    # Filter out common suffixes like 'Id', 'Key', 'Name'
    keywords = [p.lower() for p in parts if p.lower() not in ("id", "key", "name", "type", "value")]
    return keywords[0] if keywords else None


# ═══════════════════════════════════════════════════════════════════════════
# Scenario Execution
# ═══════════════════════════════════════════════════════════════════════════

def load_scenarios(path: str) -> Dict[str, Any]:
    """Load YAML scenario file."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


def execute_scenario(
    client: AgentAPIClient,
    agent_id: str,
    scenario: Dict[str, Any],
    global_variables: List[Dict] = None,
    verbose: bool = False,
    turn_retry: int = 0,
    stream: StreamingConsole = None,
) -> Dict[str, Any]:
    """
    Execute a single multi-turn test scenario.

    Args:
        client: Authenticated AgentAPIClient.
        agent_id: BotDefinition ID.
        scenario: Scenario dict from YAML template.
        global_variables: CLI-level variables to merge with scenario variables.
        verbose: Print progress to stderr (legacy; prefer stream).
        turn_retry: Number of retries per turn on transient failures (default 0).
        stream: StreamingConsole for Rich-styled verbose output.

    Returns:
        Scenario result dict with turn results and evaluation.
    """
    name = scenario.get("name", "unnamed")
    description = scenario.get("description", "")
    turns_spec = scenario.get("turns", [])
    scenario_vars = scenario.get("session_variables", [])

    # Run index/total injected by main() for progress display
    run_idx = scenario.get("_run_index", 0)
    run_total = scenario.get("_run_total", 0)

    # Merge variables: scenario-specific + global CLI variables
    all_variables = list(scenario_vars)
    if global_variables:
        # Global vars override scenario vars with same name
        global_names = {v["name"] for v in global_variables}
        all_variables = [v for v in all_variables if v["name"] not in global_names]
        all_variables.extend(global_variables)

    if stream:
        stream.scenario_start(name, run_idx, run_total, all_variables if all_variables else None,
                              description=description)
    elif verbose:
        print(f"\n  ▶ Scenario: {name}", file=sys.stderr)
        if all_variables:
            print(f"    Variables: {[v['name'] for v in all_variables]}", file=sys.stderr)

    result = {
        "name": name,
        "description": description,
        "status": "error",
        "turns": [],
        "pass_count": 0,
        "fail_count": 0,
        "total_turns": len(turns_spec),
        "elapsed_ms": 0,
        "error": None,
    }

    start_time = time.time()
    prior_turn_results: List[TurnResult] = []

    try:
        with client.session(
            agent_id=agent_id,
            variables=all_variables if all_variables else None,
        ) as session:
            for i, turn_spec in enumerate(turns_spec, 1):
                user_message = turn_spec.get("user", "")
                expectations = turn_spec.get("expect", {})
                turn_variables = turn_spec.get("variables", None)

                if stream:
                    stream.turn_start(i, len(turns_spec), user_message)
                elif verbose:
                    print(f"    Turn {i}: \"{user_message[:50]}{'...' if len(user_message) > 50 else ''}\"", file=sys.stderr)

                # Send message with optional per-turn retry
                turn_result = None
                for attempt in range(turn_retry + 1):
                    try:
                        turn_result = session.send(user_message, variables=turn_variables)
                        if not turn_result.is_error:
                            break
                    except Exception as send_err:
                        if attempt < turn_retry:
                            if stream:
                                stream.turn_retry(attempt + 1, turn_retry, str(send_err))
                            elif verbose:
                                print(f"      ⟳ Retry {attempt + 1}/{turn_retry}: {send_err}", file=sys.stderr)
                            time.sleep(1 * (attempt + 1))
                        else:
                            raise
                    if attempt < turn_retry and turn_result and turn_result.is_error:
                        if stream:
                            stream.turn_retry(attempt + 1, turn_retry, "turn error")
                        elif verbose:
                            print(f"      ⟳ Retry {attempt + 1}/{turn_retry}: turn error", file=sys.stderr)
                        time.sleep(1 * (attempt + 1))

                # Show agent response in streaming output
                if stream and turn_result:
                    stream.agent_response(turn_result)

                # Evaluate against expectations
                evaluation = evaluate_turn(turn_result, expectations, prior_turn_results)

                turn_data = {
                    "turn_number": i,
                    "user_message": user_message,
                    "agent_text": turn_result.agent_text,
                    "message_types": turn_result.message_types,
                    "elapsed_ms": round(turn_result.elapsed_ms, 1),
                    "has_response": turn_result.has_response,
                    "has_escalation": turn_result.has_escalation,
                    "has_action_result": turn_result.has_action_result,
                    "error": turn_result.error,
                    "evaluation": evaluation,
                }

                result["turns"].append(turn_data)

                if stream:
                    stream.turn_result(evaluation)
                    if evaluation["passed"]:
                        result["pass_count"] += 1
                    else:
                        result["fail_count"] += 1
                elif evaluation["passed"]:
                    result["pass_count"] += 1
                    if verbose:
                        print(f"      ✅ {evaluation['pass_count']}/{evaluation['total_checks']} checks passed", file=sys.stderr)
                else:
                    result["fail_count"] += 1
                    if verbose:
                        failed_checks = [c for c in evaluation["checks"] if not c["passed"]]
                        for fc in failed_checks:
                            print(f"      ❌ {fc['name']}: {fc['detail']}", file=sys.stderr)

                prior_turn_results.append(turn_result)

    except AgentAPIError as e:
        result["error"] = str(e)
        result["status"] = "error"
        result["elapsed_ms"] = round((time.time() - start_time) * 1000, 1)
        if stream:
            stream.scenario_error("API Error", str(e))
            stream.scenario_end(result)
        elif verbose:
            print(f"    ❌ API Error: {e}", file=sys.stderr)
        return result
    except Exception as e:
        result["error"] = f"Unexpected error: {type(e).__name__}: {e}"
        result["status"] = "error"
        result["elapsed_ms"] = round((time.time() - start_time) * 1000, 1)
        if stream:
            stream.scenario_error("Unexpected Error", f"{type(e).__name__}: {e}")
            stream.scenario_end(result)
        elif verbose:
            print(f"    ❌ Unexpected Error: {type(e).__name__}: {e}", file=sys.stderr)
        return result

    result["elapsed_ms"] = round((time.time() - start_time) * 1000, 1)

    if result["fail_count"] == 0 and result["error"] is None:
        result["status"] = "passed"
    elif result["fail_count"] > 0:
        result["status"] = "failed"

    if stream:
        stream.scenario_end(result)

    return result


# ═══════════════════════════════════════════════════════════════════════════
# Rich Output Formatting (Colored — requires `rich` library)
# ═══════════════════════════════════════════════════════════════════════════

def _make_console(width: int = None) -> "Console":
    """Create a Rich Console with recording + forced terminal color.
    If width is None, auto-detects from environment (tmux-aware).
    """
    return Console(record=True, force_terminal=True, width=_detect_width(width))


def _format_session_banner_rich(console, agent_id, scenario_file, worker_id=None, partition_label=None):
    """Render a colored session banner using Rich Panel."""
    lines = [f"Agent: {agent_id}  |  File: {scenario_file}"]
    if worker_id is not None:
        label = f" ({partition_label})" if partition_label else ""
        lines.append(f"Worker: W{worker_id}{label}")
    content = "\n".join(lines)
    console.print(Panel(content, title="[bold]🧪 Agentforce Multi-Turn Test[/bold]",
                        border_style="bright_blue", box=box.DOUBLE))


def _format_turn_panel(console, turn_data, turn_idx, total_turns):
    """Render a single turn as a Rich Panel with colored content and pass/fail border."""
    checks = turn_data.get("evaluation", {}).get("checks", [])
    pass_count = sum(1 for c in checks if c["passed"])
    all_passed = pass_count == len(checks)

    # Build content lines
    parts = []
    user_msg = turn_data.get("user_message", "").replace("\n", " ")
    agent_text = turn_data.get("agent_text", "").replace("\n", " ")
    agent_display = agent_text[:90] + "..." if len(agent_text) > 90 else agent_text

    parts.append(Text.assemble(("👤 User:  ", "bold"), (f'"{user_msg[:80]}"', "bright_green")))
    parts.append(Text.assemble(("🤖 Agent: ", "bold"), (f'"{agent_display}"', "bright_magenta")))

    # Metadata line (timing, topic, action)
    elapsed_s = turn_data.get("elapsed_ms", 0) / 1000
    meta_parts = [f"⏱ {elapsed_s:.1f}s"]
    for c in checks:
        if c["name"] == "topic_contains":
            meta_parts.append(f"📋 {c.get('expected', '?')}")
        if c["name"] == "action_invoked" and c.get("expected"):
            meta_parts.append(f"🔧 {c['expected']}")
    parts.append(Text(" | ".join(meta_parts), style="dim"))
    parts.append(Text(""))  # spacer

    # Check results
    for c in checks:
        if c["passed"]:
            parts.append(Text(f"  ✅ {c['name']}", style="green"))
        else:
            detail = f" — {c['detail']}" if c.get("detail") else ""
            parts.append(Text(f"  ❌ {c['name']}{detail}", style="red"))

    border = "green" if all_passed else "red"
    subtitle = f"{pass_count}/{len(checks)} passed"
    panel = Panel(
        Group(*parts),
        title=f"Turn {turn_idx}/{total_turns}",
        subtitle=subtitle,
        border_style=border,
        box=box.ROUNDED,
        padding=(0, 1),
    )
    console.print(panel)


def _format_scenario_result_rich(console, scenario_result):
    """Render a colored one-liner pass/fail summary for a completed scenario."""
    status = scenario_result.get("status", "error")
    turns = f"{scenario_result.get('pass_count', 0)}/{scenario_result.get('total_turns', 0)}"
    elapsed = scenario_result.get("elapsed_ms", 0) / 1000

    # Count checks
    cp = ct = 0
    for t in scenario_result.get("turns", []):
        ev = t.get("evaluation", {})
        ct += ev.get("total_checks", 0)
        cp += ev.get("pass_count", 0)

    if status == "passed":
        console.print(f"  [bold green]✅ PASSED[/] | {turns} turns | {cp}/{ct} checks | {elapsed:.1f}s")
    elif status == "failed":
        console.print(f"  [bold red]❌ FAILED[/] | {turns} turns | {cp}/{ct} checks | {elapsed:.1f}s")
    else:
        console.print(f"  [bold yellow]💥 ERROR[/] | {turns} turns | {cp}/{ct} checks | {elapsed:.1f}s")


def _format_summary_panel(console, results):
    """Render the final summary as a Rich Table inside a colored Panel."""
    summary = results.get("summary", {})
    all_passed = summary.get("failed_scenarios", 0) == 0 and summary.get("error_scenarios", 0) == 0

    # Metrics table
    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold", expand=True)
    table.add_column("Metric", style="bold", ratio=2)
    table.add_column("Result", justify="right", ratio=3)
    table.add_column("Metric", style="bold", ratio=2)
    table.add_column("Result", justify="right", ratio=3)

    sp = summary.get("passed_scenarios", 0)
    st = summary.get("total_scenarios", 0)
    tp = summary.get("passed_turns", 0)
    tt = summary.get("total_turns", 0)
    elapsed = results.get("total_elapsed_ms", 0) / 1000

    # Count checks across all scenarios
    cp = ct = 0
    for s in results.get("scenarios", []):
        for t in s.get("turns", []):
            ev = t.get("evaluation", {})
            ct += ev.get("total_checks", 0)
            cp += ev.get("pass_count", 0)

    s_style = "green" if sp == st else "red"
    t_style = "green" if tp == tt else "red"
    c_style = "green" if cp == ct else "red"

    table.add_row("Scenarios", f"[{s_style}]{sp}/{st} ✅[/]", "Turns", f"[{t_style}]{tp}/{tt} ✅[/]")
    table.add_row("Checks", f"[{c_style}]{cp}/{ct} ✅[/]", "Duration", f"{elapsed:.1f}s")

    verdict_style = "bold green" if all_passed else "bold red"
    verdict_text = "🏆 ALL SCENARIOS PASSED" if all_passed else "❌ SOME SCENARIOS FAILED"
    verdict = Text(verdict_text, style=verdict_style)

    border = "green" if all_passed else "red"
    panel = Panel(Group(table, Text(""), verdict), title="📊 Summary",
                  border_style=border, box=box.DOUBLE)
    console.print(panel)


def format_results_rich(results: Dict[str, Any], worker_id: int = None, scenario_file: str = None, width: int = None) -> str:
    """Orchestrate all Rich-powered sections into a complete colored report."""
    console = _make_console(width=width)

    # Session banner
    agent_id = results.get("agent_id", "Unknown")
    sf = scenario_file or results.get("scenario_file", "Unknown")
    partition_label = None
    if worker_id is not None:
        st = results.get("summary", {}).get("total_scenarios", 0)
        partition_label = f"{st} scenario(s)"
    _format_session_banner_rich(console, agent_id, sf, worker_id, partition_label)

    # Scenarios
    scenarios = results.get("scenarios", [])
    for idx, scenario in enumerate(scenarios, 1):
        priority = scenario.get("priority")
        name = scenario.get("name", "unnamed")
        pri = f" [dim]({priority})[/dim]" if priority else ""
        console.rule(f"[bold]Scenario {idx}/{len(scenarios)}: {name}{pri}[/bold]", style="cyan")

        for t in scenario.get("turns", []):
            _format_turn_panel(console, t, t.get("turn_number", 0), scenario.get("total_turns", 0))

        _format_scenario_result_rich(console, scenario)

    # Summary
    _format_summary_panel(console, results)

    return console.export_text(styles=True)


# ═══════════════════════════════════════════════════════════════════════════
# Results Formatting
# ═══════════════════════════════════════════════════════════════════════════

def format_results(results: Dict[str, Any]) -> str:
    """Format test results as terminal-friendly report."""
    lines = []
    scenarios = results.get("scenarios", [])
    summary = results.get("summary", {})

    lines.append("")
    lines.append("📊 MULTI-TURN TEST RESULTS")
    lines.append("=" * 64)
    lines.append("")
    lines.append(f"Agent ID:    {results.get('agent_id', 'Unknown')}")
    lines.append(f"Scenarios:   {results.get('scenario_file', 'Unknown')}")
    lines.append(f"Timestamp:   {results.get('timestamp', '')}")
    lines.append(f"Duration:    {results.get('total_elapsed_ms', 0):.0f}ms")
    lines.append("")

    # Scenario summary
    lines.append("SCENARIO RESULTS")
    lines.append("-" * 64)

    for s in scenarios:
        status_icon = {"passed": "✅", "failed": "❌", "error": "💥"}.get(s["status"], "⚠️")
        turn_info = f"{s['pass_count']}/{s['total_turns']} turns passed"
        lines.append(f"{status_icon} {s['name']:<40} {turn_info}")

        # Show failed turns inline
        if s["status"] == "failed":
            for t in s["turns"]:
                if not t["evaluation"]["passed"]:
                    failed_checks = [c for c in t["evaluation"]["checks"] if not c["passed"]]
                    for fc in failed_checks:
                        lines.append(f"   └─ Turn {t['turn_number']}: {fc['name']} — {fc['detail']}")

        if s["status"] == "error":
            lines.append(f"   └─ Error: {s.get('error', 'Unknown')}")

    lines.append("")

    # Aggregate summary
    lines.append("SUMMARY")
    lines.append("-" * 64)
    lines.append(f"Scenarios:        {summary.get('total_scenarios', 0)} total | "
                 f"{summary.get('passed_scenarios', 0)} passed | "
                 f"{summary.get('failed_scenarios', 0)} failed | "
                 f"{summary.get('error_scenarios', 0)} errors")
    lines.append(f"Turns:            {summary.get('total_turns', 0)} total | "
                 f"{summary.get('passed_turns', 0)} passed | "
                 f"{summary.get('failed_turns', 0)} failed")

    total_turns = summary.get("total_turns", 0)
    if total_turns > 0:
        pass_rate = (summary.get("passed_turns", 0) / total_turns) * 100
        lines.append(f"Turn Pass Rate:   {pass_rate:.1f}%")
    lines.append("")

    # Failed turns detail
    failed_turns = []
    for s in scenarios:
        for t in s.get("turns", []):
            if not t["evaluation"]["passed"]:
                failed_turns.append((s["name"], t))

    if failed_turns:
        lines.append("FAILED TURNS — DETAIL")
        lines.append("-" * 64)

        for scenario_name, t in failed_turns:
            failed_checks = [c for c in t["evaluation"]["checks"] if not c["passed"]]
            lines.append(f"")
            lines.append(f"❌ {scenario_name} → Turn {t['turn_number']}")
            lines.append(f"   Input:    \"{t['user_message'][:70]}\"")
            if t.get("agent_text"):
                lines.append(f"   Response: \"{t['agent_text'][:70]}{'...' if len(t.get('agent_text', '')) > 70 else ''}\"")
            for fc in failed_checks:
                lines.append(f"   Check:    {fc['name']}")
                lines.append(f"   Expected: {fc['expected']}")
                lines.append(f"   Actual:   {fc['actual']}")
                lines.append(f"   Detail:   {fc['detail']}")
                # Suggest failure category
                category = _infer_failure_category(fc["name"], t)
                if category:
                    lines.append(f"   Category: {category}")

        lines.append("")

    # Machine-readable section for fix loop
    if summary.get("failed_scenarios", 0) > 0 or summary.get("error_scenarios", 0) > 0:
        lines.append("=" * 64)
        lines.append("AGENTIC FIX INSTRUCTIONS")
        lines.append("=" * 64)
        lines.append("")
        lines.append("To automatically fix these failures, invoke sf-ai-agentscript:")
        lines.append("")

        categories_seen = set()
        for scenario_name, t in failed_turns:
            for fc in t["evaluation"]["checks"]:
                if not fc["passed"]:
                    cat = _infer_failure_category(fc["name"], t)
                    if cat and cat not in categories_seen:
                        categories_seen.add(cat)
                        fix = _suggest_fix(cat)
                        lines.append(f"  {cat}:")
                        lines.append(f"    → {fix}")
                        lines.append("")

    lines.append("=" * 64)
    lines.append("")

    return "\n".join(lines)


def _infer_failure_category(check_name: str, turn: Dict) -> Optional[str]:
    """Infer failure category from check name and turn data."""
    mapping = {
        "topic_contains": "TOPIC_RE_MATCHING_FAILURE",
        "response_contains": "CONTEXT_PRESERVATION_FAILURE",
        "response_contains_any": "CONTEXT_PRESERVATION_FAILURE",
        "response_not_contains": "GUARDRAIL_NOT_TRIGGERED",
        "context_retained": "CONTEXT_PRESERVATION_FAILURE",
        "context_uses": "CONTEXT_PRESERVATION_FAILURE",
        "no_re_ask_for": "CONTEXT_PRESERVATION_FAILURE",
        "response_references": "CONTEXT_PRESERVATION_FAILURE",
        "response_references_both": "CONTEXT_PRESERVATION_FAILURE",
        "escalation_triggered": "MULTI_TURN_ESCALATION_FAILURE",
        "guardrail_triggered": "GUARDRAIL_NOT_TRIGGERED",
        "action_invoked": "ACTION_NOT_INVOKED",
        "has_action_result": "ACTION_NOT_INVOKED",
        "action_uses_prior_output": "ACTION_CHAIN_FAILURE",
        "action_uses_variable": "ACTION_CHAIN_FAILURE",
        "response_not_empty": "RESPONSE_QUALITY_ISSUE",
        "response_acknowledges_change": "RESPONSE_QUALITY_ISSUE",
        "response_offers_help": "RESPONSE_QUALITY_ISSUE",
        "response_offers_alternative": "RESPONSE_QUALITY_ISSUE",
        "response_acknowledges_error": "RESPONSE_QUALITY_ISSUE",
        "conversation_resolved": "RESPONSE_QUALITY_ISSUE",
        "response_declines_gracefully": "GUARDRAIL_NOT_TRIGGERED",
        "resumes_normal": "GUARDRAIL_RECOVERY_FAILURE",
        "turn_elapsed_max": "RESPONSE_QUALITY_ISSUE",
        "response_matches_regex": "CONTEXT_PRESERVATION_FAILURE",
        "response_length_min": "RESPONSE_QUALITY_ISSUE",
        "response_length_max": "RESPONSE_QUALITY_ISSUE",
        "action_result_contains": "ACTION_CHAIN_FAILURE",
    }
    return mapping.get(check_name)


def _suggest_fix(category: str) -> str:
    """Suggest fix strategy for a failure category."""
    fixes = {
        "TOPIC_RE_MATCHING_FAILURE": "Add transition phrases to target topic classificationDescription",
        "CONTEXT_PRESERVATION_FAILURE": "Add 'use context from prior messages' to topic instructions",
        "MULTI_TURN_ESCALATION_FAILURE": "Add frustration detection keywords to escalation triggers",
        "GUARDRAIL_NOT_TRIGGERED": "Add explicit guardrail statements to system instructions",
        "ACTION_NOT_INVOKED": "Improve action description and trigger conditions",
        "ACTION_CHAIN_FAILURE": "Verify action output variable mappings between actions",
        "RESPONSE_QUALITY_ISSUE": "Review agent instructions for completeness",
        "GUARDRAIL_RECOVERY_FAILURE": "Ensure guardrail response doesn't terminate session state",
    }
    return fixes.get(category, "Review agent configuration for this failure type")


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Multi-Turn Agent Test Runner — execute YAML test scenarios via Agent Runtime API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run comprehensive tests:
  python3 multi_turn_test_runner.py \\
      --scenarios assets/multi-turn-comprehensive.yaml

  # With context variables:
  python3 multi_turn_test_runner.py \\
      --scenarios assets/multi-turn-topic-routing.yaml \\
      --var '$Context.AccountId=001XXXXXXXXXXXX'

  # Save JSON results:
  python3 multi_turn_test_runner.py \\
      --scenarios assets/multi-turn-comprehensive.yaml \\
      --output results.json

Environment Variables:
  SF_MY_DOMAIN         Salesforce My Domain URL
  SF_CONSUMER_KEY      ECA Consumer Key
  SF_CONSUMER_SECRET   ECA Consumer Secret
  SF_AGENT_ID          BotDefinition ID
""",
    )

    # Credentials (CLI args or env vars)
    parser.add_argument("--my-domain", default=os.environ.get("SF_MY_DOMAIN", ""),
                        help="Salesforce My Domain URL (or SF_MY_DOMAIN env)")
    parser.add_argument("--consumer-key", default=os.environ.get("SF_CONSUMER_KEY", ""),
                        help="ECA Consumer Key (or SF_CONSUMER_KEY env)")
    parser.add_argument("--consumer-secret", default=os.environ.get("SF_CONSUMER_SECRET", ""),
                        help="ECA Consumer Secret (or SF_CONSUMER_SECRET env)")
    parser.add_argument("--agent-id", default=os.environ.get("SF_AGENT_ID", ""),
                        help="BotDefinition ID (or SF_AGENT_ID env)")

    # Scenario configuration
    parser.add_argument("--scenarios", required=True,
                        help="Path to YAML scenario file")
    parser.add_argument("--scenario-filter", default=None,
                        help="Only run scenarios matching this name pattern")
    parser.add_argument("--var", action="append", default=[],
                        help="Global variable: 'name=value' or '$Context.Field=value' (repeatable)")

    # Output
    parser.add_argument("--output", default=None,
                        help="Write JSON results to this file path")
    parser.add_argument("--report-file", default=None,
                        help="Write Rich terminal report to this file (ANSI codes included)")
    parser.add_argument("--verbose", action="store_true",
                        help="Print progress to stderr")
    parser.add_argument("--json-only", action="store_true",
                        help="Only output JSON (no terminal report)")

    # Robustness
    parser.add_argument("--turn-retry", type=int, default=0,
                        help="Number of retries per turn on transient failures (default: 0)")
    parser.add_argument("--parallel", type=int, default=0,
                        help="Run scenarios in parallel with N workers (default: 0 = sequential)")
    parser.add_argument("--worker-id", type=int, default=None,
                        help="Worker identifier for swarm execution (prepends [WN] to output)")
    parser.add_argument("--no-rich", action="store_true",
                        help="Disable Rich colored output (use plain-text format instead)")
    parser.add_argument("--codeblock", action="store_true",
                        help="Stream plain-text codeblock output (no ANSI). Implies --verbose.")
    parser.add_argument("--width", type=int, default=None,
                        help="Override terminal width for Rich rendering (auto-detected by default)")

    args = parser.parse_args()

    # --codeblock implies verbose + no-rich, and suppresses json-only
    if args.codeblock:
        args.verbose = True
        args.no_rich = True
        args.json_only = False

    # Validate required args
    if not args.agent_id:
        print("ERROR: --agent-id required (or set SF_AGENT_ID env var)", file=sys.stderr)
        sys.exit(2)

    if not os.path.isfile(args.scenarios):
        print(f"ERROR: Scenario file not found: {args.scenarios}", file=sys.stderr)
        sys.exit(2)

    # Create streaming console for verbose output
    stream = StreamingConsole(
        enabled=args.verbose and not args.json_only,
        width=args.width,
        use_rich=not args.no_rich,
        codeblock=args.codeblock,
    )

    # Parse global variables
    global_variables = parse_variables(args.var) if args.var else None

    # Load scenarios
    try:
        scenario_data = load_scenarios(args.scenarios)
    except Exception as e:
        print(f"ERROR: Failed to load scenarios: {e}", file=sys.stderr)
        sys.exit(2)

    scenarios = scenario_data.get("scenarios", [])
    if not scenarios:
        print("ERROR: No scenarios found in YAML file", file=sys.stderr)
        sys.exit(2)

    # Apply filter
    if args.scenario_filter:
        pattern = args.scenario_filter.lower()
        scenarios = [s for s in scenarios if pattern in s.get("name", "").lower()]
        if not scenarios:
            print(f"ERROR: No scenarios match filter '{args.scenario_filter}'", file=sys.stderr)
            sys.exit(2)

    # Create client (route API logs through StreamingConsole)
    # When streaming is active, API logs go through the callback.
    # When --json-only, suppress API verbose entirely to keep stderr clean.
    client_verbose = args.verbose and not args.json_only
    client = AgentAPIClient(
        my_domain=args.my_domain,
        consumer_key=args.consumer_key,
        consumer_secret=args.consumer_secret,
        verbose=client_verbose,
        log_callback=stream.api_log if stream._enabled else None,
    )

    # Authenticate
    try:
        client.authenticate()
    except AgentAPIError as e:
        print(f"❌ Authentication failed: {e.message}", file=sys.stderr)
        sys.exit(2)

    # Inject run index/total into each scenario for progress display
    for idx, s in enumerate(scenarios, 1):
        s["_run_index"] = idx
        s["_run_total"] = len(scenarios)

    # Execute scenarios — print header first, then auth indicator below it
    parallel = getattr(args, 'parallel', 0)
    mode = f"parallel ({parallel} workers)" if parallel else "sequential"
    stream.run_header(len(scenarios), args.scenarios, mode)
    stream.auth_success()

    start_time = time.time()
    scenario_results = []

    def _run_one(scenario):
        return execute_scenario(
            client=client,
            agent_id=args.agent_id,
            scenario=scenario,
            global_variables=global_variables,
            verbose=args.verbose,
            turn_retry=args.turn_retry,
            stream=stream,
        )

    if parallel and parallel > 0 and len(scenarios) > 1:
        max_workers = min(parallel, len(scenarios))
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(_run_one, s): s for s in scenarios}
            for future in concurrent.futures.as_completed(futures):
                scenario_results.append(future.result())
    else:
        for scenario in scenarios:
            scenario_results.append(_run_one(scenario))

    total_elapsed = (time.time() - start_time) * 1000

    # Build aggregate results
    passed_scenarios = sum(1 for s in scenario_results if s["status"] == "passed")
    failed_scenarios = sum(1 for s in scenario_results if s["status"] == "failed")
    error_scenarios = sum(1 for s in scenario_results if s["status"] == "error")
    total_turns = sum(s["total_turns"] for s in scenario_results)
    passed_turns = sum(s["pass_count"] for s in scenario_results)
    failed_turns = sum(s["fail_count"] for s in scenario_results)

    results = {
        "agent_id": args.agent_id,
        "scenario_file": args.scenarios,
        "timestamp": datetime.now().isoformat(),
        "total_elapsed_ms": round(total_elapsed, 1),
        "summary": {
            "total_scenarios": len(scenario_results),
            "passed_scenarios": passed_scenarios,
            "failed_scenarios": failed_scenarios,
            "error_scenarios": error_scenarios,
            "total_turns": total_turns,
            "passed_turns": passed_turns,
            "failed_turns": failed_turns,
        },
        "global_variables": global_variables,
        "scenarios": scenario_results,
    }

    # Streaming summary (codeblock mode printed the report live)
    stream.run_summary(results)

    # Output — suppress post-hoc report when codeblock already streamed it
    if not args.json_only and not args.codeblock:
        if HAS_RICH and not args.no_rich:
            report = format_results_rich(results, args.worker_id, args.scenarios, width=args.width)
        else:
            report = format_results(results)
        print(report)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        stream.file_written("JSON results written to", args.output)

    if args.report_file:
        if HAS_RICH and not args.no_rich:
            report_content = format_results_rich(results, args.worker_id, args.scenarios, width=args.width)
        else:
            report_content = format_results(results)
        with open(args.report_file, "w") as f:
            f.write(report_content)
        stream.file_written("Report written to", args.report_file)

    if args.json_only:
        print(json.dumps(results, indent=2))

    # Machine-readable output for fix loop integration
    if failed_scenarios > 0 or error_scenarios > 0:
        print("---BEGIN_MACHINE_READABLE---")
        print(f"FIX_NEEDED: true")
        print(f"SCENARIOS_TOTAL: {len(scenario_results)}")
        print(f"SCENARIOS_PASSED: {passed_scenarios}")
        print(f"SCENARIOS_FAILED: {failed_scenarios}")
        print(f"SCENARIOS_ERROR: {error_scenarios}")
        print(f"TURNS_TOTAL: {total_turns}")
        print(f"TURNS_PASSED: {passed_turns}")
        print(f"TURNS_FAILED: {failed_turns}")
        if args.output:
            print(f"RESULTS_FILE: {args.output}")
        print("---END_MACHINE_READABLE---")

    # Exit code
    if error_scenarios > 0:
        sys.exit(2)
    elif failed_scenarios > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
