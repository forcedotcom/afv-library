<!-- Parent: sf-ai-agentforce-observability/SKILL.md -->
# Filtered Extraction Examples

Examples for extracting specific subsets of session tracing data.

---

## Filter by Agent

### Single Agent

Extract only sessions handled by a specific agent:

```bash
stdm-extract extract --org prod --agent Customer_Support_Agent
```

### Multiple Agents

Extract sessions from multiple agents:

```bash
stdm-extract extract --org prod \
    --agent Customer_Support_Agent \
    --agent Order_Tracking_Agent \
    --agent FAQ_Agent
```

**Note:** Agent names are the **API Name** (e.g., `My_Agent`), not the label.

---

## Filter by Date Range

### Specific Start Date

Extract from a specific date to now:

```bash
stdm-extract extract --org prod --since 2026-01-15
```

### Date Range

Extract a specific window:

```bash
stdm-extract extract --org prod \
    --since 2026-01-01 \
    --until 2026-01-15
```

### ISO DateTime Format

For precise timestamps:

```bash
stdm-extract extract --org prod \
    --since "2026-01-15T00:00:00" \
    --until "2026-01-15T23:59:59"
```

---

## Combine Filters

### Agent + Date Range

```bash
stdm-extract extract --org prod \
    --agent Customer_Support_Agent \
    --since 2026-01-01 \
    --until 2026-01-15 \
    --output ./data/jan-first-half
```

---

## Extract Specific Sessions

### Known Session IDs

When you have specific session IDs to investigate:

```bash
stdm-extract extract-tree --org prod \
    --session-ids "a0x001,a0x002,a0x003"
```

This extracts the **complete tree** for each session:
- Session record
- All interactions (turns)
- All steps (LLM and actions)
- All messages

### From a File

If you have session IDs in a file:

```bash
# Session IDs file (one per line)
cat session_ids.txt
a0x001
a0x002
a0x003

# Extract using command substitution
stdm-extract extract-tree --org prod \
    --session-ids "$(cat session_ids.txt | tr '\n' ',')"
```

---

## Incremental Extraction

### First Run

Extracts last 24 hours and saves watermark:

```bash
stdm-extract extract-incremental --org prod
```

**Creates:**
- `~/.sf/observability/prod/watermark.json`
- `./stdm_data/` (with 24h of data)

### Subsequent Runs

Extracts only new data since last run:

```bash
stdm-extract extract-incremental --org prod
```

**Watermark file:**
```json
{
  "last_run": "2026-01-28T10:15:23.000Z",
  "sessions_extracted": 1234
}
```

### Force Full Re-extraction

Delete the watermark to reset:

```bash
rm ~/.sf/observability/prod/watermark.json
stdm-extract extract-incremental --org prod  # Now extracts last 24h
```

---

## Production Workflow

### Daily Extraction Job

```bash
#!/bin/bash
# daily-extract.sh

ORG="prod"
OUTPUT_BASE="/data/agentforce"
DATE=$(date +%Y-%m-%d)

# Extract yesterday's data
stdm-extract extract --org $ORG \
    --since "$(date -d 'yesterday' +%Y-%m-%d)" \
    --until "$DATE" \
    --output "$OUTPUT_BASE/$DATE" \
    --verbose 2>&1 | tee "$OUTPUT_BASE/logs/$DATE.log"
```

### Scheduled Incremental (Cron)

```bash
# Run every hour, extract only new data
0 * * * * /usr/local/bin/stdm-extract extract-incremental --org prod >> /var/log/stdm.log 2>&1
```

---

## Finding Agent Names

If you're not sure of the exact agent API names:

### Option 1: Extract First, Then Filter

```bash
# Extract all
stdm-extract extract --org prod --days 1

# Check agent names
python3 -c "
import polars as pl
print(pl.read_parquet('./stdm_data/sessions/data.parquet')
    .select('ssot__AiAgentApiName__c')
    .unique()
)
"
```

### Option 2: Check in Salesforce

1. **Setup** → **Agents**
2. Click agent → **Details** tab
3. Copy **API Name**

---

## Tips

1. **Start small**: Test with `--days 1` before large extractions
2. **Use incremental**: For ongoing monitoring, use `extract-incremental`
3. **Separate outputs**: Use `--output` to organize by date or environment
4. **Check counts first**: Use `count` command to estimate extraction size

---

## See Also

- [Basic Extraction](basic-extraction.md) - Simple examples
- [Analysis Examples](analysis-examples.md) - Analyze filtered data
- [CLI Reference](../references/cli-reference.md) - All command options
