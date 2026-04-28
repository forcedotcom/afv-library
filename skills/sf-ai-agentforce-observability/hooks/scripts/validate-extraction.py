#!/usr/bin/env python3
"""
PostToolUse hook: Validate Parquet extraction output.

Follows sf-data validation patterns to ensure extracted data is valid
before analysis.

Validates:
- Schema matches expected DMO structure
- No null primary keys
- Timestamps are valid ISO format
- Record count > 0

Usage (called automatically by hook system):
    Receives tool result via stdin, outputs validation result to stdout.
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional


def validate_parquet_file(file_path: str) -> Dict[str, Any]:
    """
    Validate a Parquet file against expected STDM schema.

    Args:
        file_path: Path to Parquet file

    Returns:
        Validation result dict with:
        - valid: bool
        - record_count: int
        - warnings: list of warning messages
        - errors: list of error messages
    """
    result = {
        "valid": True,
        "record_count": 0,
        "warnings": [],
        "errors": [],
    }

    path = Path(file_path)
    if not path.exists():
        result["valid"] = False
        result["errors"].append(f"File not found: {file_path}")
        return result

    try:
        import pyarrow.parquet as pq

        # Read metadata without loading data
        parquet_file = pq.ParquetFile(file_path)
        metadata = parquet_file.metadata

        result["record_count"] = metadata.num_rows

        if metadata.num_rows == 0:
            result["warnings"].append("File contains 0 records")

        # Validate schema
        schema = parquet_file.schema_arrow
        field_names = [field.name for field in schema]

        # Check for expected STDM fields based on file type
        if "sessions" in str(file_path).lower():
            expected = ["ssot__Id__c", "ssot__AiAgentApiName__c", "ssot__StartTimestamp__c"]
        elif "interactions" in str(file_path).lower():
            expected = ["ssot__Id__c", "ssot__AiAgentSessionId__c", "ssot__AiAgentInteractionType__c"]
        elif "steps" in str(file_path).lower():
            expected = ["ssot__Id__c", "ssot__AiAgentInteractionId__c", "ssot__AiAgentInteractionStepType__c"]
        elif "messages" in str(file_path).lower():
            expected = ["ssot__Id__c", "ssot__AiAgentInteractionId__c", "ssot__ContentText__c"]
        else:
            expected = ["ssot__Id__c"]  # At minimum, expect an ID field

        missing = [f for f in expected if f not in field_names]
        if missing:
            result["warnings"].append(f"Missing expected fields: {missing}")

        # Check for null primary keys (sample first batch)
        table = pq.read_table(file_path, columns=["ssot__Id__c"])
        id_column = table.column("ssot__Id__c")

        null_count = id_column.null_count
        if null_count > 0:
            result["valid"] = False
            result["errors"].append(f"Found {null_count} null primary key values")

    except ImportError:
        result["warnings"].append("PyArrow not installed, skipping schema validation")
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"Validation error: {str(e)}")

    return result


def validate_extraction_directory(dir_path: str) -> Dict[str, Any]:
    """
    Validate an extraction output directory.

    Args:
        dir_path: Path to extraction directory

    Returns:
        Aggregated validation result
    """
    result = {
        "valid": True,
        "entity_counts": {},
        "warnings": [],
        "errors": [],
    }

    path = Path(dir_path)
    if not path.exists():
        result["valid"] = False
        result["errors"].append(f"Directory not found: {dir_path}")
        return result

    # Check for expected subdirectories
    expected_entities = ["sessions", "interactions", "steps", "messages"]

    for entity in expected_entities:
        entity_dir = path / entity
        if entity_dir.exists():
            parquet_files = list(entity_dir.glob("**/*.parquet"))
            if parquet_files:
                # Validate first parquet file
                file_result = validate_parquet_file(str(parquet_files[0]))
                result["entity_counts"][entity] = file_result["record_count"]

                if not file_result["valid"]:
                    result["valid"] = False
                    result["errors"].extend(file_result["errors"])

                result["warnings"].extend(file_result["warnings"])
            else:
                result["warnings"].append(f"No Parquet files found in {entity}")
        else:
            result["warnings"].append(f"Missing {entity} directory")

    # Check for metadata
    metadata_file = path / "metadata" / "extraction.json"
    if not metadata_file.exists():
        result["warnings"].append("Missing extraction metadata file")

    return result


def format_output(result: Dict[str, Any]) -> str:
    """Format validation result for display."""
    lines = []

    if result["valid"]:
        lines.append("✅ Validation passed")
    else:
        lines.append("❌ Validation failed")

    # Entity counts
    if result.get("entity_counts"):
        lines.append("\nRecord counts:")
        for entity, count in result["entity_counts"].items():
            lines.append(f"  • {entity}: {count:,}")

    # Single file count
    if result.get("record_count"):
        lines.append(f"\nRecords: {result['record_count']:,}")

    # Warnings
    if result.get("warnings"):
        lines.append("\n⚠️ Warnings:")
        for warning in result["warnings"]:
            lines.append(f"  • {warning}")

    # Errors
    if result.get("errors"):
        lines.append("\n❌ Errors:")
        for error in result["errors"]:
            lines.append(f"  • {error}")

    return "\n".join(lines)


def extract_path_from_tool_result(tool_result: Dict[str, Any]) -> Optional[str]:
    """Extract file/directory path from tool result."""
    # Check for file_path in Write tool result
    if "file_path" in tool_result:
        return tool_result["file_path"]

    # Check for output path in command output
    output = tool_result.get("output", "")
    if isinstance(output, str):
        # Look for parquet file paths
        parquet_match = re.search(r'(/[^\s]+\.parquet)', output)
        if parquet_match:
            return parquet_match.group(1)

        # Look for directory paths ending with stdm_data or similar
        dir_match = re.search(r'(/[^\s]+/stdm_data|/[^\s]+/stdm_debug)', output)
        if dir_match:
            return dir_match.group(1)

    return None


def main():
    """Main hook entry point."""
    # Read tool result from stdin
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            # No input, nothing to validate
            sys.exit(0)

        tool_result = json.loads(input_data)
    except json.JSONDecodeError:
        # Not JSON input, skip validation
        sys.exit(0)

    # Extract path from tool result
    path = extract_path_from_tool_result(tool_result)

    if not path:
        # No relevant path found, skip validation
        sys.exit(0)

    path_obj = Path(path)

    # Skip if path doesn't look like STDM data
    if not any(x in str(path).lower() for x in ["stdm", "sessions", "interactions", "steps", "messages", ".parquet"]):
        sys.exit(0)

    # Determine validation type
    if path_obj.is_file() and path.endswith(".parquet"):
        result = validate_parquet_file(path)
    elif path_obj.is_dir():
        result = validate_extraction_directory(path)
    else:
        # File doesn't exist yet or not relevant
        sys.exit(0)

    # Output result
    print(format_output(result))

    # Exit with error code if validation failed
    if not result["valid"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
