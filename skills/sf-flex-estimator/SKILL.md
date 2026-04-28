---
name: sf-flex-estimator
description: >
  Salesforce Flex Credit estimation for Agentforce and Data Cloud workloads.
  TRIGGER when: user needs cost projections, scenario planning, budget sizing,
  or architecture tradeoff analysis for Agentforce prompts/actions, Data Cloud
  meters, or monthly Flex Credit usage.
  DO NOT TRIGGER when: user is building Agentforce metadata or .agent files
  themselves (use sf-ai-agentforce or sf-ai-agentscript), implementing Data
  Cloud assets (use sf-datacloud-*), or asking for contract-specific commercial
  approval that depends on non-public pricing terms.
license: MIT
metadata:
  version: "1.1.0"
  author: "August Krys"
  scoring: "130 points across 7 categories"
---

# sf-flex-estimator: Agentforce & Data Cloud Flex Credit Estimation

Use this skill when the user needs a **public-price estimate** for:
- Agentforce prompt + action consumption
- Data Cloud monthly usage meters
- Flex Credit scenario planning
- cost optimization recommendations before build or rollout

This skill is for **planning and estimation**, not implementation.

---

## When This Skill Owns the Task

Use `sf-flex-estimator` when the user is asking questions like:
- "What will this Agentforce agent cost per month?"
- "Estimate Flex Credits for 5 prompts, 8 actions, and Data Cloud grounding"
- "Compare low / medium / high usage scenarios"
- "How much does Private Connect add?"
- "What Flex Credit savings do we get if we reduce streaming or action count?"

Delegate elsewhere when the user is:
- building Builder metadata, Prompt Builder templates, or action wiring → [sf-ai-agentforce](../sf-ai-agentforce/SKILL.md)
- authoring or fixing `.agent` files → [sf-ai-agentscript](../sf-ai-agentscript/SKILL.md)
- implementing Data Cloud connections, streams, DMOs, segments, or activations → [sf-datacloud](../sf-datacloud/SKILL.md) and the phase-specific `sf-datacloud-*` skills
- creating test data or operational data imports → [sf-data](../sf-data/SKILL.md)
- deploying metadata or runtime assets → [sf-deploy](../sf-deploy/SKILL.md)

---

## Required Context to Gather First

Ask for or infer:
- agent prompt count by tier: `starter`, `basic`, `standard`, `advanced`
- action count by type: `standard`, `custom`, `voice`, `sandbox`
- whether token overages are expected for prompts or actions
- monthly Data Cloud meter volumes, if Data Cloud is in scope
- whether Private Connect is required
- whether the estimate should model a pilot, small production, enterprise, or multiple scenarios
- whether the user wants **public list-price guidance** or is trying to reconcile contract-specific commercial numbers

If the user does not know exact monthly volumes, start with a baseline template and generate multiple scenarios.

---

## Core Pricing Model

### Agentforce

Agentforce billing is **linear** — no volume tiers.

| Component | FC per invocation |
|---|---:|
| Starter prompt | 2 |
| Basic prompt | 2 |
| Standard prompt | 4 |
| Advanced prompt | 16 |
| Standard / custom action | 20 |
| Voice action | 30 |
| Sandbox action | 16 |

### Data Cloud

Data Cloud uses **monthly cumulative tiering**.

| Tier | Monthly FC range | Multiplier |
|---|---:|---:|
| Tier 1 | 0 - 300K | 1.0x |
| Tier 2 | 300K - 1.5M | 0.8x |
| Tier 3 | 1.5M - 12.5M | 0.4x |
| Tier 4 | 12.5M+ | 0.2x |

### Other rules

- Flex Credits are priced at **$0.004 per FC** in this skill.
- Private Connect adds **20% of Data Cloud spend after tiering**.
- Agentforce and Data Cloud are estimated separately, then combined.
- Estimates in this skill use **publicly documented list pricing only**.

For the full meter table and examples, read:
- [references/agentforce-pricing.md](references/agentforce-pricing.md)
- [references/data-cloud-pricing.md](references/data-cloud-pricing.md)

---

## Recommended Workflow

### 1. Baseline the structure

Model the agent and Data Cloud footprint first.

Useful starting templates:
- [assets/templates/basic-agent-template.json](assets/templates/basic-agent-template.json)
- [assets/templates/hybrid-agent-template.json](assets/templates/hybrid-agent-template.json)
- [assets/templates/data-cloud-template.json](assets/templates/data-cloud-template.json)

### 2. Calculate the per-invocation cost

For Agentforce, estimate:

```text
per-invocation FC = prompt FC + action FC + token overage FC
```

### 3. Calculate Data Cloud base FC

Map each monthly meter volume to the current public rate card, then apply cumulative tiering.

### 4. Generate scenarios

Use the standard scenario set unless the user provides a better one:
- Low: 1K invocations / month
- Medium: 10K / month
- High: 100K / month
- Enterprise: 500K / month

### 5. Validate assumptions and recommend optimizations

Check for:
- too many prompts or actions
- unnecessary streaming usage
- likely token overages
- missing Private Connect handling
- unrealistic volume assumptions

---

## Scripts and Templates

### Calculator

- [assets/calculators/flex_calculator.py](assets/calculators/flex_calculator.py)
- [assets/calculators/tier_multiplier.py](assets/calculators/tier_multiplier.py)

### Validation helper

- [hooks/scripts/validate_estimate.py](hooks/scripts/validate_estimate.py)

> This validator is a **manual helper**. It is intentionally **not** wired into the shared auto-validation dispatcher because generic `.json` or `.md` file patterns would create too much noise.

### Example commands

```bash
# Per-invocation estimate for a template
python3 assets/calculators/flex_calculator.py \
  --mode structure \
  --agent-def assets/templates/basic-agent-template.json

# Scenario estimate for an Agentforce + Data Cloud design
python3 assets/calculators/flex_calculator.py \
  --mode scenarios \
  --agent-def assets/templates/hybrid-agent-template.json

# Tiering only
python3 assets/calculators/tier_multiplier.py \
  --base-fc 5000000 \
  --pretty

# Validate an estimate input document
python3 hooks/scripts/validate_estimate.py \
  --input assets/templates/hybrid-agent-template.json \
  --verbose
```

---

## High-Signal Estimation Rules

- Prefer **standard prompts** for most production reasoning workloads.
- Use **basic prompts** only for simple routing/classification.
- Action count often dominates cost faster than prompt count.
- Data Cloud **streaming** is materially more expensive than prep/query/segment meters.
- Tiering matters only for **Data Cloud**, not Agentforce.
- Private Connect applies only to **Data Cloud** spend in this model.
- If the user has contract-specific pricing, treat this skill as a **public baseline** and note that commercial terms may differ.

---

## Output Format

When the estimate is complete, present:
1. workload summary
2. per-invocation Agentforce cost
3. monthly scenario table
4. Data Cloud tiering impact
5. top optimization recommendations
6. confidence / validation notes

Suggested shape:

```text
Flex Credit estimate: <name>
Agentforce per invocation: <fc> FC ($<cost>)
Data Cloud monthly base: <fc> FC
Scenarios: <low / medium / high / enterprise>
Optimization priorities: <1-3 bullets>
Confidence: <high / medium / low>
```

---

## Cross-Skill Integration

| Need | Delegate to | Why |
|---|---|---|
| build the actual agent metadata | [sf-ai-agentforce](../sf-ai-agentforce/SKILL.md) | implementation of Builder assets |
| build a deterministic `.agent` bundle | [sf-ai-agentscript](../sf-ai-agentscript/SKILL.md) | authoring and validation of Agent Script |
| implement Data Cloud pipeline assets | [sf-datacloud](../sf-datacloud/SKILL.md) and `sf-datacloud-*` | live Data Cloud setup |
| package or deploy the solution | [sf-deploy](../sf-deploy/SKILL.md) | deployment workflow |
| generate supporting test or sample data | [sf-data](../sf-data/SKILL.md) | data preparation |

A common chain is:

```text
sf-ai-agentforce / sf-ai-agentscript / sf-datacloud-* → sf-flex-estimator → sf-deploy
```

---

## Reference Map

### Start here
- [README.md](README.md)
- [references/calculation-methodology.md](references/calculation-methodology.md)
- [references/common-use-cases.md](references/common-use-cases.md)
- [references/edge-cases.md](references/edge-cases.md)

### Pricing references
- [references/agentforce-pricing.md](references/agentforce-pricing.md)
- [references/data-cloud-pricing.md](references/data-cloud-pricing.md)

### Validation and scoring
- [references/scoring-rubric.md](references/scoring-rubric.md)
- [hooks/scripts/validate_estimate.py](hooks/scripts/validate_estimate.py)
