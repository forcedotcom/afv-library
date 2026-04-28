#!/usr/bin/env python3
"""
Code Analyzer Scanner - Core wrapper for Salesforce Code Analyzer V5 CLI.

Provides a Python interface to the `sf code-analyzer run` command with:
- Skill-type-aware rule selection
- Graceful dependency handling
- JSON output parsing
- Configurable timeout and options

Usage:
    scanner = CodeAnalyzerScanner()
    result = scanner.scan("/path/to/file.cls", SkillType.APEX)

    for violation in result.violations:
        print(f"{violation['severity_label']}: {violation['message']}")
"""

import subprocess
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from .dependency_checker import DependencyChecker


class SkillType(Enum):
    """Skill types for rule selection."""
    APEX = "apex"
    FLOW = "flow"
    LWC = "lwc"
    METADATA = "metadata"


@dataclass
class ScanResult:
    """Normalized scan result from Code Analyzer."""
    success: bool
    violations: List[Dict[str, Any]]
    engines_used: List[str]
    engines_unavailable: List[str]
    violation_counts: Dict[str, int]
    raw_output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    scan_time_ms: int = 0


class CodeAnalyzerScanner:
    """
    Wrapper for Salesforce Code Analyzer V5.

    Handles:
    - Rule selection based on skill type
    - Dependency checking and graceful degradation
    - CLI invocation with proper arguments
    - Output parsing and normalization

    Usage:
        scanner = CodeAnalyzerScanner()

        # Check what's available
        print(scanner.get_available_engines())

        # Scan a file
        result = scanner.scan("/path/to/AccountService.cls", SkillType.APEX)

        if result.success:
            for v in result.violations:
                print(f"[{v['severity_label']}] {v['rule']}: {v['message']}")
    """

    # Rule selectors by skill type
    # Format: engine:category or engine:tag:severity
    RULE_SELECTORS = {
        SkillType.APEX: [
            "pmd",            # All PMD Apex rules
            "regex",          # Regex patterns
            "cpd",            # Copy-paste detection
            "sfge",           # Graph engine (data flow)
        ],
        SkillType.FLOW: [
            "flow",           # Flow Scanner rules
            "regex",          # Regex XML patterns
        ],
        SkillType.LWC: [
            "eslint",         # ESLint LWC rules
            "retire-js",      # Vulnerability scanning
        ],
        SkillType.METADATA: [
            "regex",          # Regex patterns for XML
        ],
    }

    # File extensions by skill type
    FILE_EXTENSIONS = {
        SkillType.APEX: [".cls", ".trigger"],
        SkillType.FLOW: [".flow-meta.xml"],
        SkillType.LWC: [".js", ".html", ".css"],
        SkillType.METADATA: [".xml"],
    }

    # Severity labels
    SEVERITY_LABELS = {
        1: "CRITICAL",
        2: "HIGH",
        3: "MODERATE",
        4: "LOW",
        5: "INFO",
    }

    def __init__(
        self,
        config_path: Optional[str] = None,
        timeout_seconds: int = 120,
    ):
        """
        Initialize scanner.

        Args:
            config_path: Path to code-analyzer.yml config file.
                        If None, looks in shared/code-analyzer/config/
            timeout_seconds: Maximum time for scan (default 120s)
        """
        self.config_path = config_path or self._find_config()
        self.timeout_seconds = timeout_seconds
        self._dep_checker = DependencyChecker()
        self._engine_availability = None
        self._java_env = self._get_java_env()

    def _get_java_env(self) -> Dict[str, str]:
        """
        Get environment variables needed for Java.

        If Java is found at a non-standard location (e.g., Homebrew),
        returns env vars to help sf CLI find it.
        """
        java_status = self._dep_checker.check_java()
        if not java_status.available or not java_status.path:
            return {}

        java_path = java_status.path
        # Get JAVA_HOME from the java binary path (bin/java -> parent -> parent)
        java_bin_dir = os.path.dirname(java_path)  # /path/to/jdk/bin
        java_home = os.path.dirname(java_bin_dir)   # /path/to/jdk

        env = os.environ.copy()
        env["JAVA_HOME"] = java_home
        # Prepend Java bin dir to PATH
        env["PATH"] = f"{java_bin_dir}:{env.get('PATH', '')}"
        return env

    def _find_config(self) -> Optional[str]:
        """Find shared config file."""
        # Look relative to this module
        module_dir = Path(__file__).parent
        config = module_dir / "config" / "code-analyzer.yml"

        if config.exists():
            return str(config)

        # Also try code-analyzer.yaml
        config_yaml = module_dir / "config" / "code-analyzer.yaml"
        if config_yaml.exists():
            return str(config_yaml)

        return None

    def get_available_engines(self) -> List[str]:
        """Get list of available engine names."""
        return self._dep_checker.get_available_engines()

    def get_unavailable_engines(self) -> List[tuple]:
        """Get list of unavailable engines with reasons."""
        return self._dep_checker.get_unavailable_engines()

    def check_dependencies(self) -> Dict[str, bool]:
        """
        Check which dependencies are available.

        Returns:
            Dict mapping dependency name to availability status
        """
        deps = self._dep_checker.check_all()
        return {name: status.available for name, status in deps.items()}

    def is_available(self) -> bool:
        """Check if Code Analyzer is available at all."""
        deps = self.check_dependencies()
        return deps.get("sf_cli", False)

    def scan(
        self,
        file_path: str,
        skill_type: SkillType,
        additional_rules: Optional[List[str]] = None,
        severity_threshold: Optional[int] = None,
    ) -> ScanResult:
        """
        Scan a file using Code Analyzer.

        Args:
            file_path: Path to file to scan
            skill_type: Type of skill (determines rule selection)
            additional_rules: Additional rule selectors to include
            severity_threshold: Only return violations >= this severity (1-5)

        Returns:
            ScanResult with violations and metadata
        """
        # Validate file exists
        if not os.path.exists(file_path):
            return ScanResult(
                success=False,
                violations=[],
                engines_used=[],
                engines_unavailable=[],
                violation_counts={},
                error_message=f"File not found: {file_path}",
            )

        # Check if sf CLI is available
        if not self.is_available():
            return ScanResult(
                success=False,
                violations=[],
                engines_used=[],
                engines_unavailable=["all"],
                violation_counts={},
                error_message="Salesforce CLI with Code Analyzer not available",
            )

        # Get rule selectors for this skill type
        rule_selectors = list(self.RULE_SELECTORS.get(skill_type, []))
        if additional_rules:
            rule_selectors.extend(additional_rules)

        # Filter to available engines only
        available = set(self.get_available_engines())
        unavailable_engines = []

        filtered_selectors = []
        for selector in rule_selectors:
            # Extract engine name from selector (before first :)
            engine = selector.split(":")[0] if ":" in selector else selector
            if engine in available:
                filtered_selectors.append(selector)
            else:
                if engine not in [e for e, _ in unavailable_engines]:
                    unavailable_engines.append((engine, f"Missing dependencies"))

        if not filtered_selectors:
            return ScanResult(
                success=True,
                violations=[],
                engines_used=[],
                engines_unavailable=[e for e, _ in unavailable_engines],
                violation_counts={"total": 0},
                error_message="No engines available for this skill type",
            )

        # Create temp file for JSON output
        with tempfile.NamedTemporaryFile(
            suffix=".json",
            delete=False,
            mode="w"
        ) as f:
            output_file = f.name

        try:
            # Build command
            cmd = [
                "sf", "code-analyzer", "run",
                "--target", file_path,
                "--output-file", output_file,
            ]

            # Add config file if available
            if self.config_path and os.path.exists(self.config_path):
                cmd.extend(["--config-file", self.config_path])

            # Add rule selectors
            for selector in filtered_selectors:
                cmd.extend(["--rule-selector", selector])

            # Add severity threshold if specified
            if severity_threshold:
                cmd.extend(["--severity-threshold", str(severity_threshold)])

            # Run scanner
            import time
            start_time = time.time()

            # Use Java environment if available (for Homebrew/non-standard Java paths)
            env = self._java_env if self._java_env else None

            # Run from the file's directory so code-analyzer resolves
            # the workspace correctly (it defaults to CWD).
            scan_cwd = os.path.dirname(os.path.abspath(file_path)) or None

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                env=env,
                cwd=scan_cwd
            )

            scan_time = int((time.time() - start_time) * 1000)

            # Parse output
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                with open(output_file, "r") as f:
                    raw_output = json.load(f)

                return self._parse_output(
                    raw_output,
                    [e for e, _ in unavailable_engines],
                    scan_time
                )
            else:
                # No output file - might be an error
                error_msg = result.stderr.strip() if result.stderr else "No output generated"
                return ScanResult(
                    success=False,
                    violations=[],
                    engines_used=[],
                    engines_unavailable=[e for e, _ in unavailable_engines],
                    violation_counts={},
                    error_message=error_msg,
                    scan_time_ms=scan_time,
                )

        except subprocess.TimeoutExpired:
            return ScanResult(
                success=False,
                violations=[],
                engines_used=[],
                engines_unavailable=[e for e, _ in unavailable_engines],
                violation_counts={"timeout": 1},
                error_message=f"Scan timed out after {self.timeout_seconds}s",
            )
        except FileNotFoundError:
            return ScanResult(
                success=False,
                violations=[],
                engines_used=[],
                engines_unavailable=["all"],
                violation_counts={"error": 1},
                error_message="sf CLI not found - install Salesforce CLI",
            )
        except json.JSONDecodeError as e:
            return ScanResult(
                success=False,
                violations=[],
                engines_used=[],
                engines_unavailable=[e for e, _ in unavailable_engines],
                violation_counts={"error": 1},
                error_message=f"Failed to parse scanner output: {e}",
            )
        except Exception as e:
            return ScanResult(
                success=False,
                violations=[],
                engines_used=[],
                engines_unavailable=[],
                violation_counts={"error": 1},
                error_message=f"Scanner error: {e}",
            )
        finally:
            # Cleanup temp file
            if os.path.exists(output_file):
                try:
                    os.unlink(output_file)
                except Exception:
                    pass

    def _parse_output(
        self,
        raw_output: Dict[str, Any],
        unavailable_engines: List[str],
        scan_time_ms: int,
    ) -> ScanResult:
        """Parse Code Analyzer JSON output into normalized format."""
        violations = []
        engines_used = set()

        for violation in raw_output.get("violations", []):
            engine = violation.get("engine", "unknown")

            # Skip engine errors (not actual code violations)
            # These include: UninstantiableEngineError, UnexpectedEngineError, etc.
            rule = violation.get("rule", "")
            if "Error" in rule and "Engine" in rule:
                continue

            engines_used.add(engine)

            # Get primary location
            locations = violation.get("locations", [])
            primary_idx = violation.get("primaryLocationIndex", 0)
            primary_loc = locations[primary_idx] if locations and primary_idx < len(locations) else {}

            # Get severity
            severity = violation.get("severity", 5)
            severity_label = self.SEVERITY_LABELS.get(severity, "UNKNOWN")

            # Normalize violation
            violations.append({
                "rule": rule,
                "engine": engine,
                "severity": severity,
                "severity_label": severity_label,
                "message": violation.get("message", ""),
                "file": primary_loc.get("file", ""),
                "line": primary_loc.get("startLine", 0),
                "end_line": primary_loc.get("endLine", 0),
                "column": primary_loc.get("startColumn", 0),
                "end_column": primary_loc.get("endColumn", 0),
                "tags": violation.get("tags", []),
                "resources": violation.get("resources", []),
            })

        return ScanResult(
            success=True,
            violations=violations,
            engines_used=list(engines_used),
            engines_unavailable=unavailable_engines,
            violation_counts=raw_output.get("violationCounts", {}),
            raw_output=raw_output,
            scan_time_ms=scan_time_ms,
        )

    def scan_directory(
        self,
        directory: str,
        skill_type: SkillType,
        recursive: bool = True,
    ) -> ScanResult:
        """
        Scan all files in a directory matching the skill type.

        Args:
            directory: Directory path to scan
            skill_type: Type of skill (determines file extensions and rules)
            recursive: Whether to scan subdirectories

        Returns:
            ScanResult with combined violations
        """
        if not os.path.isdir(directory):
            return ScanResult(
                success=False,
                violations=[],
                engines_used=[],
                engines_unavailable=[],
                violation_counts={},
                error_message=f"Directory not found: {directory}",
            )

        # Find files matching skill type
        extensions = self.FILE_EXTENSIONS.get(skill_type, [])
        files_to_scan = []

        if recursive:
            for root, _, files in os.walk(directory):
                for file in files:
                    if any(file.endswith(ext) for ext in extensions):
                        files_to_scan.append(os.path.join(root, file))
        else:
            for file in os.listdir(directory):
                if any(file.endswith(ext) for ext in extensions):
                    files_to_scan.append(os.path.join(directory, file))

        if not files_to_scan:
            return ScanResult(
                success=True,
                violations=[],
                engines_used=[],
                engines_unavailable=[],
                violation_counts={"total": 0},
            )

        # Scan directory directly (more efficient than file by file)
        return self.scan(directory, skill_type)


def get_skill_type_for_file(file_path: str) -> Optional[SkillType]:
    """
    Determine skill type based on file extension.

    Args:
        file_path: Path to file

    Returns:
        SkillType or None if unknown
    """
    file_lower = file_path.lower()

    if file_lower.endswith(".cls") or file_lower.endswith(".trigger"):
        return SkillType.APEX
    elif file_lower.endswith(".flow-meta.xml"):
        return SkillType.FLOW
    elif file_lower.endswith(".js") or file_lower.endswith(".html"):
        return SkillType.LWC
    elif file_lower.endswith("-meta.xml"):
        return SkillType.METADATA

    return None


if __name__ == "__main__":
    # Demo when run directly
    import sys

    scanner = CodeAnalyzerScanner()

    print("Code Analyzer Scanner Status")
    print("=" * 40)
    print(f"Available: {scanner.is_available()}")
    print(f"Config: {scanner.config_path or 'Not found'}")
    print()

    deps = scanner.check_dependencies()
    print("Dependencies:")
    for dep, available in deps.items():
        status = "" if available else ""
        print(f"  {status} {dep}")

    print()
    print("Available engines:", scanner.get_available_engines())

    unavailable = scanner.get_unavailable_engines()
    if unavailable:
        print("Unavailable engines:")
        for engine, reason in unavailable:
            print(f"  - {engine}: {reason}")

    # If file provided, scan it
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        skill_type = get_skill_type_for_file(file_path)

        if skill_type:
            print(f"\nScanning {file_path} as {skill_type.value}...")
            result = scanner.scan(file_path, skill_type)

            print(f"Success: {result.success}")
            print(f"Engines used: {result.engines_used}")
            print(f"Violations: {len(result.violations)}")

            for v in result.violations[:10]:
                print(f"  [{v['severity_label']}] {v['rule']}: {v['message'][:60]}")
        else:
            print(f"\nUnknown file type: {file_path}")
