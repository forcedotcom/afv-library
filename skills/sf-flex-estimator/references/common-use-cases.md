# Common Use Cases

This file shows a few representative estimation patterns supported by `sf-flex-estimator`.

## 1. Basic Agentforce-only estimate

Template:
- `assets/templates/basic-agent-template.json`

Structure:
- 1 basic prompt
- 2 standard prompts
- 3 standard actions
- no Data Cloud

### Result

```text
Per invocation: 70 FC ($0.28)
```

### Typical scenarios

| Scenario | Monthly FC | Monthly cost | Annual cost |
|---|---:|---:|---:|
| Low (1K) | 70,000 | $280.00 | $3,360.00 |
| Medium (10K) | 700,000 | $2,800.00 | $33,600.00 |
| High (100K) | 7,000,000 | $28,000.00 | $336,000.00 |

Best fit:
- FAQ agents
- lightweight service triage
- pilot implementations without Data Cloud grounding

---

## 2. Hybrid Agentforce + Data Cloud estimate

Template:
- `assets/templates/hybrid-agent-template.json`

Structure:
- 1 basic prompt
- 3 standard prompts
- 5 standard actions
- Data Cloud baseline:
  - `data_360_prep`: 10.0
  - `data_360_streaming_pipeline`: 2.0
  - `data_360_queries`: 5.0
  - `data_360_segmentation`: 1.0

### Per invocation

```text
114 FC ($0.456)
```

### Standard generated scenarios

| Scenario | Total monthly FC | Monthly cost | Annual cost | Data Cloud discount |
|---|---:|---:|---:|---:|
| Low (1K) | 121,465 | $485.86 | $5,830.32 | 0.00% |
| Medium (10K) | 1,214,650 | $4,858.60 | $58,303.20 | 0.00% |
| High (100K) | 12,057,200 | $48,228.80 | $578,745.60 | 11.96% |
| Enterprise (500K) | 59,153,000 | $236,612.00 | $2,839,344.00 | 42.32% |

Best fit:
- service agents grounded with unified customer context
- order history or profile lookup use cases
- architecture tradeoff conversations where the user wants to compare action count versus Data Cloud scaling

---

## 3. Data Cloud-only estimate

Template:
- `assets/templates/data-cloud-template.json`

Baseline meters:
- `data_360_prep`: 500.0
- `data_360_streaming_pipeline`: 50.0
- `data_360_queries`: 100.0
- `data_360_segmentation`: 50.0
- `data_360_activation`: 100.0

### Standard generated scenarios

| Scenario | Base Data Cloud FC | Tiered FC | Monthly cost | Annual cost |
|---|---:|---:|---:|---:|
| Low (1K) | 203,800 | 203,800 | $815.20 | $9,782.40 |
| Medium (10K) | 2,038,000 | 1,475,200 | $5,900.80 | $70,809.60 |
| High (100K) | 20,380,000 | 7,236,000 | $28,944.00 | $347,328.00 |
| Enterprise (500K) | 101,900,000 | 23,540,000 | $94,160.00 | $1,129,920.00 |

Best fit:
- Data Cloud planning before an agent exists
- ingestion/segment/activation scenario modeling
- conversations focused on meter mix and tier savings

---

## Command patterns

```bash
# Agentforce only
python3 assets/calculators/flex_calculator.py --mode structure --agent-def assets/templates/basic-agent-template.json

# Hybrid scenario ladder
python3 assets/calculators/flex_calculator.py --mode scenarios --agent-def assets/templates/hybrid-agent-template.json

# Data Cloud tiering sanity check
python3 assets/calculators/tier_multiplier.py --base-fc 5000000 --pretty
```
