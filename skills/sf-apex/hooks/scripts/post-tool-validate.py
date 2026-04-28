#!/usr/bin/env python3
"""
Post-Tool Validation Hook for sf-apex plugin.

This hook runs AFTER Write or Edit tool completes and provides validation
feedback for Salesforce Apex files (*.cls, *.trigger).

Integrates:
1. Custom 150-point scoring (8 categories)
2. Salesforce Code Analyzer V5 (all available engines)

Hook Input (stdin): JSON with tool_input and tool_response
Hook Output (stdout): JSON with optional output message

This hook is ADVISORY - it provides feedback but does not block operations.
"""

import sys
import os
import json

# Add script directory to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# Find shared modules — try installed path first, then dev repo path
_CLAUDE_DIR = os.path.join(os.path.expanduser("~"), ".claude")
_CODE_ANALYZER_CANDIDATES = [
    os.path.join(_CLAUDE_DIR, "code_analyzer"),           # Installed path
    os.path.join(SCRIPT_DIR, "..", "..", "..", "..", "shared", "code_analyzer"),  # Dev repo
]
for _ca_path in _CODE_ANALYZER_CANDIDATES:
    _ca_path = os.path.normpath(_ca_path)
    if os.path.isdir(_ca_path):
        sys.path.insert(0, os.path.dirname(_ca_path))  # Parent so "from code_analyzer import" works
        break

# Also add shared dir for soql_extractor and other shared modules
PLUGIN_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))  # sf-apex/
SKILLS_ROOT = os.path.dirname(PLUGIN_ROOT)  # parent of skills/
SHARED_DIR = os.path.join(SKILLS_ROOT, "shared")
if os.path.isdir(SHARED_DIR):
    sys.path.insert(0, SHARED_DIR)


def validate_apex_with_ca(file_path: str) -> dict:
    """
    Run comprehensive Apex validation combining custom scoring with Code Analyzer.

    Args:
        file_path: Path to .cls or .trigger file

    Returns:
        dict with validation results and output message
    """
    output_parts = []
    file_name = os.path.basename(file_path)

    try:
        # ═══════════════════════════════════════════════════════════════════
        # PHASE 1: Custom 150-point validation
        # ═══════════════════════════════════════════════════════════════════
        from validate_apex import ApexValidator

        validator = ApexValidator(file_path)
        custom_results = validator.validate()

        custom_score = custom_results.get('score', 0)
        custom_max = custom_results.get('max_score', 150)
        custom_issues = custom_results.get('issues', [])
        custom_scores = custom_results.get('scores', {})
        custom_rating = custom_results.get('rating', '')

        # ═══════════════════════════════════════════════════════════════════
        # PHASE 1.5: LLM Pattern Validation (Java types, hallucinated methods)
        # ═══════════════════════════════════════════════════════════════════
        llm_issues = []
        try:
            from llm_pattern_validator import LLMPatternValidator
            llm_validator = LLMPatternValidator(file_path)
            llm_results = llm_validator.validate()
            llm_issues = llm_results.get('issues', [])

            # Add LLM issues to custom_issues with adjusted severity
            for issue in llm_issues:
                custom_issues.append({
                    'severity': issue.get('severity', 'WARNING'),
                    'category': issue.get('category', 'llm_pattern'),
                    'message': issue.get('message', ''),
                    'line': issue.get('line', 0),
                    'fix': issue.get('fix', ''),
                    'source': 'llm-validator'
                })
        except ImportError:
            pass  # LLM validator not available
        except Exception:
            pass  # Don't fail validation on LLM check errors

        # ═══════════════════════════════════════════════════════════════════
        # PHASE 2: Code Analyzer V5 scanning (if available)
        # ═══════════════════════════════════════════════════════════════════
        ca_violations = []
        ca_engines_used = []
        ca_engines_unavailable = []
        ca_available = False
        scan_time_ms = 0

        try:
            from code_analyzer.scanner import CodeAnalyzerScanner, SkillType
            from code_analyzer.score_merger import ScoreMerger

            scanner = CodeAnalyzerScanner()

            if scanner.is_available():
                ca_available = True
                scan_result = scanner.scan(file_path, SkillType.APEX)

                if scan_result.success:
                    ca_violations = scan_result.violations
                    ca_engines_used = scan_result.engines_used
                    ca_engines_unavailable = scan_result.engines_unavailable
                    scan_time_ms = scan_result.scan_time_ms
                else:
                    ca_engines_unavailable = ["Error: " + (scan_result.error_message or "Unknown")]
            else:
                ca_engines_unavailable = ["sf CLI with Code Analyzer not installed"]

        except ImportError as e:
            ca_engines_unavailable = [f"Module not available: {e}"]
        except Exception as e:
            ca_engines_unavailable = [f"Scanner error: {e}"]

        # ═══════════════════════════════════════════════════════════════════
        # PHASE 2.5: Live Query Plan Analysis (if org connected)
        # ═══════════════════════════════════════════════════════════════════
        live_plan_results = []
        org_name = None
        live_plan_available = False

        try:
            from code_analyzer.live_query_plan import LiveQueryPlanAnalyzer
            from soql_extractor import SOQLExtractor

            # Read file content for SOQL extraction
            with open(file_path, 'r') as f:
                file_content = f.read()

            analyzer = LiveQueryPlanAnalyzer()
            if analyzer.is_org_available():
                live_plan_available = True
                org_name = analyzer.get_target_org()

                # Extract SOQL queries from Apex
                extractor = SOQLExtractor(file_content, "apex")
                queries = extractor.extract()

                # Analyze each query (limit to first 5 to avoid timeout)
                for query_info in queries[:5]:
                    # Skip dynamic variable queries
                    if query_info.query_type == 'dynamic_variable':
                        continue

                    plan_result = analyzer.analyze(query_info.query)
                    live_plan_results.append({
                        'line': query_info.line,
                        'query': query_info.query[:60],
                        'in_loop': query_info.in_loop,
                        'plan': plan_result
                    })

                    # Add non-selective queries to issues
                    if plan_result.success and not plan_result.is_selective:
                        custom_issues.append({
                            'severity': 'WARNING',
                            'line': query_info.line,
                            'message': f'Non-selective SOQL (cost: {plan_result.relative_cost:.1f}, op: {plan_result.leading_operation})',
                            'fix': 'Add indexed fields to WHERE clause or reduce result set'
                        })

        except ImportError:
            pass  # Live analysis not available
        except Exception as e:
            pass  # Don't fail validation on live plan errors

        # ═══════════════════════════════════════════════════════════════════
        # PHASE 3: Merge scores (if CA results available)
        # ═══════════════════════════════════════════════════════════════════
        final_score = custom_score
        final_max = custom_max
        rating = custom_rating
        rating_stars = 0
        ca_deductions = 0
        deductions = []

        if ca_violations and ca_available:
            try:
                merger = ScoreMerger(
                    custom_scores=custom_scores,
                    custom_max_scores=validator.scores
                )
                merged = merger.merge(
                    [v if isinstance(v, dict) else v.__dict__ for v in ca_violations],
                    engines_used=ca_engines_used,
                    engines_unavailable=ca_engines_unavailable,
                )
                final_score = merged.final_score
                final_max = merged.final_max
                rating = merged.rating
                rating_stars = merged.rating_stars
                ca_deductions = merged.ca_deductions
                deductions = merged.deductions
            except Exception as e:
                # Fallback to custom score only
                pass

        # Calculate rating stars from custom score if not set
        if rating_stars == 0:
            pct = (final_score / final_max * 100) if final_max > 0 else 0
            if pct >= 90:
                rating_stars = 5
            elif pct >= 75:
                rating_stars = 4
            elif pct >= 60:
                rating_stars = 3
            elif pct >= 45:
                rating_stars = 2
            else:
                rating_stars = 1

        # ═══════════════════════════════════════════════════════════════════
        # PHASE 4: Format output
        # ═══════════════════════════════════════════════════════════════════
        stars = "" * rating_stars + "" * (5 - rating_stars)

        output_parts.append("")
        output_parts.append(f" Apex Validation: {file_name}")
        output_parts.append("" * 60)

        # Combined score
        output_parts.append(f" Score: {final_score}/{final_max} {stars} {rating}")

        # Show CA deductions if any
        if ca_deductions > 0:
            output_parts.append(f"   (Custom: {custom_score}, CA deductions: -{ca_deductions})")

        # Category breakdown
        if custom_scores:
            output_parts.append("")
            output_parts.append(" Category Breakdown:")
            for cat, score in custom_scores.items():
                max_score = validator.scores.get(cat, 0)
                if max_score > 0:
                    icon = "" if score == max_score else ("" if score >= max_score * 0.7 else "")
                    diff = f" (-{max_score - score})" if score < max_score else ""
                    display_name = cat.replace("_", " ").title()
                    output_parts.append(f"   {icon} {display_name}: {score}/{max_score}{diff}")

        # Code Analyzer status
        output_parts.append("")
        if ca_engines_used:
            output_parts.append(f" Code Analyzer: {', '.join(ca_engines_used)}")
        elif ca_available:
            output_parts.append(" Code Analyzer: No engines ran")
        else:
            output_parts.append(" Code Analyzer: Not available")

        if ca_engines_unavailable:
            for unavail in ca_engines_unavailable[:3]:
                output_parts.append(f"    {unavail}")

        if scan_time_ms > 0:
            output_parts.append(f"    Scan time: {scan_time_ms}ms")

        # Live Query Plan section
        if live_plan_results:
            output_parts.append("")
            output_parts.append(f"🌐 Live Query Plan Analysis (Org: {org_name})")
            for lp in live_plan_results[:3]:  # Show first 3
                plan = lp['plan']
                if plan.success:
                    loop_warn = " ⚠️ IN LOOP" if lp['in_loop'] else ""
                    output_parts.append(f"   L{lp['line']}: {plan.icon} Cost {plan.relative_cost:.1f} ({plan.leading_operation}){loop_warn}")
                    if plan.notes:
                        output_parts.append(f"      📝 {str(plan.notes[0])[:55]}")
            if len(live_plan_results) > 3:
                output_parts.append(f"   ... and {len(live_plan_results) - 3} more queries")
        elif live_plan_available:
            output_parts.append("")
            output_parts.append("🌐 Live Query Plan: No SOQL queries found")
        elif org_name is None and not live_plan_available:
            pass  # Don't show if org not connected (too noisy)

        # Issues list
        all_issues = []

        # Add custom issues
        for issue in custom_issues:
            severity = issue.get('severity', 'INFO')
            all_issues.append({
                'severity': severity,
                'source': 'sf-skills',
                'line': issue.get('line', 0),
                'message': issue.get('message', ''),
                'fix': issue.get('fix', ''),
            })

        # Add CA violations
        for v in ca_violations:
            if isinstance(v, dict):
                all_issues.append({
                    'severity': v.get('severity_label', 'INFO'),
                    'source': f"CA:{v.get('engine', '')}",
                    'line': v.get('line', 0),
                    'message': v.get('message', '')[:80],
                    'rule': v.get('rule', ''),
                })

        if all_issues:
            output_parts.append("")
            output_parts.append(f" Issues Found ({len(all_issues)}):")

            # Sort by severity
            severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MODERATE': 2, 'WARNING': 3, 'LOW': 4, 'INFO': 5}
            all_issues.sort(key=lambda x: severity_order.get(x['severity'], 5))

            # Display up to 12 issues
            for issue in all_issues[:12]:
                icon = {'CRITICAL': '', 'HIGH': '', 'MODERATE': '', 'WARNING': '', 'LOW': '', 'INFO': ''}.get(
                    issue['severity'], ''
                )
                source = f"[{issue['source']}]" if issue.get('source') else ""
                line_info = f"L{issue['line']}" if issue.get('line') else ""
                message = issue['message'][:65] + "..." if len(issue['message']) > 65 else issue['message']

                output_parts.append(f"   {icon} {issue['severity']} {source} {line_info}: {message}")

                if issue.get('fix'):
                    fix = issue['fix'][:55] + "..." if len(issue['fix']) > 55 else issue['fix']
                    output_parts.append(f"      Fix: {fix}")

            if len(all_issues) > 12:
                output_parts.append(f"   ... and {len(all_issues) - 12} more issues")
        else:
            output_parts.append("")
            output_parts.append(" No issues found!")

        output_parts.append("" * 60)

        return {
            "continue": True,
            "output": "\n".join(output_parts)
        }

    except ImportError as e:
        return {
            "continue": True,
            "output": f" Apex validator not available: {e}"
        }
    except Exception as e:
        return {
            "continue": True,
            "output": f" Apex validation error: {e}"
        }


def main():
    """
    Main hook entry point.

    Reads hook input from stdin, validates Apex files.
    """
    try:
        # Read hook input from stdin
        hook_input = json.load(sys.stdin)

        # Extract file path from tool input
        tool_input = hook_input.get("tool_input", {})
        file_path = tool_input.get("file_path", "")

        # Check if operation was successful
        tool_response = hook_input.get("tool_response", {})
        if not tool_response.get("success", True):
            # Operation failed, don't validate
            print(json.dumps({"continue": True}))
            return 0

        # Only validate Apex files
        result = {"continue": True}

        if file_path.endswith(".cls") or file_path.endswith(".trigger"):
            result = validate_apex_with_ca(file_path)

        # Output result
        print(json.dumps(result))
        return 0

    except json.JSONDecodeError:
        # No valid JSON input, continue silently
        print(json.dumps({"continue": True}))
        return 0
    except Exception as e:
        # Unexpected error, log but don't block
        print(json.dumps({
            "continue": True,
            "output": f" Hook error: {e}"
        }))
        return 0


if __name__ == "__main__":
    sys.exit(main())
