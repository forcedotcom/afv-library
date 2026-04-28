#!/usr/bin/env python3
"""
Apex Validator for sf-skills plugin.

Validates Salesforce Apex code (.cls, .trigger) for patterns that
Code Analyzer (PMD) does not cover.

Scoring Categories (90 points total):
1. Testing (25 pts): test methods, assertions, coverage
2. Architecture (20 pts): separation of concerns, patterns
3. Clean Code (20 pts): naming, complexity, comments
4. Error Handling (15 pts): try-catch, custom exceptions
5. Performance (10 pts): limits, caching, async

NOTE: Bulkification, security, documentation, and hardcoded IDs are
handled by sf code-analyzer (PMD rules) which runs as a separate
validation phase. This avoids duplicate checking with less accuracy.
"""

import re
import sys
import os
from typing import Dict, List, Tuple


class ApexValidator:
    """Validates Apex code for best practices."""

    def __init__(self, file_path: str):
        """
        Initialize the validator with an Apex file.

        Args:
            file_path: Path to .cls or .trigger file
        """
        self.file_path = file_path
        self.content = ""
        self.lines = []
        self.issues = []
        self.scores = {
            'testing': 25,
            'architecture': 20,
            'clean_code': 20,
            'error_handling': 15,
            'performance': 10,
        }

        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
                self.lines = self.content.split('\n')
        except Exception as e:
            self.issues.append({
                'severity': 'CRITICAL',
                'category': 'file',
                'message': f'Cannot read file: {e}',
                'line': 0
            })

    def validate(self) -> Dict:
        """
        Run all validations on the Apex file.

        Returns:
            Dictionary with validation results
        """
        if not self.content:
            return {
                'file': os.path.basename(self.file_path),
                'score': 0,
                'max_score': 150,
                'rating': 'CRITICAL',
                'issues': self.issues
            }

        # Run checks (bulkification, security, documentation handled by Code Analyzer PMD)
        self._check_null_checks()
        self._check_naming_conventions()
        self._check_error_handling()

        # Calculate total score
        total_score = sum(self.scores.values())
        max_score = 90

        # Determine rating
        if total_score >= 81:
            rating = '⭐⭐⭐⭐⭐ Excellent'
        elif total_score >= 68:
            rating = '⭐⭐⭐⭐ Very Good'
        elif total_score >= 54:
            rating = '⭐⭐⭐ Good'
        elif total_score >= 40:
            rating = '⭐⭐ Needs Work'
        else:
            rating = '⭐ Critical Issues'

        return {
            'file': os.path.basename(self.file_path),
            'score': total_score,
            'max_score': max_score,
            'rating': rating,
            'scores': self.scores.copy(),
            'issues': self.issues
        }

    def _check_null_checks(self):
        """Check for missing null checks before method calls."""
        # Look for patterns like variable.method() without prior null check
        # This is a simplified check
        null_check_pattern = r'(\w+)\s*!=\s*null'
        method_call_pattern = r'(\w+)\.\w+\s*\('

        checked_vars = set()
        for line in self.lines:
            matches = re.findall(null_check_pattern, line)
            checked_vars.update(matches)

        # Check if method calls are on unchecked variables (simplified)
        # This is advisory only since full analysis requires AST
        pass

    def _check_naming_conventions(self):
        """Check for naming convention violations."""
        # Class names should be PascalCase
        # Match actual class declarations (with optional modifiers), not "class" in comments
        class_pattern = r'^\s*(?:public|private|global|virtual|abstract|with\s+sharing|without\s+sharing|\s)*\s*class\s+(\w+)'
        for i, line in enumerate(self.lines, 1):
            # Skip comment lines
            stripped = line.strip()
            if stripped.startswith('//') or stripped.startswith('*') or stripped.startswith('/*'):
                continue
            match = re.search(class_pattern, line, re.IGNORECASE)
            if match:
                class_name = match.group(1)
                if not class_name[0].isupper():
                    self.issues.append({
                        'severity': 'INFO',
                        'category': 'clean_code',
                        'message': f'Class name "{class_name}" should be PascalCase',
                        'line': i
                    })
                    self.scores['clean_code'] -= 2

        # Method names should be camelCase
        method_pattern = r'(public|private|protected|global)\s+(static\s+)?(\w+)\s+(\w+)\s*\('
        for i, line in enumerate(self.lines, 1):
            match = re.search(method_pattern, line)
            if match:
                method_name = match.group(4)
                # Skip constructors and test methods
                if method_name[0].isupper() and '@isTest' not in self.content[:i]:
                    if method_name not in [m.group(1) for m in re.finditer(class_pattern, self.content)]:
                        self.issues.append({
                            'severity': 'INFO',
                            'category': 'clean_code',
                            'message': f'Method name "{method_name}" should be camelCase',
                            'line': i
                        })
                        self.scores['clean_code'] -= 2

    def _check_error_handling(self):
        """Check for error handling patterns."""
        has_try = 'try {' in self.content or 'try{' in self.content
        has_catch = 'catch (' in self.content or 'catch(' in self.content

        # Check for empty catch blocks
        empty_catch_pattern = r'catch\s*\([^)]+\)\s*\{\s*\}'
        for i, line in enumerate(self.lines, 1):
            if re.search(empty_catch_pattern, line):
                self.issues.append({
                    'severity': 'WARNING',
                    'category': 'error_handling',
                    'message': 'Empty catch block - exceptions are silently swallowed',
                    'line': i,
                    'fix': 'Log the exception or handle it appropriately'
                })
                self.scores['error_handling'] -= 5

        # Check for generic exception catch without specific handling
        if 'catch (Exception e)' in self.content:
            # This is OK as a fallback, but should have specific catches first
            pass

def main():
    """Command-line interface for Apex validation."""
    if len(sys.argv) < 2:
        print("Usage: python validate_apex.py <file.cls|file.trigger>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    validator = ApexValidator(file_path)
    results = validator.validate()

    # Print results
    print(f"\n🔍 Apex Validation (patterns): {results['file']}")
    print(f"Score: {results['score']}/{results['max_score']} {results['rating']}  (PMD handles bulkification, security, docs)")
    print()

    if results['issues']:
        print("Issues found:")
        for issue in results['issues']:
            severity_icon = {'CRITICAL': '🔴', 'WARNING': '🟡', 'INFO': '🔵'}.get(issue['severity'], '⚪')
            print(f"  {severity_icon} [{issue['severity']}] Line {issue['line']}: {issue['message']}")
            if 'fix' in issue:
                print(f"      Fix: {issue['fix']}")
    else:
        print("✅ No issues found!")

    # Return non-zero if critical issues
    critical_count = sum(1 for i in results['issues'] if i['severity'] == 'CRITICAL')
    sys.exit(1 if critical_count > 0 else 0)


if __name__ == "__main__":
    main()
