#!/usr/bin/env python3
"""
Generate Agentforce test specs from Agent Script (.agent) files.

This script parses .agent files to extract topics and actions, then generates
YAML test specifications compatible with `sf agent test create`.

Usage:
    python3 generate-test-spec.py --agent-file <path/to/Agent.agent> --output <path/to/spec.yaml>
    python3 generate-test-spec.py --agent-dir <path/to/aiAuthoringBundles/Agent/> --output <path/to/spec.yaml>

Output:
    YAML test spec file for sf agent test create
"""

import argparse
import re
import sys
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional

try:
    import yaml
except ImportError:
    # Fallback to manual YAML output if pyyaml not installed
    yaml = None


@dataclass
class AgentAction:
    """Represents an action defined in a topic."""
    name: str
    description: str = ""
    target: str = ""
    inputs: List[Dict] = field(default_factory=list)
    outputs: List[Dict] = field(default_factory=list)


@dataclass
class AgentTopic:
    """Represents a topic in the agent."""
    name: str
    label: str = ""
    description: str = ""
    is_start_agent: bool = False
    actions: List[AgentAction] = field(default_factory=list)
    transitions: List[str] = field(default_factory=list)


@dataclass
class AgentStructure:
    """Represents the parsed agent structure."""
    agent_name: str = ""
    agent_label: str = ""
    description: str = ""
    topics: List[AgentTopic] = field(default_factory=list)

    def get_topic(self, name: str) -> Optional[AgentTopic]:
        """Get a topic by name."""
        for topic in self.topics:
            if topic.name == name:
                return topic
        return None


def parse_agent_file(file_path: str) -> AgentStructure:
    """
    Parse an Agent Script (.agent) file and extract structure.

    Agent Script is an indentation-based DSL, NOT YAML. We parse it by:
    1. Tracking indentation levels
    2. Identifying key blocks (config, topic, actions)
    3. Extracting relevant fields
    """
    structure = AgentStructure()

    with open(file_path, 'r') as f:
        content = f.read()

    lines = content.split('\n')

    current_block = None  # 'config', 'topic', 'actions', etc.
    current_topic: Optional[AgentTopic] = None
    current_action: Optional[AgentAction] = None
    current_indent = 0
    block_indent = 0
    in_inputs_outputs = False  # Track if inside inputs:/outputs: sub-block
    io_indent = 0

    for line_num, line in enumerate(lines, 1):
        # Skip empty lines and comments
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        # Calculate indentation (tabs = 1 level, or count spaces)
        raw_indent = len(line) - len(line.lstrip())
        if '\t' in line[:raw_indent]:
            indent_level = line[:raw_indent].count('\t')
        else:
            indent_level = raw_indent // 2  # Assume 2-space indent

        # Parse config block
        if stripped.startswith('config:'):
            current_block = 'config'
            block_indent = indent_level
            continue

        if current_block == 'config' and indent_level > block_indent:
            if stripped.startswith('developer_name:'):
                structure.agent_name = extract_value(stripped)
            elif stripped.startswith('agent_name:'):
                # Legacy/alternative field name
                if not structure.agent_name:
                    structure.agent_name = extract_value(stripped)
            elif stripped.startswith('agent_label:'):
                structure.agent_label = extract_value(stripped)
            elif stripped.startswith('agent_description:'):
                structure.description = extract_value(stripped)
            elif stripped.startswith('description:'):
                if not structure.description:
                    structure.description = extract_value(stripped)

        # Parse start_agent topic
        if stripped.startswith('start_agent '):
            match = re.match(r'start_agent\s+(\w+):', stripped)
            if match:
                topic_name = match.group(1)
                current_topic = AgentTopic(name=topic_name, is_start_agent=True)
                structure.topics.append(current_topic)
                current_block = 'topic'
                block_indent = indent_level
                continue

        # Parse regular topics
        if stripped.startswith('topic ') and ':' in stripped:
            match = re.match(r'topic\s+(\w+):', stripped)
            if match:
                topic_name = match.group(1)
                current_topic = AgentTopic(name=topic_name)
                structure.topics.append(current_topic)
                current_block = 'topic'
                block_indent = indent_level
                current_action = None
                continue

        # Inside a topic
        if current_block == 'topic' and current_topic:
            if stripped.startswith('label:'):
                current_topic.label = extract_value(stripped)
            elif stripped.startswith('description:'):
                if current_action:
                    current_action.description = extract_value(stripped)
                else:
                    current_topic.description = extract_value(stripped)
            elif stripped.startswith('actions:') and indent_level == block_indent + 1:
                current_block = 'topic_actions'
                continue
            elif stripped.startswith('reasoning:'):
                current_block = 'reasoning'
                continue

        # Inside topic actions block (where flow/apex actions are defined)
        if current_block == 'topic_actions' and current_topic:
            # Check if we've exited the actions block (hit reasoning: at same or lower indent)
            if stripped.startswith('reasoning:'):
                current_block = 'reasoning'
                current_action = None
                in_inputs_outputs = False
                continue

            # Track inputs:/outputs: sub-blocks to skip field definitions
            # (e.g., "orderId: string", "orderNumber: string" are NOT action names)
            if stripped.startswith('inputs:') or stripped.startswith('outputs:'):
                in_inputs_outputs = True
                io_indent = indent_level
                continue

            # If inside inputs/outputs, skip deeper-indented lines (field defs)
            if in_inputs_outputs:
                if indent_level > io_indent:
                    continue
                else:
                    in_inputs_outputs = False

            # Check for action name definition (word followed by colon)
            skip_keywords = ('description:', 'target:', 'inp_', 'out_',
                           'instructions:', 'actions:', 'label:')
            if ':' in stripped and not stripped.startswith(skip_keywords):
                action_match = re.match(r'^(\w+):', stripped)
                if action_match:
                    action_name = action_match.group(1)
                    # Skip if this looks like a transition action (references @utils or @topic)
                    if '@utils' in stripped or '@topic' in stripped:
                        continue
                    current_action = AgentAction(name=action_name)
                    current_topic.actions.append(current_action)
                    continue

            if current_action:
                if stripped.startswith('description:'):
                    current_action.description = extract_value(stripped)
                elif stripped.startswith('target:'):
                    current_action.target = extract_value(stripped)
                elif stripped.startswith('inp_') or stripped.startswith('out_'):
                    # Legacy input/output field format (inp_fieldName, out_fieldName)
                    field_match = re.match(r'^(inp_\w+|out_\w+):', stripped)
                    if field_match:
                        field_name = field_match.group(1)
                        if field_name.startswith('inp_'):
                            current_action.inputs.append({'name': field_name})
                        else:
                            current_action.outputs.append({'name': field_name})

        # Inside reasoning block (where transitions are)
        if current_block == 'reasoning' and current_topic:
            if stripped.startswith('actions:'):
                current_block = 'reasoning_actions'
                continue

        # Parse reasoning actions (transitions)
        if current_block == 'reasoning_actions' and current_topic:
            # Look for @utils.transition to @topic.name
            transition_match = re.search(r'@utils\.transition\s+to\s+@topic\.(\w+)', stripped)
            if transition_match:
                current_topic.transitions.append(transition_match.group(1))

    return structure


def extract_value(line: str) -> str:
    """Extract the value from a 'key: value' line."""
    if ':' not in line:
        return ""

    _, value = line.split(':', 1)
    value = value.strip()

    # Remove quotes if present
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]

    return value


def generate_test_cases(structure: AgentStructure) -> List[Dict]:
    """
    Generate test cases from the parsed agent structure.

    Creates test cases for:
    1. Topic routing - one case per non-start_agent topic
    2. Transition action tests - verify start_agent routes correctly (Agent Script)
    3. Action invocation - for flow:// targets (single-utterance) AND
       apex:// targets (with conversationHistory to bypass routing)
    4. Edge cases - off-topic handling

    For Agent Script agents with start_agent routing:
    - Single-utterance tests capture the TRANSITION action (go_<topic>)
    - Business actions (apex://) require conversationHistory to pre-position
      the agent in the target topic, bypassing the start_agent routing cycle.
    """
    test_cases = []

    # Find router topic (start_agent)
    router_topic = None
    for topic in structure.topics:
        if topic.is_start_agent:
            router_topic = topic
            break

    router_name = router_topic.name if router_topic else 'topic_selector'
    has_router = router_topic is not None

    # Generate topic routing tests (with transition actions for Agent Script)
    for topic in structure.topics:
        if topic.is_start_agent:
            continue  # Don't test the router itself

        # Create utterance based on topic label/description
        utterance = generate_utterance_for_topic(topic)

        test_case = {
            'utterance': utterance,
            'expectedTopic': topic.name,
        }

        # For Agent Script with start_agent: include the transition action
        if has_router and router_topic.transitions:
            transition_action = f"go_{topic.name}"
            # Only add if this topic is in the router's transition targets
            if topic.name in router_topic.transitions:
                test_case['expectedActions'] = [transition_action]

        test_cases.append(test_case)

    # Generate action invocation tests
    for topic in structure.topics:
        if topic.is_start_agent:
            continue

        for action in topic.actions:
            if not action.target:
                continue

            if action.target.startswith('flow://'):
                # Flow actions can work in single-utterance tests
                utterance = generate_utterance_for_action(action, topic)
                test_case = {
                    'utterance': utterance,
                    'expectedTopic': topic.name,
                    'expectedActions': [action.name]
                }
                test_cases.append(test_case)

            elif action.target.startswith('apex://'):
                # Apex actions in Agent Script need conversationHistory
                # to bypass start_agent routing (which consumes the first
                # reasoning cycle on the transition action)
                utterance = generate_utterance_for_action(action, topic)
                topic_utterance = generate_utterance_for_topic(topic)

                test_case = {
                    'utterance': utterance,
                    'expectedTopic': topic.name,
                    'expectedActions': [action.name],
                    'conversationHistory': [
                        {
                            'role': 'user',
                            'message': topic_utterance,
                        },
                        {
                            'role': 'agent',
                            'topic': topic.name,
                            'message': _generate_agent_prompt(action, topic),
                        },
                    ],
                }
                test_cases.append(test_case)

    # Add edge case tests
    edge_cases = generate_edge_case_tests(router_name)
    test_cases.extend(edge_cases)

    return test_cases


def _generate_agent_prompt(action: AgentAction, topic: AgentTopic) -> str:
    """Generate a plausible agent prompt message for conversationHistory.

    This creates the agent's response that would appear before the user
    provides input for the action — establishing the topic context.
    """
    desc = action.description.lower() if action.description else action.name
    topic_label = topic.label or topic.name.replace('_', ' ')

    if 'order' in desc or 'status' in desc:
        return f"I'd be happy to help you with {topic_label.lower()}. Could you please provide the Order ID?"
    if 'account' in desc or 'lookup' in desc:
        return f"Sure, I can help with that. Could you please provide your account information?"
    if 'case' in desc or 'ticket' in desc:
        return f"I can help you create a support case. Could you describe the issue?"
    if 'search' in desc or 'find' in desc:
        return f"I can help you search. What are you looking for?"

    return f"I can help you with {topic_label.lower()}. Could you please provide the required information?"


def generate_utterance_for_topic(topic: AgentTopic) -> str:
    """Generate a test utterance that should route to this topic."""
    # Use label/description to generate appropriate utterance
    label = topic.label.lower() if topic.label else topic.name
    desc = topic.description.lower() if topic.description else ""

    # Common patterns
    if 'faq' in label or 'faq' in desc:
        return "I have a question about your services"
    if 'menu' in label or 'menu' in desc:
        return "What's on your menu?"
    if 'book' in label or 'book' in desc or 'search' in label:
        return "I'm looking for a book"
    if 'order' in label or 'order' in desc:
        return "I want to check my order status"
    if 'support' in label or 'support' in desc:
        return "I need help with an issue"
    if 'account' in label or 'account' in desc:
        return "I want to update my account"
    if 'billing' in label or 'billing' in desc or 'payment' in label:
        return "I have a question about my bill"

    # Default: use description or label
    if topic.description:
        return f"I need help with {topic.description.lower()}"
    return f"I need help with {topic.label or topic.name}"


def generate_utterance_for_action(action: AgentAction, topic: AgentTopic) -> str:
    """Generate a test utterance that should trigger this action."""
    desc = action.description.lower() if action.description else action.name

    # Extract key verbs from description
    if 'search' in desc:
        # Look for what to search for
        if 'book' in desc:
            return "Can you search for Harry Potter?"
        if 'product' in desc:
            return "Search for laptops"
        return "Can you search for something?"

    if 'create' in desc or 'add' in desc:
        if 'case' in desc or 'ticket' in desc:
            return "I need to create a support case"
        if 'order' in desc:
            return "I want to place an order"
        return f"I want to create a new {topic.name}"

    if 'get' in desc or 'lookup' in desc or 'retriev' in desc:
        if 'account' in desc:
            return "Can you look up my account information?"
        if 'order' in desc:
            return "What's the status of my order?"
        return f"Can you get the {action.name.replace('_', ' ')} for me?"

    if 'update' in desc or 'modify' in desc:
        return f"I need to update my {topic.name}"

    # Default based on action name
    return f"Please {action.name.replace('_', ' ')} for me"


def generate_edge_case_tests(router_name: str) -> List[Dict]:
    """Generate edge case test cases."""
    return [
        {
            'utterance': "What's the weather today?",
            'expectedTopic': router_name,
        },
        {
            'utterance': "Tell me a joke",
            'expectedTopic': router_name,
        }
    ]


def generate_test_spec(structure: AgentStructure, output_path: str) -> str:
    """
    Generate a YAML test spec file.

    Returns the spec content as a string.
    """
    test_cases = generate_test_cases(structure)

    spec = {
        'name': f"{structure.agent_name} Tests",
        'subjectType': 'AGENT',
        'subjectName': structure.agent_name,
        'testCases': test_cases
    }

    # Generate YAML content
    if yaml:
        content = yaml.dump(spec, default_flow_style=False, sort_keys=False, allow_unicode=True)
    else:
        content = manual_yaml_output(spec)

    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        f.write(content)

    return content


def manual_yaml_output(spec: Dict) -> str:
    """Generate YAML output without pyyaml library."""
    lines = []

    lines.append(f"name: \"{spec['name']}\"")
    lines.append(f"subjectType: {spec['subjectType']}")
    lines.append(f"subjectName: {spec['subjectName']}")
    lines.append("")
    lines.append("testCases:")

    for tc in spec['testCases']:
        lines.append(f"  - utterance: \"{tc['utterance']}\"")

        # Conversation history (for Agent Script apex:// action tests)
        history = tc.get('conversationHistory', [])
        if history:
            lines.append("    conversationHistory:")
            for entry in history:
                lines.append(f"      - role: \"{entry['role']}\"")
                lines.append(f"        message: \"{entry['message']}\"")
                if 'topic' in entry:
                    lines.append(f"        topic: \"{entry['topic']}\"")

        lines.append(f"    expectedTopic: {tc['expectedTopic']}")
        actions = tc.get('expectedActions', [])
        if actions:
            lines.append("    expectedActions:")
            for action in actions:
                lines.append(f"      - {action}")

        outcome = tc.get('expectedOutcome')
        if outcome:
            lines.append(f"    expectedOutcome: \"{outcome}\"")

        lines.append("")

    return "\n".join(lines)


def print_summary(structure: AgentStructure, test_cases: List[Dict]) -> None:
    """Print a summary of the generated test spec."""
    print("=" * 65)
    print("TEST SPEC GENERATION SUMMARY")
    print("=" * 65)
    print("")
    print(f"Agent Name: {structure.agent_name}")
    print(f"Agent Label: {structure.agent_label}")
    print(f"Topics Found: {len(structure.topics)}")
    print("")

    print("TOPICS")
    print("-" * 65)
    for topic in structure.topics:
        marker = "[START]" if topic.is_start_agent else "       "
        actions_count = len(topic.actions)
        print(f"  {marker} {topic.name}")
        print(f"           Label: {topic.label}")
        print(f"           Actions: {actions_count}")
        if topic.actions:
            for action in topic.actions:
                target_short = action.target.split('://')[-1] if action.target else 'N/A'
                print(f"              - {action.name} -> {target_short}")
    print("")

    print("TEST CASES GENERATED")
    print("-" * 65)

    # Group by category
    topic_tests = [tc for tc in test_cases if not tc.get('expectedActions')]
    action_tests = [tc for tc in test_cases if tc.get('expectedActions')]

    print(f"  Topic Routing Tests: {len(topic_tests)}")
    print(f"  Action Invocation Tests: {len(action_tests)}")
    print(f"  Total: {len(test_cases)}")
    print("")

    print("TEST CASES")
    print("-" * 65)
    for i, tc in enumerate(test_cases, 1):
        utterance = tc['utterance'][:50] + "..." if len(tc['utterance']) > 50 else tc['utterance']
        topic = tc['expectedTopic']
        actions = tc.get('expectedActions', [])
        action_str = f" -> {actions}" if actions else ""
        print(f"  {i}. \"{utterance}\"")
        print(f"     Expected: {topic}{action_str}")
    print("")
    print("=" * 65)


def main():
    parser = argparse.ArgumentParser(
        description='Generate Agentforce test specs from Agent Script files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 generate-test-spec.py --agent-file Agent.agent --output tests/spec.yaml
  python3 generate-test-spec.py --agent-dir ./aiAuthoringBundles/MyAgent/ --output spec.yaml
  python3 generate-test-spec.py --agent-file Agent.agent --output spec.yaml --verbose
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--agent-file', type=str, help='Path to .agent file')
    group.add_argument('--agent-dir', type=str, help='Path to aiAuthoringBundle directory')

    parser.add_argument('--output', '-o', type=str, required=True, help='Output YAML file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Print detailed summary')

    args = parser.parse_args()

    # Find .agent file
    if args.agent_file:
        agent_file = Path(args.agent_file)
    else:
        agent_dir = Path(args.agent_dir)
        agent_files = list(agent_dir.glob('*.agent'))
        if not agent_files:
            print(f"Error: No .agent file found in {agent_dir}", file=sys.stderr)
            sys.exit(1)
        agent_file = agent_files[0]

    if not agent_file.exists():
        print(f"Error: Agent file not found: {agent_file}", file=sys.stderr)
        sys.exit(1)

    # Parse agent file
    print(f"Parsing: {agent_file}")
    structure = parse_agent_file(str(agent_file))

    if not structure.agent_name:
        print("Warning: Could not extract agent_name from file", file=sys.stderr)
        structure.agent_name = agent_file.stem

    # Generate test spec
    content = generate_test_spec(structure, args.output)

    # Print summary
    if args.verbose:
        test_cases = generate_test_cases(structure)
        print_summary(structure, test_cases)
    else:
        test_cases = generate_test_cases(structure)
        print(f"Generated {len(test_cases)} test cases")
        print(f"Output: {args.output}")

    print("\nNext steps:")
    print(f"  1. Review: cat {args.output}")
    print(f"  2. Create test: sf agent test create --spec {args.output} --api-name {structure.agent_name}_Tests --target-org [alias]")
    print(f"  3. Run tests: sf agent test run --api-name {structure.agent_name}_Tests --wait 10 --result-format json --target-org [alias]")


if __name__ == "__main__":
    main()
