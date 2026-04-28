<!-- Parent: sf-ai-agentforce-observability/SKILL.md -->
# CLI Reference

Complete command reference for the `stdm-extract` CLI tool.

## Global Options

| Option | Description |
|--------|-------------|
| `--help` | Show help message and exit |
| `--version` | Show version number |

---

## Commands

### `extract`

Extract session tracing data for a date range.

```bash
stdm-extract extract --org <alias> [options]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--org` | String | Required | Salesforce org alias (from `sf org list`) |
| `--consumer-key` | String | `$SF_CONSUMER_KEY` | ECA consumer key |
| `--days` | Integer | 7 | Extract last N days |
| `--since` | DateTime | None | Start date (ISO format) |
| `--until` | DateTime | Now | End date (ISO format) |
| `--agent` | String | None | Filter by agent API name (repeatable) |
| `--output` | Path | `./stdm_data` | Output directory |
| `--verbose` | Flag | False | Enable verbose logging |

**Examples:**

```bash
# Last 7 days for all agents
stdm-extract extract --org prod

# Specific date range
stdm-extract extract --org prod --since 2026-01-01 --until 2026-01-15

# Filter by agent
stdm-extract extract --org prod --agent Customer_Support_Agent

# Multiple agents
stdm-extract extract --org prod --agent Agent1 --agent Agent2
```

---

### `extract-tree`

Extract complete session tree for specific session IDs.

```bash
stdm-extract extract-tree --org <alias> --session-ids <ids> [options]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--org` | String | Required | Salesforce org alias |
| `--consumer-key` | String | `$SF_CONSUMER_KEY` | ECA consumer key |
| `--session-ids` | String | Required | Comma-separated session IDs |
| `--output` | Path | `./stdm_data` | Output directory |
| `--verbose` | Flag | False | Enable verbose logging |

**Example:**

```bash
stdm-extract extract-tree --org prod --session-ids "a0x001,a0x002,a0x003"
```

---

### `extract-incremental`

Incremental extraction based on last run timestamp.

```bash
stdm-extract extract-incremental --org <alias> [options]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--org` | String | Required | Salesforce org alias |
| `--consumer-key` | String | `$SF_CONSUMER_KEY` | ECA consumer key |
| `--output` | Path | `./stdm_data` | Output directory |
| `--verbose` | Flag | False | Enable verbose logging |

**Notes:**
- Watermark stored at `~/.sf/observability/{org}/watermark.json`
- First run extracts last 24 hours
- Subsequent runs extract since last watermark

**Example:**

```bash
# First run: extracts last 24 hours
stdm-extract extract-incremental --org prod

# Subsequent runs: extracts only new data
stdm-extract extract-incremental --org prod
```

---

### `analyze`

Generate summary statistics from extracted data.

```bash
stdm-extract analyze --data-dir <path> [options]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--data-dir` | Path | Required | Directory containing Parquet files |
| `--format` | Choice | `table` | Output format: `table`, `json`, `csv` |

**Example:**

```bash
stdm-extract analyze --data-dir ./stdm_data --format table
```

---

### `debug-session`

Debug a specific session with full message timeline.

```bash
stdm-extract debug-session --data-dir <path> --session-id <id> [options]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--data-dir` | Path | Required | Directory containing Parquet files |
| `--session-id` | String | Required | Session ID to debug |
| `--verbose` | Flag | False | Show step details (LLM, actions) |
| `--output` | Path | None | Export timeline to JSON |

**Example:**

```bash
# View timeline in terminal
stdm-extract debug-session --data-dir ./stdm_data --session-id "a0x123"

# Export to JSON with full details
stdm-extract debug-session --data-dir ./stdm_data --session-id "a0x123" \
    --verbose --output ./debug/session.json
```

---

### `topics`

Analyze topic routing patterns.

```bash
stdm-extract topics --data-dir <path> [options]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--data-dir` | Path | Required | Directory containing Parquet files |
| `--format` | Choice | `table` | Output format: `table`, `json` |

**Example:**

```bash
stdm-extract topics --data-dir ./stdm_data
```

---

### `actions`

Analyze action invocation patterns.

```bash
stdm-extract actions --data-dir <path> [options]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--data-dir` | Path | Required | Directory containing Parquet files |
| `--agent` | String | None | Filter by agent API name |
| `--format` | Choice | `table` | Output format: `table`, `json` |

**Example:**

```bash
stdm-extract actions --data-dir ./stdm_data --agent Customer_Support_Agent
```

---

### `count`

Count records in Data Cloud (quick check without extraction).

```bash
stdm-extract count --org <alias> [options]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--org` | String | Required | Salesforce org alias |
| `--consumer-key` | String | `$SF_CONSUMER_KEY` | ECA consumer key |
| `--dmo` | Choice | `sessions` | DMO to count |

**Example:**

```bash
stdm-extract count --org prod --dmo sessions
```

---

### `test-auth`

Test authentication to Data Cloud.

```bash
stdm-extract test-auth --org <alias> [options]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--org` | String | Required | Salesforce org alias |
| `--consumer-key` | String | `$SF_CONSUMER_KEY` | ECA consumer key |

**Example:**

```bash
stdm-extract test-auth --org prod
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SF_CONSUMER_KEY` | Default consumer key for ECA |
| `SF_JWT_KEY_PATH` | Override JWT private key location (default: `~/.sf/jwt/{org}.key`) |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Authentication failed |
| 3 | Data not found |
| 4 | Invalid arguments |

---

## See Also

- [Auth Setup](auth-setup.md) - Setting up JWT authentication
- [Polars Cheatsheet](polars-cheatsheet.md) - Quick analysis commands
- [Troubleshooting](../references/troubleshooting.md) - Common issues
