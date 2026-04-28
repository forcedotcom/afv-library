# Data Cloud Flex Credit Pricing Reference

This reference captures the **public Data Cloud pricing model** used by `sf-flex-estimator`.

## Core concepts

- Data Cloud is modeled from **monthly usage meters**.
- The base monthly FC total is then reduced using **cumulative monthly tiering**.
- Private Connect is modeled as **20% of tiered Data Cloud FC**.
- This document reflects the **public list-price assumptions** used by the skill, not contract-specific pricing.

---

## Current meter table used by the skill

| Meter | FC per 1M units | Typical use |
|---|---:|---|
| `data_360_prep` | 40 | preparation and transformation |
| `data_360_unification` | 75,000 | identity resolution / unification |
| `data_360_segmentation` | 50 | segment creation and refresh |
| `data_360_activation` | 60 | outbound activation/export |
| `data_360_zero_copy_sharing` | 60 | sharing without copying |
| `data_360_queries` | 3 | query execution |
| `data_360_streaming_pipeline` | 3,500 | streaming/event ingestion |
| `data_360_real_time_pipeline` | 250,000 | high-cost real-time pipeline workloads |
| `data_360_code_extension` | 40 | code extension compute |

### Meter units that are not per 1M rows

| Meter | Unit |
|---|---|
| `data_360_unstructured_processing` | MB |
| `data_360_intelligent_processing` | MB |
| `data_360_code_extension` | compute unit |

---

## Legacy alias handling

The calculator accepts a compatibility layer for common legacy names, including:
- `batch_internal` → `data_360_prep`
- `queries` → `data_360_queries`
- `segmentation` → `data_360_segmentation`
- `streaming` → `data_360_streaming_pipeline`
- `profile_unification` → `data_360_unification`
- `activation_batch` / `activation_streaming` → `data_360_activation`

For new estimate inputs, prefer the current `data_360_*` meter names.

---

## Tier structure

Data Cloud tiering is applied **monthly** and **cumulatively**.

| Tier | Monthly FC range | Multiplier | Discount |
|---|---:|---:|---:|
| Tier 1 | `0 - 300,000` | `1.0x` | 0% |
| Tier 2 | `300,000 - 1,500,000` | `0.8x` | 20% |
| Tier 3 | `1,500,000 - 12,500,000` | `0.4x` | 60% |
| Tier 4 | `12,500,000+` | `0.2x` | 80% |

### Cumulative example: 5M base FC

```text
Tier 1:   300,000 × 1.0 =   300,000
Tier 2: 1,200,000 × 0.8 =   960,000
Tier 3: 3,500,000 × 0.4 = 1,400,000
Total tiered FC = 2,660,000
```

```text
Savings = 5,000,000 - 2,660,000 = 2,340,000 FC
Effective discount = 46.8%
```

---

## Private Connect

Private Connect is modeled as:

```text
Private Connect FC = tiered Data Cloud FC × 0.20
```

### Example

```text
Tiered Data Cloud FC: 2,660,000
Private Connect FC:     532,000
Data Cloud total FC:  3,192,000
```

Private Connect applies only to the Data Cloud portion of the estimate in this skill.

---

## Practical interpretation of the meters

### `data_360_prep`
Use for transformation-heavy preparation workloads and baseline ingestion prep.

### `data_360_streaming_pipeline`
Use for true streaming/event-style ingestion. This is often one of the largest cost drivers in mixed workloads.

### `data_360_queries`
Usually a relatively small meter unless the workload is heavily query-driven.

### `data_360_unification`
This is a high-cost meter and deserves explicit discussion whenever identity resolution volume is large.

### `data_360_activation`
Model outbound audience or data activation here.

---

## Optimization heuristics

### 1. Challenge streaming assumptions
Streaming can dominate monthly FC faster than prep/query/segment meters. If hourly or scheduled latency is acceptable, estimate a batch-oriented alternative and compare.

### 2. Separate high-cost meters from background meters
Call out `data_360_unification`, `data_360_streaming_pipeline`, and `data_360_real_time_pipeline` explicitly so the user sees what is really driving cost.

### 3. Show the impact of tiering at scale
The effective discount can change materially as Data Cloud FC crosses 300K, 1.5M, and 12.5M monthly thresholds.

### 4. Price Private Connect separately
Keep Private Connect visible as its own line item. It should not disappear into the base meter total.

---

## Example base calculation

```json
{
  "data_cloud_operations": {
    "operations": {
      "data_360_prep": 10.0,
      "data_360_streaming_pipeline": 2.0,
      "data_360_queries": 5.0,
      "data_360_segmentation": 1.0
    },
    "private_connect": false
  }
}
```

```text
data_360_prep:               10 ×    40 =     400 FC
data_360_streaming_pipeline:  2 × 3,500 =   7,000 FC
data_360_queries:            5 ×     3 =      15 FC
data_360_segmentation:       1 ×    50 =      50 FC
Base Data Cloud FC = 7,465 FC
```

Since 7,465 FC is below Tier 2, tiering does not change the result.

---

## Command reference

```bash
python3 assets/calculators/tier_multiplier.py --base-fc 5000000 --pretty
python3 assets/calculators/flex_calculator.py --mode scenarios --agent-def assets/templates/hybrid-agent-template.json
```

---

## Pricing caution

This skill intentionally stays within public list-price guidance. If a user needs exact commercial numbers for a live deal, call out that contract-specific terms may differ from the estimate produced here.
