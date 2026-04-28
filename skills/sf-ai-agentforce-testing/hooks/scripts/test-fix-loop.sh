#!/bin/bash
#
# test-fix-loop.sh - Automated Agent Test-Fix Loop Orchestrator
#
# This script runs agent tests and outputs structured failure data
# for Claude Code to process and fix via sf-ai-agentforce skill.
#
# Usage:
#   ./test-fix-loop.sh <test-api-name> <target-org> [max-attempts]
#
# Exit Codes:
#   0 - All tests passed
#   1 - Tests failed, fixes needed (Claude Code should invoke sf-ai-agentforce)
#   2 - Max attempts reached, escalate to human
#   3 - Error (test command failed, org unreachable, etc.)
#
# Environment Variables:
#   SKIP_TESTS - Comma-separated list of test names to skip (already escalated)
#   VERBOSE    - Set to "true" for detailed output
#
# Example:
#   ./test-fix-loop.sh Test_Agentforce_v1 AgentforceTesting 3
#
# Author: Jag Valaiyapathy
# License: MIT
#

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAX_WAIT_MINUTES=10
PYTHON_PARSER="${SCRIPT_DIR}/parse-agent-test-results.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Arguments
TEST_API_NAME="${1:-}"
TARGET_ORG="${2:-}"
MAX_ATTEMPTS="${3:-3}"
CURRENT_ATTEMPT="${CURRENT_ATTEMPT:-1}"

# Validate arguments
if [[ -z "$TEST_API_NAME" || -z "$TARGET_ORG" ]]; then
    echo "Usage: $0 <test-api-name> <target-org> [max-attempts]"
    echo ""
    echo "Arguments:"
    echo "  test-api-name  API name of the test definition (e.g., Test_Agentforce_v1)"
    echo "  target-org     Salesforce org alias"
    echo "  max-attempts   Maximum fix attempts before escalation (default: 3)"
    exit 3
fi

# Print header
print_header() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  AGENTFORCE TEST-FIX LOOP${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Test:     $TEST_API_NAME"
    echo "Org:      $TARGET_ORG"
    echo "Attempt:  $CURRENT_ATTEMPT of $MAX_ATTEMPTS"
    echo ""
}

# Run the agent test
run_tests() {
    echo -e "${YELLOW}Running agent tests...${NC}"
    echo ""

    # Run test with JSON output
    local test_output
    local exit_code=0

    test_output=$(sf agent test run \
        --api-name "$TEST_API_NAME" \
        --result-format json \
        --target-org "$TARGET_ORG" \
        --wait "$MAX_WAIT_MINUTES" 2>&1) || exit_code=$?

    # Check for command errors
    if [[ $exit_code -ne 0 ]]; then
        if echo "$test_output" | grep -q "INVALID_TYPE\|Not available"; then
            echo -e "${RED}ERROR: Agent Testing Center not enabled in org${NC}"
            echo ""
            echo "To enable:"
            echo "  - Contact Salesforce support"
            echo "  - Or use scratch org with AgentTestingCenter feature"
            exit 3
        fi

        if echo "$test_output" | grep -q "not found\|No such"; then
            echo -e "${RED}ERROR: Test definition not found: $TEST_API_NAME${NC}"
            echo ""
            echo "Available tests:"
            sf agent test list --target-org "$TARGET_ORG" 2>/dev/null || echo "  Unable to list tests"
            exit 3
        fi
    fi

    echo "$test_output"
}

# Parse test results and extract failures
parse_results() {
    local test_output="$1"

    # Try to parse as JSON
    if echo "$test_output" | jq -e . >/dev/null 2>&1; then
        local status
        local total_tests
        local passed_tests
        local failed_tests

        # Extract key metrics
        status=$(echo "$test_output" | jq -r '.result.status // .status // "Unknown"')
        total_tests=$(echo "$test_output" | jq -r '[.result.testCases // .testCases // [] | length] | add // 0')

        # Count passed/failed
        passed_tests=$(echo "$test_output" | jq -r '[.result.testCases // .testCases // [] | .[] | select(.status == "PASSED" or .status == "pass")] | length')
        failed_tests=$((total_tests - passed_tests))

        echo ""
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${BLUE}  TEST RESULTS${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
        echo ""
        echo "Status:       $status"
        echo "Total Tests:  $total_tests"
        echo -e "Passed:       ${GREEN}$passed_tests${NC}"
        echo -e "Failed:       ${RED}$failed_tests${NC}"
        echo ""

        # If all passed, exit success
        if [[ "$failed_tests" -eq 0 ]]; then
            echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
            return 0
        fi

        # Extract failure details for Claude Code
        echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${YELLOW}  FAILURES REQUIRING FIX${NC}"
        echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
        echo ""

        # Output structured failure data
        echo "$test_output" | jq -r '
            [.result.testCases // .testCases // [] | .[] | select(.status != "PASSED" and .status != "pass")] |
            to_entries | .[] |
            "FAILURE #\(.key + 1):
  Test Number: \(.value.number // .value.testNumber // "N/A")
  Utterance: \(.value.inputs.utterance // .value.utterance // "N/A")
  Expected Topic: \(.value.expectation // [] | map(select(.name | test("topic";"i"))) | .[0].expectedValue // "N/A")
  Actual Topic: \(.value.actualTopic // "N/A")
  Expected Actions: \(.value.expectation // [] | map(select(.name | test("action";"i"))) | .[0].expectedValue // "N/A")
  Actual Actions: \(.value.actualActions // "N/A")
  Score: \(.value.metrics // [] | map(select(.name == "output_validation")) | .[0].score // "N/A")
  Explainability: \(.value.metrics // [] | map(select(.name == "output_validation")) | .[0].metricExplainability // "N/A")
"'

        return 1
    else
        # Non-JSON output (human format)
        echo -e "${YELLOW}Warning: Non-JSON output, limited parsing${NC}"
        echo "$test_output"

        # Check for obvious pass/fail indicators
        if echo "$test_output" | grep -qi "all.*pass\|100%.*pass"; then
            return 0
        fi
        return 1
    fi
}

# Generate fix instructions for Claude Code
generate_fix_instructions() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  FIX INSTRUCTIONS FOR CLAUDE CODE${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "To fix these failures, Claude Code should:"
    echo ""
    echo "1. Invoke the sf-ai-agentforce skill:"
    echo "   Skill(skill=\"sf-ai-agentforce\", args=\"Fix agent failures...\")"
    echo ""
    echo "2. After applying fixes, re-run this script:"
    echo "   CURRENT_ATTEMPT=$((CURRENT_ATTEMPT + 1)) $0 $TEST_API_NAME $TARGET_ORG $MAX_ATTEMPTS"
    echo ""
    echo "3. Repeat until all tests pass or max attempts reached."
    echo ""

    # Machine-readable section for Claude Code
    echo "---BEGIN_MACHINE_READABLE---"
    echo "FIX_NEEDED: true"
    echo "TEST_API_NAME: $TEST_API_NAME"
    echo "TARGET_ORG: $TARGET_ORG"
    echo "CURRENT_ATTEMPT: $CURRENT_ATTEMPT"
    echo "MAX_ATTEMPTS: $MAX_ATTEMPTS"
    echo "NEXT_COMMAND: CURRENT_ATTEMPT=$((CURRENT_ATTEMPT + 1)) $0 $TEST_API_NAME $TARGET_ORG $MAX_ATTEMPTS"
    echo "---END_MACHINE_READABLE---"
}

# Main execution
main() {
    print_header

    # Check if max attempts reached
    if [[ "$CURRENT_ATTEMPT" -gt "$MAX_ATTEMPTS" ]]; then
        echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${RED}  MAX ATTEMPTS REACHED - ESCALATING TO HUMAN${NC}"
        echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
        echo ""
        echo "After $MAX_ATTEMPTS attempts, some tests still fail."
        echo "Manual review required."
        echo ""
        echo "Recommended actions:"
        echo "  1. Review test expectations - may need adjustment"
        echo "  2. Check agent configuration in Salesforce UI"
        echo "  3. Verify test data exists in org"
        echo "  4. Mark unfixable tests as SKIP_TESTS for future runs"
        echo ""
        exit 2
    fi

    # Run tests
    local test_output
    test_output=$(run_tests)

    # Parse and check results
    local parse_result=0
    parse_results "$test_output" || parse_result=$?

    if [[ "$parse_result" -eq 0 ]]; then
        echo ""
        echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}  TEST-FIX LOOP COMPLETE${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
        echo ""
        echo "All tests passed after $CURRENT_ATTEMPT attempt(s)."
        exit 0
    else
        generate_fix_instructions
        exit 1
    fi
}

# Run main
main
