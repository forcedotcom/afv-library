#!/usr/bin/env python3
"""
Score Merger - Combines custom sf-skills scoring with Code Analyzer findings.

This module merges the existing sf-skills validation scores (150-point for Apex,
110-point for Flow, etc.) with Salesforce Code Analyzer V5 findings to produce
a unified report.

Strategy:
- Custom scoring remains the primary score
- Code Analyzer findings add additional deductions
- Critical CA findings reduce score by up to 20 points total
- High CA findings reduce by up to 10 points total
- Duplicate findings (same rule) are deduplicated
- Findings that overlap with custom scoring categories get mapped

Usage:
    merger = ScoreMerger(
        custom_scores={"bulkification": 25, "security": 20, ...},
        custom_max_scores={"bulkification": 25, "security": 25, ...}
    )
    merged = merger.merge(ca_violations)

    print(f"Final score: {merged.final_score}/{merged.final_max}")
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class ScoreCategory(Enum):
    """Universal scoring categories across sf-skills."""
    BULKIFICATION = "bulkification"
    SECURITY = "security"
    TESTING = "testing"
    ARCHITECTURE = "architecture"
    CLEAN_CODE = "clean_code"
    ERROR_HANDLING = "error_handling"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    # Flow-specific
    DESIGN = "design"
    LOGIC = "logic"
    OBSERVABILITY = "observability"
    GOVERNANCE = "governance"


@dataclass
class ScoreDeduction:
    """A single score deduction from CA findings."""
    rule: str
    engine: str
    severity: int
    severity_label: str
    deduction: int
    category: Optional[str]
    message: str
    line: int = 0


@dataclass
class MergedScore:
    """Combined score from custom validator + Code Analyzer."""
    custom_score: int
    custom_max: int
    ca_violations_total: int
    ca_critical: int
    ca_high: int
    ca_deductions: int
    final_score: int
    final_max: int
    rating: str
    rating_stars: int
    deductions: List[ScoreDeduction]
    engines_used: List[str] = field(default_factory=list)
    engines_unavailable: List[str] = field(default_factory=list)


class ScoreMerger:
    """
    Merges custom validation scores with Code Analyzer findings.

    The merger applies deductions from CA violations on top of the custom score,
    with caps to prevent excessive penalization.
    """

    # Mapping from CA rules to sf-skills score categories
    RULE_CATEGORY_MAP = {
        # PMD Apex rules -> Categories
        "AvoidSoqlInLoops": ScoreCategory.BULKIFICATION,
        "AvoidDmlStatementsInLoops": ScoreCategory.BULKIFICATION,
        "OperationWithLimitsInLoop": ScoreCategory.BULKIFICATION,

        "ApexCRUDViolation": ScoreCategory.SECURITY,
        "ApexSharingViolations": ScoreCategory.SECURITY,
        "ApexSOQLInjection": ScoreCategory.SECURITY,
        "ApexOpenRedirect": ScoreCategory.SECURITY,
        "ApexCSRF": ScoreCategory.SECURITY,
        "ApexBadCrypto": ScoreCategory.SECURITY,
        "ApexInsecureEndpoint": ScoreCategory.SECURITY,
        "ApexXSSFromURLParam": ScoreCategory.SECURITY,
        "ApexXSSFromEscapeFalse": ScoreCategory.SECURITY,

        "ApexUnitTestClassShouldHaveAsserts": ScoreCategory.TESTING,
        "ApexUnitTestShouldNotUseSeeAllDataTrue": ScoreCategory.TESTING,
        "ApexAssertionsShouldIncludeMessage": ScoreCategory.TESTING,
        "ApexUnitTestMethodShouldHaveIsTestAnnotation": ScoreCategory.TESTING,

        "CyclomaticComplexity": ScoreCategory.CLEAN_CODE,
        "ExcessiveParameterList": ScoreCategory.CLEAN_CODE,
        "ExcessiveClassLength": ScoreCategory.CLEAN_CODE,
        "ExcessivePublicCount": ScoreCategory.CLEAN_CODE,
        "TooManyFields": ScoreCategory.CLEAN_CODE,
        "NcssMethodCount": ScoreCategory.CLEAN_CODE,
        "NcssTypeCount": ScoreCategory.CLEAN_CODE,
        "NcssConstructorCount": ScoreCategory.CLEAN_CODE,
        "AvoidGlobalModifier": ScoreCategory.CLEAN_CODE,
        "AvoidHardcodingId": ScoreCategory.CLEAN_CODE,
        "AvoidLogicInTrigger": ScoreCategory.ARCHITECTURE,
        "DebugsShouldUseLoggingLevel": ScoreCategory.CLEAN_CODE,

        "EmptyCatchBlock": ScoreCategory.ERROR_HANDLING,
        "EmptyTryOrFinallyBlock": ScoreCategory.ERROR_HANDLING,
        "EmptyStatementBlock": ScoreCategory.ERROR_HANDLING,

        "AvoidHardcodingId": ScoreCategory.PERFORMANCE,
        "OperationWithLimitsInLoop": ScoreCategory.PERFORMANCE,

        "ApexDoc": ScoreCategory.DOCUMENTATION,

        # Regex rules
        "HardcodedSalesforceUrl": ScoreCategory.CLEAN_CODE,
        "MissingWithSharing": ScoreCategory.SECURITY,
        "DeprecatedTestIsRunning": ScoreCategory.TESTING,

        # Flow rules
        "DbInLoop": ScoreCategory.BULKIFICATION,
        "GetRecordsInLoop": ScoreCategory.BULKIFICATION,
        "CyclicSubflow": ScoreCategory.ARCHITECTURE,
        "MissingFaultHandler": ScoreCategory.ERROR_HANDLING,
        "MissingFaultPath": ScoreCategory.ERROR_HANDLING,
        "HardcodedId": ScoreCategory.CLEAN_CODE,
        "MissingDescription": ScoreCategory.DOCUMENTATION,
        "MissingNullHandler": ScoreCategory.ERROR_HANDLING,
        "UnusedVariable": ScoreCategory.CLEAN_CODE,
    }

    # Deduction points per severity
    SEVERITY_DEDUCTIONS = {
        1: 5,   # Critical: -5 per violation
        2: 3,   # High: -3 per violation
        3: 1,   # Moderate: -1 per violation
        4: 0,   # Low: informational only
        5: 0,   # Info: informational only
    }

    # Maximum total deductions by severity (caps)
    MAX_DEDUCTIONS_BY_SEVERITY = {
        1: 20,  # Max -20 from critical violations
        2: 10,  # Max -10 from high violations
        3: 5,   # Max -5 from moderate violations
    }

    # Overall maximum deduction from CA
    MAX_TOTAL_DEDUCTION = 30

    # Rating thresholds (percentage of max score)
    RATING_THRESHOLDS = [
        (90, "Excellent", 5),
        (75, "Very Good", 4),
        (60, "Good", 3),
        (45, "Needs Work", 2),
        (0, "Critical Issues", 1),
    ]

    def __init__(
        self,
        custom_scores: Dict[str, int],
        custom_max_scores: Dict[str, int],
    ):
        """
        Initialize merger with custom validation scores.

        Args:
            custom_scores: Dict of category -> current score
            custom_max_scores: Dict of category -> max possible score
        """
        self.custom_scores = custom_scores
        self.custom_max_scores = custom_max_scores
        self.deductions: List[ScoreDeduction] = []

    def merge(
        self,
        ca_violations: List[Dict[str, Any]],
        engines_used: Optional[List[str]] = None,
        engines_unavailable: Optional[List[str]] = None,
    ) -> MergedScore:
        """
        Merge Code Analyzer violations with custom scores.

        Args:
            ca_violations: List of normalized violations from CodeAnalyzerScanner
            engines_used: List of engines that ran
            engines_unavailable: List of engines that couldn't run

        Returns:
            MergedScore with combined results
        """
        self.deductions = []

        # Track deductions by severity
        severity_totals = {1: 0, 2: 0, 3: 0}
        processed_rules = set()  # Dedupe same rule violations

        critical_count = 0
        high_count = 0

        for violation in ca_violations:
            rule = violation.get("rule", "")
            severity = violation.get("severity", 5)
            line = violation.get("line", 0)

            # Create unique key for deduplication (rule + line)
            dedup_key = f"{rule}:{line}"
            if dedup_key in processed_rules:
                continue
            processed_rules.add(dedup_key)

            # Count by severity
            if severity == 1:
                critical_count += 1
            elif severity == 2:
                high_count += 1

            # Calculate deduction
            base_deduction = self.SEVERITY_DEDUCTIONS.get(severity, 0)
            if base_deduction <= 0:
                continue  # No deduction for low/info

            # Check against severity cap
            current_total = severity_totals.get(severity, 0)
            max_for_severity = self.MAX_DEDUCTIONS_BY_SEVERITY.get(severity, 0)
            actual_deduction = min(base_deduction, max_for_severity - current_total)

            if actual_deduction <= 0:
                continue  # Cap reached for this severity

            severity_totals[severity] += actual_deduction

            # Map to category
            category = self.RULE_CATEGORY_MAP.get(rule)
            category_name = category.value if category else "general"

            self.deductions.append(ScoreDeduction(
                rule=rule,
                engine=violation.get("engine", "unknown"),
                severity=severity,
                severity_label=violation.get("severity_label", "UNKNOWN"),
                deduction=actual_deduction,
                category=category_name,
                message=violation.get("message", "")[:100],
                line=line,
            ))

        # Calculate totals
        custom_total = sum(self.custom_scores.values())
        custom_max = sum(self.custom_max_scores.values())

        total_deductions = sum(severity_totals.values())

        # Apply overall cap
        total_deductions = min(total_deductions, self.MAX_TOTAL_DEDUCTION)

        final_score = max(0, custom_total - total_deductions)

        # Calculate rating
        rating, rating_stars = self._calculate_rating(final_score, custom_max)

        return MergedScore(
            custom_score=custom_total,
            custom_max=custom_max,
            ca_violations_total=len(ca_violations),
            ca_critical=critical_count,
            ca_high=high_count,
            ca_deductions=total_deductions,
            final_score=final_score,
            final_max=custom_max,
            rating=rating,
            rating_stars=rating_stars,
            deductions=self.deductions,
            engines_used=engines_used or [],
            engines_unavailable=engines_unavailable or [],
        )

    def _calculate_rating(self, score: int, max_score: int) -> tuple:
        """Calculate star rating based on percentage."""
        if max_score == 0:
            return "N/A", 0

        percentage = (score / max_score) * 100

        for threshold, label, stars in self.RATING_THRESHOLDS:
            if percentage >= threshold:
                return label, stars

        return "Critical Issues", 1

    def get_category_impact(self) -> Dict[str, int]:
        """
        Get total deductions by category.

        Returns:
            Dict mapping category name to total deduction points
        """
        impact = {}
        for d in self.deductions:
            cat = d.category or "general"
            impact[cat] = impact.get(cat, 0) + d.deduction
        return impact


def merge_scores(
    custom_scores: Dict[str, int],
    custom_max_scores: Dict[str, int],
    ca_violations: List[Dict[str, Any]],
    engines_used: Optional[List[str]] = None,
    engines_unavailable: Optional[List[str]] = None,
) -> MergedScore:
    """
    Convenience function to merge scores.

    Args:
        custom_scores: Dict of category -> current score
        custom_max_scores: Dict of category -> max possible score
        ca_violations: List of normalized CA violations
        engines_used: List of engines that ran
        engines_unavailable: List of engines that couldn't run

    Returns:
        MergedScore with combined results
    """
    merger = ScoreMerger(custom_scores, custom_max_scores)
    return merger.merge(ca_violations, engines_used, engines_unavailable)


def format_rating_stars(stars: int) -> str:
    """Format rating as star icons."""
    return "" * stars + "" * (5 - stars)


if __name__ == "__main__":
    # Demo with sample data
    custom_scores = {
        "bulkification": 25,
        "security": 20,
        "testing": 25,
        "architecture": 18,
        "clean_code": 20,
        "error_handling": 15,
        "performance": 10,
        "documentation": 7,
    }

    custom_max = {
        "bulkification": 25,
        "security": 25,
        "testing": 25,
        "architecture": 20,
        "clean_code": 20,
        "error_handling": 15,
        "performance": 10,
        "documentation": 10,
    }

    ca_violations = [
        {
            "rule": "AvoidSoqlInLoops",
            "engine": "pmd",
            "severity": 1,
            "severity_label": "CRITICAL",
            "message": "SOQL query found inside loop",
            "line": 25,
        },
        {
            "rule": "EmptyCatchBlock",
            "engine": "pmd",
            "severity": 2,
            "severity_label": "HIGH",
            "message": "Empty catch block swallows exception",
            "line": 40,
        },
        {
            "rule": "CyclomaticComplexity",
            "engine": "pmd",
            "severity": 3,
            "severity_label": "MODERATE",
            "message": "Method complexity is 15 (threshold 10)",
            "line": 50,
        },
    ]

    merged = merge_scores(
        custom_scores,
        custom_max,
        ca_violations,
        engines_used=["pmd", "regex"],
        engines_unavailable=["sfge"],
    )

    print(f"Custom Score: {merged.custom_score}/{merged.custom_max}")
    print(f"CA Violations: {merged.ca_violations_total} ({merged.ca_critical} critical, {merged.ca_high} high)")
    print(f"CA Deductions: -{merged.ca_deductions}")
    print(f"Final Score: {merged.final_score}/{merged.final_max}")
    print(f"Rating: {format_rating_stars(merged.rating_stars)} {merged.rating}")
    print()
    print("Deductions:")
    for d in merged.deductions:
        print(f"  -{d.deduction} [{d.category}] {d.rule}: {d.message}")
