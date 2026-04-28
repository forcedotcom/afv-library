#!/usr/bin/env python3
"""
Multi-Turn Fix Loop

Iterative test runner that executes multi_turn_test_runner.py in a loop,
tracking iterations, detecting regressions, and producing machine-readable
fix instructions for the agentic fix loop.

Usage:
    python3 multi_turn_fix_loop.py \
        --runner hooks/scripts/multi_turn_test_runner.py \
        --scenarios assets/multi-turn-comprehensive.yaml \
        --agent-id 0XxABC... \
        --max-attempts 5 \
        --output fix-loop-results.json

    # With extra runner args:
    python3 multi_turn_fix_loop.py \
        --runner hooks/scripts/multi_turn_test_runner.py \
        --scenarios assets/my-scenarios.yaml \
        --agent-id 0XxABC... \
        --max-attempts 3 \
        --runner-args '--verbose --var $Context.AccountId=001XXX'

Exit Codes:
    0 = All tests passed
    1 = Fixes still needed (some scenarios failed on last iteration)
    2 = Max attempts reached
    3 = Execution error (runner crash, invalid args, etc.)

Dependencies:
    - Python 3.8+ standard library only (subprocess, json, argparse)
    - multi_turn_test_runner.py must be accessible

Author: Jag Valaiyapathy
License: MIT
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


# ═══════════════════════════════════════════════════════════════════════════
# Fix Loop Engine
# ═══════════════════════════════════════════════════════════════════════════

def run_test_iteration(
    runner_path: str,
    scenarios_path: str,
    agent_id: str,
    extra_args: List[str] = None,
    timeout: int = 600,
) -> Dict[str, Any]:
    """
    Run the test runner once and parse its JSON output.

    Returns:
        Dict with 'success', 'results', 'exit_code', 'error'.
    """
    cmd = [
        sys.executable, runner_path,
        "--scenarios", scenarios_path,
        "--agent-id", agent_id,
        "--json-only",
    ]
    if extra_args:
        cmd.extend(extra_args)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        # Parse JSON output
        stdout = result.stdout.strip()
        if not stdout:
            return {
                "success": False,
                "results": None,
                "exit_code": result.returncode,
                "error": f"No output from runner. stderr: {result.stderr[:500]}",
            }

        # The runner may output non-JSON lines before/after — find the JSON block
        json_start = stdout.find("{")
        json_end = stdout.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            json_str = stdout[json_start:json_end]
            results = json.loads(json_str)
        else:
            return {
                "success": False,
                "results": None,
                "exit_code": result.returncode,
                "error": f"No JSON found in output: {stdout[:300]}",
            }

        return {
            "success": result.returncode == 0,
            "results": results,
            "exit_code": result.returncode,
            "error": None,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "results": None,
            "exit_code": -1,
            "error": f"Runner timed out after {timeout}s",
        }
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "results": None,
            "exit_code": result.returncode,
            "error": f"Failed to parse runner JSON output: {e}",
        }
    except FileNotFoundError:
        return {
            "success": False,
            "results": None,
            "exit_code": -1,
            "error": f"Runner not found: {runner_path}",
        }


def extract_failed_scenarios(results: Dict) -> Set[str]:
    """Extract set of failed scenario names from test results."""
    failed = set()
    for scenario in results.get("scenarios", []):
        if scenario.get("status") != "passed":
            failed.add(scenario.get("name", "unknown"))
    return failed


def extract_failure_details(results: Dict) -> List[Dict[str, str]]:
    """Extract detailed failure info for fix instructions."""
    failures = []
    for scenario in results.get("scenarios", []):
        if scenario.get("status") == "passed":
            continue
        for turn in scenario.get("turns", []):
            if turn.get("evaluation", {}).get("passed"):
                continue
            for check in turn.get("evaluation", {}).get("checks", []):
                if not check.get("passed"):
                    failures.append({
                        "scenario": scenario.get("name", "unknown"),
                        "turn": turn.get("turn_number", 0),
                        "check": check.get("name", ""),
                        "expected": str(check.get("expected", "")),
                        "actual": str(check.get("actual", "")),
                        "detail": check.get("detail", ""),
                    })
    return failures


def detect_regressions(
    prev_passed: Set[str],
    current_failed: Set[str],
) -> List[str]:
    """Detect scenarios that passed before but now fail (regressions)."""
    return sorted(prev_passed & current_failed)


def build_fix_instructions(failures: List[Dict]) -> List[Dict[str, str]]:
    """Build categorized fix instructions from failure details."""
    # Map check names to categories
    check_to_category = {
        "topic_contains": "TOPIC_RE_MATCHING_FAILURE",
        "response_contains": "CONTEXT_PRESERVATION_FAILURE",
        "context_retained": "CONTEXT_PRESERVATION_FAILURE",
        "context_uses": "CONTEXT_PRESERVATION_FAILURE",
        "no_re_ask_for": "CONTEXT_PRESERVATION_FAILURE",
        "escalation_triggered": "MULTI_TURN_ESCALATION_FAILURE",
        "guardrail_triggered": "GUARDRAIL_NOT_TRIGGERED",
        "action_invoked": "ACTION_NOT_INVOKED",
        "action_uses_prior_output": "ACTION_CHAIN_FAILURE",
        "response_not_empty": "RESPONSE_QUALITY_ISSUE",
        "response_declines_gracefully": "GUARDRAIL_NOT_TRIGGERED",
        "resumes_normal": "GUARDRAIL_RECOVERY_FAILURE",
        "turn_elapsed_max": "RESPONSE_QUALITY_ISSUE",
        "response_matches_regex": "CONTEXT_PRESERVATION_FAILURE",
        "response_length_min": "RESPONSE_QUALITY_ISSUE",
        "response_length_max": "RESPONSE_QUALITY_ISSUE",
        "action_result_contains": "ACTION_CHAIN_FAILURE",
    }

    category_to_fix = {
        "TOPIC_RE_MATCHING_FAILURE": "Add transition phrases to target topic classificationDescription",
        "CONTEXT_PRESERVATION_FAILURE": "Add 'use context from prior messages' to topic instructions",
        "MULTI_TURN_ESCALATION_FAILURE": "Add frustration detection keywords to escalation triggers",
        "GUARDRAIL_NOT_TRIGGERED": "Add explicit guardrail statements to system instructions",
        "ACTION_NOT_INVOKED": "Improve action description and trigger conditions",
        "ACTION_CHAIN_FAILURE": "Verify action output variable mappings between actions",
        "RESPONSE_QUALITY_ISSUE": "Review agent instructions for completeness",
        "GUARDRAIL_RECOVERY_FAILURE": "Ensure guardrail response doesn't terminate session state",
    }

    seen_categories = set()
    instructions = []
    for f in failures:
        category = check_to_category.get(f["check"])
        if category and category not in seen_categories:
            seen_categories.add(category)
            instructions.append({
                "category": category,
                "fix": category_to_fix.get(category, "Review agent configuration"),
                "example_scenario": f["scenario"],
                "example_check": f["check"],
            })

    return instructions


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Multi-Turn Fix Loop — iterative test runner with regression detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 multi_turn_fix_loop.py \\
      --runner hooks/scripts/multi_turn_test_runner.py \\
      --scenarios assets/multi-turn-comprehensive.yaml \\
      --agent-id 0XxABC... \\
      --max-attempts 5

  python3 multi_turn_fix_loop.py \\
      --runner hooks/scripts/multi_turn_test_runner.py \\
      --scenarios assets/my-tests.yaml \\
      --agent-id 0XxABC... \\
      --max-attempts 3 \\
      --output results.json \\
      --runner-args '--verbose --turn-retry 1'
""",
    )

    parser.add_argument("--runner", required=True,
                        help="Path to multi_turn_test_runner.py")
    parser.add_argument("--scenarios", required=True,
                        help="Path to YAML scenario file")
    parser.add_argument("--agent-id", required=True,
                        help="BotDefinition ID")
    parser.add_argument("--max-attempts", type=int, default=5,
                        help="Maximum fix iterations (default: 5)")
    parser.add_argument("--output", default=None,
                        help="Write JSON results to this file")
    parser.add_argument("--runner-args", default="",
                        help="Extra arguments to pass to the test runner (space-separated)")
    parser.add_argument("--timeout", type=int, default=600,
                        help="Timeout per runner invocation in seconds (default: 600)")
    parser.add_argument("--verbose", action="store_true",
                        help="Print progress to stderr")

    args = parser.parse_args()

    # Validate
    if not Path(args.runner).is_file():
        print(f"ERROR: Runner not found: {args.runner}", file=sys.stderr)
        sys.exit(3)

    if not Path(args.scenarios).is_file():
        print(f"ERROR: Scenarios not found: {args.scenarios}", file=sys.stderr)
        sys.exit(3)

    extra_args = args.runner_args.split() if args.runner_args else []

    # State tracking
    iterations = []
    all_regressions = []
    prev_passed_scenarios: Set[str] = set()
    final_status = "error"

    for attempt in range(1, args.max_attempts + 1):
        if args.verbose:
            print(f"\n{'='*60}", file=sys.stderr)
            print(f"FIX LOOP — Iteration {attempt}/{args.max_attempts}", file=sys.stderr)
            print(f"{'='*60}", file=sys.stderr)

        start = time.time()
        run = run_test_iteration(
            runner_path=args.runner,
            scenarios_path=args.scenarios,
            agent_id=args.agent_id,
            extra_args=extra_args,
            timeout=args.timeout,
        )
        elapsed = time.time() - start

        iteration_data = {
            "attempt": attempt,
            "elapsed_s": round(elapsed, 1),
            "exit_code": run["exit_code"],
            "error": run["error"],
        }

        if run["error"]:
            iteration_data["status"] = "error"
            iterations.append(iteration_data)
            if args.verbose:
                print(f"  ❌ Error: {run['error']}", file=sys.stderr)
            final_status = "error"
            break

        results = run["results"]
        summary = results.get("summary", {})
        iteration_data["summary"] = summary

        current_failed = extract_failed_scenarios(results)
        current_passed = {
            s.get("name", "") for s in results.get("scenarios", [])
            if s.get("status") == "passed"
        }

        # Detect regressions
        regressions = detect_regressions(prev_passed_scenarios, current_failed)
        iteration_data["regressions"] = regressions
        all_regressions.extend(regressions)

        if regressions and args.verbose:
            print(f"  ⚠️  REGRESSIONS: {regressions}", file=sys.stderr)

        # Extract failure details
        failures = extract_failure_details(results)
        iteration_data["failure_count"] = len(failures)

        if args.verbose:
            passed = summary.get("passed_scenarios", 0)
            total = summary.get("total_scenarios", 0)
            print(f"  📊 {passed}/{total} scenarios passed", file=sys.stderr)

        if run["success"]:
            iteration_data["status"] = "passed"
            iterations.append(iteration_data)
            final_status = "passed"
            if args.verbose:
                print(f"  ✅ All scenarios passed!", file=sys.stderr)
            break

        # Build fix instructions
        fix_instructions = build_fix_instructions(failures)
        iteration_data["status"] = "fixes_needed"
        iteration_data["fix_instructions"] = fix_instructions
        iterations.append(iteration_data)

        if args.verbose:
            for fi in fix_instructions:
                print(f"  🔧 {fi['category']}: {fi['fix']}", file=sys.stderr)

        # Update state for next iteration
        prev_passed_scenarios = current_passed

        if attempt == args.max_attempts:
            final_status = "max_attempts"
            if args.verbose:
                print(f"\n  ⚠️  Max attempts ({args.max_attempts}) reached.", file=sys.stderr)
        else:
            final_status = "fixes_needed"

    # Build output
    output = {
        "final_status": final_status,
        "total_iterations": len(iterations),
        "regressions": sorted(set(all_regressions)),
        "iterations": iterations,
    }

    # Add final fix instructions from last iteration
    if iterations and iterations[-1].get("fix_instructions"):
        output["fix_instructions"] = iterations[-1]["fix_instructions"]
    else:
        output["fix_instructions"] = []

    # Write output
    if args.output:
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)
        if args.verbose:
            print(f"\n📄 Results written to: {args.output}", file=sys.stderr)

    # Print summary to stdout
    print(json.dumps(output, indent=2))

    # Exit code
    exit_codes = {
        "passed": 0,
        "fixes_needed": 1,
        "max_attempts": 2,
        "error": 3,
    }
    sys.exit(exit_codes.get(final_status, 3))


if __name__ == "__main__":
    main()
