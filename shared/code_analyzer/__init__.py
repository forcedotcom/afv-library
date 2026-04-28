"""
Salesforce Code Analyzer V5 Integration for sf-skills.

This module provides shared infrastructure for integrating Salesforce Code Analyzer
with Claude Code's hook system across all sf-skills (apex, flow, lwc, etc.).

Components:
    - scanner: Core wrapper for sf code-analyzer CLI
    - parser: JSON result normalization
    - dependency_checker: Runtime dependency detection (JDK, Node, Python)
    - score_merger: Combines custom scoring with CA findings
    - formatter: Terminal output formatting
    - live_query_plan: Real-time SOQL query plan analysis via REST API

Usage:
    from code_analyzer import CodeAnalyzerScanner, SkillType, ScoreMerger

    scanner = CodeAnalyzerScanner()
    result = scanner.scan("/path/to/file.cls", SkillType.APEX)

    merger = ScoreMerger(custom_scores, max_scores)
    merged = merger.merge(result.violations)

    # Live query plan analysis
    from code_analyzer import LiveQueryPlanAnalyzer
    analyzer = LiveQueryPlanAnalyzer()
    plan = analyzer.analyze("SELECT Id FROM Account WHERE Name = 'Acme'")
"""

from .scanner import CodeAnalyzerScanner, SkillType, ScanResult
from .dependency_checker import DependencyChecker
from .score_merger import ScoreMerger, MergedScore
from .parser import parse_ca_output, normalize_violation
from .formatter import format_validation_output
from .live_query_plan import LiveQueryPlanAnalyzer, QueryPlanResult, PlanNote

__all__ = [
    # Scanner
    "CodeAnalyzerScanner",
    "SkillType",
    "ScanResult",
    # Dependencies
    "DependencyChecker",
    # Scoring
    "ScoreMerger",
    "MergedScore",
    # Parser
    "parse_ca_output",
    "normalize_violation",
    # Formatter
    "format_validation_output",
    # Live Query Plan
    "LiveQueryPlanAnalyzer",
    "QueryPlanResult",
    "PlanNote",
]

__version__ = "1.1.0"
