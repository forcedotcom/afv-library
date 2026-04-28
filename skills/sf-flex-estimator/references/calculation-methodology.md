# Calculation Methodology

This document defines how `sf-flex-estimator` turns an Agentforce + Data Cloud design into a public list-price Flex Credit estimate.

## 1. Scope the workload

Start by separating the estimate into two buckets:

1. **Agentforce**
   - prompt tiers
   - action types
   - token overages
2. **Data Cloud**
   - monthly usage meters
   - Private Connect requirement

These buckets are priced differently and should be modeled independently before combining the result.

---

## 2. Agentforce per-invocation formula

Agentforce is modeled per invocation.

```text
per-invocation FC = prompt FC + action FC + token overage FC
per-invocation cost = per-invocation FC × 0.004
```

### Prompt rates

| Tier | FC |
|---|---:|
| starter | 2 |
| basic | 2 |
| standard | 4 |
| advanced | 16 |

### Action rates

| Type | FC |
|---|---:|
| standard | 20 |
| custom | 20 |
| voice | 30 |
| sandbox | 16 |

### Example

```text
Prompts:
- 1 basic = 2 FC
- 3 standard = 12 FC

Actions:
- 5 standard = 100 FC

Per invocation = 114 FC
Per invocation cost = 114 × 0.004 = $0.456
```

---

## 3. Token overage handling

This skill models token overages as **additional prompt or action charges**.

### Preferred input

Use explicit counts when you know them:

```json
{
  "token_overages": {
    "prompts": 1,
    "actions": 0
  }
}
```

That means one extra prompt-sized charge is added per invocation.

### If exact distribution is unknown

The calculator uses a **weighted average prompt or action rate** based on the configured structure.

Example:

```text
Prompts:
- 1 basic (2 FC)
- 3 standard (4 FC)
Average prompt rate = 14 / 4 = 3.5 FC

If prompt overages = 1:
extra prompt FC = 3.5
```

This keeps the estimate usable when the user only knows that overages occur, not which exact prompt/action causes them.

---

## 4. Data Cloud base FC formula

Data Cloud is modeled from **monthly meter volumes**.

```text
base meter FC = monthly volume × public rate
base Data Cloud FC = sum(all meter FC)
```

### Current public meter set used by this skill

| Meter | FC per 1M units |
|---|---:|
| data_360_prep | 40 |
| data_360_unification | 75,000 |
| data_360_segmentation | 50 |
| data_360_activation | 60 |
| data_360_zero_copy_sharing | 60 |
| data_360_queries | 3 |
| data_360_streaming_pipeline | 3,500 |
| data_360_real_time_pipeline | 250,000 |
| data_360_code_extension | 40 |

### Meter units that are not per 1M rows

| Meter | Unit |
|---|---|
| data_360_unstructured_processing | MB |
| data_360_intelligent_processing | MB |
| data_360_code_extension | compute unit |

The calculator accepts both current names and a limited set of legacy aliases, but the recommendation is to use the current `data_360_*` names in new estimate inputs.

---

## 5. Data Cloud tiering

After the base monthly Data Cloud FC is calculated, apply cumulative monthly tiering.

| Tier | Range | Multiplier |
|---|---:|---:|
| 1 | 0 - 300K | 1.0x |
| 2 | 300K - 1.5M | 0.8x |
| 3 | 1.5M - 12.5M | 0.4x |
| 4 | 12.5M+ | 0.2x |

### Cumulative example: 5M FC base

```text
Tier 1:   300,000 × 1.0 =   300,000
Tier 2: 1,200,000 × 0.8 =   960,000
Tier 3: 3,500,000 × 0.4 = 1,400,000
Total tiered FC = 2,660,000
```

```text
Effective discount = (5,000,000 - 2,660,000) / 5,000,000 = 46.8%
```

---

## 6. Private Connect

If Private Connect is enabled, apply it **after** Data Cloud tiering.

```text
private connect FC = tiered Data Cloud FC × 0.20
```

Example:

```text
tiered Data Cloud FC = 2,660,000
Private Connect FC = 532,000
Data Cloud total = 3,192,000
```

---

## 7. Combined monthly total

```text
total monthly FC = Agentforce FC + tiered Data Cloud FC + Private Connect FC
total monthly cost = total monthly FC × 0.004
total annual cost = total monthly cost × 12
```

---

## 8. Standard scenario generation

The default scenario set in this skill is:

| Scenario | Invocations / month |
|---|---:|
| Low | 1,000 |
| Medium | 10,000 |
| High | 100,000 |
| Enterprise | 500,000 |

### Default scaling behavior

If Data Cloud operations are present, the calculator scales the monthly meter volumes in proportion to the scenario multiplier using **1K invocations as the baseline**.

Example baseline:

```json
{
  "data_cloud_operations": {
    "operations": {
      "data_360_prep": 10.0,
      "data_360_streaming_pipeline": 2.0,
      "data_360_queries": 5.0,
      "data_360_segmentation": 1.0
    }
  }
}
```

Then the generated scenarios use:

| Scenario | Scale factor |
|---|---:|
| Low | 1x |
| Medium | 10x |
| High | 100x |
| Enterprise | 500x |

This is useful when the user only has a baseline design and wants a rough scenario ladder.

---

## 9. Validation philosophy

The 130-point rubric is intended to check:
- completeness of the structure model
- correctness of the pricing model used
- realism of usage assumptions
- clarity of scenario output
- handling of edge cases like overages and Private Connect

Use the manual validator when you want a fast sanity check:

```bash
python3 hooks/scripts/validate_estimate.py --input assets/templates/hybrid-agent-template.json --verbose
```

---

## 10. What this skill does not model

This skill intentionally does **not** model:
- custom contract discounts
- promotional pricing
- regional commercial exceptions
- non-public enterprise agreement terms
- operational costs outside Flex Credits (implementation effort, support, monitoring, data quality work)

When the user needs commercial certainty, treat this skill as a **public baseline estimate**, not a substitute for actual pricing approval.
