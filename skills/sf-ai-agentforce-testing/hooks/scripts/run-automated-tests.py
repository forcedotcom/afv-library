#!/usr/bin/env python3
"""
Automated Agentforce Agent Testing Orchestrator.

This script orchestrates the full automated testing workflow:
1. Check if Agent Testing Center is enabled
2. Generate test spec from agent definition
3. Create test definition in org
4. Run tests with JSON output
5. Parse and display results
6. Suggest fixes for failures (enables agentic fix loop)

Usage:
    python3 run-automated-tests.py --agent-name MyAgent --agent-dir <path> --target-org <alias>
    python3 run-automated-tests.py --agent-name MyAgent --agent-file <path/to/Agent.agent> --target-org <alias>

Prerequisites:
    - Agent Testing Center must be enabled in org
    - sf CLI v2 with @salesforce/plugin-agent installed
    - Python 3.8+ with pyyaml (optional, fallback exists)
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

# Import the test spec generator
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from generate_test_spec import parse_agent_file, generate_test_spec, generate_test_cases
except ImportError:
    # Fallback if module import fails
    generate_test_spec = None


def run_command(cmd: list, capture_output: bool = True) -> Tuple[int, str, str]:
    """Run a command and return (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            timeout=300  # 5 minute timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out after 5 minutes"
    except Exception as e:
        return -1, "", str(e)


def check_agent_testing_center(target_org: str) -> bool:
    """Check if Agent Testing Center is enabled in the org."""
    print("=" * 65)
    print("STEP 1: Checking Agent Testing Center Availability")
    print("=" * 65)

    cmd = ['sf', 'agent', 'test', 'list', '--target-org', target_org, '--json']
    exit_code, stdout, stderr = run_command(cmd)

    if exit_code == 0:
        print("   Agent Testing Center is ENABLED")
        return True

    # Check for specific error messages
    combined_output = stdout + stderr
    if 'INVALID_TYPE' in combined_output or 'Not available' in combined_output:
        print("   Agent Testing Center is NOT ENABLED")
        print("")
        print("   To enable Agent Testing Center:")
        print("   - Contact Salesforce support or your account team")
        print("   - May require: Agentforce Service Agent license or Einstein Platform license")
        print("")
        return False

    # Other error
    print(f"   Warning: Could not determine status. Error: {stderr[:100]}")
    return False


def find_agent_file(agent_name: str, agent_dir: Optional[str], agent_file: Optional[str]) -> Optional[Path]:
    """Find the .agent file to test."""
    if agent_file:
        path = Path(agent_file)
        if path.exists():
            return path
        print(f"Error: Agent file not found: {agent_file}")
        return None

    if agent_dir:
        dir_path = Path(agent_dir)
        agent_files = list(dir_path.glob('*.agent'))
        if agent_files:
            return agent_files[0]

        # Try looking in standard DX structure
        bundle_path = dir_path / 'force-app/main/default/aiAuthoringBundles' / agent_name
        if bundle_path.exists():
            agent_files = list(bundle_path.glob('*.agent'))
            if agent_files:
                return agent_files[0]

        print(f"Error: No .agent file found in {agent_dir}")
        return None

    # Try current directory DX structure
    cwd = Path.cwd()
    bundle_path = cwd / 'force-app/main/default/aiAuthoringBundles' / agent_name
    if bundle_path.exists():
        agent_files = list(bundle_path.glob('*.agent'))
        if agent_files:
            return agent_files[0]

    print(f"Error: Could not find agent file for {agent_name}")
    return None


def generate_test_spec_file(agent_file: Path, output_dir: Path, agent_name: str) -> Optional[Path]:
    """Generate test spec YAML file from agent definition."""
    print("")
    print("=" * 65)
    print("STEP 2: Generating Test Spec from Agent Definition")
    print("=" * 65)
    print(f"   Agent file: {agent_file}")

    output_path = output_dir / f"{agent_name}-testSpec.yaml"

    # Try using generate-test-spec.py
    spec_script = SCRIPT_DIR / 'generate-test-spec.py'
    if spec_script.exists():
        cmd = [
            sys.executable, str(spec_script),
            '--agent-file', str(agent_file),
            '--output', str(output_path),
            '--verbose'
        ]
        exit_code, stdout, stderr = run_command(cmd, capture_output=False)

        if exit_code == 0 and output_path.exists():
            print(f"   Generated: {output_path}")
            return output_path

    # Fallback: try direct import
    if generate_test_spec:
        try:
            structure = parse_agent_file(str(agent_file))
            if not structure.agent_name:
                structure.agent_name = agent_name
            generate_test_spec(structure, str(output_path))
            print(f"   Generated: {output_path}")
            return output_path
        except Exception as e:
            print(f"   Error generating spec: {e}")

    print("   Error: Could not generate test spec")
    return None


def create_test_in_org(spec_file: Path, test_name: str, target_org: str) -> bool:
    """Create test definition in org using sf agent test create."""
    print("")
    print("=" * 65)
    print("STEP 3: Creating Test Definition in Org")
    print("=" * 65)
    print(f"   Spec file: {spec_file}")
    print(f"   Test name: {test_name}")
    print(f"   Target org: {target_org}")

    cmd = [
        'sf', 'agent', 'test', 'create',
        '--spec', str(spec_file),
        '--api-name', test_name,
        '--target-org', target_org,
        '--json'
    ]

    exit_code, stdout, stderr = run_command(cmd)

    if exit_code == 0:
        print("   Test definition created successfully")
        return True

    # Check for specific errors
    combined = stdout + stderr
    if 'INVALID_TYPE' in combined or 'Not available' in combined:
        print("   Error: Agent Testing Center not available")
        print("   Run 'sf agent test list' to verify access")
        return False

    if 'already exists' in combined.lower():
        print("   Test definition already exists - will use existing")
        return True

    print(f"   Error creating test: {stderr[:200]}")
    return False


def run_tests(test_name: str, target_org: str, wait_minutes: int = 10) -> Tuple[bool, str]:
    """Run agent tests and return results."""
    print("")
    print("=" * 65)
    print("STEP 4: Running Agent Tests")
    print("=" * 65)
    print(f"   Test name: {test_name}")
    print(f"   Wait timeout: {wait_minutes} minutes")
    print("")
    print("   Running tests (this may take a few minutes)...")

    cmd = [
        'sf', 'agent', 'test', 'run',
        '--api-name', test_name,
        '--wait', str(wait_minutes),
        '--result-format', 'json',
        '--target-org', target_org
    ]

    exit_code, stdout, stderr = run_command(cmd)

    if exit_code == 0:
        print("   Tests completed")
        return True, stdout

    print(f"   Tests may have failed or timed out")
    print(f"   Exit code: {exit_code}")

    # Return whatever output we got for parsing
    return False, stdout if stdout else stderr


def parse_and_display_results(output: str, agent_name: str) -> dict:
    """Parse test results and display formatted output."""
    print("")
    print("=" * 65)
    print("STEP 5: Parsing and Displaying Results")
    print("=" * 65)

    # Try to parse as JSON
    try:
        data = json.loads(output)
        result = data.get('result', data)
    except json.JSONDecodeError:
        print("   Warning: Could not parse JSON output")
        print("   Raw output:")
        print(output[:500])
        return {'passed': 0, 'failed': 0, 'total': 0}

    # Extract results
    summary = {
        'passed': 0,
        'failed': 0,
        'total': 0,
        'failures': []
    }

    test_cases = result.get('testCases', result.get('results', []))

    for test in test_cases:
        outcome = test.get('status', test.get('outcome', '')).lower()
        if outcome in ['pass', 'passed', 'success']:
            summary['passed'] += 1
        elif outcome in ['fail', 'failed', 'error']:
            summary['failed'] += 1
            summary['failures'].append({
                'name': test.get('name', test.get('testCaseName', 'Unknown')),
                'utterance': test.get('utterance', test.get('input', '')),
                'expected_topic': test.get('expectedTopic', ''),
                'actual_topic': test.get('actualTopic', ''),
                'expected_actions': test.get('expectedActions', []),
                'actual_actions': test.get('actualActions', []),
                'error': test.get('errorMessage', test.get('message', ''))
            })

    summary['total'] = summary['passed'] + summary['failed']

    # Display results
    print("")
    status_icon = "PASS" if summary['failed'] == 0 else "FAIL"
    print(f"   {status_icon}: {summary['passed']}/{summary['total']} tests passed")
    print("")

    if summary['failures']:
        print("   FAILURES:")
        print("   " + "-" * 60)
        for i, f in enumerate(summary['failures'], 1):
            print(f"   {i}. {f['name']}")
            if f['utterance']:
                utt = f['utterance'][:60] + '...' if len(f['utterance']) > 60 else f['utterance']
                print(f"      Utterance: \"{utt}\"")
            if f['expected_topic'] and f['actual_topic']:
                print(f"      Expected topic: {f['expected_topic']}")
                print(f"      Actual topic: {f['actual_topic']}")
            if f['error']:
                err = f['error'][:80] + '...' if len(f['error']) > 80 else f['error']
                print(f"      Error: {err}")
            print("")

    return summary


def suggest_fixes(summary: dict, agent_name: str) -> None:
    """Suggest fixes for failing tests (enables agentic fix loop)."""
    if summary['failed'] == 0:
        print("")
        print("=" * 65)
        print("ALL TESTS PASSED!")
        print("=" * 65)
        return

    print("")
    print("=" * 65)
    print("AGENTIC FIX SUGGESTIONS")
    print("=" * 65)
    print("")

    # Categorize failures
    topic_failures = []
    action_failures = []

    for f in summary['failures']:
        if f['expected_actions'] and not f['actual_actions']:
            action_failures.append(f)
        elif f['expected_topic'] != f['actual_topic']:
            topic_failures.append(f)
        else:
            topic_failures.append(f)  # Default

    if topic_failures:
        print("TOPIC ROUTING FIXES:")
        print("-" * 65)
        print("   The agent is routing utterances to wrong topics.")
        print("")
        print("   Suggested fix: Improve topic descriptions and scope.")
        print("")
        print("   Claude Code command:")
        print(f"   Skill(skill=\"sf-ai-agentforce\", args=\"Fix topic routing for {agent_name}:")
        for f in topic_failures[:3]:  # Show first 3
            print(f"     - Utterance '{f['utterance'][:40]}...' should route to {f['expected_topic']}\")")
        print("")

    if action_failures:
        print("ACTION INVOCATION FIXES:")
        print("-" * 65)
        print("   Expected actions were not invoked.")
        print("")
        print("   Suggested fix: Check action descriptions and trigger conditions.")
        print("")
        print("   Claude Code command:")
        print(f"   Skill(skill=\"sf-ai-agentforce\", args=\"Fix action triggers for {agent_name}:")
        for f in action_failures[:3]:
            actions = ', '.join(f['expected_actions']) if f['expected_actions'] else 'actions'
            print(f"     - Utterance should trigger {actions}\")")
        print("")

    print("NEXT STEPS:")
    print("-" * 65)
    print("   1. Apply the suggested fixes to the agent script")
    print("   2. Re-validate: sf agent validate authoring-bundle --api-name", agent_name)
    print("   3. Re-deploy: sf project deploy start --source-dir <agent-dir>")
    print("   4. Re-run tests: python3 run-automated-tests.py --agent-name", agent_name, "...")
    print("")


def main():
    parser = argparse.ArgumentParser(
        description='Automated Agentforce Agent Testing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Prerequisites:
  - Agent Testing Center must be enabled in org
  - sf CLI v2 with @salesforce/plugin-agent installed

Examples:
  # Test agent from directory
  python3 run-automated-tests.py --agent-name Coffee_Shop_FAQ_Agent \\
      --agent-dir /path/to/project --target-org MyOrg

  # Test specific agent file
  python3 run-automated-tests.py --agent-name Coffee_Shop_FAQ_Agent \\
      --agent-file /path/to/Agent.agent --target-org MyOrg

  # Skip test creation (use existing test)
  python3 run-automated-tests.py --agent-name Coffee_Shop_FAQ_Agent \\
      --target-org MyOrg --skip-create
        """
    )

    parser.add_argument('--agent-name', required=True, help='API name of the agent')
    parser.add_argument('--agent-file', help='Path to .agent file')
    parser.add_argument('--agent-dir', help='Path to project directory')
    parser.add_argument('--target-org', required=True, help='Target org alias')
    parser.add_argument('--output-dir', help='Directory for generated spec files')
    parser.add_argument('--wait', type=int, default=10, help='Wait timeout in minutes (default: 10)')
    parser.add_argument('--skip-create', action='store_true', help='Skip test creation, use existing')
    parser.add_argument('--skip-check', action='store_true', help='Skip Agent Testing Center check')

    args = parser.parse_args()

    print("")
    print("=" * 65)
    print("AGENTFORCE AUTOMATED TESTING")
    print("=" * 65)
    print(f"Agent: {args.agent_name}")
    print(f"Target Org: {args.target_org}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")

    # Step 1: Check Agent Testing Center
    if not args.skip_check:
        if not check_agent_testing_center(args.target_org):
            print("")
            print("FALLBACK: Use sf agent preview for manual testing:")
            print(f"   sf agent preview --api-name {args.agent_name} --target-org {args.target_org}")
            sys.exit(1)
    else:
        print("Skipping Agent Testing Center check (--skip-check)")

    # Step 2: Generate test spec
    agent_file = find_agent_file(args.agent_name, args.agent_dir, args.agent_file)
    if not agent_file:
        print("Error: Could not find agent file")
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else Path(tempfile.gettempdir()) / 'agentforce-tests'
    output_dir.mkdir(parents=True, exist_ok=True)

    spec_file = generate_test_spec_file(agent_file, output_dir, args.agent_name)
    if not spec_file:
        print("Error: Could not generate test spec")
        sys.exit(1)

    # Step 3: Create test in org
    test_name = f"{args.agent_name}_Tests"
    if not args.skip_create:
        if not create_test_in_org(spec_file, test_name, args.target_org):
            print("Warning: Test creation failed, attempting to run existing test...")

    # Step 4: Run tests
    success, output = run_tests(test_name, args.target_org, args.wait)

    # Step 5: Parse and display results
    summary = parse_and_display_results(output, args.agent_name)

    # Step 6: Suggest fixes
    suggest_fixes(summary, args.agent_name)

    # Exit code based on test results
    sys.exit(0 if summary['failed'] == 0 else 1)


if __name__ == "__main__":
    main()
