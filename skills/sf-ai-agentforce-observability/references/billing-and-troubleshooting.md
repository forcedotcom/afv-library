<!-- Parent: sf-ai-agentforce-observability/SKILL.md -->

# Billing Considerations & Troubleshooting

## Billing Considerations

> **Reference**: [Billing Considerations for Agentforce Session Tracing](https://help.salesforce.com/s/articleView?id=ai.generative_ai_session_trace_usage_types.htm)

Agentforce Session Tracing consumes **Data 360 credits** for ingestion, storage, and processing.

### Credit Consumption

| Usage Type | Digital Wallet Card | Description |
|------------|---------------------|-------------|
| **Batch Data Pipeline** | Data Services | Records ingested via data streams. ~24 records per LLM round-trip. **Primary cost driver**. |
| **Data Queries** | Data Services | Records processed when running queries, reports, dashboards |
| **Streaming Calculated Insights** | Data Services | Used for Prompt Builder usage and feedback metrics |
| **Storage Beyond Allocation** | Data Storage | Storage consumed above allocated amount |

### Cost Estimation

```
Records per session ≈ Turns × 24 (avg per LLM call)
Daily records ≈ Sessions/day × Avg turns × 24

Example:
  1,000 sessions/day × 4 turns × 24 = 96,000 records/day ingested
```

**Tip**: Use [Digital Wallet](https://help.salesforce.com/s/articleView?id=sf.digital_wallet.htm) for near real-time consumption tracking.

---

## Common Issues & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | JWT auth expired/invalid | Refresh token or reconfigure ECA |
| `No session data` | Tracing not enabled | Enable Session Tracing in Agent Settings |
| `Query timeout` | Too much data | Add date filters, use incremental |
| `Memory error` | Loading all data | Use Polars lazy frames |
| `Missing DMO` | Wrong API version | Use API v60.0+ |

See [references/troubleshooting.md](../references/troubleshooting.md) for detailed solutions.

---

## Agentforce Credit Costs (Cross-Reference)

When analyzing traces for performance optimization, understanding credit costs per step type is critical:

| Step Type | Credit Cost | Notes |
|-----------|------------|-------|
| Framework operations (`before/after_reasoning`, `set`, `if/else`, `@utils.*`) | FREE | No credit consumption |
| Prompt Template invocations | 2-16 credits/call | Varies by template complexity |
| Flow/Apex action executions | 20 credits/call | Most expensive step type |

**Optimization insight**: When trace analysis reveals excessive action calls, consider consolidating multiple Flow actions into a single Apex action or using framework-level `set` operations where possible.

See `sf-ai-agentscript/references/production-gotchas.md` for the full credit consumption model and optimization strategies.
