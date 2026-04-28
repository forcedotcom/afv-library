# Scoring Rubric

## Overview

SF-Flex-Estimator uses a 130-point scoring system across 7 categories to evaluate estimate quality. This document provides detailed scoring criteria for each category.

---

## Scoring Categories

### 1. Use Case Analysis (25 points)

**Purpose:** Measure completeness of workload decomposition and component identification.

| Score | Criteria |
|-------|----------|
| **23-25 (Excellent)** | • All agent components identified (prompts, actions, DC ops)<br>• Prompt tiers correctly determined<br>• Action types properly categorized<br>• Data Cloud operations fully mapped<br>• Requirements gathering complete with no gaps |
| **18-22 (Good)** | • Most components identified<br>• Minor gaps in prompt tier determination<br>• Action types mostly correct<br>• DC operations partially mapped<br>• Requirements mostly complete |
| **13-17 (Fair)** | • Basic components identified<br>• Some uncertainty in prompt tiers<br>• Action types partially correct<br>• DC operations incomplete<br>• Requirements have significant gaps |
| **<13 (Poor)** | • Incomplete component identification<br>• Prompt tiers unknown or incorrect<br>• Action types not categorized<br>• DC operations missing or wrong<br>• Requirements gathering inadequate |

**Common Deductions:**
- Missing prompt count: -5 points
- Unknown prompt tiers: -3 points per tier
- Actions not categorized: -4 points
- DC operations not mapped: -5 points
- No edge case consideration: -3 points

---

### 2. Estimation Accuracy (25 points)

**Purpose:** Measure correctness of Flex Credit calculations.

| Score | Criteria |
|-------|----------|
| **23-25 (Excellent)** | • Per-invocation cost calculated correctly<br>• All rates applied accurately<br>• Token overages handled properly<br>• DC rates correct for all meters<br>• Math verified and correct |
| **18-22 (Good)** | • Per-invocation cost mostly correct<br>• Minor rate application errors<br>• Token overages estimated reasonably<br>• DC rates mostly correct<br>• Math has minor errors (<5%) |
| **13-17 (Fair)** | • Per-invocation cost has errors<br>• Some rates applied incorrectly<br>• Token overages not estimated<br>• DC rates partially incorrect<br>• Math errors (5-15%) |
| **<13 (Poor)** | • Per-invocation cost wrong<br>• Rates applied incorrectly<br>• Token overages ignored<br>• DC rates wrong<br>• Significant math errors (>15%) |

**Common Deductions:**
- Wrong prompt rate: -3 points per prompt
- Wrong action rate: -4 points per action
- Token overage not calculated: -3 points
- DC rate incorrect: -3 points per meter
- Calculation error >10%: -5 points

---

### 3. Data Cloud Tiering (20 points)

**Purpose:** Measure correctness of tiered multiplier application.

| Score | Criteria |
|-------|----------|
| **18-20 (Excellent)** | • Correct 4-tier cumulative calculation<br>• All tier boundaries identified<br>• Volume-based discounting accurate<br>• Private Connect calculated correctly<br>• Tier savings documented |
| **14-17 (Good)** | • Tiered multiplier applied (minor errors)<br>• Most tier boundaries correct<br>• Volume discounting mostly accurate<br>• Private Connect handled<br>• Tier savings estimated |
| **10-13 (Fair)** | • Tiered multiplier attempted but errors<br>• Some tier boundaries wrong<br>• Volume discounting partially correct<br>• Private Connect may be wrong<br>• Tier savings missing |
| **<10 (Poor)** | • No tiered multiplier applied<br>• Flat discount used instead<br>• Tier boundaries ignored<br>• Private Connect calculation wrong<br>• Tier savings not calculated |

**Common Deductions:**
- Flat discount instead of cumulative: -8 points
- Wrong tier boundary: -3 points each
- Private Connect on wrong base (AF+DC instead of DC only): -5 points
- Private Connect not applied when required: -4 points
- Tier savings not documented: -2 points

**Critical Errors (immediate score <10):**
- Using flat multiplier across all volume (e.g., base_fc × 0.6 for entire amount)
- Applying Private Connect to Agentforce FC
- Not applying any tiering when DC FC > 300K

---

### 4. Cost Breakdown (20 points)

**Purpose:** Measure clarity and completeness of cost presentation.

| Score | Criteria |
|-------|----------|
| **18-20 (Excellent)** | • Clear categorization (AF, DC, PC)<br>• All scenarios generated (Low/Medium/High/Enterprise)<br>• Monthly and annual projections<br>• Per-component visibility<br>• Formatted for readability |
| **14-17 (Good)** | • Good categorization<br>• Most scenarios generated<br>• Monthly projections present<br>• Component breakdown mostly clear<br>• Reasonable formatting |
| **10-13 (Fair)** | • Basic categorization<br>• Limited scenarios<br>• Only monthly OR annual<br>• Component breakdown incomplete<br>• Poor formatting |
| **<10 (Poor)** | • No clear categorization<br>• Single scenario only<br>• Missing projections<br>• No component breakdown<br>• Unreadable format |

**Common Deductions:**
- Missing scenario: -3 points each (max 4 scenarios)
- No annual projection: -2 points
- No component breakdown: -4 points
- Poor formatting: -2 points
- Missing cost summary: -3 points

---

### 5. Edge Case Handling (15 points)

**Purpose:** Measure handling of special scenarios and complexity.

| Score | Criteria |
|-------|----------|
| **14-15 (Excellent)** | • Token overages estimated and applied<br>• Private Connect handled correctly<br>• Multi-org scenarios addressed<br>• Sandbox vs production considered<br>• All edge cases documented |
| **11-13 (Good)** | • Token overages considered<br>• Private Connect mentioned<br>• Multi-org partially addressed<br>• Most edge cases handled |
| **8-10 (Fair)** | • Token overages mentioned<br>• Private Connect may be missed<br>• Multi-org not considered<br>• Some edge cases handled |
| **<8 (Poor)** | • Token overages ignored<br>• Private Connect not handled<br>• Multi-org not addressed<br>• Edge cases missing |

**Common Deductions:**
- Token overages not estimated: -3 points
- Private Connect not considered when >1M DC FC: -4 points
- Multi-org not addressed when applicable: -3 points
- Sandbox costs not differentiated: -2 points
- Voice actions not priced correctly: -3 points

**Edge Cases Checklist:**
- ✅ Token overages (prompts >2K, actions >10K)
- ✅ Private Connect (20% of DC, not AF)
- ✅ Multi-org deployments (Home + Companion)
- ✅ Sandbox vs production action rates
- ✅ Voice action premium (30 FC vs 20 FC)
- ✅ Mixed workloads (AF + DC)

---

### 6. Documentation Quality (15 points)

**Purpose:** Measure clarity of assumptions, methodology, and recommendations.

| Score | Criteria |
|-------|----------|
| **14-15 (Excellent)** | • Clear assumptions documented<br>• Methodology explained<br>• Actionable recommendations (3+)<br>• Optimization opportunities identified<br>• Well-structured and readable |
| **11-13 (Good)** | • Assumptions documented<br>• Methodology described<br>• Some recommendations (1-2)<br>• Optimization mentioned<br>• Readable structure |
| **8-10 (Fair)** | • Basic assumptions<br>• Methodology unclear<br>• Limited recommendations<br>• No optimization guidance<br>• Poor structure |
| **<8 (Poor)** | • No assumptions documented<br>• Methodology missing<br>• No recommendations<br>• No optimization guidance<br>• Disorganized |

**Common Deductions:**
- Assumptions not documented: -4 points
- Methodology not explained: -3 points
- No optimization recommendations: -4 points
- Poor structure/readability: -2 points
- Missing next steps: -2 points

**Documentation Checklist:**
- ✅ Assumptions clearly stated
- ✅ Calculation methodology explained
- ✅ At least 3 optimization recommendations
- ✅ Savings projections for recommendations
- ✅ Next steps provided
- ✅ Confidence level stated (High/Medium/Low)

---

### 7. Validation & Sanity Checks (10 points)

**Purpose:** Measure reasonableness and validation of estimates.

| Score | Criteria |
|-------|----------|
| **9-10 (Excellent)** | • All validation checks pass<br>• Realistic volume estimates<br>• Sanity checks documented<br>• Warnings flagged appropriately<br>• Confidence level assessed |
| **7-8 (Good)** | • Most validation passes<br>• Volumes reasonable<br>• Basic sanity checks<br>• Major warnings noted<br>• Confidence mentioned |
| **5-6 (Fair)** | • Some validation issues<br>• Volumes questionable<br>• Limited sanity checks<br>• Warnings may be missed<br>• Confidence unclear |
| **<5 (Poor)** | • Validation fails<br>• Unrealistic volumes<br>• No sanity checks<br>• Warnings ignored<br>• No confidence assessment |

**Common Deductions:**
- Unrealistic agent invocations (e.g., 50M/month for pilot): -2 points
- Unrealistic DC volumes (e.g., 1B rows streaming): -3 points
- Per-invocation cost out of range (4-500 FC): -2 points
- No validation performed: -5 points
- Confidence level not stated: -1 point

**Validation Checks:**
- ✅ Agent invocations: 100 - 10M/month
- ✅ Prompt count: 1-20 per agent
- ✅ Action count: 0-50 per agent
- ✅ Per-invocation: 4-500 FC
- ✅ DC volumes: Within reasonable ranges per meter
- ✅ Token overage: 0-30% of prompts
- ✅ Cost scaling: Linear for AF, tiered for DC

---

## Overall Scoring

### Score Calculation

```
Total Score = Use Case (25) + Accuracy (25) + DC Tiering (20) +
              Cost Breakdown (20) + Edge Cases (15) +
              Documentation (15) + Validation (10)
Max Score = 130 points
```

### Quality Thresholds

| Score Range | Grade | Description | Action |
|-------------|-------|-------------|--------|
| **117-130 (90%+)** | ✅ Excellent | High confidence, production ready | Proceed with confidence |
| **104-116 (80-89%)** | ⭐ Very Good | Production ready with minor review | Minor adjustments recommended |
| **91-103 (70-79%)** | ⚠️ Good | Review assumptions before proceeding | Review and validate |
| **78-90 (60-69%)** | ⚠️ Needs Work | Address gaps in analysis | Significant revision needed |
| **<78 (<60%)** | ❌ BLOCKED | Critical issues must be resolved | Must re-estimate |

### Common Score Ranges

**117-130 (Excellent):**
- All components identified and mapped correctly
- Tiered multipliers applied accurately
- All scenarios generated with proper breakdowns
- Edge cases handled comprehensively
- Clear documentation with actionable recommendations
- All validation checks pass

**104-116 (Very Good):**
- Most components correct, minor gaps
- Tiered multipliers mostly correct
- All scenarios present, minor formatting issues
- Most edge cases handled
- Good documentation, some recommendations
- Validation mostly passes

**91-103 (Good):**
- Core components identified, some uncertainties
- Tiered multipliers applied with some errors
- Limited scenarios or missing projections
- Some edge cases missed
- Basic documentation, limited recommendations
- Some validation warnings

**78-90 (Needs Work):**
- Missing components or incorrect mapping
- Tiered multipliers wrong or not applied
- Incomplete scenarios
- Edge cases largely ignored
- Poor documentation
- Multiple validation failures

**<78 (Blocked):**
- Critical calculation errors
- Flat discount instead of tiered
- No scenarios or breakdowns
- Edge cases completely missed
- No documentation
- Unrealistic estimates

---

## Scoring Examples

### Example 1: Excellent Score (125/130)

**Breakdown:**
- Use Case Analysis: 25/25 - All components identified, prompt tiers correct
- Estimation Accuracy: 24/25 - Per-invocation correct, minor rounding
- Data Cloud Tiering: 20/20 - Cumulative tiers applied perfectly
- Cost Breakdown: 19/20 - All scenarios, minor formatting improvement
- Edge Case Handling: 15/15 - Token overages, Private Connect, multi-org
- Documentation: 14/15 - Clear assumptions, 3 recommendations
- Validation: 8/10 - All checks pass, one minor warning

**Grade:** ✅ Excellent - Production ready

### Example 2: Good Score (95/130)

**Breakdown:**
- Use Case Analysis: 20/25 - Some prompt tier uncertainty
- Estimation Accuracy: 22/25 - Minor rate application errors
- Data Cloud Tiering: 14/20 - Tiered multiplier applied, boundary issues
- Cost Breakdown: 16/20 - Missing one scenario
- Edge Case Handling: 9/15 - Token overages missed, Private Connect handled
- Documentation: 10/15 - Basic assumptions, limited recommendations
- Validation: 4/10 - Some unrealistic volumes

**Grade:** ⚠️ Good - Review assumptions before proceeding

### Example 3: Blocked Score (65/130)

**Breakdown:**
- Use Case Analysis: 15/25 - Missing action types
- Estimation Accuracy: 10/25 - Wrong rates applied
- Data Cloud Tiering: 5/20 - Flat discount used instead of cumulative
- Cost Breakdown: 12/20 - Only one scenario
- Edge Case Handling: 6/15 - Most edge cases ignored
- Documentation: 7/15 - No assumptions, no recommendations
- Validation: 10/10 - Unrealistic volumes, no validation

**Grade:** ❌ BLOCKED - Must re-estimate

---

## Self-Assessment Checklist

Before finalizing an estimate, verify:

### Use Case Analysis (25 points)
- [ ] All prompts counted and tiers assigned
- [ ] All actions counted and types categorized
- [ ] Token overages estimated
- [ ] Data Cloud operations identified and mapped
- [ ] Special requirements noted (Private Connect, multi-org)

### Estimation Accuracy (25 points)
- [ ] Per-invocation cost calculated
- [ ] Correct rates applied to all components
- [ ] Token overages factored in
- [ ] DC rates correct for all meters
- [ ] Math verified

### Data Cloud Tiering (20 points)
- [ ] Cumulative 4-tier logic applied (not flat discount)
- [ ] Tier boundaries correct (300K, 1.5M, 12.5M)
- [ ] Private Connect calculated correctly (20% of DC tiered FC)
- [ ] Tier savings documented

### Cost Breakdown (20 points)
- [ ] 4 scenarios generated (Low/Medium/High/Enterprise)
- [ ] Monthly and annual projections
- [ ] AF, DC, PC broken out separately
- [ ] Clear formatting

### Edge Case Handling (15 points)
- [ ] Token overages estimated
- [ ] Private Connect considered if DC >1M FC
- [ ] Multi-org addressed if applicable
- [ ] Voice/sandbox rates correct

### Documentation (15 points)
- [ ] Assumptions documented
- [ ] Methodology explained
- [ ] 3+ optimization recommendations with savings
- [ ] Next steps provided

### Validation (10 points)
- [ ] Volumes realistic
- [ ] Per-invocation in range (4-500 FC)
- [ ] Sanity checks performed
- [ ] Confidence level stated

---

## Version History

- **v1.0.0** (2026-03-10): Initial scoring rubric with 130-point system
