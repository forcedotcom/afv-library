#!/usr/bin/env python3
"""
Parse Agentforce test results and format for Claude auto-fix loop.

This hook parses the JSON output from `sf agent test run/results` and provides
structured feedback that enables Claude to automatically fix failing tests.

Environment Variables:
    TOOL_OUTPUT: The stdout from the Bash command
    TOOL_INPUT: The command that was executed

Output:
    Formatted test results with failure analysis and fix suggestions
"""

import json
import os
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

# Only process sf agent test commands
def should_process() -> bool:
    """Check if this is an agent test command we should process."""
    tool_input = os.environ.get('TOOL_INPUT', '')
    return any(cmd in tool_input for cmd in [
        'sf agent test run',
        'sf agent test results',
        'sf agent test resume',
        'sf agent preview',
        'einstein/ai-agent/v1',
        'ai-agent/v1/agents',
        'ai-agent/v1/sessions'
    ])


def parse_test_results(output: str) -> dict:
    """
    Parse test results from sf CLI JSON output.

    Returns:
        dict with summary, failures, and coverage data
    """
    try:
        # Try to parse as JSON (if --result-format json was used)
        data = json.loads(output)
        return parse_json_results(data)
    except json.JSONDecodeError:
        # Parse human-readable output
        return parse_text_results(output)


def parse_json_results(data: dict) -> dict:
    """Parse JSON format test results from sf agent test."""
    result = data.get('result', data)

    summary = {
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'total': 0,
        'agent_name': '',
        'test_suite': '',
        'status': 'Unknown'
    }

    failures = []
    topic_coverage = []
    action_coverage = []

    # Extract agent/suite info
    summary['agent_name'] = result.get('aiEvaluationName', result.get('agentName', 'Unknown'))
    summary['test_suite'] = result.get('testSuiteName', result.get('name', 'Unknown'))
    summary['status'] = result.get('status', 'Unknown')

    # Parse test case results
    test_cases = result.get('testCases', result.get('results', []))

    for test in test_cases:
        outcome = test.get('status', test.get('outcome', '')).lower()

        if outcome in ['pass', 'passed', 'success']:
            summary['passed'] += 1
        elif outcome in ['fail', 'failed', 'error']:
            summary['failed'] += 1
            failure = extract_failure(test)
            failures.append(failure)
        elif outcome in ['skip', 'skipped']:
            summary['skipped'] += 1

    summary['total'] = summary['passed'] + summary['failed'] + summary['skipped']

    # Extract coverage if available
    coverage_data = result.get('coverage', {})
    if coverage_data:
        topic_coverage = coverage_data.get('topics', [])
        action_coverage = coverage_data.get('actions', [])

    return {
        'summary': summary,
        'failures': failures,
        'topic_coverage': topic_coverage,
        'action_coverage': action_coverage
    }


def extract_failure(test: dict) -> dict:
    """Extract failure details from a test case result."""
    return {
        'name': test.get('name', test.get('testCaseName', 'Unknown')),
        'category': test.get('category', detect_category(test)),
        'utterance': test.get('utterance', test.get('input', '')),
        'expected_topic': test.get('expectedTopic', ''),
        'actual_topic': test.get('actualTopic', test.get('selectedTopic', '')),
        'expected_actions': test.get('expectedActions', []),
        'actual_actions': test.get('actualActions', test.get('invokedActions', [])),
        'expected_behavior': test.get('expectedBehavior', ''),
        'actual_behavior': test.get('actualBehavior', ''),
        'error_message': test.get('errorMessage', test.get('message', '')),
        'response': test.get('response', test.get('agentResponse', '')),
        'conversation_id': test.get('conversationId', '')
    }


def detect_category(test: dict) -> str:
    """Detect test category from test structure."""
    if test.get('expectedTopic'):
        return 'topic_routing'
    if test.get('expectedActions'):
        return 'action_invocation'
    if test.get('expectedBehavior') in ['guardrail_triggered', 'graceful_decline']:
        return 'guardrails'
    if test.get('expectedBehavior') in ['escalation_triggered', 'no_escalation']:
        return 'escalation'
    if test.get('conversationHistory'):
        return 'multi_turn'
    return 'edge_cases'


def parse_text_results(output: str) -> dict:
    """Parse human-readable test output."""
    summary = {
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'total': 0,
        'agent_name': 'Unknown',
        'test_suite': 'Unknown',
        'status': 'Unknown'
    }

    failures = []

    # Look for pass/fail patterns
    pass_match = re.search(r'(\d+)\s+(?:test[s]?\s+)?pass(?:ed|ing)?', output, re.IGNORECASE)
    fail_match = re.search(r'(\d+)\s+(?:test[s]?\s+)?fail(?:ed|ing|ure)?', output, re.IGNORECASE)

    if pass_match:
        summary['passed'] = int(pass_match.group(1))
    if fail_match:
        summary['failed'] = int(fail_match.group(1))

    summary['total'] = summary['passed'] + summary['failed']

    # Look for agent name
    agent_match = re.search(r'[Aa]gent[:\s]+([A-Za-z0-9_]+)', output)
    if agent_match:
        summary['agent_name'] = agent_match.group(1)

    # Look for failure details
    failure_patterns = [
        r'FAILED[:\s]+([^\n]+)',
        r'Error[:\s]+([^\n]+)',
        r'Topic mismatch[:\s]+expected\s+(\w+)\s+got\s+(\w+)'
    ]

    for pattern in failure_patterns:
        for match in re.finditer(pattern, output, re.IGNORECASE):
            failures.append({
                'name': 'Unknown',
                'category': 'unknown',
                'error_message': match.group(1) if match.lastindex >= 1 else match.group(0),
                'utterance': '',
                'expected_topic': '',
                'actual_topic': ''
            })

    return {
        'summary': summary,
        'failures': failures,
        'topic_coverage': [],
        'action_coverage': []
    }


def categorize_failure(failure: dict) -> dict:
    """
    Categorize a test failure and provide fix strategy.

    Returns:
        dict with failure_type, root_cause, suggested_fix, and target_skill
    """
    category = failure.get('category', 'unknown')
    error_msg = failure.get('error_message', '')

    analysis = {
        'failure_type': 'Unknown',
        'root_cause': 'Unable to determine root cause',
        'suggested_fix': 'Review the agent configuration',
        'target_skill': 'sf-ai-agentforce',
        'auto_fixable': False,
        'fix_location': ''
    }

    # Topic routing failures
    if category == 'topic_routing' or 'topic' in error_msg.lower():
        analysis['failure_type'] = 'TOPIC_NOT_MATCHED'
        expected = failure.get('expected_topic', 'expected')
        actual = failure.get('actual_topic', 'actual')

        if actual:
            analysis['root_cause'] = f"Wrong topic selected: expected '{expected}' but got '{actual}'"
            analysis['suggested_fix'] = "Improve topic scope descriptions to better match the utterance intent"
        else:
            analysis['root_cause'] = f"No topic matched for utterance"
            analysis['suggested_fix'] = "Add topic scope examples or adjust classificationDescription"

        analysis['fix_location'] = f"Agent Script: {failure.get('name', '')}"
        analysis['auto_fixable'] = True

    # Action invocation failures
    elif category == 'action_invocation' or 'action' in error_msg.lower():
        expected_actions = failure.get('expected_actions', [])
        actual_actions = failure.get('actual_actions', [])

        if expected_actions and not actual_actions:
            analysis['failure_type'] = 'ACTION_NOT_INVOKED'
            action_names = [a.get('name', str(a)) if isinstance(a, dict) else str(a) for a in expected_actions]
            analysis['root_cause'] = f"Expected action(s) not invoked: {', '.join(action_names)}"
            analysis['suggested_fix'] = "Check action trigger conditions and topic instructions"
        elif actual_actions:
            analysis['failure_type'] = 'WRONG_ACTION_SELECTED'
            analysis['root_cause'] = "Incorrect action was selected"
            analysis['suggested_fix'] = "Review action descriptions and topic instructions for clarity"
        else:
            analysis['failure_type'] = 'ACTION_INVOCATION_FAILED'
            analysis['root_cause'] = "Action invocation error"
            analysis['suggested_fix'] = "Check action configuration and underlying Flow/Apex"

        analysis['fix_location'] = "Topic actions configuration"
        analysis['auto_fixable'] = True

    # Guardrail failures
    elif category == 'guardrails' or 'guardrail' in error_msg.lower():
        expected_behavior = failure.get('expected_behavior', '')

        if expected_behavior == 'guardrail_triggered':
            analysis['failure_type'] = 'GUARDRAIL_NOT_TRIGGERED'
            analysis['root_cause'] = "Harmful request was not blocked"
            analysis['suggested_fix'] = "Add explicit guardrail instructions in agent system prompt"
        elif expected_behavior == 'graceful_decline':
            analysis['failure_type'] = 'OFF_TOPIC_NOT_HANDLED'
            analysis['root_cause'] = "Off-topic request was not gracefully declined"
            analysis['suggested_fix'] = "Add fallback topic or improve system instructions for off-topic handling"
        else:
            analysis['failure_type'] = 'GUARDRAIL_ISSUE'
            analysis['root_cause'] = "Guardrail behavior unexpected"
            analysis['suggested_fix'] = "Review agent system instructions and topic scope"

        analysis['fix_location'] = "Agent system instructions or guardrail settings"
        analysis['auto_fixable'] = True

    # Escalation failures
    elif category == 'escalation' or 'escalat' in error_msg.lower():
        expected_behavior = failure.get('expected_behavior', '')

        if expected_behavior == 'escalation_triggered':
            analysis['failure_type'] = 'ESCALATION_NOT_TRIGGERED'
            analysis['root_cause'] = "User request should have triggered human handoff"
            analysis['suggested_fix'] = "Add escalation action or improve escalation trigger instructions"
        elif expected_behavior == 'no_escalation':
            analysis['failure_type'] = 'UNNECESSARY_ESCALATION'
            analysis['root_cause'] = "Simple request unnecessarily escalated to human"
            analysis['suggested_fix'] = "Adjust escalation thresholds in topic instructions"

        analysis['fix_location'] = "Escalation action or topic instructions"
        analysis['auto_fixable'] = True

    # Response quality issues
    elif category in ['edge_cases', 'multi_turn']:
        analysis['failure_type'] = 'RESPONSE_QUALITY_ISSUE'
        analysis['root_cause'] = "Agent response did not meet quality expectations"
        analysis['suggested_fix'] = "Review agent instructions for handling edge cases"
        analysis['fix_location'] = "Agent system instructions"
        analysis['auto_fixable'] = False  # Typically requires human review

    return analysis


def format_output(results: dict) -> str:
    """Format test results for Claude consumption."""
    summary = results['summary']
    failures = results['failures']

    lines = []
    lines.append("=" * 65)
    lines.append("AGENTFORCE TEST RESULTS")
    lines.append("=" * 65)
    lines.append("")

    # Agent/Suite info
    lines.append(f"Agent: {summary['agent_name']}")
    lines.append(f"Suite: {summary['test_suite']}")
    lines.append(f"Status: {summary['status']}")
    lines.append("")

    # Summary
    status_icon = "PASS" if summary['failed'] == 0 else "FAIL"
    lines.append(f"{status_icon} SUMMARY")
    lines.append("-" * 65)
    lines.append(f"   Passed:   {summary['passed']}")
    lines.append(f"   Failed:   {summary['failed']}")
    lines.append(f"   Skipped:  {summary['skipped']}")
    lines.append(f"   Total:    {summary['total']}")
    lines.append("")

    # Failures with analysis
    if failures:
        lines.append("FAILED TESTS")
        lines.append("-" * 65)

        # Group failures by category
        categorized = {}
        for failure in failures:
            analysis = categorize_failure(failure)
            cat = analysis['failure_type']
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append((failure, analysis))

        for failure_type, items in categorized.items():
            lines.append(f"\n>> {failure_type} ({len(items)} failure{'s' if len(items) > 1 else ''})")

            for i, (failure, analysis) in enumerate(items, 1):
                lines.append(f"\n   {i}. {failure.get('name', 'Unknown')}")

                if failure.get('utterance'):
                    utterance = failure['utterance'][:80] + "..." if len(failure.get('utterance', '')) > 80 else failure.get('utterance', '')
                    lines.append(f"      Utterance: \"{utterance}\"")

                if failure.get('expected_topic') and failure.get('actual_topic'):
                    lines.append(f"      Expected Topic: {failure['expected_topic']}")
                    lines.append(f"      Actual Topic: {failure['actual_topic']}")

                if failure.get('error_message'):
                    msg = failure['error_message'][:100] + "..." if len(failure.get('error_message', '')) > 100 else failure.get('error_message', '')
                    lines.append(f"      Error: {msg}")

                lines.append(f"      Root Cause: {analysis['root_cause']}")
                lines.append(f"      Fix Location: {analysis['fix_location']}")
                lines.append(f"      Suggested Fix: {analysis['suggested_fix']}")

                if analysis['auto_fixable']:
                    lines.append(f"      AUTO-FIXABLE: Yes - sf-ai-agentforce skill can attempt fix")

        lines.append("")
        lines.append("=" * 65)
        lines.append("AGENTIC FIX INSTRUCTIONS")
        lines.append("=" * 65)
        lines.append("")
        lines.append("To automatically fix these failures, invoke sf-ai-agentforce skill:")
        lines.append("")

        # Generate fix prompt based on failure types
        if 'TOPIC_NOT_MATCHED' in categorized:
            lines.append("1. TOPIC FIXES: Improve topic scope/description to match utterances")
            lines.append("   - Update classificationDescription with better examples")
            lines.append("   - Add scope patterns that match failed utterances")

        if any(ft in categorized for ft in ['ACTION_NOT_INVOKED', 'WRONG_ACTION_SELECTED', 'ACTION_INVOCATION_FAILED']):
            lines.append("2. ACTION FIXES: Adjust action triggers and instructions")
            lines.append("   - Check action preconditions and availability")
            lines.append("   - Improve topic instructions for when to invoke actions")

        if any(ft in categorized for ft in ['GUARDRAIL_NOT_TRIGGERED', 'OFF_TOPIC_NOT_HANDLED']):
            lines.append("3. GUARDRAIL FIXES: Strengthen safety instructions")
            lines.append("   - Add explicit guardrail statements to system prompt")
            lines.append("   - Configure fallback topic for off-topic handling")

        if any(ft in categorized for ft in ['ESCALATION_NOT_TRIGGERED', 'UNNECESSARY_ESCALATION']):
            lines.append("4. ESCALATION FIXES: Adjust handoff triggers")
            lines.append("   - Add/modify escalation action conditions")
            lines.append("   - Update topic instructions for when to escalate")

        lines.append("")
        lines.append("After fixes, re-run tests:")
        lines.append(f"   sf agent test run --api-name {summary['agent_name']}_Tests --wait 10 --target-org [alias]")
        lines.append("")

    lines.append("=" * 65)

    return "\n".join(lines)


def main():
    """Main entry point."""
    if not should_process():
        # Not an agent test command, exit silently
        sys.exit(0)

    output = os.environ.get('TOOL_OUTPUT', '')

    if not output:
        sys.exit(0)

    # Check if this looks like agent test output
    keywords = ['test', 'agent', 'evaluation', 'passed', 'failed', 'topic', 'action']
    if not any(kw in output.lower() for kw in keywords):
        sys.exit(0)

    try:
        results = parse_test_results(output)

        # Only output if there were tests or failures
        if results['summary']['total'] > 0 or results['failures']:
            formatted = format_output(results)
            print(formatted)
    except Exception as e:
        # Silently fail - don't block on parsing errors
        sys.exit(0)


if __name__ == "__main__":
    main()
