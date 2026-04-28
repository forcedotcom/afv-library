#!/usr/bin/env python3
"""
Dependency Checker for Salesforce Code Analyzer V5.

Detects availability of runtime dependencies required by different CA engines:
- JDK 11+ (PMD, CPD, SFGE)
- Node.js (ESLint, RetireJS)
- Python 3.10+ (Flow Scanner)
- sf CLI with code-analyzer plugin

Provides graceful degradation information when dependencies are missing.
"""

import subprocess
import re
import sys
import shutil
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from functools import lru_cache


@dataclass
class DependencyStatus:
    """Status of a single dependency."""
    name: str
    available: bool
    version: Optional[str] = None
    path: Optional[str] = None
    error: Optional[str] = None
    install_hint: Optional[str] = None


@dataclass
class EngineAvailability:
    """Availability status for CA engines."""
    engine: str
    available: bool
    reason: Optional[str] = None
    dependencies: List[str] = None


class DependencyChecker:
    """
    Checks and caches dependency availability for Code Analyzer engines.

    Usage:
        checker = DependencyChecker()

        # Check specific dependency
        java_status = checker.check_java()

        # Get all engine availability
        engines = checker.get_engine_availability()

        # Get user-friendly message
        message = checker.get_availability_message()
    """

    # Engine -> Required dependencies mapping
    ENGINE_DEPENDENCIES = {
        "pmd": ["java", "sf_cli"],
        "cpd": ["java", "sf_cli"],
        "sfge": ["java", "sf_cli"],
        "eslint": ["node", "sf_cli"],
        "retire-js": ["node", "sf_cli"],
        "flow": ["python", "sf_cli"],
        "regex": ["sf_cli"],  # Regex only needs sf CLI
    }

    # Install hints for each dependency
    INSTALL_HINTS = {
        "java": {
            "darwin": "brew install openjdk@11",
            "linux": "sudo apt install openjdk-11-jdk",
            "win32": "Download from https://adoptium.net/",
        },
        "node": {
            "darwin": "brew install node",
            "linux": "sudo apt install nodejs npm",
            "win32": "Download from https://nodejs.org/",
        },
        "python": {
            "darwin": "brew install python@3.10",
            "linux": "sudo apt install python3.10",
            "win32": "Download from https://python.org/",
        },
        "sf_cli": {
            "all": "npm install -g @salesforce/cli && sf plugins install @salesforce/sfdx-code-analyzer",
        },
    }

    def __init__(self):
        """Initialize dependency checker."""
        self._cache: Dict[str, DependencyStatus] = {}

    def clear_cache(self):
        """Clear the dependency cache (useful for re-checking)."""
        self._cache.clear()

    # Common Java installation paths to check as fallback
    JAVA_PATHS = [
        # Homebrew on Apple Silicon
        "/opt/homebrew/opt/openjdk@11/bin/java",
        "/opt/homebrew/opt/openjdk@17/bin/java",
        "/opt/homebrew/opt/openjdk@21/bin/java",
        "/opt/homebrew/opt/openjdk/bin/java",
        # Homebrew on Intel Mac
        "/usr/local/opt/openjdk@11/bin/java",
        "/usr/local/opt/openjdk@17/bin/java",
        "/usr/local/opt/openjdk@21/bin/java",
        "/usr/local/opt/openjdk/bin/java",
        # Standard macOS/Linux locations
        "/usr/bin/java",
        "/usr/local/bin/java",
    ]

    def _try_java_at_path(self, java_path: str) -> Optional[DependencyStatus]:
        """
        Try to get Java version from a specific path.

        Returns:
            DependencyStatus if valid Java found, None otherwise
        """
        import os
        if not os.path.exists(java_path):
            return None

        try:
            result = subprocess.run(
                [java_path, "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Java outputs version to stderr
            output = result.stderr.lower()

            # Parse version (e.g., "openjdk version \"11.0.2\"" or "java version \"17.0.1\"")
            version_match = re.search(r'version\s*["\']?(\d+)(?:\.(\d+))?', output)

            if version_match:
                major = int(version_match.group(1))
                version_str = version_match.group(0)

                if major >= 11:
                    return DependencyStatus(
                        name="Java (JDK 11+)",
                        available=True,
                        version=version_str,
                        path=java_path,
                    )
        except Exception:
            pass

        return None

    def check_java(self) -> DependencyStatus:
        """
        Check if JDK 11+ is available.

        Checks multiple locations including Homebrew paths to handle
        wrapper scripts that may intercept the default java command.

        Returns:
            DependencyStatus with version info if available
        """
        if "java" in self._cache:
            return self._cache["java"]

        # First, try JAVA_HOME if set
        import os
        java_home = os.environ.get("JAVA_HOME")
        if java_home:
            java_path = os.path.join(java_home, "bin", "java")
            status = self._try_java_at_path(java_path)
            if status:
                self._cache["java"] = status
                return status

        # Try default PATH java
        java_path = shutil.which("java")
        if java_path:
            status = self._try_java_at_path(java_path)
            if status:
                self._cache["java"] = status
                return status

        # Try common installation paths (Homebrew, etc.)
        for fallback_path in self.JAVA_PATHS:
            status = self._try_java_at_path(fallback_path)
            if status:
                self._cache["java"] = status
                return status

        # No valid Java found
        status = DependencyStatus(
            name="Java (JDK 11+)",
            available=False,
            error="JDK 11+ not found in PATH or common locations",
            install_hint=self._get_install_hint("java"),
        )
        self._cache["java"] = status
        return status

    def check_node(self) -> DependencyStatus:
        """
        Check if Node.js is available.

        Returns:
            DependencyStatus with version info if available
        """
        if "node" in self._cache:
            return self._cache["node"]

        try:
            node_path = shutil.which("node")
            if not node_path:
                status = DependencyStatus(
                    name="Node.js",
                    available=False,
                    error="node command not found in PATH",
                    install_hint=self._get_install_hint("node"),
                )
                self._cache["node"] = status
                return status

            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                status = DependencyStatus(
                    name="Node.js",
                    available=True,
                    version=version,
                    path=node_path,
                )
            else:
                status = DependencyStatus(
                    name="Node.js",
                    available=False,
                    error=result.stderr.strip() or "Unknown error",
                    install_hint=self._get_install_hint("node"),
                )

            self._cache["node"] = status
            return status

        except subprocess.TimeoutExpired:
            status = DependencyStatus(
                name="Node.js",
                available=False,
                error="node --version timed out",
                install_hint=self._get_install_hint("node"),
            )
            self._cache["node"] = status
            return status
        except Exception as e:
            status = DependencyStatus(
                name="Node.js",
                available=False,
                error=str(e),
                install_hint=self._get_install_hint("node"),
            )
            self._cache["node"] = status
            return status

    def check_python(self) -> DependencyStatus:
        """
        Check if Python 3.10+ is available.

        Returns:
            DependencyStatus with version info if available
        """
        if "python" in self._cache:
            return self._cache["python"]

        # If we're running, Python is available - check version
        major = sys.version_info.major
        minor = sys.version_info.minor
        version = f"{major}.{minor}.{sys.version_info.micro}"

        if major >= 3 and minor >= 10:
            status = DependencyStatus(
                name="Python 3.10+",
                available=True,
                version=version,
                path=sys.executable,
            )
        else:
            status = DependencyStatus(
                name="Python 3.10+",
                available=False,
                version=version,
                path=sys.executable,
                error=f"Python {major}.{minor} found, but 3.10+ required for Flow Scanner",
                install_hint=self._get_install_hint("python"),
            )

        self._cache["python"] = status
        return status

    def check_sf_cli(self) -> DependencyStatus:
        """
        Check if Salesforce CLI with code-analyzer plugin is available.

        Returns:
            DependencyStatus with version info if available
        """
        if "sf_cli" in self._cache:
            return self._cache["sf_cli"]

        try:
            sf_path = shutil.which("sf")
            if not sf_path:
                status = DependencyStatus(
                    name="Salesforce CLI",
                    available=False,
                    error="sf command not found in PATH",
                    install_hint=self._get_install_hint("sf_cli"),
                )
                self._cache["sf_cli"] = status
                return status

            # Check sf version
            result = subprocess.run(
                ["sf", "--version"],
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode != 0:
                status = DependencyStatus(
                    name="Salesforce CLI",
                    available=False,
                    error="sf --version failed",
                    install_hint=self._get_install_hint("sf_cli"),
                )
                self._cache["sf_cli"] = status
                return status

            sf_version = result.stdout.strip().split("\n")[0]

            # Check if code-analyzer plugin is installed
            plugin_result = subprocess.run(
                ["sf", "plugins"],
                capture_output=True,
                text=True,
                timeout=15
            )

            has_ca_plugin = "code-analyzer" in plugin_result.stdout.lower() or \
                           "sfdx-scanner" in plugin_result.stdout.lower()

            if has_ca_plugin:
                status = DependencyStatus(
                    name="Salesforce CLI + Code Analyzer",
                    available=True,
                    version=sf_version,
                    path=sf_path,
                )
            else:
                status = DependencyStatus(
                    name="Salesforce CLI + Code Analyzer",
                    available=False,
                    version=sf_version,
                    path=sf_path,
                    error="Code Analyzer plugin not installed",
                    install_hint="sf plugins install @salesforce/sfdx-code-analyzer",
                )

            self._cache["sf_cli"] = status
            return status

        except subprocess.TimeoutExpired:
            status = DependencyStatus(
                name="Salesforce CLI",
                available=False,
                error="sf command timed out",
                install_hint=self._get_install_hint("sf_cli"),
            )
            self._cache["sf_cli"] = status
            return status
        except Exception as e:
            status = DependencyStatus(
                name="Salesforce CLI",
                available=False,
                error=str(e),
                install_hint=self._get_install_hint("sf_cli"),
            )
            self._cache["sf_cli"] = status
            return status

    def check_all(self) -> Dict[str, DependencyStatus]:
        """
        Check all dependencies.

        Returns:
            Dict mapping dependency name to status
        """
        return {
            "java": self.check_java(),
            "node": self.check_node(),
            "python": self.check_python(),
            "sf_cli": self.check_sf_cli(),
        }

    def get_engine_availability(self) -> Dict[str, EngineAvailability]:
        """
        Get availability status for each Code Analyzer engine.

        Returns:
            Dict mapping engine name to availability status
        """
        deps = self.check_all()
        engines = {}

        for engine, required_deps in self.ENGINE_DEPENDENCIES.items():
            missing = []
            for dep in required_deps:
                if not deps[dep].available:
                    missing.append(deps[dep].name)

            if missing:
                engines[engine] = EngineAvailability(
                    engine=engine,
                    available=False,
                    reason=f"Missing: {', '.join(missing)}",
                    dependencies=required_deps,
                )
            else:
                engines[engine] = EngineAvailability(
                    engine=engine,
                    available=True,
                    dependencies=required_deps,
                )

        return engines

    def get_available_engines(self) -> List[str]:
        """Get list of available engine names."""
        engines = self.get_engine_availability()
        return [name for name, status in engines.items() if status.available]

    def get_unavailable_engines(self) -> List[Tuple[str, str]]:
        """Get list of unavailable engines with reasons."""
        engines = self.get_engine_availability()
        return [
            (name, status.reason)
            for name, status in engines.items()
            if not status.available
        ]

    def get_availability_message(self) -> str:
        """
        Get a formatted message about engine availability.

        Returns:
            Human-readable status message
        """
        engines = self.get_engine_availability()
        available = [e for e, s in engines.items() if s.available]
        unavailable = [(e, s.reason) for e, s in engines.items() if not s.available]

        lines = []

        if available:
            lines.append(f"Available engines: {', '.join(available)}")

        if unavailable:
            lines.append("Unavailable engines:")
            for engine, reason in unavailable:
                lines.append(f"  - {engine}: {reason}")

            # Add install hints
            deps = self.check_all()
            missing_deps = [d for d, s in deps.items() if not s.available]
            if missing_deps:
                lines.append("")
                lines.append("To enable more engines, install:")
                for dep in missing_deps:
                    status = deps[dep]
                    if status.install_hint:
                        lines.append(f"  {status.name}: {status.install_hint}")

        return "\n".join(lines)

    def _get_install_hint(self, dependency: str) -> str:
        """Get platform-specific install hint."""
        hints = self.INSTALL_HINTS.get(dependency, {})

        if "all" in hints:
            return hints["all"]

        import platform
        system = platform.system().lower()

        if system == "darwin":
            return hints.get("darwin", "")
        elif system == "linux":
            return hints.get("linux", "")
        elif system == "windows":
            return hints.get("win32", "")
        else:
            return hints.get("linux", "")  # Default to linux


# Convenience function
def check_dependencies() -> Dict[str, bool]:
    """
    Quick check of all dependencies.

    Returns:
        Dict mapping dependency name to availability boolean
    """
    checker = DependencyChecker()
    deps = checker.check_all()
    return {name: status.available for name, status in deps.items()}


if __name__ == "__main__":
    # Run dependency check when executed directly
    checker = DependencyChecker()
    print(checker.get_availability_message())
