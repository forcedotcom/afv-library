# Edge Cases

This document highlights the most common scenarios where a fast estimate can become misleading if assumptions are not called out explicitly.

## 1. Token overages

If prompts or actions exceed their normal token thresholds, add extra prompt/action charges per invocation.

### Guidance
- use explicit overage counts when known
- if the user only knows that overages happen, document that the estimate is using a weighted average overage charge
- high-context grounding, large payload actions, and document-heavy prompts deserve extra scrutiny

---

## 2. Private Connect

Private Connect is a separate uplift on top of tiered Data Cloud FC.

```text
Private Connect FC = tiered Data Cloud FC × 0.20
```

### Guidance
- show it as its own line item
- do not bury it inside the base Data Cloud number
- confirm whether it is actually required for the target deployment

---

## 3. Unification-heavy workloads

`data_360_unification` is one of the highest-cost meters in the public model.

### Guidance
- challenge the proposed cadence
- check whether the volume is full-refresh or incremental
- show unification separately from lower-cost prep/query/segment meters

---

## 4. Streaming overuse

`data_360_streaming_pipeline` can dominate monthly cost faster than prep/query/segment meters.

### Guidance
- estimate an alternative with lower streaming volume whenever the business process tolerates latency
- present both the real-time and batch-oriented option if the user is undecided

---

## 5. Multi-org architectures

This skill can still guide multi-org planning, but the estimate should be broken into buckets instead of pretending everything is one homogeneous workload.

Recommended split:
- home org Agentforce spend
- home org Data Cloud spend
- companion org Data Cloud spend
- Private Connect by org, if required

### Guidance
- keep each org or region as its own line item
- do not assume the same Data Cloud volumes across every org unless the user confirms that assumption
- note that this skill is still a public-price planning model, not a substitute for commercial review

---

## 6. Contract-specific pricing

This skill intentionally uses public list-price assumptions.

### Guidance
If the user asks for exact commercial numbers:
- provide the public baseline estimate
- explicitly say commercial terms may differ
- avoid claiming contract accuracy that the public model cannot guarantee

---

## 7. Unknown or legacy meter names

Older notes may use legacy names such as `batch_internal`, `streaming`, `queries`, or `profile_unification`.

### Guidance
- normalize them to current `data_360_*` meters when possible
- call out that the estimate is using the current public meter model
- avoid mixing current and legacy labels in the final report
