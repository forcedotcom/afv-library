<!-- Parent: sf-ai-agentforce-observability/SKILL.md -->
# Basic Extraction Examples

Simple examples to get started with STDM extraction.

## Prerequisites

1. JWT authentication configured (see [Auth Setup](../references/auth-setup.md))
2. Consumer key set: `export SF_CONSUMER_KEY="3MVG9..."`
3. Org alias available in `sf org list`

---

## Example 1: Extract Last 7 Days

The simplest extraction - all sessions from the last 7 days:

```bash
stdm-extract extract --org prod
```

**Output structure:**
```
./stdm_data/
├── sessions/
│   └── data.parquet
├── interactions/
│   └── data.parquet
├── steps/
│   └── data.parquet
└── messages/
    └── data.parquet
```

---

## Example 2: Extract Last 24 Hours

```bash
stdm-extract extract --org prod --days 1
```

---

## Example 3: Custom Output Directory

```bash
stdm-extract extract --org prod --output /data/agentforce/prod
```

---

## Example 4: Verbose Mode

See detailed progress and timing:

```bash
stdm-extract extract --org prod --verbose
```

**Sample output:**
```
🔐 Authenticating to Data Cloud...
   Instance URL: https://myorg.my.salesforce.com

📊 Extracting sessions...
   Query: SELECT ... FROM ssot__AIAgentSession__dlm WHERE ...
   Records: 1,234 (2.3s)

📊 Extracting interactions...
   Records: 5,678 (4.1s)

📊 Extracting steps...
   Records: 12,345 (8.7s)

📊 Extracting messages...
   Records: 9,876 (5.2s)

✅ Extraction complete!
   Total records: 29,133
   Duration: 20.3s
   Output: ./stdm_data/
```

---

## Example 5: Test Authentication First

Before extracting, verify your setup:

```bash
stdm-extract test-auth --org prod
```

**Success:**
```
✅ Authentication successful
   Instance URL: https://myorg.my.salesforce.com
   Token valid for: 3599 seconds
```

**Failure:**
```
❌ Authentication failed
   Error: invalid_grant
   Hint: Check certificate expiration with:
         openssl x509 -enddate -noout -in ~/.sf/jwt/prod.key
```

---

## Example 6: Count Records Before Extraction

Check how much data exists without downloading:

```bash
stdm-extract count --org prod --dmo sessions
```

**Output:**
```
📊 Record counts for prod:
   Sessions: 12,345
```

---

## Example 7: Extract from Sandbox

Works the same as production - just use the sandbox alias:

```bash
# List your orgs
sf org list

# Extract from sandbox
stdm-extract extract --org mysandbox --days 3
```

---

## What's Next?

- [Filtered Extraction](filtered-extraction.md) - Filter by agent, date range
- [Analysis Examples](analysis-examples.md) - Analyze extracted data
- [Debugging Sessions](debugging-sessions.md) - Debug specific sessions

---

## Quick Reference

| Task | Command |
|------|---------|
| Last 7 days | `stdm-extract extract --org prod` |
| Last N days | `stdm-extract extract --org prod --days N` |
| Test auth | `stdm-extract test-auth --org prod` |
| Check counts | `stdm-extract count --org prod` |
| Verbose mode | Add `--verbose` to any command |
