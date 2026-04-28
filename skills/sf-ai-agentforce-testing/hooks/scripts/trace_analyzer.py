#!/usr/bin/env python3
"""
trace_analyzer.py — Analyze Agentforce v1.1 trace files from sf agent preview CLI.

Ported from sf-ai-agentforce-observability to sf-ai-agentforce-testing.
Reads trace JSON from .sfdx/agents/{agent}/sessions/{sid}/traces/{planId}.json

Usage:
    python3 trace_analyzer.py --traces-dir ~/.sf/sfdx/agents/My_Agent/sessions/abc/traces/
    python3 trace_analyzer.py --traces-dir ./traces/ --output analysis.json
"""

import json
import sys
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# ═══════════════════════════════════════════════════════════════
# 13 Step Type Constants (v1.1 PlanSuccessResponse)
# ═══════════════════════════════════════════════════════════════

USER_INPUT = "UserInputStep"
SESSION_INIT = "SessionInitialStateStep"
NODE_ENTRY = "NodeEntryStateStep"
VARIABLE_UPDATE = "VariableUpdateStep"
BEFORE_REASONING = "BeforeReasoningStep"
BEFORE_REASONING_ITER = "BeforeReasoningIterationStep"
ENABLED_TOOLS = "EnabledToolsStep"
LLM_STEP = "LLMStep"
REASONING = "ReasoningStep"
FUNCTION_STEP = "FunctionStep"
TRANSITION = "TransitionStep"
AFTER_REASONING = "AfterReasoningStep"
PLANNER_RESPONSE = "PlannerResponseStep"

ALL_STEP_TYPES = [
    USER_INPUT, SESSION_INIT, NODE_ENTRY, VARIABLE_UPDATE,
    BEFORE_REASONING, BEFORE_REASONING_ITER, ENABLED_TOOLS,
    LLM_STEP, REASONING, FUNCTION_STEP, TRANSITION,
    AFTER_REASONING, PLANNER_RESPONSE,
]


class TraceAnalyzer:
    """Analyze Agentforce v1.1 trace data from CLI preview sessions."""

    def __init__(self, traces: list[dict[str, Any]]):
        """
        Initialize with a list of trace dicts (one per turn/plan).
        Each trace is a PlanSuccessResponse with a 'steps' array.
        """
        self.traces = traces
        self._all_steps: list[dict] = []
        for trace in traces:
            steps = trace.get("steps", trace.get("planSteps", []))
            self._all_steps.extend(steps)

    @classmethod
    def from_cli_traces(cls, traces_dir: Path) -> "TraceAnalyzer":
        """
        Load traces from sf agent preview CLI output directory.
        Reads all .json files from the traces directory.

        Path pattern: ~/.sf/sfdx/agents/{agent}/sessions/{sid}/traces/{planId}.json
        """
        traces_dir = Path(traces_dir).expanduser()
        if not traces_dir.exists():
            raise FileNotFoundError(f"Traces directory not found: {traces_dir}")

        trace_files = sorted(traces_dir.glob("*.json"))
        if not trace_files:
            raise FileNotFoundError(f"No trace JSON files in: {traces_dir}")

        traces = []
        for tf in trace_files:
            with open(tf) as f:
                data = json.load(f)
                # Handle both raw PlanSuccessResponse and wrapped formats
                if isinstance(data, list):
                    traces.extend(data)
                else:
                    traces.append(data)

        return cls(traces)

    # ─── Filter helpers ──────────────────────────────────────

    def _steps_of_type(self, step_type: str) -> list[dict]:
        return [s for s in self._all_steps if s.get("stepType") == step_type]

    def _steps_for_trace(self, trace: dict) -> list[dict]:
        return trace.get("steps", trace.get("planSteps", []))

    # ═══════════════════════════════════════════════════════════
    # Analysis Methods
    # ═══════════════════════════════════════════════════════════

    def conversation_timeline(self) -> list[dict]:
        """Build a turn-by-turn timeline of the conversation."""
        timeline = []
        for i, trace in enumerate(self.traces):
            steps = self._steps_for_trace(trace)
            turn = {
                "turn": i + 1,
                "user_input": None,
                "agent_response": None,
                "topic": None,
                "actions": [],
                "grounding": None,
                "safety_score": None,
                "llm_latency_ms": 0,
                "action_latency_ms": 0,
            }

            for step in steps:
                st = step.get("stepType", "")
                data = step.get("data", {})

                if st == USER_INPUT:
                    turn["user_input"] = data.get("utterance", data.get("input", ""))
                elif st == PLANNER_RESPONSE:
                    turn["agent_response"] = data.get("responseText", "")
                    turn["safety_score"] = data.get("safetyScore", {})
                elif st == TRANSITION:
                    turn["topic"] = data.get("to", "")
                elif st == FUNCTION_STEP:
                    turn["actions"].append({
                        "name": data.get("function", ""),
                        "error": data.get("error"),
                        "latency_ms": data.get("executionLatency", 0),
                    })
                    turn["action_latency_ms"] += data.get("executionLatency", 0)
                elif st == REASONING:
                    turn["grounding"] = data.get("groundingAssessment", "")
                elif st == LLM_STEP:
                    turn["llm_latency_ms"] += data.get("execution_latency", 0)

            timeline.append(turn)
        return timeline

    def grounding_report(self) -> list[dict]:
        """Extract all grounding assessments."""
        results = []
        for step in self._steps_of_type(REASONING):
            data = step.get("data", {})
            results.append({
                "assessment": data.get("groundingAssessment", "UNKNOWN"),
                "text": data.get("reasoningText", ""),
            })
        return results

    def safety_report(self) -> list[dict]:
        """Extract safety scores from planner responses."""
        results = []
        for step in self._steps_of_type(PLANNER_RESPONSE):
            data = step.get("data", {})
            score = data.get("safetyScore", {})
            results.append({
                "response_preview": (data.get("responseText", ""))[:100],
                "overall": score.get("overall", None),
                "toxicity": score.get("toxicity", None),
                "prompt_injection": score.get("prompt_injection", None),
                "pii_detection": score.get("pii_detection", None),
            })
        return results

    def variable_diff_report(self) -> list[dict]:
        """Extract all variable state changes."""
        results = []
        for step in self._steps_of_type(VARIABLE_UPDATE):
            data = step.get("data", {})
            results.append({
                "variable": data.get("variableName", ""),
                "old_value": data.get("oldValue"),
                "new_value": data.get("newValue"),
            })
        return results

    def action_report(self) -> list[dict]:
        """Extract all action executions with I/O."""
        results = []
        for step in self._steps_of_type(FUNCTION_STEP):
            data = step.get("data", {})
            results.append({
                "action": data.get("function", ""),
                "arguments": data.get("arguments", {}),
                "result": data.get("result"),
                "error": data.get("error"),
                "latency_ms": data.get("executionLatency", 0),
            })
        return results

    def routing_report(self) -> list[dict]:
        """Extract all topic transitions."""
        results = []
        for step in self._steps_of_type(TRANSITION):
            data = step.get("data", {})
            results.append({
                "from": data.get("from", ""),
                "to": data.get("to", ""),
            })
        return results

    def timing_report(self) -> dict:
        """Aggregate timing data across LLM and action steps."""
        llm_steps = self._steps_of_type(LLM_STEP)
        action_steps = self._steps_of_type(FUNCTION_STEP)

        llm_total = sum(s.get("data", {}).get("execution_latency", 0) for s in llm_steps)
        action_total = sum(s.get("data", {}).get("executionLatency", 0) for s in action_steps)
        token_in = sum(s.get("data", {}).get("input_tokens", 0) for s in llm_steps)
        token_out = sum(s.get("data", {}).get("output_tokens", 0) for s in llm_steps)

        return {
            "llm_calls": len(llm_steps),
            "llm_total_ms": llm_total,
            "llm_avg_ms": llm_total // max(len(llm_steps), 1),
            "action_calls": len(action_steps),
            "action_total_ms": action_total,
            "action_avg_ms": action_total // max(len(action_steps), 1),
            "total_latency_ms": llm_total + action_total,
            "input_tokens": token_in,
            "output_tokens": token_out,
        }

    def agentscript_suggestions(self) -> list[str]:
        """Generate Agent Script fix suggestions based on trace findings."""
        suggestions = []

        # Check for ungrounded reasoning
        for gr in self.grounding_report():
            if gr["assessment"] == "UNGROUNDED":
                suggestions.append(
                    "UNGROUNDED reasoning detected — review topic instructions for "
                    "specificity. Add explicit context in `instructions: ->` block."
                )
                break

        # Check for action failures
        for ar in self.action_report():
            if ar.get("error"):
                suggestions.append(
                    f"Action '{ar['action']}' failed with error: {ar['error']}. "
                    "Check `available when:` conditions and action target configuration."
                )

        # Check for unexpected transitions
        transitions = self.routing_report()
        if len(transitions) > 3:
            suggestions.append(
                f"Excessive topic transitions ({len(transitions)}) detected. "
                "Review topic descriptions for overlap — the planner may be "
                "oscillating between topics."
            )

        # Check safety scores
        for sr in self.safety_report():
            overall = sr.get("overall")
            if overall is not None and overall < 0.9:
                suggestions.append(
                    f"Low safety score ({overall}) detected. "
                    "Review response guidelines and guardrail configuration."
                )

        # Check for slow actions
        for ar in self.action_report():
            if ar.get("latency_ms", 0) > 5000:
                suggestions.append(
                    f"Slow action '{ar['action']}' ({ar['latency_ms']}ms). "
                    "Consider optimizing the underlying Flow/Apex or adding caching."
                )

        if not suggestions:
            suggestions.append("No issues detected — all checks passed.")

        return suggestions

    # ═══════════════════════════════════════════════════════════
    # Prompt Validation (New in v2.2)
    # ═══════════════════════════════════════════════════════════

    def prompt_validation(self, expected_instructions: list[str]) -> dict:
        """
        Validate that expected instruction text appears in compiled LLM prompts.

        Args:
            expected_instructions: List of instruction strings to search for

        Returns:
            Dict with found/missing instruction lists and pass/fail status
        """
        llm_steps = self._steps_of_type(LLM_STEP)
        if not llm_steps:
            return {
                "status": "NO_DATA",
                "found": [],
                "missing": expected_instructions,
                "message": "No LLM steps found in traces",
            }

        # Concatenate all system prompts for searching
        all_prompts = ""
        for step in llm_steps:
            prompt_content = step.get("data", {}).get("prompt_content", [])
            for msg in prompt_content:
                if msg.get("role") == "system":
                    all_prompts += msg.get("content", "") + "\n"

        found = []
        missing = []
        for instruction in expected_instructions:
            if instruction.lower() in all_prompts.lower():
                found.append(instruction)
            else:
                missing.append(instruction)

        return {
            "status": "PASS" if not missing else "FAIL",
            "found": found,
            "missing": missing,
            "total_checked": len(expected_instructions),
            "message": (
                f"All {len(found)} instructions found in compiled prompts"
                if not missing
                else f"{len(missing)}/{len(expected_instructions)} instructions NOT found in compiled prompts"
            ),
        }

    # ═══════════════════════════════════════════════════════════
    # Output Methods
    # ═══════════════════════════════════════════════════════════

    def render_turn_panel(self, trace: dict, console: Console) -> None:
        """Render a single turn as a Rich panel."""
        steps = self._steps_for_trace(trace)

        user_input = ""
        agent_response = ""
        topic = ""
        actions = []
        grounding = ""

        for step in steps:
            st = step.get("stepType", "")
            data = step.get("data", {})

            if st == USER_INPUT:
                user_input = data.get("utterance", data.get("input", ""))
            elif st == PLANNER_RESPONSE:
                agent_response = data.get("responseText", "")
            elif st == TRANSITION:
                topic = data.get("to", "")
            elif st == FUNCTION_STEP:
                fn = data.get("function", "")
                err = data.get("error")
                status = "[red]FAIL[/red]" if err else "[green]OK[/green]"
                actions.append(f"  {status} {fn}")
            elif st == REASONING:
                grounding = data.get("groundingAssessment", "")

        lines = []
        lines.append(f"[bold]User:[/bold] {user_input}")
        if topic:
            lines.append(f"[bold]Topic:[/bold] {topic}")
        if actions:
            lines.append("[bold]Actions:[/bold]")
            lines.extend(actions)
        if grounding:
            color = "green" if grounding == "GROUNDED" else "red"
            lines.append(f"[bold]Grounding:[/bold] [{color}]{grounding}[/{color}]")
        lines.append(f"[bold]Response:[/bold] {agent_response[:200]}")

        console.print(Panel("\n".join(lines), title="Turn", border_style="cyan"))

    def render_terminal(self, console: Console) -> None:
        """Render full analysis to terminal with Rich formatting."""
        console.print("\n[bold cyan]═══ Trace Analysis Report ═══[/bold cyan]\n")

        # Timeline
        timeline = self.conversation_timeline()
        for turn in timeline:
            self.render_turn_panel(self.traces[turn["turn"] - 1], console)

        # Timing
        timing = self.timing_report()
        timing_table = Table(title="Timing Summary", show_header=True)
        timing_table.add_column("Metric", style="bold")
        timing_table.add_column("Value", justify="right")
        timing_table.add_row("LLM Calls", str(timing["llm_calls"]))
        timing_table.add_row("LLM Total", f"{timing['llm_total_ms']}ms")
        timing_table.add_row("LLM Avg", f"{timing['llm_avg_ms']}ms")
        timing_table.add_row("Action Calls", str(timing["action_calls"]))
        timing_table.add_row("Action Total", f"{timing['action_total_ms']}ms")
        timing_table.add_row("Input Tokens", str(timing["input_tokens"]))
        timing_table.add_row("Output Tokens", str(timing["output_tokens"]))
        console.print(timing_table)

        # Suggestions
        suggestions = self.agentscript_suggestions()
        console.print("\n[bold yellow]Agent Script Suggestions:[/bold yellow]")
        for s in suggestions:
            console.print(f"  • {s}")

    def to_json(self, output_path: Path) -> None:
        """Export full analysis as JSON."""
        analysis = {
            "timeline": self.conversation_timeline(),
            "grounding": self.grounding_report(),
            "safety": self.safety_report(),
            "variables": self.variable_diff_report(),
            "actions": self.action_report(),
            "routing": self.routing_report(),
            "timing": self.timing_report(),
            "suggestions": self.agentscript_suggestions(),
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(analysis, f, indent=2, default=str)

    def to_summary(self) -> dict:
        """Return a summary dict with pass/fail status."""
        grounding = self.grounding_report()
        actions = self.action_report()
        safety = self.safety_report()

        ungrounded = sum(1 for g in grounding if g["assessment"] == "UNGROUNDED")
        failed_actions = sum(1 for a in actions if a.get("error"))
        low_safety = sum(
            1 for s in safety
            if s.get("overall") is not None and s["overall"] < 0.9
        )

        has_issues = ungrounded > 0 or failed_actions > 0 or low_safety > 0

        return {
            "status": "FAIL" if has_issues else "PASS",
            "turns": len(self.traces),
            "ungrounded": ungrounded,
            "failed_actions": failed_actions,
            "low_safety_scores": low_safety,
            "total_actions": len(actions),
            "total_transitions": len(self.routing_report()),
        }

    def render_summary_line(self) -> str:
        """Return a single-line summary string."""
        s = self.to_summary()
        status = "[green]PASS[/green]" if s["status"] == "PASS" else "[red]FAIL[/red]"
        parts = [
            f"{status}",
            f"{s['turns']} turns",
            f"{s['total_actions']} actions",
        ]
        if s["ungrounded"]:
            parts.append(f"[red]{s['ungrounded']} ungrounded[/red]")
        if s["failed_actions"]:
            parts.append(f"[red]{s['failed_actions']} action failures[/red]")
        if s["low_safety_scores"]:
            parts.append(f"[yellow]{s['low_safety_scores']} low safety[/yellow]")
        return " | ".join(parts)


# ═══════════════════════════════════════════════════════════════
# CLI Entry Point
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze Agentforce v1.1 trace files")
    parser.add_argument(
        "--traces-dir", required=True, type=Path,
        help="Path to traces directory (.sfdx/agents/.../traces/)"
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help="Optional JSON output path"
    )
    args = parser.parse_args()

    console = Console()

    try:
        analyzer = TraceAnalyzer.from_cli_traces(args.traces_dir)
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

    # Render to terminal
    analyzer.render_terminal(console)
    console.print(f"\n{analyzer.render_summary_line()}")

    # Optional JSON output
    if args.output:
        analyzer.to_json(args.output)
        console.print(f"\n[dim]Analysis written to: {args.output}[/dim]")

    # Exit code
    summary = analyzer.to_summary()
    sys.exit(0 if summary["status"] == "PASS" else 1)
