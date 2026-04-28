# sf-flex-estimator

Flex Credit estimation for **Agentforce** and **Data Cloud** workloads in sf-skills.

This skill helps you estimate:
- Agentforce per-invocation Flex Credits from prompt and action structure
- Data Cloud monthly Flex Credits from usage meters
- cumulative Data Cloud tier discounts
- Private Connect uplift
- low / medium / high / enterprise scenarios

## What this skill is for

Use `sf-flex-estimator` when you need **planning guidance before implementation**:
- pricing a new agent design
- sizing a pilot vs production rollout
- comparing architecture options
- identifying the main cost drivers in a proposed design

## What this skill is not for

- It does **not** create Agentforce metadata or `.agent` files.
- It does **not** provision or mutate Data Cloud assets.
- It does **not** replace contract-specific pricing from Salesforce commercial teams.

## Quick start

### Basic agent estimate

```bash
python3 assets/calculators/flex_calculator.py \
  --mode structure \
  --agent-def assets/templates/basic-agent-template.json
```

### Agentforce + Data Cloud scenario estimate

```bash
python3 assets/calculators/flex_calculator.py \
  --mode scenarios \
  --agent-def assets/templates/hybrid-agent-template.json
```

### Data Cloud tiering only

```bash
python3 assets/calculators/tier_multiplier.py \
  --base-fc 5000000 \
  --pretty
```

### Validate an estimate input

```bash
python3 hooks/scripts/validate_estimate.py \
  --input assets/templates/hybrid-agent-template.json \
  --verbose
```

## Included templates

| Template | Best for |
|---|---|
| `assets/templates/basic-agent-template.json` | Agentforce-only estimates |
| `assets/templates/hybrid-agent-template.json` | Agentforce + Data Cloud grounding |
| `assets/templates/data-cloud-template.json` | Data Cloud-only workloads |

## Included references

| Path | Purpose |
|---|---|
| `SKILL.md` | main skill instructions and handoff rules |
| `references/agentforce-pricing.md` | Agentforce prompt/action pricing |
| `references/data-cloud-pricing.md` | Data Cloud meter pricing and tiering |
| `references/calculation-methodology.md` | formulas, assumptions, and scenario logic |
| `references/common-use-cases.md` | sample estimation patterns |
| `references/edge-cases.md` | token overages, Private Connect, multi-org notes |
| `references/scoring-rubric.md` | 130-point validation rubric |

## Key pricing assumptions in this skill

- Agentforce uses **linear** pricing in this model.
- Data Cloud uses **monthly cumulative tiering**:
  - Tier 1: `0 - 300K` at `1.0x`
  - Tier 2: `300K - 1.5M` at `0.8x`
  - Tier 3: `1.5M - 12.5M` at `0.4x`
  - Tier 4: `12.5M+` at `0.2x`
- Flex Credits are modeled at **$0.004 per FC**.
- Private Connect adds **20% of Data Cloud spend after tiering**.
- Estimates use **public list-price guidance** only.

## Notes on validation

`hooks/scripts/validate_estimate.py` is a **manual validation helper**. It is not connected to the shared repo-wide auto-validation dispatcher because generic estimate files do not map cleanly to a single file extension or path convention.

## Credit

Primary contributor: [August Krys](https://github.com/not2technical)

Related repo:
- [not2technical/sf-skills](https://github.com/not2technical/sf-skills)

## License

MIT — see [LICENSE](LICENSE)
