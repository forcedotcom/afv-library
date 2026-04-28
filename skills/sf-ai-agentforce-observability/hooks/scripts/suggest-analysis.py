#!/usr/bin/env python3
"""
PostToolUse hook: Suggest relevant Polars analysis based on extraction results.

After extracting STDM data, suggests appropriate analysis commands
based on the data volume and patterns found.

Usage (called automatically by hook system):
    Receives tool result via stdin, outputs suggestions to stdout.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional


def analyze_extraction_and_suggest(data_dir: str) -> List[str]:
    """
    Analyze extracted data and suggest relevant analysis commands.

    Args:
        data_dir: Path to extraction directory

    Returns:
        List of suggested commands/actions
    """
    suggestions = []
    path = Path(data_dir)

    if not path.exists():
        return suggestions

    # Check metadata for extraction info
    metadata_file = path / "metadata" / "extraction.json"
    if metadata_file.exists():
        with open(metadata_file) as f:
            metadata = json.load(f)

        results = metadata.get("results", {})

        # Suggest based on record counts
        session_count = results.get("sessions_count", 0)
        interaction_count = results.get("interactions_count", 0)
        step_count = results.get("steps_count", 0)

        if session_count > 0:
            suggestions.append(
                f"📊 **Session Summary**: Run `python3 scripts/cli.py analyze --data-dir {data_dir}` "
                f"to see summary statistics for {session_count} sessions"
            )

        if session_count > 100:
            suggestions.append(
                "📈 **Trend Analysis**: Consider analyzing sessions by date with "
                "`analyzer.sessions_by_date()` to identify patterns"
            )

        if interaction_count > 0 and step_count > 0:
            suggestions.append(
                "🎯 **Topic Analysis**: Run `python3 scripts/cli.py topics --data-dir {data_dir}` "
                "to see which topics are handling the most conversations"
            )

            suggestions.append(
                "⚡ **Action Analysis**: Run `python3 scripts/cli.py actions --data-dir {data_dir}` "
                "to see most frequently used actions"
            )

        # Check for failed sessions
        if session_count > 0:
            suggestions.append(
                "❌ **Failed Sessions**: Use `analyzer.find_failed_sessions()` "
                "to identify sessions that ended with escalation or abandonment"
            )

    # Check for specific session IDs in extraction
    sessions_dir = path / "sessions"
    if sessions_dir.exists():
        try:
            import pyarrow.parquet as pq
            parquet_files = list(sessions_dir.glob("**/*.parquet"))
            if parquet_files:
                table = pq.read_table(parquet_files[0], columns=["ssot__Id__c"])
                sample_ids = table.column("ssot__Id__c").to_pylist()[:3]
                if sample_ids:
                    suggestions.append(
                        f"🔍 **Debug Session**: To investigate a specific session, run:\n"
                        f"   `python3 scripts/cli.py debug-session --data-dir {data_dir} "
                        f"--session-id \"{sample_ids[0]}\"`"
                    )
        except ImportError:
            pass
        except Exception:
            pass

    return suggestions


def suggest_next_skills(data_dir: str) -> List[str]:
    """
    Suggest related skills based on analysis findings.

    Args:
        data_dir: Path to extraction directory

    Returns:
        List of skill suggestions
    """
    suggestions = []
    path = Path(data_dir)

    if not path.exists():
        return suggestions

    # Always suggest testing after observability
    suggestions.append(
        "🧪 **Create Tests**: Use `Skill(skill=\"sf-ai-agentforce-testing\")` "
        "to create test cases based on observed patterns"
    )

    # Suggest agent script fixes if needed
    suggestions.append(
        "🔧 **Fix Issues**: If you find topic routing issues, use "
        "`Skill(skill=\"sf-ai-agentscript\")` to improve agent definitions"
    )

    return suggestions


def format_suggestions(analysis_suggestions: List[str], skill_suggestions: List[str]) -> str:
    """Format all suggestions for display."""
    lines = []

    if analysis_suggestions:
        lines.append("\n💡 **Suggested Analysis:**")
        for suggestion in analysis_suggestions:
            lines.append(f"\n{suggestion}")

    if skill_suggestions:
        lines.append("\n\n🔗 **Related Skills:**")
        for suggestion in skill_suggestions:
            lines.append(f"\n{suggestion}")

    return "\n".join(lines) if lines else ""


def extract_data_dir_from_tool_result(tool_result: Dict[str, Any]) -> Optional[str]:
    """Extract data directory path from tool result."""
    # Check for output directory in command
    output = tool_result.get("output", "")
    if isinstance(output, str):
        # Look for output directory mentions
        import re
        dir_match = re.search(r'Output:\s*(/[^\s]+|\.\/[^\s]+)', output)
        if dir_match:
            return dir_match.group(1)

        # Look for stdm_data pattern
        dir_match = re.search(r'(/[^\s]+/stdm_data|/[^\s]+/stdm_debug|\.\/stdm_data|\.\/stdm_debug)', output)
        if dir_match:
            return dir_match.group(1)

    return None


def main():
    """Main hook entry point."""
    # Read tool result from stdin
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            sys.exit(0)

        tool_result = json.loads(input_data)
    except json.JSONDecodeError:
        sys.exit(0)

    # Extract data directory from tool result
    data_dir = extract_data_dir_from_tool_result(tool_result)

    if not data_dir:
        # Try common default paths
        for default in ["./stdm_data", "./stdm_debug"]:
            if Path(default).exists():
                data_dir = default
                break

    if not data_dir or not Path(data_dir).exists():
        sys.exit(0)

    # Generate suggestions
    analysis_suggestions = analyze_extraction_and_suggest(data_dir)
    skill_suggestions = suggest_next_skills(data_dir)

    # Only output if we have suggestions
    output = format_suggestions(analysis_suggestions, skill_suggestions)
    if output:
        print(output)


if __name__ == "__main__":
    main()
